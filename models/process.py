from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path

class ProcessMode(Enum):
    AUTO = "auto"
    EXTRACT_ARC = "extract_arc"
    EXTRACT_ISO = "extract"
    COMPRESS = "compress"

class ProcessState(Enum):
    IDLE = auto()
    RUNNING = auto()
    PAUSED = auto()
    CANCELLING = auto()
    COMPLETED = auto()
    PARTIAL = auto()    # 🟠 Adicionado para sucesso parcial
    FAILED = auto()
    CANCELLED = auto()

class CollisionPolicy(Enum):
    CANCEL = auto()
    SKIP = auto()
    OVERWRITE = auto()  # 🔴 Política de overwrite agora explicitamente tratada

@dataclass
class ProcessRequest:
    mode: ProcessMode
    items: list[Path]
    target: Path
    keep_originals: bool
    collision_policy: CollisionPolicy

@dataclass
class ProcessResult:
    completed: int
    failed: int
    cancelled: int
    total: int