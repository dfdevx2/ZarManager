# Changelog - ZarManager

## [v1.0.0] - 2026-08-24

### Statement to the Community
To ZarManager users: I acknowledge that previous versions (0.x) presented severe instabilities, including interface freezes, rendering failures on Linux environments (Wayland), and unhandled concurrency errors. I apologize for the unsatisfactory technical experience. Version 1.0.0 represents a complete architectural rewrite, replacing experimental frameworks with industry standards to ensure absolute stability and performance.

### Architecture and Engineering
* **Migration to Qt/PySide6:** The graphical interface was completely rewritten using PySide6, ensuring native stability on Linux, Windows, and macOS.
* **Process Isolation (QThread):** The compression and extraction engine (`core.py`) has been isolated into strict asynchronous threads. The graphical interface will no longer freeze under any I/O processing load.
* **Separation of Concerns (SOLID):** The monolithic code was decoupled into Service components (`FileService`, `SoundService`, `UpdateService`), Data Models, and UI Controllers.
* **Strict Error Handling:** Implemented rigorous exception catching for permission issues, file system failures, and environment errors, preventing the application from crashing silently.

### User Interface (UI/UX)
* **Dynamic Translation Engine:** The interface now supports real-time language switching (PT-BR / EN) without needing to restart the application. Hardcoded texts have been entirely removed.
* **Integrated Native Themes:** Implemented native Qt color palettes, including optimized dark themes (AMOLED, Steam, Xbox) with calculated contrast to prevent visual fatigue.
* **System Modal Dialogs:** Replaced simulated pop-ups with native operating system modal dialog boxes, ensuring predictable behavior during directory navigation and alerts.
* **Optimized Console Reports:** The operation log in the interface now uses frequency limitation (throttling) and a buffer limit, saving CPU and RAM cycles during massive operations.

### Core Features
* **Safe Overwrite Policy:** Added the capability for prior and safe deletion of destination files/folders when the user chooses to overwrite data in case of a collision.
* **Rigorous State Management:** The processing lifecycle now obeys a strict finite state machine (IDLE, RUNNING, PAUSED, CANCELLING, COMPLETED, PARTIAL, FAILED).
* **Asynchronous Auditory Feedback:** Success and failure sound signals now use native fallbacks for each operating system without interrupting the main thread.