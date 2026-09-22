"""Feedback sonoro da interface.

Porquê QSoundEffect e não QAudioSink: o QSoundEffect existe precisamente para
sons curtos de UI -- pré-carrega o WAV e toca com latência baixa. O QAudioSink
só compensa quando se quer sintetizar áudio em tempo real, o que aqui seria
complexidade sem retorno.

Substitui o SoundService antigo, que lançava uma thread e um processo
`paplay`/`afplay` a cada som -- caro, dependente de binários do sistema, e com
um `winsound.MessageBeep` no Windows que soa a erro de sistema.

Desacoplamento: em vez de espalhar `play()` por dezenas de widgets, instala-se
um único event filter na QApplication. Um widget que não queira som declara
`setProperty("sfx", False)`.
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path

from PySide6.QtCore import QElapsedTimer, QEvent, QObject, QUrl
from PySide6.QtWidgets import QAbstractButton

from services.logging_service import logger
from services.paths import assets_dir

try:
    from PySide6.QtMultimedia import QSoundEffect
except ImportError:                                # QtMultimedia ausente no build
    QSoundEffect = None


class Sfx(str, Enum):
    CLICK = "click"
    NAV = "nav"
    SUCCESS = "success"
    ERROR = "error"


class SoundManager(QObject):
    # Evita metralhadora de cliques quando se carrega repetidamente.
    MIN_GAP_MS = 45

    def __init__(self, cfg, directory: Path | None = None, parent=None):
        super().__init__(parent)
        self.cfg = cfg
        self.directory = Path(directory) if directory else assets_dir() / "sfx"
        self._effects: dict[Sfx, object] = {}
        self._last: dict[Sfx, int] = {}
        self._clock = QElapsedTimer()
        self._clock.start()
        self.available = QSoundEffect is not None

        if not self.available:
            logger.info("QtMultimedia indisponível: a interface fica silenciosa.")
            return

        self._log_backend_plugins()

        for sound in Sfx:
            path = self.directory / f"{sound.value}.wav"
            if not path.exists():
                logger.warning("Efeito sonoro em falta: %s", path)
                continue
            effect = QSoundEffect(self)
            effect.statusChanged.connect(
                lambda _sound=sound, _effect=effect: self._log_status(_sound, _effect)
            )
            effect.setSource(QUrl.fromLocalFile(str(path)))
            self._effects[sound] = effect

        if not self._effects:
            logger.info("Nenhum WAV encontrado em %s", self.directory)
        self.set_volume(self.cfg.get_float("sfx_volume"))

    # ---------------------------------------------------------------- API
    @property
    def enabled(self) -> bool:
        return self.cfg.get_bool("sfx_enabled") and bool(self._effects)

    def set_enabled(self, enabled: bool) -> None:
        self.cfg.set("sfx_enabled", bool(enabled))

    def set_volume(self, volume: float) -> None:
        value = max(0.0, min(1.0, float(volume)))
        for effect in self._effects.values():
            effect.setVolume(value)

    @staticmethod
    def _log_backend_plugins() -> None:
        """Diagnóstico de arranque: sem isto, um som que falha em silêncio
        (backend do QtMultimedia ausente do build empacotado, ou presente mas
        sem conseguir ligar-se a um dispositivo de áudio real) não deixa
        nenhuma pista no registo além do aviso tardio do `statusChanged`. Isto
        confirma logo no arranque se o Qt encontrou algum plugin de
        multimédia, e onde foi à procura -- o `qt6-multimedia-ffmpeg` do
        sistema (pacman/apt/brew) NÃO tem efeito nenhum aqui: um build do
        Nuitka é auto-contido e usa apenas os plugins que vieram dentro do
        próprio pacote do PySide6, nunca os do Qt do sistema."""
        try:
            from PySide6.QtCore import QLibraryInfo

            plugins_root = Path(QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath))
            multimedia_dir = plugins_root / "multimedia"
            found = sorted(p.name for p in multimedia_dir.glob("*")) if multimedia_dir.is_dir() else []
            if found:
                logger.info(
                    "Plugins de QtMultimedia em %s: %s", multimedia_dir, ", ".join(found),
                )
            else:
                logger.warning(
                    "Nenhum plugin de QtMultimedia encontrado em %s -- o backend de "
                    "áudio (normalmente 'libffmpegmediaplugin') não foi incluído neste "
                    "build. Isto é independente de qualquer pacote de sistema instalado.",
                    multimedia_dir,
                )
        except Exception as exc:  # noqa: BLE001 -- diagnóstico, nunca deve impedir o arranque
            logger.debug("Não foi possível listar plugins de QtMultimedia: %s", exc)

        # O plugin FFmpeg só decodifica; tocar o som é outra camada -- pede
        # um dispositivo de saída de áudio real, que o Qt descobre via
        # PipeWire/PulseAudio/ALSA consoante o que o sistema expõe. Se o
        # play() é chamado com sucesso (log INFO próprio) mas continua sem
        # som, é aqui que a resposta está: sem um output por omissão, o
        # QSoundEffect não tem para onde mandar o áudio, e isso não aparece
        # como erro em lado nenhum -- só haveria silêncio.
        try:
            from PySide6.QtMultimedia import QMediaDevices

            outputs = QMediaDevices.audioOutputs()
            default = QMediaDevices.defaultAudioOutput()
            if not outputs:
                logger.warning(
                    "QMediaDevices não encontrou NENHUM dispositivo de saída de áudio "
                    "-- o QSoundEffect não tem para onde tocar o som, mesmo que o "
                    "ficheiro carregue e o play() seja chamado sem erro."
                )
            else:
                logger.info(
                    "Dispositivos de saída de áudio: %s (por omissão: %s)",
                    ", ".join(d.description() for d in outputs),
                    default.description() if not default.isNull() else "nenhum",
                )
        except Exception as exc:  # noqa: BLE001
            logger.debug("Não foi possível listar dispositivos de áudio: %s", exc)

    def _log_status(self, sound: Sfx, effect) -> None:
        """QSoundEffect carrega de forma assíncrona; sem isto, um motor de
        áudio em falta (backend do QtMultimedia ausente, é o caso mais comum
        em builds mínimas do Linux) faz o som falhar sempre em silêncio, sem
        nada no registo a explicar porquê."""
        status = effect.status()
        if status == QSoundEffect.Status.Error:
            logger.warning(
                "Efeito sonoro '%s' não carregou (motor de áudio do QtMultimedia "
                "em falta ou sem suporte a WAV?). Fonte: %s",
                sound.value, effect.source().toLocalFile(),
            )
        elif status == QSoundEffect.Status.Ready:
            # Antes era logger.debug() -- o nível do logger é INFO (ver
            # logging_service.py), por isso esta linha nunca aparecia no
            # ficheiro, mesmo quando tudo corria bem. Sem ela é impossível
            # distinguir "carregou e o play() é que falha" de "nunca chegou
            # a carregar" só a olhar para o registo.
            logger.info("Efeito sonoro '%s' pronto (backend OK).", sound.value)

    def play(self, sound: Sfx) -> None:
        """Só pode ser chamado a partir da thread da GUI."""
        effect = self._effects.get(sound)
        if effect is None:
            logger.warning("play('%s') chamado mas o efeito nunca foi carregado.", sound.value)
            return
        if not self.enabled:
            logger.info(
                "play('%s') ignorado: som desligado nas definições (sfx_enabled=%s).",
                sound.value, self.cfg.get_bool("sfx_enabled"),
            )
            return
        if QSoundEffect is not None and effect.status() != QSoundEffect.Status.Ready:
            logger.warning(
                "play('%s') ignorado: status=%s (não está Ready).",
                sound.value, effect.status(),
            )
            return

        now = self._clock.elapsed()
        if now - self._last.get(sound, -10_000) < self.MIN_GAP_MS:
            logger.info("play('%s') ignorado: debounce (< %dms desde o último).", sound.value, self.MIN_GAP_MS)
            return
        self._last[sound] = now
        try:
            effect.play()
            logger.info(
                "play('%s') chamado -- volume=%.2f, muted=%s, source=%s",
                sound.value, effect.volume(), effect.isMuted(), effect.source().toLocalFile(),
            )
        except RuntimeError as exc:
            logger.warning("Falha ao tocar '%s': %s", sound.value, exc)

    def preview(self) -> None:
        self.play(Sfx.NAV)

    # -------------------------------------------------------- event filter
    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.MouseButtonRelease and isinstance(obj, QAbstractButton):
            flag = obj.property("sfx")
            if obj.isEnabled() and flag is not False:
                self.play(Sfx.NAV if flag == "nav" else Sfx.CLICK)
        return False

    def install(self, app) -> None:
        app.installEventFilter(self)
