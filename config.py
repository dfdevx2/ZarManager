"""Persistência das definições do utilizador."""

from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path

from services.paths import config_dir

DEFAULT_CONFIG = {
    # Diretórios
    "source_dir": "",
    "target_dir": "",
    # Processamento
    "workers": 4,
    "keep_originals": False,
    "collision_policy": "ASK",          # ASK | SKIP | OVERWRITE | RENAME
    "auto_profile": True,               # no modo auto, encadeia até ao formato alvo
    # Aparência
    "language": "pt-br",
    "theme": "Sistema",
    "reduce_motion": False,
    "window_geometry": "",
    # Áudio
    "sfx_enabled": True,
    "sfx_volume": 0.35,
    # Atualizações
    "auto_update": True,
    # Estado de primeira execução
    "first_boot_done": False,
    "tutorial_done": False,
}


class ConfigManager:
    def __init__(self, filename: str = "settings.json", directory: Path | None = None):
        base_path = Path(directory) if directory else config_dir()
        try:
            base_path.mkdir(parents=True, exist_ok=True)
        except OSError:
            base_path = Path(tempfile.gettempdir())

        self.config_file = base_path / filename
        self.default_config = dict(DEFAULT_CONFIG)
        self.config = self.load_config()

    # ------------------------------------------------------------------ IO
    def load_config(self) -> dict:
        data = dict(self.default_config)
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as handle:
                    stored = json.load(handle)
                if isinstance(stored, dict):
                    data.update({k: v for k, v in stored.items()})
            except (OSError, ValueError):
                pass
        # Garante que chaves novas aparecem em configs antigos
        for key, value in self.default_config.items():
            data.setdefault(key, value)
        return data

    def save_config(self) -> bool:
        """Escrita atómica: grava num ficheiro temporário e só depois substitui.
        Evita um settings.json truncado se a app morrer a meio da escrita."""
        try:
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.config_file.with_suffix(".tmp")
            with open(tmp, "w", encoding="utf-8") as handle:
                json.dump(self.config, handle, indent=4, ensure_ascii=False)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp, self.config_file)
            return True
        except OSError:
            from services.logging_service import logger

            logger.warning("Não foi possível gravar %s", self.config_file)
            return False

    # --------------------------------------------------------------- Acesso
    def get(self, key: str, fallback=None):
        if key in self.config:
            return self.config[key]
        if key in self.default_config:
            return self.default_config[key]
        return fallback

    def set(self, key: str, value) -> None:
        if self.config.get(key) == value:
            return
        self.config[key] = value
        self.save_config()

    def get_int(self, key: str, minimum: int = 1, maximum: int = 64) -> int:
        try:
            return max(minimum, min(maximum, int(self.get(key))))
        except (TypeError, ValueError):
            return max(minimum, min(maximum, int(self.default_config.get(key, minimum))))

    def get_float(self, key: str, minimum: float = 0.0, maximum: float = 1.0) -> float:
        try:
            return max(minimum, min(maximum, float(self.get(key))))
        except (TypeError, ValueError):
            return float(self.default_config.get(key, minimum))

    def get_bool(self, key: str) -> bool:
        value = self.get(key)
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            return value.strip().lower() in {"1", "true", "yes", "on"}
        return bool(self.default_config.get(key, False))
