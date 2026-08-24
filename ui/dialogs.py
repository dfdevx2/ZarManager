from PySide6.QtWidgets import QMessageBox, QFileDialog, QWidget
from typing import Optional, List

class DialogManager:
    """
    Gestor centralizado de janelas de diálogo nativas usando PySide6.
    Garante que os avisos e seletores de pastas seguem o tema do sistema operativo.
    """
    
    @staticmethod
    def show_error(parent: Optional[QWidget], title: str, text: str):
        QMessageBox.critical(parent, title, text)

    @staticmethod
    def show_warning(parent: Optional[QWidget], title: str, text: str):
        QMessageBox.warning(parent, title, text)

    @staticmethod
    def show_info(parent: Optional[QWidget], title: str, text: str):
        QMessageBox.information(parent, title, text)

    @staticmethod
    def select_directory(parent: Optional[QWidget], title: str, start_dir: str = "") -> str:
        """Abre o seletor nativo de pastas do sistema."""
        return QFileDialog.getExistingDirectory(
            parent, 
            title, 
            start_dir,
            QFileDialog.Option.ShowDirsOnly
        )

    @staticmethod
    def ask_custom(parent: Optional[QWidget], title: str, text: str, buttons: List[str]) -> str:
        """
        Cria uma caixa de diálogo com botões personalizados (ex: Sobrescrever, Pular, Cancelar)
        e devolve o texto do botão exato que o utilizador clicou.
        """
        msg_box = QMessageBox(parent)
        msg_box.setWindowTitle(title)
        msg_box.setText(text)
        msg_box.setIcon(QMessageBox.Icon.Question)

        for btn_text in buttons:
            msg_box.addButton(btn_text, QMessageBox.ButtonRole.ActionRole)
            
        msg_box.exec()
        
        # Identifica qual foi o botão clicado para devolver a string
        if msg_box.clickedButton():
            return msg_box.clickedButton().text()
            
        return ""