# Changelog - ZarManager

## [v1.2.0] - 2026-08-30 (Enterprise Refactor Update)

This update represents the most significant architectural restructuring of ZarManager to date. The primary focus was transitioning from a functional script to a production-ready (Enterprise-grade) application, ensuring fault tolerance, optimized native performance, evasion of antivirus false positives, and UI stability.

### Core Engine & I/O (core.py)
* **High-Performance Terminal Parsing (Regex):** The terminal reading engine for 7-Zip and extract-xiso was rewritten. The percentage capture regular expression (re) is now pre-compiled globally, eliminating CPU overhead on the Main Thread during intensive I/O operations.
* **Refresh Rate Limiter (10 FPS):** The progress update system now utilizes an asynchronous time buffer. The interface (app.py) is notified at a maximum interval of 0.1s, preventing process lockups ("Not Responding" state) and freeing up hardware resources during large-scale extractions.
* **Abstract Environment Resolution:** Implemented the _resolve_environment() function based on the pathlib library. The engine dynamically detects the execution context (Raw Python, Nuitka, or PyInstaller), mapping internal binaries and preventing directory resolution failures across macOS and Linux environments.
* **File Anomaly Tolerance (Code 1):** The 7-Zip engine was configured to treat Return Code 1 (Warning) as a success state. This allows for the uninterrupted processing of .rar files containing residual signatures, a standard occurrence in Xbox 360 Scene distributions.
* **Privilege Mitigation (UAC):** Implemented exception handling for OSError (WinError 740). In permission block scenarios, the system now returns a structured notification to the interface instead of presenting a critical technical failure to the user.
* **Safe File Operations:** The try/except blocks in deletion routines were replaced by the native Python C++ abstraction (unlink(missing_ok=True)), mitigating race conditions associated with temporary file locks by the operating system.

### UI Orchestration & Theming (app.py)
* **Data-Driven Architecture (Dictionaries):** The theme system was refactored to utilize QPalette-based data structures, eliminating the dependency on extensive conditional flows. The addition of new visual profiles is now managed exclusively through mapped dictionaries.
* **High-Performance Repainting:** The visual transition method now performs a global stylesheet clearance (app.setStyleSheet("")) followed by a recursive unpolish/polish cycle. This guarantees the prevention of visual anomalies and memory leaks associated with inactive theme artifacts.
* **Safe Shutdown Interception (Anti-Corruption):** The PySide6 closeEvent was reinforced with integrity checks (getattr). A forced interruption of the application now suspends and safely terminates active processes, preventing the structural corruption of ISO or ZAR files.

### DevOps, Packaging & CI/CD (build.yml)
* **Distribution Paradigm (Windows Portable):** The Onefile model was replaced by a portable directory structure (ZarManager-Portable). This adjustment aligns the application with Windows Defender security guidelines, mitigating heuristic malware classifications triggered by aggressive temporary extractions.
* **Automatic Privilege Elevation:** The Nuitka compiler was updated with the --windows-uac-admin flag. The executable requests administrative elevation upon startup, automatically delegating privileges to secondary engines (7z.exe and extract-xiso.exe) without requiring user intervention.
* **Cross-Platform Directory Sanitization:** The GitHub Actions pipeline now integrates strict cleanup routines (Remove-Item and rm -f) prior to compilation. This ensures that the final packages contain only the binaries corresponding to the target operating system.
* **Operational Documentation Integration:** The build process automatically generates and includes instruction manuals (LEIA-ME.txt and README_EN.txt) within the final package, outlining the operational guidelines for the portable structure.