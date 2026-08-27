# Changelog

All notable changes to ZarManager will be documented in this file.

## [1.1.0] - 2026-08-27

### Added
* **macOS Support:** First official release for Apple Silicon and Intel Macs via `.dmg` image bundle, featuring native macOS UI styling and ad-hoc digital signature.
* **First Boot Guide:** Implemented an interactive tutorial overlay that greets new users, explaining tabs, operations, and folder configurations to streamline onboarding.
* **Interactive Tooltips (Balloon Tips):** Added globally styled `QToolTip` explanations. Hovering over any button, tab, or option for 2 seconds now reveals a sleek, native-looking explanation panel.
* **Ko-fi Integration:** Added a direct support button in the "About" tab for users who wish to donate and support the project's continuous development.

### Changed
* **UI Design Standardization:** Refined the "Branco" (Light) theme across all operating systems. It now features soft grays and modern blue accents perfectly mimicking macOS aesthetic guidelines on Linux and Windows platforms.
* Enhanced UI theme engine to dynamically switch to native window rendering when running on Darwin systems, while strictly managing Custom `QPalette` colors globally.
* Improved English localization with a real-time log event tracker, ensuring dynamic text strings and list views (`No compatible files...`) correctly update when switching languages mid-session.
* Adjusted default worker threads count to 2, optimizing standard HDD workflows automatically and clamping maximum threads to available file count.