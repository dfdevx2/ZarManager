"""Lista de itens com estado e progresso por linha.

A lista antiga era um QListWidget de texto simples: o estado de cada ficheiro
só aparecia na consola, em texto corrido. Aqui cada linha desenha o seu
próprio estado, formato detectado e barra de progresso.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, QSize, Qt, Signal
from PySide6.QtGui import QColor, QFont, QPainter, QPen
from PySide6.QtWidgets import (
    QAbstractItemView, QListWidget, QListWidgetItem, QStyledItemDelegate,
)

from core.events import ItemState
from ui.theme.tokens import Tokens, get as get_tokens

ROW_HEIGHT = 56
CHECK_SIZE = 18
DATA_ROLE = Qt.ItemDataRole.UserRole + 1

_STATE_TOKEN = {
    ItemState.DONE: "success",
    ItemState.FAILED: "danger",
    ItemState.SKIPPED: "text_muted",
    ItemState.CANCELLED: "warning",
    ItemState.RUNNING: "accent",
    ItemState.QUEUED: "text_muted",
}


class ItemDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.tokens: Tokens = get_tokens("Preto")
        self.labels: dict[str, str] = {}

    def apply_tokens(self, tokens: Tokens) -> None:
        self.tokens = tokens

    def sizeHint(self, option, index) -> QSize:
        return QSize(option.rect.width(), ROW_HEIGHT)

    @staticmethod
    def check_rect(row: QRect) -> QRect:
        return QRect(row.left() + 12, row.center().y() - CHECK_SIZE // 2, CHECK_SIZE, CHECK_SIZE)

    def paint(self, painter: QPainter, option, index) -> None:
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        tokens = self.tokens
        data = index.data(DATA_ROLE) or {}
        row = option.rect.adjusted(4, 3, -4, -3)
        checked = index.data(Qt.ItemDataRole.CheckStateRole) == Qt.CheckState.Checked

        # fundo
        background = QColor(tokens.surface_alt if checked else tokens.surface)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(background)
        painter.drawRoundedRect(row, tokens.radius_md, tokens.radius_md)

        # checkbox
        box = self.check_rect(row)
        accent = QColor(tokens.accent)
        if checked:
            painter.setBrush(accent)
            painter.setPen(QPen(accent, 1))
            painter.drawRoundedRect(box, 5, 5)
            painter.setPen(QPen(QColor(tokens.accent_text), 2))
            painter.drawLine(box.left() + 4, box.center().y(), box.center().x() - 1, box.bottom() - 4)
            painter.drawLine(box.center().x() - 1, box.bottom() - 4, box.right() - 3, box.top() + 5)
        else:
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(QColor(tokens.border_strong), 1.2))
            painter.drawRoundedRect(box, 5, 5)

        text_left = box.right() + 14
        status_width = 150
        text_width = max(60, row.width() - text_left + row.left() - status_width - 16)

        # nome
        name_font = QFont(option.font)
        name_font.setWeight(QFont.Weight.DemiBold)
        painter.setFont(name_font)
        painter.setPen(QColor(tokens.text if checked else tokens.text_muted))
        name_rect = QRect(text_left, row.top() + 9, text_width, 18)
        painter.drawText(
            name_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            option.fontMetrics.elidedText(str(data.get("name", "")), Qt.TextElideMode.ElideMiddle, text_width),
        )

        # subtítulo: formato detectado e última linha do motor
        small = QFont(option.font)
        small.setPointSizeF(max(8.0, option.font.pointSizeF() - 1.5))
        painter.setFont(small)
        painter.setPen(QColor(tokens.text_muted))
        subtitle = data.get("subtitle", "")
        sub_rect = QRect(text_left, row.top() + 27, text_width, 16)
        painter.drawText(
            sub_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter,
            option.fontMetrics.elidedText(str(subtitle), Qt.TextElideMode.ElideRight, text_width),
        )

        # estado, à direita
        state = data.get("state", ItemState.QUEUED)
        colour = QColor(getattr(tokens, _STATE_TOKEN.get(state, "text_muted")))
        painter.setPen(colour)
        status_rect = QRect(row.right() - status_width - 12, row.top() + 9, status_width, 18)
        painter.drawText(
            status_rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter,
            str(data.get("status", "")),
        )

        # progresso, apenas enquanto corre
        percent = float(data.get("percent") or 0.0)
        if state is ItemState.RUNNING and percent > 0:
            track = QRect(row.right() - status_width - 12, row.top() + 32, status_width, 4)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(tokens.border))
            painter.drawRoundedRect(track, 2, 2)
            filled = QRect(track)
            filled.setWidth(max(2, int(track.width() * min(1.0, percent))))
            painter.setBrush(accent)
            painter.drawRoundedRect(filled, 2, 2)

        painter.restore()

    def editorEvent(self, event, model, option, index) -> bool:
        """Clicar em qualquer ponto da linha alterna a seleção."""
        from PySide6.QtCore import QEvent

        if event.type() == QEvent.Type.MouseButtonRelease and event.button() == Qt.MouseButton.LeftButton:
            current = index.data(Qt.ItemDataRole.CheckStateRole)
            new_state = (
                Qt.CheckState.Unchecked if current == Qt.CheckState.Checked else Qt.CheckState.Checked
            )
            model.setData(index, new_state, Qt.ItemDataRole.CheckStateRole)
            return True
        return super().editorEvent(event, model, option, index)


class ItemList(QListWidget):
    selectionCountChanged = Signal(int, int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.delegate = ItemDelegate(self)
        self.setItemDelegate(self.delegate)
        self.setMouseTracking(True)
        self.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setUniformItemSizes(True)
        self._by_name: dict[str, QListWidgetItem] = {}
        self.itemChanged.connect(lambda _item: self._emit_counts())

    def apply_tokens(self, tokens: Tokens) -> None:
        self.delegate.apply_tokens(tokens)
        self.viewport().update()

    def _force_full_repaint(self) -> None:
        """Repintura garantida após uma alteração em lote com sinais bloqueados.

        `self.blockSignals(True)` impede o `itemChanged` (o sinal do próprio
        QListWidget) de disparar, mas em teoria não devia impedir o modelo
        interno de propagar `dataChanged` para a view. Na prática, em
        combinação com `setUniformItemSizes(True)`, já vimos o repaint ficar
        preso ao estado antigo até ao primeiro clique manual. Em vez de
        confiar só em `viewport().update()`, emitimos nós mesmos o
        `dataChanged` para o intervalo inteiro -- é o sinal exacto de que o
        Qt depende para repintar, por isso funciona independentemente do que
        estiver a acontecer por baixo com o `blockSignals`.
        """
        model = self.model()
        if model is not None and model.rowCount() > 0:
            top_left = model.index(0, 0)
            bottom_right = model.index(model.rowCount() - 1, 0)
            model.dataChanged.emit(
                top_left, bottom_right,
                [Qt.ItemDataRole.CheckStateRole, DATA_ROLE],
            )
        self.viewport().update()
        self.update()

    # --------------------------------------------------------------- dados
    def populate(self, paths: list[Path], empty_message: str = "") -> None:
        self.blockSignals(True)
        self.clear()
        self._by_name.clear()

        if not paths:
            placeholder = QListWidgetItem("")
            placeholder.setFlags(Qt.ItemFlag.NoItemFlags)
            placeholder.setData(DATA_ROLE, {"name": empty_message, "subtitle": "", "status": ""})
            self.addItem(placeholder)
            self.blockSignals(False)
            self._force_full_repaint()
            self._emit_counts()
            return

        for path in paths:
            item = QListWidgetItem("")
            item.setFlags(Qt.ItemFlag.ItemIsEnabled | Qt.ItemFlag.ItemIsUserCheckable)
            # Fica por marcar aqui de propósito -- ver nota abaixo.
            item.setCheckState(Qt.CheckState.Unchecked)
            item.setData(DATA_ROLE, {
                "name": path.name,
                "path": str(path),
                "subtitle": "",
                "status": "",
                "state": ItemState.QUEUED,
                "percent": 0.0,
            })
            self.addItem(item)
            self._by_name[path.name] = item

        self.blockSignals(False)
        # Marcar tudo aqui, ANTES de inserir na lista, e só repintar no fim
        # (com dataChanged manual e tudo) continuava a deixar as caixas em
        # branco até ao primeiro clique -- confirmado por vídeo, mesmo depois
        # do dataChanged. `set_all_checked()` faz exactamente essa marcação
        # em massa e, esse sim, repinta correctamente (mesmo vídeo). Em vez
        # de manter dois caminhos que deviam ser equivalentes mas não são na
        # prática, a carga inicial reaproveita o único que comprovadamente
        # funciona.
        self.set_all_checked(True)

    def checked_paths(self) -> list[Path]:
        paths = []
        for index in range(self.count()):
            item = self.item(index)
            if item.checkState() == Qt.CheckState.Checked:
                data = item.data(DATA_ROLE) or {}
                if data.get("path"):
                    paths.append(Path(data["path"]))
        return paths

    def set_all_checked(self, checked: bool) -> None:
        self.blockSignals(True)
        state = Qt.CheckState.Checked if checked else Qt.CheckState.Unchecked
        for index in range(self.count()):
            item = self.item(index)
            if item.flags() & Qt.ItemFlag.ItemIsUserCheckable:
                item.setCheckState(state)
        self.blockSignals(False)
        self._force_full_repaint()
        self._emit_counts()

    def toggle_all(self) -> None:
        self.set_all_checked(self.checked_count() != self.selectable_count())

    def selectable_count(self) -> int:
        return len(self._by_name)

    def checked_count(self) -> int:
        return len(self.checked_paths())

    def _emit_counts(self) -> None:
        self.selectionCountChanged.emit(self.checked_count(), self.selectable_count())

    # -------------------------------------------------------------- estado
    def update_status(self, name: str, status_text: str, state, percent: float | None,
                      subtitle: str | None = None) -> None:
        item = self._by_name.get(name)
        if item is None:
            return
        data = dict(item.data(DATA_ROLE) or {})
        data["status"] = status_text
        data["state"] = state
        data["percent"] = percent if percent is not None else data.get("percent", 0.0)
        if subtitle is not None:
            data["subtitle"] = subtitle
        item.setData(DATA_ROLE, data)
        self.viewport().update(self.visualItemRect(item))

    def reset_status(self) -> None:
        for item in self._by_name.values():
            data = dict(item.data(DATA_ROLE) or {})
            data.update({"status": "", "state": ItemState.QUEUED, "percent": 0.0, "subtitle": ""})
            item.setData(DATA_ROLE, data)
        self.viewport().update()

    def set_locked(self, locked: bool) -> None:
        """Durante um job a lista não deve mudar por baixo dos pés."""
        for item in self._by_name.values():
            flags = item.flags()
            if locked:
                item.setFlags(flags & ~Qt.ItemFlag.ItemIsUserCheckable)
            else:
                item.setFlags(flags | Qt.ItemFlag.ItemIsUserCheckable)
