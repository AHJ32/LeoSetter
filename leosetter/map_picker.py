import customtkinter as ctk
import tkintermapview

def _make_themed_dialog(parent, title: str, width: int, height: int):
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

    parent.update_idletasks()
    x = parent.winfo_rootx() + (parent.winfo_width()  - width)  // 2
    y = parent.winfo_rooty() + (parent.winfo_height() - height) // 2
    dlg.geometry(f"{width}x{height}+{x}+{y}")

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

    dlg._dx = dlg._dy = 0
    def _start(e): dlg._dx, dlg._dy = e.x_root, e.y_root
    def _drag(e):
        dlg.geometry(f"+{dlg.winfo_x()+e.x_root-dlg._dx}+{dlg.winfo_y()+e.y_root-dlg._dy}")
        dlg._dx, dlg._dy = e.x_root, e.y_root
    title_bar.bind("<ButtonPress-1>", _start)
    title_bar.bind("<B1-Motion>",     _drag)

    content = ctk.CTkFrame(dlg, fg_color="#0e0b14", corner_radius=0)
    content.pack(fill="both", expand=True)
    return dlg, content

def _show_msg(parent, title: str, message: str, error: bool = False):
    dlg, content = _make_themed_dialog(parent, title, 420, 150)
    color = "#ef4444" if error else "#fafafa"
    ctk.CTkLabel(content, text=message, wraplength=380, justify="left",
                 text_color=color).pack(padx=20, pady=(20, 8), anchor="w")
    f = ctk.CTkFrame(content, fg_color="transparent")
    f.pack(padx=20, pady=(4, 16), anchor="e")
    ctk.CTkButton(f, text="OK", width=80, command=dlg.destroy).pack()
    parent.wait_window(dlg)


class MapPickerDialog(ctk.CTkFrame):
    def __init__(self, top, parent_content, start_lat: float = 0.0, start_lon: float = 0.0):
        super().__init__(parent_content, fg_color="#0e0b14", corner_radius=0)
        self.top = top
        self.pack(fill="both", expand=True)

        self.lat = None
        self.lon = None
        self.marker = None

        # Search bar
        self.search_frame = ctk.CTkFrame(self)
        self.search_frame.pack(fill="x", padx=10, pady=10)
        
        self.search_entry = ctk.CTkEntry(self.search_frame, placeholder_text="Search country or place...", width=300)
        self.search_entry.pack(side="left", padx=5)
        self.search_entry.bind("<Return>", self.search_place)
        
        self.search_btn = ctk.CTkButton(self.search_frame, text="Search", command=self.search_place, width=80)
        self.search_btn.pack(side="left", padx=5)

        # Map widget
        self.map_widget = tkintermapview.TkinterMapView(self, corner_radius=0)
        self.map_widget.pack(fill="both", expand=True, padx=10, pady=5)
        
        # Action buttons
        self.btn_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.btn_frame.pack(fill="x", padx=10, pady=10)
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Cancel", command=self.cancel, width=120,
                                        fg_color="transparent", border_width=1,
                                        border_color="#322b3c", text_color="#fafafa",
                                        hover_color="#27212f")
        self.btn_cancel.pack(side="right", padx=5)

        
        self.btn_ok = ctk.CTkButton(self.btn_frame, text="Use Location", command=self.accept, width=120)
        self.btn_ok.pack(side="right", padx=5)

        # Initialize map
        if start_lat or start_lon:
            self.map_widget.set_position(start_lat, start_lon)
            self.map_widget.set_zoom(8)
            self.set_marker(start_lat, start_lon)
        else:
            self.map_widget.set_position(20, 0)
            self.map_widget.set_zoom(2)
            
        self.map_widget.add_right_click_menu_command(label="Set Location", command=self.set_marker_from_menu, pass_coords=True)
        # Also let left click set the marker immediately
        self.map_widget.add_left_click_map_command(self.set_marker_from_click)

    def search_place(self, event=None):
        query = self.search_entry.get()
        if query:
            import geopy.geocoders
            try:
                geolocator = geopy.geocoders.Nominatim(user_agent="LeoSetterApp_v1_github")
                location = geolocator.geocode(query)
                if location:
                    self.lat = location.latitude
                    self.lon = location.longitude
                    
                    self.map_widget.set_position(self.lat, self.lon)
                    self.map_widget.set_zoom(10)
                    
                    self.map_widget.delete_all_marker()
                    self.set_marker(self.lat, self.lon)
                else:
                    _show_msg(self, "Not Found", f"Could not find '{query}'")
            except Exception as e:
                _show_msg(self, "Search Error", f"An error occurred: {str(e)}", error=True)

    def set_marker_from_menu(self, coords):
        self.set_marker(coords[0], coords[1])
        
    def set_marker_from_click(self, coords):
        self.set_marker(coords[0], coords[1])

    def set_marker(self, lat, lon):
        if self.marker:
            self.marker.delete()
        self.marker = self.map_widget.set_marker(lat, lon, text="Selected Location")
        self.lat = lat
        self.lon = lon

    def accept(self):
        if self.lat is not None and self.lon is not None:
            self.top.destroy()
        else:
            _show_msg(self.top, "No Location", "Please select a location on the map first.")
            
    def cancel(self):
        self.lat = None
        self.lon = None
        self.top.destroy()
        
    @classmethod
    def get_location(cls, parent, start_lat: float = 0.0, start_lon: float = 0.0):
        dlg, dlg_content = _make_themed_dialog(parent, "Pick Location on Map", 900, 600)
        picker = cls(dlg, dlg_content, start_lat, start_lon)
        parent.wait_window(dlg)
        if picker.lat is not None and picker.lon is not None:
            return picker.lat, picker.lon, True
        return 0.0, 0.0, False
