"""Leitor de Games on Demand (GOD / SVOD), em Python puro.

Um GOD é um XDVDFS partido aos bocados: o cabeçalho fica num ficheiro sem
extensão e os dados numa pasta `<cabeçalho>.data`, em ficheiros data0000,
data0001, ... Dentro de cada um, os dados vêm intercalados com tabelas de
hash, tal como no STFS -- só que com outra geometria.

Geometria de um ficheiro de dados (0xA290000 bytes, exactamente):

    1 bloco de hash L1
    203 x [ 1 bloco de hash L0 + 204 blocos de dados ]

    1 + 203 * (1 + 204) = 41616 blocos de 0x1000 = 0xA290000    ✓

Os blocos de dados contam-se aqui em sectores de 0x800 (o sector de um DVD),
que é como o resto do mundo fala deste formato: 204 blocos = 0x198 sectores
por grupo, 203 * 204 blocos = 0x14388 sectores por ficheiro.

Sobre a fiabilidade destes números
----------------------------------
A estrutura acima está confirmada por duas fontes independentes que batem
certo ao byte. O que nenhuma delas fixa é onde começam os dados dentro do
ficheiro (0x2000 ou 0x12000, conforme o layout GDF melhorado) nem se o
`data_block_offset` do descritor se lê em big ou em little endian.

Em vez de adivinhar, o leitor experimenta as variantes e fica com a que o
próprio ficheiro valida -- a assinatura MICROSOFT*XBOX*MEDIA tem de aparecer
onde o XDVDFS manda. Se nenhuma validar, levanta GodError em vez de escrever
uma imagem partida. É por isso que `probe()` existe e é chamado antes de se
escrever um único byte.

Uma variante que se descartou de propósito: uma das implementações de
referência não conta a tabela L0 no primeiro sector de cada grupo. Com a
geometria acima isso põe o sector 0x198 em 0xCE000, que é exactamente onde
está a tabela L0 do grupo 1 -- leria a tabela de hash como se fossem dados.
Fica de fora por ser demonstravelmente errada, e não por preferência.

O que sai daqui é a imagem XDVDFS. Quem a lê é o extract-xiso, que já está no
pipeline -- não há aqui nenhum parser do sistema de ficheiros do Xbox.
"""

from __future__ import annotations

import re
import struct
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterator

from core.xbox.stfs import MAGICS, OFF_CONTENT_TYPE, OFF_DISPLAY_NAME, OFF_TITLE_ID

SECTOR = 0x800                     # sector de DVD
BLOCK = 0x1000                     # bloco de hash
SECTORS_PER_GROUP = 0x198          # 204 blocos de dados entre tabelas L0
SECTORS_PER_FILE = 0x14388         # 203 grupos por ficheiro de dados
DATA_FILE_SIZE = 0xA290000

# Descritor SVOD, no mesmo sítio onde um STFS põe o seu (cabeçalho + 0x379).
OFF_DESCRIPTOR = 0x379
OFF_DESC_SIZE = OFF_DESCRIPTOR + 0x00
OFF_DEVICE_FEATURES = OFF_DESCRIPTOR + 0x18
OFF_DATA_BLOCK_COUNT = OFF_DESCRIPTOR + 0x19       # uint24
OFF_DATA_BLOCK_OFFSET = OFF_DESCRIPTOR + 0x1C      # uint24
DESCRIPTOR_SIZE = 0x24

CONTENT_TYPE_GOD = 0x00007000
FEATURE_ENHANCED_GDF = 0x40

XDVDFS_MAGIC = b"MICROSOFT*XBOX*MEDIA"
# Deslocamentos onde a assinatura pode estar numa imagem Xbox 360 válida.
XGD_PARTITIONS = (0x00000000, 0xFD90000, 0x02080000, 0x18300000)

DATA_FILE_RE = re.compile(r"^data\d{4}$", re.IGNORECASE)

# Bases possíveis dentro de um ficheiro de dados: a seguir ao L1 + primeiro L0
# (0x2000) ou depois do cabeçalho maior do layout GDF melhorado (0x12000).
BASE_OFFSETS = (0x2000, 0x12000)


class GodError(Exception):
    pass


class GodCancelled(GodError):
    """Interrupção pedida por quem chamou -- não é uma falha do pacote."""


def _u24_be(data: bytes) -> int:
    return (data[0] << 16) | (data[1] << 8) | data[2]


def _u24_le(data: bytes) -> int:
    return data[0] | (data[1] << 8) | (data[2] << 16)


@dataclass(frozen=True)
class Layout:
    """Uma interpretação possível do formato. `probe()` escolhe a certa."""

    base: int                  # bytes antes do primeiro sector de dados
    lead_sectors: int          # sectores em branco antes do início do fluxo

    def offset_in_file(self, sector: int) -> int:
        return self.base + sector * SECTOR + (sector // SECTORS_PER_GROUP) * BLOCK


class GodPackage:
    """Lê um Games on Demand e reconstrói a imagem XDVDFS."""

    def __init__(self, header: Path):
        self.header = Path(header)
        self.data_dir = self.header.with_name(self.header.name + ".data")
        self.data_files: list[Path] = []
        self.magic = b""
        self.content_type = 0
        self.title_id = 0
        self.display_name = ""
        self.device_features = 0
        self.data_block_count = 0
        self.data_block_offset_be = 0
        self.data_block_offset_le = 0
        self.layout: Layout | None = None
        self._handles: dict[int, object] = {}

    # ------------------------------------------------------------- ciclo
    def __enter__(self) -> "GodPackage":
        self.open()
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def open(self) -> "GodPackage":
        try:
            self._read_header()
            self._collect_data_files()
            self.layout = self.probe()
        except Exception:
            # O probe já abriu ficheiros de dados; se falhar aqui, o __exit__
            # nunca chega a correr e os descritores ficavam pendurados.
            self.close()
            raise
        return self

    def close(self) -> None:
        for handle in self._handles.values():
            try:
                handle.close()
            except OSError:
                pass
        self._handles.clear()

    # ------------------------------------------------------------ leitura
    def _read_header(self) -> None:
        try:
            head = self.header.open("rb")
        except OSError as exc:
            raise GodError(f"não foi possível abrir o cabeçalho: {exc}") from exc

        with head:
            data = head.read(0x1000)

        if len(data) < 0x500 or data[:4] not in MAGICS:
            raise GodError("não é um contentor do Xbox 360 (magic inválido)")

        self.magic = data[:4]
        self.content_type = struct.unpack_from(">I", data, OFF_CONTENT_TYPE)[0]
        self.title_id = struct.unpack_from(">I", data, OFF_TITLE_ID)[0]

        if data[OFF_DESC_SIZE] != DESCRIPTOR_SIZE:
            raise GodError("descritor de volume com tamanho inesperado")

        self.device_features = data[OFF_DEVICE_FEATURES]
        self.data_block_count = _u24_be(data[OFF_DATA_BLOCK_COUNT:OFF_DATA_BLOCK_COUNT + 3])
        raw_offset = data[OFF_DATA_BLOCK_OFFSET:OFF_DATA_BLOCK_OFFSET + 3]
        self.data_block_offset_be = _u24_be(raw_offset)
        self.data_block_offset_le = _u24_le(raw_offset)

        name = data[OFF_DISPLAY_NAME:OFF_DISPLAY_NAME + 0x80]
        self.display_name = name.decode("utf-16-be", errors="ignore").split("\x00")[0].strip()

    def _collect_data_files(self) -> None:
        if not self.data_dir.is_dir():
            raise GodError(f"falta a pasta de dados {self.data_dir.name}")

        try:
            files = sorted(
                (entry for entry in self.data_dir.iterdir()
                 if entry.is_file() and DATA_FILE_RE.match(entry.name)),
                key=lambda entry: entry.name.lower(),
            )
        except OSError as exc:
            raise GodError(f"não foi possível ler {self.data_dir.name}: {exc}") from exc

        if not files:
            raise GodError(f"{self.data_dir.name} não tem ficheiros data0000…")

        # Uma peça a meio em falta dava uma imagem silenciosamente corrompida.
        for index, entry in enumerate(files):
            if entry.name.lower() != f"data{index:04d}":
                raise GodError(f"falta o ficheiro data{index:04d} em {self.data_dir.name}")

        self.data_files = files

    def _handle(self, index: int):
        if index not in self._handles:
            if index >= len(self.data_files):
                raise GodError(f"pedido o ficheiro data{index:04d}, que não existe")
            try:
                self._handles[index] = self.data_files[index].open("rb")
            except OSError as exc:
                raise GodError(f"não foi possível abrir data{index:04d}: {exc}") from exc
        return self._handles[index]

    # --------------------------------------------------------- geometria
    def read_sector(self, sector: int, layout: Layout | None = None) -> bytes:
        """Um sector do fluxo de dados, já sem as tabelas de hash pelo meio."""
        layout = layout or self.layout
        if layout is None:
            raise GodError("geometria ainda não determinada")

        position = sector - layout.lead_sectors
        if position < 0:
            return b"\x00" * SECTOR          # espaço antes do início do fluxo

        index, inner = divmod(position, SECTORS_PER_FILE)
        handle = self._handle(index)
        handle.seek(layout.offset_in_file(inner))
        data = handle.read(SECTOR)
        return data.ljust(SECTOR, b"\x00") if len(data) < SECTOR else data

    @property
    def total_sectors(self) -> int:
        """Tamanho da imagem, em sectores."""
        if self.data_block_count:
            counted = self.data_block_count * 2      # blocos de 0x1000 -> sectores
        else:
            counted = len(self.data_files) * SECTORS_PER_FILE
        lead = self.layout.lead_sectors if self.layout else 0
        return lead + counted

    # ------------------------------------------------------------- probe
    def candidates(self) -> list[Layout]:
        leads = []
        for offset in (self.data_block_offset_be, self.data_block_offset_le, 0):
            value = offset * 2
            # Um avanço maior do que a primeira partição não faz sentido: a
            # assinatura deixaria de caber onde o XDVDFS a põe.
            if 0 <= value <= 0x40 and value not in leads:
                leads.append(value)

        return [
            Layout(base=base, lead_sectors=lead)
            for lead in leads
            for base in BASE_OFFSETS
        ]

    def probe(self) -> Layout:
        """Escolhe a geometria que o próprio ficheiro valida.

        O teste é a assinatura do XDVDFS: se a leitura estiver desalinhada
        nem que seja por um bloco, ela não aparece.
        """
        for layout in self.candidates():
            try:
                if self._validates(layout):
                    return layout
            except GodError:
                continue

        raise GodError(
            "não foi possível reconhecer a geometria deste GOD "
            "(nenhuma variante produziu uma imagem XDVDFS válida)"
        )

    def _validates(self, layout: Layout) -> bool:
        for partition in XGD_PARTITIONS:
            sector = (partition + 0x10000) // SECTOR
            try:
                data = self.read_sector(sector, layout)
            except (GodError, OSError):
                return False
            if data[:len(XDVDFS_MAGIC)] == XDVDFS_MAGIC:
                return True
        return False

    # ---------------------------------------------------------- extração
    def sectors(self) -> Iterator[bytes]:
        for sector in range(self.total_sectors):
            yield self.read_sector(sector)

    def rebuild(
        self,
        destination: Path,
        progress: Callable[[float, str], None] | None = None,
        should_cancel: Callable[[], bool] | None = None,
        chunk_sectors: int = 256,
    ) -> Path:
        """Escreve a imagem XDVDFS em `destination`."""
        destination = Path(destination)
        destination.parent.mkdir(parents=True, exist_ok=True)

        total = self.total_sectors or 1
        name = destination.name
        written = 0

        with destination.open("wb") as out:
            while written < total:
                if should_cancel is not None and should_cancel():
                    raise GodCancelled("cancelado")

                batch = min(chunk_sectors, total - written)
                out.write(b"".join(
                    self.read_sector(written + step) for step in range(batch)
                ))
                written += batch
                if progress is not None:
                    progress(min(1.0, written / total), name)

        return destination


def is_god(header: Path) -> bool:
    header = Path(header)
    data_dir = header.with_name(header.name + ".data")
    try:
        if not data_dir.is_dir():
            return False
        with header.open("rb") as handle:
            return handle.read(4) in MAGICS
    except OSError:
        return False


def describe(header: Path) -> dict:
    try:
        with GodPackage(header) as package:
            return {
                "title_id": f"{package.title_id:08X}",
                "name": package.display_name,
                "parts": len(package.data_files),
                "sectors": package.total_sectors,
                "base": hex(package.layout.base) if package.layout else "",
            }
    except (GodError, OSError):
        return {}
