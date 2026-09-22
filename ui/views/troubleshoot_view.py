"""Resolução de problemas.

Era um QMessageBox com uma parede de texto para os três sistemas ao mesmo
tempo. Agora é uma página: o cartão do sistema actual aparece aberto, os
outros ficam recolhidos, e há acções que fazem o trabalho em vez de o
descrever (verificar motores, copiar comando, copiar diagnóstico, abrir logs).
"""

from __future__ import annotations

import json
import platform

from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtGui import QDesktopServices, QGuiApplication
from PySide6.QtWidgets import (
    QHBoxLayout, QLabel, QScrollArea, QVBoxLayout, QWidget,
)

from core.engines import ENGINES, EngineResolver
from services.logging_service import LoggerService
from services.paths import describe, log_dir
from ui.widgets.card import Card, StatusRow, action_button
from version import __version__

MAC_COMMAND = "xattr -cr /Applications/ZarManager.app"
LINUX_COMMAND = "chmod +x ZarManager-*.AppImage"


class Collapsible(Card):
    """Cartão com corpo que abre e fecha."""

    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.header_button = action_button("", "quiet")
        self.header_button.clicked.connect(self.toggle)
        self.header_button.setCursor(Qt.CursorShape.PointingHandCursor)

        self.title = QLabel()
        self.title.setProperty("role", "section")

        row = QHBoxLayout()
        row.addWidget(self.title)
        row.addStretch()
        row.addWidget(self.header_button)
        self.add_layout(row)

        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 4, 0, 0)
        self.content_layout.setSpacing(10)
        self.add(self.content)

        self.set_expanded(False)

    def set_expanded(self, expanded: bool) -> None:
        self.content.setVisible(expanded)
        self.header_button.setText("▴" if expanded else "▾")

    def toggle(self) -> None:
        self.set_expanded(not self.content.isVisible())


class TroubleshootView(QWidget):
    def __init__(self, cfg, translator, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.t = translator
        self.resolver = EngineResolver()
        self._build()
        self.retranslate()
        self.refresh_engines()

    def _build(self) -> None:
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 8, 0)
        layout.setSpacing(14)

        self.lbl_title = QLabel()
        self.lbl_title.setProperty("role", "title")
        self.lbl_sub = QLabel()
        self.lbl_sub.setProperty("role", "muted")
        self.lbl_sub.setWordWrap(True)
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_sub)

        layout.addWidget(self._engines_card())

        system = platform.system()
        order = {
            "Windows": ["win", "lin", "mac", "perf"],
            "Darwin": ["mac", "win", "lin", "perf"],
        }.get(system, ["lin", "win", "mac", "perf"])

        self.sections: dict[str, Collapsible] = {}
        for position, key in enumerate(order):
            section = self._section(key)
            section.set_expanded(position == 0)
            self.sections[key] = section
            layout.addWidget(section)

        layout.addStretch()
        scroll.setWidget(content)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    def _engines_card(self) -> Card:
        card = Card()
        self.lbl_engines = QLabel()
        self.lbl_engines.setProperty("role", "section")
        self.lbl_engines_desc = QLabel()
        self.lbl_engines_desc.setProperty("role", "muted")
        self.lbl_engines_desc.setWordWrap(True)
        card.add(self.lbl_engines)
        card.add(self.lbl_engines_desc)

        self.engine_rows: dict[str, StatusRow] = {}
        for engine_id in ENGINES:
            row = StatusRow()
            self.engine_rows[engine_id] = row
            card.add(row)

        self.btn_check = action_button("", "ghost")
        self.btn_diag = action_button("", "ghost")
        self.btn_logs = action_button("", "ghost")
        self.lbl_feedback = QLabel()
        self.lbl_feedback.setProperty("role", "success")

        self.btn_check.clicked.connect(self.refresh_engines)
        self.btn_diag.clicked.connect(self.copy_diagnostics)
        self.btn_logs.clicked.connect(self.open_logs)

        row = QHBoxLayout()
        row.setSpacing(10)
        row.addWidget(self.btn_check)
        row.addWidget(self.btn_diag)
        row.addWidget(self.btn_logs)
        row.addWidget(self.lbl_feedback)
        row.addStretch()
        card.add_layout(row)
        return card

    def _section(self, key: str) -> Collapsible:
        section = Collapsible()
        body = QLabel()
        body.setWordWrap(True)
        body.setProperty("role", "muted")
        section.content_layout.addWidget(body)
        section.body_label = body

        command = {"mac": MAC_COMMAND, "lin": LINUX_COMMAND}.get(key)
        if command:
            code = QLabel(command)
            code.setObjectName("Console")
            code.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            code.setWordWrap(True)
            section.content_layout.addWidget(code)

            button = action_button("", "ghost")
            button.clicked.connect(lambda _checked=False, text=command: self.copy(text))
            section.copy_button = button

            row = QHBoxLayout()
            row.addWidget(button)
            row.addStretch()
            section.content_layout.addLayout(row)
        return section

    # --------------------------------------------------------------- acções
    def refresh_engines(self) -> None:
        self.resolver = EngineResolver()
        for engine_id, row in self.engine_rows.items():
            spec = ENGINES[engine_id]
            status = self.resolver.probe(engine_id)
            if status.native:
                row.set_state(True, spec.label, self.t("ts_engine_native"))
                continue

            detail = status.version or status.path or ""
            if not status.found:
                detail = "" if spec.bundled else self.t("ev_engine_optional_missing", engines="")
            row.set_state(status.found, spec.label, detail[:70], optional=not spec.bundled)

    def copy(self, text: str) -> None:
        QGuiApplication.clipboard().setText(text)
        self.lbl_feedback.setText(self.t("ts_copied"))
        QTimer.singleShot(2500, lambda: self.lbl_feedback.setText(""))

    def copy_diagnostics(self) -> None:
        engines = {
            engine_id: self.resolver.probe(engine_id).path or "ausente"
            for engine_id in ENGINES
        }
        payload = {
            "version": __version__,
            "environment": describe(),
            "engines": engines,
            "config": {
                "theme": self.cfg.get("theme"),
                "language": self.cfg.get("language"),
                "workers": self.cfg.get("workers"),
                "collision_policy": self.cfg.get("collision_policy"),
            },
        }
        report = json.dumps(payload, indent=2, ensure_ascii=False)
        tail = LoggerService.tail(40)
        if tail:
            report += "\n\n--- log ---\n" + tail
        self.copy(report)

    def open_logs(self) -> None:
        directory = log_dir()
        directory.mkdir(parents=True, exist_ok=True)
        QDesktopServices.openUrl(QUrl.fromLocalFile(str(directory)))

    # --------------------------------------------------------------- textos
    def retranslate(self) -> None:
        self.lbl_title.setText(self.t("ts_title"))
        self.lbl_sub.setText(self.t("ts_sub"))
        self.lbl_engines.setText(self.t("ts_engines"))
        self.lbl_engines_desc.setText(self.t("ts_engines_desc"))
        self.btn_check.setText(self.t("btn_check_engines"))
        self.btn_diag.setText(self.t("btn_copy_diag"))
        self.btn_logs.setText(self.t("btn_open_logs"))

        for key, section in self.sections.items():
            section.title.setText(self.t(f"ts_{key}_title"))
            section.body_label.setText(self.t(f"ts_{key}_body"))
            if hasattr(section, "copy_button"):
                section.copy_button.setText(self.t("btn_copy_command"))

        self.refresh_engines()
