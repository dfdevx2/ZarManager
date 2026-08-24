import os
import shutil
import platform
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QProgressBar, QTextEdit, QGroupBox, QComboBox, QSlider, QCheckBox
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QUrl, QTimer
from PySide6.QtGui import QFont, QDesktopServices

import locales
from models.process import ProcessMode, ProcessState, CollisionPolicy, ProcessRequest, ProcessResult
from models.tab import TabState
from services.logging_service import logger
from services.file_service import FileService
from services.update_service import UpdateService
from services.sound_service import SoundService
from ui.dialogs import DialogManager
from core import ZarManagerCore

GITHUB_REPO_URL = "https://github.com/dfdevx2/ZarManager"

class CoreWorkerThread(QThread):
    log_signal = Signal(str, str)
    progress_signal = Signal(object, int, int, float)
    status_signal = Signal(object, str, str)
    finished_signal = Signal(object, object)

    def __init__(self, request: ProcessRequest, workers: int, get_text_cb, parent=None):
        super().__init__(parent)
        self.req = request
        self.workers = workers
        self.get_text = get_text_cb
        self.manager = None

    def run(self):
        self.manager = ZarManagerCore(
            self.req.items, str(self.req.target), self.workers, self.req.mode.value, self.req.keep_originals, 
            lambda m: self.log_signal.emit(m, "INFO"),
            lambda c, t, r: self.progress_signal.emit(self.req.mode, c, t, r),
            lambda i, s: self.status_signal.emit(self.req.mode, i, s)
        )
        
        try:
            if hasattr(self.manager, 'verify_environment'):
                verify_res = self.manager.verify_environment()
                if isinstance(verify_res, tuple):
                    success, reason = verify_res
                else:
                    success = bool(verify_res)
                    reason = self.get_text("err_env_min") or "Environment does not meet minimum requirements."
            else:
                success, reason = True, ""

            if not success:
                t_crit = self.get_text("log_crit_env") or "[CRITICAL ERROR]"
                self.log_signal.emit(f"{t_crit} {reason}", "ERROR")
                self.finished_signal.emit(self.req.mode, ProcessState.FAILED)
                return
            
            if self.req.collision_policy == CollisionPolicy.OVERWRITE:
                t_over = self.get_text("log_over_act") or "[SYSTEM] Overwrite policy active. Cleaning conflicts in target..."
                self.log_signal.emit(t_over, "WARNING")
                for item in self.req.items:
                    name = item.stem + ".zar" if self.req.mode in [ProcessMode.AUTO, ProcessMode.COMPRESS] else item.name
                    target_file = self.req.target / name
                    if target_file.exists():
                        try:
                            if target_file.is_file():
                                target_file.unlink()
                            elif target_file.is_dir():
                                shutil.rmtree(target_file)
                            t_rem = self.get_text("log_rem_prev") or "[SYSTEM] Removed previous file:"
                            self.log_signal.emit(f"{t_rem} {name}", "INFO")
                        except Exception as e:
                            t_err_over = self.get_text("log_err_over") or "[ERROR] Failed to overwrite"
                            self.log_signal.emit(f"{t_err_over} {name}: {e}", "ERROR")
            
            self.manager.start_processing()
            
            stats = self.manager.get_completion_stats() if hasattr(self.manager, 'get_completion_stats') else {"failed": 0, "completed": len(self.req.items), "cancelled": 0, "total": len(self.req.items)}
            res = ProcessResult(**stats)
            
            if res.cancelled > 0 or (hasattr(self.manager, 'is_cancelled') and self.manager.is_cancelled()):
                self.finished_signal.emit(self.req.mode, ProcessState.CANCELLED)
            elif res.failed > 0 and res.completed > 0:
                self.finished_signal.emit(self.req.mode, ProcessState.PARTIAL)
            elif res.failed > 0:
                self.finished_signal.emit(self.req.mode, ProcessState.FAILED)
            else:
                self.finished_signal.emit(self.req.mode, ProcessState.COMPLETED)
                
        except Exception as e:
            logger.error("Exception in worker", exc_info=True)
            t_fatal = self.get_text("log_fatal") or "[FATAL] Engine error:"
            self.log_signal.emit(f"{t_fatal} {e}. Check logs.", "ERROR")
            self.finished_signal.emit(self.req.mode, ProcessState.FAILED)


class QtTabState:
    def __init__(self, title_key: str, tip_key: str):
        self.title_key = title_key
        self.tip_key = tip_key
        self.list_view: QListWidget = None
        self.items: dict = {} 
        self.state: ProcessState = ProcessState.IDLE
        self.lbl_title: QLabel = None
        self.lbl_tip: QLabel = None
        self.grp_dir: QGroupBox = None
        self.btn_src: QPushButton = None
        self.btn_tgt: QPushButton = None
        self.lbl_items_header: QLabel = None
        self.btn_invert: QPushButton = None
        self.lbl_counter: QLabel = None
        self.lbl_percentage: QLabel = None
        self.progress: QProgressBar = None
        self.txt_source: QLineEdit = None
        self.txt_target: QLineEdit = None
        self.btn_start: QPushButton = None
        self.btn_pause: QPushButton = None
        self.btn_cancel: QPushButton = None


class MainController(QWidget):
    def __init__(self, cfg, app_version: str, apply_theme_cb):
        super().__init__()
        self.cfg = cfg
        self.app_version = app_version
        self.apply_theme_cb = apply_theme_cb
        
        self.tab_data: dict[ProcessMode, QtTabState] = {
            ProcessMode.AUTO: QtTabState("tab_auto", "tip_auto"),
            ProcessMode.EXTRACT_ARC: QtTabState("tab_extract_arc", "tip_extract_arc"),
            ProcessMode.EXTRACT_ISO: QtTabState("tab_extract", "tip_extract"),
            ProcessMode.COMPRESS: QtTabState("tab_compress", "tip_compress")
        }
        
        self.active_threads: dict[ProcessMode, CoreWorkerThread] = {}
        self._build_ui()
        self._populate_initial_data()
        self.retranslate_ui()

    def get_text(self, key: str) -> str:
        return locales.get_text(self.cfg.get("language") or "en", key)

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        
        self.tabs = QTabWidget()
        self.tabs.addTab(self._build_action_tab(ProcessMode.AUTO), "")
        self.tabs.addTab(self._build_action_tab(ProcessMode.EXTRACT_ARC), "")
        self.tabs.addTab(self._build_action_tab(ProcessMode.EXTRACT_ISO), "")
        self.tabs.addTab(self._build_action_tab(ProcessMode.COMPRESS), "")
        
        self.settings_idx = self.tabs.addTab(self._build_settings(), "")
        self.about_idx = self.tabs.addTab(self._build_about(), "")
        
        self.lbl_console = QLabel()
        font_bold = QFont()
        font_bold.setBold(True)
        self.lbl_console.setFont(font_bold)
        
        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setMaximumHeight(150)
        self.console.setStyleSheet("font-family: monospace; background-color: #1a1a1a; color: #d4d4d4; border: 1px solid #333;")
        
        main_layout.addWidget(self.tabs)
        main_layout.addWidget(self.lbl_console)
        main_layout.addWidget(self.console)

    def _build_action_tab(self, mode: ProcessMode) -> QWidget:
        tab_widget = QWidget()
        layout = QVBoxLayout(tab_widget)
        ui = self.tab_data[mode]
        
        ui.lbl_title = QLabel()
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        ui.lbl_title.setFont(font)
        
        ui.lbl_tip = QLabel()
        ui.lbl_tip.setStyleSheet("color: gray;")
        
        ui.grp_dir = QGroupBox()
        dir_layout = QVBoxLayout(ui.grp_dir)
        
        src_row = QHBoxLayout()
        ui.txt_source = QLineEdit(self.cfg.get("source_dir") or "")
        ui.txt_source.setReadOnly(True)
        ui.btn_src = QPushButton()
        ui.btn_src.clicked.connect(lambda: self._select_dir(mode, "source", ui.txt_source))
        src_row.addWidget(ui.txt_source)
        src_row.addWidget(ui.btn_src)
        
        tgt_row = QHBoxLayout()
        ui.txt_target = QLineEdit(self.cfg.get("target_dir") or "")
        ui.txt_target.setReadOnly(True)
        ui.btn_tgt = QPushButton()
        ui.btn_tgt.clicked.connect(lambda: self._select_dir(mode, "target", ui.txt_target))
        tgt_row.addWidget(ui.txt_target)
        tgt_row.addWidget(ui.btn_tgt)
        
        dir_layout.addLayout(src_row)
        dir_layout.addLayout(tgt_row)
        
        files_header = QHBoxLayout()
        ui.lbl_items_header = QLabel()
        ui.btn_invert = QPushButton()
        ui.btn_invert.clicked.connect(lambda: self._toggle_all_selections(mode))
        files_header.addWidget(ui.lbl_items_header)
        files_header.addStretch()
        files_header.addWidget(ui.btn_invert)
        
        ui.list_view = QListWidget()
        
        prog_row = QHBoxLayout()
        ui.lbl_counter = QLabel("0 / 0")
        ui.lbl_percentage = QLabel("0%")
        ui.progress = QProgressBar()
        ui.progress.setRange(0, 100)
        ui.progress.setValue(0)
        
        prog_row.addWidget(ui.lbl_counter)
        prog_row.addStretch()
        prog_row.addWidget(ui.lbl_percentage)
        
        btn_row = QHBoxLayout()
        btn_row.addStretch()
        
        ui.btn_start = QPushButton()
        ui.btn_start.setMinimumHeight(40)
        ui.btn_start.setStyleSheet("font-weight: bold;") 
        ui.btn_start.clicked.connect(lambda: self._start_pipeline(mode))
        
        ui.btn_pause = QPushButton()
        ui.btn_pause.setMinimumHeight(40)
        ui.btn_pause.setEnabled(False)
        ui.btn_pause.clicked.connect(lambda: self._toggle_pause(mode))
        
        ui.btn_cancel = QPushButton()
        ui.btn_cancel.setMinimumHeight(40)
        ui.btn_cancel.setEnabled(False)
        ui.btn_cancel.setStyleSheet("background-color: #b71c1c; color: white; font-weight: bold;")
        ui.btn_cancel.clicked.connect(lambda: self._request_cancel(mode))
        
        btn_row.addWidget(ui.btn_start)
        btn_row.addWidget(ui.btn_pause)
        btn_row.addWidget(ui.btn_cancel)
        
        layout.addWidget(ui.lbl_title)
        layout.addWidget(ui.lbl_tip)
        layout.addWidget(ui.grp_dir)
        layout.addLayout(files_header)
        layout.addWidget(ui.list_view)
        layout.addLayout(prog_row)
        layout.addWidget(ui.progress)
        layout.addLayout(btn_row)
        
        return tab_widget

    def _build_settings(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(15)
        
        self.lbl_set_title = QLabel()
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.lbl_set_title.setFont(font)
        layout.addWidget(self.lbl_set_title)
        
        lang_layout = QHBoxLayout()
        self.lbl_set_lang = QLabel()
        self.cb_lang = QComboBox()
        self.cb_lang.addItems(["pt-br", "en"])
        idx_lang = self.cb_lang.findText(self.cfg.get("language") or "en")
        if idx_lang >= 0: self.cb_lang.setCurrentIndex(idx_lang)
        
        def on_lang_change(txt):
            self.cfg.set("language", txt)
            self.retranslate_ui() 
            
        self.cb_lang.currentTextChanged.connect(on_lang_change)
        lang_layout.addWidget(self.lbl_set_lang)
        lang_layout.addWidget(self.cb_lang)
        lang_layout.addStretch()
        
        theme_layout = QHBoxLayout()
        self.lbl_set_theme = QLabel()
        self.cb_theme = QComboBox()
        self.cb_theme.addItems(["Sistema", "Preto", "Branco", "Steam", "Xbox"])
        idx_theme = self.cb_theme.findText(self.cfg.get("theme") or "Sistema")
        if idx_theme >= 0: self.cb_theme.setCurrentIndex(idx_theme)
        
        def on_theme_change(txt):
            self.cfg.set("theme", txt)
            self.apply_theme_cb() 
            
        self.cb_theme.currentTextChanged.connect(on_theme_change)
        theme_layout.addWidget(self.lbl_set_theme)
        theme_layout.addWidget(self.cb_theme)
        theme_layout.addStretch()
        
        workers_val = int(self.cfg.get("workers") or 4)
        self.lbl_set_workers = QLabel()
        
        self.slider_workers = QSlider(Qt.Orientation.Horizontal)
        self.slider_workers.setMinimum(1)
        self.slider_workers.setMaximum(16)
        self.slider_workers.setValue(workers_val)
        self.slider_workers.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_workers.setTickInterval(1)
        
        def on_worker_change(val):
            self.cfg.set("workers", val)
            self.lbl_set_workers.setText(f"{self.get_text('lbl_workers') or 'Workers'} (Current: {val})")
            
        self.slider_workers.valueChanged.connect(on_worker_change)
        
        self.lbl_set_warn = QLabel()
        self.lbl_set_warn.setStyleSheet("color: #e67e22; font-style: italic;")
        self.lbl_set_warn.setWordWrap(True)

        layout.addLayout(lang_layout)
        layout.addLayout(theme_layout)
        layout.addSpacing(10)
        layout.addWidget(self.lbl_set_workers)
        layout.addWidget(self.slider_workers)
        layout.addWidget(self.lbl_set_warn)
        layout.addStretch()
        
        return w

    def _build_about(self):
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setSpacing(15)
        
        self.lbl_ab_title = QLabel()
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.lbl_ab_title.setFont(font)
        layout.addWidget(self.lbl_ab_title)
        
        self.lbl_ab_info = QLabel()
        layout.addWidget(self.lbl_ab_info)
        
        self.btn_ab_git = QPushButton()
        self.btn_ab_git.setStyleSheet("padding: 10px; text-align: left;")
        self.btn_ab_git.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL)))
        layout.addWidget(self.btn_ab_git)
        
        self.grp_ab_tut = QGroupBox()
        tut_layout = QVBoxLayout(self.grp_ab_tut)
        self.lbl_ab_tut = QLabel()
        self.lbl_ab_tut.setWordWrap(True)
        tut_layout.addWidget(self.lbl_ab_tut)
        layout.addWidget(self.grp_ab_tut)
        
        upd_layout = QHBoxLayout()
        self.chk_auto_upd = QCheckBox()
        self.chk_auto_upd.setChecked(self.cfg.get("auto_update") is not False)
        self.chk_auto_upd.stateChanged.connect(lambda state: self.cfg.set("auto_update", state == Qt.CheckState.Checked.value))
        
        self.btn_ab_upd = QPushButton()
        self.btn_ab_upd.clicked.connect(self._check_for_updates)
        
        self.lbl_upd_status = QLabel("")
        
        upd_layout.addWidget(self.chk_auto_upd)
        upd_layout.addStretch()
        upd_layout.addWidget(self.btn_ab_upd)
        upd_layout.addWidget(self.lbl_upd_status)
        
        layout.addLayout(upd_layout)
        layout.addStretch()
        
        return w

    def retranslate_ui(self):
        self.lbl_console.setText(self.get_text("lbl_console") or "Log Console")
        self.tabs.setTabText(0, self.get_text("tab_auto") or "Auto Mode")
        self.tabs.setTabText(1, self.get_text("tab_extract_arc") or "Extract ZIP/RAR")
        self.tabs.setTabText(2, self.get_text("tab_extract") or "Extract ISO")
        self.tabs.setTabText(3, self.get_text("tab_compress") or "Compress")
        self.tabs.setTabText(self.settings_idx, self.get_text("tab_settings") or "Settings")
        self.tabs.setTabText(self.about_idx, self.get_text("tab_about") or "About")
        
        t_dir = self.get_text("lbl_directories") or "Directories"
        t_src = self.get_text("lbl_search_source") or "Browse Source..."
        t_tgt = self.get_text("lbl_search_target") or "Browse Target..."
        t_sel = self.get_text("lbl_selectable_items") or "Selectable Items:"
        t_inv = self.get_text("btn_invert_sel") or "Invert Selection"
        t_sta = self.get_text("btn_start_proc") or "▶ Start Processing"
        t_can = self.get_text("btn_cancel_proc") or "⏹ Cancel"
        
        for mode, ui in self.tab_data.items():
            ui.lbl_title.setText(self.get_text(ui.title_key))
            ui.lbl_tip.setText(self.get_text(ui.tip_key))
            ui.grp_dir.setTitle(t_dir)
            ui.btn_src.setText(t_src)
            ui.btn_tgt.setText(t_tgt)
            ui.lbl_items_header.setText(t_sel)
            ui.btn_invert.setText(t_inv)
            ui.btn_start.setText(t_sta)
            ui.btn_cancel.setText(t_can)
            if ui.state == ProcessState.PAUSED:
                ui.btn_pause.setText(self.get_text("btn_resume_proc") or "▶ Resume")
            else:
                ui.btn_pause.setText(self.get_text("btn_pause_proc") or "⏸ Pause")
            
            # Update counter translations dynamically
            if ui.lbl_counter:
                txt = ui.lbl_counter.text()
                parts = txt.split(" ")
                if len(parts) >= 3:
                    c = parts[0]
                    t = parts[2]
                    txt_proc = self.get_text("lbl_processed") or "processed"
                    ui.lbl_counter.setText(f"{c} / {t} {txt_proc}")

        self.lbl_set_title.setText(self.get_text("tab_settings") or "Settings")
        self.lbl_set_lang.setText((self.get_text("lbl_language") or "Language") + ":")
        self.lbl_set_theme.setText((self.get_text("lbl_theme") or "Theme") + ":")
        val = self.slider_workers.value()
        self.lbl_set_workers.setText(f"{self.get_text('lbl_workers') or 'Workers'} (Current: {val})")
        self.lbl_set_warn.setText(self.get_text("worker_warning") or "Worker Warning...")
        
        self.lbl_ab_title.setText(self.get_text("tab_about") or "About")
        t_dev = self.get_text("lbl_about_dev") or "Developer"
        self.lbl_ab_info.setText(f"<b>ZarManager {self.app_version}</b><br><br>💻 {t_dev}: dfdevx2<br>📜 License: MIT License")
        self.btn_ab_git.setText(self.get_text("btn_repo") or "🌐 Official GitHub Repository")
        self.grp_ab_tut.setTitle(self.get_text("lbl_how_to_use") or "How to Use")
        self.lbl_ab_tut.setText(self.get_text("about_tutorial") or "Tutorial...")
        self.chk_auto_upd.setText(self.get_text("lbl_auto_update") or "Check for automatic updates")
        self.btn_ab_upd.setText(self.get_text("btn_check_update") or "Check Updates")

    def _populate_initial_data(self):
        t_ready = self.get_text("log_ready") or "System ready for operation. Native optimized listing active."
        self.emit_log(t_ready, "INFO")
        for m in [ProcessMode.AUTO, ProcessMode.EXTRACT_ARC, ProcessMode.EXTRACT_ISO, ProcessMode.COMPRESS]:
            self._refresh_file_list(m, self.cfg.get("source_dir") or "")

    def _select_dir(self, mode: ProcessMode, target_type: str, line_edit: QLineEdit):
        start_dir = line_edit.text()
        t_sel_dir = self.get_text("lbl_select_dir") or "Select directory"
        chosen = DialogManager.select_directory(self, f"{t_sel_dir} ({target_type})", start_dir)
        if chosen:
            self.cfg.set(f"{target_type}_dir", chosen)
            line_edit.setText(chosen)
            t_set = self.get_text("log_dir_set") or "[SYSTEM] Directory set:"
            self.emit_log(f"{t_set} {target_type}_dir -> {chosen}")
            if target_type == "source":
                self._refresh_file_list(mode, chosen)

    def _refresh_file_list(self, mode: ProcessMode, directory: str):
        ui = self.tab_data[mode]
        ui.list_view.clear()
        ui.items.clear()
        
        files = FileService.find_processable_files(directory, mode)
        if not files:
            msg = self.get_text("msg_no_files") or "No compatible files found."
            item = QListWidgetItem(msg)
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            ui.list_view.addItem(item)
        else:
            for f in files:
                item = QListWidgetItem(f.name)
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsUserCheckable)
                item.setCheckState(Qt.CheckState.Checked)
                ui.list_view.addItem(item)
                ui.items[f.name] = (f, item)

    def _toggle_all_selections(self, mode: ProcessMode):
        ui = self.tab_data[mode]
        if not ui.items: return
        all_checked = all(item.checkState() == Qt.CheckState.Checked for _, item in ui.items.values())
        new_state = Qt.CheckState.Unchecked if all_checked else Qt.CheckState.Checked
        for _, item in ui.items.values():
            item.setCheckState(new_state)

    def _update_ui_state(self, mode: ProcessMode, state: ProcessState):
        ui = self.tab_data[mode]
        ui.state = state
        
        is_busy = state in {ProcessState.RUNNING, ProcessState.PAUSED, ProcessState.CANCELLING}
        ui.btn_start.setEnabled(not is_busy)
        ui.btn_pause.setEnabled(is_busy and state != ProcessState.CANCELLING)
        ui.btn_cancel.setEnabled(is_busy and state != ProcessState.CANCELLING)
        
        if state == ProcessState.PAUSED:
            ui.btn_pause.setText(self.get_text("btn_resume_proc") or "▶ Resume")
        else:
            ui.btn_pause.setText(self.get_text("btn_pause_proc") or "⏸ Pause")

    def _start_pipeline(self, mode: ProcessMode):
        ui = self.tab_data[mode]
        
        if mode in self.active_threads or ui.state in {ProcessState.RUNNING, ProcessState.PAUSED, ProcessState.CANCELLING}:
            t_err_run = self.get_text("msg_err_running") or "Mode is already running."
            DialogManager.show_error(self, "Warning", t_err_run)
            return
            
        target_dir = self.cfg.get("target_dir")
        if not target_dir: 
            t_err_tgt = self.get_text("msg_err_target") or "Set the target directory."
            DialogManager.show_warning(self, "Error", t_err_tgt)
            return

        selected = [path for path, item in ui.items.values() if item.checkState() == Qt.CheckState.Checked]
        if not selected: 
            t_err_sel = self.get_text("msg_err_select") or "Select at least one file to process."
            DialogManager.show_warning(self, "Warning", t_err_sel)
            return

        target_path = Path(target_dir)
        collisions = [p for p in selected if (target_path / (p.stem + ".zar" if mode in [ProcessMode.AUTO, ProcessMode.COMPRESS] else p.name)).exists()]

        req = ProcessRequest(mode=mode, items=selected, target=target_path, keep_originals=False, collision_policy=CollisionPolicy.CANCEL)

        if collisions:
            resp = DialogManager.ask_custom(self, self.get_text("msg_collision_title"), self.get_text("msg_collision_desc"), 
                                            [self.get_text("btn_cancel"), self.get_text("btn_skip_existing"), self.get_text("btn_overwrite")])
            if resp == self.get_text("btn_cancel") or resp == "":
                t_warn_canc = self.get_text("log_warn_cancelled") or "[WARNING] Operation cancelled due to conflicts."
                self.emit_log(t_warn_canc, "WARNING")
                return
            elif resp == self.get_text("btn_skip_existing"):
                req.items = [p for p in req.items if p not in collisions]
                if not req.items:
                    t_warn_emp = self.get_text("log_warn_empty") or "[WARNING] Queue empty after skipping conflicts."
                    self.emit_log(t_warn_emp, "WARNING")
                    return
                req.collision_policy = CollisionPolicy.SKIP
            else:
                req.collision_policy = CollisionPolicy.OVERWRITE
        
        self._prompt_deletion(req)

    def _prompt_deletion(self, req: ProcessRequest):
        t_del = self.get_text("btn_delete_default") or "Delete (Default)"
        t_keep = self.get_text("btn_keep_originals") or "Keep Originals"
        resp = DialogManager.ask_custom(self, self.get_text("delete_title"), self.get_text("delete_msg"), [t_del, t_keep])
        if resp == "": return 
        req.keep_originals = (resp == t_keep)
        self._dispatch_worker(req)

    def _dispatch_worker(self, req: ProcessRequest):
        self._update_ui_state(req.mode, ProcessState.RUNNING)
        t_start = self.get_text("log_start_worker") or "[SYSTEM] Starting Worker"
        self.emit_log(f"{t_start} (Mode: {req.mode.value} | {len(req.items)} items).", "INFO")
        
        ui = self.tab_data[req.mode]
        ui.progress.setValue(0)
        ui.lbl_percentage.setText("0%")
        txt_proc = self.get_text("lbl_processed") or "processed"
        ui.lbl_counter.setText(f"0 / {len(req.items)} {txt_proc}")

        workers = int(self.cfg.get("workers") or 4)
        worker = CoreWorkerThread(req, workers, self.get_text, self)
        
        worker.log_signal.connect(self.emit_log)
        worker.progress_signal.connect(self._on_progress_update)
        worker.status_signal.connect(self._on_status_update)
        worker.finished_signal.connect(self._on_worker_finished)
        
        self.active_threads[req.mode] = worker
        worker.start()

    def _toggle_pause(self, mode: ProcessMode):
        worker = self.active_threads.get(mode)
        if worker and worker.manager:
            st = worker.manager.toggle_pause()
            self._update_ui_state(mode, ProcessState.PAUSED if st else ProcessState.RUNNING)
            t_pause = self.get_text("log_paused") or "Paused"
            t_resume = self.get_text("log_resumed") or "Resumed"
            state_str = t_pause if st else t_resume
            self.emit_log(f"[SYSTEM] Process {state_str}.", "INFO")

    def _request_cancel(self, mode: ProcessMode):
        worker = self.active_threads.get(mode)
        if worker and worker.manager:
            self._update_ui_state(mode, ProcessState.CANCELLING)
            worker.manager.request_cancel()
            t_canc = self.get_text("log_cancelling") or "[SYSTEM] Cancel request sent. Waiting for threads to stop safely..."
            self.emit_log(t_canc, "WARNING")

    def _check_for_updates(self):
        self.btn_ab_upd.setEnabled(False)
        self.lbl_upd_status.setText(self.get_text("lbl_checking_updates") or "Checking for updates...")
        
        def perform_check():
            try:
                has_update = False
                if hasattr(UpdateService, 'check_latest'):
                    has_update = UpdateService.check_latest(self.app_version)
                
                if has_update:
                    self.lbl_upd_status.setText(self.get_text("msg_update_avail") or "New update available!")
                else:
                    self.lbl_upd_status.setText(self.get_text("msg_update_none") or "You are running the latest version.")
            except Exception:
                self.lbl_upd_status.setText(self.get_text("msg_update_fail") or "No updates found or connection timeout.")
            finally:
                self.btn_ab_upd.setEnabled(True)
                QTimer.singleShot(5000, lambda: self.lbl_upd_status.setText(""))

        QTimer.singleShot(800, perform_check)

    @Slot(str, str)
    def emit_log(self, msg: str, level: str = "INFO"):
        if level == "ERROR": logger.error(msg)
        elif level == "WARNING": logger.warning(msg)
        else: logger.info(msg)
        
        safe_msg = msg.replace("<", "&lt;").replace(">", "&gt;")
        color = "#e53935" if level == "ERROR" else "#ffb300" if level == "WARNING" else "#d4d4d4"
        self.console.append(f"<span style='color:{color};'>{safe_msg}</span>")
        self.console.verticalScrollBar().setValue(self.console.verticalScrollBar().maximum())

    @Slot(object, int, int, float)
    def _on_progress_update(self, mode: ProcessMode, c: int, t: int, r: float):
        ui = self.tab_data[mode]
        val = int(r * 100)
        ui.progress.setValue(val)
        ui.lbl_percentage.setText(f"{val}%")
        txt_proc = self.get_text("lbl_processed") or "processed"
        ui.lbl_counter.setText(f"{c} / {t} {txt_proc}")

    @Slot(object, str, str)
    def _on_status_update(self, mode: ProcessMode, item_name: str, status: str):
        # Tradução dinâmica instantânea do core.py baseada no idioma selecionado
        t_extracting_iso = self.get_text("log_extracting_iso") or "EXTRACTING ISO"
        t_extracting_arc = self.get_text("log_extracting_arc") or "EXTRACTING ARCHIVE"
        t_compressing = self.get_text("log_compressing") or "COMPRESSING ZAR"
        t_completed = self.get_text("log_completed") or "COMPLETED"
        t_failed = self.get_text("log_failed") or "FAILED"
        t_cancelled = self.get_text("log_cancelled") or "CANCELLED"
        
        status = status.replace("EXTRAINDO ISO", t_extracting_iso)
        status = status.replace("DESCOMPACTANDO", t_extracting_arc)
        status = status.replace("COMPRIMINDO ZAR", t_compressing)
        status = status.replace("CONCLUIDO", t_completed)
        status = status.replace("FALHA", t_failed)
        status = status.replace("CANCELADO", t_cancelled)

        if "FALHA" in status.upper() or t_failed.upper() in status.upper():
            SoundService.play("error")
            self.emit_log(f"[{item_name}] {status}", "ERROR")
        else:
            self.emit_log(f"[{item_name}] {status}", "INFO")

    @Slot(object, object)
    def _on_worker_finished(self, mode: ProcessMode, state: ProcessState):
        self.active_threads.pop(mode, None)
        self._update_ui_state(mode, state)
        
        if state == ProcessState.COMPLETED:
            SoundService.play("success")
            t_succ = self.get_text("log_succ") or "[SUCCESS] Operation finished perfectly."
            self.emit_log(t_succ, "INFO")
            t_done = self.get_text("msg_done") or "Completed"
            t_done_desc = self.get_text("msg_done_desc") or "Batch processing finished without errors."
            DialogManager.show_info(self, t_done, t_done_desc)
        elif state == ProcessState.PARTIAL:
            SoundService.play("error")
            t_warn = self.get_text("log_warn_partial") or "[WARNING] Operation finished with partial failures."
            self.emit_log(t_warn, "WARNING")
        elif state == ProcessState.FAILED:
            SoundService.play("error")
            t_err = self.get_text("log_err_crit") or "[ERROR] Operation failed critically."
            self.emit_log(t_err, "ERROR")
        elif state == ProcessState.CANCELLED:
            t_usr_canc = self.get_text("log_usr_canc") or "[SYSTEM] Operation cancelled by the user."
            self.emit_log(t_usr_canc, "INFO")