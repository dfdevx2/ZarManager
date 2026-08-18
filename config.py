# config.py
# Gerenciamento de persistência de dados do usuário

import json
from pathlib import Path

CONFIG_FILE = Path(__file__).parent.resolve() / "settings.json"

DEFAULT_CONFIG = {
    "source_dir": "",
    "target_dir": "",
    "workers": 2,
    "language": "pt-br",
    "theme": "Sistema" # Modificado para ler o ambiente do SO nativamente
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()

    def load_config(self) -> dict:
        if not CONFIG_FILE.exists():
            self.save_config(DEFAULT_CONFIG)
            return DEFAULT_CONFIG
            
        try:
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                for key, value in DEFAULT_CONFIG.items():
                    if key not in data:
                        data[key] = value
                return data
        except Exception as e:
            print(f"[AVISO] Falha ao ler configurações, restaurando padrões. Erro: {e}")
            return DEFAULT_CONFIG

    def save_config(self, new_config: dict = None):
        if new_config:
            self.config = new_config
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key: str):
        return self.config.get(key, DEFAULT_CONFIG.get(key))

    def set(self, key: str, value):
        self.config[key] = value
        self.save_config()