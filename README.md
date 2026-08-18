<div align="center">
  <img src="img/logo.png" alt="ZarManager Logo" width="200"/>
  <h1>ZarManager</h1>
  <p>A powerful GUI tool to extract XISO files and compress them into ZAR format.</p>
</div>

---

## 📌 About The Project

**ZarManager** was developed to automate and simplify the process of extracting Xbox 360 ISO files (XDVDFS) and subsequently compressing the extracted files into the `.zar` format. 

Initially designed with Linux in mind, it has evolved into a cross-platform application (Windows and Linux) capable of running smoothly even through compatibility layers like Winlator on Android.

### 🎯 Purpose
Managing and converting large ISO files can be tedious when using command-line tools manually. ZarManager provides a clean, user-friendly interface to batch process these files efficiently, utilizing multi-threading to speed up the workflow while keeping the UI responsive.

## 🚀 Features

*   **Batch Processing:** Select multiple files or directories to process at once.
*   **Full Pipeline (Auto Mode):** Automatically extracts an ISO and immediately compresses its contents into a `.zar` file, cleaning up temporary files afterwards.
*   **Isolated Modes:** Choose to only extract an ISO or only compress a directory.
*   **Real-time Progress:** Accurate, fluid progress bars and item counters.
*   **Cross-Platform:** Works natively on Windows and Linux.
*   **Winlator Compatible:** Specifically optimized to run without UI freezes when emulated on Android via Winlator.

## 🛠️ Built With

*   [Python](https://www.python.org/)
*   [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) - For the modern GUI.
*   [extract-xiso](https://github.com/XboxDev/extract-xiso) - For ISO extraction.
*   [zarchive](https://github.com/vasi/zarchive) - For ZAR compression.

*Disclaimer: AI tools were used during the development of this project to assist with code structuring, logic optimization, and code review.*

## 📥 Installation (Pre-compiled Binaries)

You don't need to install Python to use ZarManager. You can download the ready-to-use binaries from the **[Releases](../../releases)** page.

1. Go to the Releases page.
2. Download `ZarManager-Windows.zip` or `ZarManager-Linux.zip`.
3. Extract the folder.
4. Run the executable (`ZarManager.exe` on Windows or `ZarManager` on Linux).

## 💻 Building from Source

If you prefer to run from the source code or build it yourself:

### Prerequisites
*   Python 3.10+
*   The `bin` folder containing the required executables (`extract-xiso`, `zarchive` for Linux; `extract-xiso.exe`, `zarchive.exe` for Windows).

### Setup

1.  Clone the repository:
    ```bash
    git clone [https://github.com/YOUR_USERNAME/ZarManager.git](https://github.com/YOUR_USERNAME/ZarManager.git)
    cd ZarManager
    ```

2.  Install the required Python packages:
    ```bash
    pip install -r requirements.txt
    ```

3.  Run the application:
    ```bash
    python app.py
    ```

### Building the Executable

You can build the executable yourself using PyInstaller.

```bash
pip install pyinstaller
pyinstaller --noconfirm --onedir --windowed --name "ZarManager" app.py
cp -r bin dist/ZarManager/  # On Windows, use: xcopy /E /I /Y bin dist\ZarManager\bin

📜 License

This project is free to use. However, commercial use and reselling are strictly prohibited. See the LICENSE file for more details.