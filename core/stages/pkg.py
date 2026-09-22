"""Extração de pacotes PKG (PlayStation 3 e PlayStation 4).

EXPERIMENTAL -- ler antes de activar:

* PS4: o shadPS4 passou a ler .zar nativamente (0.17.0), por isso a cadeia
  PKG -> pasta -> .zar tem destino: o emulador abre o resultado. O que ele
  não abre é um .pkg de retalho cifrado -- precisa do jogo já descriptografado
  em pasta. Ferramentas como o PkgTool.Core (LibOrbisPkg) tratam fPKG e debug,
  não retail. Um .pkg de retalho falha na extração, que é o comportamento
  certo: mais vale falhar do que entregar um .zar que não abre.
* PS3: o RPCS3 instala ficheiros .pkg directamente e não lê .zar. Extrair e
  comprimir aqui serve para arrumar a biblioteca, não para jogar.

A etapa fica registada para que a arquitetura esteja pronta, mas sem o motor
presente o planeador ignora-a.

Campos do cabeçalho PS4 (big endian, herdado da PS3), confirmados na
psdevwiki e úteis para diagnóstico: 0x00 magic, 0x40 content_id (0x24 bytes),
0x70 drm_type, 0x74 content_type, 0x78 content_flags.
"""

from __future__ import annotations

from pathlib import Path

from core.formats import Fmt
from core.stages.base import Artifact, Stage, StageContext, register


@register
class PkgExtract(Stage):
    id = "pkg"
    engine = "pkg"
    consumes = frozenset({Fmt.PKG_PS3, Fmt.PKG_PS4})
    produces = Fmt.GAME_DIR
    cost = 2.0
    creates_directory = True
    label_key = "stage_pkg"
    experimental = True

    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        return ctx.temp_path("_pkg")

    def build_command(self, artifact: Artifact, output: Path, ctx: StageContext) -> list[str]:
        template = ctx.options.get("pkg_command")
        if template:
            return [
                part.replace("{input}", str(artifact.path)).replace("{output}", str(output))
                for part in template
            ]
        return ["extract", str(artifact.path), str(output)]
