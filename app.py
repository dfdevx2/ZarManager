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
        
        # macOS usa tema translúcido nativo, Windows/Linux usam Fusion
        if sys_os == "Darwin":
            app.setStyle("macOS")
        else:
            app.setStyle("Fusion")
            
        tooltip_style = """
            QToolTip {
                background-color: #2c3e50;
                color: #ffffff;
                border: 1px solid #34495e;
                border-radius: 6px;
                padding: 6px 10px;
                font-family: -apple-system, "Segoe UI", Roboto, Arial;
                font-size: 13px;
            }
        """
        app.setStyleSheet(tooltip_style)
        
        theme_name = self.cfg.get("theme") or "Sistema"
        
        # RESET DA PALETA NO LINUX/WINDOWS PARA EVITAR SOBREPOSIÇÃO DE CORES
        if sys_os != "Darwin":
            app.setPalette(app.style().standardPalette())
            
        palette = app.palette()
        
        if theme_name == "Sistema":
            try:
                is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
            except AttributeError:
                is_dark = palette.color(QPalette.Window).lightness() < 128
            theme_name = "Preto" if is_dark else "Branco"

        if theme_name == "Preto":
            palette.setColor(QPalette.Window, QColor(12, 12, 12))          
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(6, 6, 6))            
            palette.setColor(QPalette.AlternateBase, QColor(16, 16, 16))
            palette.setColor(QPalette.ToolTipBase, QColor(44, 62, 80))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(22, 22, 22))       
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(138, 43, 226))       
            palette.setColor(QPalette.Highlight, QColor(138, 43, 226))  
            palette.setColor(QPalette.HighlightedText, Qt.white)
            # Definir cores de desativado previne textos ilegíveis no Linux
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(120, 120, 120))
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(120, 120, 120))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(120, 120, 120))
            
        elif theme_name == "Branco":
            palette.setColor(QPalette.Window, QColor(245, 246, 248))       
            palette.setColor(QPalette.WindowText, QColor(30, 30, 30))      
            palette.setColor(QPalette.Base, QColor(255, 255, 255))         
            palette.setColor(QPalette.AlternateBase, QColor(238, 240, 242))
            palette.setColor(QPalette.ToolTipBase, QColor(44, 62, 80))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, QColor(30, 30, 30))
            palette.setColor(QPalette.Button, QColor(230, 232, 235))       
            palette.setColor(QPalette.ButtonText, QColor(30, 30, 30))
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(52, 152, 219))          
            palette.setColor(QPalette.Highlight, QColor(52, 152, 219))     
            palette.setColor(QPalette.HighlightedText, Qt.white)
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(150, 150, 150))
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(150, 150, 150))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(150, 150, 150))
            
        elif theme_name == "Steam":
            palette.setColor(QPalette.Window, QColor(23, 29, 37))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(13, 19, 27))         
            palette.setColor(QPalette.AlternateBase, QColor(27, 40, 56))
            palette.setColor(QPalette.ToolTipBase, QColor(44, 62, 80))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(42, 71, 94))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(102, 192, 244))      
            palette.setColor(QPalette.Highlight, QColor(102, 192, 244)) 
            palette.setColor(QPalette.HighlightedText, Qt.white)
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 120, 140))
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(100, 120, 140))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 120, 140))

        elif theme_name == "Xbox":
            palette.setColor(QPalette.Window, QColor(16, 30, 18))
            palette.setColor(QPalette.WindowText, Qt.white)
            palette.setColor(QPalette.Base, QColor(10, 20, 12))         
            palette.setColor(QPalette.AlternateBase, QColor(20, 40, 25))
            palette.setColor(QPalette.ToolTipBase, QColor(44, 62, 80))
            palette.setColor(QPalette.ToolTipText, Qt.white)
            palette.setColor(QPalette.Text, Qt.white)
            palette.setColor(QPalette.Button, QColor(26, 60, 32))
            palette.setColor(QPalette.ButtonText, Qt.white)
            palette.setColor(QPalette.BrightText, Qt.red)
            palette.setColor(QPalette.Link, QColor(16, 124, 16))        
            palette.setColor(QPalette.Highlight, QColor(16, 124, 16))   
            palette.setColor(QPalette.HighlightedText, Qt.white)
            palette.setColor(QPalette.Disabled, QPalette.Text, QColor(100, 130, 110))
            palette.setColor(QPalette.Disabled, QPalette.WindowText, QColor(100, 130, 110))
            palette.setColor(QPalette.Disabled, QPalette.ButtonText, QColor(100, 130, 110))

        app.setPalette(palette)

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