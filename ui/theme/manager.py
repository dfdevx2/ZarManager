"""Aplicação de temas.

Mudanças face ao código antigo:

* Uma única fonte de verdade (tokens), em vez de paletas duplicadas em app.py
  e theme_mac.py.
* Sem o laço `unpolish/polish` sobre `app.allWidgets()`: `setStyleSheet` na
  QApplication já repolimenta tudo, e o laço era caro em janelas grandes.
* No macOS, o estilo nativo só é usado no tema "Sistema". Misturar
  `setStyle("macOS")` com uma paleta personalizada produzia resultados
  inconsistentes; os temas personalizados usam Fusion, como no resto.
"""

from __future__ import annotations

import platform

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QPalette
from PySide6.QtWidgets import QApplication

from ui.theme import qss
from ui.theme.tokens import DEFAULT_DARK, DEFAULT_LIGHT, THEMES, Tokens, get

SYSTEM_THEME = "Sistema"
_IS_MAC = platform.system() == "Darwin"
_IS_LINUX = platform.system() == "Linux"


def available_themes() -> list[str]:
    return [SYSTEM_THEME, *THEMES.keys()]


def _system_prefers_dark(app: QApplication) -> bool:
    try:
        return app.styleHints().colorScheme() == Qt.ColorScheme.Dark
    except AttributeError:
        window = app.style().standardPalette().color(QPalette.ColorRole.Window)
        return window.lightness() < 128


def resolve(app: QApplication, name: str | None) -> tuple[str, Tokens]:
    """Nome pedido -> (nome efectivo, tokens)."""
    requested = name or SYSTEM_THEME
    if requested != SYSTEM_THEME:
        return requested, get(requested)

    # No Linux o tema do sistema raramente combina com a app; o escuro é a
    # escolha que não surpreende ninguém.
    if _IS_LINUX:
        return DEFAULT_DARK, get(DEFAULT_DARK)

    effective = DEFAULT_DARK if _system_prefers_dark(app) else DEFAULT_LIGHT
    return effective, get(effective)


def build_palette(t: Tokens) -> QPalette:
    palette = QPalette()
    bg, surface, surface_alt = QColor(t.bg), QColor(t.surface), QColor(t.surface_alt)
    text, muted, accent = QColor(t.text), QColor(t.text_muted), QColor(t.accent)

    palette.setColor(QPalette.ColorRole.Window, bg)
    palette.setColor(QPalette.ColorRole.WindowText, text)
    palette.setColor(QPalette.ColorRole.Base, surface)
    palette.setColor(QPalette.ColorRole.AlternateBase, surface_alt)
    palette.setColor(QPalette.ColorRole.Text, text)
    palette.setColor(QPalette.ColorRole.Button, surface_alt)
    palette.setColor(QPalette.ColorRole.ButtonText, text)
    palette.setColor(QPalette.ColorRole.BrightText, QColor(t.danger))
    palette.setColor(QPalette.ColorRole.ToolTipBase, surface)
    palette.setColor(QPalette.ColorRole.ToolTipText, text)
    palette.setColor(QPalette.ColorRole.Link, accent)
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor(t.accent_hover))
    palette.setColor(QPalette.ColorRole.Highlight, accent)
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(t.accent_text))
    palette.setColor(QPalette.ColorRole.PlaceholderText, muted)

    for role in (
        QPalette.ColorRole.Text,
        QPalette.ColorRole.WindowText,
        QPalette.ColorRole.ButtonText,
    ):
        palette.setColor(QPalette.ColorGroup.Disabled, role, muted)

    return palette


class ThemeManager:
    """Mantém o tema actual e notifica quem precisa de se repintar."""

    def __init__(self, app: QApplication, cfg):
        self.app = app
        self.cfg = cfg
        self.tokens: Tokens = get(DEFAULT_DARK)
        self.effective_name: str = DEFAULT_DARK
        self._listeners: list = []

    def subscribe(self, callback) -> None:
        """Widgets que desenham à mão (as pílulas, por exemplo) precisam dos
        tokens novos, porque o QSS não chega lá."""
        if callback not in self._listeners:
            self._listeners.append(callback)

    def apply(self, name: str | None = None) -> Tokens:
        requested = name if name is not None else self.cfg.get("theme")
        effective, tokens = resolve(self.app, requested)

        self.effective_name = effective
        self.tokens = tokens

        if _IS_MAC and (requested or SYSTEM_THEME) == SYSTEM_THEME:
            self.app.setStyle("macOS")
            self.app.setPalette(self.app.style().standardPalette())
            self.app.setStyleSheet("")
        else:
            self.app.setStyle("Fusion")
            self.app.setPalette(build_palette(tokens))
            self.app.setStyleSheet(qss.build(tokens))

        for callback in list(self._listeners):
            try:
                callback(tokens)
            except RuntimeError:
                self._listeners.remove(callback)      # widget já destruído

        return tokens
