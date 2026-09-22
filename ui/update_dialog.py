"""Diálogo de atualização."""

from __future__ import annotations

import json
import platform
import tempfile
import webbrowser
from pathlib import Path
from urllib.error import URLError

from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QDialog, QHBoxLayout, QLabel, QProgressBar, QTextBrowser, QVBoxLayout,
)

from services.logging_service import logger
from services.updater_service import DownloadThread, UpdaterService, open_url
from services.versioning import is_newer, normalize
from ui.widgets.card import action_button

RELEASE_API = "https://api.github.com/repos/dfdevx2/ZarManager/releases/latest"
RELEASE_PAGE = "https://github.com/dfdevx2/ZarManager/releases/latest"


class GitHubFetchThread(QThread):
    result_signal = Signal(dict)
    error_signal = Signal(str)

    def run(self) -> None:
        try:
            with open_url(RELEASE_API, timeout=12) as response:
                self.result_signal.emit(json.loads(response.read().decode("utf-8")))
        except URLError as exc:
            self.error_signal.emit(str(exc.reason))
        except Exception as exc:
            logger.info("Falha ao consultar releases: %s", exc)
            self.error_signal.emit(str(exc))


class UpdateDialog(QDialog):
    def __init__(self, current_version: str, translator, parent=None, pre_fetched: dict | None = None):
        super().__init__(parent)
        self.t = translator
        self.current_version = normalize(current_version)
        self.release: dict | None = None
        self.download: DownloadThread | None = None

        self._build()

        if pre_fetched:
            self._on_release(pre_fetched)
        else:
            self.fetch = GitHubFetchThread(self)
            self.fetch.result_signal.connect(self._on_release)
            self.fetch.error_signal.connect(self._on_error)
            self.fetch.start()

    def _build(self) -> None:
        self.setWindowTitle(self.t("upd_title"))
        self.setMinimumSize(620, 470)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(22, 20, 22, 18)
        layout.setSpacing(12)

        self.lbl_title = QLabel(self.t("upd_checking"))
        self.lbl_title.setProperty("role", "section")
        self.lbl_sub = QLabel(self.t("upd_installed", version=f"v{self.current_version}"))
        self.lbl_sub.setProperty("role", "muted")

        self.progress = QProgressBar()
        self.progress.setProperty("variant", "thin")
        self.progress.setRange(0, 0)
        self.progress.setTextVisible(False)

        self.changelog = QTextBrowser()
        self.changelog.setOpenExternalLinks(True)

        self.btn_later = action_button(self.t("btn_later"), "ghost")
        self.btn_action = action_button(self.t("btn_download_update"), "primary")
        self.btn_later.clicked.connect(self.reject)
        self.btn_action.clicked.connect(self._start_download)
        self.btn_action.setEnabled(False)

        buttons = QHBoxLayout()
        buttons.addStretch()
        buttons.addWidget(self.btn_later)
        buttons.addWidget(self.btn_action)

        layout.addWidget(self.lbl_title)
        layout.addWidget(self.lbl_sub)
        layout.addWidget(self.progress)
        layout.addWidget(self.changelog, 1)
        layout.addLayout(buttons)

    # -------------------------------------------------------------- estados
    def _on_release(self, data: dict) -> None:
        self.release = data
        self.progress.hide()

        latest = normalize(data.get("tag_name", ""))
        self.changelog.setMarkdown(data.get("body") or "")

        if is_newer(latest, self.current_version):
            self.lbl_title.setText(self.t("upd_available", version=f"v{latest}"))
            self.btn_action.setEnabled(True)
            return

        self.lbl_title.setText(self.t("upd_latest", version=f"v{latest}"))
        self.btn_action.setText(self.t("btn_close"))
        self.btn_action.setProperty("variant", "ghost")
        self.btn_action.setEnabled(True)
        try:
            self.btn_action.clicked.disconnect()
        except RuntimeError:
            pass
        self.btn_action.clicked.connect(self.accept)
        self.btn_later.hide()

    def _on_error(self, message: str) -> None:
        self.progress.hide()
        if message == "checksum":
            self.lbl_title.setText(self.t("upd_checksum_failed"))
        else:
            self.lbl_title.setText(self.t("upd_error"))
            self.changelog.setPlainText(message)
        self.btn_action.setEnabled(False)
        self.btn_later.setEnabled(True)

    # ------------------------------------------------------------ descarga
    def _start_download(self) -> None:
        if not self.release:
            return

        # No macOS o Gatekeeper rejeita um DMG substituído por baixo; abrir a
        # página da release é o caminho que não deixa o utilizador preso.
        if platform.system() == "Darwin":
            webbrowser.open(self.release.get("html_url", RELEASE_PAGE))
            self.accept()
            return

        url, extension = UpdaterService.get_asset_url(self.release)
        if not url:
            self.changelog.setPlainText(self.t("upd_no_asset"))
            return

        asset_name = url.rsplit("/", 1)[-1]
        checksum = UpdaterService.get_checksum(self.release, asset_name)

        self.btn_action.setEnabled(False)
        self.btn_later.setEnabled(False)
        self.progress.show()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.lbl_title.setText(self.t("upd_downloading"))

        destination = Path(tempfile.gettempdir()) / f"ZarManager_Update{extension}"
        self.download = DownloadThread(url, str(destination), checksum)
        self.download.progress_signal.connect(self.progress.setValue)
        self.download.error_signal.connect(self._on_error)
        self.download.finished_signal.connect(self._apply)
        self.download.start()

    def _apply(self, path: str) -> None:
        self.lbl_title.setText(self.t("upd_restart"))
        self.progress.setValue(100)
        UpdaterService.apply_update_and_restart(path)

    def reject(self) -> None:
        if self.download is not None and self.download.isRunning():
            self.download.cancel()
            self.download.wait(2000)
        super().reject()
