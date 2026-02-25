import customtkinter as ctk
import tkintermapview
from tkinter import messagebox

class MapPickerDialog(ctk.CTkToplevel):
    def __init__(self, parent=None, start_lat: float = 0.0, start_lon: float = 0.0):
        super().__init__(parent)
        self.title("Pick Location on Map")
        self.geometry("900x600")
        
        # Make it modal if parent is provided
        if parent:
            self.transient(parent)
            self.grab_set()

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
        
        self.btn_cancel = ctk.CTkButton(self.btn_frame, text="Cancel", command=self.cancel, width=120, fg_color="transparent", border_width=1, text_color=("gray10", "gray90"))
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
                    messagebox.showwarning("Not Found", f"Could not find '{query}'")
            except Exception as e:
                messagebox.showerror("Search Error", f"An error occurred: {str(e)}")

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
            self.destroy()
        else:
            messagebox.showwarning("Error", "Please select a location on the map first.")
            
    def cancel(self):
        self.lat = None
        self.lon = None
        self.destroy()

    @staticmethod
    def get_location(parent=None, start_lat: float = 0.0, start_lon: float = 0.0):
        dlg = MapPickerDialog(parent, start_lat, start_lon)
        # Wait for dialog to close
        if parent:
            parent.wait_window(dlg)
        else:
            dlg.wait_window()
            
        ok = dlg.lat is not None and dlg.lon is not None
        return (dlg.lat, dlg.lon, ok)
