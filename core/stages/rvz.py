"""Conversão para RVZ (GameCube e Wii) com o DolphinTool.

Roadmap: o motor não é distribuído em bin/. A etapa só entra no planeamento
quando o `dolphin-tool` existir em bin/ ou no PATH, e é por isso que ela pode
ficar registada sem quebrar nada.

Licença: o DolphinTool é GPL-2.0-or-later. Distribuí-lo dentro de bin/ como
programa separado é aceitável, mas obriga a incluir o texto da licença e a
apontar para o código-fonte (a tela Sobre já o faz).
"""

from __future__ import annotations

import re
from pathlib import Path

from core.formats import Fmt
from core.stages.base import Artifact, Stage, StageContext, register

DOLPHIN_PROGRESS = re.compile(r"(\d{1,3})(?:[.,]\d+)?\s*%")


@register
class RvzConvert(Stage):
    id = "rvz"
    engine = "dolphin-tool"
    consumes = frozenset({Fmt.GC_ISO, Fmt.WII_ISO})
    produces = Fmt.RVZ
    progress_re = DOLPHIN_PROGRESS
    cost = 3.0
    label_key = "stage_rvz"

    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        return ctx.temp_path(".rvz")

    def build_command(self, artifact: Artifact, output: Path, ctx: StageContext) -> list[str]:
        options = ctx.options
        return [
            "convert",
            "-f", "rvz",
            "-c", str(options.get("rvz_compression", "zstd")),
            "-l", str(options.get("rvz_level", 5)),
            "-b", str(options.get("rvz_block_size", 131072)),
            "-i", str(artifact.path),
            "-o", str(output),
        ]
