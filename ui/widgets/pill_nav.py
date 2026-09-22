"""Barra de navegação "pílula flutuante".

Restrição que define toda a implementação: o QSS do Qt não tem `transition`
nem `animation`. Tudo o que se move aqui é QPropertyAnimation sobre
propriedades Qt registadas em Python, lidas no paintEvent.

Duas decisões que valem a pena explicar:

* A elevação NÃO move o widget. Mexer na geometria faria o layout recalcular
  posições a cada frame e as pílulas vizinhas tremeriam. Em vez disso a
  propriedade `lift` desloca apenas o desenho, dentro do rectângulo que o
  layout já reservou.
* O brilho NÃO usa QGraphicsDropShadowEffect. Esse efeito é renderizado por
  software, um widget só aceita um efeito de cada vez, e com cinco pílulas a
  animar nota-se. Rectângulos concêntricos com alfa decrescente custam quase
  nada e ficam melhores sobre fundos escuros.
"""

from __future__ import annotations

from PySide6.QtCore import (
    Property, QEasingCurve, QPropertyAnimation, QRectF, QSize, Qt, Signal,
)
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import QAbstractButton, QButtonGroup, QFrame, QHBoxLayout, QSizePolicy

from ui.theme.tokens import Tokens, get as get_tokens

LIFT_PX = 3.0
GLOW_LAYERS = 5
HOVER_MS = 340
LEAVE_MS = 260
GLOW_MS = 200
SLIDE_MS = 320
OVERSHOOT = 2.6          # a "física de salto" vive neste número


def _mix(a: QColor, b: QColor, ratio: float) -> QColor:
    ratio = max(0.0, min(1.0, ratio))
    return QColor(
        int(a.red() + (b.red() - a.red()) * ratio),
        int(a.green() + (b.green() - a.green()) * ratio),
        int(a.blue() + (b.blue() - a.blue()) * ratio),
    )


class PillButton(QAbstractButton):
    def __init__(self, text: str, icon_text: str = "", parent=None):
        super().__init__(parent)
        self.setText(text)
        self.icon_text = icon_text
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setProperty("sfx", "nav")          # lido pelo SoundManager

        self._tokens: Tokens = get_tokens("Preto")
        self._animated = True
        self._lift = 0.0
        self._glow = 0.0
        self._selection = 0.0

        self._anim_lift = QPropertyAnimation(self, b"lift", self)
        self._anim_glow = QPropertyAnimation(self, b"glow", self)
        self._anim_sel = QPropertyAnimation(self, b"selection", self)

        self.toggled.connect(self._on_toggled)

    # ------------------------------------------------------ propriedades
    def _get_lift(self) -> float:
        return self._lift

    def _set_lift(self, value: float) -> None:
        self._lift = value
        self.update()

    lift = Property(float, _get_lift, _set_lift)

    def _get_glow(self) -> float:
        return self._glow

    def _set_glow(self, value: float) -> None:
        self._glow = value
        self.update()

    glow = Property(float, _get_glow, _set_glow)

    def _get_selection(self) -> float:
        return self._selection

    def _set_selection(self, value: float) -> None:
        self._selection = value
        self.update()

    selection = Property(float, _get_selection, _set_selection)

    # ------------------------------------------------------------ estado
    def apply_tokens(self, tokens: Tokens) -> None:
        self._tokens = tokens
        self.update()

    def set_animated(self, animated: bool) -> None:
        self._animated = animated
        if not animated:
            for anim in (self._anim_lift, self._anim_glow, self._anim_sel):
                anim.stop()
            self._lift = 0.0
            self._glow = 1.0 if self.isChecked() else 0.0
            self._selection = 1.0 if self.isChecked() else 0.0
            self.update()

    def _animate(self, anim: QPropertyAnimation, end: float, ms: int,
                 curve=QEasingCurve.Type.OutCubic, overshoot: float | None = None) -> None:
        if not self._animated:
            anim.stop()
            name = anim.propertyName().data().decode()
            setattr(self, f"_{name}", end)
            self.update()
            return
        easing = QEasingCurve(curve)
        if overshoot is not None:
            easing.setOvershoot(overshoot)
        anim.stop()
        anim.setDuration(ms)
        anim.setEasingCurve(easing)
        anim.setStartValue(getattr(self, f"_{anim.propertyName().data().decode()}"))
        anim.setEndValue(end)
        anim.start()

    def _on_toggled(self, checked: bool) -> None:
        self._animate(self._anim_sel, 1.0 if checked else 0.0, GLOW_MS)
        if not checked and not self.underMouse():
            self._animate(self._anim_glow, 0.0, LEAVE_MS)
        elif checked:
            self._animate(self._anim_glow, 1.0, GLOW_MS)

    # ------------------------------------------------------------ eventos
    def enterEvent(self, event):
        self._animate(self._anim_lift, LIFT_PX, HOVER_MS,
                      QEasingCurve.Type.OutBack, OVERSHOOT)
        self._animate(self._anim_glow, 1.0, GLOW_MS)
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._animate(self._anim_lift, 0.0, LEAVE_MS)
        if not self.isChecked():
            self._animate(self._anim_glow, 0.0, LEAVE_MS)
        super().leaveEvent(event)

    def sizeHint(self) -> QSize:
        metrics = self.fontMetrics()
        label = f"{self.icon_text}  {self.text()}" if self.icon_text else self.text()
        return QSize(metrics.horizontalAdvance(label) + 40, max(38, metrics.height() + 20))

    # ------------------------------------------------------------- pintura
    def paintEvent(self, _event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        tokens = self._tokens
        accent = QColor(tokens.accent)
        body = QRectF(self.rect()).adjusted(4, 5, -4, -4).translated(0, -self._lift)
        radius = body.height() / 2

        # Brilho: camadas concêntricas, sem QGraphicsEffect.
        if self._glow > 0.01:
            painter.setPen(Qt.PenStyle.NoPen)
            for layer in range(GLOW_LAYERS, 0, -1):
                colour = QColor(accent)
                colour.setAlphaF(0.055 * self._glow * (GLOW_LAYERS - layer + 1) / GLOW_LAYERS)
                painter.setBrush(colour)
                painter.drawRoundedRect(
                    body.adjusted(-layer, -layer, layer, layer), radius + layer, radius + layer
                )

        # O preenchimento do item activo é desenhado pelo indicador da barra
        # (para poder deslizar); aqui só entra o realce do hover.
        if self._selection < 0.99 and self._glow > 0.01:
            hover = QColor(tokens.surface_hover)
            hover.setAlphaF(0.85 * self._glow * (1.0 - self._selection))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(hover)
            painter.drawRoundedRect(body, radius, radius)

        edge = QColor(accent)
        edge.setAlphaF(0.18 + 0.55 * self._glow * (1.0 - self._selection))
        painter.setBrush(Qt.BrushStyle.NoBrush)
        painter.setPen(QPen(edge, 1.2))
        painter.drawRoundedRect(body, radius, radius)

        font = QFont(self.font())
        font.setWeight(QFont.Weight.DemiBold if self._selection > 0.5 else QFont.Weight.Medium)
        painter.setFont(font)

        colour = _mix(QColor(tokens.text_muted), QColor(tokens.accent_text), self._selection)
        if self._selection < 0.5:
            colour = _mix(colour, QColor(tokens.text), self._glow)
        painter.setPen(colour)

        label = f"{self.icon_text}  {self.text()}" if self.icon_text else self.text()
        painter.drawText(body, Qt.AlignmentFlag.AlignCenter, label)


class PillNav(QFrame):
    """Barra de pílulas com indicador deslizante."""

    currentChanged = Signal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("PillNav")
        self.setSizePolicy(QSizePolicy.Policy.Maximum, QSizePolicy.Policy.Fixed)

        self._tokens: Tokens = get_tokens("Preto")
        self._animated = True
        self._indicator = QRectF()
        self._anim = QPropertyAnimation(self, b"indicator", self)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(6, 5, 6, 5)
        layout.setSpacing(4)

        self.group = QButtonGroup(self)
        self.group.setExclusive(True)
        self.group.idToggled.connect(self._on_id_toggled)
        self._buttons: list[PillButton] = []

    # ------------------------------------------------------ propriedades
    def _get_indicator(self) -> QRectF:
        return self._indicator

    def _set_indicator(self, rect: QRectF) -> None:
        self._indicator = rect
        self.update()

    indicator = Property(QRectF, _get_indicator, _set_indicator)

    # --------------------------------------------------------------- API
    def add_pill(self, text: str, icon_text: str = "", data=None) -> PillButton:
        button = PillButton(text, icon_text, self)
        button.apply_tokens(self._tokens)
        button.set_animated(self._animated)
        button.setProperty("pill_data", data)
        index = len(self._buttons)
        self._buttons.append(button)
        self.group.addButton(button, index)
        self.layout().addWidget(button)
        if index == 0:
            button.setChecked(True)
        return button

    def set_labels(self, labels: list[str]) -> None:
        for button, label in zip(self._buttons, labels):
            button.setText(label)
            button.updateGeometry()
        self.updateGeometry()
        self._move_indicator(animated=False)

    def current_index(self) -> int:
        return self.group.checkedId()

    def current_data(self):
        button = self.group.checkedButton()
        return button.property("pill_data") if button else None

    def set_current_index(self, index: int) -> None:
        if 0 <= index < len(self._buttons):
            self._buttons[index].setChecked(True)

    def apply_tokens(self, tokens: Tokens) -> None:
        self._tokens = tokens
        for button in self._buttons:
            button.apply_tokens(tokens)
        self.update()

    def set_animated(self, animated: bool) -> None:
        self._animated = animated
        for button in self._buttons:
            button.set_animated(animated)

    # ------------------------------------------------------------ eventos
    def _on_id_toggled(self, index: int, checked: bool) -> None:
        if not checked:
            return
        self._move_indicator()
        self.currentChanged.emit(index)

    def _move_indicator(self, animated: bool = True) -> None:
        button = self.group.checkedButton()
        if button is None:
            return
        geometry = QRectF(button.geometry()).adjusted(4, 5, -4, -4)
        if not animated or not self._animated or self._indicator.isNull():
            self._anim.stop()
            self._set_indicator(geometry)
            return
        self._anim.stop()
        self._anim.setDuration(SLIDE_MS)
        self._anim.setEasingCurve(QEasingCurve(QEasingCurve.Type.OutCubic))
        self._anim.setStartValue(self._indicator)
        self._anim.setEndValue(geometry)
        self._anim.start()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._move_indicator(animated=False)

    def showEvent(self, event):
        super().showEvent(event)
        self._move_indicator(animated=False)

    def keyPressEvent(self, event):
        """Setas e Enter: importa para quem usa comando ou um handheld."""
        key = event.key()
        if key in (Qt.Key.Key_Left, Qt.Key.Key_Right):
            step = -1 if key == Qt.Key.Key_Left else 1
            index = (self.current_index() + step) % max(1, len(self._buttons))
            self.set_current_index(index)
            self._buttons[index].setFocus(Qt.FocusReason.TabFocusReason)
            event.accept()
            return
        super().keyPressEvent(event)

    def paintEvent(self, event):
        super().paintEvent(event)
        if self._indicator.isNull():
            return
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)
        radius = self._indicator.height() / 2

        accent = QColor(self._tokens.accent)
        painter.setPen(Qt.PenStyle.NoPen)
        for layer in range(4, 0, -1):
            halo = QColor(accent)
            halo.setAlphaF(0.05 * (5 - layer) / 4)
            painter.setBrush(halo)
            painter.drawRoundedRect(
                self._indicator.adjusted(-layer, -layer, layer, layer), radius + layer, radius + layer
            )
        painter.setBrush(accent)
        painter.drawRoundedRect(self._indicator, radius, radius)
