"""Reconstrução de um Games on Demand na imagem XDVDFS que ele guarda.

Etapa nativa, como a do STFS. O que sai daqui é um .iso, que o planeador
entrega logo ao extract-xiso -- a cadeia `god -> xiso -> pasta -> zar` monta-se
sozinha, sem uma linha de código dedicada a essa combinação.

Reconstruir a imagem em vez de ler o sistema de ficheiros do Xbox é
deliberado: deixa a parte difícil com o extract-xiso, que já está no pipeline
e é testado por muita gente, e dá uma validação imediata -- se a geometria
estivesse errada, ele recusava a imagem à cabeça em vez de produzir uma pasta
com lixo lá dentro.
"""

from __future__ import annotations

from pathlib import Path

from core.errors import Cancelled, EngineFailed
from core.formats import Fmt
from core.stages.base import Artifact, NativeStage, StageContext, register


@register
class GodRebuild(NativeStage):
    id = "god"
    consumes = frozenset({Fmt.GOD})
    produces = Fmt.XISO
    cost = 3.0                        # escreve a imagem inteira em disco
    creates_directory = False
    label_key = "stage_god"

    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        return ctx.temp_path(".iso")

    def extract(self, artifact: Artifact, output: Path, ctx: StageContext,
                progress, should_cancel) -> None:
        from core.xbox.god import GodCancelled, GodError, GodPackage

        try:
            with GodPackage(artifact.path) as package:
                ctx.suggest_name(package.display_name)
                package.rebuild(
                    output, progress=progress, should_cancel=should_cancel,
                )
        except GodCancelled as exc:
            raise Cancelled() from exc
        except GodError as exc:
            raise EngineFailed(self.id, -1, str(exc)) from exc
