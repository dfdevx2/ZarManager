# ZarManager v2.0.1 - Hotfix & Flatpak Beautification

**ZarManager v2.0.1** is a hotfix and targeted polish update focused on improving the native Linux desktop experience. This release ensures that the experimental Flatpak bundle integrates seamlessly with system application menus and software centers.

### 🎨 Visual & Desktop Integration

* **App Store Metadata Injection (Hotfix):** Automatically generates AppStream metadata (`.metainfo.xml` with modern `<developer>` schema) and desktop entry (`.desktop`) files during the build process. ZarManager will now display its proper name, description, category, and author details in Linux software centers like KDE Discover and GNOME Software.
* **Native Flatpak Icon Support:** Added automatic conversion and scaling of the source icon into a high-resolution 512x512 format native to Linux desktops, ensuring clean presentation in system trays and application stores without sizing issues.

### 🛠️ Pipeline Enhancements

* **ImageMagick Integration:** The CI/CD GitHub Actions runner now natively utilizes ImageMagick to handle and convert graphical assets automatically during the build.

### 📦 Distribution 

Every release continues to generate **4 official binaries**:
1. `ZarManager-Windows.zip` (Portable Windows Build)
2. `ZarManager-Linux.zip` (Standard Linux Directory Build)
3. `ZarManager-Linux-x86_64.AppImage` (Universal Portable Linux Executable)
4. `ZarManager-Linux-x86_64.flatpak` (Experimental Flatpak Bundle - Full desktop integration!)