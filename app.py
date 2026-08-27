import sys
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtGui import QPalette, QColor, QCloseEvent
from PySide6.QtCore import Qt

from config import ConfigManager
from version import __version__
from ui.welcome_view import WelcomeView
from ui.main_view import MainController
from ui.dialogs import DialogManager

class ZarManagerApp(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle(f"ZarManager v{__version__}")
        self.setMinimumSize(1050, 750)

        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        if not self.cfg.get("first_boot_done"):
            self.welcome = WelcomeView(self.cfg, self.apply_theme, self.boot_main_app)
            self.stack.addWidget(self.welcome)
        else:
            self.apply_theme()
            self.boot_main_app()

    def apply_theme(self):
        app = QApplication.instance()
        sys_os = platform.system()
        theme_name = self.cfg.get("theme") or "Sistema"
        
        # 1. Limpa estilos anteriores para evitar conflitos residuais de memória
        app.setStyleSheet("")
        
        # 2. Isolamento Estrito por Sistema Operacional
        if sys_os == "Darwin":
            from ui.theme_mac import apply_mac_theme
            apply_mac_theme(app, theme_name)
        else:
            # Arquitetura Original Windows / Linux
            app.setStyle("Fusion")
            
            tooltip_style = """
                QToolTip {
                    background-color: #2c3e50;
                    color: #ffffff;
                    border: 1px solid #34495e;
                    border-radius: 6px;
                    padding: 6px 10px;
                    font-family: "Segoe UI", Roboto, Arial;
                    font-size: 13px;
                }
            """
            app.setStyleSheet(tooltip_style)
            
            if sys_os == "Linux" and theme_name == "Sistema":
                theme_name = "Preto"
                
            if theme_name == "Sistema":
                try:
                    is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
                except AttributeError:
                    is_dark = app.style().standardPalette().color(QPalette.ColorRole.Window).lightness() < 128
                theme_name = "Preto" if is_dark else "Branco"

            # Base limpa do sistema para evitar artefatos
            palette = app.style().standardPalette()
            
            if theme_name == "Preto":
                palette.setColor(QPalette.ColorRole.Window, QColor(12, 12, 12))          
                palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Base, QColor(6, 6, 6))            
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(16, 16, 16))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
                palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Button, QColor(22, 22, 22))       
                palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
                palette.setColor(QPalette.ColorRole.Link, QColor(138, 43, 226))       
                palette.setColor(QPalette.ColorRole.Highlight, QColor(138, 43, 226))  
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
                
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(120, 120, 120))
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(120, 120, 120))
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(120, 120, 120))
                
            elif theme_name == "Steam":
                palette.setColor(QPalette.ColorRole.Window, QColor(23, 29, 37))
                palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Base, QColor(13, 19, 27))         
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(27, 40, 56))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
                palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Button, QColor(42, 71, 94))
                palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
                palette.setColor(QPalette.ColorRole.Link, QColor(102, 192, 244))      
                palette.setColor(QPalette.ColorRole.Highlight, QColor(102, 192, 244)) 
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)
                
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(100, 120, 140))
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(100, 120, 140))
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(100, 120, 140))

            elif theme_name == "Xbox":
                palette.setColor(QPalette.ColorRole.Window, QColor(16, 30, 18))
                palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Base, QColor(10, 20, 12))         
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 40, 25))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
                palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Button, QColor(26, 60, 32))
                palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
                palette.setColor(QPalette.ColorRole.Link, QColor(16, 124, 16))        
                palette.setColor(QPalette.ColorRole.Highlight, QColor(16, 124, 16))   
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
                
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(100, 130, 110))
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(100, 130, 110))
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(100, 130, 110))
                
            elif theme_name == "Branco":
                palette.setColor(QPalette.ColorRole.Window, QColor(245, 246, 248))       
                palette.setColor(QPalette.ColorRole.WindowText, QColor(30, 30, 30))      
                palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))         
                palette.setColor(QPalette.ColorRole.AlternateBase, QColor(238, 240, 242))
                palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(44, 62, 80))
                palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
                palette.setColor(QPalette.ColorRole.Text, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.Button, QColor(230, 232, 235))       
                palette.setColor(QPalette.ColorRole.ButtonText, QColor(30, 30, 30))
                palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
                palette.setColor(QPalette.ColorRole.Link, QColor(52, 152, 219))          
                palette.setColor(QPalette.ColorRole.Highlight, QColor(52, 152, 219))     
                palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
                
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, QColor(150, 150, 150))
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, QColor(150, 150, 150))
                palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, QColor(150, 150, 150))

            app.setPalette(palette)

        # 3. Força a atualização visual imediata de TODOS os widgets abertos
        # A sintaxe correta no PySide6 exige o uso do objeto QStyle para aplicar a repintura
        current_style = app.style()
        for widget in app.allWidgets():
            current_style.unpolish(widget)
            current_style.polish(widget)
            widget.update()

    def boot_main_app(self):
        self.cfg.set("first_boot_done", True)
        self.main_view = MainController(self.cfg, f"v{__version__}", self.apply_theme)
        self.stack.addWidget(self.main_view)
        self.stack.setCurrentWidget(self.main_view)

    def closeEvent(self, event: QCloseEvent):
        if hasattr(self, 'main_view') and self.main_view.active_threads:
            title = self.main_view.get_text("warn_exit_title", "Aviso de Encerramento")
            msg = self.main_view.get_text("warn_exit_msg", "Existem processos ativos em segundo plano.\nSe fechar agora, o programa irá cancelar e abortar tudo de forma segura.\n\nDeseja mesmo sair?")
            btn_yes = self.main_view.get_text("btn_exit_yes", "Sair e Abortar")
            btn_no = self.main_view.get_text("btn_exit_no", "Cancelar e Voltar")
            
            resp = DialogManager.ask_custom(self, title, msg, [btn_yes, btn_no])
            
            if resp == btn_yes:
                for mode, worker in self.main_view.active_threads.items():
                    if worker and worker.manager:
                        worker.manager.request_cancel()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

def main():
    app = QApplication(sys.argv)
    cfg = ConfigManager()
    window = ZarManagerApp(cfg)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()