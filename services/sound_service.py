import platform
import subprocess
import threading
from typing import Literal
from services.logging_service import logger

class WindowsSoundBackend:
    @staticmethod
    def play(sound_type: str):
        try:
            import winsound
            winsound.MessageBeep(winsound.MB_OK if sound_type == "success" else winsound.MB_ICONHAND)
        except Exception as e:
            logger.warning(f"Erro no som Windows: {e}")

class LinuxSoundBackend:
    @staticmethod
    def play(sound_type: str):
        try:
            # 🟠 Fallback seguro para Wayland/X11 ignorando o print \a
            sound_file = "/usr/share/sounds/freedesktop/stereo/complete.oga" if sound_type == "success" else "/usr/share/sounds/freedesktop/stereo/dialog-error.oga"
            subprocess.run(["paplay", sound_file], stderr=subprocess.DEVNULL, check=False)
        except Exception:
            pass # No Linux, se não houver paplay, falha silenciosamente sem rebentar

class MacOSSoundBackend:
    @staticmethod
    def play(sound_type: str):
        try:
            sound_file = "/System/Library/Sounds/Glass.aiff" if sound_type == "success" else "/System/Library/Sounds/Basso.aiff"
            subprocess.run(["afplay", sound_file], check=False)
        except Exception:
            pass

class SoundService:
    @staticmethod
    def play(sound_type: Literal["success", "error"] = "success") -> None:
        def _play_async():
            sys_name = platform.system()
            if sys_name == "Windows":
                WindowsSoundBackend.play(sound_type)
            elif sys_name == "Darwin":
                MacOSSoundBackend.play(sound_type)
            else:
                LinuxSoundBackend.play(sound_type)
                
        threading.Thread(target=_play_async, daemon=True).start()