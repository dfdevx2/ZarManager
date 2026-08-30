import os
import shutil
import platform
import webbrowser
from pathlib import Path

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QLabel, 
    QPushButton, QLineEdit, QListWidget, QListWidgetItem,
    QProgressBar, QTextEdit, QGroupBox, QComboBox, QSlider, QCheckBox, QMessageBox
)
from PySide6.QtCore import Qt, QThread, Signal, Slot, QUrl, QTimer
from PySide6.QtGui import QFont, QDesktopServices

import locales
from models.process import ProcessMode, ProcessState, CollisionPolicy, ProcessRequest, ProcessResult
from models.tab import TabState
from services.logging_service import logger
from services.file_service import FileService
from services.sound_service import SoundService
from ui.dialogs import DialogManager
from core import ZarManagerCore

GITHUB_REPO_URL = "https://github.com/dfdevx2/ZarManager"

class CoreWorkerThread(QThread):
    log_signal = Signal(str, str)
    progress_signal = Signal(object, int, int, float)
    status_signal = Signal(object, str, str)
    finished_signal = Signal(object, object)
    error_dialog_signal = Signal(str, str)
    av_alert_signal = Signal(str)

    def __init__(self, request: ProcessRequest, workers: int, policy_str: str, parent=None):
        super().__init__(parent)
        self.req = request
        self.workers = workers
        self.policy_str = policy_str
        self.manager = None

    def run(self):
        self.manager = ZarManagerCore(
            self.req.items, str(self.req.target), self.workers, self.req.mode.value, 
            self.req.keep_originals, self.policy_str, 
            lambda m: self.log_signal.emit(m, "INFO"),
            lambda c, t, r: self.progress_signal.emit(self.req.mode, c, t, r),
            lambda i, s: self.status_signal.emit(self.req.mode, i, s)
        )
        
        try:
            if hasattr(self.manager, 'verify_environment'):
                env_res = self.manager.verify_environment()
                if isinstance(env_res, tuple):
                    success, missing_files = env_res
                else:
                    success = env_res
                    missing_files = []
            else:
                success, missing_files = True, []

            if not success:
                missing_str = ", ".join(missing_files) if missing_files else "Ficheiros desconhecidos"
                sys_os = platform.system()
                
                if sys_os == "Windows":
                    err_title = self.parent().get_text("err_title_win", "Error")
                    err_msg = self.parent().get_text("err_msg_win", "Missing: {0}").format(missing_str)
                elif sys_os == "Darwin":
                    err_title = self.parent().get_text("err_title_mac", "Error")
                    err_msg = self.parent().get_text("err_msg_mac", "Missing: {0}").format(missing_str)
                else:
                    err_title = self.parent().get_text("err_title_lin", "Error")
                    err_msg = self.parent().get_text("err_msg_lin", "Missing: {0}").format(missing_str)
                
                self.log_signal.emit(f"[CRITICAL ERROR] Missing Engines: {missing_str}", "ERROR")
                self.error_dialog_signal.emit(err_title, err_msg)
                self.finished_signal.emit(self.req.mode, ProcessState.FAILED)
                return
            else:
                t_ok = self.parent().get_text("log_env_ok", "[SYSTEM] Verification complete. All embedded engines are operational.")
                self.log_signal.emit(t_ok, "INFO")
            
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
            error_str = str(e)
            logger.error("Exception in worker", exc_info=True)
            
            if "AV_BLOCK|" in error_str:
                binary_name = error_str.split("|")[1]
                self.av_alert_signal.emit(binary_name)
                self.finished_signal.emit(self.req.mode, ProcessState.FAILED)
                return

            self.log_signal.emit(f"[FATAL] Erro do motor: {error_str}. Verifique logs.", "ERROR")
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
        
        if not self.cfg.get("tutorial_done"):
            QTimer.singleShot(800, self._show_tutorial)
            
        if self.cfg.get("auto_update") is not False:
            QTimer.singleShot(2500, lambda: self._check_for_updates(silent=True))

    def get_text(self, key: str, fallback: str = "") -> str:
        try:
            lang = self.cfg.get("language") or "pt-br"
            val = locales.get_text(lang, key)
            if not val or val == key:
                return fallback if fallback else key
            return val
        except Exception:
            return fallback if fallback else key

    def _show_tutorial(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(self.get_text("tut_title", "Guia Rápido"))
        msg.setText(self.get_text("tut_msg", "Bem-vindo ao ZarManager!\n..."))
        msg.setIcon(QMessageBox.Icon.Information)
        msg.exec()
        self.cfg.set("tutorial_done", True)

    def _show_troubleshooting(self):
        msg = QMessageBox(self)
        msg.setWindowTitle(self.get_text("diag_troubleshoot_title", "Troubleshooting"))
        msg.setText(self.get_text("diag_troubleshoot_msg", "Help..."))
        msg.setIcon(QMessageBox.Icon.Warning)
        msg.exec()

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
        idx_lang = self.cb_lang.findText(self.cfg.get("language") or "pt-br")
        if idx_lang >= 0: self.cb_lang.setCurrentIndex(idx_lang)
        
        def on_lang_change(txt):
            self.cfg.set("language", txt)
            self.emit_log(self.get_text("log_lang_changed", "Idioma alterado."), "INFO")
            self.retranslate_ui() 
            
        self.cb_lang.currentTextChanged.connect(on_lang_change)
        lang_layout.addWidget(self.lbl_set_lang)
        lang_layout.addWidget(self.cb_lang)
        lang_layout.addStretch()
        
        theme_layout = QHBoxLayout()
        self.lbl_set_theme = QLabel()
        
        self.cb_theme = QComboBox()
        self.cb_theme.currentIndexChanged.connect(self._on_theme_index_change)
        
        theme_layout.addWidget(self.lbl_set_theme)
        theme_layout.addWidget(self.cb_theme)
        theme_layout.addStretch()
        
        workers_val = int(self.cfg.get("workers") or 2)
        self.lbl_set_workers = QLabel()
        
        self.slider_workers = QSlider(Qt.Orientation.Horizontal)
        self.slider_workers.setMinimum(1)
        self.slider_workers.setMaximum(16)
        self.slider_workers.setValue(workers_val)
        self.slider_workers.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_workers.setTickInterval(1)
        
        def on_worker_change(val):
            self.cfg.set("workers", val)
            self.lbl_set_workers.setText(f"{self.get_text('lbl_workers', 'Workers')} (Atual: {val})")
            
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

    def _on_theme_index_change(self, index):
        if index >= 0:
            theme_data = self.cb_theme.itemData(index)
            if theme_data and theme_data != self.cfg.get("theme"):
                self.cfg.set("theme", theme_data)
                self.apply_theme_cb()

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
        
        btn_layout = QVBoxLayout()
        btn_layout.setSpacing(8)
        
        self.btn_ab_git = QPushButton()
        self.btn_ab_git.setStyleSheet("padding: 10px; text-align: left;")
        self.btn_ab_git.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_REPO_URL)))
        btn_layout.addWidget(self.btn_ab_git)

        self.btn_ab_kofi = QPushButton()
        self.btn_ab_kofi.setStyleSheet("""
            QPushButton { background-color: #29abe0; color: white; font-weight: bold; padding: 10px; text-align: left; border-radius: 4px; }
            QPushButton:hover { background-color: #1a8fbe; }
        """)
        self.btn_ab_kofi.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://ko-fi.com/dfdx047")))
        btn_layout.addWidget(self.btn_ab_kofi)
        
        self.btn_ab_trouble = QPushButton()
        self.btn_ab_trouble.setStyleSheet("""
            QPushButton { background-color: #e67e22; color: white; font-weight: bold; padding: 10px; text-align: left; border-radius: 4px; }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.btn_ab_trouble.clicked.connect(self._show_troubleshooting)
        btn_layout.addWidget(self.btn_ab_trouble)
        
        layout.addLayout(btn_layout)
        
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
        self.btn_ab_upd.clicked.connect(lambda: self._check_for_updates(silent=False))
        
        self.lbl_upd_status = QLabel("")
        
        upd_layout.addWidget(self.chk_auto_upd)
        upd_layout.addStretch()
        upd_layout.addWidget(self.btn_ab_upd)
        upd_layout.addWidget(self.lbl_upd_status)
        
        layout.addLayout(upd_layout)
        layout.addStretch()
        
        return w

    def retranslate_ui(self):
        self.lbl_console.setText(self.get_text("lbl_console", "Console de Registo"))
        self.tabs.setTabText(0, self.get_text("tab_auto", "Modo Auto"))
        self.tabs.setTabText(1, self.get_text("tab_extract_arc", "Extrair ZIP/RAR"))
        self.tabs.setTabText(2, self.get_text("tab_extract", "Extrair ISO"))
        self.tabs.setTabText(3, self.get_text("tab_compress", "Comprimir"))
        self.tabs.setTabText(self.settings_idx, self.get_text("tab_settings", "Configurações"))
        self.tabs.setTabText(self.about_idx, self.get_text("tab_about", "Sobre"))
        
        self.tabs.setTabToolTip(0, self.get_text("tip_auto"))
        self.tabs.setTabToolTip(1, self.get_text("tip_extract_arc"))
        self.tabs.setTabToolTip(2, self.get_text("tip_extract"))
        self.tabs.setTabToolTip(3, self.get_text("tip_compress"))
        self.cb_theme.setToolTip(self.get_text("tip_theme"))
        self.cb_lang.setToolTip(self.get_text("tip_lang"))
        self.slider_workers.setToolTip(self.get_text("worker_warning"))
        
        current_theme = self.cfg.get("theme") or "Sistema"
        self.cb_theme.blockSignals(True)
        self.cb_theme.clear()
        themes = [
            ("Sistema", self.get_text("theme_system", "System")),
            ("Preto", self.get_text("theme_black", "Pitch Black")),
            ("Branco", self.get_text("theme_white", "White")),
            ("Steam", "Steam"),
            ("Xbox", "Xbox")
        ]
        for data_val, display_text in themes:
            self.cb_theme.addItem(display_text, data_val)
            if data_val == current_theme:
                self.cb_theme.setCurrentIndex(self.cb_theme.count() - 1)
        self.cb_theme.blockSignals(False)
        
        t_dir = self.get_text("lbl_directories", "Diretórios")
        t_src = self.get_text("lbl_search_source", "Procurar Origem...")
        t_tgt = self.get_text("lbl_search_target", "Procurar Destino...")
        t_sel = self.get_text("lbl_selectable_items", "Itens Selecionáveis:")
        t_inv = self.get_text("btn_invert_sel", "Inverter Seleção")
        t_sta = self.get_text("btn_start_proc", "▶ Iniciar Processamento")
        t_can = self.get_text("btn_cancel_proc", "⏹ Cancelar")
        
        for mode, ui in self.tab_data.items():
            ui.lbl_title.setText(self.get_text(ui.title_key, "ZarManager"))
            ui.lbl_tip.setText(self.get_text(ui.tip_key, "Pipeline Automático"))
            ui.grp_dir.setTitle(t_dir)
            ui.btn_src.setText(t_src)
            ui.btn_tgt.setText(t_tgt)
            ui.lbl_items_header.setText(t_sel)
            ui.btn_invert.setText(t_inv)
            ui.btn_start.setText(t_sta)
            ui.btn_cancel.setText(t_can)
            
            ui.btn_src.setToolTip(self.get_text("tip_source"))
            ui.btn_tgt.setToolTip(self.get_text("tip_target"))
            ui.btn_invert.setToolTip(self.get_text("tip_invert"))
            ui.btn_start.setToolTip(self.get_text("tip_start"))
            ui.btn_pause.setToolTip(self.get_text("tip_pause"))
            ui.btn_cancel.setToolTip(self.get_text("tip_cancel"))
            
            if ui.state == ProcessState.PAUSED:
                ui.btn_pause.setText(self.get_text("btn_resume_proc", "▶ Retomar"))
            else:
                ui.btn_pause.setText(self.get_text("btn_pause_proc", "⏸ Pausar"))

            if ui.list_view.count() == 1:
                item = ui.list_view.item(0)
                if not (item.flags() & Qt.ItemFlag.ItemIsUserCheckable):
                    item.setText(self.get_text("msg_no_files", "Nenhum ficheiro compatível..."))

        self.lbl_set_title.setText(self.get_text("tab_settings", "Configurações"))
        self.lbl_set_lang.setText((self.get_text("lbl_language", "Idioma")) + ":")
        self.lbl_set_theme.setText((self.get_text("lbl_theme", "Tema")) + ":")
        val = self.slider_workers.value()
        self.lbl_set_workers.setText(f"{self.get_text('lbl_workers', 'Workers')} (Atual: {val})")
        self.lbl_set_warn.setText(self.get_text("worker_warning", "Atenção ao número de workers selecionado."))
        
        self.lbl_ab_title.setText(self.get_text("tab_about", "Sobre"))
        t_dev = self.get_text("lbl_about_dev", "Desenvolvedor")
        self.lbl_ab_info.setText(f"<b>ZarManager {self.app_version}</b><br><br>💻 {t_dev}: dfdevx2<br>📜 Licença: MIT License")
        self.btn_ab_git.setText(self.get_text("btn_repo", "🌐 Repositório Oficial no GitHub"))
        self.btn_ab_kofi.setText(self.get_text("btn_kofi", "☕ Apoiar o Projeto no Ko-fi"))
        self.btn_ab_trouble.setText(self.get_text("btn_troubleshoot", "🛠️ Resolução de Erros Comuns"))
        self.grp_ab_tut.setTitle(self.get_text("lbl_how_to_use", "Como Usar"))
        self.lbl_ab_tut.setText(self.get_text("about_tutorial", "Selecione o diretório, marque os itens e inicie."))
        self.chk_auto_upd.setText(self.get_text("lbl_auto_update", "Procurar Atualizações Automáticas"))
        self.btn_ab_upd.setText(self.get_text("btn_check_update", "Procurar Atualizações"))

    def _populate_initial_data(self):
        self.emit_log(self.get_text("log_ready", "Sistema pronto para operação."), "INFO")
        for m in [ProcessMode.AUTO, ProcessMode.EXTRACT_ARC, ProcessMode.EXTRACT_ISO, ProcessMode.COMPRESS]:
            self._refresh_file_list(m, self.cfg.get("source_dir") or "")

    def _select_dir(self, mode: ProcessMode, target_type: str, line_edit: QLineEdit):
        start_dir = line_edit.text()
        chosen = DialogManager.select_directory(self, f"Selecione o diretório ({target_type})", start_dir)
        if chosen:
            self.cfg.set(f"{target_type}_dir", chosen)
            line_edit.setText(chosen)
            self.emit_log(f"[SISTEMA] {target_type}_dir definido: {chosen}")
            if target_type == "source":
                self._refresh_file_list(mode, chosen)

    def _refresh_file_list(self, mode: ProcessMode, directory: str):
        ui = self.tab_data[mode]
        ui.list_view.clear()
        ui.items.clear()
        
        files = FileService.find_processable_files(directory, mode)
        if not files:
            msg = self.get_text("msg_no_files", "Nenhum ficheiro compatível encontrado.")
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
            ui.btn_pause.setText(self.get_text("btn_resume_proc", "▶ Retomar"))
        else:
            ui.btn_pause.setText(self.get_text("btn_pause_proc", "⏸ Pausar"))

    def _start_pipeline(self, mode: ProcessMode):
        ui = self.tab_data[mode]
        
        if mode in self.active_threads or ui.state in {ProcessState.RUNNING, ProcessState.PAUSED, ProcessState.CANCELLING}:
            DialogManager.show_error(self, "Aviso", self.get_text("msg_err_running", "O processo já está em execução."))
            return
            
        target_dir = self.cfg.get("target_dir")
        if not target_dir: 
            DialogManager.show_warning(self, "Erro", self.get_text("msg_err_target", "Defina o diretório de destino."))
            return

        selected = [path for path, item in ui.items.values() if item.checkState() == Qt.CheckState.Checked]
        if not selected: 
            DialogManager.show_warning(self, "Aviso", self.get_text("msg_err_select", "Selecione ao menos um ficheiro."))
            return

        target_path = Path(target_dir)
        collisions = []
        for p in selected:
            possible_names = [p.name, p.stem + ".zar", p.stem + ".iso", p.stem]
            if any((target_path / pos).exists() for pos in possible_names):
                collisions.append(p)

        req = ProcessRequest(mode=mode, items=selected, target=target_path, keep_originals=False, collision_policy=CollisionPolicy.CANCEL)
        policy_str = "RENAME" 

        if collisions:
            btn_canc = self.get_text("btn_cancel", "Cancelar")
            btn_skip = self.get_text("btn_skip_existing", "Pular Existentes")
            btn_over = self.get_text("btn_overwrite", "Sobrescrever")
            btn_ren = self.get_text("btn_rename", "Renomear Auto (_1)")
            
            resp = DialogManager.ask_custom(self, 
                                            self.get_text("msg_collision_title", "Conflito de Ficheiros"), 
                                            self.get_text("msg_collision_desc", "Alguns ficheiros ou pastas intermédias já existem no destino. O que deseja fazer?"), 
                                            [btn_canc, btn_skip, btn_over, btn_ren])
            if resp == btn_canc or resp == "":
                self.emit_log(self.get_text("log_warn_cancelled", "[AVISO] Operação cancelada devido a conflitos."), "WARNING")
                return
            elif resp == btn_skip:
                policy_str = "SKIP"
            elif resp == btn_over:
                policy_str = "OVERWRITE"
            elif resp == btn_ren:
                policy_str = "RENAME"
        
        self._prompt_deletion(req, policy_str)

    def _prompt_deletion(self, req: ProcessRequest, policy_str: str):
        t_del = self.get_text("btn_delete_default", "Apagar Originais (Padrão)")
        t_keep = self.get_text("btn_keep_originals", "Manter Originais")
        
        resp = DialogManager.ask_custom(self, 
                                        self.get_text("delete_title", "Manter Ficheiros de Origem?"), 
                                        self.get_text("delete_msg", "Após processar, deseja apagar os originais para poupar espaço?"), 
                                        [t_del, t_keep])
        if resp == "": return 
        req.keep_originals = (resp == t_keep)
        self._dispatch_worker(req, policy_str)

    @Slot(str, str)
    def _show_thread_error(self, title: str, msg: str):
        DialogManager.show_error(self, title, msg)

    @Slot(str)
    def _show_antivirus_alert(self, binary_name):
        for mode in ProcessMode:
            if mode in self.active_threads:
                self._request_cancel(mode)
                
        SoundService.play("error")
        t_title = self.get_text("av_alert_title", "Alerta Crítico de Segurança")
        msg = self.get_text("av_alert_msg", "Erro de antivírus bloqueando {0}.").format(binary_name)
        
        QMessageBox.critical(self, t_title, msg)
        self.emit_log(self.get_text("log_av_block", "[BLOQUEIO] Motor destruído: {0}").format(binary_name), "ERROR")

    def _dispatch_worker(self, req: ProcessRequest, policy_str: str):
        self._update_ui_state(req.mode, ProcessState.RUNNING)
        self.emit_log(f"[SISTEMA] Iniciando Trabalhador (Modo: {req.mode.value} | {len(req.items)} itens).", "INFO")
        
        ui = self.tab_data[req.mode]
        ui.progress.setValue(0)
        ui.lbl_percentage.setText("0%")
        txt_proc = self.get_text("lbl_processed", "processados")
        ui.lbl_counter.setText(f"0 / {len(req.items)} {txt_proc}")

        workers = int(self.cfg.get("workers") or 2)
        worker = CoreWorkerThread(req, workers, policy_str, self)
        
        worker.log_signal.connect(self.emit_log)
        worker.progress_signal.connect(self._on_progress_update)
        worker.status_signal.connect(self._on_status_update)
        worker.finished_signal.connect(self._on_worker_finished)
        worker.error_dialog_signal.connect(self._show_thread_error)
        worker.av_alert_signal.connect(self._show_antivirus_alert) 
        
        self.active_threads[req.mode] = worker
        worker.start()

    def _toggle_pause(self, mode: ProcessMode):
        worker = self.active_threads.get(mode)
        if worker and worker.manager:
            st = worker.manager.toggle_pause()
            self._update_ui_state(mode, ProcessState.PAUSED if st else ProcessState.RUNNING)
            if st:
                self.emit_log("[SISTEMA] Processo Pausado.", "INFO")
            else:
                self.emit_log("[SISTEMA] Processo Retomado.", "INFO")

    def _request_cancel(self, mode: ProcessMode):
        worker = self.active_threads.get(mode)
        if worker and worker.manager:
            self._update_ui_state(mode, ProcessState.CANCELLING)
            worker.manager.request_cancel()
            self.emit_log("[SISTEMA] Interrupção enviada. A aguardar que as threads parem com segurança...", "WARNING")

    def _check_for_updates(self, silent=False):
        try:
            from ui.update_dialog import UpdateDialog, GitHubFetchThread
        except ImportError:
            self.emit_log("[ERRO] Arquivo 'ui/update_dialog.py' não encontrado. Por favor, coloque-o na pasta 'ui'.", "ERROR")
            return

        if not silent:
            # Clique manual: Abre a janela sempre
            dialog = UpdateDialog(self.app_version, self.cfg.get("language") or "pt-br", self)
            dialog.exec()
        else:
            # Arranque silencioso: Verifica no fundo sem congelar a UI
            self.silent_thread = GitHubFetchThread()
            
            def on_silent_done(data):
                latest_version = data.get("tag_name", "").lower().replace("v", "")
                current = self.app_version.lower().replace("v", "")
                # Se for maior, invoca o popup e passa a versão já descarregada
                if latest_version > current:
                    dialog = UpdateDialog(self.app_version, self.cfg.get("language") or "pt-br", self, pre_fetched_data=data)
                    dialog.exec()
                    
            self.silent_thread.result_signal.connect(on_silent_done)
            self.silent_thread.start()

    @Slot(str, str)
    def emit_log(self, msg: str, level: str = "INFO"):
        lang = self.cfg.get("language") or "pt-br"
        if lang == "en":
            msg = msg.replace("[ERRO CRÍTICO]", "[CRITICAL ERROR]")
            msg = msg.replace("[SISTEMA] Pulando ficheiro existente:", "[SYSTEM] Skipping existing file:")
            msg = msg.replace("[SISTEMA] Sobrescrevendo ficheiro existente:", "[SYSTEM] Overwriting existing file:")
            msg = msg.replace("[SISTEMA] Renomeado para evitar conflito:", "[SYSTEM] Renamed to avoid conflict:")
            msg = msg.replace("Alguns ficheiros ou pastas intermédias já existem no destino", "Some files or intermediate folders already exist in the target")
            msg = msg.replace("O ambiente não atende aos requisitos mínimos.", "Environment does not meet minimum requirements.")
            msg = msg.replace("[SISTEMA] Iniciando Trabalhador", "[SYSTEM] Starting Worker")
            msg = msg.replace("Modo:", "Mode:")
            msg = msg.replace("itens", "items")
            msg = msg.replace("[SISTEMA] Processo Pausado.", "[SYSTEM] Process Paused.")
            msg = msg.replace("[SISTEMA] Processo Retomado.", "[SYSTEM] Process Resumed.")
            msg = msg.replace("[SISTEMA] Interrupção enviada. A aguardar que as threads parem com segurança...", "[SYSTEM] Interrupt sent. Waiting for threads to stop safely...")
            msg = msg.replace("[SUCESSO] Operação", "[SUCCESS] Operation")
            msg = msg.replace("finalizada perfeitamente.", "finished perfectly.")
            msg = msg.replace("[AVISO] Operação", "[WARNING] Operation")
            msg = msg.replace("terminou com falhas parciais.", "finished with partial failures.")
            msg = msg.replace("[ERRO] Operação", "[ERROR] Operation")
            msg = msg.replace("falhou criticamente.", "failed critically.")
            msg = msg.replace("[SISTEMA] Operação", "[SYSTEM] Operation")
            msg = msg.replace("foi cancelada pelo utilizador.", "was cancelled by the user.")
            msg = msg.replace("[SISTEMA] source_dir definido:", "[SYSTEM] source_dir set:")
            msg = msg.replace("[SISTEMA] target_dir definido:", "[SYSTEM] target_dir set:")
            msg = msg.replace("[SISTEMA] Lote abortado pelo utilizador.", "[SYSTEM] Batch aborted by user.")
            msg = msg.replace("[SISTEMA] Lote concluído com sucesso.", "[SYSTEM] Batch completed successfully.")
            
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
        txt_proc = self.get_text("lbl_processed", "processados")
        ui.lbl_counter.setText(f"{c} / {t} {txt_proc}")

    @Slot(object, str, str)
    def _on_status_update(self, mode: ProcessMode, item_name: str, status: str):
        t_extracting_iso = self.get_text("log_extracting_iso", "EXTRAINDO ISO")
        t_extracting_arc = self.get_text("log_extracting_arc", "DESCOMPACTANDO")
        t_compressing = self.get_text("log_compressing", "COMPRIMINDO ZAR")
        t_completed = self.get_text("log_completed", "CONCLUÍDO")
        t_skipped = self.get_text("log_skipped", "PULADO")
        t_failed = self.get_text("log_failed", "FALHA")
        t_cancelled = self.get_text("log_cancelled", "CANCELADO")
        
        status = status.replace("EXTRAINDO ISO", t_extracting_iso)
        status = status.replace("DESCOMPACTANDO", t_extracting_arc)
        status = status.replace("COMPRIMINDO ZAR", t_compressing)
        status = status.replace("CONCLUIDO", t_completed)
        status = status.replace("PULADO", t_skipped)
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
            self.emit_log(f"[SUCESSO] Operação {mode.value} finalizada perfeitamente.", "INFO")
            t_done = self.get_text("msg_done", "Concluído")
            t_done_desc = self.get_text("msg_done_desc", "O processamento em lote terminou sem erros.")
            DialogManager.show_info(self, t_done, t_done_desc)
        elif state == ProcessState.PARTIAL:
            SoundService.play("error")
            self.emit_log(f"[AVISO] Operação {mode.value} terminou com falhas parciais.", "WARNING")
        elif state == ProcessState.FAILED:
            SoundService.play("error")
            self.emit_log(f"[ERRO] Operação {mode.value} falhou criticamente.", "ERROR")
        elif state == ProcessState.CANCELLED:
            self.emit_log(f"[SISTEMA] Operação {mode.value} foi cancelada pelo utilizador.", "INFO")