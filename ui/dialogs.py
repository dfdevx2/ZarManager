"""Diálogos.

`ask_custom` passou a devolver a CHAVE da opção e não o texto do botão. Antes,
o chamador comparava strings traduzidas para saber o que o utilizador
escolheu -- bastava mudar uma tradução para partir a lógica.
"""

from __future__ import annotations

from PySide6.QtWidgets import QFileDialog, QMessageBox, QWidget


class DialogManager:
    @staticmethod
    def show_error(parent: QWidget | None, title: str, text: str) -> None:
        QMessageBox.critical(parent, title, text)

    @staticmethod
    def show_warning(parent: QWidget | None, title: str, text: str) -> None:
        QMessageBox.warning(parent, title, text)

    @staticmethod
    def show_info(parent: QWidget | None, title: str, text: str) -> None:
        QMessageBox.information(parent, title, text)

    @staticmethod
    def select_directory(parent: QWidget | None, title: str, start_dir: str = "") -> str:
        return QFileDialog.getExistingDirectory(
            parent, title, start_dir, QFileDialog.Option.ShowDirsOnly
        )

    @staticmethod
    def ask_custom(
        parent: QWidget | None,
        title: str,
        text: str,
        options: list[tuple[str, str]],
        icon: QMessageBox.Icon = QMessageBox.Icon.Question,
    ) -> str | None:
        """options: [(chave, rótulo), ...]. Devolve a chave escolhida."""
        box = QMessageBox(parent)
        box.setWindowTitle(title)
        box.setText(text)
        box.setIcon(icon)

        buttons = {}
        for key, label in options:
            button = box.addButton(label, QMessageBox.ButtonRole.ActionRole)
            buttons[button] = key

        box.exec()
        return buttons.get(box.clickedButton())
