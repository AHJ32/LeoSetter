import os
import threading
import queue
import customtkinter as ctk
from tkinter import filedialog, messagebox, simpledialog
from typing import Dict, List

from . import exif_backend as xb

IMAGE_EXTS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp"}

class ExifWorker(threading.Thread):
    def __init__(self, mode: str, path_or_paths, callback, payload=None, clear_fields=None, skip_keywords=False, inplace=True):
        super().__init__()
        self.mode = mode
        self.path_or_paths = path_or_paths
        self.callback = callback
        self.payload = payload
        self.clear_fields = clear_fields
        self.skip_keywords = skip_keywords
        self.inplace = inplace
        self.daemon = True

    def run(self):
        try:
            if self.mode == 'read':
                data = xb.read_metadata(self.path_or_paths) or {}
                self.callback({"status": "success", "mode": "read", "data": data, "path": self.path_or_paths})
            elif self.mode == 'write':
                xb.write_metadata(self.path_or_paths, self.payload, skip_keywords=self.skip_keywords, inplace=self.inplace)
                self.callback({"status": "success", "mode": "write", "path": self.path_or_paths})
            elif self.mode == 'batch_apply':
                total = len(self.path_or_paths)
                for index, path in enumerate(self.path_or_paths):
                    xb.write_metadata(path, self.payload, skip_keywords=self.skip_keywords, inplace=self.inplace)
                    self.callback({"status": "progress", "mode": "batch_apply", "current": index + 1, "total": total})
                self.callback({"status": "success", "mode": "batch_apply"})
            elif self.mode == 'batch_clear':
                total = len(self.path_or_paths)
                for index, path in enumerate(self.path_or_paths):
                    xb.clear_metadata(path, self.clear_fields, inplace=self.inplace)
                    self.callback({"status": "progress", "mode": "batch_clear", "current": index + 1, "total": total})
                self.callback({"status": "success", "mode": "batch_clear"})
            elif self.mode == 'save_all':
                total = len(self.payload)
                for index, (path, data) in enumerate(self.payload.items()):
                    xb.write_metadata(path, data, skip_keywords=self.skip_keywords, inplace=self.inplace)
                    self.callback({"status": "progress", "mode": "save_all", "current": index + 1, "total": total})
                self.callback({"status": "success", "mode": "save_all"})
        except Exception as e:
            self.callback({"status": "error", "message": f"{self.mode} failed: {str(e)}", "mode": self.mode})


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("LeoSetter")
        self.geometry("1200x750")
        
        # Application State
        self.folder_path = ""
        self.image_files = []
        self.current_image_path = None
        self.staged_changes = {} # File path -> dict of changed fields
        self.editing_disabled = False
        self._is_populating = False
        
        self.inplace_mode = True
        
        # Setup UI
        self.setup_ui()
        
        # Worker Queue for non-blocking UI
        self.queue = queue.Queue()
        self.after(100, self.process_queue)

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Toolbar
        self.toolbar = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.toolbar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.btn_open = ctk.CTkButton(self.toolbar, text="📂 Open Folder", command=self.open_folder, width=120)
        self.btn_open.pack(side="left", padx=10, pady=10)
        
        self.btn_filenames = ctk.CTkButton(self.toolbar, text="📝 Use Filenames", command=self.apply_filenames_to_all, width=120)
        self.btn_filenames.pack(side="left", padx=5, pady=10)
        
        self.btn_tags = ctk.CTkButton(self.toolbar, text="🏷️ Set Tags", command=self.set_tags_for_all, width=120)
        self.btn_tags.pack(side="left", padx=5, pady=10)
        
        self.btn_save_all = ctk.CTkButton(self.toolbar, text="💾 Save All Changes", command=self.save_all, fg_color="#28a745", hover_color="#218838", width=140)
        self.btn_save_all.pack(side="left", padx=20, pady=10)
        
        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=280, corner_radius=0)
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.grid_rowconfigure(0, weight=1)
        
        self.file_list = ctk.CTkScrollableFrame(self.sidebar, label_text="Images", width=250)
        self.file_list.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.file_buttons = {}
        
        # Main form area
        self.main_area = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)
        self.main_area.grid_columnconfigure((0, 1), weight=1)
        
        self.form_vars = {}
        
        self.create_form_section("Description", ["Title", "Subject", "Tags", "Comments", "Rating"], 0, 0)
        self.create_form_section("Origin", ["Authors", "DateTaken", "ProgramName", "DateAcquired", "Copyright"], 0, 1)
        self.create_form_section("Location (GPS)", ["GPSLatitude", "GPSLongitude", "GPSAltitude"], 1, 0, columnspan=2)
        
        # Action Bar in Main Area
        self.action_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, columnspan=2, pady=20, sticky="ew")
        
        self.btn_apply = ctk.CTkButton(self.action_frame, text="Apply to All", command=self.apply_to_all)
        self.btn_apply.pack(side="left", padx=10)
        
        self.btn_clear = ctk.CTkButton(self.action_frame, text="Clear Selected Fields in Batch", command=self.clear_batch, fg_color="#dc3545", hover_color="#c82333")
        self.btn_clear.pack(side="left", padx=10)
        
        self.btn_save_current = ctk.CTkButton(self.action_frame, text="Save Current", command=self.save_current)
        self.btn_save_current.pack(side="right", padx=10)
        
        # Status Bar
        self.status_var = ctk.StringVar(value="Ready. Open a folder to start.")
        self.status_lbl = ctk.CTkLabel(self, textvariable=self.status_var, anchor="w", justify="left")
        self.status_lbl.grid(row=2, column=0, columnspan=2, sticky="ew", padx=10, pady=5)
        
    def create_form_section(self, title, fields, row, col, columnspan=1):
        frame = ctk.CTkFrame(self.main_area)
        frame.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=10, pady=10)
        
        lbl = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        lbl.pack(pady=(10, 5), padx=10, anchor="w")
        
        for field in fields:
            self.create_field(frame, field)
            
    def create_field(self, parent, field_name):
        f_frame = ctk.CTkFrame(parent, fg_color="transparent")
        f_frame.pack(fill="x", padx=10, pady=2)
        
        f_lbl = ctk.CTkLabel(f_frame, text=field_name, width=120, anchor="w")
        f_lbl.pack(side="left")
        
        var = ctk.StringVar()
        var.trace_add("write", lambda *args, f=field_name: self.on_field_edited(f))
        self.form_vars[field_name] = var
        
        entry = ctk.CTkEntry(f_frame, textvariable=var)
        entry.pack(side="left", fill="x", expand=True)
        
    def open_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_path = folder
            self.load_folder()
            
    def load_folder(self):
        self.image_files = []
        for root, _, files in os.walk(self.folder_path):
            for f in files:
                if os.path.splitext(f)[1].lower() in IMAGE_EXTS:
                    self.image_files.append(os.path.join(root, f))
        self.image_files.sort()
        self.staged_changes.clear()
        self.update_file_list()
        self.status_var.set(f"Loaded {len(self.image_files)} images from {self.folder_path}")
        if self.image_files:
            self.load_image(self.image_files[0])
            
    def update_file_list(self):
        for widget in self.file_list.winfo_children():
            widget.destroy()
        self.file_buttons.clear()
        
        for path in self.image_files:
            btn = ctk.CTkButton(self.file_list, text=os.path.basename(path), fg_color="transparent", 
                                text_color=("gray10", "gray90"), hover_color=("gray70", "gray30"),
                                anchor="w", command=lambda p=path: self.load_image(p))
            btn.pack(fill="x", pady=1)
            self.file_buttons[path] = btn
            
    def refresh_list_colors(self):
        for path, btn in self.file_buttons.items():
            if path == self.current_image_path:
                btn.configure(fg_color=("#3a7ebf", "#1f538d"), text_color="white")
            elif path in self.staged_changes and self.staged_changes[path]:
                btn.configure(fg_color=("#e0a800", "#d39e00"), text_color="white")
            else:
                btn.configure(fg_color="transparent", text_color=("gray10", "gray90"))

    def load_image(self, path):
        if self.editing_disabled:
            return
        self.current_image_path = path
        self.refresh_list_colors()
        self.status_var.set(f"Loading metadata for {os.path.basename(path)}...")
        self.set_ui_state("disabled")
        worker = ExifWorker('read', path, self.worker_callback)
        worker.start()
        
    def on_field_edited(self, field):
        if self._is_populating or not self.current_image_path:
            return
        
        val = self.form_vars[field].get()
        if self.current_image_path not in self.staged_changes:
            self.staged_changes[self.current_image_path] = {}
        self.staged_changes[self.current_image_path][field] = val
        self.refresh_list_colors()

    def apply_filenames_to_all(self):
        if not self.image_files: return
        self._is_populating = True
        for path in self.image_files:
            name = os.path.splitext(os.path.basename(path))[0]
            if path not in self.staged_changes:
                self.staged_changes[path] = {}
            self.staged_changes[path].update({"Title": name, "Subject": name, "Comments": name})
        
        if self.current_image_path:
            name = os.path.splitext(os.path.basename(self.current_image_path))[0]
            self.form_vars["Title"].set(name)
            self.form_vars["Subject"].set(name)
            self.form_vars["Comments"].set(name)
            
        self._is_populating = False
        self.refresh_list_colors()
        self.status_var.set("Filenames staged for all images.")

    def set_tags_for_all(self):
        if not self.image_files: return
        dialog = ctk.CTkInputDialog(text="Enter tags separated by commas:", title="Set Tags")
        tags = dialog.get_input()
        if not tags: return
        
        self._is_populating = True
        for path in self.image_files:
            if path not in self.staged_changes:
                self.staged_changes[path] = {}
            self.staged_changes[path]["Tags"] = tags.strip()
            
        if self.current_image_path:
            self.form_vars["Tags"].set(tags.strip())
            
        self._is_populating = False
        self.refresh_list_colors()
        self.status_var.set("Tags staged for all images.")
        
    def current_payload(self) -> Dict[str, str]:
        payload = {}
        for f, var in self.form_vars.items():
            val = var.get().strip()
            if val:
                payload[f] = val
        return payload

    def save_current(self):
        if not self.current_image_path: return
        payload = self.current_payload()
        if not payload:
            messagebox.showinfo("Info", "No data to save.")
            return
            
        self.set_ui_state("disabled")
        self.status_var.set(f"Saving {os.path.basename(self.current_image_path)}...")
        worker = ExifWorker('write', self.current_image_path, self.worker_callback, payload=payload, inplace=self.inplace_mode)
        worker.start()

    def apply_to_all(self):
        if not self.image_files: return
        payload = self.current_payload()
        if not payload: return
        
        self.set_ui_state("disabled")
        worker = ExifWorker('batch_apply', self.image_files, self.worker_callback, payload=payload, inplace=self.inplace_mode)
        worker.start()

    def clear_batch(self):
        if not self.image_files: return
        fields_str = simpledialog.askstring("Clear Fields", "Enter field names to clear (comma-separated):", parent=self)
        if not fields_str: return
        
        fields = [f.strip() for f in fields_str.split(',') if f.strip() in self.form_vars]
        if not fields: return
        
        self.set_ui_state("disabled")
        worker = ExifWorker('batch_clear', self.image_files, self.worker_callback, clear_fields=fields, inplace=self.inplace_mode)
        worker.start()

    def save_all(self):
        if not self.staged_changes:
            self.status_var.set("No changes to save.")
            return
            
        self.set_ui_state("disabled")
        self.status_var.set(f"Saving changes to {len(self.staged_changes)} files...")
        worker = ExifWorker('save_all', None, self.worker_callback, payload=self.staged_changes, inplace=self.inplace_mode)
        worker.start()

    def worker_callback(self, result):
        self.queue.put(result)
        
    def process_queue(self):
        try:
            while True:
                res = self.queue.get_nowait()
                if res['status'] == 'error':
                    messagebox.showerror("Error", res['message'])
                    self.status_var.set("Error occurred.")
                    self.set_ui_state("normal")
                elif res['status'] == 'progress':
                    self.status_var.set(f"Processing {res['current']}/{res['total']}...")
                elif res['status'] == 'success':
                    if res['mode'] == 'read':
                        self._populate_form(res['data'])
                        self.status_var.set(f"Loaded {os.path.basename(res['path'])}")
                    elif res['mode'] == 'write':
                        if self.current_image_path in self.staged_changes:
                            del self.staged_changes[self.current_image_path]
                        self.refresh_list_colors()
                        self.status_var.set(f"Saved {os.path.basename(res['path'])}")
                    elif res['mode'] == 'batch_apply' or res['mode'] == 'batch_clear':
                        self.staged_changes.clear()
                        self.refresh_list_colors()
                        self.status_var.set(f"Batch operation completed.")
                    elif res['mode'] == 'save_all':
                        self.staged_changes.clear()
                        self.refresh_list_colors()
                        self.status_var.set("Saved all changes successfully!")
                    self.set_ui_state("normal")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.process_queue)

    def _populate_form(self, data):
        self._is_populating = True
        for field, var in self.form_vars.items():
            staged_val = self.staged_changes.get(self.current_image_path, {}).get(field)
            if staged_val is not None:
                val = staged_val
            else:
                val = data.get(field, "")
            var.set(val)
        self._is_populating = False

    def set_ui_state(self, state):
        self.editing_disabled = (state == "disabled")
        for btn in [self.btn_open, self.btn_filenames, self.btn_tags, self.btn_save_all, 
                    self.btn_apply, self.btn_clear, self.btn_save_current]:
            btn.configure(state=state)
