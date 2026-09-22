"""Extração de imagens XDVDFS (Xbox e Xbox 360) com o extract-xiso."""

from __future__ import annotations

from pathlib import Path

from core.formats import Fmt
from core.stages.base import Artifact, Stage, StageContext, register


@register
class XisoExtract(Stage):
    id = "xiso"
    engine = "xiso"
    consumes = frozenset({Fmt.XISO})
    produces = Fmt.GAME_DIR
    cost = 2.0
    creates_directory = True
    label_key = "stage_xiso"

    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        return ctx.temp_path("_xiso")

    def build_command(self, artifact: Artifact, output: Path, ctx: StageContext) -> list[str]:
        return ["-d", str(output), "-x", str(artifact.path)]
