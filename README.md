# LeoSetter

<div align="center">
  <img src="assets/LeoSetter.png" alt="LeoSetter Logo" width="180"/>
  <br/>
  <strong>A beautiful, dark-themed desktop application for batch editing image metadata.</strong>
  <br/><br/>

  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
  ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat-square)
  ![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
</div>

---

## ✨ Features

- 🖼️ **Batch Metadata Editing** — Open a folder and edit EXIF/XMP metadata for all images at once
- 🏷️ **Field Support** — Title, Subject, Tags, Comments, Rating, Authors, Date Taken, Copyright, GPS and more
- 📋 **Templates** — Save and reapply metadata presets across multiple photo sessions
- 🗺️ **Map Picker** — Click anywhere on an interactive map to set GPS coordinates
- 💾 **Safe by Default** — Staged changes are previewed before writing; choose to overwrite in-place or not
- 🌙 **Dark Theme** — Beautiful glassmorphism-inspired dark UI with custom-themed dialog windows

## 📦 Installation

### Option 1: Windows Installer (Recommended)

> Download the latest `LeoSetterSetup.exe` from [Releases](https://github.com/AHJ32/LeoSetter/releases).

Run the installer and follow the setup wizard. It will:
- Install all Python dependencies automatically
- Optionally create a Desktop shortcut
- Optionally add LeoSetter to the Start Menu

No Python installation is required.

---

### Option 2: Run from Source

#### Prerequisites

- **Python 3.10 or newer**
- **exiftool** installed on your system

#### Windows Setup

1. Install [Python 3.10+](https://www.python.org/downloads/) (check "Add to PATH")
2. Install exiftool — download from [exiftool.org](https://exiftool.org/), rename `exiftool(-k).exe` → `exiftool.exe` and place it on your PATH
3. Clone the repository and install dependencies:

```powershell
git clone https://github.com/AHJ32/LeoSetter.git
cd LeoSetter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

#### Linux Setup (Debian / Ubuntu / Pop!_OS)

1. Install Python and exiftool via your package manager:

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip exiftool
```

2. Clone the repository and install dependencies:

```bash
git clone https://github.com/AHJ32/LeoSetter.git
cd LeoSetter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

> **Note for Linux:** The custom dark title bar uses a Windows DWM API call that is skipped on Linux. Dialogs fall back to the standard `overrideredirect` approach.

---

## 🚀 Usage

1. **Open a Folder** — Use the toolbar's *"Open Folder"* button to browse to a directory of images.
2. **Select an Image** — Click any filename in the sidebar to load its current metadata.
3. **Edit Fields** — Fill in the metadata form on the right (Title, Tags, GPS, etc.).
4. **Stage Changes** — Edited images are highlighted in the sidebar; changes are not written yet.
5. **Save** — Click *"Save Changes"* to write staged changes for all images to disk.

### Toolbar Quick Actions

| Button | Action |
|---|---|
| 📁 Open Folder | Browse for a folder of images |
| 📄 Set Filenames | Pre-fill Title, Subject, and Comments from each image's filename |
| 🏷️ Set Tags | Batch-assign the same tag(s) to all images |
| 🗺️ Pick from Map | Open an interactive map to pick GPS coordinates |
| 💾 Save Template | Save the current form as a reusable preset |
| 📋 Apply Template | Load a saved preset into the current form |
| ⚙️ Manage Templates | Delete or review saved templates |
| 💾 Save Changes | Write all staged metadata changes to disk |
| 🗑️ Clear All | Clear metadata from all images (with confirmation) |

---

## 🤝 Contributing

We welcome contributions of all kinds! Please read [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on:

- Reporting bugs
- Requesting features
- Submitting pull requests

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [GeoSetter](https://www.geosetter.de/en/) for inspiration
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for beautiful cross-platform UI components
- [tkintermapview](https://github.com/TomSchimansky/TkinterMapView) for the interactive map widget
- [ExifTool by Phil Harvey](https://exiftool.org/) for robust metadata read/write
