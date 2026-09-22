"""Área de trabalho e política de colisões.

A área de trabalho fica DENTRO do diretório de destino (numa pasta oculta) e
não em /tmp. Duas razões:

* mover o artefacto final passa a ser um `os.replace` instantâneo em vez de
  uma cópia entre sistemas de ficheiros -- /tmp é frequentemente tmpfs, e
  extrair um Xbox 360 de 7 GB para RAM não acaba bem;
* tudo o que é intermédio vive num sítio previsível, fácil de limpar depois
  de um crash.

O nome começa por ponto e o FileService ignora-o, o que resolve o caso em que
o destino está dentro da origem (o settings.json do projeto tem exactamente
isso) e as pastas temporárias apareciam na lista como itens processáveis.
"""

from __future__ import annotations

import os
import re
import shutil
import threading
import time
from pathlib import Path

WORK_DIR_NAME = ".zarmanager-work"
_SLUG_RE = re.compile(r"[^A-Za-z0-9._-]+")


def slugify(name: str, limit: int = 60) -> str:
    cleaned = _SLUG_RE.sub("_", name).strip("._-")
    return (cleaned or "item")[:limit]


class JobWorkspace:
    def __init__(self, target: Path, job_id: str | None = None):
        self.target = Path(target)
        self.job_id = job_id or time.strftime("%Y%m%d-%H%M%S")
        self.root = self.target / WORK_DIR_NAME / self.job_id
        self._lock = threading.Lock()
        self._used: set[str] = set()

    def prepare(self) -> None:
        self.root.mkdir(parents=True, exist_ok=True)

    def item_dir(self, name: str) -> Path:
        base = slugify(name)
        with self._lock:
            candidate, counter = base, 1
            while candidate in self._used:
                candidate = f"{base}_{counter}"
                counter += 1
            self._used.add(candidate)
        path = self.root / candidate
        path.mkdir(parents=True, exist_ok=True)
        return path

    def cleanup(self) -> None:
        shutil.rmtree(self.root, ignore_errors=True)
        parent = self.target / WORK_DIR_NAME
        try:
            if parent.is_dir() and not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass

    @staticmethod
    def purge_stale(target: Path, max_age_hours: float = 24.0) -> int:
        """Remove restos de execuções que morreram a meio."""
        parent = Path(target) / WORK_DIR_NAME
        if not parent.is_dir():
            return 0
        removed = 0
        cutoff = time.time() - max_age_hours * 3600
        try:
            for entry in parent.iterdir():
                try:
                    if entry.stat().st_mtime < cutoff:
                        shutil.rmtree(entry, ignore_errors=True)
                        removed += 1
                except OSError:
                    continue
            if not any(parent.iterdir()):
                parent.rmdir()
        except OSError:
            pass
        return removed


class CollisionResolver:
    """Resolve conflitos no destino de forma segura entre threads.

    O código antigo tinha uma corrida: dois workers podiam ver que "Jogo_1"
    não existia e renomear ambos para "Jogo_1". As reservas abaixo garantem
    que um nome devolvido a um worker nunca é devolvido a outro.
    """

    SKIP = "SKIP"
    OVERWRITE = "OVERWRITE"
    RENAME = "RENAME"

    def __init__(self, policy: str = RENAME):
        self.policy = (policy or self.RENAME).upper()
        self._lock = threading.Lock()
        self._reserved: set[Path] = set()

    def resolve(self, destination: Path) -> tuple[Path | None, str]:
        """Devolve (caminho a usar, ação) ou (None, 'skip')."""
        with self._lock:
            if destination not in self._reserved and not destination.exists():
                self._reserved.add(destination)
                return destination, "new"

            if self.policy == self.SKIP:
                return None, "skip"

            if self.policy == self.OVERWRITE:
                self._reserved.add(destination)
                return destination, "overwrite"

            stem, suffix, parent = destination.stem, destination.suffix, destination.parent
            counter = 1
            candidate = destination
            while candidate in self._reserved or candidate.exists():
                candidate = parent / f"{stem}_{counter}{suffix}"
                counter += 1
            self._reserved.add(candidate)
            return candidate, "rename"

    def release(self, path: Path) -> None:
        with self._lock:
            self._reserved.discard(path)


def move_into_place(source: Path, destination: Path) -> Path:
    """Move o artefacto final para o destino, substituindo se for preciso."""
    destination.parent.mkdir(parents=True, exist_ok=True)

    if destination.exists():
        if destination.is_dir() and not destination.is_symlink():
            shutil.rmtree(destination, ignore_errors=True)
        else:
            destination.unlink(missing_ok=True)

    try:
        os.replace(source, destination)          # mesmo sistema de ficheiros
    except OSError:
        shutil.move(str(source), str(destination))
    return destination
