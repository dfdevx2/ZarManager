# Changelog
All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.3.0] - 2026-09-22

### Added
- **Xbox 360 containers.** XBLA titles, DLC and title updates (STFS: `CON `/`LIVE`/`PIRS`) are read and extracted natively, in pure Python — no extra binary to ship, nothing an antivirus can delete. These files carry no extension, so they never even appeared in the file list before; they are now detected by their header.
- **Games on Demand (GOD/SVOD).** The split `data0000`, `data0001`, … files are reassembled into the XDVDFS image, which is then handed to `extract-xiso` — so `god → xiso → folder → .zar` builds itself with no code tying those steps together. The on-disk geometry is chosen by trying the documented variants and keeping the one the disc signature validates; if none validates, the job fails instead of writing a broken image. **Still unverified against a retail package.**
- **Native stages** (`NativeStage`): a stage can now run in-process instead of launching an engine, and keep the same progress throttling, pause and cancellation. Troubleshooting shows these as built in rather than hunting for a binary.
- A container that is named after its content ID (`8A1B2C3D`) is delivered under the game's own name, read from inside the package. A file the user already named keeps its name.
- **RVZ, CHD and PKG are now real, bundled engines**, not a roadmap entry that only worked if the binary happened to be on `PATH`. `bin/` ships `chdman` (MAME), `DolphinTool`, and `PkgTool.Core` (LibOrbisPkg) for Windows, Linux and macOS. Since they now genuinely ship, a missing one is treated the same as a missing 7-Zip or extract-xiso — a hard stop for the affected job, not a silent skip.
- Format detection by magic bytes (Xbox XDVDFS, GameCube, Wii, ISO9660, CD sheets, PS3/PS4 packages, CHD, RVZ) with re-identification after each step.
- Modular pipeline: stages register themselves and a planner finds the shortest route to the target format.
- Real pause: the running process is suspended (SIGSTOP) on Linux and macOS.
- Floating pill navigation with bounce physics, glow and a sliding indicator; keyboard and gamepad navigation; a "reduce motion" setting.
- UI sound effects via `QSoundEffect`, with volume control and an off switch.
- Redesigned welcome (three steps, themes previewed as cards), troubleshooting (engine check, copy diagnostics, open logs) and about screens.
- Per-item status, detected format and progress in the file list.
- Tests: 16 end-to-end pipeline tests with fake engines, plus UI smoke tests that run without Qt installed.

### Fixed
- **Batch results were reported wrong.** The UI called `get_completion_stats()` and `is_cancelled()` through `hasattr`; neither existed on the core, so the fallback always reported `failed=0`. Batches with failures — or cancelled ones — announced "finished without errors" and played the success sound.
- **The antivirus alert was dead code.** `AV_BLOCK` was re-raised inside the pipeline but swallowed by the `except Exception` in `start_processing`, so `av_alert_signal` never fired. A missing engine now propagates to the UI.
- **`verify_environment()` returned a bool** while the UI expected `(bool, list)`, so the error dialog always said "unknown files" instead of naming the missing engine.
- **`7z e` flattened directory structures**, corrupting any archive that contained a game folder rather than an ISO. It is now `7z x`.
- **Originals were deleted too early.** The `.zip` was removed right after extraction; if compression failed afterwards, the user lost the original and got no result. Deletion is now transactional.
- **The destination folder appeared as an input item** when it lived inside the source folder — which is exactly what the shipped `settings.json` did. Work folders, the destination itself and `.zar`/`.chd`/`.rvz` outputs are now excluded from listings.
- **Race in collision handling:** two workers could rename to the same `_1`. Names are now reserved atomically.
- **Nuitka builds were treated as interpreted.** Nuitka sets `__compiled__`, not `sys.frozen`. Settings were written next to the binary — a read-only mount inside an AppImage — and lost on every launch, and the in-place Windows updater never actually ran.
- **The AppImage updater replaced the wrong file** (`sys.argv[0]`, the binary mounted under `/tmp/.mount_*`, rather than `$APPIMAGE`).
- **TLS verification was disabled** in the update check and download. Combined with `--windows-uac-admin`, that let a network attacker deliver an executable running as administrator. Verification is on, certifi is bundled, and a published `SHA256SUMS` is validated before an update is applied.
- **Version comparison was string-based:** `"1.10.0" > "1.9.0"` evaluated to `False`, so updates would have stopped being detected after 1.9.
- **Cancelling could hang** on a blocking `stdout.read(1)` when an engine produced no output. Reading now happens on a dedicated thread.
- Log output had no file handler, so GUI builds (which have no console) recorded nothing. There is now a rotating log file.
- **Checkboxes didn't repaint after a bulk selection change.** Loading a folder or clicking *Invert selection* updated the counter and the underlying state correctly, but the checkbox squares kept showing the old state until the user clicked one by hand. The batch path set each item's state with the list's signals blocked (to avoid re-running the counter once per item), and the redraw that followed wasn't reliably forcing Qt to repaint every visible row. Population and bulk toggles now explicitly re-emit the model's `dataChanged` for the whole range before repainting — the same signal Qt's own view machinery relies on, so it no longer depends on an assumption about what `blockSignals` does or doesn't suppress internally.
- **The pill navigation had a rectangle around it and a dashed focus outline** that weren't part of the intended look. The rectangle came from a leftover border/background on the `PillNav` frame in the stylesheet; the dashed outline was an explicit focus-ring paint that fired on every click, since clicking a pill also gives it keyboard focus. Both are gone — the hover glow, lift and sliding indicator are untouched.
- **Sound effect diagnostics.** `QSoundEffect` loads asynchronously and fails silently when the platform has no working audio backend — `play()` was a silent no-op with nothing in the log to explain why. The manager now logs, at startup, which QtMultimedia plugins Qt actually found (or the fact that it found none), and logs per-effect load failures via `statusChanged`. **Known issue, still open on Linux:** even after this diagnostic pass, sound has been confirmed still not working on at least one Linux build. A system package like `qt6-multimedia-ffmpeg` has **no effect** on this — a Nuitka build is self-contained and only ever loads the QtMultimedia plugins that shipped inside the PySide6 wheel, never the system's Qt. The likely cause is that Nuitka's generic dependency scan doesn't reliably pull in the ffmpeg backend plugin (`libffmpegmediaplugin`) or its own shared-library dependencies, since Nuitka has no special-cased handling for QtMultimedia. The Linux CI job now greps the build output for the plugin and runs `ldd` on it, surfacing missing dependencies as a build warning instead of only being discoverable after a user reports silence.

### Changed
- Four independent tabs, each with its own thread and directories, became one shared workspace with a single queue — four jobs could previously run over the same folder at once.
- Themes are generated from a single token set instead of palettes duplicated across `app.py` and `theme_mac.py`.
- The core emits translation keys instead of formatted strings; the `msg.replace(...)` translation block is gone, and worker threads no longer touch QWidgets.
- CI derives the version from the tag instead of repeating it in ten places, runs the test suite before building, and publishes checksums.
- The macOS CI job now also strips the Linux-named copies of `chdman`, `dolphin-tool` and `PkgTool.Core` from the `.dmg` (they'd otherwise ship uselessly alongside the correct `-mac` binaries).
- Documentation and in-app text now describe the portable-folder distribution instead of the old single-executable-into-%TEMP% model.
- README stated MIT while `LICENSE` has always been non-commercial; the README now matches the license. The `.zar` format is credited to Exzap (ZArchive), not to "vasi".
- The PKG note was out of date: shadPS4 reads `.zar` natively as of 0.17.0, so `PKG → folder → .zar` has a real destination, and `PkgTool.Core` (LibOrbisPkg) is now the bundled engine for it. Retail PS4 packages are still encrypted and out of scope — `PkgTool.Core` only handles fPKG/debug packages.

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
