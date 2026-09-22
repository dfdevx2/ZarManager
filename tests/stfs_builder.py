"""Construtor de pacotes STFS sintéticos, para os testes.

O que este ficheiro prova e o que não prova:

PROVA que o leitor em `core/xbox/stfs.py` é coerente -- que percorre a tabela
de ficheiros, resolve caminhos de subdiretórios, segue a cadeia de blocos de
um ficheiro não contíguo e acerta no endereçamento quando o pacote é grande o
suficiente para ter mais do que uma tabela de hash.

NÃO PROVA compatibilidade byte a byte com pacotes de retalho: o escritor e o
leitor partilham a mesma leitura da especificação, por isso um mal-entendido
comum passaria despercebido. Para isso é preciso um ficheiro XBLA ou DLC real.
"""

from __future__ import annotations

import struct
from dataclasses import dataclass
from pathlib import Path

BLOCK_SIZE = 0x1000
HASH_ENTRY_SIZE = 0x18
ENTRIES_PER_TABLE = 0xAA
LEVEL1_SPAN = 0x70E4
FILE_ENTRY_SIZE = 0x40
HEADER_SIZE = 0xB000               # tamanho normal: dá table_size_shift = 0
END_OF_CHAIN = 0xFFFFFF


@dataclass
class _Item:
    path: str
    data: bytes
    contiguous: bool = True
    blocks: list[int] | None = None
    index: int = 0
    parent: int = -1
    is_directory: bool = False


class StfsBuilder:
    """Monta um pacote STFS válido a partir de ficheiros em memória."""

    def __init__(self, magic: bytes = b"CON ", title_id: int = 0x4D5307D5,
                 display_name: str = "Pacote de Teste"):
        self.magic = magic
        self.title_id = title_id
        self.display_name = display_name
        self._items: list[_Item] = []

    # ------------------------------------------------------------- entrada
    def add_file(self, path: str, data: bytes, contiguous: bool = True) -> "StfsBuilder":
        self._items.append(_Item(path=path, data=data, contiguous=contiguous))
        return self

    # ------------------------------------------- endereçamento (espelha o leitor)
    @staticmethod
    def backing_block(block: int) -> int:
        adjust = 0
        if block >= ENTRIES_PER_TABLE:
            adjust += (block // ENTRIES_PER_TABLE) + 1
        if block >= LEVEL1_SPAN:
            adjust += (block // LEVEL1_SPAN) + 1
        return block + adjust

    @staticmethod
    def level0_table_block(block: int) -> int:
        if block < ENTRIES_PER_TABLE:
            return 0
        number = (block // ENTRIES_PER_TABLE) * 0xAB
        number += (block // LEVEL1_SPAN) + 1
        if block // LEVEL1_SPAN == 0:
            return number
        return number + 1

    @classmethod
    def data_offset(cls, block: int) -> int:
        return HEADER_SIZE + BLOCK_SIZE + cls.backing_block(block) * BLOCK_SIZE

    @classmethod
    def hash_offset(cls, block: int) -> int:
        table = cls.level0_table_block(block)
        return HEADER_SIZE + table * BLOCK_SIZE + (block % ENTRIES_PER_TABLE) * HASH_ENTRY_SIZE

    # ------------------------------------------------------------ montagem
    def build(self, destination: Path) -> Path:
        directories, files = self._expand()
        entries = directories + files

        table_entries = len(entries)
        table_blocks = max(1, (table_entries * FILE_ENTRY_SIZE + BLOCK_SIZE - 1) // BLOCK_SIZE)

        # Bloco 0 em diante: tabela de ficheiros. Os dados vêm a seguir.
        next_block = table_blocks
        for item in files:
            needed = max(1, (len(item.data) + BLOCK_SIZE - 1) // BLOCK_SIZE)
            blocks = list(range(next_block, next_block + needed))
            if not item.contiguous and needed > 1:
                blocks.reverse()          # força uma cadeia fora de ordem
            item.blocks = blocks
            next_block += needed

        total_blocks = next_block
        image = bytearray(self.data_offset(total_blocks + ENTRIES_PER_TABLE))

        self._write_header(image, table_blocks, total_blocks)
        self._write_file_table(image, entries, table_blocks)

        for item in files:
            self._write_item(image, item)

        Path(destination).write_bytes(bytes(image))
        return Path(destination)

    def _expand(self) -> tuple[list[_Item], list[_Item]]:
        """Cria as entradas de diretório implicadas pelos caminhos."""
        directories: dict[str, _Item] = {}

        for item in self._items:
            parts = item.path.split("/")[:-1]
            accumulated = ""
            for part in parts:
                accumulated = f"{accumulated}/{part}" if accumulated else part
                if accumulated not in directories:
                    directories[accumulated] = _Item(
                        path=accumulated, data=b"", is_directory=True
                    )

        ordered_dirs = sorted(directories.values(), key=lambda d: d.path.count("/"))
        files = list(self._items)

        for index, entry in enumerate(ordered_dirs + files):
            entry.index = index

        lookup = {entry.path: entry.index for entry in ordered_dirs}
        for entry in ordered_dirs + files:
            parent_path = "/".join(entry.path.split("/")[:-1])
            entry.parent = lookup.get(parent_path, -1)

        return ordered_dirs, files

    def _write_header(self, image: bytearray, table_blocks: int, total_blocks: int) -> None:
        image[0:4] = self.magic
        struct.pack_into(">I", image, 0x340, HEADER_SIZE)
        struct.pack_into(">I", image, 0x344, 0x00007000)          # Games on Demand-ish
        struct.pack_into(">Q", image, 0x34C, total_blocks * BLOCK_SIZE)
        struct.pack_into(">I", image, 0x360, self.title_id)

        image[0x379] = 0x24                                        # tamanho do descritor
        image[0x37A] = 0x00                                        # block separation
        struct.pack_into("<H", image, 0x37C, table_blocks)
        image[0x37E:0x381] = (0).to_bytes(3, "little")             # tabela no bloco 0
        struct.pack_into(">I", image, 0x395, total_blocks)

        name = self.display_name.encode("utf-16-be")[:0x7E]
        image[0x411:0x411 + len(name)] = name

    def _write_file_table(self, image: bytearray, entries: list[_Item],
                          table_blocks: int) -> None:
        table = bytearray(table_blocks * BLOCK_SIZE)

        for entry in entries:
            name = entry.path.split("/")[-1].encode("utf-8")[:0x28]
            flags = len(name)
            if entry.is_directory:
                flags |= 0x80
            elif entry.contiguous:
                flags |= 0x40

            blocks = entry.blocks or []
            start = blocks[0] if blocks else 0
            count = len(blocks)

            record = bytearray(FILE_ENTRY_SIZE)
            record[0:len(name)] = name
            record[0x28] = flags
            record[0x29:0x2C] = count.to_bytes(3, "little")
            record[0x2C:0x2F] = count.to_bytes(3, "little")
            record[0x2F:0x32] = start.to_bytes(3, "little")
            struct.pack_into(">h", record, 0x32, entry.parent)
            struct.pack_into(">I", record, 0x34, len(entry.data))

            offset = entry.index * FILE_ENTRY_SIZE
            table[offset:offset + FILE_ENTRY_SIZE] = record

        for position in range(table_blocks):
            block = position
            chunk = table[position * BLOCK_SIZE:(position + 1) * BLOCK_SIZE]
            self._place(image, block, chunk)
            nxt = block + 1 if position + 1 < table_blocks else END_OF_CHAIN
            self._place_hash(image, block, nxt)

    def _write_item(self, image: bytearray, item: _Item) -> None:
        blocks = item.blocks or []
        for position, block in enumerate(blocks):
            chunk = item.data[position * BLOCK_SIZE:(position + 1) * BLOCK_SIZE]
            self._place(image, block, chunk.ljust(BLOCK_SIZE, b"\x00"))
            nxt = blocks[position + 1] if position + 1 < len(blocks) else END_OF_CHAIN
            self._place_hash(image, block, nxt)

    @classmethod
    def _place(cls, image: bytearray, block: int, chunk: bytes) -> None:
        offset = cls.data_offset(block)
        if offset + BLOCK_SIZE > len(image):
            image.extend(b"\x00" * (offset + BLOCK_SIZE - len(image)))
        image[offset:offset + BLOCK_SIZE] = chunk.ljust(BLOCK_SIZE, b"\x00")[:BLOCK_SIZE]

    @classmethod
    def _place_hash(cls, image: bytearray, block: int, next_block: int) -> None:
        offset = cls.hash_offset(block)
        if offset + HASH_ENTRY_SIZE > len(image):
            image.extend(b"\x00" * (offset + HASH_ENTRY_SIZE - len(image)))
        record = bytearray(HASH_ENTRY_SIZE)
        record[0x14] = 0x80                                        # bloco em uso
        record[0x15:0x18] = next_block.to_bytes(3, "little")
        image[offset:offset + HASH_ENTRY_SIZE] = record
