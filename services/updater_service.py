import os
import sys
import platform
import subprocess
import urllib.request
import tempfile
import ssl
from pathlib import Path
from PySide6.QtCore import QThread, Signal

class DownloadThread(QThread):
    progress_signal = Signal(int)
    finished_signal = Signal(str)
    error_signal = Signal(str)

    def __init__(self, url, dest_path):
        super().__init__()
        self.url = url
        self.dest_path = dest_path

    def run(self):
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            
            req = urllib.request.Request(self.url, headers={'User-Agent': 'ZarManager-Updater'})
            with urllib.request.urlopen(req, context=ctx, timeout=15) as response:
                total_size = int(response.info().get('Content-Length', -1))
                downloaded = 0
                chunk_size = 16384 

                with open(self.dest_path, 'wb') as f:
                    while True:
                        chunk = response.read(chunk_size)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            progress = int((downloaded / total_size) * 100)
                            self.progress_signal.emit(progress)

            self.finished_signal.emit(str(self.dest_path))
        except Exception as e:
            self.error_signal.emit(str(e))

class UpdaterService:
    @staticmethod
    def get_asset_url(release_data: dict) -> tuple[str, str]:
        os_name = platform.system()
        assets = release_data.get("assets", [])

        for asset in assets:
            name = asset["name"].lower()
            if os_name == "Windows" and name.endswith(".zip"):
                return asset["browser_download_url"], ".zip"
            elif os_name == "Linux" and name.endswith(".appimage"):
                return asset["browser_download_url"], ".AppImage"
            elif os_name == "Darwin" and (name.endswith(".dmg") or name.endswith(".zip")):
                return asset["browser_download_url"], Path(name).suffix
                
        return None, None

    @staticmethod
    def apply_update_and_restart(new_file_path: str):
        os_name = platform.system()
        is_compiled = getattr(sys, 'frozen', False)
        
        if not is_compiled and not sys.argv[0].endswith(".AppImage"):
            UpdaterService._reveal_file(new_file_path)
            sys.exit(0)

        current_exe = sys.executable if is_compiled else sys.argv[0]

        if os_name == "Windows":
            current_dir = Path(current_exe).parent
            bat_path = Path(tempfile.gettempdir()) / "zarmanager_update.bat"
            extract_dir = Path(tempfile.gettempdir()) / "ZarManager_Extracted"
            
            with open(bat_path, "w") as f:
                f.write(f"""@echo off
timeout /t 2 /nobreak > NUL
powershell -Command "Expand-Archive -Path '{new_file_path}' -DestinationPath '{extract_dir}' -Force"
xcopy /Y /E /H /C /I /R "{extract_dir}\\ZarManager-Windows\\*" "{current_dir}\\"
rmdir /S /Q "{extract_dir}"
del "{new_file_path}"
start "" "{current_exe}"
del "%~f0"
""")
            subprocess.Popen(str(bat_path), shell=True, creationflags=subprocess.CREATE_NO_WINDOW)
            sys.exit(0)

        elif os_name == "Linux":
            sh_path = Path(tempfile.gettempdir()) / "zarmanager_update.sh"
            with open(sh_path, "w") as f:
                f.write(f"""#!/bin/bash
sleep 2
rm "{current_exe}"
mv "{new_file_path}" "{current_exe}"
chmod +x "{current_exe}"
"{current_exe}" &
rm "$0"
""")
            os.chmod(sh_path, 0o755)
            subprocess.Popen(str(sh_path), shell=True)
            sys.exit(0)

        elif os_name == "Darwin":
            UpdaterService._reveal_file(new_file_path)
            sys.exit(0)

    @staticmethod
    def _reveal_file(path: str):
        if platform.system() == "Windows":
            subprocess.run(["explorer", "/select,", str(path)])
        elif platform.system() == "Darwin":
            subprocess.run(["open", "-R", str(path)])
        else:
            subprocess.run(["xdg-open", str(Path(path).parent)])