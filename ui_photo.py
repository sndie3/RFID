from PyQt5.QtWidgets import QLabel, QMenu, QFileDialog, QMessageBox
from PyQt5.QtCore import pyqtSignal, Qt
from PyQt5.QtGui import QPixmap, QCursor
import base64

class PhotoWidget(QLabel):
    photo_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        self.setMinimumSize(100, 100)
        self.setAlignment(Qt.AlignCenter)
        self.setStyleSheet("""
            QLabel {
                border: 1px solid #cccccc;
                border-radius: 5px;
                background-color: #ffffff;
                color: #888888;
                font-size: 12px;
            }
        """)
        self.setText("Click to add\nphoto")
        self.photo_data = None
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.show_photo_options()
    
    def show_photo_options(self):
        menu = QMenu()
        upload_action = menu.addAction("📁 Upload Photo")
        camera_action = menu.addAction("📷 Take Photo")
        clear_action = menu.addAction("🗑️ Clear Photo")
        
        action = menu.exec_(QCursor.pos())
        
        if action == upload_action:
            self.upload_photo()
        elif action == camera_action:
            self.capture_photo()
        elif action == clear_action:
            self.clear_photo()
    
    def upload_photo(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Photo", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif)"
        )
        if file_path:
            self.load_photo(file_path)
    
    def capture_photo(self):
        QMessageBox.information(self, "Camera", "Camera capture would be implemented here.\nFor now, please use 'Upload Photo'.")
    
    def load_photo(self, file_path):
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            with open(file_path, 'rb') as f:
                self.photo_data = base64.b64encode(f.read()).decode()
            self.photo_changed.emit()
    
    def clear_photo(self):
        self.clear()
        self.setText("Click to add\nphoto")
        self.photo_data = None
        self.photo_changed.emit()
    
    def get_photo_data(self):
        return self.photo_data
    
    def set_photo_data(self, photo_data):
        if photo_data:
            try:
                image_data = base64.b64decode(photo_data)
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.setPixmap(scaled_pixmap)
                self.photo_data = photo_data
            except Exception as e:
                print(f"Error loading photo: {e}") 