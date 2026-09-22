"""Construtor de pacotes GOD sintéticos, para os testes.

O que prova e o que não prova, tal como no stfs_builder:

PROVA que o leitor reconstrói a imagem byte a byte a partir dos ficheiros
partidos, que salta as tabelas de hash nos sítios certos, que atravessa a
fronteira entre data0000 e data0001, e -- o que aqui mais interessa -- que o
`probe()` encontra sozinho a geometria com que o pacote foi escrito e recusa
um pacote que não bate com nenhuma.

NÃO PROVA compatibilidade com um GOD de retalho. O escritor segue a mesma
leitura da especificação que o leitor, por isso um mal-entendido comum
passava despercebido. Para fechar essa dúvida é preciso um pacote real.
"""

from __future__ import annotations

import struct
from pathlib import Path

from core.xbox import god
from core.xbox.god import SECTOR, Layout


class GodBuilder:
    """Escreve um GOD a partir de uma imagem em memória e de uma geometria."""

    def __init__(self, layout: Layout, title_id: int = 0x4D5307D5,
                 display_name: str = "GOD de Teste", offset_big_endian: bool = True,
                 magic: bytes = b"CON "):
        self.layout = layout
        self.title_id = title_id
        self.display_name = display_name
        self.offset_big_endian = offset_big_endian
        self.magic = magic

    def build(self, destination: Path, image: bytes) -> Path:
        destination = Path(destination)
        lead = self.layout.lead_sectors

        stream = image[lead * SECTOR:]
        sectors = max(1, (len(stream) + SECTOR - 1) // SECTOR)

        parts: dict[int, bytearray] = {}
        for index in range(sectors):
            file_index, inner = divmod(index, god.SECTORS_PER_FILE)
            offset = self.layout.offset_in_file(inner)
            part = parts.setdefault(file_index, bytearray())
            if len(part) < offset + SECTOR:
                part.extend(b"\x00" * (offset + SECTOR - len(part)))
            chunk = stream[index * SECTOR:(index + 1) * SECTOR]
            part[offset:offset + SECTOR] = chunk.ljust(SECTOR, b"\x00")

        data_dir = destination.with_name(destination.name + ".data")
        data_dir.mkdir(parents=True, exist_ok=True)
        for file_index in sorted(parts):
            (data_dir / f"data{file_index:04d}").write_bytes(bytes(parts[file_index]))

        destination.write_bytes(self._header(sectors))
        return destination

    def _header(self, stream_sectors: int) -> bytes:
        head = bytearray(0x1000)
        head[0:4] = self.magic
        struct.pack_into(">I", head, god.OFF_CONTENT_TYPE, god.CONTENT_TYPE_GOD)
        struct.pack_into(">I", head, god.OFF_TITLE_ID, self.title_id)

        head[god.OFF_DESC_SIZE] = god.DESCRIPTOR_SIZE
        head[god.OFF_DEVICE_FEATURES] = (
            god.FEATURE_ENHANCED_GDF if self.layout.base != 0x2000 else 0x00
        )

        blocks = (stream_sectors + 1) // 2          # sectores de 0x800 -> blocos de 0x1000
        head[god.OFF_DATA_BLOCK_COUNT:god.OFF_DATA_BLOCK_COUNT + 3] = \
            blocks.to_bytes(3, "big")

        offset_value = self.layout.lead_sectors // 2
        head[god.OFF_DATA_BLOCK_OFFSET:god.OFF_DATA_BLOCK_OFFSET + 3] = \
            offset_value.to_bytes(3, "big" if self.offset_big_endian else "little")

        name = self.display_name.encode("utf-16-be")[:0x7E]
        head[god.OFF_DISPLAY_NAME:god.OFF_DISPLAY_NAME + len(name)] = name
        return bytes(head)


def make_xdvdfs_image(sectors: int, seed: bytes = b"\xa5") -> bytes:
    """Imagem XDVDFS plausível: ruído previsível com a assinatura no sítio."""
    image = bytearray((seed * SECTOR) * sectors)
    for index in range(sectors):
        # Marca cada sector, para que uma troca de posições seja visível.
        struct.pack_into(">I", image, index * SECTOR, index)

    magic_at = 0x10000
    if len(image) >= magic_at + 0x20:
        image[magic_at:magic_at + len(god.XDVDFS_MAGIC)] = god.XDVDFS_MAGIC
    return bytes(image)
