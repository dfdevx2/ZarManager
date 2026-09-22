"""Tela principal de trabalho.

Mudança estrutural face ao MainController antigo: havia quatro abas, cada uma
com os seus próprios campos de diretório, a sua própria lista e a sua própria
thread -- quatro jobs podiam correr ao mesmo tempo sobre a mesma pasta. Agora
há um painel de diretórios partilhado, uma lista e uma fila única; as pílulas
escolhem apenas o modo.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QTimer, Signal
from PySide6.QtGui import QTextCursor
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QLineEdit, QProgressBar, QTextEdit, QVBoxLayout, QWidget,
)

from core.events import ItemState, Level
from core.job import JobRequest
from core.planner import Mode
from core.workspace import CollisionResolver
from services.file_service import FileService
from services.sound import Sfx
from ui.dialogs import DialogManager
from ui.widgets.card import Card, action_button, separator
from ui.widgets.item_list import ItemList
from ui.worker import JobThread

CONSOLE_LIMIT = 400

_STATE_KEY = {
    ItemState.QUEUED: "state_queued",
    ItemState.RUNNING: "state_running",
    ItemState.DONE: "state_done",
    ItemState.FAILED: "state_failed",
    ItemState.SKIPPED: "state_skipped",
    ItemState.CANCELLED: "state_cancelled",
}


class WorkspaceView(QWidget):
    busyChanged = Signal(bool)

    def __init__(self, cfg, translator, sound, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.t = translator
        self.sound = sound
        self.mode = Mode.AUTO
        self.job: JobThread | None = None
        self._paused = False

        self._build()
        self.retranslate()
        QTimer.singleShot(0, self.refresh_items)

    # --------------------------------------------------------------- layout
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(14)

        self.lbl_tip = QLabel()
        self.lbl_tip.setProperty("role", "muted")

        # --- diretórios -------------------------------------------------
        self.card_dirs = Card()
        self.txt_source = QLineEdit(self.cfg.get("source_dir") or "")
        self.txt_target = QLineEdit(self.cfg.get("target_dir") or "")
        self.lbl_source = QLabel()
        self.lbl_target = QLabel()
        self.btn_source = action_button("", "ghost")
        self.btn_target = action_button("", "ghost")
        self.lbl_dir_warning = QLabel()
        self.lbl_dir_warning.setProperty("role", "warning")
        self.lbl_dir_warning.setWordWrap(True)

        for label, field, button, key in (
            (self.lbl_source, self.txt_source, self.btn_source, "source_dir"),
            (self.lbl_target, self.txt_target, self.btn_target, "target_dir"),
        ):
            field.setReadOnly(True)
            label.setFixedWidth(76)
            button.clicked.connect(lambda _checked=False, k=key: self._pick(k))
            row = QHBoxLayout()
            row.setSpacing(10)
            row.addWidget(label)
            row.addWidget(field, 1)
            row.addWidget(button)
            self.card_dirs.add_layout(row)

        self.card_dirs.add(self.lbl_dir_warning)

        # --- itens -------------------------------------------------------
        self.lbl_items = QLabel()
        self.lbl_items.setProperty("role", "section")
        self.lbl_selected = QLabel()
        self.lbl_selected.setProperty("role", "muted")
        self.btn_invert = action_button("", "quiet")
        self.btn_refresh = action_button("", "quiet")
        self.btn_invert.clicked.connect(lambda: self.items.toggle_all())
        self.btn_refresh.clicked.connect(self.refresh_items)

        header = QHBoxLayout()
        header.addWidget(self.lbl_items)
        header.addSpacing(10)
        header.addWidget(self.lbl_selected)
        header.addStretch()
        header.addWidget(self.btn_refresh)
        header.addWidget(self.btn_invert)

        self.items = ItemList()
        self.items.selectionCountChanged.connect(self._on_selection_changed)

        # --- progresso e controlos --------------------------------------
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.lbl_counter = QLabel()
        self.lbl_counter.setProperty("role", "muted")
        self.lbl_percent = QLabel("0%")
        self.lbl_percent.setProperty("role", "metric")

        self.btn_start = action_button("", "primary")
        self.btn_pause = action_button("", "ghost")
        self.btn_cancel = action_button("", "danger")
        self.btn_start.setMinimumWidth(150)
        self.btn_pause.setEnabled(False)
        self.btn_cancel.setEnabled(False)
        self.btn_start.clicked.connect(self.start_job)
        self.btn_pause.clicked.connect(self.toggle_pause)
        self.btn_cancel.clicked.connect(self.cancel_job)

        controls = QHBoxLayout()
        controls.setSpacing(10)
        controls.addWidget(self.lbl_counter)
        controls.addStretch()
        controls.addWidget(self.lbl_percent)
        controls.addSpacing(16)
        controls.addWidget(self.btn_pause)
        controls.addWidget(self.btn_cancel)
        controls.addWidget(self.btn_start)

        # --- consola -----------------------------------------------------
        self.lbl_console = QLabel()
        self.lbl_console.setProperty("role", "muted")
        self.btn_console = action_button("", "quiet")
        self.btn_clear = action_button("", "quiet")
        self.btn_console.clicked.connect(self._toggle_console)
        self.btn_clear.clicked.connect(lambda: self.console.clear())

        console_header = QHBoxLayout()
        console_header.addWidget(self.lbl_console)
        console_header.addStretch()
        console_header.addWidget(self.btn_clear)
        console_header.addWidget(self.btn_console)

        self.console = QTextEdit()
        self.console.setObjectName("Console")
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(150)
        self.console.setVisible(False)

        outer.addWidget(self.lbl_tip)
        outer.addWidget(self.card_dirs)
        outer.addLayout(header)
        outer.addWidget(self.items, 1)
        outer.addWidget(self.progress)
        outer.addLayout(controls)
        outer.addWidget(separator())
        outer.addLayout(console_header)
        outer.addWidget(self.console)

    # ----------------------------------------------------------------- API
    def apply_tokens(self, tokens) -> None:
        self.items.apply_tokens(tokens)
        self._tokens = tokens

    def set_mode(self, mode: Mode) -> None:
        if mode == self.mode:
            return
        self.mode = mode
        self.retranslate()
        self.refresh_items()

    @property
    def busy(self) -> bool:
        return self.job is not None and self.job.isRunning()

    def request_cancel_for_exit(self) -> None:
        if self.job is not None:
            self.job.cancel()

    # ------------------------------------------------------------ diretórios
    def _pick(self, key: str) -> None:
        field = self.txt_source if key == "source_dir" else self.txt_target
        chosen = DialogManager.select_directory(self, self.t("btn_browse"), field.text())
        if not chosen:
            return
        self.cfg.set(key, chosen)
        field.setText(chosen)
        self._check_directories()
        if key == "source_dir":
            self.refresh_items()

    def _check_directories(self) -> None:
        warnings = FileService.validate_directories(self.txt_source.text(), self.txt_target.text())
        self.lbl_dir_warning.setText(" ".join(self.t(key) for key in warnings))

    def refresh_items(self) -> None:
        if self.busy:
            return
        self.txt_source.setText(self.cfg.get("source_dir") or "")
        self.txt_target.setText(self.cfg.get("target_dir") or "")
        self._check_directories()

        source = self.txt_source.text()
        message = self.t("msg_no_files") if source else self.t("msg_no_source")
        paths = FileService.find_processable_files(source, self.mode, self.txt_target.text())
        self.items.populate(paths, message)
        self.progress.setValue(0)
        self.lbl_percent.setText("0%")

    def _on_selection_changed(self, checked: int, total: int) -> None:
        self.lbl_selected.setText(self.t("lbl_selected", checked=checked, total=total))
        self.btn_start.setEnabled(checked > 0 and not self.busy)

    # ----------------------------------------------------------------- job
    def start_job(self) -> None:
        if self.busy:
            DialogManager.show_warning(self, self.t("app_title"), self.t("msg_err_running"))
            return

        target = self.cfg.get("target_dir")
        if not target:
            DialogManager.show_warning(self, self.t("app_title"), self.t("msg_err_target"))
            return

        selected = self.items.checked_paths()
        if not selected:
            DialogManager.show_warning(self, self.t("app_title"), self.t("msg_err_select"))
            return

        policy = self._resolve_policy(selected, Path(target))
        if policy is None:
            return

        keep = self._resolve_keep_originals()
        if keep is None:
            return

        request = JobRequest(
            items=selected,
            target=Path(target),
            mode=self.mode,
            keep_originals=keep,
            policy=policy,
            workers=self.cfg.get_int("workers", 1, 16),
        )

        self.items.reset_status()
        self.items.set_locked(True)
        self.progress.setValue(0)
        self.lbl_percent.setText("0%")
        self._paused = False

        self.job = JobThread(request, self)
        self.job.event_signal.connect(self._on_event)
        self.job.progress_signal.connect(self._on_progress)
        self.job.item_signal.connect(self._on_item)
        self.job.finished_signal.connect(self._on_finished)
        self.job.engine_missing_signal.connect(self._on_engine_missing)
        self.job.env_error_signal.connect(self._on_env_error)
        self.job.start()

        self._set_busy(True)

    def _resolve_policy(self, selected: list[Path], target: Path) -> str | None:
        configured = (self.cfg.get("collision_policy") or "ASK").upper()
        if configured != "ASK":
            return configured

        conflicts = [
            path for path in selected
            if any((target / f"{path.stem}{suffix}").exists()
                   for suffix in ("", ".zar", ".chd", ".rvz"))
        ]
        if not conflicts:
            return CollisionResolver.RENAME

        choice = DialogManager.ask_custom(
            self,
            self.t("dlg_collision_title"),
            self.t("dlg_collision_desc"),
            [
                ("cancel", self.t("btn_cancel")),
                (CollisionResolver.SKIP, self.t("btn_skip_existing")),
                (CollisionResolver.OVERWRITE, self.t("btn_overwrite")),
                (CollisionResolver.RENAME, self.t("btn_rename")),
            ],
        )
        return None if choice in (None, "cancel") else choice

    def _resolve_keep_originals(self) -> bool | None:
        if self.cfg.get_bool("keep_originals"):
            return True
        choice = DialogManager.ask_custom(
            self,
            self.t("dlg_delete_title"),
            self.t("dlg_delete_desc"),
            [("keep", self.t("btn_keep_originals")), ("delete", self.t("btn_delete_originals"))],
        )
        if choice is None:
            return None
        return choice == "keep"

    def toggle_pause(self) -> None:
        if self.job is None:
            return
        self._paused = self.job.toggle_pause()
        self.btn_pause.setText(self.t("btn_resume") if self._paused else self.t("btn_pause"))

    def cancel_job(self) -> None:
        if self.job is None:
            return
        self.job.cancel()
        self.btn_cancel.setEnabled(False)
        self.btn_pause.setEnabled(False)

    def _set_busy(self, busy: bool) -> None:
        self.btn_start.setEnabled(not busy and self.items.checked_count() > 0)
        self.btn_pause.setEnabled(busy)
        self.btn_cancel.setEnabled(busy)
        self.btn_source.setEnabled(not busy)
        self.btn_target.setEnabled(not busy)
        self.btn_invert.setEnabled(not busy)
        self.btn_refresh.setEnabled(not busy)
        if not busy:
            self.btn_pause.setText(self.t("btn_pause"))
        self.busyChanged.emit(busy)

    # -------------------------------------------------------------- sinais
    def _on_event(self, event) -> None:
        self.log(self.t.event(event), event.level)

    def _on_progress(self, progress) -> None:
        percent = int(progress.ratio * 100)
        self.progress.setValue(percent)
        self.lbl_percent.setText(f"{percent}%")
        self.lbl_counter.setText(
            self.t("lbl_progress", done=progress.done, total=progress.total)
        )

    def _on_item(self, status) -> None:
        if status.state is ItemState.RUNNING and status.stage_id:
            label = self.t(f"stage_{status.stage_id}", fallback=self.t("state_running"))
        else:
            label = self.t(_STATE_KEY.get(status.state, "state_queued"))

        subtitle = status.detail if status.detail else None
        self.items.update_status(status.name, label, status.state, status.percent, subtitle)

    def _on_finished(self, result) -> None:
        self.job = None
        self.items.set_locked(False)
        self._set_busy(False)

        # A lista só é repovoada DEPOIS do diálogo: caso contrário o estado
        # final de cada item ("Concluído", "Falhou") desaparecia antes de o
        # utilizador o conseguir ler.
        outcome = result.state_key
        if outcome == "completed" and result.completed:
            self.sound.play(Sfx.SUCCESS)
            DialogManager.show_info(
                self, self.t("dlg_done_title"),
                self.t("dlg_done_desc", completed=result.completed),
            )
        elif outcome == "partial":
            self.sound.play(Sfx.ERROR)
            DialogManager.show_warning(
                self, self.t("dlg_partial_title"),
                self.t("dlg_partial_desc", completed=result.completed, failed=result.failed),
            )
        elif outcome == "failed":
            self.sound.play(Sfx.ERROR)
            DialogManager.show_error(self, self.t("dlg_failed_title"), self.t("dlg_failed_desc"))
        elif outcome == "cancelled":
            DialogManager.show_info(
                self, self.t("dlg_cancelled_title"), self.t("dlg_cancelled_desc")
            )

        self.refresh_items()

    def _on_engine_missing(self, engine_id: str) -> None:
        self.sound.play(Sfx.ERROR)
        DialogManager.show_error(
            self, self.t("av_alert_title"), self.t("av_alert_msg", engine=engine_id)
        )

    def _on_env_error(self, missing: list) -> None:
        self.sound.play(Sfx.ERROR)
        DialogManager.show_error(
            self, self.t("dlg_env_title"), self.t("dlg_env_desc", engines=", ".join(missing))
        )

    # ------------------------------------------------------------- consola
    def log(self, message: str, level=Level.INFO) -> None:
        colour = {
            Level.ERROR: "#EF5350",
            Level.WARNING: "#FFB300",
            Level.SUCCESS: "#66BB6A",
        }.get(level, "#B9BDC7")

        safe = message.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        self.console.append(f"<span style='color:{colour};'>{safe}</span>")

        if self.console.document().blockCount() > CONSOLE_LIMIT:
            cursor = self.console.textCursor()
            cursor.movePosition(QTextCursor.MoveOperation.Start)
            cursor.select(QTextCursor.SelectionType.BlockUnderCursor)
            cursor.removeSelectedText()

        bar = self.console.verticalScrollBar()
        bar.setValue(bar.maximum())

    def _toggle_console(self) -> None:
        self.console.setVisible(not self.console.isVisible())
        self.btn_console.setText(
            "▴" if self.console.isVisible() else "▾"
        )

    # -------------------------------------------------------------- textos
    def retranslate(self) -> None:
        tips = {
            Mode.AUTO: "tip_auto",
            Mode.EXTRACT_ARC: "tip_extract_arc",
            Mode.EXTRACT_ISO: "tip_extract",
            Mode.COMPRESS: "tip_compress",
        }
        self.lbl_tip.setText(self.t(tips.get(self.mode, "tip_auto")))
        self.lbl_source.setText(self.t("lbl_source"))
        self.lbl_target.setText(self.t("lbl_target"))
        self.btn_source.setText(self.t("btn_browse"))
        self.btn_target.setText(self.t("btn_browse"))
        self.lbl_items.setText(self.t("lbl_items"))
        self.btn_invert.setText(self.t("btn_invert"))
        self.btn_refresh.setText(self.t("btn_refresh"))
        self.btn_start.setText(self.t("btn_start"))
        self.btn_pause.setText(self.t("btn_resume") if self._paused else self.t("btn_pause"))
        self.btn_cancel.setText(self.t("btn_cancel"))
        self.lbl_console.setText(self.t("lbl_console"))
        self.btn_clear.setText(self.t("btn_clear_console"))
        self.btn_console.setText("▴" if self.console.isVisible() else "▾")
        self._on_selection_changed(self.items.checked_count(), self.items.selectable_count())
