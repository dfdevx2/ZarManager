# ZarManager v1.3.3 - The Robust Preservation & Multi-Build Update

We are proud to release **ZarManager v1.3.3**, a massive milestone focused on universal cross-platform compatibility, file-system safety, and deep pipeline stability.

### 🚀 Major Features & Core Improvements

* **Universal 7-Zip Pipeline (`.zip`, `.rar`, `.7z`):** Automatically detects compressed ROM archives, applies "flat" extraction logic (`7z e`) to bypass nested subdirectories, extracts the core `.iso` or files, and safely cleans up temporary elements.
* **Collision Detection Engine:** Intelligent safeguards built into every batch mode. If a destination `.zar` file or extracted folder already exists, ZarManager prompts you to **Overwrite**, **Skip**, or **Cancel**, protecting your existing library.
* **Background Silent Auto-Updater:** Checks for new GitHub releases asynchronously on startup without freezing the UI. A clean notification prompt appears if an update is found (can be completely toggled off in the *About* tab).
* **Cross-Platform Audio Feedback:** Integrated auditory notifications (system beeps/chimes) upon successful batch completions or critical pipeline errors, allowing you to run heavy queues unattended.

### ⚡ UI Overhaul & Performance

* **C-Native Treeview Rendering (Zero Lag):** Replaced legacy listboxes with a high-performance `Treeview`. Capable of rendering thousands of items instantly with custom row-height spacing and smooth scrolling.
* **New "AMOLED Purple" Theme:** Replaced standard dark mode with an absolute pure-black (`#000000`) background accented by vibrant purple highlights, tailored for OLED screens and modern aesthetics.
* **Linux Window State Fix:** Resolved the Wayland/X11 initial render collapse bug using an automated geometry-refresh protocol on startup.

### 🐧 Linux & AppImage Fixes (v1.3.3)

* **Read-Only File System Fix:** Fixed a critical crash on AppImages where the internal configuration (`settings.json`) attempted to write inside the read-only mounted path (`/tmp/...`). Configurations are now dynamically routed to the user's secure profile directory (`~/.config/zarmanager/settings.json`), keeping the application fully compliant with strict sandbox environments.
* **Multi-Format Distribution:** Every release now automatically generates and publishes **3 distinct binaries**:
  1. `ZarManager-Windows.zip` (Portable Windows Build)
  2. `ZarManager-Linux.zip` (Standard Linux Directory Build)
  3. `ZarManager-Linux-x86_64.AppImage` (Universal Portable Linux Executable)

### 🛠️ Dedicated Workflow Tabs

1. **Automated Pipeline (Full):** Drag-and-drop any combination of archives, ISOs, or folders. Automatically decompresses, extracts XISO, compresses to `.zar`, and cleans up.
2. **Extract Archives Only:** Isated tool for unpacking `.zip`, `.rar`, or `.7z` archives flatly.
3. **Extract ISO Only:** Unpacks raw XDVDFS structures from standard Xbox 360 `.iso` images.
4. **Compress Only:** Compresses structured game directories directly into high-efficiency `.zar` files.