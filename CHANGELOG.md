# Changelog

All notable changes to ZarManager will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.0] - 2026-08-27

### Added
* **Initial macOS Support:** Introduced full support for Apple Silicon and Intel hardware architectures. The release pipeline now generates a native `.dmg` application bundle.
* **Native macOS Styling:** Engineered the UI engine to dynamically detect Darwin systems and enforce the native Apple rendering style, bypassing standard Fusion mechanics to respect local ecosystem aesthetics.
* **Proactive Environment Verification:** Implemented an intelligent pre-flight environment scan within `core.py`. The engine now verifies the presence and integrity of all embedded background binaries (`7z`, `extract-xiso`, `zarchive`) before initializing the processing queue.
* **OS-Specific Troubleshooting Dialogues:** Added a system-aware error handling protocol. If required binaries are missing, the application identifies the host OS and triggers a tailored diagnostic dialogue. This explicitly guides users to resolve Antivirus false positives (Windows), Gatekeeper quarantine flags (macOS), or missing FUSE/execution permissions (Linux).
* **First-Boot Interactive Guide:** Deployed a streamlined onboarding overlay for new users. This executes automatically on the first software launch, providing a structured overview of operation modes, directory configurations, and essential security warnings regarding runtime extractions.
* **Dynamic Hover Tooltips:** Integrated globally styled `QToolTip` components across the entire interface. Maintaining the cursor over operational elements for a designated threshold invokes detailed, localized functional descriptions.
* **Creator Support Integration:** Established a direct funding channel by adding a dedicated Ko-fi button within the "About" interface, redirecting users to the official developer support page.
* **Build System Optimization:** Upgraded the GitHub Actions CI/CD pipeline by implementing robust Nuitka caching protocols (`actions/cache@v4`), significantly accelerating compilation times. Also integrated dynamic `.icns` file generation using native macOS `sips` commands during the build phase.

### Changed
* **UI Palette Standardization:** Deeply refined the custom visual themes ("Branco", "Preto", "Steam", and "Xbox"). The color matrix was recalibrated to utilize softer accents, deeper contrast ratios, and modern UI guidelines across all operating systems.
* **Smart Thread Clamping:** Overhauled the multi-threading logic within the core engine. The `ThreadPoolExecutor` now dynamically calculates and restricts the active worker count to match the exact number of files in the processing queue, effectively eliminating ghost threads and unnecessary CPU/Disk I/O overhead.
* **Default Worker Threshold:** Adjusted the default concurrent worker count from 4 to 2 to optimize standard mechanical Hard Disk Drive (HDD) workflows and prevent severe disk bottlenecking during intensive batch extractions.
* **Real-Time Localization Engine:** Upgraded the internal translation handler. Dynamic UI elements, such as combo boxes and real-time processing status logs ("Extracting", "Compressing"), now respond instantly to language state changes without requiring an application restart.

### Fixed
* **Linux Rendering Overlap:** Resolved a critical UI bug exclusive to Linux environments where switching themes caused severe color overlapping and illegible typography. Fixed by enforcing a strict `standardPalette()` override prior to injecting customized color matrices into the `QApplication` instance.
* **Runtime Execution Permissions:** Implemented an explicit `os.chmod(0o755)` directive for UNIX-based systems (macOS/Linux) prior to invoking internal binaries, successfully preventing "Permission Denied" crashes when running from locked AppImage or DMG mounts.
* **Translation Fallbacks:** Fixed missing dictionary keys in the `locales.py` registry that forced the system into Portuguese fallbacks regardless of the selected user language.

## [1.0.0] - 2026-08-25

### Added
* **Pure PySide6 Architecture:** Concluded full deprecation of legacy frameworks (Flet). Rebuilt the entire graphical interface and concurrency management using Qt for Python (PySide6), achieving optimal performance, reduced memory consumption, and rock-stable background multi-threading via `QThread`.
* **Linux AppImage Distribution:** Engineered a universal `.AppImage` bundle distribution featuring built-in desktop icon integration (`img/icon.png`) and standard desktop entry metadata.
* **Advanced Windows Build & Code Signing:** Implemented embedded official application icons (`img/icon.ico`), clean enterprise product metadata, and automated ad-hoc digital code signing (Self-Signed Certificates) to mitigate aggressive heuristic security flags.
* **Update Verification Architecture:** Built a synchronous version control system featuring timeout handling to cross-reference the local build with the main GitHub repository release tags.
* **Repository Branding Asset Structure:** Integrated official vector and raster asset icons directly into the root repository structure for automated CI/CD fetching.

### Changed
* Refactored core worker pipelines and batch compression queues for improved operational stability and granular real-time terminal logging.

### Acknowledgments
* **AI-Assisted Debugging:** Codebase concurrency management, PySide6 thread synchronization limits, and cross-platform Nuitka packaging logic were rigorously debugged and optimized with the assistance of Artificial Intelligence tools.