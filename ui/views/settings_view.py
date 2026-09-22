"""Configurações, agrupadas por cartões."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox, QComboBox, QHBoxLayout, QLabel, QScrollArea, QSlider, QVBoxLayout, QWidget,
)

import locales
from ui.theme import SYSTEM_THEME, available_themes
from ui.widgets.card import Card, action_button


class SettingsView(QWidget):
    languageChanged = Signal()
    themeChanged = Signal(str)
    motionChanged = Signal(bool)

    def __init__(self, cfg, translator, sound, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.t = translator
        self.sound = sound
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

        self.lbl_title = QLabel()
        self.lbl_title.setProperty("role", "title")
        layout.addWidget(self.lbl_title)

        layout.addWidget(self._appearance_card())
        layout.addWidget(self._audio_card())
        layout.addWidget(self._performance_card())
        layout.addWidget(self._files_card())
        layout.addWidget(self._updates_card())
        layout.addStretch()

        scroll.setWidget(content)
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.addWidget(scroll)

    # --------------------------------------------------------------- cartões
    def _row(self, card: Card, label: QLabel, widget: QWidget) -> None:
        row = QHBoxLayout()
        row.addWidget(label)
        row.addStretch()
        row.addWidget(widget)
        card.add_layout(row)

    def _appearance_card(self) -> Card:
        card = Card()
        self.lbl_appearance = QLabel()
        self.lbl_appearance.setProperty("role", "section")
        card.add(self.lbl_appearance)

        self.lbl_language = QLabel()
        self.combo_language = QComboBox()
        for code, label in locales.LANGUAGES.items():
            self.combo_language.addItem(label, code)
        index = self.combo_language.findData(self.cfg.get("language"))
        if index >= 0:
            self.combo_language.setCurrentIndex(index)
        self.combo_language.setMinimumWidth(190)
        self.combo_language.currentIndexChanged.connect(self._on_language)
        self._row(card, self.lbl_language, self.combo_language)

        self.lbl_theme = QLabel()
        self.combo_theme = QComboBox()
        self.combo_theme.setMinimumWidth(190)
        for name in available_themes():
            self.combo_theme.addItem(name, name)
        theme_index = self.combo_theme.findData(self.cfg.get("theme") or SYSTEM_THEME)
        if theme_index >= 0:
            self.combo_theme.setCurrentIndex(theme_index)
        self.combo_theme.currentIndexChanged.connect(self._on_theme)
        self._row(card, self.lbl_theme, self.combo_theme)

        self.chk_motion = QCheckBox()
        self.chk_motion.setChecked(self.cfg.get_bool("reduce_motion"))
        self.chk_motion.toggled.connect(self._on_motion)
        card.add(self.chk_motion)

        self.lbl_motion_hint = QLabel()
        self.lbl_motion_hint.setProperty("role", "muted")
        self.lbl_motion_hint.setWordWrap(True)
        card.add(self.lbl_motion_hint)
        return card

    def _audio_card(self) -> Card:
        card = Card()
        self.lbl_audio = QLabel()
        self.lbl_audio.setProperty("role", "section")
        card.add(self.lbl_audio)

        self.chk_sfx = QCheckBox()
        self.chk_sfx.setChecked(self.cfg.get_bool("sfx_enabled"))
        self.chk_sfx.toggled.connect(self._on_sfx)
        card.add(self.chk_sfx)

        self.lbl_volume = QLabel()
        self.slider_volume = QSlider(Qt.Orientation.Horizontal)
        self.slider_volume.setRange(0, 100)
        self.slider_volume.setValue(int(self.cfg.get_float("sfx_volume") * 100))
        self.slider_volume.setFixedWidth(200)
        self.slider_volume.valueChanged.connect(self._on_volume)

        self.btn_test = action_button("", "ghost")
        self.btn_test.clicked.connect(lambda: self.sound.preview())

        row = QHBoxLayout()
        row.addWidget(self.lbl_volume)
        row.addStretch()
        row.addWidget(self.slider_volume)
        row.addWidget(self.btn_test)
        card.add_layout(row)

        if not getattr(self.sound, "available", True):
            self.chk_sfx.setEnabled(False)
            self.slider_volume.setEnabled(False)
            self.btn_test.setEnabled(False)
        return card

    def _performance_card(self) -> Card:
        card = Card()
        self.lbl_performance = QLabel()
        self.lbl_performance.setProperty("role", "section")
        card.add(self.lbl_performance)

        self.lbl_workers = QLabel()
        self.slider_workers = QSlider(Qt.Orientation.Horizontal)
        self.slider_workers.setRange(1, 16)
        self.slider_workers.setValue(self.cfg.get_int("workers", 1, 16))
        self.slider_workers.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider_workers.setTickInterval(1)
        self.slider_workers.valueChanged.connect(self._on_workers)

        card.add(self.lbl_workers)
        card.add(self.slider_workers)

        self.lbl_workers_hint = QLabel()
        self.lbl_workers_hint.setProperty("role", "muted")
        self.lbl_workers_hint.setWordWrap(True)
        card.add(self.lbl_workers_hint)
        return card

    def _files_card(self) -> Card:
        card = Card()
        self.lbl_files = QLabel()
        self.lbl_files.setProperty("role", "section")
        card.add(self.lbl_files)

        self.chk_keep = QCheckBox()
        self.chk_keep.setChecked(self.cfg.get_bool("keep_originals"))
        self.chk_keep.toggled.connect(lambda value: self.cfg.set("keep_originals", value))
        card.add(self.chk_keep)

        self.lbl_collision = QLabel()
        self.combo_collision = QComboBox()
        self.combo_collision.setMinimumWidth(190)
        for key in ("ASK", "SKIP", "OVERWRITE", "RENAME"):
            self.combo_collision.addItem(key, key)
        index = self.combo_collision.findData((self.cfg.get("collision_policy") or "ASK").upper())
        if index >= 0:
            self.combo_collision.setCurrentIndex(index)
        self.combo_collision.currentIndexChanged.connect(
            lambda: self.cfg.set("collision_policy", self.combo_collision.currentData())
        )
        self._row(card, self.lbl_collision, self.combo_collision)
        return card

    def _updates_card(self) -> Card:
        card = Card()
        self.lbl_updates = QLabel()
        self.lbl_updates.setProperty("role", "section")
        card.add(self.lbl_updates)

        self.chk_auto_update = QCheckBox()
        self.chk_auto_update.setChecked(self.cfg.get_bool("auto_update"))
        self.chk_auto_update.toggled.connect(lambda value: self.cfg.set("auto_update", value))
        card.add(self.chk_auto_update)
        return card

    # --------------------------------------------------------------- acções
    def _on_language(self) -> None:
        self.cfg.set("language", self.combo_language.currentData())
        self.languageChanged.emit()

    def _on_theme(self) -> None:
        name = self.combo_theme.currentData()
        self.cfg.set("theme", name)
        self.themeChanged.emit(name)

    def _on_motion(self, value: bool) -> None:
        self.cfg.set("reduce_motion", value)
        self.motionChanged.emit(value)

    def _on_sfx(self, value: bool) -> None:
        self.sound.set_enabled(value)

    def _on_volume(self, value: int) -> None:
        self.cfg.set("sfx_volume", value / 100.0)
        self.sound.set_volume(value / 100.0)

    def _on_workers(self, value: int) -> None:
        self.cfg.set("workers", value)
        self.lbl_workers.setText(self.t("set_workers", value=value))

    # --------------------------------------------------------------- textos
    def retranslate(self) -> None:
        self.lbl_title.setText(self.t("set_title"))
        self.lbl_appearance.setText(self.t("set_appearance"))
        self.lbl_language.setText(self.t("set_language"))
        self.lbl_theme.setText(self.t("set_theme"))
        self.chk_motion.setText(self.t("set_motion"))
        self.lbl_motion_hint.setText(self.t("set_motion_hint"))
        self.lbl_audio.setText(self.t("set_audio"))
        self.chk_sfx.setText(self.t("set_sfx"))
        self.lbl_volume.setText(self.t("set_volume"))
        self.btn_test.setText(self.t("set_test_sound"))
        self.lbl_performance.setText(self.t("set_performance"))
        self.lbl_workers.setText(self.t("set_workers", value=self.slider_workers.value()))
        self.lbl_workers_hint.setText(self.t("set_workers_hint"))
        self.lbl_files.setText(self.t("set_files"))
        self.chk_keep.setText(self.t("set_keep_originals"))
        self.lbl_collision.setText(self.t("set_collision"))
        self.lbl_updates.setText(self.t("set_updates"))
        self.chk_auto_update.setText(self.t("set_auto_update"))

        for index, key in enumerate(("collision_ask", "collision_skip",
                                     "collision_overwrite", "collision_rename")):
            self.combo_collision.setItemText(index, self.t(key))

        for index in range(self.combo_theme.count()):
            name = self.combo_theme.itemData(index)
            self.combo_theme.setItemText(index, name)
