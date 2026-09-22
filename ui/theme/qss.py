"""Gerador de QSS a partir dos tokens.

Nota importante para quem mexer aqui: o QSS do Qt NÃO suporta `transition`
nem `animation`. Toda a física das pílulas (elevação, brilho, indicador
deslizante) é feita em Python com QPropertyAnimation -- ver ui/widgets/pill_nav.py.

Os estilos de botão são escolhidos por propriedade dinâmica em vez de
setStyleSheet inline:

    botao.setProperty("variant", "primary")   # primary | danger | ghost | quiet
"""

from __future__ import annotations

from ui.theme.tokens import Tokens


def build(t: Tokens) -> str:
    font = f'font-family: {t.font_family};' if t.font_family else ""
    return f"""
/* ---------------------------------------------------------------- base */
QWidget {{
    background-color: {t.bg};
    color: {t.text};
    {font}
    font-size: 13px;
}}
QMainWindow, QDialog {{ background-color: {t.bg}; }}

QLabel {{ background: transparent; }}
QLabel[role="title"]    {{ font-size: 26px; font-weight: 700; }}
QLabel[role="subtitle"] {{ font-size: 15px; color: {t.text_muted}; }}
QLabel[role="section"]  {{ font-size: 15px; font-weight: 600; }}
QLabel[role="muted"]    {{ color: {t.text_muted}; }}
QLabel[role="danger"]   {{ color: {t.danger}; }}
QLabel[role="warning"]  {{ color: {t.warning}; }}
QLabel[role="success"]  {{ color: {t.success}; }}
QLabel[role="hero"]     {{ font-size: 44px; font-weight: 800; letter-spacing: -1px; }}
QLabel[role="metric"]   {{ font-size: 22px; font-weight: 700; }}

/* -------------------------------------------------------------- cartões */
QFrame#Card {{
    background-color: {t.surface};
    border: 1px solid {t.border};
    border-radius: {t.radius_lg}px;
}}
QFrame#CardFlat {{
    background-color: {t.surface_alt};
    border: 1px solid {t.border};
    border-radius: {t.radius_md}px;
}}
QFrame#Separator {{ background-color: {t.border}; border: none; max-height: 1px; }}
QFrame#PillNav {{
    background: transparent;
    border: none;
}}

/* -------------------------------------------------------------- botões */
QPushButton {{
    background-color: {t.surface_alt};
    color: {t.text};
    border: 1px solid {t.border};
    border-radius: {t.radius_md}px;
    padding: 8px 16px;
    font-weight: 600;
}}
QPushButton:hover  {{ background-color: {t.surface_hover}; border-color: {t.border_strong}; }}
QPushButton:pressed {{ background-color: {t.border}; }}
QPushButton:disabled {{ color: {t.text_muted}; background-color: {t.surface}; border-color: {t.border}; }}

QPushButton[variant="primary"] {{
    background-color: {t.accent}; color: {t.accent_text}; border: 1px solid {t.accent};
}}
QPushButton[variant="primary"]:hover {{ background-color: {t.accent_hover}; border-color: {t.accent_hover}; }}
QPushButton[variant="primary"]:disabled {{ background-color: {t.surface_alt}; color: {t.text_muted}; border-color: {t.border}; }}

QPushButton[variant="danger"] {{
    background-color: transparent; color: {t.danger}; border: 1px solid {t.danger};
}}
QPushButton[variant="danger"]:hover {{ background-color: {t.danger}; color: #FFFFFF; }}
QPushButton[variant="danger"]:disabled {{ color: {t.text_muted}; border-color: {t.border}; background: transparent; }}

QPushButton[variant="ghost"] {{ background-color: transparent; border-color: {t.border}; }}
QPushButton[variant="ghost"]:hover {{ background-color: {t.surface_hover}; }}

QPushButton[variant="quiet"] {{
    background: transparent; border: none; color: {t.text_muted}; padding: 6px 10px;
}}
QPushButton[variant="quiet"]:hover {{ color: {t.text}; background-color: {t.surface_hover}; }}

/* -------------------------------------------------------------- campos */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QComboBox {{
    background-color: {t.surface_alt};
    border: 1px solid {t.border};
    border-radius: {t.radius_md}px;
    padding: 7px 10px;
    selection-background-color: {t.accent};
    selection-color: {t.accent_text};
}}
QLineEdit:focus, QTextEdit:focus, QComboBox:focus {{ border-color: {t.accent}; }}
QLineEdit:read-only {{ color: {t.text_muted}; }}

QComboBox::drop-down {{ border: none; width: 24px; }}
QComboBox::down-arrow {{
    image: none; border-left: 4px solid transparent; border-right: 4px solid transparent;
    border-top: 5px solid {t.text_muted}; margin-right: 8px;
}}
QComboBox QAbstractItemView {{
    background-color: {t.surface};
    border: 1px solid {t.border};
    border-radius: {t.radius_md}px;
    selection-background-color: {t.accent};
    selection-color: {t.accent_text};
    padding: 4px;
    outline: none;
}}

/* --------------------------------------------------------------- listas */
QListWidget, QListView, QTreeView {{
    background-color: {t.surface};
    border: 1px solid {t.border};
    border-radius: {t.radius_md}px;
    padding: 4px;
    outline: none;
}}
QListWidget::item {{ border-radius: {t.radius_sm}px; padding: 2px; }}
QListWidget::item:hover {{ background-color: {t.surface_hover}; }}
QListWidget::item:selected {{ background-color: {t.surface_alt}; color: {t.text}; }}

/* ------------------------------------------------------------ checkbox */
QCheckBox {{ spacing: 8px; background: transparent; }}
QCheckBox::indicator {{
    width: 17px; height: 17px;
    border: 1px solid {t.border_strong};
    border-radius: 5px;
    background-color: {t.surface_alt};
}}
QCheckBox::indicator:hover {{ border-color: {t.accent}; }}
QCheckBox::indicator:checked {{ background-color: {t.accent}; border-color: {t.accent}; }}
QCheckBox::indicator:disabled {{ border-color: {t.border}; background-color: {t.surface}; }}

/* ------------------------------------------------------------ progresso */
QProgressBar {{
    background-color: {t.surface_alt};
    border: none;
    border-radius: 5px;
    height: 10px;
    text-align: center;
    color: transparent;
}}
QProgressBar::chunk {{ background-color: {t.accent}; border-radius: 5px; }}
QProgressBar[variant="thin"] {{ height: 5px; border-radius: 3px; }}
QProgressBar[variant="thin"]::chunk {{ border-radius: 3px; }}

/* -------------------------------------------------------------- slider */
QSlider::groove:horizontal {{ height: 5px; background: {t.surface_alt}; border-radius: 3px; }}
QSlider::sub-page:horizontal {{ background: {t.accent}; border-radius: 3px; }}
QSlider::handle:horizontal {{
    background: {t.text}; width: 16px; height: 16px;
    margin: -6px 0; border-radius: 8px;
}}
QSlider::handle:horizontal:hover {{ background: {t.accent}; }}

/* ---------------------------------------------------------- scrollbars */
QScrollBar:vertical {{ background: transparent; width: 10px; margin: 2px; }}
QScrollBar::handle:vertical {{ background: {t.border_strong}; border-radius: 5px; min-height: 30px; }}
QScrollBar::handle:vertical:hover {{ background: {t.accent}; }}
QScrollBar:horizontal {{ background: transparent; height: 10px; margin: 2px; }}
QScrollBar::handle:horizontal {{ background: {t.border_strong}; border-radius: 5px; min-width: 30px; }}
QScrollBar::add-line, QScrollBar::sub-line {{ height: 0; width: 0; }}
QScrollBar::add-page, QScrollBar::sub-page {{ background: transparent; }}

/* -------------------------------------------------------------- consola */
QTextEdit#Console {{
    background-color: {t.console_bg};
    color: {t.console_text};
    border: 1px solid {t.border};
    border-radius: {t.radius_md}px;
    font-family: "JetBrains Mono", "Cascadia Mono", "DejaVu Sans Mono", Menlo, monospace;
    font-size: 12px;
    padding: 8px;
}}

/* ------------------------------------------------------------- tooltips */
QToolTip {{
    background-color: {t.surface};
    color: {t.text};
    border: 1px solid {t.border_strong};
    border-radius: {t.radius_sm}px;
    padding: 6px 10px;
}}

/* --------------------------------------------------------------- grupos */
QGroupBox {{
    border: 1px solid {t.border};
    border-radius: {t.radius_md}px;
    margin-top: 14px;
    padding: 12px;
    font-weight: 600;
}}
QGroupBox::title {{ subcontrol-origin: margin; left: 12px; padding: 0 6px; color: {t.text_muted}; }}

QScrollArea {{ border: none; background: transparent; }}
QScrollArea > QWidget > QWidget {{ background: transparent; }}
QMessageBox {{ background-color: {t.surface}; }}
"""
