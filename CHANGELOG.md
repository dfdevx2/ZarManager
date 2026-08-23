# ZarManager v1.3.5 - The Flatpak & UI Safety Update

**ZarManager v1.3.5** focuses on giving users more control over their disk space, fixing minor UI localization bugs, and taking a massive step forward in Linux distribution by introducing experimental Flatpak support.

### 🚀 New Features & Enhancements

* **Pre-Operation Safety Prompt:** Added a native dialog box that appears right before a batch process begins. Users can now explicitly choose whether to **Keep** or **Delete** the original source files (ISOs, ZIPs, or extracted folders) after a successful operation, giving you total control over disk space management.
* **Experimental Flatpak Support:** The CI/CD pipeline now automatically compiles and bundles ZarManager into a standalone `.flatpak` package using the Freedesktop SDK. This provides an alternative, highly sandboxed installation method for Linux users (especially on Arch/CachyOS) who wish to bypass `fuse2` AppImage requirements.
* **Dynamic Translation Engine:** The "Performance Warning" message in the Settings tab (regarding CPU threads and I/O bottlenecks) is now fully integrated into the localization engine and will update dynamically when switching between English and Portuguese.

### 🛠️ Bug Fixes

* **Phantom Update Loop Fixed:** Resolved an issue where the internal version tracker was outdated, causing the background auto-updater to falsely prompt users to download a new release on startup even if they were on the latest version.
* **Core Execution Cleanup:** Safely bypassed the `os.remove()` and `shutil.rmtree()` commands deep within the core processing loop whenever the user elects to keep original files, preventing accidental data loss on large libraries.

### 📦 Distribution 

Every release now generates **4 official binaries**:
1. `ZarManager-Windows.zip` (Portable Windows Build)
2. `ZarManager-Linux.zip` (Standard Linux Directory Build)
3. `ZarManager-Linux-x86_64.AppImage` (Universal Portable Linux Executable)
4. `ZarManager-Linux-x86_64.flatpak` (Experimental Flatpak Bundle)