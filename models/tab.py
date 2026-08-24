from dataclasses import dataclass, field
from pathlib import Path
from PySide6.QtWidgets import QListView, QCheckBox, QLabel, QProgressBar, QWidget
from models.process import ProcessState

@dataclass
class TabState:
    list_view: QListView | None = None
    items: dict[str, tuple[Path, QCheckBox]] = field(default_factory=dict)
    lbl_counter: QLabel | None = None
    lbl_percentage: QLabel | None = None
    progress: QProgressBar | None = None
    tasks_col: QWidget | None = None
    btns: dict[str, QWidget] = field(default_factory=dict)
    
    state: ProcessState = ProcessState.IDLE
    last_ui_update: float = 0.0
    last_log_update: float = 0.0