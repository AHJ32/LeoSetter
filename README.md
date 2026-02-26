<div align="center">
  <img src="assets/LeoSetter.png" alt="LeoSetter Logo" width="180"/>
  <br/>
  <h1>LeoSetter</h1>
  <strong>A beautiful, dark-themed desktop app for batch editing image metadata.</strong>
  <br/><br/>

  ![Python](https://img.shields.io/badge/Python-3.10%2B-blue?style=flat-square&logo=python)
  ![Platform](https://img.shields.io/badge/Platform-Windows%20%7C%20Linux-lightgrey?style=flat-square)
  ![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)
  ![Release](https://img.shields.io/github/v/release/AHJ32/LeoSetter?style=flat-square&color=coral)
</div>

---

## What is LeoSetter?

LeoSetter is a free, open-source desktop application that lets you view and batch-edit EXIF/XMP metadata for entire folders of images — all from a clean, dark-themed UI. Whether you're a photographer tagging a shoot, or a developer embedding GPS coordinates into test images, LeoSetter makes it fast and safe.

It is powered by [ExifTool](https://exiftool.org/) under the hood and uses [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the interface.

---

## ✨ Features

- 🖼️ **Batch Metadata Editing** — Open a folder and edit EXIF/XMP metadata for all images at once
- 🏷️ **Rich Field Support** — Title, Subject, Tags, Comments, Rating, Authors, Date Taken, Copyright, GPS, and more
- 📋 **Templates** — Save and reapply metadata presets across multiple photo sessions
- 🗺️ **Map Picker** — Click anywhere on an interactive map to set GPS coordinates
- 💾 **Safe by Default** — Staged changes are previewed before writing to disk
- 🌙 **Dark Theme** — Glassmorphism-inspired dark UI with fully custom-themed dialogs

---

## 📦 Download & Install

> **The easiest way to get started — no Python required.**

Download the latest **`LeoSetterSetup.exe`** from the [**Releases page →**](https://github.com/AHJ32/LeoSetter/releases)

The installer wizard will:

- Bundle everything — Python runtime, all libraries, and ExifTool — inside a single setup file
- Let you choose whether to create a **Desktop shortcut** (checked by default)
- Let you choose whether to add LeoSetter to the **Start Menu** (checked by default)
- Offer to launch the app immediately after installation

No additional software needs to be installed.

---

## 🛠️ Setup from Source

Use this method if you want to run or develop LeoSetter directly from the codebase.

### Prerequisites

| Requirement | Version |
|---|---|
| Python | 3.10 or newer |
| ExifTool | Latest stable |

---

### Windows (PowerShell)

**1. Install Python**

Download from [python.org](https://www.python.org/downloads/) and check **"Add Python to PATH"** during installation.

**2. Install ExifTool**

Download the Windows executable from [exiftool.org](https://exiftool.org/), rename `exiftool(-k).exe` → `exiftool.exe`, and place it somewhere on your `PATH` (e.g. `C:\Windows\`).

**3. Clone and run**

```powershell
git clone https://github.com/AHJ32/LeoSetter.git
cd LeoSetter
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

---

### Linux (Debian / Ubuntu / Pop!_OS)

**1. Install dependencies**

```bash
sudo apt-get update
sudo apt-get install -y python3 python3-venv python3-pip libimage-exiftool-perl
```

**2. Clone and run**

```bash
git clone https://github.com/AHJ32/LeoSetter.git
cd LeoSetter
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python3 run.py
```

> **Note for Linux:** The custom dark title bar relies on the Windows DWM API and is automatically skipped on Linux. All other features work identically.

---

## 🚀 Usage

1. **Open a Folder** — Click *"Open Folder"* in the toolbar and browse to a directory of images.
2. **Select an Image** — Click any filename in the sidebar to load its metadata.
3. **Edit Fields** — Fill in the form on the right (Title, Tags, GPS, etc.).
4. **Stage Changes** — Edited images are highlighted; changes are not written yet.
5. **Save** — Click *"Save Changes"* to write all staged changes to disk.

### Toolbar Reference

| Button | Action |
|---|---|
| 📁 Open Folder | Browse for a folder of images |
| 📄 Set Filenames | Pre-fill Title, Subject, and Comments from each filename |
| 🏷️ Set Tags | Batch-assign tags to all images |
| 🗺️ Pick from Map | Open the interactive map to pick GPS coordinates |
| 💾 Save Template | Save the current form as a reusable preset |
| 📋 Apply Template | Load a saved preset into the form |
| ⚙️ Manage Templates | Delete or review saved templates |
| 💾 Save Changes | Write all staged metadata to disk |
| 🗑️ Clear All | Clear metadata from all images (with confirmation) |

---

## 🤝 Contributing

We welcome contributions of all kinds — bug fixes, new features, documentation improvements, and more.

Please read **[CONTRIBUTING.md](CONTRIBUTING.md)** for the full guide, including:
- How to report bugs
- How to submit pull requests
- Development setup instructions

---

## 💡 Requesting a Feature

Have an idea for something LeoSetter should do? We'd love to hear it.

See **[docs/FEATURE_REQUEST.md](docs/FEATURE_REQUEST.md)** for the step-by-step process for submitting a feature request, what makes a great request, and what happens after you submit one.

---

## 📜 License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- [GeoSetter](https://www.geosetter.de/en/) for the original inspiration
- [CustomTkinter](https://github.com/TomSchimansky/CustomTkinter) for the beautiful UI components
- [tkintermapview](https://github.com/TomSchimansky/TkinterMapView) for the interactive map widget
- [ExifTool by Phil Harvey](https://exiftool.org/) for robust metadata read/write
