"""Importar este pacote regista todas as etapas disponíveis."""

from core.stages import archive, chd, god, pkg, rvz, stfs, xiso, zar  # noqa: F401
from core.stages.base import (  # noqa: F401
    REGISTRY,
    Artifact,
    NativeStage,
    Stage,
    StageContext,
    all_stages,
    register,
)

__all__ = [
    "REGISTRY", "Artifact", "NativeStage", "Stage", "StageContext",
    "all_stages", "register",
]
