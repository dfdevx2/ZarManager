# Changelog

All notable changes to ZarManager will be documented in this file.

## [1.1.0] - 2026-08-27

### Added
* **macOS Support:** First official release for Apple Silicon and Intel Macs via `.dmg` image bundle, featuring native macOS UI styling and ad-hoc digital signature.
* **Ko-fi Integration:** Added a direct support button in the "About" tab for users who wish to donate and support the project's continuous development.

### Changed
* Enhanced UI theme engine to dynamically switch to native `macOS` window rendering when running on Darwin systems, bypassing the standard `Fusion` style.
* Rebuilt the "Branco" (Light) theme with softer grays and modern blue accents to prevent system-forced dark palette clashes.
* Adjusted default worker threads count to 2, optimizing standard HDD workflows automatically and clamping maximum threads to available file count.
* Fixed real-time engine status string localization ("Extracting", "Compressing") in the console.

## [1.0.0] - 2026-08-25

### Added
* **Pure PySide6 Architecture:** Full removal of legacy dependencies like Flet, achieving optimal performance, reduced memory consumption, and rock-stable background multi-threading via `QThread`.
* **Linux AppImage Support:** Added universal `.AppImage` bundle distribution featuring built-in desktop icon integration (`img/icon.png`) and standard desktop entry metadata.
* **Advanced Windows Build & Code Signing:** Embedded official application icon (`img/icon.ico`), clean enterprise product metadata, and automated self-signed digital code signing to mitigate heuristic security flags.
* **Synchronized Versioning:** Unified version control system linking the main application window and the "About" tab dynamically.
* **Update Verification Timeout:** Implemented built-in timeout handling and feedback messages for the update check button to prevent infinite loading states.
* **Repository Branding:** Integrated official asset icons and branding resources directly into the repository structure.

### Changed
* Refactored core worker pipelines and batch compression queues for improved stability and real-time logging.

### Acknowledgments
* **AI-Assisted Debugging:** Codebase concurrency management, thread synchronization, and error handling were rigorously debugged and optimized with the assistance of Artificial Intelligence.