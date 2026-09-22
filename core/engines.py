"""Resolução dos binários dos motores.

Cada motor é declarado uma vez, com os nomes que tem em cada sistema e os
nomes pelos quais pode existir no PATH. A UI de Troubleshooting usa `probe()`
para mostrar um ✓/✗ e a versão de cada motor.
"""

from __future__ import annotations

import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path

from services.paths import bin_dir

_SYSTEM = platform.system()
_IS_WINDOWS = _SYSTEM == "Windows"
_IS_MAC = _SYSTEM == "Darwin"


@dataclass(frozen=True)
class EngineSpec:
    id: str
    windows: tuple[str, ...] = ()
    linux: tuple[str, ...] = ()
    macos: tuple[str, ...] = ()
    system_names: tuple[str, ...] = ()
    version_args: tuple[str, ...] = ()
    bundled: bool = True            # distribuído dentro de bin/
    native: bool = False            # lido em Python, sem binário nenhum
    label: str = ""
    license: str = ""
    homepage: str = ""

    def local_names(self) -> tuple[str, ...]:
        if _IS_WINDOWS:
            return self.windows
        if _IS_MAC:
            return self.macos or self.linux
        return self.linux


ENGINES: dict[str, EngineSpec] = {
    "7z": EngineSpec(
        id="7z",
        windows=("7z.exe",),
        linux=("7z", "7zz"),
        macos=("7zz", "7z"),
        system_names=("7zz", "7z", "7za"),
        version_args=(),
        label="7-Zip",
        license="LGPL-2.1 (unRAR restrita)",
        homepage="https://www.7-zip.org/",
    ),
    "xiso": EngineSpec(
        id="xiso",
        windows=("extract-xiso.exe",),
        linux=("extract-xiso",),
        macos=("extract-xiso-mac", "extract-xiso"),
        system_names=("extract-xiso",),
        version_args=("-v",),
        label="extract-xiso",
        license="BSD-3-Clause",
        homepage="https://github.com/XboxDev/extract-xiso",
    ),
    "zar": EngineSpec(
        id="zar",
        windows=("zarchive.exe",),
        linux=("zarchive",),
        macos=("zarchive-mac", "zarchive"),
        system_names=("zarchive",),
        label="ZArchive",
        license="MIT",
        homepage="https://github.com/Exzap/ZArchive",
    ),
    # --- Leitores nativos: não há binário, estão sempre presentes ---
    "stfs": EngineSpec(
        id="stfs",
        native=True,
        label="Leitor STFS (XBLA/DLC)",
        license="integrado no ZarManager",
        homepage="https://free60.org/System-Software/Formats/STFS/",
    ),
    # --- Distribuídos a partir da v1.3.0: já vêm dentro de bin/ ---
    "chdman": EngineSpec(
        id="chdman",
        windows=("chdman.exe",),
        linux=("chdman",),
        macos=("chdman-mac", "chdman"),
        system_names=("chdman",),
        version_args=("--help",),
        label="chdman (MAME)",
        license="GPL-2.0-or-later",
        homepage="https://www.mamedev.org/",
    ),
    "dolphin-tool": EngineSpec(
        id="dolphin-tool",
        windows=("DolphinTool.exe", "dolphin-tool.exe"),
        linux=("dolphin-tool",),
        macos=("dolphin-tool-mac", "dolphin-tool"),
        system_names=("dolphin-tool", "DolphinTool"),
        version_args=("--help",),
        label="DolphinTool",
        license="GPL-2.0-or-later",
        homepage="https://dolphin-emu.org/",
    ),
    "pkg": EngineSpec(
        id="pkg",
        windows=("PkgTool.Core.exe", "pkg.exe"),
        linux=("PkgTool.Core", "pkg"),
        macos=("PkgTool.Core-mac", "PkgTool.Core", "pkg"),
        system_names=("PkgTool.Core", "pkg"),
        label="PkgTool (LibOrbisPkg)",
        license="LGPL-3.0",
        homepage="https://github.com/maxton/LibOrbisPkg",
    ),
}


@dataclass
class EngineStatus:
    id: str
    label: str
    found: bool
    path: str = ""
    version: str = ""
    bundled: bool = True
    native: bool = False
    error: str = ""


class EngineResolver:
    """Localiza binários, primeiro em bin/ e depois no PATH do sistema."""

    def __init__(self, directory: Path | None = None):
        self.bin_dir = Path(directory) if directory else bin_dir()
        self._cache: dict[str, Path | None] = {}

    def path(self, engine_id: str) -> Path | None:
        if engine_id in self._cache:
            return self._cache[engine_id]

        spec = ENGINES.get(engine_id)
        resolved: Path | None = None

        if spec:
            for name in spec.local_names():
                candidate = self.bin_dir / name
                if candidate.exists():
                    resolved = candidate
                    break
            if resolved is None:
                for name in spec.system_names:
                    found = shutil.which(name)
                    if found:
                        resolved = Path(found)
                        break

        self._cache[engine_id] = resolved
        return resolved

    def require(self, engine_id: str) -> Path:
        """Caminho do motor, validado no momento exacto da execução.

        A validação é deliberadamente tardia: o antivírus pode apagar o
        binário entre o arranque da app e o início da etapa.
        """
        from core.errors import EngineMissing

        resolved = self.path(engine_id)
        if resolved is None or not resolved.exists():
            self._cache.pop(engine_id, None)
            resolved = self.path(engine_id)
        if resolved is None or not resolved.exists():
            spec = ENGINES.get(engine_id)
            name = spec.local_names()[0] if spec and spec.local_names() else engine_id
            raise EngineMissing(engine_id, str(self.bin_dir / name))
        self.ensure_executable(resolved)
        return resolved

    @staticmethod
    def ensure_executable(path: Path) -> None:
        if _IS_WINDOWS:
            return
        try:
            mode = path.stat().st_mode
            if not mode & 0o111:
                os.chmod(path, mode | 0o755)
        except OSError:
            pass

    def probe(self, engine_id: str) -> EngineStatus:
        spec = ENGINES.get(engine_id)
        label = spec.label if spec else engine_id

        if spec is not None and spec.native:
            # Não há nada para procurar: o leitor vem dentro da aplicação.
            return EngineStatus(
                id=engine_id, label=label, found=True, bundled=True, native=True,
            )

        resolved = self.path(engine_id)

        if resolved is None:
            return EngineStatus(
                id=engine_id, label=label, found=False,
                bundled=bool(spec and spec.bundled),
            )

        self.ensure_executable(resolved)
        version = ""
        if spec and spec.version_args:
            version = self._probe_version(resolved, spec.version_args)

        return EngineStatus(
            id=engine_id, label=label, found=True, path=str(resolved),
            version=version, bundled=bool(spec and spec.bundled),
        )

    @staticmethod
    def _probe_version(path: Path, args: tuple[str, ...]) -> str:
        flags = subprocess.CREATE_NO_WINDOW if _IS_WINDOWS else 0
        try:
            result = subprocess.run(
                [str(path), *args], capture_output=True, text=True,
                timeout=6, creationflags=flags,
            )
            output = (result.stdout or result.stderr or "").strip().splitlines()
            return output[0][:80] if output else ""
        except (OSError, subprocess.SubprocessError):
            return ""

    def probe_all(self) -> list[EngineStatus]:
        return [self.probe(engine_id) for engine_id in ENGINES]
