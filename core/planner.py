"""Planeador incremental de pipelines.

Em vez de uma sequência fixa de `if`, o planeador vê as etapas como um grafo
(`consumes -> produces`) e procura o caminho mais curto até ao formato alvo.
Encadeamentos como `zip -> gc_iso -> rvz` saem de graça, sem uma linha de
código dedicada a essa combinação.

É incremental de propósito: depois de cada etapa o item é reclassificado e o
alvo recalculado. Só depois de abrir um .7z é que se sabe o que estava lá
dentro.
"""

from __future__ import annotations

from collections import deque
from enum import Enum

from core.errors import NoRoute
from core.formats import Fmt
from core.stages import REGISTRY
from core.stages.base import Stage


class Mode(str, Enum):
    AUTO = "auto"
    EXTRACT_ARC = "extract_arc"
    EXTRACT_ISO = "extract"       # valor mantido por compatibilidade de config
    COMPRESS = "compress"


# Modo -> (formato alvo fixo, etapas permitidas). None = decidido pelo perfil.
MODE_RULES: dict[Mode, tuple[Fmt | None, frozenset[str] | None]] = {
    Mode.AUTO: (None, None),
    Mode.EXTRACT_ARC: (Fmt.GAME_DIR, frozenset({"archive"})),
    Mode.EXTRACT_ISO: (Fmt.GAME_DIR, frozenset({"archive", "xiso", "stfs", "god", "pkg"})),
    Mode.COMPRESS: (Fmt.ZAR, None),
}

# Perfis do modo automático: formato de entrada -> alvos, por ordem de
# preferência. O primeiro alvo com rota disponível ganha.
PROFILES: dict[Fmt, tuple[Fmt, ...]] = {
    Fmt.ARCHIVE: (Fmt.ZAR, Fmt.GAME_DIR),
    Fmt.GAME_DIR: (Fmt.ZAR,),
    Fmt.XISO: (Fmt.ZAR,),
    Fmt.STFS: (Fmt.ZAR, Fmt.GAME_DIR),
    Fmt.GOD: (Fmt.ZAR, Fmt.GAME_DIR),
    Fmt.GC_ISO: (Fmt.RVZ,),
    Fmt.WII_ISO: (Fmt.RVZ,),
    Fmt.ISO9660: (Fmt.CHD,),
    Fmt.CD_IMAGE: (Fmt.CHD,),
    Fmt.PKG_PS3: (Fmt.ZAR, Fmt.GAME_DIR),
    Fmt.PKG_PS4: (Fmt.ZAR, Fmt.GAME_DIR),
}


class Planner:
    def __init__(self, resolver, mode: Mode):
        self.resolver = resolver
        self.mode = mode
        fixed_target, allowed = MODE_RULES.get(mode, (None, None))
        self.fixed_target = fixed_target
        self.allowed = allowed
        self._stages = self._collect()

    # ------------------------------------------------------------ grafo
    def _collect(self) -> list[Stage]:
        stages = []
        for stage_id, cls in REGISTRY.items():
            if self.allowed is not None and stage_id not in self.allowed:
                continue
            stage = cls()
            if stage.available(self.resolver):
                stages.append(stage)
        return stages

    @property
    def available_ids(self) -> list[str]:
        return [stage.id for stage in self._stages]

    def missing_for(self, fmt: Fmt) -> list[str]:
        """Motores que fariam falta para processar este formato."""
        wanted = []
        for stage_id, cls in REGISTRY.items():
            if self.allowed is not None and stage_id not in self.allowed:
                continue
            if fmt in cls.consumes and not cls().available(self.resolver):
                wanted.append(cls.engine)
        return wanted

    def route(self, source: Fmt, target: Fmt) -> list[Stage]:
        """Caminho mais curto de `source` até `target`, em número de etapas."""
        if source is target:
            return []

        queue: deque[tuple[Fmt, list[Stage]]] = deque([(source, [])])
        seen = {source}

        while queue:
            current, path = queue.popleft()
            for stage in self._stages:
                if current not in stage.consumes:
                    continue
                produced = stage.produces
                if produced is target:
                    return [*path, stage]
                if produced not in seen:
                    seen.add(produced)
                    queue.append((produced, [*path, stage]))

        raise NoRoute(source.value, target.value)

    # --------------------------------------------------------- decisões
    def target_for(self, fmt: Fmt) -> Fmt | None:
        """Formato final desejado para um item com este formato."""
        if self.fixed_target is not None:
            return self.fixed_target

        for candidate in PROFILES.get(fmt, ()):
            if candidate is fmt:
                return candidate
            try:
                self.route(fmt, candidate)
                return candidate
            except NoRoute:
                continue
        return None

    def plan(self, fmt: Fmt) -> list[Stage]:
        """Cadeia prevista para um item. Usada para distribuir o peso do
        progresso; a cadeia real é recalculada a cada etapa."""
        target = self.target_for(fmt)
        if target is None or target is fmt:
            return []
        try:
            return self.route(fmt, target)
        except NoRoute:
            return []

    def next_stage(self, fmt: Fmt) -> Stage | None:
        """Próxima etapa a executar, ou None quando o item está concluído."""
        target = self.target_for(fmt)
        if target is None or target is fmt:
            return None
        route = self.route(fmt, target)
        return route[0] if route else None
