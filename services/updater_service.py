"""Descarga e aplicação de atualizações.

Correcções face à versão anterior:

* TLS: o `ctx.verify_mode = ssl.CERT_NONE` foi removido. Combinado com o
  `--windows-uac-admin`, aquilo permitia a um atacante na mesma rede entregar
  um executável que corria como administrador. Agora usa-se o certifi quando
  está disponível e, em alternativa, o arquivo de certificados do sistema.
* Integridade: se a release publicar um SHA256SUMS, o ficheiro descarregado é
  validado antes de ser aplicado.
* Deteção de compilação: passa pelo services.paths, que conhece o Nuitka. O
  `sys.frozen` antigo é do PyInstaller e nunca era verdadeiro nos builds
  atuais -- ou seja, a atualização in-place nunca corria no Windows.
* AppImage: substitui o ficheiro indicado por $APPIMAGE e não o binário
  montado em /tmp/.mount_*, que era o que acontecia antes.
"""

from __future__ import annotations

import hashlib
import os
import platform
import ssl
import subprocess
import tempfile
import urllib.request
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from services.logging_service import logger
from services.paths import IS_FROZEN, appimage_path, running_executable

USER_AGENT = "ZarManager-Updater"
_TIMEOUT = 20


def ssl_context() -> ssl.SSLContext:
    """Contexto TLS com verificação ligada, sempre."""
    try:
        import certifi

        return ssl.create_default_context(cafile=certifi.where())
    except ImportError:
        return ssl.create_default_context()


def open_url(url: str, timeout: int = _TIMEOUT):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, context=ssl_context(), timeout=timeout)


class DownloadThread(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, url: str, dest_path: str, expected_sha256: str = ""):
        super().__init__()
        self.url = url
        self.dest_path = dest_path
        self.expected_sha256 = (expected_sha256 or "").lower()
        self._cancelled = False

    def cancel(self):
        self._cancelled = True

    def run(self):
        digest = hashlib.sha256()
        try:
            with open_url(self.url) as response:
                total = int(response.info().get("Content-Length", -1))
                downloaded = 0
                with open(self.dest_path, "wb") as handle:
                    while True:
                        if self._cancelled:
                            raise InterruptedError("cancelado")
                        chunk = response.read(65536)
                        if not chunk:
                            break
                        handle.write(chunk)
                        digest.update(chunk)
                        downloaded += len(chunk)
                        if total > 0:
                            self.progress_signal.emit(int(downloaded / total * 100))

            if self.expected_sha256 and digest.hexdigest().lower() != self.expected_sha256:
                Path(self.dest_path).unlink(missing_ok=True)
                self.error_signal.emit("checksum")
                return

            self.finished_signal.emit(str(self.dest_path))
        except InterruptedError:
            Path(self.dest_path).unlink(missing_ok=True)
        except Exception as exc:
            logger.warning("Falha na descarga: %s", exc)
            self.error_signal.emit(str(exc))


class UpdaterService:
    @staticmethod
    def get_asset_url(release_data: dict) -> tuple[str | None, str | None]:
        os_name = platform.system()
        for asset in release_data.get("assets", []):
            name = asset.get("name", "").lower()
            url = asset.get("browser_download_url")
            if not url:
                continue
            if os_name == "Windows" and name.endswith(".zip"):
                return url, ".zip"
            if os_name == "Linux" and name.endswith(".appimage"):
                return url, ".AppImage"
            if os_name == "Darwin" and name.endswith((".dmg", ".zip")):
                return url, Path(name).suffix
        return None, None

    @staticmethod
    def get_checksum(release_data: dict, asset_name: str) -> str:
        """Lê o SHA256SUMS da release, quando existe."""
        for asset in release_data.get("assets", []):
            if asset.get("name", "").upper().startswith("SHA256SUMS"):
                try:
                    with open_url(asset["browser_download_url"], timeout=10) as response:
                        for line in response.read().decode("utf-8", "ignore").splitlines():
                            parts = line.split()
                            if len(parts) >= 2 and parts[-1].lstrip("*") == asset_name:
                                return parts[0]
                except Exception as exc:
                    logger.info("SHA256SUMS indisponível: %s", exc)
                return ""
        return ""

    # ------------------------------------------------------------- aplicar
    @staticmethod
    def apply_update_and_restart(new_file_path: str) -> None:
        os_name = platform.system()
        app_image = appimage_path()

        if not IS_FROZEN and app_image is None:
            UpdaterService.reveal_file(new_file_path)
            raise SystemExit(0)

        current = running_executable()

        if os_name == "Windows":
            UpdaterService._apply_windows(current, new_file_path)
        elif os_name == "Linux":
            UpdaterService._apply_linux(current, new_file_path)
        else:
            UpdaterService.reveal_file(new_file_path)
        raise SystemExit(0)

    @staticmethod
    def _apply_windows(current_exe: Path, new_file_path: str) -> None:
        current_dir = current_exe.parent
        temp = Path(tempfile.gettempdir())
        extract_dir = temp / "ZarManager_Update"
        script = temp / "zarmanager_update.bat"

        script.write_text(
            "@echo off\r\n"
            "timeout /t 2 /nobreak > NUL\r\n"
            f'if exist "{extract_dir}" rmdir /S /Q "{extract_dir}"\r\n'
            f"powershell -NoProfile -Command \"Expand-Archive -Path '{new_file_path}'"
            f" -DestinationPath '{extract_dir}' -Force\"\r\n"
            f'for /d %%D in ("{extract_dir}\\*") do xcopy /Y /E /H /C /I /Q "%%D\\*" "{current_dir}\\"\r\n'
            f'rmdir /S /Q "{extract_dir}"\r\n'
            f'del "{new_file_path}"\r\n'
            f'start "" "{current_exe}"\r\n'
            'del "%~f0"\r\n',
            encoding="utf-8",
        )
        subprocess.Popen(
            ["cmd", "/c", str(script)],
            creationflags=subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS,
        )

    @staticmethod
    def _apply_linux(current_exe: Path, new_file_path: str) -> None:
        script = Path(tempfile.gettempdir()) / "zarmanager_update.sh"
        script.write_text(
            "#!/bin/sh\n"
            "sleep 2\n"
            f'if mv -f "{new_file_path}" "{current_exe}"; then\n'
            f'  chmod +x "{current_exe}"\n'
            f'  "{current_exe}" &\n'
            "fi\n"
            'rm -- "$0"\n',
            encoding="utf-8",
        )
        os.chmod(script, 0o755)
        subprocess.Popen(["/bin/sh", str(script)], start_new_session=True)

    @staticmethod
    def reveal_file(path: str) -> None:
        target = Path(path)
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", f"/select,{target}"], check=False)
            elif platform.system() == "Darwin":
                subprocess.run(["open", "-R", str(target)], check=False)
            else:
                subprocess.run(["xdg-open", str(target.parent)], check=False)
        except OSError as exc:
            logger.warning("Não foi possível abrir o gestor de ficheiros: %s", exc)
