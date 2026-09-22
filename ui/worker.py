"""Ponte entre o core (threads simples) e a UI (Qt).

O core chama callbacks a partir das suas worker threads. Esta classe
transforma-os em sinais Qt, que são a única forma segura de tocar na interface
a partir de outra thread.

Nota: o CoreWorkerThread antigo chamava `self.parent().get_text(...)` durante
a execução, ou seja, acedia a um QWidget fora da thread da GUI. Aqui o core só
emite chaves e a tradução acontece do lado da UI.
"""

from __future__ import annotations

from PySide6.QtCore import QThread, Signal

from core.errors import CoreError, EngineMissing
from core.events import Event, JobResult, Level
from core.job import JobRequest, JobRunner
from services.logging_service import logger


class JobThread(QThread):
    event_signal = Signal(object)        # core.events.Event
    progress_signal = Signal(object)     # core.events.Progress
    item_signal = Signal(object)         # core.events.ItemStatus
    finished_signal = Signal(object)     # core.events.JobResult
    engine_missing_signal = Signal(str)  # id do motor
    env_error_signal = Signal(list)      # motores em falta

    def __init__(self, request: JobRequest, parent=None):
        super().__init__(parent)
        self.request = request
        self.runner = JobRunner(
            request,
            on_event=self.event_signal.emit,
            on_progress=self.progress_signal.emit,
            on_item=self.item_signal.emit,
        )

    # -------------------------------------------------------------- controlo
    def cancel(self) -> None:
        self.runner.cancel()

    def toggle_pause(self) -> bool:
        return self.runner.toggle_pause()

    @property
    def is_cancelled(self) -> bool:
        return self.runner.is_cancelled

    # ---------------------------------------------------------------- run
    def run(self) -> None:
        try:
            ready, missing = self.runner.verify_environment()
            if not ready:
                self.env_error_signal.emit(missing)
                self.finished_signal.emit(JobResult(total=len(self.request.items)))
                return

            result = self.runner.run()
            self.finished_signal.emit(result)

        except EngineMissing as exc:
            # Este é o caminho do alerta de antivírus. No código antigo a
            # exceção nunca chegava aqui.
            self.engine_missing_signal.emit(exc.engine_id)
            self.finished_signal.emit(self.runner.result)
        except CoreError as exc:
            logger.error("Job terminou com erro: %s", exc)
            self.event_signal.emit(Event(exc.key, exc.args_dict, Level.ERROR))
            self.finished_signal.emit(self.runner.result)
        except Exception as exc:                      # pragma: no cover
            logger.exception("Falha inesperada no job")
            self.event_signal.emit(Event("err_generic", {"error": str(exc)}, Level.ERROR))
            self.finished_signal.emit(self.runner.result)
