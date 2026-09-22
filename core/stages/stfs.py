"""Extração de pacotes STFS (XBLA, DLC, actualizações de título).

Etapa nativa: não há binário a distribuir. As ferramentas que existem para
este formato -- Velocity, wxPirs, Horizon -- são gráficas, só para Windows,
ou ambas as coisas. O leitor vive em `core/xbox/stfs.py`.
"""

from __future__ import annotations

from pathlib import Path

from core.errors import Cancelled, EngineFailed
from core.formats import Fmt
from core.stages.base import Artifact, NativeStage, StageContext, register


@register
class StfsExtract(NativeStage):
    id = "stfs"
    consumes = frozenset({Fmt.STFS})
    produces = Fmt.GAME_DIR
    cost = 1.5
    creates_directory = True
    label_key = "stage_stfs"

    # A estrutura interna do pacote é a que o Xbox 360 espera: um DLC com uma
    # única pasta à cabeça não é um invólucro, é o caminho onde o conteúdo tem
    # de ficar.
    unwrap_payload = False

    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        return ctx.temp_path("_stfs")

    def extract(self, artifact: Artifact, output: Path, ctx: StageContext,
                progress, should_cancel) -> None:
        from core.xbox.stfs import StfsCancelled, StfsError, StfsPackage

        try:
            with StfsPackage(artifact.path) as package:
                ctx.suggest_name(package.display_name)
                package.extract_all(
                    output, progress=progress, should_cancel=should_cancel,
                )
        except StfsCancelled as exc:
            raise Cancelled() from exc
        except StfsError as exc:
            raise EngineFailed(self.id, -1, str(exc)) from exc
