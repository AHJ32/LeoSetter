import os
from typing import Dict, List
from PyQt5.QtCore import Qt, QSettings, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QFileDialog,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QDoubleSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
    QListWidget,
    QListWidgetItem,
    QComboBox,
    QInputDialog,
    QTextEdit,
    QDialog,
)
from PyQt5.QtGui import QBrush, QColor

from . import exif_backend as xb
from .map_picker import MapPickerDialog


IMAGE_EXTS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp"}


class ExifWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)
    progress = pyqtSignal(int, int)

    def __init__(self, mode: str, path_or_paths, payload=None, clear_fields=None, skip_keywords=False, inplace=False):
        super().__init__()
        self.mode = mode
        self.path_or_paths = path_or_paths
        self.payload = payload
        self.clear_fields = clear_fields
        self.skip_keywords = skip_keywords
        self.inplace = inplace

    def run(self):
        try:
            if self.mode == 'read':
                data = xb.read_metadata(self.path_or_paths) or {}
                self.finished.emit(data)
            elif self.mode == 'write':
                xb.write_metadata(self.path_or_paths, self.payload, skip_keywords=self.skip_keywords, inplace=self.inplace)
                self.finished.emit({"success": True})
            elif self.mode == 'batch_apply':
                total = len(self.path_or_paths)
                errors = []
                for i, p in enumerate(self.path_or_paths):
                    try:
                        xb.write_metadata(p, self.payload, skip_keywords=self.skip_keywords, inplace=self.inplace)
                    except Exception as ex:
                        errors.append(f"{os.path.basename(p)}: {ex}")
                    self.progress.emit(i + 1, total)
                self.finished.emit({"success": True, "errors": errors, "total": total - len(errors)})
            elif self.mode == 'batch_clear':
                total = len(self.path_or_paths)
                errors = []
                for i, p in enumerate(self.path_or_paths):
                    try:
                        xb.clear_metadata(p, self.clear_fields, inplace=self.inplace)
                    except Exception as ex:
                        errors.append(f"{os.path.basename(p)}: {ex}")
                    self.progress.emit(i + 1, total)
                self.finished.emit({"success": True, "errors": errors, "total": total - len(errors)})
            elif self.mode == 'save_all':
                total = len(self.payload)
                errors = []
                for i, (p, p_payload) in enumerate(self.payload.items()):
                    try:
                        xb.write_metadata(p, p_payload, skip_keywords=self.skip_keywords, inplace=self.inplace)
                    except Exception as ex:
                        errors.append(f"{os.path.basename(p)}: {ex}")
                    self.progress.emit(i + 1, total)
                self.finished.emit({"success": True, "errors": errors, "total": total - len(errors)})
        except Exception as e:
            self.error.emit(str(e))


class MVPWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("LeoSetter")
        self.resize(1200, 700)

        self.settings = QSettings("PyGeoSetter", "MVP")
        self.current_folder: str = self.settings.value("last_folder", "", type=str) or ""
        self.images: List[str] = []
        # Staging area for batch operations before saving to disk
        self.pending_changes: Dict[str, Dict[str, str]] = {}
        # Write mode: when True, pass inplace to backend (overwrite original, no backup)
        self.overwrite_no_backup: bool = True

        # Actions (with shortcuts similar to GeoSetter)
        self.open_folder_action = QAction("Open Folder...", self)
        self.open_folder_action.setShortcut("Ctrl+O")
        self.open_folder_action.triggered.connect(self.open_folder)

        # Save All staged changes
        self.save_all_action = QAction("Save All", self)
        # Per request: Ctrl+S
        self.save_all_action.setShortcut("Ctrl+S")
        self.save_all_action.triggered.connect(self.save_all)

        self.clear_selected_action = QAction("Clear All", self)
        # Shortcut removed per user request
        self.clear_selected_action.triggered.connect(self.clear_selected_fields_batch)

        self.select_all_action = QAction("Select All", self)
        self.select_all_action.setShortcut("Ctrl+A")
        self.select_all_action.triggered.connect(self.select_all_images)

        self.refresh_action = QAction("Refresh", self)
        self.refresh_action.setShortcut("Ctrl+R")
        self.refresh_action.triggered.connect(self.refresh_folder)

        self.quit_action = QAction("Quit", self)
        self.quit_action.setShortcut("Ctrl+Q")
        self.quit_action.triggered.connect(self.close)

        # Batch: Use Filenames for Title/Subject/Comments
        self.use_filenames_action = QAction("Use Filenames (Title/Subject/Comments)", self)
        # Per request: Ctrl+F
        self.use_filenames_action.setShortcut("Ctrl+F")
        self.use_filenames_action.triggered.connect(self.apply_filenames_to_all)

        # Batch: Set Tags for all images
        self.set_tags_action = QAction("Set Tags For All…", self)
        # Using Ctrl+T as per user request
        self.set_tags_action.setShortcut("Ctrl+T")
        self.set_tags_action.triggered.connect(self.set_tags_for_all)

        # Settings: overwrite original (no backup)
        self.overwrite_action = QAction("Overwrite original (no backup)", self)
        self.overwrite_action.setCheckable(True)
        self.overwrite_action.setChecked(True)
        # Per request: Ctrl+Shift+O
        self.overwrite_action.setShortcut("Ctrl+Shift+O")
        self.overwrite_action.toggled.connect(self._toggle_overwrite)

        # Menu
        m_file = self.menuBar().addMenu("&File")
        m_file.addAction(self.open_folder_action)
        m_file.addSeparator()
        m_file.addAction(self.save_all_action)
        m_file.addSeparator()
        m_file.addAction(self.clear_selected_action)
        m_file.addAction(self.use_filenames_action)
        m_file.addAction(self.set_tags_action)
        m_file.addSeparator()
        m_file.addAction(self.overwrite_action)
        m_file.addSeparator()
        m_file.addAction(self.select_all_action)
        m_file.addAction(self.refresh_action)
        m_file.addSeparator()
        m_file.addAction(self.quit_action)

        m_templates = self.menuBar().addMenu("&Templates")
        # Template actions in the menu
        self.act_save_template = QAction("Save Template…", self)
        # Changed to 'C' as per user request
        self.act_save_template.setShortcut("C")
        self.act_save_template.triggered.connect(self.save_template_dialog)
        self.act_apply_template = QAction("Apply Template (Skip Keywords)", self)
        # Per request: Ctrl+E
        self.act_apply_template.setShortcut("Ctrl+E")
        self.act_apply_template.triggered.connect(self.apply_template_dialog)
        self.act_manage_templates = QAction("Manage Templates…", self)
        self.act_manage_templates.triggered.connect(self.manage_templates_dialog)
        m_templates.addAction(self.act_save_template)
        m_templates.addAction(self.act_apply_template)
        m_templates.addSeparator()
        m_templates.addAction(self.act_manage_templates)

        # Templates toolbar removed to prevent duplication; use the menu instead.

        # View menu with Full Metadata viewer
        m_view = self.menuBar().addMenu("&View")
        self.view_full_meta_action = QAction("View Full Metadata", self)
        self.view_full_meta_action.triggered.connect(self.view_full_metadata)
        m_view.addAction(self.view_full_meta_action)

        # Main toolbar with common actions
        main_tb = self.addToolBar("Main")
        # Per request: remove Open Folder and Clear from toolbar; remove Save Current / Apply To All
        # Add Use Filenames and Set Tags buttons to toolbar
        main_tb.addAction(self.use_filenames_action)
        main_tb.addAction(self.set_tags_action)
        main_tb.addSeparator()
        main_tb.addAction(self.select_all_action)
        main_tb.addAction(self.refresh_action)

        # Central UI
        splitter = QSplitter(Qt.Horizontal)
        self.setCentralWidget(splitter)

        # Left: file list
        left_container = QWidget()
        left_layout = QVBoxLayout(left_container)
        self.folder_label = QLabel("No folder selected")
        left_layout.addWidget(self.folder_label)
        self.file_list = QListWidget()
        self.file_list.itemSelectionChanged.connect(self.on_file_selected)
        left_layout.addWidget(self.file_list, 1)

        # Buttons under list
        btn_row = QHBoxLayout()
        self.btn_open = QPushButton("Open Folder…")
        self.btn_open.clicked.connect(self.open_folder)
        btn_row.addWidget(self.btn_open)
        left_layout.addLayout(btn_row)

        splitter.addWidget(left_container)

        # Right: form
        right = QWidget()
        right_layout = QVBoxLayout(right)

        form_group = QGroupBox("Metadata")
        form = QFormLayout(form_group)

        # Description
        self.f_Title = QLineEdit()
        self.f_Subject = QLineEdit()
        self.f_Rating = QSpinBox(); self.f_Rating.setRange(0, 5)
        self.f_Tags = QLineEdit()  # comma-separated
        self.f_Comments = QLineEdit()

        form.addRow("Title", self.f_Title)
        form.addRow("Subject", self.f_Subject)
        form.addRow("Rating (0-5)", self.f_Rating)
        form.addRow("Tags (comma)", self.f_Tags)
        form.addRow("Comments", self.f_Comments)

        # Origin
        self.f_Authors = QLineEdit()
        self.f_DateTaken = QLineEdit()
        self.f_ProgramName = QLineEdit()
        self.f_DateAcquired = QLineEdit()
        self.f_Copyright = QLineEdit()

        form.addRow(QLabel("\nOrigin"))
        form.addRow("Authors", self.f_Authors)
        form.addRow("Date taken", self.f_DateTaken)
        form.addRow("Program name", self.f_ProgramName)
        form.addRow("Date acquired", self.f_DateAcquired)
        form.addRow("Copyright", self.f_Copyright)

        # GPS
        self.f_GPSLatitude = QDoubleSpinBox(); self.f_GPSLatitude.setRange(-90.0, 90.0); self.f_GPSLatitude.setDecimals(8)
        self.f_GPSLongitude = QDoubleSpinBox(); self.f_GPSLongitude.setRange(-180.0, 180.0); self.f_GPSLongitude.setDecimals(8)
        self.f_GPSAltitude = QDoubleSpinBox(); self.f_GPSAltitude.setRange(-10000.0, 100000.0); self.f_GPSAltitude.setDecimals(2)

        form.addRow(QLabel("\nGPS"))
        form.addRow("Latitude", self.f_GPSLatitude)
        form.addRow("Longitude", self.f_GPSLongitude)
        form.addRow("Altitude (m)", self.f_GPSAltitude)

        # Map picker button
        map_btn_row = QHBoxLayout()
        self.btn_pick_map = QPushButton("Pick on Map…")
        self.btn_pick_map.setToolTip("Click a location on the map or search a country/place to set GPS")
        self.btn_pick_map.clicked.connect(self.pick_on_map)
        map_btn_row.addWidget(self.btn_pick_map)
        map_btn_row.addStretch(1)
        right_layout.addLayout(map_btn_row)

        right_layout.addWidget(form_group)

        # Buttons (bottom-right): Save All and Clear All (in this order)
        button_bar = QHBoxLayout()
        self.btn_save_all = QPushButton("Save All")
        self.btn_save_all.clicked.connect(self.save_all)
        self.btn_clear_all = QPushButton("Clear All")
        self.btn_clear_all.clicked.connect(self.clear_selected_fields_batch)

        button_bar.addStretch(1)
        button_bar.addWidget(self.btn_save_all)
        button_bar.addWidget(self.btn_clear_all)

        right_layout.addLayout(button_bar)
        splitter.addWidget(right)
        splitter.setStretchFactor(1, 1)

        if self.current_folder and os.path.isdir(self.current_folder):
            self.load_folder(self.current_folder)

    # Utility
    def current_path(self) -> str:
        items = self.file_list.selectedItems()
        if not items:
            return ""
        return items[0].data(Qt.UserRole) or ""

    def payload_from_form(self) -> Dict[str, str]:
        return {
            "Title": self.f_Title.text(),
            "Subject": self.f_Subject.text(),
            "Rating": str(self.f_Rating.value()),
            "Tags": self.f_Tags.text(),
            "Comments": self.f_Comments.text(),
            "Authors": self.f_Authors.text(),
            "DateTaken": self.f_DateTaken.text(),
            "ProgramName": self.f_ProgramName.text(),
            "DateAcquired": self.f_DateAcquired.text(),
            "Copyright": self.f_Copyright.text(),
            "GPSLatitude": str(self.f_GPSLatitude.value()),
            "GPSLongitude": str(self.f_GPSLongitude.value()),
            "GPSAltitude": str(self.f_GPSAltitude.value()),
        }

    def set_form(self, data: Dict[str, str]) -> None:
        self.f_Title.setText(data.get("Title", ""))
        self.f_Subject.setText(data.get("Subject", ""))
        self.f_Rating.setValue(int(data.get("Rating", "0") or 0))
        self.f_Tags.setText(data.get("Tags", ""))
        self.f_Comments.setText(data.get("Comments", ""))
        self.f_Authors.setText(data.get("Authors", ""))
        self.f_DateTaken.setText(data.get("DateTaken", ""))
        self.f_ProgramName.setText(data.get("ProgramName", ""))
        self.f_DateAcquired.setText(data.get("DateAcquired", ""))
        self.f_Copyright.setText(data.get("Copyright", ""))
        # GPS
        try:
            self.f_GPSLatitude.setValue(float(data.get("GPSLatitude", "0") or 0))
        except ValueError:
            self.f_GPSLatitude.setValue(0.0)
        try:
            self.f_GPSLongitude.setValue(float(data.get("GPSLongitude", "0") or 0))
        except ValueError:
            self.f_GPSLongitude.setValue(0.0)
        try:
            self.f_GPSAltitude.setValue(float(data.get("GPSAltitude", "0") or 0))
        except ValueError:
            self.f_GPSAltitude.setValue(0.0)

    # Folder & files
    def open_folder(self) -> None:
        class CustomFileDialog(QFileDialog):
            def keyPressEvent(self, event):
                if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                    # Get the current directory and selected items
                    current_dir = self.directory().absolutePath()
                    selected = self.selectedFiles()
                    
                    # If a directory is selected, navigate into it
                    if selected and os.path.isdir(selected[0]) and selected[0] != current_dir:
                        self.setDirectory(selected[0])
                        return
                    
                    # If we're in a directory with no subdirectories, accept the current directory
                    has_subdirs = any(os.path.isdir(os.path.join(current_dir, d)) 
                                   for d in os.listdir(current_dir) if not d.startswith('.'))
                    
                    if not has_subdirs:
                        self.accept()
                        return
                
                # Default behavior for other keys
                super().keyPressEvent(event)
        
        # Create and configure the dialog
        dialog = CustomFileDialog()
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, True)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        dialog.setWindowTitle("Select Folder")
        dialog.setDirectory(self.current_folder or os.path.expanduser("~"))
        
        # Connect the dialog's accepted signal
        if dialog.exec_() == QDialog.Accepted:
            folder = dialog.selectedFiles()[0] if dialog.selectedFiles() else dialog.directory().absolutePath()
            if os.path.isdir(folder):
                self.load_folder(folder)

    def load_folder(self, folder: str) -> None:
        if not xb.ensure_exiftool_available():
            QMessageBox.critical(self, "Missing dependency", "exiftool is not installed. Please install it (sudo apt install exiftool).")
            return
        self.current_folder = folder
        self.settings.setValue("last_folder", folder)
        self.folder_label.setText(folder)
        self.file_list.clear()
        self.images = []
        for root, _, files in os.walk(folder):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in IMAGE_EXTS:
                    p = os.path.join(root, f)
                    self.images.append(p)
        self.images.sort()
        for p in self.images:
            item = QListWidgetItem(os.path.relpath(p, folder))
            item.setData(Qt.UserRole, p)
            self.file_list.addItem(item)
        if self.images:
            self.file_list.setCurrentRow(0)
        self.statusBar().showMessage(f"Loaded {len(self.images)} file(s)", 3000)
        # Apply staged highlighting
        self.refresh_item_markers()

    def on_file_selected(self) -> None:
        path = self.current_path()
        if not path:
            return
        self.statusBar().showMessage(f"Loading metadata: {os.path.basename(path)}...", 2000)
        self.centralWidget().setEnabled(False)
        self._worker = ExifWorker(mode='read', path_or_paths=path)
        self._worker.finished.connect(lambda data: self._on_read_finished(data, path))
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_read_finished(self, data: dict, path: str) -> None:
        self.centralWidget().setEnabled(True)
        # Overlay staged changes if present for this file
        staged = self.pending_changes.get(path)
        if staged:
            data = {**data, **staged}
        self.set_form(data)
        self.statusBar().showMessage(f"Loaded metadata: {os.path.basename(path)}", 2000)

    def _on_worker_error(self, err_msg: str) -> None:
        self.centralWidget().setEnabled(True)
        QMessageBox.warning(self, "Error", err_msg)
        self.statusBar().showMessage("Operation failed.", 2000)

    def apply_filenames_to_all(self) -> None:
        if not self.images:
            QMessageBox.information(self, "No images", "Open a folder with images first.")
            return
        # Confirm action
        if QMessageBox.question(
            self,
            "Use Filenames",
            "Set Title, Subject, and Comments to each image's filename for ALL images in this folder?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        ) != QMessageBox.Yes:
            return
        # Stage changes only; do not write yet
        for p in self.images:
            name = os.path.splitext(os.path.basename(p))[0]
            updates = {"Title": name, "Subject": name, "Comments": name}
            self._stage_changes(p, updates)
        QMessageBox.information(self, "Use Filenames (Staged)", "Staged Title/Subject/Comments for all images. Click 'Save All' to write.")
        self.statusBar().showMessage("Staged filenames for all images", 4000)
        self.refresh_item_markers()

    def set_tags_for_all(self) -> None:
        if not self.images:
            QMessageBox.information(self, "No images", "Open a folder with images first.")
            return
        # Ask for tags (comma-separated)
        text, ok = QInputDialog.getText(self, "Set Tags For All", "Enter tags (comma-separated):")
        if not ok:
            return
        tags = text.strip()
        # Stage tag updates only; do not write yet
        for p in self.images:
            self._stage_changes(p, {"Tags": tags})
        QMessageBox.information(self, "Tags (Staged)", "Staged tags for all images. Click 'Save All' to write.")
        self.statusBar().showMessage("Staged tags for all images", 3000)
        self.refresh_item_markers()

    # Save/apply
    def save_current(self) -> None:
        path = self.current_path()
        if not path:
            QMessageBox.information(self, "No selection", "Select a file first.")
            return
        self.centralWidget().setEnabled(False)
        self.statusBar().showMessage("Saving current image...")
        self._worker = ExifWorker(
            mode='write',
            path_or_paths=path,
            payload=self.payload_from_form(),
            skip_keywords=False,
            inplace=self.overwrite_no_backup
        )
        self._worker.finished.connect(self._on_save_current_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_save_current_finished(self, res: dict) -> None:
        self.centralWidget().setEnabled(True)
        QMessageBox.information(self, "Saved", "Metadata written.")
        self.statusBar().showMessage("Saved current image", 2000)

    def apply_to_all(self, skip_keywords: bool = False) -> None:
        if not self.images:
            QMessageBox.information(self, "No images", "Open a folder with images first.")
            return
        self.centralWidget().setEnabled(False)
        self.statusBar().showMessage(f"Applying to {len(self.images)} images...")
        self._worker = ExifWorker(
            mode='batch_apply',
            path_or_paths=self.images,
            payload=self.payload_from_form(),
            skip_keywords=skip_keywords,
            inplace=self.overwrite_no_backup
        )
        self._worker.progress.connect(lambda cur, tot: self.statusBar().showMessage(f"Applying {cur}/{tot}..."))
        self._worker.finished.connect(self._on_apply_to_all_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_apply_to_all_finished(self, res: dict) -> None:
        self.centralWidget().setEnabled(True)
        errors = res.get("errors", [])
        if errors:
            QMessageBox.warning(self, "Batch", "Some files failed:\n" + "\n".join(errors[:10]))
        else:
            QMessageBox.information(self, "Batch", "Applied metadata to all images.")
        self.statusBar().showMessage("Applied to all images", 3000)

    def clear_selected_fields_batch(self) -> None:
        if not self.images:
            QMessageBox.information(self, "No images", "Open a folder first.")
            return
        # Determine selected fields based on non-empty inputs (simple UX for MVP)
        fields: List[str] = []
        mapping = {
            "Title": self.f_Title.text(),
            "Subject": self.f_Subject.text(),
            "Rating": str(self.f_Rating.value()) if self.f_Rating.value() else "",
            "Tags": self.f_Tags.text(),
            "Comments": self.f_Comments.text(),
            "Authors": self.f_Authors.text(),
            "DateTaken": self.f_DateTaken.text(),
            "ProgramName": self.f_ProgramName.text(),
            "DateAcquired": self.f_DateAcquired.text(),
            "Copyright": self.f_Copyright.text(),
            "GPSLatitude": str(self.f_GPSLatitude.value()),
            "GPSLongitude": str(self.f_GPSLongitude.value()),
            "GPSAltitude": str(self.f_GPSAltitude.value()),
        }
        for k, v in mapping.items():
            if v:
                fields.append(k)
        if not fields:
            if QMessageBox.question(
                self,
                "Clear All?",
                "No fields typed. Clear ALL supported fields in batch?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.Yes
            ) != QMessageBox.Yes:
                return
            # Clear all known fields
            fields = list(xb.TAG_MAP.keys())
        
        self.centralWidget().setEnabled(False)
        self.statusBar().showMessage(f"Clearing fields for {len(self.images)} images...")
        self._worker = ExifWorker(
            mode='batch_clear',
            path_or_paths=self.images,
            clear_fields=fields,
            inplace=self.overwrite_no_backup
        )
        self._worker.progress.connect(lambda cur, tot: self.statusBar().showMessage(f"Clearing {cur}/{tot}..."))
        self._worker.finished.connect(self._on_batch_clear_finished)
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_batch_clear_finished(self, res: dict) -> None:
        self.centralWidget().setEnabled(True)
        errors = res.get("errors", [])
        if errors:
            QMessageBox.warning(self, "Batch Clear", "Some files failed to clear:\n" + "\n".join(errors[:10]))
        else:
            QMessageBox.information(self, "Batch Clear", "Selected fields cleared for all images.")
        self.statusBar().showMessage("Cleared selected fields for all", 3000)

    # Selection and refresh helpers
    def select_all_images(self) -> None:
        if self.file_list.count() == 0:
            return
        self.file_list.selectAll()

    def refresh_folder(self) -> None:
        if self.current_folder and os.path.isdir(self.current_folder):
            self.load_folder(self.current_folder)
        else:
            self.statusBar().showMessage("No folder to refresh", 2000)

    # Map picker
    def pick_on_map(self) -> None:
        try:
            start_lat = float(self.f_GPSLatitude.value())
        except Exception:
            start_lat = 0.0
        try:
            start_lon = float(self.f_GPSLongitude.value())
        except Exception:
            start_lon = 0.0
        lat, lon, ok = MapPickerDialog.get_location(self, start_lat, start_lon)
        if ok and lat is not None and lon is not None:
            self.f_GPSLatitude.setValue(float(lat))
            self.f_GPSLongitude.setValue(float(lon))

    # Templates
    def refresh_templates(self) -> None:
        self.templates = xb.load_templates()

    def save_template_dialog(self) -> None:
        # Ask only for a template name; store internally under mvp/templates/templates.json
        name, ok = QInputDialog.getText(self, "Save Template", "Template name:")
        if not ok or not name.strip():
            return
        key = name.strip()
        payload = self.payload_from_form()
        self.refresh_templates()
        self.templates[key] = payload
        xb.save_templates(self.templates)
        QMessageBox.information(self, "Template Saved", f"Saved template '{key}'.")

    def apply_template_dialog(self) -> None:
        self.refresh_templates()
        if not self.templates:
            QMessageBox.information(self, "No Templates", "Save a template first.")
            return
        # Choose from existing stored templates
        names = sorted(self.templates.keys())
        key, ok = QInputDialog.getItem(self, "Choose Template", "Template:", names, 0, False)
        if not ok or not key:
            return
        payload = self.templates.get(key)
        if not payload:
            return
        payload_skipped = dict(payload)
        for k in ("Tags", "Title", "Subject", "Comments"):
            payload_skipped.pop(k, None)
        self.set_form(payload_skipped)
        if QMessageBox.question(
            self,
            "Apply",
            "Apply template to all images now (Keywords excluded)?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes
        ) == QMessageBox.Yes:
            # Stage template payload for all (excluding protected fields); do not write yet
            batch_payload = self.payload_from_form()
            for k in ("Title", "Subject", "Comments", "Tags"):
                batch_payload.pop(k, None)
            for p in self.images:
                self._stage_changes(p, batch_payload)
            QMessageBox.information(self, "Template (Staged)", "Staged template fields for all images. Click 'Save All' to write.")
            self.statusBar().showMessage("Staged template for all images", 3000)
            self.refresh_item_markers()

    def manage_templates_dialog(self) -> None:
        while True:  # Keep showing the dialog until user cancels
            self.refresh_templates()
            if not self.templates:
                QMessageBox.information(self, "Templates", "No templates saved yet.")
                return
                
            names = sorted(self.templates.keys())
            key, ok = QInputDialog.getItem(
                self, 
                "Manage Templates", 
                "Select template (Cancel to exit):", 
                names, 
                0,  # Default to first item
                False  # Not editable
            )
            
            if not ok or not key:
                return  # User cancelled
                
            action = QMessageBox.question(
                self,
                "Manage Template",
                f"What would you like to do with template '{key}'?\n\n"
                "Click 'Yes' to rename, 'No' to delete, or 'Cancel' to go back.",
                QMessageBox.Yes | QMessageBox.No | QMessageBox.Cancel,
                QMessageBox.Yes  # Default to Yes
            )
            
            if action == QMessageBox.Yes:  # Rename
                while True:  # Keep asking for new name until valid or cancelled
                    new_name, ok2 = QInputDialog.getText(
                        self, 
                        "Rename Template", 
                        f"Rename '{key}' to:",
                        text=key
                    )
                    if not ok2:  # User cancelled
                        break
                        
                    new_name = new_name.strip()
                    if not new_name:
                        QMessageBox.warning(self, "Error", "Template name cannot be empty.")
                        continue
                        
                    if new_name == key:
                        break  # No change
                        
                    if new_name in self.templates:
                        QMessageBox.warning(self, "Error", f"A template named '{new_name}' already exists.")
                        continue
                        
                    # Perform the rename
                    self.templates[new_name] = self.templates.pop(key)
                    xb.save_templates(self.templates)
                    QMessageBox.information(self, "Success", f"Template renamed to '{new_name}'.")
                    break  # Exit rename loop
                    
            elif action == QMessageBox.No:  # Delete
                confirm = QMessageBox.question(
                    self,
                    "Confirm Delete",
                    f"Are you sure you want to delete the template '{key}'?\nThis cannot be undone.",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.Yes  # Default to Yes
                )
                
                if confirm == QMessageBox.Yes:
                    self.templates.pop(key, None)
                    xb.save_templates(self.templates)
                    QMessageBox.information(self, "Success", "Template deleted.")
                    
                    # If no more templates, exit management
                    if not self.templates:
                        return
            else:
                # User clicked Cancel, show the list again
                continue

    def closeEvent(self, event):
        if self.current_folder:
            self.settings.setValue("last_folder", self.current_folder)
        super().closeEvent(event)

    # --- Staging helpers and Save All ---
    def _stage_changes(self, path: str, updates: Dict[str, str]) -> None:
        existing = self.pending_changes.get(path, {})
        existing.update({k: v for k, v in updates.items() if v is not None})
        self.pending_changes[path] = existing

    def save_all(self) -> None:
        if not self.pending_changes:
            QMessageBox.information(self, "Save All", "No staged changes to save.")
            return
        
        self.centralWidget().setEnabled(False)
        self.statusBar().showMessage(f"Saving {len(self.pending_changes)} files...")
        
        pending_copy = dict(self.pending_changes)
        
        self._worker = ExifWorker(
            mode='save_all',
            path_or_paths=None,
            payload=pending_copy,
            inplace=self.overwrite_no_backup
        )
        self._worker.progress.connect(lambda cur, tot: self.statusBar().showMessage(f"Saving {cur}/{tot}..."))
        self._worker.finished.connect(lambda res: self._on_save_all_finished(res, pending_copy))
        self._worker.error.connect(self._on_worker_error)
        self._worker.start()

    def _on_save_all_finished(self, res: dict, requested: dict) -> None:
        self.centralWidget().setEnabled(True)
        errors = res.get("errors", [])
        total_saved = res.get("total", 0)
        
        # Only clear from pending what was attempted/saved
        for p in requested.keys():
            self.pending_changes.pop(p, None)
            
        if errors:
            QMessageBox.warning(self, "Save All", "Some files failed to save:\n" + "\n".join(errors[:10]))
        QMessageBox.information(self, "Save All", f"Saved {total_saved} file(s).")
        self.statusBar().showMessage(f"Saved {total_saved} file(s)", 4000)
        self.refresh_item_markers()

    def _toggle_overwrite(self, checked: bool) -> None:
        self.overwrite_no_backup = checked
        msg = "Overwrite mode ON: writing directly to originals (no backup)." if checked else "Overwrite mode OFF: changes will not overwrite originals."
        self.statusBar().showMessage(msg, 4000)

    # --- UI marking helpers ---
    def refresh_item_markers(self) -> None:
        """Color items with staged changes (e.g., yellow)."""
        yellow = QBrush(QColor(255, 235, 130))  # soft yellow
        default = QBrush()
        for i in range(self.file_list.count()):
            item = self.file_list.item(i)
            path = item.data(Qt.UserRole)
            if path in self.pending_changes:
                item.setBackground(yellow)
            else:
                item.setBackground(default)

    # --- Viewers ---
    def view_full_metadata(self) -> None:
        path = self.current_path()
        if not path:
            QMessageBox.information(self, "No selection", "Select a file first.")
            return
        try:
            raw = xb.read_raw_json(path)
        except Exception as e:
            QMessageBox.critical(self, "Metadata", str(e))
            return
        dlg = QDialog(self)
        dlg.setWindowTitle("Full Metadata (read-only)")
        dlg.resize(800, 600)
        lay = QVBoxLayout(dlg)
        txt = QTextEdit(dlg)
        txt.setReadOnly(True)
        txt.setPlainText(raw)
        lay.addWidget(txt)
        dlg.exec_()
