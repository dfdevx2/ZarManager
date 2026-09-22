"""Extração de contentores comprimidos com o 7-Zip."""

from __future__ import annotations

import re
from pathlib import Path

from core.formats import Fmt
from core.stages.base import Artifact, Stage, StageContext, register

# O 7z com -bsp1 escreve "  42% 12 - nome" na mesma linha, reescrita com \r.
SEVENZIP_PROGRESS = re.compile(r"(\d{1,3})(?:[.,]\d+)?\s*%")


@register
class ArchiveExtract(Stage):
    id = "archive"
    engine = "7z"
    consumes = frozenset({Fmt.ARCHIVE})
    produces = Fmt.GAME_DIR
    # Código 1 = "Warning (Non fatal error(s))". Ficheiros da Scene disparam
    # isto constantemente (timestamps, atributos NTFS) e o resultado é válido.
    ok_codes = frozenset({0, 1})
    progress_re = SEVENZIP_PROGRESS
    cost = 1.0
    creates_directory = True
    label_key = "stage_archive"

    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        return ctx.temp_path("_unpacked")

    def build_command(self, artifact: Artifact, output: Path, ctx: StageContext) -> list[str]:
        # 'x' e não 'e': 'e' achata a estrutura de diretórios e corrompe
        # qualquer arquivo que contenha uma pasta de jogo em vez de uma ISO.
        return ["x", str(artifact.path), f"-o{output}", "-y", "-bsp1"]
