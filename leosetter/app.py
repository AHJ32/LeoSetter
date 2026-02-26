import os
import sys
import webbrowser
import threading
import queue
import customtkinter as ctk
from tkinter import filedialog
from typing import Dict, List

from . import exif_backend as xb
from .map_picker import MapPickerDialog
from .version import APP_VERSION, GITHUB_URL
from . import updater

import json
from PIL import Image

IMAGE_EXTS = {".jpg", ".jpeg", ".tif", ".tiff", ".png", ".webp"}


def _resource_path(*parts: str) -> str:
    """
    Return the absolute path to a bundled resource.

    When running as a PyInstaller frozen app, _MEIPASS is the temp folder where
    all bundled data files are extracted.  In development, we fall back to the
    project root (two levels above this file).
    """
    if getattr(sys, "frozen", False):
        base = sys._MEIPASS  # type: ignore[attr-defined]
    else:
        # project root: leosetter/ -> parent
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, *parts)


def _user_config_dir() -> str:
    """Return a writable per-user config directory (same as exif_backend uses)."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA", os.path.expanduser("~"))
    else:
        base = os.environ.get("XDG_CONFIG_HOME", os.path.join(os.path.expanduser("~"), ".config"))
    path = os.path.join(base, "LeoSetter")
    os.makedirs(path, exist_ok=True)
    return path


# Apply LeoSetter theme before any widget is created
_THEME_PATH = _resource_path("leosetter", "leosetter_theme.json")
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme(_THEME_PATH)

SETTINGS_FILE = os.path.join(_user_config_dir(), "settings.json")

# ─── Themed dialog helpers ────────────────────────────────────────────────────

def _dark_titlebar(win):
    """Force dark title bar on Windows via DWMAPI — used only for the main App window."""
    import sys
    if sys.platform != "win32":
        return
    try:
        from ctypes import windll, byref, sizeof, c_int
        for get in (lambda: windll.user32.GetParent(win.winfo_id()),
                    lambda: int(win.wm_frame(), 16)):
            try:
                hwnd = get()
                if hwnd:
                    for attr in (19, 20):
                        windll.dwmapi.DwmSetWindowAttribute(
                            hwnd, attr, byref(c_int(1)), sizeof(c_int))
            except Exception:
                pass
    except Exception:
        pass

def _make_themed_dialog(parent, title: str, width: int, height: int):
    """
    Create a fully themed borderless CTkToplevel with a custom dark title bar.
    Returns (dlg, content_frame).  The caller packs/grids widgets into content_frame.
    """
    dlg = ctk.CTkToplevel(parent)
    
    import sys
    if sys.platform == "win32":
        def _remove_caption():
            try:
                from ctypes import windll
                hwnd = windll.user32.GetParent(dlg.winfo_id())
                GWL_STYLE = -16
                WS_CAPTION = 0x00C00000
                WS_THICKFRAME = 0x00040000
                style = windll.user32.GetWindowLongW(hwnd, GWL_STYLE)
                windll.user32.SetWindowLongW(hwnd, GWL_STYLE, style & ~WS_CAPTION & ~WS_THICKFRAME)
            except Exception:
                pass
        dlg.after(10, _remove_caption)
    else:
        dlg.overrideredirect(True)

    dlg.configure(fg_color="#0e0b14")
    dlg.resizable(False, False)
    dlg.transient(parent)
    dlg.grab_set()

    # Centre over parent
    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width()  - width)  // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    dlg.geometry(f"{width}x{height}+{x}+{y}")

    # ── Custom title bar ──────────────────────────────────────────────────────
    title_bar = ctk.CTkFrame(dlg, height=36, fg_color="#1a1524", corner_radius=0)
    title_bar.pack(fill="x", side="top")
    title_bar.pack_propagate(False)

    ctk.CTkLabel(title_bar, text=title,
                 font=ctk.CTkFont(size=13, weight="bold"),
                 text_color="#fafafa").pack(side="left", padx=12)

    ctk.CTkButton(title_bar, text="✕", width=36, height=36,
                  fg_color="transparent", hover_color="#ef4444",
                  text_color="#8f8599", corner_radius=0,
                  command=dlg.destroy).pack(side="right", padx=0)

    # Dragging
    dlg._dx = dlg._dy = 0
    def _start(e): dlg._dx, dlg._dy = e.x_root, e.y_root
    def _drag(e):
        dlg.geometry(f"+{dlg.winfo_x()+e.x_root-dlg._dx}+{dlg.winfo_y()+e.y_root-dlg._dy}")
        dlg._dx, dlg._dy = e.x_root, e.y_root
    title_bar.bind("<ButtonPress-1>", _start)
    title_bar.bind("<B1-Motion>",     _drag)

    # Content area
    content = ctk.CTkFrame(dlg, fg_color="#0e0b14", corner_radius=0)
    content.pack(fill="both", expand=True)
    return dlg, content

def ask_confirm(parent, title: str, message: str) -> bool:
    """Themed yes/no dialog. Returns True if Yes clicked."""
    dlg, content = _make_themed_dialog(parent, title, 460, 170)
    result = [False]
    ctk.CTkLabel(content, text=message, wraplength=420, justify="left").pack(
        padx=24, pady=(20, 8), anchor="w")
    f = ctk.CTkFrame(content, fg_color="transparent")
    f.pack(padx=24, pady=(4, 20), anchor="e")
    def _yes(): result[0] = True; dlg.destroy()
    ctk.CTkButton(f, text="Yes", width=80, fg_color="#e84466",
                  hover_color="#c73858", command=_yes).pack(side="left", padx=(0, 8))
    ctk.CTkButton(f, text="No",  width=80, command=dlg.destroy).pack(side="left")
    parent.wait_window(dlg)
    return result[0]

def show_message(parent, title: str, message: str, error: bool = False):
    """Themed info / error dialog."""
    dlg, content = _make_themed_dialog(parent, title, 460, 170)
    color = "#ef4444" if error else "#fafafa"
    ctk.CTkLabel(content, text=message, wraplength=420, justify="left",
                 text_color=color).pack(padx=24, pady=(20, 8), anchor="w")
    f = ctk.CTkFrame(content, fg_color="transparent")
    f.pack(padx=24, pady=(4, 20), anchor="e")
    ctk.CTkButton(f, text="OK", width=80, command=dlg.destroy).pack()
    parent.wait_window(dlg)

def ask_string(parent, title: str, prompt: str) -> str:
    """Themed text input dialog."""
    dlg, content = _make_themed_dialog(parent, title, 460, 200)
    result = [None]
    
    ctk.CTkLabel(content, text=prompt, wraplength=420, justify="left",
                 text_color="#fafafa").pack(padx=24, pady=(20, 8), anchor="w")
                 
    entry = ctk.CTkEntry(content, width=412, fg_color="#27212f",
                         border_color="#322b3c", text_color="#fafafa")
    entry.pack(padx=24, pady=(0, 20))
    dlg.after(150, lambda: entry.focus())
    
    f = ctk.CTkFrame(content, fg_color="transparent")
    f.pack(padx=24, pady=(0, 20), anchor="e")
    
    def _ok(event=None):
        result[0] = entry.get()
        dlg.destroy()
        
    entry.bind("<Return>", _ok)
    
    ctk.CTkButton(f, text="OK", width=80, fg_color="#e84466",
                  hover_color="#c73858", command=_ok).pack(side="left", padx=(0, 8))
    ctk.CTkButton(f, text="Cancel", width=80, command=dlg.destroy).pack(side="left")
    
    parent.wait_window(dlg)
    return result[0]


# ─────────────────────────────────────────────────────────────────────────────


def load_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_settings(settings: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
    except Exception:
        pass

FORM_LAYOUT = [
    {
        "title": "Description",
        "fields": ["Title", "Subject", "Tags", "Comments", "Rating"],
        "row": 0, "col": 0, "colspan": 2
    },
    {
        "title": "Origin",
        "fields": ["Authors", "DateTaken", "ProgramName", "DateAcquired", "Copyright"],
        "row": 1, "col": 0, "colspan": 2
    },
]

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
                chunk_size = 50
                for i in range(0, total, chunk_size):
                    chunk = self.path_or_paths[i:i + chunk_size]
                    xb.write_metadata(chunk, self.payload, skip_keywords=self.skip_keywords, inplace=self.inplace)
                    current = min(i + chunk_size, total)
                    self.callback({"status": "progress", "mode": "batch_apply", "current": current, "total": total})
                self.callback({"status": "success", "mode": "batch_apply"})
            elif self.mode == 'batch_clear':
                total = len(self.path_or_paths)
                chunk_size = 50
                for i in range(0, total, chunk_size):
                    chunk = self.path_or_paths[i:i + chunk_size]
                    xb.clear_metadata(chunk, self.clear_fields, inplace=self.inplace)
                    current = min(i + chunk_size, total)
                    self.callback({"status": "progress", "mode": "batch_clear", "current": current, "total": total})
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
        self.after(150, lambda: _dark_titlebar(self))
        _blank_ico = _resource_path("assets", "blank.ico")
        self.after(200, lambda: self.iconbitmap(_blank_ico))
        self.after(350, lambda: _dark_titlebar(self))

        # Load Settings
        self.settings = load_settings()
        geom = self.settings.get("geometry", "800x600")
        self.geometry(geom)
        
        # Application State
        self.folder_path = self.settings.get("last_folder", "")
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
        
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Auto-load last folder if it exists
        if self.folder_path and os.path.exists(self.folder_path):
            self.load_folder()

    def setup_ui(self):
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # Toolbar
        self.toolbar = ctk.CTkFrame(self, height=60, corner_radius=0)
        self.toolbar.grid(row=0, column=0, columnspan=3, sticky="ew")
        
        self.btn_open = ctk.CTkButton(self.toolbar, text="📂 Open Folder", command=self.open_folder, width=120)
        self.btn_open.pack(side="left", padx=10, pady=10)
        
        self.btn_filenames = ctk.CTkButton(self.toolbar, text="📝 Use Filenames", command=self.apply_filenames_to_all, width=120)
        self.btn_filenames.pack(side="left", padx=5, pady=10)
        
        self.btn_tags = ctk.CTkButton(self.toolbar, text="🏷️ Set Tags", command=self.set_tags_for_all, width=120)
        self.btn_tags.pack(side="left", padx=5, pady=10)
        
        # Template buttons
        self.btn_save_template = ctk.CTkButton(self.toolbar, text="💾 Save Template", command=self.save_template_dialog, width=120)
        self.btn_save_template.pack(side="left", padx=5, pady=10)
        
        self.btn_apply_template = ctk.CTkButton(self.toolbar, text="📂 Apply Template", command=self.apply_template_dialog, width=120)
        self.btn_apply_template.pack(side="left", padx=5, pady=10)
        
        self.btn_manage_templates = ctk.CTkButton(self.toolbar, text="⚙️ Manage Templates", command=self.manage_templates_dialog, width=130)
        self.btn_manage_templates.pack(side="left", padx=5, pady=10)
        
        self.btn_map = ctk.CTkButton(self.toolbar, text="🗺️ Pick from Map", command=self.pick_on_map, width=130)
        self.btn_map.pack(side="left", padx=5, pady=10)

        # ── Right-side toolbar icons ───────────────────────────────────────────
        # GitHub icon — opens the repo in the browser
        self.btn_github = ctk.CTkButton(
            self.toolbar,
            text="🐙",
            width=44, height=40,
            fg_color="transparent",
            hover_color="#27212f",
            corner_radius=8,
            font=ctk.CTkFont(size=18),
            command=lambda: webbrowser.open(GITHUB_URL),
        )
        self.btn_github.pack(side="right", padx=(0, 8), pady=10)

        # Gear / Settings icon — opens the settings dialog
        self.btn_settings = ctk.CTkButton(
            self.toolbar,
            text="⚙️",
            width=44, height=40,
            fg_color="transparent",
            hover_color="#27212f",
            corner_radius=8,
            font=ctk.CTkFont(size=18),
            command=self.show_settings_dialog,
        )
        self.btn_settings.pack(side="right", padx=(0, 4), pady=10)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=450, corner_radius=0)
        self.sidebar.grid(row=1, column=0, sticky="ns")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_rowconfigure(0, weight=1)
        self.sidebar.grid_columnconfigure(0, weight=1)
        
        self.file_list = ctk.CTkScrollableFrame(self.sidebar, label_text="Images")
        self.file_list.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        self.file_buttons = {}
        
        # Main form area
        self.main_area = ctk.CTkScrollableFrame(self, corner_radius=0, fg_color="transparent")
        self.main_area.grid(row=1, column=1, sticky="nsew", padx=20, pady=20)
        self.main_area.grid_columnconfigure(0, weight=1)
        self.main_area.grid_columnconfigure(1, weight=1)
        self.main_area.grid_rowconfigure(0, weight=1)
        self.main_area.grid_rowconfigure(1, weight=1)
        
        self.form_vars = {}
        
        # Register GPS vars silently (no UI rows — map picker uses these)
        for gps_field in ["GPSLatitude", "GPSLongitude"]:
            var = ctk.StringVar()
            var.trace_add("write", lambda *args, f=gps_field: self.on_field_edited(f))
            self.form_vars[gps_field] = var
        
        for section in FORM_LAYOUT:
            self.create_form_section(
                title=section["title"],
                fields=section["fields"],
                row=section["row"],
                col=section["col"],
                columnspan=section.get("colspan", 1),
            )
        
        # Action Bar in Main Area
        self.action_frame = ctk.CTkFrame(self.main_area, fg_color="transparent")
        self.action_frame.grid(row=2, column=0, columnspan=2, pady=20, sticky="ew")
        
        self.inplace_var = ctk.BooleanVar(value=True)
        self.check_inplace = ctk.CTkCheckBox(self.action_frame, text="Overwite Originals (Inplace)", variable=self.inplace_var, command=self.toggle_inplace)
        self.check_inplace.pack(side="left", padx=10)
        
        self.btn_clear = ctk.CTkButton(self.action_frame, text="Clear All", command=self.clear_all_batch, fg_color="#ef4444", hover_color="#c53030", text_color="#fafafa")
        self.btn_clear.pack(side="left", padx=10)
        
        self.btn_save_all = ctk.CTkButton(self.action_frame, text="💾 Save Changes", command=self.save_all, fg_color="#28a745", hover_color="#218838", width=140)
        self.btn_save_all.pack(side="right", padx=10)
        
        # Status Bar
        self.status_frame = ctk.CTkFrame(self, height=30, fg_color="transparent")
        self.status_frame.grid(row=2, column=0, columnspan=3, sticky="ew", padx=10, pady=5)
        self.status_frame.grid_columnconfigure(0, weight=1)
        
        self.status_var = ctk.StringVar(value="Ready. Open a folder to start.")
        self.status_lbl = ctk.CTkLabel(self.status_frame, textvariable=self.status_var, anchor="w", justify="left")
        self.status_lbl.grid(row=0, column=0, sticky="w")
        
        self.progress_bar = ctk.CTkProgressBar(self.status_frame, width=200, mode="determinate")
        self.progress_bar.grid(row=0, column=1, sticky="e", padx=10)
        self.progress_bar.set(0)
        self.progress_bar.grid_remove() # Hidden by default
        
    def create_form_section(self, title, fields, row, col, columnspan=1):
        frame = ctk.CTkFrame(self.main_area)
        frame.grid(row=row, column=col, columnspan=columnspan, sticky="nsew", padx=10, pady=10)
        
        lbl = ctk.CTkLabel(frame, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        lbl.pack(pady=(16, 8), padx=20, anchor="w")
        
        for field in fields:
            self.create_field(frame, field)
            
    def create_field(self, parent, field_name):
        f_frame = ctk.CTkFrame(parent, fg_color="transparent")
        f_frame.pack(fill="x", padx=20, pady=6)
        
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
            try:
                with Image.open(path) as src_img:
                    img = src_img.copy()
                    img.thumbnail((48, 48))
                    if img.mode != 'RGB':
                        img = img.convert('RGB')
                    ctk_img = ctk.CTkImage(light_image=img, size=img.size)
            except Exception:
                ctk_img = None
                
            fname = os.path.basename(path)
            display_name = fname if len(fname) <= 45 else fname[:28] + '...' + fname[-13:]
                
            btn_kwargs = {
                "text": display_name,
                "fg_color": "transparent",
                "text_color": "#fafafa",
                "hover_color": "#27212f",
                "anchor": "w",
                "command": lambda p=path: self.load_image(p)
            }
            if ctk_img:
                btn_kwargs["image"] = ctk_img
                btn_kwargs["compound"] = "left"
                
            btn = ctk.CTkButton(self.file_list, **btn_kwargs)
            btn.pack(fill="x", pady=2)
            self.file_buttons[path] = btn
            
    def refresh_list_colors(self):
        for path, btn in self.file_buttons.items():
            if path == self.current_image_path:
                btn.configure(fg_color="#e84466", text_color="#fafafa")
            elif path in self.staged_changes and self.staged_changes[path]:
                btn.configure(fg_color="#7a3b1e", text_color="#f5c07a")
            else:
                btn.configure(fg_color="transparent", text_color="#fafafa")

    def load_image(self, path):
        if self.editing_disabled:
            return
        self.current_image_path = path
        self.refresh_list_colors()
        self.status_var.set(f"Loading metadata for {os.path.basename(path)}...")
        self.set_ui_state("disabled", visual=False)
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
        tags = ask_string(self, "Set Tags", "Enter tags separated by commas:")
        if tags is None: return
        
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

    def clear_all_batch(self):
        if not self.image_files: return
        if not ask_confirm(self, "Clear All Fields",
                           "Are you sure you want to clear ALL metadata fields from ALL images?\nThis cannot be undone."):
            return

        fields = list(self.form_vars.keys())
        if not fields: return

        # Visually clear the form
        self._is_populating = True
        for k in fields:
            self.form_vars[k].set("")
        self._is_populating = False

        # Clear staged changes for all images
        self.staged_changes.clear()
        self.refresh_list_colors()

        # Immediately write clears to disk for every image
        self.set_ui_state("disabled")
        self.status_var.set(f"Clearing metadata from {len(self.image_files)} images...")
        worker = ExifWorker('batch_clear', self.image_files, self.worker_callback,
                            clear_fields=fields, inplace=self.inplace_mode)
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
                    show_message(self, "Error", res['message'], error=True)
                    self.status_var.set("Error occurred.")
                    self.progress_bar.grid_remove()
                    self.set_ui_state("normal", visual=(res.get('mode') != 'read'))
                elif res['status'] == 'progress':
                    self.status_var.set(f"Processing {res['current']}/{res['total']}...")
                    if not self.progress_bar.winfo_viewable():
                        self.progress_bar.grid()
                    self.progress_bar.set(res['current'] / max(1, res['total']))
                elif res['status'] == 'success':
                    self.progress_bar.grid_remove()
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
                    self.set_ui_state("normal", visual=(res['mode'] != 'read'))
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

    def set_ui_state(self, state, visual=True):
        self.editing_disabled = (state == "disabled")
        if visual:
            for btn in [self.btn_open, self.btn_filenames, self.btn_tags, self.btn_save_all,
                        self.btn_clear, self.btn_map,
                        self.btn_save_template, self.btn_apply_template, self.btn_manage_templates,
                        self.check_inplace]:
                btn.configure(state=state)

    # ── Settings / Update checker ─────────────────────────────────────────────

    def show_settings_dialog(self):
        """Open the Settings popover with version info and an update checker."""
        dlg, content = _make_themed_dialog(self, "Settings", 400, 240)

        # Version row
        ver_row = ctk.CTkFrame(content, fg_color="transparent")
        ver_row.pack(fill="x", padx=24, pady=(20, 4))
        ctk.CTkLabel(ver_row, text="Version:",
                     font=ctk.CTkFont(weight="bold"),
                     text_color="#8f8599").pack(side="left")
        ctk.CTkLabel(ver_row, text=f"  {APP_VERSION}",
                     text_color="#fafafa").pack(side="left")

        # Status label (reused during update check)
        status_var = ctk.StringVar(value="")
        status_lbl = ctk.CTkLabel(content, textvariable=status_var,
                                  wraplength=360, text_color="#8f8599",
                                  font=ctk.CTkFont(size=12))
        status_lbl.pack(padx=24, pady=(0, 8), anchor="w")

        # Check for Update button
        btn_check = ctk.CTkButton(
            content, text="🔄  Check for Update", width=180,
            fg_color="#2d2540", hover_color="#3d3554",
            command=lambda: self._check_for_update(status_var, btn_check, dlg),
        )
        btn_check.pack(padx=24, anchor="w")

        # GitHub link
        link_row = ctk.CTkFrame(content, fg_color="transparent")
        link_row.pack(fill="x", padx=24, pady=(16, 0))
        ctk.CTkLabel(link_row, text="GitHub:",
                     font=ctk.CTkFont(weight="bold"),
                     text_color="#8f8599").pack(side="left")
        gh_btn = ctk.CTkButton(
            link_row, text=f"  {GITHUB_URL}",
            fg_color="transparent", hover_color="#27212f",
            text_color="#e84466", anchor="w", font=ctk.CTkFont(size=12),
            command=lambda: webbrowser.open(GITHUB_URL),
        )
        gh_btn.pack(side="left")

    def _check_for_update(self, status_var: ctk.StringVar, btn: ctk.CTkButton, dlg):
        """Run the update check in a background thread and react on the main thread."""
        btn.configure(state="disabled", text="Checking…")
        status_var.set("Contacting GitHub…")

        def _worker():
            try:
                tag, exe_url = updater.fetch_latest_release()
                if updater.is_newer(tag):
                    # Newer version found
                    self.after(0, lambda: self._offer_update(tag, exe_url, status_var, btn, dlg))
                else:
                    self.after(0, lambda: [
                        status_var.set(f"✅  You are up to date  (v{APP_VERSION})"),
                        btn.configure(state="normal", text="🔄  Check for Update"),
                    ])
            except Exception as exc:
                msg = str(exc)
                self.after(0, lambda: [
                    status_var.set(f"⚠️  {msg}"),
                    btn.configure(state="normal", text="🔄  Check for Update"),
                ])

        threading.Thread(target=_worker, daemon=True).start()

    def _offer_update(self, tag: str, exe_url, status_var: ctk.StringVar,
                      btn: ctk.CTkButton, settings_dlg):
        """Show an update-available prompt and handle download + relaunch."""
        btn.configure(state="normal", text="🔄  Check for Update")
        status_var.set(f"🆕  New version available: {tag}")

        if not exe_url:
            # No EXE asset — just point to the releases page
            if ask_confirm(self, "Update Available",
                           f"Version {tag} is available.\n"
                           "No installer asset found. Open the Releases page?"):
                webbrowser.open(f"https://github.com/AHJ32/LeoSetter/releases/latest")
            return

        if not ask_confirm(self, "Update Available",
                           f"Version {tag} is available.\n"
                           "Download and install now? The app will restart automatically."):
            return

        settings_dlg.destroy()

        # ── Download in background with progress ──────────────────────────────
        prog_dlg, prog_content = _make_themed_dialog(self, "Downloading Update", 420, 160)
        prog_var = ctk.StringVar(value="Starting download…")
        ctk.CTkLabel(prog_content, textvariable=prog_var,
                     wraplength=380).pack(padx=24, pady=(20, 8), anchor="w")
        prog_bar = ctk.CTkProgressBar(prog_content, width=380, mode="determinate")
        prog_bar.pack(padx=24, pady=(0, 16))
        prog_bar.set(0)

        def _on_progress(done, total):
            if total > 0:
                frac = done / total
                pct  = int(frac * 100)
                mb_done  = done  / (1024 * 1024)
                mb_total = total / (1024 * 1024)
                self.after(0, lambda f=frac, p=pct, d=mb_done, t=mb_total: [
                    prog_bar.set(f),
                    prog_var.set(f"Downloading… {d:.1f} MB / {t:.1f} MB  ({p}%)"),
                ])

        def _download_worker():
            try:
                path = updater.download_update(exe_url, progress_callback=_on_progress)
                self.after(0, lambda: _launch(path))
            except Exception as exc:
                err = str(exc)
                self.after(0, lambda: [
                    prog_dlg.destroy(),
                    show_message(self, "Download Failed",
                                 f"Could not download update:\n{err}", error=True),
                ])

        def _launch(path: str):
            prog_dlg.destroy()
            show_message(self, "Launching Installer",
                         "The installer will now open. LeoSetter will close.")
            updater.launch_installer(path)

        threading.Thread(target=_download_worker, daemon=True).start()

    def pick_on_map(self):
        lat_str = self.form_vars.get("GPSLatitude", ctk.StringVar()).get()
        lon_str = self.form_vars.get("GPSLongitude", ctk.StringVar()).get()
        
        try:
            lat = xb.parse_decimal_or_dms(lat_str) if lat_str else 0.0
            lon = xb.parse_decimal_or_dms(lon_str) if lon_str else 0.0
            if lat == 0.0 and lon == 0.0:
                lat, lon = self.settings.get("map_lat", 0.0), self.settings.get("map_lon", 0.0)
        except ValueError:
            lat, lon = self.settings.get("map_lat", 0.0), self.settings.get("map_lon", 0.0)
            
        new_lat, new_lon, ok = MapPickerDialog.get_location(self, lat, lon)
        if ok:
            self.settings["map_lat"] = new_lat
            self.settings["map_lon"] = new_lon
            if "GPSLatitude" in self.form_vars:
                self.form_vars["GPSLatitude"].set(str(new_lat))
            if "GPSLongitude" in self.form_vars:
                self.form_vars["GPSLongitude"].set(str(new_lon))
            self.on_field_edited("GPSLatitude")
            self.on_field_edited("GPSLongitude")

    def toggle_inplace(self):
        self.inplace_mode = self.inplace_var.get()

    def save_template_dialog(self):
        name = ask_string(self, "Save Template", "Enter template name:")
        if not name: return
        payload = self.current_payload()
        if not payload:
            show_message(self, "Error", "No non-empty fields to save.", error=True)
            return
        templates = xb.load_templates()
        templates[name] = payload
        xb.save_templates(templates)
        self.status_var.set(f"Template '{name}' saved.")

    def apply_template_dialog(self):
        templates = xb.load_templates()
        if not templates:
            show_message(self, "Templates", "No templates found.")
            return
        
        dlg, dlg_content = _make_themed_dialog(self, "Apply Template", 300, 420)

        ctk.CTkLabel(dlg_content, text="Select a template:").pack(pady=10)
        
        listbox = ctk.CTkScrollableFrame(dlg_content)
        listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        selected_var = ctk.StringVar()
        for tname in templates.keys():
            rb = ctk.CTkRadioButton(listbox, text=tname, variable=selected_var, value=tname)
            rb.pack(anchor="w", pady=2)
            
        def on_apply():
            tname = selected_var.get()
            if tname and tname in templates:
                payload = templates[tname]
                
                self._is_populating = True
                for path in self.image_files:
                    if path not in self.staged_changes:
                        self.staged_changes[path] = {}
                    for k, v in payload.items():
                        self.staged_changes[path][k] = v
                        
                if self.current_image_path:
                    for k, v in payload.items():
                        if k in self.form_vars:
                            self.form_vars[k].set(v)
                            
                self._is_populating = False
                self.refresh_list_colors()
                
                self.status_var.set(f"Applied template '{tname}' to all images.")
                dlg.destroy()
                
        ctk.CTkButton(dlg_content, text="Apply", command=on_apply).pack(pady=10)

    def manage_templates_dialog(self):
        templates = xb.load_templates()
        if not templates:
            show_message(self, "Templates", "No templates found.")
            return
            
        dlg, dlg_content = _make_themed_dialog(self, "Manage Templates", 400, 420)
        
        ctk.CTkLabel(dlg_content, text="Existing templates:").pack(pady=10)
        
        listbox = ctk.CTkScrollableFrame(dlg_content)
        listbox.pack(fill="both", expand=True, padx=10, pady=5)
        
        for tname in list(templates.keys()):
            frame = ctk.CTkFrame(listbox, fg_color="transparent")
            frame.pack(fill="x", pady=2)
            ctk.CTkLabel(frame, text=tname).pack(side="left")
            def delete_t(n=tname, f=frame):
                del templates[n]
                xb.save_templates(templates)
                f.destroy()
                self.status_var.set(f"Deleted template '{n}'.")
            ctk.CTkButton(frame, text="Delete", fg_color="#ef4444", hover_color="#c53030", text_color="#fafafa", width=60, command=delete_t).pack(side="right")
            
    def on_closing(self):
        self.settings["geometry"] = self.geometry()
        self.settings["last_folder"] = self.folder_path
        save_settings(self.settings)
        self.destroy()
