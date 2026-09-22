"""Conversão para CHD com o chdman (MAME).

Roadmap: motor não distribuído, resolvido pelo PATH.

O chdman tem subcomandos diferentes consoante a media:
  * createcd  -- folhas .cue/.gdi/.toc e imagens de CD
  * createdvd -- imagens de DVD (PS2, por exemplo)
Escolher mal produz um CHD que o emulador recusa, por isso o subcomando sai
directamente do formato detectado e não da extensão do ficheiro.

Licença: chdman é GPL-2.0-or-later (ver nota em rvz.py).
"""

from __future__ import annotations

import re
from pathlib import Path

from core.formats import Fmt
from core.stages.base import Artifact, Stage, StageContext, register

CHDMAN_PROGRESS = re.compile(r"(\d{1,3})(?:[.,]\d+)?\s*%")


@register
class ChdConvert(Stage):
    id = "chd"
    engine = "chdman"
    consumes = frozenset({Fmt.CD_IMAGE, Fmt.ISO9660})
    produces = Fmt.CHD
    progress_re = CHDMAN_PROGRESS
    cost = 3.0
    label_key = "stage_chd"

    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        return ctx.temp_path(".chd")

    def build_command(self, artifact: Artifact, output: Path, ctx: StageContext) -> list[str]:
        subcommand = "createcd" if artifact.fmt is Fmt.CD_IMAGE else "createdvd"
        return [subcommand, "-i", str(artifact.path), "-o", str(output), "-f"]
