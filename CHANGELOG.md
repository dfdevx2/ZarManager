# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.2.0] - 2026-08-30

### Added
- **Smart In-Place Updater:** Integrated a native, asynchronous update engine for the ZarManager project. On Windows and Linux, the application queries the GitHub API, downloads the latest release to a temporary folder, generates an OS-specific injection script, and safely self-restarts into the new version.
- **Automatic Startup Notifications:** Implemented a silent background thread that checks for updates on application boot, automatically triggering an interactive changelog dialog if a newer version is detected.
- **Advanced File Collision Handling:** Added a global collision policy engine. When extraction or compression engines detect duplicate files or intermediate folders in the target directory, users are now prompted to Overwrite, Skip Existing, or Auto-Rename files dynamically.
- **Surgical Security Interception (Windows):** Implemented a pre-flight deep scan milliseconds before shell command execution. If Windows Defender or another Antivirus silently deletes a background engine, the application safely halts processing threads, aborts the queue, and presents a dedicated tutorial on how to whitelist the tool.
- **Bilingual Localization Expansion:** Added comprehensive English and Portuguese translations for all new collision dialogs, update sequences, and security alerts.

### Changed
- **macOS Browser Fallback for Updates:** macOS Gatekeeper blocks in-place executable modifications. The updater on macOS now securely redirects the user to the default browser to download the latest `.dmg` release manually.
- **Windows Build & Update Architecture:** Transitioned the Windows build pipeline from a single-file executable to a folder-based distribution compressed into a `.zip` archive. Consequently, the internal updater now utilizes native PowerShell commands (`Expand-Archive` and `xcopy`) to unpack the `.zip` and seamlessly merge the updated files over the existing directory.

### Fixed
- **macOS / UNIX Extraction Failures:** Resolved fatal "File exists" and directory creation conflicts during XDVDFS extraction by restructuring `extract-xiso` command arguments to respect strict UNIX file system constraints.
- **Update Dialog Missing Module:** Fixed a `ModuleNotFoundError` during manual update checks by properly structuring the `ui.update_dialog` import path and adding an exception fallback to notify the user if the UI component is misplaced.