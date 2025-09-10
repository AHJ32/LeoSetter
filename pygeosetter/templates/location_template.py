"""
Location template management for PyGeoSetter
"""
import os
import json
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QMessageBox, QInputDialog, QMenu, QAction

class LocationTemplateManager(QObject):
    """Manages location templates for quick access"""
    
    template_updated = pyqtSignal()
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.templates_dir = os.path.join(os.path.expanduser('~'), '.pygeosetter', 'templates')
        self.templates = {}
        self.current_template = None
        
        # Create templates directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Load existing templates
        self.load_templates()
    
    def load_templates(self):
        """Load all saved templates from disk"""
        self.templates.clear()
        
        if not os.path.exists(self.templates_dir):
            return
        
        for filename in os.listdir(self.templates_dir):
            if filename.endswith('.json'):
                try:
                    with open(os.path.join(self.templates_dir, filename), 'r') as f:
                        template_data = json.load(f)
                        template_name = os.path.splitext(filename)[0]
                        self.templates[template_name] = template_data
                except Exception as e:
                    print(f"Error loading template {filename}: {e}")
        
        self.template_updated.emit()
    
    def save_template(self, name, latitude, longitude, altitude=0, description='', tags=None, 
                     title='', country='', state='', city='', sublocation='',
                     creator='', creator_title='', creator_website='', creator_email='',
                     creator_phone='', creator_address='', creator_postal_code='',
                     copyright='', usage_terms=''):
        """Save a new template or update an existing one"""
        if not name:
            QMessageBox.warning(self.app, "Error", "Template name cannot be empty")
            return False
        
        template_data = {
            # Basic Info
            'name': name,
            'title': title,
            'description': description,
            'tags': tags or [],
            
            # Location
            'country': country,
            'state': state,
            'city': city,
            'sublocation': sublocation,
            
            # Coordinates
            'latitude': latitude,
            'longitude': longitude,
            'altitude': altitude,
            
            # Creator
            'creator': creator,
            'creator_title': creator_title,
            'creator_website': creator_website,
            'creator_email': creator_email,
            'creator_phone': creator_phone,
            'creator_address': creator_address,
            'creator_postal_code': creator_postal_code,
            
            # Copyright
            'copyright': copyright,
            'usage_terms': usage_terms
        }
        
        # Save to file
        filename = os.path.join(self.templates_dir, f"{name}.json")
        try:
            with open(filename, 'w') as f:
                json.dump(template_data, f, indent=2)
            
            # Update in-memory cache
            self.templates[name] = template_data
            self.current_template = name
            self.template_updated.emit()
            return True
            
        except Exception as e:
            QMessageBox.critical(self.app, "Error", f"Failed to save template: {e}")
            return False
    
    def delete_template(self, name):
        """Delete a template"""
        if name not in self.templates:
            return False
        
        try:
            # Delete file
            filename = os.path.join(self.templates_dir, f"{name}.json")
            if os.path.exists(filename):
                os.remove(filename)
            
            # Update in-memory cache
            del self.templates[name]
            if self.current_template == name:
                self.current_template = None
            
            self.template_updated.emit()
            return True
            
        except Exception as e:
            QMessageBox.critical(self.app, "Error", f"Failed to delete template: {e}")
            return False
    
    def get_template(self, name):
        """Get a template by name"""
        return self.templates.get(name)
    
    def get_template_names(self):
        """Get a list of all template names"""
        return sorted(self.templates.keys())
    
    def create_template_menu(self, parent, callback):
        """Create a menu with all templates"""
        menu = QMenu("Templates", parent)
        
        if not self.templates:
            no_templates = menu.addAction("No templates available")
            no_templates.setEnabled(False)
            return menu
        
        # Add templates to menu
        for name in sorted(self.templates.keys()):
            action = menu.addAction(name)
            action.triggered.connect(lambda checked, n=name: callback(n))
        
        return menu
    
    def show_save_template_dialog(self, latitude, longitude, altitude=0, parent=None):
        """Show dialog to save current location as a template"""
        from PyQt5.QtWidgets import QDialog, QVBoxLayout, QFormLayout, QDialogButtonBox, QLineEdit, QTextEdit
        
        dialog = QDialog(parent or self.app)
        dialog.setWindowTitle("Save Location Template")
        layout = QVBoxLayout()
        
        # Form layout for template details
        form_layout = QFormLayout()
        
        # Basic Info
        name_edit = QLineEdit(f"Location at {latitude:.6f}, {longitude:.6f}")
        title_edit = QLineEdit()
        description_edit = QTextEdit()
        description_edit.setMaximumHeight(60)
        
        # Location
        country_edit = QLineEdit()
        state_edit = QLineEdit()
        city_edit = QLineEdit()
        sublocation_edit = QLineEdit()
        
        # Add fields to form
        form_layout.addRow("Name*:", name_edit)
        form_layout.addRow("Title:", title_edit)
        form_layout.addRow("Description:", description_edit)
        form_layout.addRow("Country:", country_edit)
        form_layout.addRow("State/Province:", state_edit)
        form_layout.addRow("City:", city_edit)
        form_layout.addRow("Sublocation:", sublocation_edit)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        
        # Add widgets to layout
        layout.addLayout(form_layout)
        layout.addWidget(button_box)
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            name = name_edit.text().strip()
            if not name:
                QMessageBox.warning(dialog, "Error", "Template name cannot be empty")
                return False
                
            return self.save_template(
                name=name,
                latitude=latitude,
                longitude=longitude,
                altitude=altitude,
                title=title_edit.text(),
                description=description_edit.toPlainText(),
                country=country_edit.text(),
                state=state_edit.text(),
                city=city_edit.text(),
                sublocation=sublocation_edit.text()
            )
        
        return False


class TemplateAction(QAction):
    """Action for a template in the template menu"""
    
    def __init__(self, template_data, parent=None):
        super().__init__(template_data['name'], parent)
        self.template_data = template_data
        
        # Set tooltip with additional info
        tooltip = f"Lat: {template_data['latitude']:.6f}, Lon: {template_data['longitude']:.6f}"
        if template_data.get('description'):
            tooltip = f"{template_data['description']}\n{tooltip}"
        self.setToolTip(tooltip)
