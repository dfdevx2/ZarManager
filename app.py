import sys
import platform
from PySide6.QtWidgets import QApplication, QMainWindow, QStackedWidget
from PySide6.QtGui import QPalette, QColor
from PySide6.QtCore import Qt

from config import ConfigManager
from ui.welcome_view import WelcomeView
from ui.main_view import MainController

class ZarManagerApp(QMainWindow):
    def __init__(self, cfg):
        super().__init__()
        self.cfg = cfg
        self.setWindowTitle("ZarManager v2.0.2")
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
        app.setStyle("Fusion")
        
        theme_name = self.cfg.get("theme") or "Sistema"
        if platform.system() == "Linux" and theme_name == "Sistema":
            theme_name = "Preto"

        palette = QPalette()
        
        if theme_name == "Preto":
            # TEMA AMOLED (Preto Absoluto)
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
            
        elif theme_name == "Steam":
            # TEMA STEAM (Azul mais escuro / Profundo)
            palette.setColor(QPalette.ColorRole.Window, QColor(15, 24, 34))       # Azul Profundo
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
            # TEMA XBOX (Estrutura idêntica à da Steam, mas em tons de verde escuro)
            palette.setColor(QPalette.ColorRole.Window, QColor(15, 34, 18))       # Verde Profundo
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
            
        else:
            # Temas do Sistema / Claro
            palette = app.style().standardPalette()
            if theme_name == "Branco":
                palette.setColor(QPalette.ColorRole.Highlight, QColor(59, 142, 208))
                
        app.setPalette(palette)

    def boot_main_app(self):
        self.cfg.set("first_boot_done", True)
        self.main_view = MainController(self.cfg, "v2.0.2", self.apply_theme)
        self.stack.addWidget(self.main_view)
        self.stack.setCurrentWidget(self.main_view)

def main():
    app = QApplication(sys.argv)
    cfg = ConfigManager()
    window = ZarManagerApp(cfg)
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()