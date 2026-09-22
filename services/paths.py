"""Resolução de caminhos em tempo de execução.

Compatível com Python puro (dev), Nuitka standalone, Nuitka onefile,
AppImage e bundle .app do macOS.

Dois factos descobertos na auditoria e que motivam este módulo:

1. O Nuitka NÃO define ``sys.frozen`` (isso é do PyInstaller). Ele define a
   global ``__compiled__`` em cada módulo compilado. O código antigo testava
   ``sys.frozen`` e por isso gravava o settings.json ao lado do binário --
   numa AppImage isso é um mount read-only e as definições perdiam-se a cada
   arranque.

2. Dentro de uma AppImage, ``sys.argv[0]`` aponta para o binário montado em
   ``/tmp/.mount_XXXX``. O ficheiro .AppImage real está em ``$APPIMAGE``.
   O updater antigo substituía o ficheiro errado.
"""

from __future__ import annotations

import os
import platform
import sys
from pathlib import Path

APP_NAME = "ZarManager"
APP_SLUG = "zarmanager"

IS_NUITKA = "__compiled__" in globals()
IS_PYINSTALLER = bool(getattr(sys, "frozen", False))
IS_FROZEN = IS_NUITKA or IS_PYINSTALLER

SYSTEM = platform.system()
IS_WINDOWS = SYSTEM == "Windows"
IS_MAC = SYSTEM == "Darwin"
IS_LINUX = not IS_WINDOWS and not IS_MAC


def _candidate_roots():
    """Candidatos a raiz de recursos, do mais fiável para o menos."""
    # Em standalone e em onefile o Nuitka reescreve __file__ para dentro da
    # pasta de distribuição/extração. É o único caminho válido nos dois casos.
    yield Path(__file__).resolve().parent.parent

    meipass = getattr(sys, "_MEIPASS", None)
    if meipass:
        yield Path(meipass)

    try:
        yield Path(sys.executable).resolve().parent
    except Exception:
        pass

    try:
        if sys.argv and sys.argv[0]:
            yield Path(sys.argv[0]).resolve().parent
    except Exception:
        pass

    yield Path.cwd()


def resource_root() -> Path:
    """Pasta que contém os data files (bin/, assets/, img/)."""
    candidates = []
    for root in _candidate_roots():
        if root in candidates:
            continue
        candidates.append(root)
        if (root / "bin").is_dir() or (root / "assets").is_dir():
            return root
    return candidates[0] if candidates else Path.cwd()


def bin_dir() -> Path:
    return resource_root() / "bin"


def assets_dir() -> Path:
    return resource_root() / "assets"


def is_portable() -> bool:
    """Modo portátil: um ficheiro 'portable.txt' ao lado do executável faz com
    que as definições viajem com a pasta (útil na distribuição Windows)."""
    try:
        return (resource_root() / "portable.txt").exists()
    except Exception:
        return False


def config_dir() -> Path:
    if is_portable():
        return resource_root() / "userdata"

    if IS_WINDOWS:
        base = os.environ.get("APPDATA") or (Path.home() / "AppData" / "Roaming")
        return Path(base) / APP_NAME
    if IS_MAC:
        return Path.home() / "Library" / "Application Support" / APP_NAME

    base = os.environ.get("XDG_CONFIG_HOME") or (Path.home() / ".config")
    return Path(base) / APP_SLUG


def log_dir() -> Path:
    return config_dir() / "logs"


def temp_root() -> Path:
    """Raiz para artefactos intermédios. Fica FORA da pasta de origem e da de
    destino, o que evita que a própria UI liste as pastas temp_* como itens
    processáveis."""
    import tempfile

    return Path(tempfile.gettempdir()) / f"{APP_SLUG}-work"


def appimage_path() -> Path | None:
    """Caminho real do ficheiro .AppImage, quando estamos dentro de uma."""
    value = os.environ.get("APPIMAGE")
    if value:
        candidate = Path(value)
        if candidate.exists():
            return candidate
    return None


def running_executable() -> Path:
    """Ficheiro que o utilizador realmente lançou (alvo de uma auto-atualização)."""
    app_image = appimage_path()
    if app_image:
        return app_image
    if IS_FROZEN:
        return Path(sys.executable).resolve()
    return Path(sys.argv[0]).resolve() if sys.argv and sys.argv[0] else Path(sys.executable)


def describe() -> dict:
    """Usado pelo botão 'Copiar diagnóstico' da tela de Troubleshooting."""
    return {
        "app": APP_NAME,
        "system": SYSTEM,
        "release": platform.release(),
        "machine": platform.machine(),
        "python": platform.python_version(),
        "frozen": IS_FROZEN,
        "packager": "nuitka" if IS_NUITKA else ("pyinstaller" if IS_PYINSTALLER else "source"),
        "appimage": str(appimage_path() or ""),
        "portable": is_portable(),
        "resource_root": str(resource_root()),
        "config_dir": str(config_dir()),
    }
