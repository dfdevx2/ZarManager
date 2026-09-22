"""Tela Sobre."""

from __future__ import annotations

import platform

from PySide6.QtCore import QSize, Qt, QUrl, Signal
from PySide6.QtGui import QDesktopServices, QPixmap
from PySide6.QtWidgets import QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget

from core.engines import ENGINES, EngineResolver
from services.paths import resource_root
from ui.widgets.card import Card, InfoRow, action_button
from version import __version__

GITHUB_URL = "https://github.com/dfdevx2/ZarManager"
KOFI_URL = "https://ko-fi.com/dfdx047"
LICENSE_NAME = "ZarManager Non-Commercial License"


class AboutView(QWidget):
    troubleshootRequested = Signal()
    updateRequested = Signal()

    def __init__(self, cfg, translator, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.t = translator
        self.resolver = EngineResolver()
        self._build()
        self.retranslate()

    def _build(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(14)

        layout.addWidget(self._header_card())
        layout.addWidget(self._engines_card())
        layout.addLayout(self._actions_row())
        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _header_card(self) -> Card:
        card = Card()
        header = QHBoxLayout()
        header.setSpacing(16)

        logo = QLabel()
        icon = resource_root() / "img" / "icon.png"
        if icon.exists():
            pixmap = QPixmap(str(icon)).scaled(
                QSize(72, 72), Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            logo.setPixmap(pixmap)
        logo.setFixedSize(72, 72)

        title_column = QVBoxLayout()
        title_column.setSpacing(2)
        self.lbl_name = QLabel("ZarManager")
        self.lbl_name.setProperty("role", "title")
        self.lbl_tagline = QLabel()
        self.lbl_tagline.setProperty("role", "muted")
        self.lbl_tagline.setWordWrap(True)
        title_column.addWidget(self.lbl_name)
        title_column.addWidget(self.lbl_tagline)

        header.addWidget(logo)
        header.addLayout(title_column, 1)
        card.add_layout(header)

        self.row_version = InfoRow("", f"v{__version__}")
        self.row_platform = InfoRow("", f"{platform.system()} {platform.machine()}")
        self.row_dev = InfoRow("", "dfdevx2")
        self.row_license = InfoRow("", LICENSE_NAME)
        for row in (self.row_version, self.row_platform, self.row_dev, self.row_license):
            card.add(row)
        return card

    def _engines_card(self) -> Card:
        card = Card()
        self.lbl_engines = QLabel()
        self.lbl_engines.setProperty("role", "section")
        self.lbl_engines_desc = QLabel()
        self.lbl_engines_desc.setProperty("role", "muted")
        self.lbl_engines_desc.setWordWrap(True)
        card.add(self.lbl_engines)
        card.add(self.lbl_engines_desc)

        for spec in ENGINES.values():
            row = InfoRow(spec.label, spec.license)
            row.value.setProperty("role", "muted")
            row.setToolTip(spec.homepage)
            card.add(row)
        return card

    def _actions_row(self) -> QHBoxLayout:
        self.btn_repo = action_button("", "ghost")
        self.btn_kofi = action_button("", "ghost")
        self.btn_update = action_button("", "primary")
        self.btn_trouble = action_button("", "ghost")

        self.btn_repo.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(GITHUB_URL)))
        self.btn_kofi.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(KOFI_URL)))
        self.btn_update.clicked.connect(self.updateRequested.emit)
        self.btn_trouble.clicked.connect(self.troubleshootRequested.emit)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.btn_repo)
        row.addWidget(self.btn_kofi)
        row.addWidget(self.btn_trouble)
        row.addStretch()
        row.addWidget(self.btn_update)
        return row

    def retranslate(self) -> None:
        self.lbl_tagline.setText(self.t("about_tagline"))
        self.row_version.set_label(self.t("about_version"))
        self.row_platform.set_label(self.t("about_platform"))
        self.row_dev.set_label(self.t("about_dev"))
        self.row_license.set_label(self.t("about_license"))
        self.lbl_engines.setText(self.t("about_engines"))
        self.lbl_engines_desc.setText(self.t("about_engines_desc"))
        self.btn_repo.setText(self.t("btn_repo"))
        self.btn_kofi.setText(self.t("btn_kofi"))
        self.btn_update.setText(self.t("btn_check_update"))
        self.btn_trouble.setText(self.t("btn_troubleshoot"))
