from dataclasses import dataclass, field
from pathlib import Path
from models.process import ProcessState

@dataclass
class TabState:
    list_view: ft.ListView | None = None
    items: dict[str, tuple[Path, ft.Checkbox]] = field(default_factory=dict)
    lbl_counter: ft.Text | None = None
    lbl_percentage: ft.Text | None = None
    progress: ft.ProgressBar | None = None
    tasks_col: ft.Column | None = None
    btns: dict[str, ft.Control] = field(default_factory=dict)
    
    state: ProcessState = ProcessState.IDLE
    last_ui_update: float = 0.0
    last_log_update: float = 0.0