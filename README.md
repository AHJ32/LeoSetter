# LeoSetter — Minimal MVP

A lightweight metadata editor focused on the essentials: edit a small, practical set of metadata fields, batch apply/clear across a folder, and use templates that fill everything except keywords.

## MVP Features

- **Edit fields**
  - GPS: Latitude, Longitude, Altitude (decimal degrees)
  - Description: Title, Subject, Rating, Tags (keywords), Comments
  - Origin: Authors, Date taken, Program name, Date acquired, Copyright
- **Batch apply**: Apply current form to all images in the open folder (keywords excluded by default on batch apply)
- **Batch clear**: Clear selected fields for all images (or clear all supported fields if you confirm)
- **Templates**: Save current form as a template and apply templates (keywords are excluded on apply)
- **Image formats**: JPEG, TIFF, PNG, WEBP (and others supported by `exiftool`)

## Installation

### Prerequisites

- Python 3.10+
- Qt5 libraries (installed automatically by pip via PyQt5)
- Python virtual environment (recommended)
- `exiftool` (system package, used for robust EXIF/XMP write/read)
  - Debian/Ubuntu/Pop!_OS: `sudo apt-get install -y exiftool`

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/leosetter.git
   cd leosetter
   ```

2. Create and activate a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install `exiftool` (if you haven't already):

## Usage

### Running the Application (from source)

To start the minimal app:

```bash
python run.py
```

Alternatively, you can use the CLI alias installed by setup.py:

```bash
leosetter
```

### Basic Operations

- Open a folder of images via File → "Open Folder…" (left pane lists images)
- Selecting a file loads its metadata into the form on the right
- "Save Current" writes metadata to a copy file (safer default)
- "Apply To All (Skip Keywords)" batch-applies the current form to all images in the open folder (keywords excluded)
- "Clear Selected Fields (Batch)" clears the non-empty fields you’ve entered; leave everything empty to clear all supported fields
- Templates: "Save Template…" stores the current form; "Apply Template (Skip Keywords)" loads a template, fills the form except keywords, and can batch-apply

## Building

Packaging is not part of the MVP yet. If you want a single-file build, consider PyInstaller later.

## Contributing

Contributions are welcome. Focus areas:

- Stability of read/write across formats using `exiftool`
- DMS input for GPS (conversion to decimal degrees)
- Thumbnail grid for the file list
- Optional in-place overwrite with automatic backups

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- GeoSetter for inspiration
- All the open-source libraries used in this project
