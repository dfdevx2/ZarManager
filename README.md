<p align="center">
  <img src="img/logo.png" alt="ZarManager Logo" width="250">
</p>

<p align="center">
  <a href="https://github.com/dfdevx2/ZarManager/releases"><img src="https://img.shields.io/github/v/release/dfdevx2/ZarManager?style=for-the-badge&color=2ecc71" alt="Release"></a>
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-blue?style=for-the-badge&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://doc.qt.io/qtforpython-6/"><img src="https://img.shields.io/badge/Qt-PySide6-41CD52?style=for-the-badge&logo=qt&logoColor=white" alt="Qt"></a>
  <a href="https://ko-fi.com/dfdx047"><img src="https://img.shields.io/badge/Ko--fi-Donate-29abe0?style=for-the-badge&logo=ko-fi" alt="Ko-fi"></a>
</p>

# ZarManager

ZarManager exists because a game backup collection is rarely in the format
you actually want it in. A folder ends up mixing `.zip`s, raw `.iso`s, split
Xbox 360 downloads and loose game folders — and turning that into something
consistent, playable and disk-space-reasonable normally means learning half a
dozen different command-line tools, each with its own flags and quirks.

ZarManager is a cross-platform desktop front-end for that whole job. Point it
at a folder, and it figures out what each file actually is by reading its
header (not trusting the extension), works out the shortest chain of steps to
get it into your target format, and runs the right engine for each step —
7-Zip, extract-xiso, ZArchive, chdman, DolphinTool, PkgTool.Core, or its own
built-in Xbox 360 container readers — in the background, with real progress,
pause and cancel. A whole library goes in one queue and comes out the other
side already organized, without babysitting eighteen terminal windows.

## 📸 Interface

<p align="center">
  <img src="img/print1.png" alt="ZarManager Interface 1" width="49%">
  <img src="img/print2.png" alt="ZarManager Interface 2" width="49%">
</p>
<p align="center">
  <img src="img/print3.png" alt="ZarManager Interface 3" width="49%">
  <img src="img/print4.png" alt="ZarManager Interface 4" width="49%">
</p>

## 🚀 Features

* **Format detection by magic bytes.** The pipeline reads the file header
  instead of trusting the extension — `.iso` alone cannot tell you whether a
  disc is Xbox, GameCube, Wii or PS2. After each step the result is
  re-identified, which is what lets `zip → iso → archive` chain by itself.
* **Modular pipeline.** Each engine is a *stage* declaring what it consumes
  and what it produces; a planner finds the shortest route to the target
  format. Adding an engine is adding one file.
* **Native readers for Xbox 360 containers.** STFS packages (XBLA, DLC, title
  updates) and Games on Demand/SVOD images are parsed in pure Python — no
  binary to install, nothing an antivirus can quarantine.
* **Transactional batches.** Everything intermediate is written to a hidden
  work folder inside the destination. Originals are deleted only once the
  final artifact is in place — a late failure costs you nothing.
* **Real cancel and pause.** Cancelling interrupts the running engine instead
  of waiting for it; pausing suspends the process itself on Linux and macOS.
* **Parallel batches** with a shared queue and collision handling
  (skip, replace, auto-rename) that is safe across workers.
* **Four themes** (Pitch Black, White, Steam, Xbox), English and PT-BR,
  subtle UI sound effects, and a *reduce motion* switch.
* **Troubleshooting built in.** Help → Check engines shows exactly which
  binary is present, where it was found, and its version — before you queue a
  job that would otherwise fail halfway through.

## 🧭 Supported chains

| Input | Detected as | Result |
|---|---|---|
| `.zip` `.rar` `.7z` | archive | extracted, then re-identified and chained |
| Xbox / Xbox 360 `.iso` | XDVDFS | extracted, then compressed to `.zar` |
| XBLA title, DLC, title update | STFS package | extracted natively, then compressed to `.zar` |
| Games on Demand (`data0000`, …) | GOD / SVOD | image rebuilt natively, extracted, then `.zar` |
| Game folder | game folder | `.zar` |
| GameCube / Wii `.iso` | GC / Wii | `.rvz` (via `DolphinTool`) |
| PS1 / PS2 `.iso`, `.cue` / `.gdi` | ISO9660 / CD | `.chd` (via `chdman`) |
| PS3 / PS4 `.pkg` | package | extracted, then `.zar` (via `PkgTool.Core`) |

Every engine above ships inside `bin/` for Windows, Linux and macOS — nothing
to download or configure separately. Xbox 360 containers (STFS and GOD/SVOD)
need no binary at all, since they're read directly by ZarManager itself.

Two caveats worth knowing, both detailed in
[`docs/ARCHITECTURE.md`](docs/ARCHITECTURE.md). **Games on Demand** support
has not yet been confirmed against a retail package: the reader picks its
geometry by validating against the disc signature and refuses to write an
image when nothing validates, so it fails loudly rather than quietly producing
garbage — but a real package is what would settle it. **PKG** only handles
fPKG/debug packages; a retail PS4 package is encrypted and out of scope for
any current open-source tool. shadPS4 itself reads `.zar` natively as of
0.17.0, so `PKG → folder → .zar` has a real destination once you have an
fPKG to feed it.

## 📦 Install

* **Windows** — download `ZarManager-vX.Y.Z-Windows.zip` and unzip it
  anywhere. It is a **portable folder**: `ZarManager.exe` and the `bin` folder
  must stay together. If your antivirus removes anything from `bin`, exclude
  the whole folder.
* **Linux** — download the `.AppImage`, `chmod +x` it, run it. Needs FUSE.
  > ⚠️ **Known issue:** UI sound effects don't play on at least some Linux
  > builds — the interface stays fully functional, just silent. This is
  > being tracked; see the [1.3.0 changelog entry](CHANGELOG.md) for what's
  > already been ruled out.
* **macOS** — download the `.dmg`. Gatekeeper flags unsigned binaries; clear
  the quarantine with `xattr -cr /Applications/ZarManager.app`.

Settings live in your user config directory (`%APPDATA%`, `~/.config`,
`~/Library/Application Support`). Put an empty `portable.txt` next to the
executable to keep them in the program folder instead.

## 🛠️ Engines and credits

ZarManager is a workflow wrapper around open-source archival engines. Each is
a separate program with its own license, bundled as-is:

* **[extract-xiso](https://github.com/XboxDev/extract-xiso)** — Xbox XDVDFS
  images, by *XboxDev*. BSD-3-Clause.
* **[ZArchive](https://github.com/Exzap/ZArchive)** — the seekable
  zstd-compressed `.zar` format, by *Exzap* (Cemu). MIT.
* **[7-Zip](https://www.7-zip.org/)** — archive extraction. LGPL-2.1, with the
  unRAR restriction.
* **[chdman](https://www.mamedev.org/)** (MAME) — CHD compression for CD/DVD
  formats (PS1, PS2, Dreamcast, and others MAME supports). GPL-2.0-or-later.
* **[DolphinTool](https://dolphin-emu.org/)** — RVZ compression for GameCube
  and Wii images, from the Dolphin project. GPL-2.0-or-later.
* **[PkgTool.Core](https://github.com/maxton/LibOrbisPkg)** (LibOrbisPkg) —
  PS3/PS4 `.pkg` extraction, by *maxton*. LGPL-3.0.
* **[PySide6](https://doc.qt.io/qtforpython-6/)** — the Qt interface.

STFS and GOD/SVOD (Xbox 360) support has no external engine — it's read
directly by ZarManager's own code.

## 🧑‍💻 Development

```bash
git clone https://github.com/dfdevx2/ZarManager.git
cd ZarManager
pip install -r requirements.txt
python app.py
```

Tests need neither Qt nor a display — the core has no Qt dependency at all,
and the UI is exercised against a stub in `tests/qt_stub`:

```bash
python tests/test_pipeline.py    # pipeline end-to-end, with fake engines
python tests/test_ui_smoke.py    # imports, screen construction, locale keys
```

Regenerate the interface sounds with `python tools/make_sfx.py`.

## 📜 License

ZarManager is released under a **non-commercial license** — use, copy and
modify freely for non-commercial purposes; selling it or any derived product
is prohibited. See [`LICENSE`](LICENSE) for the exact terms.

> Earlier versions of this README claimed MIT. That was never what `LICENSE`
> said; the non-commercial terms are the ones that apply.

The bundled engines keep their own licenses, listed above and in the About
screen.

> 🤖 **AI-assisted development:** concurrency, Qt thread synchronisation,
> error handling and the Nuitka packaging pipeline were debugged, refined and
> documented with the assistance of AI.
