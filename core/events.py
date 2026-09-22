"""Eventos tipados emitidos pelo core.

O core não conhece idiomas. Em vez de строк prontas, emite uma chave de
tradução e argumentos; a UI resolve com locales.py. Isto elimina o bloco de
`msg.replace(...)` que existia no emit_log e, sobretudo, deixa de ser preciso
chamar `self.parent().get_text()` a partir de uma worker thread -- ou seja,
deixa de haver acesso a QWidgets fora da thread da GUI.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Level(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class ItemState(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    DONE = "done"
    SKIPPED = "skipped"
    FAILED = "failed"
    CANCELLED = "cancelled"

    @property
    def is_final(self) -> bool:
        return self is not ItemState.QUEUED and self is not ItemState.RUNNING


@dataclass(frozen=True)
class Event:
    """Mensagem de log independente de idioma."""

    key: str
    args: dict = field(default_factory=dict)
    level: Level = Level.INFO


@dataclass(frozen=True)
class ItemStatus:
    """Estado de um item da fila, como a lista da UI o desenha."""

    name: str
    state: ItemState
    stage_id: str | None = None      # "archive", "xiso", "zar", "rvz", ...
    percent: float | None = None     # 0.0 - 1.0 dentro da etapa atual
    detail: str | None = None        # última linha do motor (não traduzível)
    error_key: str | None = None
    error_args: dict = field(default_factory=dict)


@dataclass(frozen=True)
class Progress:
    """Progresso global do lote."""

    done: int
    total: int
    ratio: float


@dataclass
class JobResult:
    completed: int = 0
    failed: int = 0
    skipped: int = 0
    cancelled: int = 0
    total: int = 0

    @property
    def state_key(self) -> str:
        if self.cancelled:
            return "cancelled"
        if self.failed and self.completed:
            return "partial"
        if self.failed:
            return "failed"
        return "completed"
