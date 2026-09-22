"""Execução de processos externos.

Este módulo concentra TODAS as proteções de I/O e concorrência que existiam
espalhadas no core.py antigo:

* Regex de progresso pré-compilado ao nível do módulo (e por etapa, quando a
  etapa declara o seu).
* Limitador assíncrono de taxa de atualização da UI a 10 FPS.
* Códigos de retorno tolerados por etapa -- o 7-Zip devolve 1 em avisos
  inofensivos, muito comuns em dumps da Scene.
* Captura do WinError 740 (elevação UAC no Windows).
* Verificação do binário imediatamente antes do Popen, que é o sinal de que
  o antivírus apagou um motor.

Mudanças face ao original:

* A leitura do stdout passou para uma thread dedicada. Antes, um
  `stdout.read(1)` bloqueante fazia com que o cancelamento só fosse visto
  quando o motor escrevesse alguma coisa -- um motor silencioso deixava o
  botão Cancelar sem efeito.
* A pausa suspende mesmo o processo (SIGSTOP) em Linux e macOS, em vez de
  apenas segurar os itens seguintes da fila.
"""

from __future__ import annotations

import os
import platform
import queue
import re
import signal
import subprocess
import threading
import time
from pathlib import Path
from typing import Callable

from core.errors import Cancelled, ElevationRequired, EngineFailed
from services.logging_service import logger

# Pré-compilado uma única vez: este padrão corre por cada linha de terminal.
PROGRESS_PATTERN = re.compile(r"(\d{1,3})(?:[.,]\d+)?\s*%")

_IS_WINDOWS = platform.system() == "Windows"
_IS_POSIX = not _IS_WINDOWS

UI_REFRESH_INTERVAL = 0.1        # 10 FPS
_POLL_INTERVAL = 0.05
_TERMINATE_GRACE = 5.0


class CancelToken:
    """Cancelamento e pausa partilhados por todos os workers de um job."""

    def __init__(self):
        self._cancelled = threading.Event()
        self._resumed = threading.Event()
        self._resumed.set()
        self._lock = threading.Lock()
        self._live_processes: set[subprocess.Popen] = set()

    # ------------------------------------------------------------ estado
    @property
    def cancelled(self) -> bool:
        return self._cancelled.is_set()

    @property
    def paused(self) -> bool:
        return not self._resumed.is_set()

    def cancel(self) -> None:
        self._cancelled.set()
        self._resumed.set()          # destranca quem estiver à espera

    def toggle_pause(self) -> bool:
        """Devolve True se ficou em pausa."""
        if self._resumed.is_set():
            self._resumed.clear()
            self._signal_all(pause=True)
            return True
        self._resumed.set()
        self._signal_all(pause=False)
        return False

    def wait_if_paused(self) -> None:
        self._resumed.wait()

    def raise_if_cancelled(self) -> None:
        if self._cancelled.is_set():
            raise Cancelled()

    # ------------------------------------------------- processos activos
    def register(self, process: subprocess.Popen) -> None:
        with self._lock:
            self._live_processes.add(process)
        if self.paused:
            _suspend(process, True)

    def unregister(self, process: subprocess.Popen) -> None:
        with self._lock:
            self._live_processes.discard(process)

    def _signal_all(self, pause: bool) -> None:
        with self._lock:
            processes = list(self._live_processes)
        for process in processes:
            _suspend(process, pause)


def _suspend(process: subprocess.Popen, pause: bool) -> None:
    """Suspende/retoma um processo filho.

    POSIX resolve isto nativamente com SIGSTOP/SIGCONT. No Windows não há
    equivalente na stdlib; usamos psutil se estiver presente e, se não
    estiver, a pausa degrada para "pausar a fila" (os itens em curso
    terminam). O rótulo do botão na UI reflecte isso.
    """
    if process.poll() is not None:
        return
    try:
        if _IS_POSIX:
            os.kill(process.pid, signal.SIGSTOP if pause else signal.SIGCONT)
            return
        try:
            import psutil  # opcional
        except ImportError:
            return
        handle = psutil.Process(process.pid)
        handle.suspend() if pause else handle.resume()
    except (OSError, ProcessLookupError, PermissionError):
        pass
    except Exception as exc:                      # psutil.NoSuchProcess etc.
        logger.debug("Falha ao suspender processo: %s", exc)


def _reader(stream, sink: queue.Queue) -> None:
    """Lê o stdout do motor e parte em linhas por \\r ou \\n.

    Os motores reportam progresso reescrevendo a mesma linha com \\r, por isso
    não se pode usar readline().
    """
    buffer = bytearray()
    try:
        while True:
            chunk = stream.read(4096)
            if not chunk:
                break
            buffer.extend(chunk)
            cut = max(buffer.rfind(b"\r"), buffer.rfind(b"\n"))
            if cut == -1:
                if len(buffer) > 8192:           # linha patológica sem quebras
                    buffer = buffer[-4096:]
                continue
            head, buffer = bytes(buffer[:cut]), bytearray(buffer[cut + 1:])
            for raw in re.split(rb"[\r\n]+", head):
                text = raw.decode("utf-8", errors="ignore").strip()
                if text:
                    sink.put(text)
    except (OSError, ValueError):
        pass
    finally:
        if buffer:
            text = bytes(buffer).decode("utf-8", errors="ignore").strip()
            if text:
                sink.put(text)
        sink.put(None)


def native_callbacks(runner, refresh_interval: float | None = None):
    """Adapta uma etapa em Python puro ao contrato do ProcessRunner.

    Devolve `(progress, should_cancel)`. O progresso passa pelo mesmo
    limitador de 10 FPS dos motores externos e o cancelamento lê o mesmo
    CancelToken -- incluindo a pausa, que aqui bloqueia o worker em vez de
    mandar SIGSTOP. Para quem está a ver a UI, uma extração nativa é
    indistinguível de um subprocesso.

    Aceita um runner em falta ou incompleto (testes com duplos) sem rebentar.
    """
    token = getattr(runner, "token", None)
    sink = getattr(runner, "on_progress", None)
    interval = refresh_interval or getattr(runner, "refresh_interval", UI_REFRESH_INTERVAL)
    last_emit = 0.0

    def should_cancel() -> bool:
        if token is None:
            return False
        token.wait_if_paused()
        return token.cancelled

    def progress(ratio: float, label: str = "") -> None:
        nonlocal last_emit
        if should_cancel():
            raise Cancelled()
        if sink is None:
            return
        now = time.monotonic()
        if now - last_emit >= interval:
            sink(ratio, label)
            last_emit = now

    return progress, should_cancel


class ProcessRunner:
    """Corre um motor e reporta progresso já limitado a 10 FPS."""

    def __init__(
        self,
        resolver,
        token: CancelToken,
        on_progress: Callable[[float | None, str], None] | None = None,
        refresh_interval: float = UI_REFRESH_INTERVAL,
    ):
        self.resolver = resolver
        self.token = token
        self.on_progress = on_progress
        self.refresh_interval = refresh_interval

    def run(
        self,
        engine_id: str,
        args: list[str],
        cwd: str | Path | None = None,
        ok_codes: frozenset[int] = frozenset({0}),
        progress_re: re.Pattern | None = None,
    ) -> str:
        """Executa o motor. Devolve a última linha útil do terminal."""
        self.token.raise_if_cancelled()
        self.token.wait_if_paused()
        self.token.raise_if_cancelled()

        binary = self.resolver.require(engine_id)      # levanta EngineMissing
        command = [str(binary), *args]
        pattern = progress_re or PROGRESS_PATTERN
        flags = subprocess.CREATE_NO_WINDOW if _IS_WINDOWS else 0

        logger.info("Motor %s: %s", engine_id, " ".join(command))

        try:
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                bufsize=0,
                cwd=str(cwd) if cwd else None,
                creationflags=flags,
            )
        except OSError as exc:
            if getattr(exc, "winerror", None) == 740:
                raise ElevationRequired(engine_id) from exc
            raise EngineFailed(engine_id, -1, str(exc)) from exc

        sink: queue.Queue = queue.Queue()
        reader = threading.Thread(
            target=_reader, args=(process.stdout, sink), daemon=True,
            name=f"reader-{engine_id}",
        )
        self.token.register(process)
        reader.start()

        last_line = ""
        last_emit = 0.0
        cancelled = False

        try:
            finished = False
            while not finished:
                if self.token.cancelled and not cancelled:
                    cancelled = True
                    self._terminate(process)

                try:
                    line = sink.get(timeout=_POLL_INTERVAL)
                except queue.Empty:
                    continue

                if line is None:                      # reader terminou
                    finished = True
                    continue

                last_line = line
                now = time.monotonic()
                if self.on_progress and (now - last_emit) >= self.refresh_interval:
                    match = pattern.search(line)
                    percent = None
                    if match:
                        try:
                            percent = min(1.0, max(0.0, float(match.group(1)) / 100.0))
                        except ValueError:
                            percent = None
                    self.on_progress(percent, line)
                    last_emit = now

            process.wait(timeout=_TERMINATE_GRACE)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait(timeout=_TERMINATE_GRACE)
        finally:
            self.token.unregister(process)
            reader.join(timeout=1.0)
            try:
                if process.stdout:
                    process.stdout.close()
            except OSError:
                pass

        if cancelled or self.token.cancelled:
            raise Cancelled()

        code = process.returncode
        if code not in ok_codes:
            raise EngineFailed(engine_id, code, last_line)

        if code != 0:
            logger.info("Motor %s devolveu %s (tolerado): %s", engine_id, code, last_line)

        return last_line

    @staticmethod
    def _terminate(process: subprocess.Popen) -> None:
        """Um processo suspenso ignora SIGTERM; é preciso retomá-lo primeiro."""
        if process.poll() is not None:
            return
        if _IS_POSIX:
            try:
                os.kill(process.pid, signal.SIGCONT)
            except OSError:
                pass
        try:
            process.terminate()
        except OSError:
            pass
