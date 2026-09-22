"""Leitor de pacotes STFS (Xbox 360), em Python puro.

STFS é o contentor usado por títulos Xbox Live Arcade, DLC, atualizações de
título e saves. O ficheiro começa por "CON ", "LIVE" ou "PIRS".

Porquê nativo e não um motor externo: as ferramentas conhecidas (wxPirs,
Velocity, Le Fluffie) são GUI de Windows. Um parser em Python não precisa de
binário empacotado, não dispara falso positivo de antivírus, não traz questão
de licença e corre em Linux e macOS -- que é onde o projeto vive.

A parte não trivial do formato é o endereçamento: os blocos de dados têm
tabelas de hash intercaladas, uma a cada 0xAA blocos e outra a cada 0x70E4,
por isso o número lógico de um bloco não é a sua posição no ficheiro.

Referências: Free60 Wiki (System-Software/Formats/STFS) e o parser py360 de
arkem. As duas concordam nos offsets do cabeçalho e da tabela de ficheiros.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Iterator

MAGICS = (b"CON ", b"LIVE", b"PIRS")

BLOCK_SIZE = 0x1000
HASH_ENTRY_SIZE = 0x18
ENTRIES_PER_TABLE = 0xAA           # blocos cobertos por uma tabela de nível 0
LEVEL1_SPAN = 0x70E4               # 0xAA * 0xAA
FILE_ENTRY_SIZE = 0x40

# Offsets absolutos no cabeçalho
OFF_HEADER_SIZE = 0x340            # BE u32
OFF_CONTENT_TYPE = 0x344           # BE u32
OFF_CONTENT_SIZE = 0x34C           # BE u64
OFF_TITLE_ID = 0x360               # BE u32
OFF_DESCRIPTOR = 0x379             # 0x24 bytes
OFF_FILE_TABLE_COUNT = 0x37C       # LE u16   (descritor + 0x03)
OFF_FILE_TABLE_BLOCK = 0x37E       # LE u24   (descritor + 0x05)
OFF_ALLOCATED_BLOCKS = 0x395       # BE u32   (descritor + 0x1C)
OFF_DISPLAY_NAME = 0x411           # UTF-16BE

# Flags do byte 0x28 de cada entrada da tabela de ficheiros
FLAG_NAME_LENGTH = 0x3F
FLAG_CONTIGUOUS = 0x40
FLAG_DIRECTORY = 0x80

MAX_CHAIN = 1 << 22                # trava contra uma cadeia de blocos circular


class StfsError(Exception):
    pass


class StfsCancelled(StfsError):
    """Interrupção pedida por quem chamou -- não é uma falha do pacote."""


def _u24_le(data: bytes) -> int:
    return data[0] | (data[1] << 8) | (data[2] << 16)


@dataclass
class StfsEntry:
    name: str
    is_directory: bool
    blocks: int
    start_block: int
    parent: int
    size: int
    contiguous: bool
    index: int = 0
    path: str = field(default="")

    @property
    def is_file(self) -> bool:
        return not self.is_directory


class StfsPackage:
    """Abre um pacote STFS e extrai o seu conteúdo."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.handle = None
        self.entries: list[StfsEntry] = []
        self.magic = b""
        self.header_size = 0
        self.content_type = 0
        self.content_size = 0
        self.title_id = 0
        self.display_name = ""
        self.table_size_shift = 0
        self.file_table_blocks = 0
        self.file_table_block = 0
        self.allocated_blocks = 0

    # ----------------------------------------------------------- abertura
    def __enter__(self) -> "StfsPackage":
        self.open()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def open(self) -> "StfsPackage":
        self.handle = self.path.open("rb")
        try:
            self._read_header()
            self._read_file_table()
        except Exception:
            self.close()
            raise
        return self

    def close(self) -> None:
        if self.handle is not None:
            self.handle.close()
            self.handle = None

    # ----------------------------------------------------------- cabeçalho
    def _read_header(self) -> None:
        head = self._read_at(0, 0x1000)
        if len(head) < 0x400 or head[:4] not in MAGICS:
            raise StfsError("não é um pacote STFS (magic inválido)")

        self.magic = head[:4]
        self.header_size = struct.unpack_from(">I", head, OFF_HEADER_SIZE)[0]
        self.content_type = struct.unpack_from(">I", head, OFF_CONTENT_TYPE)[0]
        self.content_size = struct.unpack_from(">Q", head, OFF_CONTENT_SIZE)[0]
        self.title_id = struct.unpack_from(">I", head, OFF_TITLE_ID)[0]

        self.file_table_blocks = struct.unpack_from("<H", head, OFF_FILE_TABLE_COUNT)[0]
        self.file_table_block = _u24_le(head[OFF_FILE_TABLE_BLOCK:OFF_FILE_TABLE_BLOCK + 3])
        self.allocated_blocks = struct.unpack_from(">I", head, OFF_ALLOCATED_BLOCKS)[0]

        # Tabelas de hash ocupam 1 bloco quando o cabeçalho tem 0xB000 (o caso
        # normal) e 2 blocos caso contrário.
        self.table_size_shift = 0 if ((self.header_size + 0xFFF) & 0xF000) >> 0xC == 0xB else 1

        name = head[OFF_DISPLAY_NAME:OFF_DISPLAY_NAME + 0x80]
        self.display_name = name.decode("utf-16-be", errors="ignore").split("\x00")[0].strip()

        if self.file_table_blocks == 0:
            raise StfsError("tabela de ficheiros vazia")

    @property
    def _hash_table_base(self) -> int:
        """Posição da primeira tabela de hash (logo a seguir ao cabeçalho)."""
        return (self.header_size + 0xFFF) & 0xFFFFF000

    @property
    def _data_base(self) -> int:
        """Posição do primeiro bloco de dados: depois da primeira tabela."""
        return self._hash_table_base + (BLOCK_SIZE << self.table_size_shift)

    # ------------------------------------------------------ endereçamento
    def _backing_block(self, block: int) -> int:
        """Número lógico -> índice físico, contando as tabelas pelo meio."""
        adjust = 0
        if block >= ENTRIES_PER_TABLE:
            adjust += ((block // ENTRIES_PER_TABLE) + 1) << self.table_size_shift
        if block >= LEVEL1_SPAN:
            adjust += ((block // LEVEL1_SPAN) + 1) << self.table_size_shift
        return block + adjust

    def block_offset(self, block: int) -> int:
        return self._data_base + self._backing_block(block) * BLOCK_SIZE

    def _level0_table_block(self, block: int) -> int:
        """Bloco físico da tabela de hash que descreve `block`."""
        if block < ENTRIES_PER_TABLE:
            return 0
        number = (block // ENTRIES_PER_TABLE) * 0xAB
        number += ((block // LEVEL1_SPAN) + 1) << self.table_size_shift
        if block // LEVEL1_SPAN == 0:
            return number
        return number + (1 << self.table_size_shift)

    def hash_entry(self, block: int) -> tuple[int, int]:
        """(estado, próximo bloco) da entrada de hash de `block`."""
        table = self._level0_table_block(block)
        offset = self._hash_table_base + table * BLOCK_SIZE
        offset += (block % ENTRIES_PER_TABLE) * HASH_ENTRY_SIZE
        record = self._read_at(offset, HASH_ENTRY_SIZE)
        if len(record) < HASH_ENTRY_SIZE:
            raise StfsError(f"tabela de hash truncada no bloco {block}")
        return record[0x14], _u24_le(record[0x15:0x18])

    # -------------------------------------------------- tabela de ficheiros
    def _read_file_table(self) -> None:
        raw = b"".join(
            self._read_block(block)
            for block in self._walk_blocks(self.file_table_block, self.file_table_blocks)
        )

        entries: list[StfsEntry] = []
        for index in range(len(raw) // FILE_ENTRY_SIZE):
            chunk = raw[index * FILE_ENTRY_SIZE:(index + 1) * FILE_ENTRY_SIZE]
            flags = chunk[0x28]
            length = flags & FLAG_NAME_LENGTH
            if length == 0:
                continue                      # entrada vazia

            name = chunk[:length].decode("utf-8", errors="replace").rstrip("\x00")
            if not name:
                continue

            entries.append(
                StfsEntry(
                    name=name,
                    is_directory=bool(flags & FLAG_DIRECTORY),
                    contiguous=bool(flags & FLAG_CONTIGUOUS),
                    blocks=_u24_le(chunk[0x29:0x2C]),
                    start_block=_u24_le(chunk[0x2F:0x32]),
                    parent=struct.unpack_from(">h", chunk, 0x32)[0],
                    size=struct.unpack_from(">I", chunk, 0x34)[0],
                    index=index,
                )
            )

        self.entries = entries
        self._resolve_paths()

    def _resolve_paths(self) -> None:
        by_index = {entry.index: entry for entry in self.entries}

        def resolve(entry: StfsEntry, depth: int = 0) -> str:
            if entry.parent < 0 or depth > 32:
                return entry.name
            parent = by_index.get(entry.parent)
            if parent is None or parent is entry:
                return entry.name
            return f"{resolve(parent, depth + 1)}/{entry.name}"

        for entry in self.entries:
            entry.path = resolve(entry)

    # ------------------------------------------------------------- leitura
    def _read_at(self, offset: int, size: int) -> bytes:
        self.handle.seek(offset)
        return self.handle.read(size)

    def _read_block(self, block: int) -> bytes:
        data = self._read_at(self.block_offset(block), BLOCK_SIZE)
        if len(data) < BLOCK_SIZE:
            data = data.ljust(BLOCK_SIZE, b"\x00")
        return data

    def _walk_blocks(self, start: int, count: int) -> Iterator[int]:
        """Percorre os blocos de um ficheiro seguindo a cadeia das tabelas de
        hash. Se a cadeia se partir, continua sequencialmente."""
        block = start
        for produced in range(count):
            if block < 0 or produced > MAX_CHAIN:
                raise StfsError("cadeia de blocos inválida")
            yield block

            if produced + 1 >= count:
                break
            try:
                _status, nxt = self.hash_entry(block)
            except StfsError:
                nxt = block + 1
            block = nxt if 0 < nxt < 0xFFFFFF else block + 1

    def read_file(self, entry: StfsEntry) -> Iterator[bytes]:
        remaining = entry.size
        blocks = (
            iter(range(entry.start_block, entry.start_block + entry.blocks))
            if entry.contiguous
            else self._walk_blocks(entry.start_block, entry.blocks)
        )
        for block in blocks:
            if remaining <= 0:
                break
            chunk = self._read_block(block)
            take = min(BLOCK_SIZE, remaining)
            remaining -= take
            yield chunk[:take]

        if remaining > 0:
            raise StfsError(f"{entry.path}: faltam {remaining} bytes")

    # ------------------------------------------------------------- extração
    @property
    def files(self) -> list[StfsEntry]:
        return [entry for entry in self.entries if entry.is_file]

    def extract_all(
        self,
        destination: Path,
        progress: Callable[[float, str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
    ) -> int:
        destination = Path(destination)
        destination.mkdir(parents=True, exist_ok=True)

        files = self.files
        total = sum(entry.size for entry in files) or 1
        written = 0
        count = 0

        for entry in files:
            if should_cancel is not None and should_cancel():
                raise StfsCancelled("cancelado")

            target = self._safe_target(destination, entry.path)
            target.parent.mkdir(parents=True, exist_ok=True)

            with target.open("wb") as handle:
                for chunk in self.read_file(entry):
                    handle.write(chunk)
                    written += len(chunk)
                    if progress is not None:
                        progress(min(1.0, written / total), entry.name)

            count += 1

        if count == 0:
            raise StfsError("o pacote não contém ficheiros")
        return count

    @staticmethod
    def _safe_target(root: Path, relative: str) -> Path:
        """Impede que um nome como ../../x escreva fora do destino."""
        parts = [part for part in relative.replace("\\", "/").split("/")
                 if part not in ("", ".", "..")]
        return root.joinpath(*parts) if parts else root / "sem_nome"


def is_stfs(path: Path) -> bool:
    try:
        with Path(path).open("rb") as handle:
            return handle.read(4) in MAGICS
    except OSError:
        return False


def describe(path: Path) -> dict:
    """Metadados para a UI, sem custo de extração."""
    try:
        with StfsPackage(path) as package:
            return {
                "magic": package.magic.decode("ascii", "replace").strip(),
                "title_id": f"{package.title_id:08X}",
                "name": package.display_name,
                "files": len(package.files),
                "content_type": f"{package.content_type:08X}",
            }
    except (StfsError, OSError):
        return {}
