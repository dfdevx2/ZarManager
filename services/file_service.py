"""Listagem dos itens processáveis numa pasta de origem."""

from __future__ import annotations

import os
from pathlib import Path

from core.formats import ARCHIVE_SUFFIXES, CD_SHEET_SUFFIXES, STFS_MAGICS
from core.planner import Mode
from core.workspace import WORK_DIR_NAME
from services.logging_service import logger

IMAGE_SUFFIXES = {".iso", ".gcm", ".wbfs", ".nkit"}
PACKAGE_SUFFIXES = {".pkg"}
# Saídas do próprio ZarManager: nunca reaparecem como entrada.
OUTPUT_SUFFIXES = {".zar", ".chd", ".rvz"}


def is_xbox_container(entry: Path) -> bool:
    """Um XBLA, DLC ou cabeçalho GOD não tem extensão nenhuma.

    Sem isto, um pacote do Xbox 360 largado na pasta de origem simplesmente
    não aparecia na lista -- não há sufixo por onde o apanhar, só os quatro
    bytes do cabeçalho.
    """
    if entry.suffix:
        return False
    try:
        with entry.open("rb") as handle:
            return handle.read(4) in STFS_MAGICS
    except OSError:
        return False


def _is_god_data_dir(entry: Path) -> bool:
    """A pasta `<cabeçalho>.data` é metade de um GOD, não um item à parte."""
    if entry.suffix.lower() != ".data":
        return False
    header = entry.with_name(entry.stem)
    try:
        return header.is_file() and is_xbox_container(header)
    except OSError:
        return False


class FileService:
    ARCHIVE_EXTENSIONS = ARCHIVE_SUFFIXES
    ISO_EXTENSIONS = IMAGE_SUFFIXES

    @classmethod
    def find_processable_files(
        cls, directory: str, mode: Mode, target: str | None = None
    ) -> list[Path]:
        if not directory or not os.path.isdir(directory):
            return []

        source = Path(directory)
        target_path = Path(target).resolve() if target else None
        found: list[Path] = []

        try:
            for entry in sorted(source.iterdir()):
                # Ficheiros ocultos, a área de trabalho e o próprio destino
                # nunca são itens. Era isto que fazia aparecer as pastas
                # temp_* e a pasta 'zar/' na lista quando o destino estava
                # dentro da origem.
                if entry.name.startswith(".") or entry.name == WORK_DIR_NAME:
                    continue
                if target_path is not None:
                    try:
                        if entry.resolve() == target_path:
                            continue
                    except OSError:
                        continue

                suffix = entry.suffix.lower()
                is_file = entry.is_file()

                if is_file and suffix in OUTPUT_SUFFIXES:
                    continue
                if not is_file and _is_god_data_dir(entry):
                    continue

                xbox = is_file and is_xbox_container(entry)

                if mode is Mode.AUTO:
                    if entry.is_dir() or xbox or (
                        is_file
                        and suffix in ARCHIVE_SUFFIXES | IMAGE_SUFFIXES
                        | PACKAGE_SUFFIXES | CD_SHEET_SUFFIXES
                    ):
                        found.append(entry)
                elif mode is Mode.EXTRACT_ARC:
                    if is_file and suffix in ARCHIVE_SUFFIXES:
                        found.append(entry)
                elif mode is Mode.EXTRACT_ISO:
                    if xbox or (
                        is_file
                        and suffix in IMAGE_SUFFIXES | ARCHIVE_SUFFIXES | PACKAGE_SUFFIXES
                    ):
                        found.append(entry)
                elif mode is Mode.COMPRESS:
                    if entry.is_dir():
                        found.append(entry)
        except PermissionError:
            logger.error("Permissão negada ao ler: %s", directory)
        except OSError as exc:
            logger.error("Falha de sistema de ficheiros em %s: %s", directory, exc)

        return found

    @staticmethod
    def validate_directories(source: str, target: str) -> list[str]:
        """Devolve chaves de aviso sobre a combinação origem/destino."""
        warnings: list[str] = []
        if not source or not target:
            return warnings
        try:
            source_path = Path(source).resolve()
            target_path = Path(target).resolve()
        except OSError:
            return warnings

        if source_path == target_path:
            warnings.append("warn_same_dir")
        elif target_path.is_relative_to(source_path):
            warnings.append("warn_target_inside_source")
        return warnings
