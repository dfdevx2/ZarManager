import os
import json
import sys
from pathlib import Path

class ConfigManager:
    def __init__(self, filename="settings.json"):
        # CORREÇÃO CRÍTICA DO APPIMAGE: Se o programa estiver compilado (PyInstaller),
        # redireciona o caminho de escrita para a pasta segura do utilizador no sistema.
        if getattr(sys, 'frozen', False):
            if os.name == 'nt':  # Windows Portable
                base_path = Path(os.getenv('APPDATA')) / "ZarManager"
            else:  # Linux (AppImage / Binário)
                base_path = Path.home() / ".config" / "zarmanager"
        else:  # Modo de desenvolvimento (VS Code)
            base_path = Path(__file__).parent.resolve()

        base_path.mkdir(parents=True, exist_ok=True)
        self.config_file = base_path / filename
        
        self.default_config = {
            "source_dir": "",
            "target_dir": "",
            "workers": 4,
            "language": "pt-br",
            "theme": "Sistema",
            "auto_update": True,
            "window_geometry": ""
        }
        self.config = self.load_config()

    def load_config(self):
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # Garante que chaves novas apareçam mesmo em configs antigos
                    for k, v in self.default_config.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception:
                pass
        return self.default_config.copy()

    def save_config(self):
        try:
            # Cria a pasta de destino caso não exista antes de salvar
            self.config_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"[ERRO DE CONFIGURAÇÃO] Não foi possível salvar o arquivo: {e}")

    def get(self, key):
        return self.config.get(key, self.default_config.get(key))

    def set(self, key, value):
        self.config[key] = value
        self.save_config()