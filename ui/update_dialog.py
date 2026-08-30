import json
import urllib.request
from urllib.error import URLError
import tempfile
from pathlib import Path

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
    QPushButton, QTextBrowser, QProgressBar
)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont

import locales
from services.updater_service import UpdaterService, DownloadThread

class GitHubFetchThread(QThread):
    result_signal = Signal(dict)
    error_signal = Signal(str)

    def run(self):
        url = "https://api.github.com/repos/dfdevx2/ZarManager/releases/latest"
        req = urllib.request.Request(url, headers={'User-Agent': 'ZarManager-App'})
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                self.result_signal.emit(data)
        except URLError as e:
            self.error_signal.emit(f"Falha de rede: {e.reason}")
        except Exception as e:
            self.error_signal.emit(str(e))

class UpdateDialog(QDialog):
    def __init__(self, current_version: str, lang: str = "pt-br", parent=None, pre_fetched_data=None):
        super().__init__(parent)
        self.current_version = current_version.lower().replace("v", "")
        self.lang = lang
        self.release_data = None
        self.dl_thread = None
        
        self._build_ui()
        
        # Se recebeu os dados do verificador automático, não volta a procurar
        if pre_fetched_data:
            self._on_fetch_success(pre_fetched_data)
        else:
            self._fetch_data()

    def get_text(self, key: str, fallback: str = "") -> str:
        return locales.get_text(self.lang, key) or fallback

    def _build_ui(self):
        t_title = self.get_text("msg_update_popup_title", "Atualização Disponível")
        self.setWindowTitle(t_title)
        self.setMinimumSize(650, 500)
        self.setWindowFlag(Qt.WindowType.WindowContextHelpButtonHint, False)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        
        self.lbl_title = QLabel(self.get_text("msg_checking_update", "Procurando atualizações..."))
        font = QFont()
        font.setPointSize(18)
        font.setBold(True)
        self.lbl_title.setFont(font)
        
        self.lbl_subtitle = QLabel(f"Versão Instalada: v{self.current_version}")
        self.lbl_subtitle.setStyleSheet("color: #888888; font-weight: bold;")
        
        self.changelog_box = QTextBrowser()
        self.changelog_box.setOpenExternalLinks(True)
        
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setFixedHeight(4)
        self.progress.setTextVisible(False)
        
        btn_layout = QHBoxLayout()
        self.btn_later = QPushButton(self.get_text("btn_exit_no", "Lembrar Mais Tarde"))
        self.btn_later.setMinimumHeight(35)
        self.btn_later.clicked.connect(self.reject)
        
        self.btn_update = QPushButton(self.get_text("btn_download_update", "Atualizar Agora"))
        self.btn_update.setMinimumHeight(35)
        self.btn_update.setEnabled(False)
        self.btn_update.setStyleSheet("background-color: #2ecc71; color: black; font-weight: bold; padding: 0px 20px;")
        self.btn_update.clicked.connect(self._start_download)
        
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_later)
        btn_layout.addWidget(self.btn_update)
        
        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_subtitle)
        layout.addWidget(self.progress)
        layout.addWidget(self.changelog_box)
        layout.addLayout(btn_layout)

    def _fetch_data(self):
        self.thread = GitHubFetchThread()
        self.thread.result_signal.connect(self._on_fetch_success)
        self.thread.error_signal.connect(self._on_fetch_error)
        self.thread.start()

    def _on_fetch_success(self, data):
        self.progress.hide()
        self.release_data = data
        
        latest_version = data.get("tag_name", "").lower().replace("v", "")
        body_markdown = data.get("body", "Nenhum changelog disponível.")
        
        self.changelog_box.setMarkdown(body_markdown)
        
        if latest_version > self.current_version:
            t_avail = self.get_text("msg_update_avail", "Nova versão disponível!").format("v" + latest_version)
            self.lbl_title.setText(f"🚀 {t_avail}")
            self.btn_update.setEnabled(True)
        else:
            t_latest = self.get_text("msg_update_latest", "O sistema está atualizado.").format("v" + latest_version)
            self.lbl_title.setText(f"✅ {t_latest}")
            self.btn_update.setText("Fechar")
            self.btn_update.setStyleSheet("") 
            self.btn_update.setEnabled(True)
            self.btn_update.clicked.disconnect()
            self.btn_update.clicked.connect(self.accept)
            self.btn_later.hide()

    def _on_fetch_error(self, error_msg):
        self.progress.hide()
        self.lbl_title.setText("❌ " + self.get_text("msg_update_error", "Falha na comunicação com o servidor."))
        self.changelog_box.setText(f"Detalhes técnicos:\n{error_msg}")
        self.btn_update.setEnabled(False)

    def _start_download(self):
        import platform
        import webbrowser
        
        if platform.system() == "Darwin":
            release_url = self.release_data.get("html_url", "https://github.com/dfdevx2/ZarManager/releases/latest")
            webbrowser.open(release_url)
            self.accept()
            return
            
        url, ext = UpdaterService.get_asset_url(self.release_data)
        
        if not url:
            self.changelog_box.setText("❌ Nenhum binário compatível com o seu Sistema Operativo foi encontrado nas Releases do GitHub.")
            return

        self.btn_update.setEnabled(False)
        self.btn_later.setEnabled(False)
        self.progress.show()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        
        self.lbl_title.setText("A transferir a nova versão...")
        self.btn_update.setText("Transferindo...")

        temp_dir = Path(tempfile.gettempdir())
        dest_path = temp_dir / f"ZarManager_Update{ext}"

        self.dl_thread = DownloadThread(url, str(dest_path))
        self.dl_thread.progress_signal.connect(self.progress.setValue)
        self.dl_thread.error_signal.connect(self._on_fetch_error)
        self.dl_thread.finished_signal.connect(self._on_download_finished)
        self.dl_thread.start()

    def _on_download_finished(self, downloaded_path: str):
        self.lbl_title.setText("✅ Transferência Concluída! A reiniciar...")
        self.progress.setValue(100)
        UpdaterService.apply_update_and_restart(downloaded_path)