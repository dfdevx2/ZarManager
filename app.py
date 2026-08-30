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
        """Orquestrador principal de temas. Limpa a cache e delega por OS."""
        app = QApplication.instance()
        sys_os = platform.system()
        theme_name = self.cfg.get("theme") or "Sistema"
        
        # Limpeza de memória de estilos residuais (Evita vazamentos visuais)
        app.setStyleSheet("")
        
        # Roteamento Estrito de OS
        if sys_os == "Darwin":
            from ui.theme_mac import apply_mac_theme
            apply_mac_theme(app, theme_name)
        else:
            self._apply_windows_linux_theme(app, sys_os, theme_name)

        # Força repintura nativa de alta performance em toda a árvore de widgets
        current_style = app.style()
        for widget in app.allWidgets():
            current_style.unpolish(widget)
            current_style.polish(widget)
            widget.update()

    def _apply_windows_linux_theme(self, app: QApplication, sys_os: str, theme_name: str):
        """Motor de renderização Fusion para Windows e Linux baseados em Dicionários."""
        app.setStyle("Fusion")
        
        app.setStyleSheet("""
            QToolTip {
                background-color: #2c3e50; color: #ffffff;
                border: 1px solid #34495e; border-radius: 6px;
                padding: 6px 10px; font-family: "Segoe UI", Roboto, Arial; font-size: 13px;
            }
        """)
        
        if sys_os == "Linux" and theme_name == "Sistema":
            theme_name = "Preto"
            
        if theme_name == "Sistema":
            try:
                is_dark = app.styleHints().colorScheme() == Qt.ColorScheme.Dark
            except AttributeError:
                is_dark = app.style().standardPalette().color(QPalette.ColorRole.Window).lightness() < 128
            theme_name = "Preto" if is_dark else "Branco"

        # Arquitetura Data-Driven para cores (Extensível e Manutenível)
        themes_data = {
            "Preto": {
                "active": {
                    QPalette.ColorRole.Window: (12, 12, 12), QPalette.ColorRole.WindowText: Qt.GlobalColor.white,
                    QPalette.ColorRole.Base: (6, 6, 6), QPalette.ColorRole.AlternateBase: (16, 16, 16),
                    QPalette.ColorRole.ToolTipBase: (44, 62, 80), QPalette.ColorRole.ToolTipText: Qt.GlobalColor.white,
                    QPalette.ColorRole.Text: Qt.GlobalColor.white, QPalette.ColorRole.Button: (22, 22, 22),
                    QPalette.ColorRole.ButtonText: Qt.GlobalColor.white, QPalette.ColorRole.BrightText: Qt.GlobalColor.red,
                    QPalette.ColorRole.Link: (138, 43, 226), QPalette.ColorRole.Highlight: (138, 43, 226),
                    QPalette.ColorRole.HighlightedText: Qt.GlobalColor.white
                },
                "disabled": (120, 120, 120)
            },
            "Steam": {
                "active": {
                    QPalette.ColorRole.Window: (23, 29, 37), QPalette.ColorRole.WindowText: Qt.GlobalColor.white,
                    QPalette.ColorRole.Base: (13, 19, 27), QPalette.ColorRole.AlternateBase: (27, 40, 56),
                    QPalette.ColorRole.ToolTipBase: (44, 62, 80), QPalette.ColorRole.ToolTipText: Qt.GlobalColor.white,
                    QPalette.ColorRole.Text: Qt.GlobalColor.white, QPalette.ColorRole.Button: (42, 71, 94),
                    QPalette.ColorRole.ButtonText: Qt.GlobalColor.white, QPalette.ColorRole.BrightText: Qt.GlobalColor.red,
                    QPalette.ColorRole.Link: (102, 192, 244), QPalette.ColorRole.Highlight: (102, 192, 244),
                    QPalette.ColorRole.HighlightedText: Qt.GlobalColor.black
                },
                "disabled": (100, 120, 140)
            },
            "Xbox": {
                "active": {
                    QPalette.ColorRole.Window: (16, 30, 18), QPalette.ColorRole.WindowText: Qt.GlobalColor.white,
                    QPalette.ColorRole.Base: (10, 20, 12), QPalette.ColorRole.AlternateBase: (20, 40, 25),
                    QPalette.ColorRole.ToolTipBase: (44, 62, 80), QPalette.ColorRole.ToolTipText: Qt.GlobalColor.white,
                    QPalette.ColorRole.Text: Qt.GlobalColor.white, QPalette.ColorRole.Button: (26, 60, 32),
                    QPalette.ColorRole.ButtonText: Qt.GlobalColor.white, QPalette.ColorRole.BrightText: Qt.GlobalColor.red,
                    QPalette.ColorRole.Link: (16, 124, 16), QPalette.ColorRole.Highlight: (16, 124, 16),
                    QPalette.ColorRole.HighlightedText: Qt.GlobalColor.white
                },
                "disabled": (100, 130, 110)
            },
            "Branco": {
                "active": {
                    QPalette.ColorRole.Window: (245, 246, 248), QPalette.ColorRole.WindowText: (30, 30, 30),
                    QPalette.ColorRole.Base: (255, 255, 255), QPalette.ColorRole.AlternateBase: (238, 240, 242),
                    QPalette.ColorRole.ToolTipBase: (44, 62, 80), QPalette.ColorRole.ToolTipText: Qt.GlobalColor.white,
                    QPalette.ColorRole.Text: (30, 30, 30), QPalette.ColorRole.Button: (230, 232, 235),
                    QPalette.ColorRole.ButtonText: (30, 30, 30), QPalette.ColorRole.BrightText: Qt.GlobalColor.red,
                    QPalette.ColorRole.Link: (52, 152, 219), QPalette.ColorRole.Highlight: (52, 152, 219),
                    QPalette.ColorRole.HighlightedText: Qt.GlobalColor.white
                },
                "disabled": (150, 150, 150)
            }
        }

        # Constrói a paleta nativa a partir da configuração selecionada
        palette = app.style().standardPalette()
        selected_theme = themes_data.get(theme_name, themes_data["Preto"])
        
        for role, color_val in selected_theme["active"].items():
            color = QColor(*color_val) if isinstance(color_val, tuple) else color_val
            palette.setColor(role, color)
            
        dis_color = QColor(*selected_theme["disabled"])
        for role in [QPalette.ColorRole.Text, QPalette.ColorRole.WindowText, QPalette.ColorRole.ButtonText]:
            palette.setColor(QPalette.ColorGroup.Disabled, role, dis_color)

        app.setPalette(palette)

    def boot_main_app(self):
        self.cfg.set("first_boot_done", True)
        self.main_view = MainController(self.cfg, f"v{__version__}", self.apply_theme)
        self.stack.addWidget(self.main_view)
        self.stack.setCurrentWidget(self.main_view)

    def closeEvent(self, event: QCloseEvent):
        """Intercetação de segurança (Anti-Corrupção de ficheiros ao fechar abruptamente)."""
        if getattr(self, 'main_view', None) and getattr(self.main_view, 'active_threads', None):
            title = self.main_view.get_text("warn_exit_title", "Aviso de Encerramento")
            msg = self.main_view.get_text("warn_exit_msg", "Existem processos ativos em segundo plano.\nSe fechar agora, o programa irá cancelar e abortar tudo de forma segura.\n\nDeseja mesmo sair?")
            btn_yes = self.main_view.get_text("btn_exit_yes", "Sair e Abortar")
            btn_no = self.main_view.get_text("btn_exit_no", "Cancelar e Voltar")
            
            resp = DialogManager.ask_custom(self, title, msg, [btn_yes, btn_no])
            
            if resp == btn_yes:
                # Paralisa todas as threads ativas instantaneamente
                for worker in self.main_view.active_threads.values():
                    if worker and hasattr(worker, 'manager') and worker.manager:
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