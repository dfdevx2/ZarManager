"""Janela principal: cabeçalho com pílulas + pilha de páginas."""

from __future__ import annotations

from PySide6.QtCore import QSize, Qt, QTimer
from PySide6.QtGui import QCloseEvent, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
)

from core.planner import Mode
from services.paths import resource_root
from ui.dialogs import DialogManager
from ui.i18n import Translator
from ui.views.about_view import AboutView
from ui.views.settings_view import SettingsView
from ui.views.troubleshoot_view import TroubleshootView
from ui.views.workspace_view import WorkspaceView
from ui.widgets.card import action_button
from ui.widgets.pill_nav import PillNav
from version import __version__

PAGE_WORKSPACE = 0
PAGE_SETTINGS = 1
PAGE_ABOUT = 2
PAGE_HELP = 3

MODES = [Mode.AUTO, Mode.EXTRACT_ARC, Mode.EXTRACT_ISO, Mode.COMPRESS]
MODE_KEYS = ["nav_auto", "nav_arc", "nav_iso", "nav_zar"]
MODE_ICONS = ["⚡", "📦", "💿", "🗜"]


class MainWindow(QMainWindow):
    def __init__(self, cfg, theme_manager, sound):
        super().__init__()
        self.cfg = cfg
        self.theme_manager = theme_manager
        self.sound = sound
        self.t = Translator(cfg)

        self.setWindowTitle(f"ZarManager v{__version__}")
        self.setMinimumSize(1040, 720)
        self._restore_geometry()

        self._build()
        self.retranslate()

        self.theme_manager.subscribe(self._on_tokens)
        self._on_tokens(self.theme_manager.tokens)

        if self.cfg.get_bool("auto_update"):
            QTimer.singleShot(2500, lambda: self._check_updates(silent=True))

    # --------------------------------------------------------------- layout
    def _build(self) -> None:
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 18, 24, 20)
        layout.setSpacing(16)

        layout.addLayout(self._header())

        self.stack = QStackedWidget()
        self.workspace = WorkspaceView(self.cfg, self.t, self.sound)
        self.settings = SettingsView(self.cfg, self.t, self.sound)
        self.about = AboutView(self.cfg, self.t)
        self.help = TroubleshootView(self.cfg, self.t)

        for page in (self.workspace, self.settings, self.about, self.help):
            self.stack.addWidget(page)

        self.settings.languageChanged.connect(self.retranslate)
        self.settings.themeChanged.connect(self._on_theme_changed)
        self.settings.motionChanged.connect(self._on_motion_changed)
        self.about.troubleshootRequested.connect(lambda: self._show_page(PAGE_HELP))
        self.about.updateRequested.connect(lambda: self._check_updates(silent=False))
        self.workspace.busyChanged.connect(self._on_busy)

        layout.addWidget(self.stack, 1)
        self.setCentralWidget(central)

    def _header(self) -> QHBoxLayout:
        header = QHBoxLayout()
        header.setSpacing(14)

        logo = QLabel()
        icon = resource_root() / "img" / "icon.png"
        if icon.exists():
            logo.setPixmap(
                QPixmap(str(icon)).scaled(
                    QSize(30, 30), Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation,
                )
            )
        brand = QLabel("ZarManager")
        brand.setProperty("role", "section")

        self.nav = PillNav()
        for key, icon_text in zip(MODE_KEYS, MODE_ICONS):
            self.nav.add_pill(self.t(key), icon_text)
        self.nav.set_animated(not self.cfg.get_bool("reduce_motion"))
        self.nav.currentChanged.connect(self._on_mode_changed)

        self.btn_settings = action_button("", "quiet")
        self.btn_about = action_button("", "quiet")
        self.btn_help = action_button("", "quiet")
        self.btn_settings.clicked.connect(lambda: self._show_page(PAGE_SETTINGS))
        self.btn_about.clicked.connect(lambda: self._show_page(PAGE_ABOUT))
        self.btn_help.clicked.connect(lambda: self._show_page(PAGE_HELP))

        header.addWidget(logo)
        header.addWidget(brand)
        header.addStretch()
        header.addWidget(self.nav)
        header.addStretch()
        header.addWidget(self.btn_help)
        header.addWidget(self.btn_about)
        header.addWidget(self.btn_settings)
        return header

    # -------------------------------------------------------------- navegação
    def _show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        if index == PAGE_HELP:
            self.help.refresh_engines()

    def _on_mode_changed(self, index: int) -> None:
        if 0 <= index < len(MODES):
            self.workspace.set_mode(MODES[index])
        self._show_page(PAGE_WORKSPACE)

    def _on_busy(self, busy: bool) -> None:
        # Durante um job não se troca de modo por baixo dos pés do worker.
        self.nav.setEnabled(not busy)

    # ----------------------------------------------------------------- tema
    def _on_tokens(self, tokens) -> None:
        self.nav.apply_tokens(tokens)
        self.workspace.apply_tokens(tokens)

    def _on_theme_changed(self, name: str) -> None:
        self.theme_manager.apply(name)

    def _on_motion_changed(self, reduce_motion: bool) -> None:
        self.nav.set_animated(not reduce_motion)

    # ------------------------------------------------------------ updates
    def _check_updates(self, silent: bool) -> None:
        from ui.update_dialog import GitHubFetchThread, UpdateDialog
        from services.versioning import is_newer

        if not silent:
            UpdateDialog(f"v{__version__}", self.t, self).exec()
            return

        self._update_thread = GitHubFetchThread(self)

        def on_result(data: dict) -> None:
            if is_newer(data.get("tag_name", ""), __version__):
                UpdateDialog(f"v{__version__}", self.t, self, pre_fetched=data).exec()

        self._update_thread.result_signal.connect(on_result)
        self._update_thread.start()

    # --------------------------------------------------------------- textos
    def retranslate(self) -> None:
        self.nav.set_labels([self.t(key) for key in MODE_KEYS])
        self.btn_settings.setText(self.t("nav_settings"))
        self.btn_about.setText(self.t("nav_about"))
        self.btn_help.setText(self.t("nav_help"))
        self.workspace.retranslate()
        self.settings.retranslate()
        self.about.retranslate()
        self.help.retranslate()

    # ------------------------------------------------------------ geometria
    def _restore_geometry(self) -> None:
        stored = self.cfg.get("window_geometry")
        if not stored:
            return
        try:
            from PySide6.QtCore import QByteArray

            self.restoreGeometry(QByteArray.fromBase64(stored.encode("ascii")))
        except Exception:
            pass

    def _save_geometry(self) -> None:
        try:
            self.cfg.set("window_geometry", bytes(self.saveGeometry().toBase64()).decode("ascii"))
        except Exception:
            pass

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.workspace.busy:
            choice = DialogManager.ask_custom(
                self,
                self.t("warn_exit_title"),
                self.t("warn_exit_msg"),
                [("stay", self.t("btn_exit_no")), ("quit", self.t("btn_exit_yes"))],
            )
            if choice != "quit":
                event.ignore()
                return
            self.workspace.request_cancel_for_exit()

        self._save_geometry()
        event.accept()
