"""Núcleo do ZarManager: sem qualquer dependência de Qt.

Isto é deliberado -- permite testar o pipeline inteiro sem interface, e é o
que torna possível validar a lógica em CI sem um servidor gráfico.
"""

from core.engines import ENGINES, EngineResolver
from core.errors import Cancelled, CoreError, ElevationRequired, EngineFailed, EngineMissing, NoRoute
from core.events import Event, ItemState, ItemStatus, JobResult, Level, Progress
from core.formats import Fmt, sniff
from core.job import JobRequest, JobRunner
from core.planner import Mode, Planner

__all__ = [
    "ENGINES", "EngineResolver", "Cancelled", "CoreError", "ElevationRequired",
    "EngineFailed", "EngineMissing", "NoRoute", "Event", "ItemState", "ItemStatus",
    "JobResult", "Level", "Progress", "Fmt", "sniff", "JobRequest", "JobRunner",
    "Mode", "Planner",
]
