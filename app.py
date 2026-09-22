"""Ponto de entrada do ZarManager."""

from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from config import ConfigManager
from services.logging_service import logger
from services.paths import resource_root
from services.sound import SoundManager
from ui.i18n import Translator
from ui.theme import ThemeManager
from version import __version__


def _install_icon(app: QApplication) -> None:
    icon_path = resource_root() / "img" / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("ZarManager")
    app.setApplicationVersion(__version__)
    app.setOrganizationName("dfdevx2")
    _install_icon(app)

    cfg = ConfigManager()
    logger.info("ZarManager v%s a arrancar (config: %s)", __version__, cfg.config_file)

    theme_manager = ThemeManager(app, cfg)
    theme_manager.apply()

    sound = SoundManager(cfg)
    sound.install(app)

    from ui.main_window import MainWindow

    holder: dict = {}

    def open_main() -> None:
        window = MainWindow(cfg, theme_manager, sound)
        holder["window"] = window
        window.show()
        if "welcome" in holder:
            holder.pop("welcome").close()

    if cfg.get_bool("first_boot_done"):
        open_main()
    else:
        from ui.views.welcome_view import WelcomeView

        welcome = WelcomeView(cfg, Translator(cfg), theme_manager)
        welcome.setWindowTitle(f"ZarManager v{__version__}")
        welcome.resize(900, 620)
        welcome.finished.connect(open_main)
        holder["welcome"] = welcome
        welcome.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
