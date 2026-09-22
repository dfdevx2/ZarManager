"""Execução de um lote (job).

Substitui o ZarManagerCore. Diferenças que interessam:

* `run()` devolve um JobResult real. Antes a UI chamava `get_completion_stats()`
  e `is_cancelled()` via hasattr -- métodos que nunca existiram -- e caía num
  fallback `failed=0, completed=len(items)`. Na prática, um lote com falhas ou
  cancelado tocava o som de sucesso e mostrava "terminou sem erros".
* `verify_environment()` devolve `(bool, list)`, que é o que a UI sempre
  esperou. Antes devolvia só um bool e a mensagem de erro dizia sempre
  "Ficheiros desconhecidos" em vez de nomear o motor em falta.
* Um EngineMissing (antivírus a apagar um motor) sobe até quem chamou, em vez
  de ser engolido por um `except Exception` que apenas o registava no log.
* Os originais só são apagados depois de o artefacto final existir no destino.
  Antes, o .zip era removido logo após a extração: se o zarchive falhasse a
  seguir, o utilizador ficava sem o original E sem o resultado.
"""

from __future__ import annotations

import threading
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from core.engines import ENGINES, EngineResolver
from core.errors import Cancelled, CoreError, EngineMissing, NoRoute
from core.events import Event, ItemState, ItemStatus, JobResult, Level, Progress
from core.formats import Fmt, sniff
from core.planner import Mode, Planner
from core.runner import CancelToken, ProcessRunner
from core.stages.base import Artifact, StageContext, looks_like_identifier
from core.workspace import CollisionResolver, JobWorkspace, move_into_place
from services.logging_service import logger

MAX_CHAIN_STEPS = 8          # trava contra um ciclo de etapas mal declarado


@dataclass
class JobRequest:
    items: list[Path]
    target: Path
    mode: Mode
    keep_originals: bool = False
    policy: str = CollisionResolver.RENAME
    workers: int = 4
    options: dict = field(default_factory=dict)


class _OptimisticResolver:
    """Finge que todos os motores existem. Serve para calcular a cadeia ideal
    e assim descobrir QUE motores fariam falta."""

    def path(self, engine_id):
        return Path(engine_id)

    def require(self, engine_id):
        return Path(engine_id)


class JobRunner:
    def __init__(
        self,
        request: JobRequest,
        on_event: Callable[[Event], None] | None = None,
        on_progress: Callable[[Progress], None] | None = None,
        on_item: Callable[[ItemStatus], None] | None = None,
        resolver: EngineResolver | None = None,
    ):
        self.request = request
        self.on_event = on_event or (lambda event: None)
        self.on_progress = on_progress or (lambda progress: None)
        self.on_item = on_item or (lambda status: None)

        self.resolver = resolver or EngineResolver()
        self.token = CancelToken()
        self.planner = Planner(self.resolver, request.mode)
        self.collisions = CollisionResolver(request.policy)
        self.workspace = JobWorkspace(request.target)

        self.result = JobResult(total=len(request.items))
        self.fatal: CoreError | None = None

        self._ratios: dict[str, float] = {item.name: 0.0 for item in request.items}
        self._lock = threading.Lock()

    # ------------------------------------------------------------ controlo
    def cancel(self) -> None:
        self.token.cancel()
        self._emit("ev_cancel_requested", level=Level.WARNING)

    def toggle_pause(self) -> bool:
        paused = self.token.toggle_pause()
        self._emit("ev_paused" if paused else "ev_resumed")
        return paused

    @property
    def is_cancelled(self) -> bool:
        return self.token.cancelled

    # --------------------------------------------------------- ambiente
    def planned_engines(self) -> set[str]:
        optimistic = Planner(_OptimisticResolver(), self.request.mode)
        engines: set[str] = set()
        for item in self.request.items:
            for stage in optimistic.plan(sniff(item)):
                if stage.engine:          # etapas nativas não têm binário
                    engines.add(stage.engine)
        return engines

    def verify_environment(self) -> tuple[bool, list[str]]:
        """(ambiente pronto, motores em falta que deviam estar distribuídos)."""
        missing_bundled: list[str] = []
        missing_optional: list[str] = []

        for engine_id in sorted(self.planned_engines()):
            if self.resolver.path(engine_id) is not None:
                continue
            spec = ENGINES.get(engine_id)
            label = spec.label if spec else engine_id
            (missing_bundled if spec and spec.bundled else missing_optional).append(label)

        if missing_optional:
            self._emit(
                "ev_engine_optional_missing",
                {"engines": ", ".join(missing_optional)},
                Level.WARNING,
            )
        if missing_bundled:
            self._emit(
                "ev_engine_missing",
                {"engines": ", ".join(missing_bundled)},
                Level.ERROR,
            )
            return False, missing_bundled

        self._emit("ev_env_ok")
        return True, []

    # ------------------------------------------------------------- execução
    def run(self) -> JobResult:
        request = self.request
        self._emit("ev_job_start", {"mode": request.mode.value, "count": len(request.items)})

        self._warn_about_directories()
        JobWorkspace.purge_stale(request.target)
        self.workspace.prepare()

        for item in request.items:
            self.on_item(ItemStatus(item.name, ItemState.QUEUED))

        workers = max(1, min(request.workers, len(request.items) or 1))
        try:
            with ThreadPoolExecutor(max_workers=workers, thread_name_prefix="zar") as pool:
                futures = {pool.submit(self._process, item): item for item in request.items}
                for future in as_completed(futures):
                    try:
                        future.result()
                    except Cancelled:
                        pass
                    except EngineMissing as exc:
                        # Motor apagado a meio: interrompe o lote inteiro e
                        # deixa a UI levantar o alerta de antivírus.
                        if self.fatal is None:
                            self.fatal = exc
                        self.token.cancel()
                    except Exception as exc:                    # pragma: no cover
                        logger.exception("Falha inesperada no worker")
                        self._emit("ev_item_failed", {"name": "?", "error": str(exc)}, Level.ERROR)
        finally:
            self.workspace.cleanup()

        if self.token.cancelled and self.fatal is None:
            self._emit("ev_job_cancelled", level=Level.WARNING)
        else:
            self._emit(
                "ev_job_done",
                {
                    "completed": self.result.completed,
                    "failed": self.result.failed,
                    "skipped": self.result.skipped,
                },
                Level.SUCCESS if not self.result.failed else Level.WARNING,
            )

        if self.fatal is not None:
            raise self.fatal
        return self.result

    # --------------------------------------------------------------- item
    def _process(self, item: Path) -> None:
        name = item.name
        if self.token.cancelled:
            self._finish(name, ItemState.CANCELLED)
            return

        work_dir = self.workspace.item_dir(name)
        base_name = item.stem if item.is_file() else item.name
        context = StageContext(
            base_name=base_name,
            work_dir=work_dir,
            target_dir=self.request.target,
            runner=None,
            resolver=self.resolver,
            options=self.request.options,
        )

        executed = 0
        artifact = Artifact(item, sniff(item))

        try:
            if artifact.fmt is Fmt.UNKNOWN:
                self._emit("ev_item_unknown", {"name": name}, Level.WARNING)
                self._finish(name, ItemState.SKIPPED)
                return

            self._emit("ev_item_start", {"name": name, "fmt": artifact.fmt.value})
            weights = self._weights(artifact.fmt)
            base_ratio = 0.0

            while executed < MAX_CHAIN_STEPS:
                self.token.raise_if_cancelled()
                try:
                    stage = self.planner.next_stage(artifact.fmt)
                except NoRoute:
                    if executed == 0:
                        missing = self.planner.missing_for(artifact.fmt)
                        self._emit(
                            "ev_item_no_route",
                            {"name": name, "fmt": artifact.fmt.value,
                             "engines": ", ".join(missing) or "-"},
                            Level.WARNING,
                        )
                        self._finish(name, ItemState.SKIPPED)
                        return
                    break

                if stage is None:
                    break

                weight = weights[min(executed, len(weights) - 1)]
                self.on_item(ItemStatus(name, ItemState.RUNNING, stage.id, base_ratio))

                def report(percent, line, _name=name, _stage=stage.id,
                           _base=base_ratio, _weight=weight):
                    ratio = _base + (percent or 0.0) * _weight
                    self._set_ratio(_name, ratio)
                    self.on_item(ItemStatus(_name, ItemState.RUNNING, _stage, ratio, line))

                context.runner = ProcessRunner(self.resolver, self.token, report)
                context.step = executed
                artifact = stage.run(artifact, context)

                executed += 1
                base_ratio = min(1.0, base_ratio + weight)
                self._set_ratio(name, base_ratio)

            if executed == 0:
                self._emit("ev_item_nothing_to_do", {"name": name})
                self._finish(name, ItemState.SKIPPED)
                return

            # O nome de dentro do pacote só manda quando o do ficheiro é
            # um identificador que não diz nada a ninguém.
            final_name = base_name
            if context.suggested_name and looks_like_identifier(base_name):
                final_name = context.suggested_name

            self._deliver(item, artifact, final_name, name)

        except Cancelled:
            self._finish(name, ItemState.CANCELLED)
            raise
        except EngineMissing:
            self._finish(name, ItemState.FAILED)
            raise
        except CoreError as exc:
            self._emit(
                "ev_item_failed",
                {"name": name, "error": getattr(exc, "detail", "") or str(exc)},
                Level.ERROR,
            )
            self._finish(name, ItemState.FAILED, error_key=exc.key, error_args=exc.args_dict)
        except OSError as exc:
            self._emit("ev_item_failed", {"name": name, "error": str(exc)}, Level.ERROR)
            self._finish(name, ItemState.FAILED)
        finally:
            self._cleanup(work_dir)

    # ------------------------------------------------------------ entrega
    def _deliver(self, original: Path, artifact: Artifact, base_name: str, name: str) -> None:
        suffix = artifact.path.suffix if artifact.path.is_file() else ""
        destination = self.request.target / f"{base_name}{suffix}"
        resolved, action = self.collisions.resolve(destination)

        if resolved is None:
            self._emit("ev_item_skip_exists", {"name": name}, Level.WARNING)
            self._finish(name, ItemState.SKIPPED)
            return

        if action == "overwrite":
            self._emit("ev_collision_overwrite", {"name": resolved.name}, Level.WARNING)
        elif action == "rename":
            self._emit("ev_collision_rename", {"name": resolved.name}, Level.WARNING)

        final = move_into_place(artifact.path, resolved)

        # Só agora, com o resultado já no destino, é seguro apagar o original.
        if not self.request.keep_originals:
            self._remove_original(original, final)

        self._emit("ev_item_done", {"name": name, "output": final.name}, Level.SUCCESS)
        self._finish(name, ItemState.DONE)

    def _remove_original(self, original: Path, final: Path) -> None:
        try:
            if original.resolve() == final.resolve():
                return                      # o destino é o próprio original
            if original.is_dir():
                import shutil

                shutil.rmtree(original, ignore_errors=True)
            else:
                original.unlink(missing_ok=True)
            self._emit("ev_original_removed", {"name": original.name})
        except OSError as exc:
            self._emit(
                "ev_original_remove_failed",
                {"name": original.name, "error": str(exc)},
                Level.WARNING,
            )

    # ------------------------------------------------------------ auxiliares
    def _weights(self, fmt: Fmt) -> list[float]:
        planned = self.planner.plan(fmt)
        costs = [stage.cost for stage in planned] or [1.0]
        total = sum(costs) or 1.0
        return [cost / total for cost in costs]

    def _warn_about_directories(self) -> None:
        try:
            target = self.request.target.resolve()
        except OSError:
            return
        for item in self.request.items:
            try:
                if item.resolve() == target:
                    self._emit("ev_target_is_item", {"name": item.name}, Level.WARNING)
            except OSError:
                continue

    def _cleanup(self, work_dir: Path) -> None:
        import shutil

        shutil.rmtree(work_dir, ignore_errors=True)

    def _set_ratio(self, name: str, ratio: float) -> None:
        with self._lock:
            self._ratios[name] = max(0.0, min(1.0, ratio))
            total = sum(self._ratios.values())
            done = self.result.completed + self.result.failed + self.result.skipped + self.result.cancelled
            count = max(1, self.result.total)
        self.on_progress(Progress(done, self.result.total, total / count))

    def _finish(self, name: str, state: ItemState, error_key=None, error_args=None) -> None:
        with self._lock:
            if state is ItemState.DONE:
                self.result.completed += 1
                self._ratios[name] = 1.0
            elif state is ItemState.FAILED:
                self.result.failed += 1
            elif state is ItemState.SKIPPED:
                self.result.skipped += 1
                self._ratios[name] = 1.0
            elif state is ItemState.CANCELLED:
                self.result.cancelled += 1
            total = sum(self._ratios.values())
            done = self.result.completed + self.result.failed + self.result.skipped + self.result.cancelled
            count = max(1, self.result.total)

        self.on_item(ItemStatus(name, state, error_key=error_key, error_args=error_args or {}))
        self.on_progress(Progress(done, self.result.total, total / count))

    def _emit(self, key: str, args: dict | None = None, level: Level = Level.INFO) -> None:
        self.on_event(Event(key, args or {}, level))
