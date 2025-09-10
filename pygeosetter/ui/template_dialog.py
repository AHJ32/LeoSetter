"""
Template management dialog for PyGeoSetter
"""
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem,
    QPushButton, QGroupBox, QFormLayout, QLineEdit, QTextEdit,
    QLabel, QMessageBox, QDialogButtonBox, QDoubleSpinBox, QSplitter
)
from PyQt5.QtCore import Qt, pyqtSignal
from ..templates.location_template import LocationTemplateManager
from .map_widget import MapWidget

class TemplateDialog(QDialog):
    """Dialog for managing location templates"""
    template_selected = pyqtSignal(dict)
    
    def __init__(self, template_manager, parent=None):
        super().__init__(parent)
        self.template_manager = template_manager
        self.current_template = None
        self.init_ui()
        self.load_templates()
    
    def init_ui(self):
        """Initialize the UI"""
        self.setWindowTitle("Location Templates")
        layout = QVBoxLayout(self)
        
        # Template list
        self.template_list = QListWidget()
        self.template_list.itemSelectionChanged.connect(self.template_selected_slot)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.new_btn = QPushButton("New")
        self.edit_btn = QPushButton("Edit")
        self.delete_btn = QPushButton("Delete")
        self.new_btn.clicked.connect(self.new_template)
        self.edit_btn.clicked.connect(self.edit_template)
        self.delete_btn.clicked.connect(self.delete_template)
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.edit_btn)
        btn_layout.addWidget(self.delete_btn)
        
        # Create a splitter for the template form and map
        splitter = QSplitter(Qt.Horizontal)
        
        # Left side - Template details
        details_group = QGroupBox("Template Details")
        details_layout = QFormLayout()
        
        # Basic Information
        self.name_edit = QLineEdit()
        self.title_edit = QLineEdit()
        self.description_edit = QTextEdit()
        self.description_edit.setMaximumHeight(60)
        
        # Location
        self.country_edit = QLineEdit()
        self.state_edit = QLineEdit()
        self.city_edit = QLineEdit()
        self.sublocation_edit = QLineEdit()
        
        # Coordinates
        self.lat_edit = QDoubleSpinBox()
        self.lat_edit.setRange(-90, 90)
        self.lat_edit.setDecimals(6)
        self.lon_edit = QDoubleSpinBox()
        self.lon_edit.setRange(-180, 180)
        self.lon_edit.setDecimals(6)
        
        # Add fields to layout with sections
        details_layout.addRow(QLabel("<b>Basic Information</b>"))
        details_layout.addRow("Name*:", self.name_edit)
        details_layout.addRow("Title:", self.title_edit)
        details_layout.addRow("Description:", self.description_edit)
        
        details_layout.addRow(QLabel("<b>Location</b>"))
        details_layout.addRow("Country:", self.country_edit)
        details_layout.addRow("State/Province:", self.state_edit)
        details_layout.addRow("City:", self.city_edit)
        details_layout.addRow("Sublocation:", self.sublocation_edit)
        
        details_layout.addRow(QLabel("<b>Coordinates</b>"))
        details_layout.addRow("Latitude*:", self.lat_edit)
        details_layout.addRow("Longitude*:", self.lon_edit)
        
        details_group.setLayout(details_layout)
        
        # Right side - Map
        map_group = QGroupBox("Location Map")
        map_layout = QVBoxLayout()
        
        # Create the map widget
        self.map_widget = MapWidget()
        self.map_widget.setMinimumSize(400, 300)
        
        # Connect map signals
        self.map_widget.location_changed.connect(self.update_coordinates_from_map)
        
        # Connect coordinate changes to update the map
        self.lat_edit.valueChanged.connect(self.update_map_from_coordinates)
        self.lon_edit.valueChanged.connect(self.update_map_from_coordinates)
        
        map_layout.addWidget(self.map_widget)
        map_group.setLayout(map_layout)
        
        # Add both sides to the splitter
        splitter.addWidget(details_group)
        splitter.addWidget(map_group)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
        # Template list group
        template_list_group = QGroupBox("Saved Templates")
        template_list_layout = QVBoxLayout()
        template_list_layout.addWidget(self.template_list)
        template_list_group.setLayout(template_list_layout)
        
        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.Ok | QDialogButtonBox.Cancel | QDialogButtonBox.Save
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.Save).clicked.connect(self.save_template)
        
        # Add widgets to main layout
        main_layout = QHBoxLayout()
        main_layout.addWidget(template_list_group, 1)
        main_layout.addWidget(splitter, 2)
        
        layout.addLayout(btn_layout)
        layout.addLayout(main_layout)
        layout.addWidget(button_box)
    
    def load_templates(self):
        """Load templates into the list"""
        self.template_list.clear()
        for name in sorted(self.template_manager.templates.keys()):
            self.template_list.addItem(name)
    
    def update_coordinates_from_map(self, lat, lon):
        """Update coordinate fields when map location changes"""
        # Block signals to prevent infinite loop
        self.lat_edit.blockSignals(True)
        self.lon_edit.blockSignals(True)
        
        self.lat_edit.setValue(lat)
        self.lon_edit.setValue(lon)
        
        # Re-enable signals
        self.lat_edit.blockSignals(False)
        self.lon_edit.blockSignals(False)
    
    def update_map_from_coordinates(self):
        """Update map when coordinate fields change"""
        try:
            lat = self.lat_edit.value()
            lon = self.lon_edit.value()
            self.map_widget.set_location(lat, lon)
        except (ValueError, AttributeError):
            pass
    
    def template_selected_slot(self):
        """Handle template selection"""
        selected = self.template_list.currentItem()
        if not selected:
            return
            
        template = self.template_manager.templates[selected.text()]
        self.current_template = template['name']
        
        # Basic Info
        self.name_edit.setText(template.get('name', ''))
        self.title_edit.setText(template.get('title', ''))
        self.description_edit.setPlainText(template.get('description', ''))
        
        # Location
        self.country_edit.setText(template.get('country', ''))
        self.state_edit.setText(template.get('state', ''))
        self.city_edit.setText(template.get('city', ''))
        self.sublocation_edit.setText(template.get('sublocation', ''))
        
        # Coordinates
        if 'latitude' in template and 'longitude' in template:
            lat = template['latitude']
            lon = template['longitude']
            
            # Block signals to prevent multiple updates
            self.lat_edit.blockSignals(True)
            self.lon_edit.blockSignals(True)
            
            self.lat_edit.setValue(lat)
            self.lon_edit.setValue(lon)
            
            # Update the map
            self.map_widget.set_location(lat, lon)
            
            # Re-enable signals
            self.lat_edit.blockSignals(False)
            self.lon_edit.blockSignals(False)
        
        # Creator
        self.creator_edit.setText(template.get('creator', ''))
        self.creator_title_edit.setText(template.get('creator_title', ''))
        self.creator_website_edit.setText(template.get('creator_website', ''))
        self.creator_email_edit.setText(template.get('creator_email', ''))
        self.creator_phone_edit.setText(template.get('creator_phone', ''))
        self.creator_address_edit.setPlainText(template.get('creator_address', ''))
        self.creator_postal_code_edit.setText(template.get('creator_postal_code', ''))
        
        # Copyright
        self.copyright_edit.setText(template.get('copyright', ''))
        self.usage_terms_edit.setPlainText(template.get('usage_terms', ''))
    
    def clear_form(self):
        """Clear the template form with simplified fields"""
        self.current_template = None
        
        # Basic Info
        self.name_edit.clear()
        self.title_edit.clear()
        self.description_edit.clear()
        
        # Location
        self.country_edit.clear()
        self.state_edit.clear()
        self.city_edit.clear()
        self.sublocation_edit.clear()
        
        # Coordinates
        self.lat_edit.setValue(0)
        self.lon_edit.setValue(0)
        
        self.name_edit.setFocus()
    
    def new_template(self):
        """Create a new template"""
        self.clear_form()
    
    def edit_template(self):
        """Edit selected template"""
        if not self.template_list.currentItem():
            return
        self.template_selected_slot()
    
    def delete_template(self):
        """Delete selected template"""
        selected = self.template_list.currentItem()
        if not selected:
            return
            
        name = selected.text()
        if QMessageBox.question(
            self, "Delete Template",
            f"Delete template '{name}'?",
            QMessageBox.Yes | QMessageBox.No
        ) == QMessageBox.Yes:
            self.template_manager.delete_template(name)
            self.load_templates()
    
    def save_template(self):
        """Save the current template with simplified fields"""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Template name cannot be empty")
            return
            
        template = {
            # Basic Info
            'name': name,
            'title': self.title_edit.text(),
            'description': self.description_edit.toPlainText(),
            
            # Location
            'country': self.country_edit.text(),
            'state': self.state_edit.text(),
            'city': self.city_edit.text(),
            'sublocation': self.sublocation_edit.text(),
            
            # Coordinates
            'latitude': self.lat_edit.value(),
            'longitude': self.lon_edit.value()
        }
        
        if self.template_manager.save_template(**template):
            self.load_templates()
    
    def accept(self):
        """Handle dialog acceptance"""
        selected = self.template_list.currentItem()
        if selected:
            template = self.template_manager.templates[selected.text()]
            self.template_selected.emit(template)
        super().accept()
