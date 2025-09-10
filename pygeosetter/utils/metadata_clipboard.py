"""
Clipboard functionality for copying and pasting metadata between images.
"""
from PyQt5.QtWidgets import QApplication, QMessageBox
from PyQt5.QtCore import QMimeData, Qt
import json

class MetadataClipboard:
    """Handles copying and pasting of image metadata between views"""
    
    # MIME type for our custom metadata format
    MIME_TYPE = "application/x-pygeosetter-metadata"
    
    @staticmethod
    def get_metadata_from_image(image_widget):
        """Extract metadata from an image widget"""
        if not image_widget or not hasattr(image_widget, 'exif_data'):
            return None
            
        return {
            'gps': image_widget.exif_data.get('gps', {}),
            'exif': {
                'datetime_original': image_widget.exif_data.get('exif', {}).get('DateTimeOriginal', ''),
                'datetime_digitized': image_widget.exif_data.get('exif', {}).get('DateTimeDigitized', ''),
                'make': image_widget.exif_data.get('exif', {}).get('Make', ''),
                'model': image_widget.exif_data.get('exif', {}).get('Model', ''),
            },
            'iptc': {
                'headline': image_widget.exif_data.get('iptc', {}).get('Headline', ''),
                'caption': image_widget.exif_data.get('iptc', {}).get('Caption/Abstract', ''),
                'keywords': image_widget.exif_data.get('iptc', {}).get('Keywords', []),
            },
            'xmp': {
                'title': image_widget.exif_data.get('xmp', {}).get('Title', ''),
                'creator': image_widget.exif_data.get('xmp', {}).get('Creator', ''),
                'description': image_widget.exif_data.get('xmp', {}).get('Description', ''),
                'rights': image_widget.exif_data.get('xmp', {}).get('Rights', ''),
            },
            'location': {
                'latitude': image_widget.lat,
                'longitude': image_widget.lon,
                'altitude': image_widget.altitude,
                'country': image_widget.exif_data.get('iptc', {}).get('Country/PrimaryLocationName', ''),
                'state': image_widget.exif_data.get('iptc', {}).get('Province/State', ''),
                'city': image_widget.exif_data.get('iptc', {}).get('City', ''),
                'sublocation': image_widget.exif_data.get('iptc', {}).get('Sub-location', ''),
            },
            'creator': {
                'name': image_widget.exif_data.get('xmp', {}).get('Creator', ''),
                'title': image_widget.exif_data.get('xmp', {}).get('CreatorJobTitle', ''),
                'website': image_widget.exif_data.get('xmp', {}).get('WebStatement', ''),
                'email': image_widget.exif_data.get('xmp', {}).get('CreatorWorkEmail', ''),
                'phone': image_widget.exif_data.get('xmp', {}).get('CreatorWorkPhone', ''),
                'address': image_widget.exif_data.get('xmp', {}).get('CreatorWorkAddress', ''),
                'postal_code': image_widget.exif_data.get('xmp', {}).get('CreatorWorkPostalCode', ''),
            },
            'copyright': {
                'notice': image_widget.exif_data.get('xmp', {}).get('Rights', ''),
                'usage_terms': image_widget.exif_data.get('xmp', {}).get('UsageTerms', ''),
                'copyright_status': image_widget.exif_data.get('xmp', {}).get('CopyrightStatus', ''),
            }
        }
    
    @staticmethod
    def copy_metadata(image_widget):
        """Copy metadata from an image widget to the clipboard"""
        metadata = MetadataClipboard.get_metadata_from_image(image_widget)
        if not metadata:
            return False
            
        mime_data = QMimeData()
        mime_data.setData(MetadataClipboard.MIME_TYPE, json.dumps(metadata).encode('utf-8'))
        
        clipboard = QApplication.clipboard()
        clipboard.setMimeData(mime_data)
        return True
    
    @staticmethod
    def paste_metadata(target_widget, paste_options=None):
        """
        Paste metadata to a target widget
        
        Args:
            target_widget: The widget to paste metadata to
            paste_options: Dict specifying which metadata to paste, e.g.:
                {
                    'gps': True,
                    'datetime': True,
                    'location': True,
                    'creator': True,
                    'copyright': True,
                    'keywords': False
                }
        """
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        
        if not mime_data.hasFormat(MetadataClipboard.MIME_TYPE):
            return False
            
        try:
            metadata = json.loads(mime_data.data(MetadataClipboard.MIME_TYPE).data().decode('utf-8'))
            
            # Default options: paste everything if not specified
            if paste_options is None:
                paste_options = {
                    'gps': True,
                    'datetime': True,
                    'location': True,
                    'creator': True,
                    'copyright': True,
                    'keywords': True
                }
            
            # Apply metadata based on options
            if paste_options.get('gps', True) and 'gps' in metadata:
                target_widget.exif_data.setdefault('gps', {}).update(metadata['gps'])
                
            if paste_options.get('datetime', True) and 'exif' in metadata:
                target_widget.exif_data.setdefault('exif', {}).update({
                    k: v for k, v in metadata['exif'].items() 
                    if v and k in ['DateTimeOriginal', 'DateTimeDigitized']
                })
            
            if paste_options.get('location', True) and 'location' in metadata:
                loc = metadata['location']
                if 'latitude' in loc and 'longitude' in loc:
                    target_widget.lat = loc['latitude']
                    target_widget.lon = loc['longitude']
                    target_widget.altitude = loc.get('altitude', 0)
                    
                    # Update map if available
                    if hasattr(target_widget, 'update_map_location'):
                        target_widget.update_map_location()
                
                # Update location fields
                iptc = target_widget.exif_data.setdefault('iptc', {})
                for field in ['country', 'state', 'city', 'sublocation']:
                    if field in loc and loc[field]:
                        iptc[{
                            'country': 'Country/PrimaryLocationName',
                            'state': 'Province/State',
                            'city': 'City',
                            'sublocation': 'Sub-location'
                        }[field]] = loc[field]
            
            if paste_options.get('creator', True) and 'creator' in metadata:
                xmp = target_widget.exif_data.setdefault('xmp', {})
                creator = metadata['creator']
                
                if creator.get('name'):
                    xmp['Creator'] = creator['name']
                if creator.get('title'):
                    xmp['CreatorJobTitle'] = creator['title']
                if creator.get('website'):
                    xmp['WebStatement'] = creator['website']
                if creator.get('email'):
                    xmp['CreatorWorkEmail'] = creator['email']
                if creator.get('phone'):
                    xmp['CreatorWorkPhone'] = creator['phone']
                if creator.get('address'):
                    xmp['CreatorWorkAddress'] = creator['address']
                if creator.get('postal_code'):
                    xmp['CreatorWorkPostalCode'] = creator['postal_code']
            
            if paste_options.get('copyright', True) and 'copyright' in metadata:
                xmp = target_widget.exif_data.setdefault('xmp', {})
                copyright_data = metadata['copyright']
                
                if copyright_data.get('notice'):
                    xmp['Rights'] = copyright_data['notice']
                if copyright_data.get('usage_terms'):
                    xmp['UsageTerms'] = copyright_data['usage_terms']
                if copyright_data.get('copyright_status'):
                    xmp['CopyrightStatus'] = copyright_data['copyright_status']
            
            if paste_options.get('keywords', True) and 'iptc' in metadata and 'Keywords' in metadata['iptc']:
                target_widget.exif_data.setdefault('iptc', {})['Keywords'] = metadata['iptc']['Keywords']
            
            # Update the UI
            if hasattr(target_widget, 'update_exif_display'):
                target_widget.update_exif_display()
                
            return True
            
        except Exception as e:
            QMessageBox.warning(
                None,
                "Paste Error",
                f"Failed to paste metadata: {str(e)}"
            )
            return False

    @staticmethod
    def has_metadata():
        """Check if the clipboard contains metadata"""
        clipboard = QApplication.clipboard()
        mime_data = clipboard.mimeData()
        return mime_data.hasFormat(MetadataClipboard.MIME_TYPE)
