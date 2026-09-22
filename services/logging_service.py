"""Logging da aplicação.

O build GUI não tem consola (--windows-console-mode=disable), por isso um
StreamHandler sozinho perdia todos os registos. Passa a existir também um
ficheiro rotativo na pasta de configuração do utilizador, que a tela de
Troubleshooting sabe abrir e anexar ao diagnóstico.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from services.paths import log_dir

LOG_FILENAME = "zarmanager.log"
_MAX_BYTES = 1_000_000
_BACKUPS = 3


def log_file_path() -> Path:
    return log_dir() / LOG_FILENAME


class LoggerService:
    @staticmethod
    def setup() -> logging.Logger:
        log = logging.getLogger("ZarManager")
        log.propagate = False
        log.setLevel(logging.INFO)

        if log.handlers:
            return log

        formatter = logging.Formatter(
            "%(asctime)s [%(levelname)s] %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

        stream = logging.StreamHandler()
        stream.setFormatter(formatter)
        log.addHandler(stream)

        try:
            directory = log_dir()
            directory.mkdir(parents=True, exist_ok=True)
            file_handler = RotatingFileHandler(
                directory / LOG_FILENAME,
                maxBytes=_MAX_BYTES,
                backupCount=_BACKUPS,
                encoding="utf-8",
            )
            file_handler.setFormatter(formatter)
            log.addHandler(file_handler)
        except OSError:
            # Sem permissões de escrita: a app continua, só sem log em ficheiro.
            pass

        return log

    @staticmethod
    def tail(lines: int = 60) -> str:
        try:
            with open(log_file_path(), "r", encoding="utf-8", errors="ignore") as handle:
                return "".join(handle.readlines()[-lines:])
        except OSError:
            return ""


logger = LoggerService.setup()
