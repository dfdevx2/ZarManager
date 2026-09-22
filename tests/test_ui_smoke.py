"""Smoke test da UI sem Qt instalado.

Importa todos os módulos e constrói todas as telas contra o stub em
`tests/qt_stub`. Não valida aparência -- valida que o código corre.
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
STUB = ROOT / "tests" / "qt_stub"

try:
    import PySide6  # noqa: F401

    USING_STUB = False
except ImportError:
    sys.path.insert(0, str(STUB))
    USING_STUB = True

sys.path.insert(0, str(ROOT))

MODULES = [
    "app", "config", "locales",
    "core", "core.formats", "core.engines", "core.runner", "core.planner",
    "core.job", "core.workspace", "core.events", "core.errors", "core.stages",
    "services.paths", "services.logging_service", "services.file_service",
    "services.sound", "services.updater_service", "services.versioning",
    "ui.i18n", "ui.dialogs", "ui.worker", "ui.update_dialog", "ui.main_window",
    "ui.theme", "ui.theme.tokens", "ui.theme.qss", "ui.theme.manager",
    "ui.widgets", "ui.widgets.card", "ui.widgets.item_list", "ui.widgets.pill_nav",
    "ui.views", "ui.views.welcome_view", "ui.views.workspace_view",
    "ui.views.settings_view", "ui.views.about_view", "ui.views.troubleshoot_view",
]


class ImportTest(unittest.TestCase):
    def test_todos_os_modulos_importam(self):
        import importlib

        for name in MODULES:
            with self.subTest(module=name):
                importlib.import_module(name)

    def test_core_nao_importa_qt(self):
        """O core tem de continuar testável sem interface.

        Corre num subprocesso limpo: importar o pacote core inteiro não pode
        deixar nenhum módulo do PySide6 carregado.
        """
        import subprocess
        import textwrap

        script = textwrap.dedent(
            """
            import sys
            sys.path.insert(0, %r)
            import core, core.job, core.planner, core.stages, core.runner
            qt = [m for m in sys.modules if m.startswith("PySide6")]
            print(",".join(qt))
            """
        ) % str(ROOT)

        result = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "", "o core puxou Qt")


@unittest.skipUnless(USING_STUB or True, "")
class WidgetBuildTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PySide6.QtWidgets import QApplication

        from config import ConfigManager
        from services.sound import SoundManager
        from ui.i18n import Translator
        from ui.theme import ThemeManager

        cls.cfg = ConfigManager(directory=tempfile.mkdtemp())
        cls.app = QApplication.instance() or QApplication([])
        cls.t = Translator(cls.cfg)
        cls.theme = ThemeManager(cls.app, cls.cfg)
        cls.theme.apply("Preto")
        cls.sound = SoundManager(cls.cfg, directory=ROOT / "assets" / "sfx")

    def test_constroi_todas_as_telas(self):
        from ui.main_window import MainWindow
        from ui.views.about_view import AboutView
        from ui.views.settings_view import SettingsView
        from ui.views.troubleshoot_view import TroubleshootView
        from ui.views.welcome_view import WelcomeView
        from ui.views.workspace_view import WorkspaceView

        factories = {
            "workspace": lambda: WorkspaceView(self.cfg, self.t, self.sound),
            "settings": lambda: SettingsView(self.cfg, self.t, self.sound),
            "about": lambda: AboutView(self.cfg, self.t),
            "troubleshoot": lambda: TroubleshootView(self.cfg, self.t),
            "welcome": lambda: WelcomeView(self.cfg, self.t, self.theme),
            "main": lambda: MainWindow(self.cfg, self.theme, self.sound),
        }
        for name, factory in factories.items():
            with self.subTest(view=name):
                self.assertIsNotNone(factory())

    def test_todos_os_temas_aplicam(self):
        from ui.theme import available_themes

        for name in available_themes():
            with self.subTest(theme=name):
                self.assertIsNotNone(self.theme.apply(name))

    def test_troca_de_modo_e_de_idioma(self):
        from core.planner import Mode
        from ui.main_window import MainWindow

        window = MainWindow(self.cfg, self.theme, self.sound)
        for index in range(len(Mode)):
            window._on_mode_changed(index)
        for language in ("en", "pt-br"):
            self.cfg.set("language", language)
            window.retranslate()

    def test_sinais_do_job_atualizam_a_lista(self):
        from core.events import Event, ItemState, ItemStatus, JobResult, Level, Progress
        from ui.views.workspace_view import WorkspaceView

        view = WorkspaceView(self.cfg, self.t, self.sound)
        view._on_event(Event("ev_item_done", {"name": "X.zip", "output": "X.zar"}, Level.SUCCESS))
        view._on_progress(Progress(1, 4, 0.25))
        view._on_item(ItemStatus("X.zip", ItemState.RUNNING, "zar", 0.5, "compressing 50%"))
        view._on_item(ItemStatus("X.zip", ItemState.DONE))
        view._on_finished(JobResult(completed=1, total=1))


class LocaleTest(unittest.TestCase):
    def test_nenhuma_chave_em_falta(self):
        import locales

        for language, missing in locales.missing_keys().items():
            with self.subTest(language=language):
                self.assertEqual(missing, [], f"chaves em falta em {language}")

    def test_chaves_usadas_existem(self):
        """Cada self.t("chave") no código tem de existir no locales."""
        import re

        import locales

        pattern = re.compile(r'self\.t\(\s*["\']([a-z0-9_]+)["\']')
        known = set(locales.TRANSLATIONS["pt-br"])
        dynamic = {"stage_", "ts_", "collision_", "fmt_", "state_"}
        missing = set()

        for path in (ROOT / "ui").rglob("*.py"):
            for key in pattern.findall(path.read_text(encoding="utf-8")):
                if key not in known and not any(key.startswith(p) for p in dynamic):
                    missing.add(key)

        self.assertEqual(sorted(missing), [], "chaves usadas mas não traduzidas")


if __name__ == "__main__":
    unittest.main(verbosity=2)
