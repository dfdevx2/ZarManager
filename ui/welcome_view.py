import os
import platform
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont

import locales

class WelcomeView(QWidget):
    def __init__(self, cfg, apply_theme_cb, on_finish_cb):
        super().__init__()
        self.cfg = cfg
        self.apply_theme_cb = apply_theme_cb
        self.on_finish_cb = on_finish_cb

        self._setup_defaults()
        self._build_ui()
        self.retranslate_ui() # Aplica traduções logo no arranque

    def get_text(self, key: str) -> str:
        return locales.get_text(self.cfg.get("language") or "en", key)

    def _setup_defaults(self):
        if not self.cfg.get("language"):
            sys_lang = os.environ.get("LANG", "en").lower()
            self.cfg.set("language", "pt-br" if "pt" in sys_lang else "en")
        
        if not self.cfg.get("theme"):
            self.cfg.set("theme", "Preto" if platform.system() == "Linux" else "Sistema")
        
        self.apply_theme_cb()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.setSpacing(20)

        # Labels com referências guardadas (self) para podermos alterar os textos em tempo real
        title = QLabel("ZarManager")
        font_title = QFont()
        font_title.setPointSize(36)
        font_title.setBold(True)
        title.setFont(font_title)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.lbl_subtitle = QLabel()
        font_sub = QFont()
        font_sub.setPointSize(14)
        self.lbl_subtitle.setFont(font_sub)
        self.lbl_subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Seletor de Idioma
        lang_layout = QHBoxLayout()
        lang_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_lang = QLabel()
        
        self.lang_combo = QComboBox()
        self.lang_combo.addItems(["pt-br", "en"])
        idx = self.lang_combo.findText(self.cfg.get("language"))
        if idx >= 0: self.lang_combo.setCurrentIndex(idx)
        
        self.lang_combo.currentTextChanged.connect(self._change_lang)
        
        lang_layout.addWidget(self.lbl_lang)
        lang_layout.addWidget(self.lang_combo)

        # Seletor de Tema
        self.lbl_instruction = QLabel()
        self.lbl_instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)

        theme_layout = QHBoxLayout()
        theme_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        theme_layout.setSpacing(10)
        
        btn_system = QPushButton("Sistema")
        btn_dark = QPushButton("Escuro/Dark")
        btn_light = QPushButton("Claro/Light")
        btn_steam = QPushButton("Steam")
        btn_xbox = QPushButton("Xbox")
        
        btn_system.clicked.connect(lambda: self._preview_theme("Sistema"))
        btn_dark.clicked.connect(lambda: self._preview_theme("Preto"))
        btn_light.clicked.connect(lambda: self._preview_theme("Branco"))
        btn_steam.clicked.connect(lambda: self._preview_theme("Steam"))
        btn_xbox.clicked.connect(lambda: self._preview_theme("Xbox"))

        theme_layout.addWidget(btn_system)
        theme_layout.addWidget(btn_dark)
        theme_layout.addWidget(btn_light)
        theme_layout.addWidget(btn_steam)
        theme_layout.addWidget(btn_xbox)

        self.btn_continue = QPushButton()
        self.btn_continue.setMinimumHeight(45)
        self.btn_continue.setMinimumWidth(280)
        self.btn_continue.setStyleSheet("font-weight: bold; font-size: 14px;")
        self.btn_continue.clicked.connect(self._on_continue)

        layout.addWidget(title)
        layout.addWidget(self.lbl_subtitle)
        layout.addSpacing(15)
        layout.addLayout(lang_layout)
        layout.addSpacing(15)
        layout.addWidget(self.lbl_instruction)
        layout.addLayout(theme_layout)
        layout.addSpacing(30)
        layout.addWidget(self.btn_continue, 0, Qt.AlignmentFlag.AlignCenter)

    def retranslate_ui(self):
        """Muda todos os textos na mosca sem reiniciar."""
        self.lbl_subtitle.setText(self.get_text("msg_welcome") or "Bem-vindo / Welcome")
        self.lbl_lang.setText((self.get_text("lbl_language") or "Idioma") + ":")
        self.lbl_instruction.setText(self.get_text("msg_choose_theme") or "Escolha o tema inicial:")
        self.btn_continue.setText(self.get_text("btn_continue") or "Continuar / Continue")

    def _change_lang(self, lang: str):
        self.cfg.set("language", lang)
        self.retranslate_ui()

    def _preview_theme(self, theme_name: str):
        self.cfg.set("theme", theme_name)
        self.apply_theme_cb()

    def _on_continue(self):
        self.on_finish_cb()