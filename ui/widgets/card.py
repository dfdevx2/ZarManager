"""Peças reutilizáveis: cartões, títulos e linhas de informação."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame, QHBoxLayout, QLabel, QPushButton, QSizePolicy, QVBoxLayout, QWidget,
)


class Card(QFrame):
    """Superfície elevada com título opcional."""

    def __init__(self, title: str = "", subtitle: str = "", flat: bool = False, parent=None):
        super().__init__(parent)
        self.setObjectName("CardFlat" if flat else "Card")

        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(18, 16, 18, 16)
        self._layout.setSpacing(10)

        self.title_label = None
        self.subtitle_label = None

        if title:
            self.title_label = QLabel(title)
            self.title_label.setProperty("role", "section")
            self._layout.addWidget(self.title_label)
        if subtitle:
            self.subtitle_label = QLabel(subtitle)
            self.subtitle_label.setProperty("role", "muted")
            self.subtitle_label.setWordWrap(True)
            self._layout.addWidget(self.subtitle_label)

    def body(self) -> QVBoxLayout:
        return self._layout

    def add(self, widget: QWidget) -> QWidget:
        self._layout.addWidget(widget)
        return widget

    def add_layout(self, layout):
        self._layout.addLayout(layout)
        return layout

    def set_title(self, text: str) -> None:
        if self.title_label:
            self.title_label.setText(text)

    def set_subtitle(self, text: str) -> None:
        if self.subtitle_label:
            self.subtitle_label.setText(text)


class InfoRow(QWidget):
    """Linha 'rótulo .... valor', usada no Sobre e no diagnóstico."""

    def __init__(self, label: str, value: str = "", parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        self.label = QLabel(label)
        self.label.setProperty("role", "muted")
        self.value = QLabel(value)
        self.value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        self.value.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self.value.setWordWrap(True)

        layout.addWidget(self.label)
        layout.addStretch()
        layout.addWidget(self.value)

    def set_value(self, text: str) -> None:
        self.value.setText(text)

    def set_label(self, text: str) -> None:
        self.label.setText(text)


class StatusRow(QWidget):
    """Linha de motor: ✓/✗ + nome + versão. Usada no Troubleshooting."""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 2, 0, 2)
        layout.setSpacing(10)

        self.icon = QLabel("•")
        self.icon.setFixedWidth(18)
        self.name = QLabel("")
        self.detail = QLabel("")
        self.detail.setProperty("role", "muted")
        self.detail.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)

        layout.addWidget(self.icon)
        layout.addWidget(self.name)
        layout.addStretch()
        layout.addWidget(self.detail)

    def set_state(self, ok: bool, name: str, detail: str = "", optional: bool = False) -> None:
        self.icon.setText("✓" if ok else ("○" if optional else "✗"))
        self.icon.setProperty("role", "success" if ok else ("muted" if optional else "danger"))
        self.icon.style().unpolish(self.icon)
        self.icon.style().polish(self.icon)
        self.name.setText(name)
        self.detail.setText(detail)


def separator() -> QFrame:
    line = QFrame()
    line.setObjectName("Separator")
    line.setFrameShape(QFrame.Shape.HLine)
    line.setFixedHeight(1)
    line.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    return line


def action_button(text: str, variant: str = "", tooltip: str = "") -> QPushButton:
    button = QPushButton(text)
    if variant:
        button.setProperty("variant", variant)
    if tooltip:
        button.setToolTip(tooltip)
    button.setMinimumHeight(38)
    button.setCursor(Qt.CursorShape.PointingHandCursor)
    return button
