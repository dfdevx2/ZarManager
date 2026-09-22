"""Compressão para .zar com o ZArchive."""

from __future__ import annotations

from pathlib import Path

from core.formats import Fmt
from core.stages.base import Artifact, Stage, StageContext, register


@register
class ZarCompress(Stage):
    id = "zar"
    engine = "zar"
    consumes = frozenset({Fmt.GAME_DIR})
    produces = Fmt.ZAR
    cost = 3.0
    label_key = "stage_zar"

    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        return ctx.temp_path(".zar")

    def build_command(self, artifact: Artifact, output: Path, ctx: StageContext) -> list[str]:
        return [str(artifact.path), str(output)]
