"""Onboarding em três passos.

A tela antiga era uma coluna de botões com "Sistema / Escuro / Claro / Steam /
Xbox" escritos a texto: escolhia-se o tema sem o ver. Aqui cada tema é um
cartão que se desenha a si próprio com a sua própria paleta.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QEasingCurve, QPropertyAnimation, QRectF, Qt, Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QButtonGroup, QComboBox, QGraphicsOpacityEffect, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QVBoxLayout, QWidget,
)

import locales
from ui.dialogs import DialogManager
from ui.theme import SYSTEM_THEME, THEMES
from ui.theme.tokens import Tokens
from ui.widgets.card import action_button

STEP_COUNT = 3


class ThemeCard(QPushButton):
    """Miniatura de uma janela, desenhada com os tokens do tema."""

    def __init__(self, theme_name: str, tokens: Tokens | None, parent=None):
        super().__init__(parent)
        self.theme_name = theme_name
        self.tokens = tokens
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedSize(168, 124)
        self.setProperty("sfx", "nav")

    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        body = QRectF(self.rect()).adjusted(2, 2, -2, -2)

        if self.tokens is None:                      # cartão "Sistema"
            painter.setBrush(QColor("#7F7F8A"))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(body, 12, 12)
            painter.setPen(QColor("#FFFFFF"))
            font = QFont(self.font())
            font.setWeight(QFont.Weight.DemiBold)
            painter.setFont(font)
            painter.drawText(body, Qt.AlignmentFlag.AlignCenter, self.text())
            self._draw_border(painter, body, QColor("#FFFFFF"))
            return

        t = self.tokens
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QColor(t.bg))
        painter.drawRoundedRect(body, 12, 12)

        # barra de pílulas em miniatura
        pill_area = QRectF(body.left() + 12, body.top() + 12, body.width() - 24, 18)
        painter.setBrush(QColor(t.surface))
        painter.drawRoundedRect(pill_area, 9, 9)
        active = QRectF(pill_area.left() + 3, pill_area.top() + 3, 44, 12)
        painter.setBrush(QColor(t.accent))
        painter.drawRoundedRect(active, 6, 6)

        # painel e linhas de conteúdo
        panel = QRectF(body.left() + 12, body.top() + 40, body.width() - 24, body.height() - 76)
        painter.setBrush(QColor(t.surface))
        painter.drawRoundedRect(panel, 8, 8)
        painter.setBrush(QColor(t.surface_alt))
        for row in range(3):
            line = QRectF(panel.left() + 8, panel.top() + 8 + row * 13, panel.width() - 16, 8)
            painter.drawRoundedRect(line, 4, 4)

        # barra de progresso
        track = QRectF(body.left() + 12, body.bottom() - 28, body.width() - 24, 6)
        painter.setBrush(QColor(t.surface_alt))
        painter.drawRoundedRect(track, 3, 3)
        filled = QRectF(track)
        filled.setWidth(track.width() * 0.62)
        painter.setBrush(QColor(t.accent))
        painter.drawRoundedRect(filled, 3, 3)

        painter.setPen(QColor(t.text_muted))
        label = QRectF(body.left() + 12, body.bottom() - 20, body.width() - 24, 16)
        painter.drawText(label, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.text())

        self._draw_border(painter, body, QColor(t.accent))

    def _draw_border(self, painter: QPainter, body: QRectF, accent: QColor) -> None:
        painter.setBrush(Qt.BrushStyle.NoBrush)
        if self.isChecked():
            painter.setPen(QPen(accent, 2.4))
            painter.drawRoundedRect(body, 12, 12)
        elif self.underMouse():
            glow = QColor(accent)
            glow.setAlphaF(0.55)
            painter.setPen(QPen(glow, 1.6))
            painter.drawRoundedRect(body, 12, 12)
        else:
            edge = QColor(accent)
            edge.setAlphaF(0.18)
            painter.setPen(QPen(edge, 1.0))
            painter.drawRoundedRect(body, 12, 12)

    def enterEvent(self, event):
        self.update()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.update()
        super().leaveEvent(event)


class WelcomeView(QWidget):
    finished = Signal()

    def __init__(self, cfg, translator, theme_manager, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.t = translator
        self.theme_manager = theme_manager

        self._setup_defaults()
        self._build()
        self.retranslate()

    # ------------------------------------------------------------ arranque
    def _setup_defaults(self) -> None:
        import os
        import platform

        if not self.cfg.get("language"):
            system_lang = (os.environ.get("LANG") or "en").lower()
            self.cfg.set("language", "pt-br" if "pt" in system_lang else "en")
        if not self.cfg.get("theme"):
            self.cfg.set("theme", "Preto" if platform.system() == "Linux" else SYSTEM_THEME)

    # --------------------------------------------------------------- layout
    def _build(self) -> None:
        outer = QVBoxLayout(self)
        outer.setContentsMargins(48, 40, 48, 32)
        outer.setSpacing(18)

        self.hero = QLabel()
        self.hero.setProperty("role", "hero")
        self.hero.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.subtitle = QLabel()
        self.subtitle.setProperty("role", "subtitle")
        self.subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_language_step())
        self.stack.addWidget(self._build_theme_step())
        self.stack.addWidget(self._build_directories_step())

        self.opacity = QGraphicsOpacityEffect(self.stack)
        self.opacity.setOpacity(1.0)
        self.stack.setGraphicsEffect(self.opacity)
        self._fade = QPropertyAnimation(self.opacity, b"opacity", self)

        self.step_label = QLabel()
        self.step_label.setProperty("role", "muted")

        self.btn_back = action_button("", "ghost")
        self.btn_next = action_button("", "primary")
        self.btn_back.clicked.connect(lambda: self._go(self.stack.currentIndex() - 1))
        self.btn_next.clicked.connect(self._next)

        footer = QHBoxLayout()
        footer.addWidget(self.step_label)
        footer.addStretch()
        footer.addWidget(self.btn_back)
        footer.addWidget(self.btn_next)

        outer.addStretch(1)
        outer.addWidget(self.hero)
        outer.addWidget(self.subtitle)
        outer.addSpacing(12)
        outer.addWidget(self.stack, 3)
        outer.addStretch(1)
        outer.addLayout(footer)

        self._update_footer()

    def _step_frame(self, title_attr: str, desc_attr: str) -> tuple[QWidget, QVBoxLayout]:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(10)
        layout.setAlignment(Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignTop)

        title = QLabel()
        title.setProperty("role", "section")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setattr(self, title_attr, title)

        description = QLabel()
        description.setProperty("role", "muted")
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        setattr(self, desc_attr, description)

        layout.addWidget(title)
        layout.addWidget(description)
        layout.addSpacing(10)
        return page, layout

    def _build_language_step(self) -> QWidget:
        page, layout = self._step_frame("lbl_lang_title", "lbl_lang_desc")

        self.combo_lang = QComboBox()
        for code, label in locales.LANGUAGES.items():
            self.combo_lang.addItem(label, code)
        index = self.combo_lang.findData(self.cfg.get("language"))
        if index >= 0:
            self.combo_lang.setCurrentIndex(index)
        self.combo_lang.setFixedWidth(260)
        self.combo_lang.currentIndexChanged.connect(self._on_language)

        row = QHBoxLayout()
        row.addStretch()
        row.addWidget(self.combo_lang)
        row.addStretch()
        layout.addLayout(row)
        return page

    def _build_theme_step(self) -> QWidget:
        page, layout = self._step_frame("lbl_theme_title", "lbl_theme_desc")

        self.theme_group = QButtonGroup(self)
        self.theme_group.setExclusive(True)
        grid = QHBoxLayout()
        grid.setSpacing(12)
        grid.addStretch()

        current = self.cfg.get("theme") or SYSTEM_THEME
        entries = [(SYSTEM_THEME, None), *[(name, tokens) for name, tokens in THEMES.items()]]
        for name, tokens in entries:
            card = ThemeCard(name, tokens, self)
            card.setText(name)
            card.setChecked(name == current)
            card.clicked.connect(lambda _checked=False, n=name: self._preview_theme(n))
            self.theme_group.addButton(card)
            grid.addWidget(card)

        grid.addStretch()
        layout.addLayout(grid)
        return page

    def _build_directories_step(self) -> QWidget:
        page, layout = self._step_frame("lbl_dirs_title", "lbl_dirs_desc")

        self.txt_source = QLineEdit(self.cfg.get("source_dir") or "")
        self.txt_target = QLineEdit(self.cfg.get("target_dir") or "")
        self.lbl_src = QLabel()
        self.lbl_tgt = QLabel()
        self.btn_src = action_button("", "ghost")
        self.btn_tgt = action_button("", "ghost")
        self.lbl_dir_warning = QLabel()
        self.lbl_dir_warning.setProperty("role", "warning")
        self.lbl_dir_warning.setWordWrap(True)
        self.lbl_dir_warning.setAlignment(Qt.AlignmentFlag.AlignCenter)

        for line_edit in (self.txt_source, self.txt_target):
            line_edit.setReadOnly(True)
            line_edit.setFixedWidth(360)

        self.btn_src.clicked.connect(lambda: self._pick("source_dir", self.txt_source))
        self.btn_tgt.clicked.connect(lambda: self._pick("target_dir", self.txt_target))

        for label, field, button in (
            (self.lbl_src, self.txt_source, self.btn_src),
            (self.lbl_tgt, self.txt_target, self.btn_tgt),
        ):
            row = QHBoxLayout()
            row.addStretch()
            label.setFixedWidth(90)
            row.addWidget(label)
            row.addWidget(field)
            row.addWidget(button)
            row.addStretch()
            layout.addLayout(row)

        layout.addWidget(self.lbl_dir_warning)
        return page

    # ------------------------------------------------------------- acções
    def _on_language(self, _index: int) -> None:
        self.cfg.set("language", self.combo_lang.currentData())
        self.retranslate()

    def _preview_theme(self, name: str) -> None:
        self.cfg.set("theme", name)
        self.theme_manager.apply(name)

    def _pick(self, key: str, field: QLineEdit) -> None:
        chosen = DialogManager.select_directory(self, self.t("btn_browse"), field.text())
        if chosen:
            self.cfg.set(key, chosen)
            field.setText(chosen)
            self._check_directories()

    def _check_directories(self) -> None:
        from services.file_service import FileService

        warnings = FileService.validate_directories(self.txt_source.text(), self.txt_target.text())
        self.lbl_dir_warning.setText(" ".join(self.t(key) for key in warnings))

    def _go(self, index: int) -> None:
        index = max(0, min(STEP_COUNT - 1, index))
        if index == self.stack.currentIndex():
            return

        if self.cfg.get_bool("reduce_motion"):
            self.stack.setCurrentIndex(index)
            self._update_footer()
            return

        self._fade.stop()
        self._fade.setDuration(150)
        self._fade.setEasingCurve(QEasingCurve(QEasingCurve.Type.InOutQuad))
        self._fade.setStartValue(1.0)
        self._fade.setEndValue(0.0)

        def swap():
            try:
                self._fade.finished.disconnect(swap)
            except RuntimeError:
                pass
            self.stack.setCurrentIndex(index)
            self._update_footer()
            self._fade.setStartValue(0.0)
            self._fade.setEndValue(1.0)
            self._fade.setDuration(220)
            self._fade.start()

        self._fade.finished.connect(swap)
        self._fade.start()

    def _next(self) -> None:
        if self.stack.currentIndex() >= STEP_COUNT - 1:
            self.cfg.set("first_boot_done", True)
            self.finished.emit()
            return
        self._go(self.stack.currentIndex() + 1)

    def _update_footer(self) -> None:
        index = self.stack.currentIndex()
        self.btn_back.setVisible(index > 0)
        self.btn_next.setText(
            self.t("btn_start_using") if index == STEP_COUNT - 1 else self.t("btn_next")
        )
        self.step_label.setText(self.t("welcome_step", current=index + 1, total=STEP_COUNT))
        if index == STEP_COUNT - 1:
            self._check_directories()

    # -------------------------------------------------------------- textos
    def retranslate(self) -> None:
        self.hero.setText(self.t("welcome_hero"))
        self.subtitle.setText(self.t("welcome_sub"))
        self.lbl_lang_title.setText(self.t("welcome_lang_title"))
        self.lbl_lang_desc.setText(self.t("welcome_lang_desc"))
        self.lbl_theme_title.setText(self.t("welcome_theme_title"))
        self.lbl_theme_desc.setText(self.t("welcome_theme_desc"))
        self.lbl_dirs_title.setText(self.t("welcome_dirs_title"))
        self.lbl_dirs_desc.setText(self.t("welcome_dirs_desc"))
        self.lbl_src.setText(self.t("lbl_source"))
        self.lbl_tgt.setText(self.t("lbl_target"))
        self.btn_src.setText(self.t("btn_browse"))
        self.btn_tgt.setText(self.t("btn_browse"))
        self.btn_back.setText(self.t("btn_back"))
        self._update_footer()
