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
        
        theme_name = self.cfg.get("theme") or "Sistema"
        
        if theme_name == "Sistema":
            try:
                is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
            except AttributeError:
                is_dark = app.style().standardPalette().color(QPalette.Window).lightness() < 128
                
            theme_name = "Preto" if is_dark else "Branco"

        palette = QPalette()
        
        if theme_name == "Preto":
            palette.setColor(QPalette.ColorRole.Window, QColor(0, 0, 0))          
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(8, 8, 8))            
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(15, 15, 15))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(0, 0, 0))
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(15, 15, 15))       
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(138, 43, 226))       
            palette.setColor(QPalette.ColorRole.Highlight, QColor(138, 43, 226))  
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
            
        elif theme_name == "Branco":
            palette.setColor(QPalette.ColorRole.Window, QColor(240, 242, 245))       
            palette.setColor(QPalette.ColorRole.WindowText, QColor(40, 40, 40))      
            palette.setColor(QPalette.ColorRole.Base, QColor(255, 255, 255))         
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(248, 249, 250))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(255, 255, 255))
            palette.setColor(QPalette.ColorRole.ToolTipText, QColor(40, 40, 40))
            palette.setColor(QPalette.ColorRole.Text, QColor(40, 40, 40))
            palette.setColor(QPalette.ColorRole.Button, QColor(230, 230, 230))       
            palette.setColor(QPalette.ColorRole.ButtonText, QColor(40, 40, 40))
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(52, 152, 219))          
            palette.setColor(QPalette.ColorRole.Highlight, QColor(52, 152, 219))     
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)
            
        elif theme_name == "Steam":
            palette.setColor(QPalette.ColorRole.Window, QColor(15, 24, 34))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(11, 14, 19))         
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 35, 50))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(11, 14, 19))
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(25, 45, 60))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(64, 150, 200))      
            palette.setColor(QPalette.ColorRole.Highlight, QColor(64, 150, 200)) 
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.black)

        elif theme_name == "Xbox":
            palette.setColor(QPalette.ColorRole.Window, QColor(15, 34, 18))
            palette.setColor(QPalette.ColorRole.WindowText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Base, QColor(11, 19, 12))         
            palette.setColor(QPalette.ColorRole.AlternateBase, QColor(20, 50, 25))
            palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(11, 19, 12))
            palette.setColor(QPalette.ColorRole.ToolTipText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Text, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.Button, QColor(25, 60, 30))
            palette.setColor(QPalette.ColorRole.ButtonText, Qt.GlobalColor.white)
            palette.setColor(QPalette.ColorRole.BrightText, Qt.GlobalColor.red)
            palette.setColor(QPalette.ColorRole.Link, QColor(16, 124, 16))        
            palette.setColor(QPalette.ColorRole.Highlight, QColor(16, 124, 16))   
            palette.setColor(QPalette.ColorRole.HighlightedText, Qt.GlobalColor.white)

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