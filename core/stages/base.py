"""Contrato das etapas (padrão Strategy + Registry).

Cada motor externo é encapsulado numa Stage que declara o que consome, o que
produz e como constrói a linha de comando. O planeador liga-as sozinho, o que
significa que adicionar PKG, CHD ou RVZ é adicionar um ficheiro neste pacote
-- sem mexer no pipeline nem duplicar código.

Todas as etapas escrevem na área de trabalho do item, nunca directamente no
destino. Só quando a cadeia inteira termina é que o artefacto final é movido
para o destino. É isso que torna a operação transaccional: se o zarchive
falhar depois do 7z ter corrido, o original continua intacto e o destino
continua limpo.
"""

from __future__ import annotations

import re
import shutil
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import ClassVar

from core.formats import Fmt, payload_path, sniff


@dataclass(frozen=True)
class Artifact:
    path: Path
    fmt: Fmt
    temporary: bool = False       # vive na área de trabalho

    def with_path(self, path: Path, fmt: Fmt | None = None) -> "Artifact":
        return Artifact(path, fmt or self.fmt, self.temporary)


@dataclass
class StageContext:
    """Tudo o que uma etapa precisa de saber sobre o item em curso."""

    base_name: str                # nome do item original, sem extensão
    work_dir: Path                # área de trabalho exclusiva deste item
    target_dir: Path
    runner: object                # ProcessRunner
    resolver: object              # EngineResolver
    options: dict = field(default_factory=dict)
    step: int = 0
    total_steps: int = 1

    # Um contentor do Xbox 360 chama-se "8A1B2C3D" no disco mas sabe o nome do
    # jogo por dentro. Uma etapa que o descubra deixa-o aqui e a entrega usa-o
    # em vez do nome do ficheiro.
    suggested_name: str = ""

    def temp_path(self, suffix: str = "") -> Path:
        self.work_dir.mkdir(parents=True, exist_ok=True)
        return self.work_dir / f"{self.base_name}{suffix}"

    def suggest_name(self, name: str) -> None:
        """Propõe um nome melhor para o resultado final, se for utilizável."""
        cleaned = sanitize_name(name)
        if cleaned:
            self.suggested_name = cleaned


_UNSAFE_NAME = re.compile(r'[\\/:*?"<>|\x00-\x1f]')


def sanitize_name(name: str) -> str:
    """Nome de ficheiro seguro a partir de texto vindo de dentro de um pacote.

    O nome de exibição de um contentor é escrito por quem o empacotou; pode
    trazer barras, dois pontos ou caracteres de controlo. Nada disto pode
    chegar a um caminho.
    """
    cleaned = _UNSAFE_NAME.sub(" ", name or "").strip(" .")
    cleaned = " ".join(cleaned.split())
    if cleaned.upper() in {"", "CON", "PRN", "AUX", "NUL"}:
        return ""                     # nomes reservados no Windows
    return cleaned[:120]


_IDENTIFIER_NAME = re.compile(r"^[0-9A-Fa-f]{8,}$")


def looks_like_identifier(name: str) -> bool:
    """O nome do ficheiro não diz nada a ninguém?

    O dashboard do Xbox 360 grava os contentores com o identificador do
    conteúdo por nome -- "8A1B2C3D", ou 42 dígitos hexadecimais. Nesses casos
    vale a pena usar o nome que vem dentro do pacote. Quando o utilizador já
    deu um nome legível ao ficheiro, esse é que manda.
    """
    return bool(_IDENTIFIER_NAME.match(name or ""))


class Stage(ABC):
    id: ClassVar[str] = ""
    engine: ClassVar[str] = ""
    consumes: ClassVar[frozenset] = frozenset()
    produces: ClassVar[Fmt] = Fmt.UNKNOWN

    # O 7-Zip devolve 1 em avisos inofensivos (muito comum em dumps da Scene);
    # cada etapa declara os códigos que tolera.
    ok_codes: ClassVar[frozenset] = frozenset({0})
    progress_re: ClassVar[re.Pattern | None] = None

    # Custo relativo, usado para distribuir o peso no progresso total.
    cost: ClassVar[float] = 1.0
    creates_directory: ClassVar[bool] = False
    label_key: ClassVar[str] = ""

    # Descascar um invólucro de pasta única faz sentido no que sai de um .zip
    # (o empacotador da Scene deixa sempre uma pasta a mais), mas não num
    # contentor cuja estrutura interna é a que a consola espera encontrar.
    unwrap_payload: ClassVar[bool] = True

    # ------------------------------------------------------------- comando
    @abstractmethod
    def output_for(self, artifact: Artifact, ctx: StageContext) -> Path:
        """Caminho que esta etapa vai escrever (sempre dentro de work_dir)."""

    @abstractmethod
    def build_command(self, artifact: Artifact, output: Path, ctx: StageContext) -> list[str]:
        """Argumentos do motor (sem o caminho do binário)."""

    # ------------------------------------------------------------ execução
    def prepare_output(self, artifact: Artifact, ctx: StageContext) -> Path:
        """Limpa restos de uma tentativa anterior e cria a pasta de destino."""
        output = self.output_for(artifact, ctx)
        if output.exists():
            shutil.rmtree(output, ignore_errors=True) if output.is_dir() else output.unlink(missing_ok=True)

        output.parent.mkdir(parents=True, exist_ok=True)
        if self.creates_directory:
            output.mkdir(parents=True, exist_ok=True)
        return output

    def run(self, artifact: Artifact, ctx: StageContext) -> Artifact:
        output = self.prepare_output(artifact, ctx)

        ctx.runner.run(
            self.engine,
            self.build_command(artifact, output, ctx),
            cwd=ctx.work_dir,
            ok_codes=self.ok_codes,
            progress_re=self.progress_re,
        )
        return self.finalize(output, ctx)

    def finalize(self, output: Path, ctx: StageContext) -> Artifact:
        """Reclassifica o que saiu. Depois de extrair um contentor, só o
        conteúdo diz o que ele era."""
        if not output.exists():
            from core.errors import EngineFailed

            raise EngineFailed(self.engine or self.id, 0, f"sem saída em {output.name}")

        if output.is_dir():
            try:
                if not any(output.iterdir()):
                    from core.errors import EngineFailed

                    raise EngineFailed(self.engine or self.id, 0, f"{output.name} ficou vazio")
            except OSError:
                pass

        resolved = (
            payload_path(output)
            if output.is_dir() and self.unwrap_payload
            else output
        )
        return Artifact(resolved, sniff(resolved), temporary=True)

    def available(self, resolver) -> bool:
        return resolver.path(self.engine) is not None


class NativeStage(Stage):
    """Etapa executada em Python puro, sem subprocesso.

    Nem todos os formatos têm um motor externo aceitável. Os contentores do
    Xbox 360 (STFS e GOD) são o primeiro caso: as ferramentas que existem são
    só para Windows, com interface gráfica, ou não são distribuíveis. Ler o
    formato aqui dentro sai mais barato do que empacotar mais um binário por
    sistema -- e elimina um motor que o antivírus possa apagar.

    O que muda face a uma etapa normal é apenas o `run`: o planeador, o
    progresso, a pausa e o cancelamento continuam a ser exactamente os mesmos.
    `available()` devolve sempre True porque não há binário para procurar.
    """

    engine = ""                       # não há binário a resolver
    label_key = ""

    def build_command(self, artifact: Artifact, output: Path, ctx: StageContext) -> list[str]:
        raise NotImplementedError("uma etapa nativa não constrói linhas de comando")

    @abstractmethod
    def extract(self, artifact: Artifact, output: Path, ctx: StageContext,
                progress, should_cancel) -> None:
        """Escreve o resultado em `output`.

        `progress(ratio, label)` já vem limitado a 10 FPS e levanta Cancelled
        sozinho; `should_cancel()` serve para os intervalos em que não há
        progresso a reportar.
        """

    def run(self, artifact: Artifact, ctx: StageContext) -> Artifact:
        from core.errors import Cancelled, CoreError, EngineFailed

        output = self.prepare_output(artifact, ctx)
        from core.runner import native_callbacks

        progress, should_cancel = native_callbacks(ctx.runner)

        try:
            self.extract(artifact, output, ctx, progress, should_cancel)
        except (Cancelled, CoreError):
            raise
        except OSError as exc:
            raise EngineFailed(self.id, -1, str(exc)) from exc

        return self.finalize(output, ctx)

    def available(self, resolver) -> bool:
        return True


# --------------------------------------------------------------- registry
REGISTRY: dict[str, type[Stage]] = {}


def register(cls: type[Stage]) -> type[Stage]:
    if not cls.id:
        raise ValueError(f"{cls.__name__} sem id")
    REGISTRY[cls.id] = cls
    return cls


def all_stages() -> list[Stage]:
    return [cls() for cls in REGISTRY.values()]
