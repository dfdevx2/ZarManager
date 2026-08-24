# ZarManager

ZarManager is a cross-platform graphical tool designed to automate XISO extraction and batch compression into `.zar` archives.

## Key Features

* **Automated Pipeline:** Reads directories, identifies `.zip`, `.rar`, `.7z`, and `.iso` files, runs cascading extractions, and compresses the final output autonomously.
* **Multi-Threaded Performance:** Flexible worker configuration for concurrent extraction and compression adapted to your hardware, maximizing disk utilization.
* **Native Stability:** Built with **PySide6 (Qt)** featuring strict asynchronous background execution (`QThread`), ensuring absolute fluidity across Windows, Linux (X11/Wayland), and macOS.
* **Dynamic Interface:** Real-time support for multiple visual themes (AMOLED, Steam, Xbox, Light) and languages (PT-BR, EN) without restarting.
* **Data Safety:** Automatic handling of file collisions with granular options for overwriting and preserving source files.

## System Requirements

* Python 3.10 or higher
* PySide6 (>= 6.5.0)

## Installation (Development Environment)

Clone the repository and set up the environment:

```bash
git clone [https://github.com/dfdevx2/ZarManager.git](https://github.com/dfdevx2/ZarManager.git)
cd ZarManager
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Run the application:
```bash
python app.py
```

## Compilation (Binaries)

The project uses Nuitka to compile standalone native binaries. To compile the application on your operating system, run:

```bash
python -m nuitka --onefile --enable-plugin=pyside6 --output-dir=dist app.py
```
The final executable will be available in the `dist/` directory.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.
