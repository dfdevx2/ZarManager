import json
import urllib.request
import urllib.error
from typing import Any
from services.logging_service import logger

class UpdateService:
    API_URL = "https://api.github.com/repos/dfdevx2/ZarManager/releases/latest"

    @classmethod
    def get_latest_release(cls) -> dict[str, Any] | None:
        try:
            req = urllib.request.Request(cls.API_URL, headers={'User-Agent': 'ZarManager'})
            # 🔴 NUNCA mais usar ssl._create_unverified_context()
            with urllib.request.urlopen(req, timeout=7) as res:
                return json.loads(res.read().decode())
        except urllib.error.URLError as exc:
            logger.error(f"Erro de rede ao validar update: {exc}")
        except Exception as exc:
            logger.error(f"Falha não tratada no UpdateService: {exc}")
        return None