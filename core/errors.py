"""Exceções do core, todas com chave de tradução."""

from __future__ import annotations


class CoreError(Exception):
    key = "err_generic"

    def __init__(self, message: str = "", **args):
        super().__init__(message or self.key)
        self.args_dict = args


class EngineMissing(CoreError):
    """Binário ausente no arranque da etapa.

    Quase sempre é o antivírus a apagar o motor: a pasta foi validada no
    arranque e o ficheiro desapareceu entretanto. É este o sinal que dispara
    o alerta de antivírus na UI -- e agora ele propaga-se mesmo até lá.
    """

    key = "err_engine_missing"

    def __init__(self, engine_id: str, path: str = ""):
        super().__init__(f"Motor ausente: {engine_id}", engine=engine_id, path=path)
        self.engine_id = engine_id
        self.path = path


class EngineFailed(CoreError):
    key = "err_engine_failed"

    def __init__(self, engine_id: str, code: int, detail: str = ""):
        super().__init__(
            f"{engine_id} terminou com código {code}", engine=engine_id, code=code, detail=detail
        )
        self.engine_id = engine_id
        self.code = code
        self.detail = detail


class ElevationRequired(CoreError):
    """WinError 740: o Windows exige elevação para lançar o processo."""

    key = "err_elevation_required"

    def __init__(self, engine_id: str):
        super().__init__("Elevação necessária", engine=engine_id)
        self.engine_id = engine_id


class Cancelled(CoreError):
    key = "err_cancelled"


class NoRoute(CoreError):
    """Não existe cadeia de etapas entre o formato de entrada e o alvo."""

    key = "err_no_route"

    def __init__(self, source: str, target: str):
        super().__init__(f"Sem rota {source} -> {target}", source=source, target=target)
        self.source = source
        self.target = target
