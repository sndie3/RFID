import sys
import sqlite3
import hashlib
import serial
import threading
import time
import os
import base64
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class SerialReader(QThread):
    card_detected = pyqtSignal(str)
    
    def __init__(self, port='COM3', baud_rate=9600):
        super().__init__()
        self.port = port
        self.baud_rate = baud_rate
        self.running = False
        self.serial_connection = None
    
    def run(self):
        try:
            self.serial_connection = serial.Serial(self.port, self.baud_rate, timeout=1)
            self.running = True
            
            while self.running:
                if self.serial_connection.in_waiting > 0:
                    card_id = self.serial_connection.readline().decode('utf-8').strip()
                    if card_id and len(card_id) > 0:
                        self.card_detected.emit(card_id)
                time.sleep(0.1)
                
        except serial.SerialException as e:
            print(f"Serial connection error: {e}")
        except Exception as e:
            print(f"Error in serial reader: {e}")
    
    def stop(self):
        self.running = False
        if self.serial_connection and self.serial_connection.is_open:
            self.serial_connection.close()
        self.wait()

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect('rfid_system.db')
        self.create_tables()
    
    def create_tables(self):
        cursor = self.conn.cursor()
        
        # Create admin table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS admin (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create RFID cards table (updated with new fields)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS rfid_cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT UNIQUE NOT NULL,
                first_name TEXT NOT NULL,
                last_name TEXT NOT NULL,
                role TEXT NOT NULL CHECK(role IN ('Student', 'Employee')),
                school_id TEXT,
                employee_id TEXT,
                phone_number TEXT,
                program TEXT NOT NULL,
                photo BLOB,
                status TEXT DEFAULT 'Active',
                registered_by TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create access log table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS access_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                card_id TEXT NOT NULL,
                full_name TEXT NOT NULL,
                role TEXT NOT NULL,
                status TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create default admin if doesn't exist
        cursor.execute("SELECT COUNT(*) FROM admin")
        if cursor.fetchone()[0] == 0:
            default_password = self.hash_password("admin123")
            cursor.execute("INSERT INTO admin (username, password) VALUES (?, ?)", 
                         ("admin", default_password))
        
        self.conn.commit()
    
    def hash_password(self, password):
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_admin(self, username, password):
        cursor = self.conn.cursor()
        hashed_password = self.hash_password(password)
        cursor.execute("SELECT * FROM admin WHERE username = ? AND password = ?", 
                      (username, hashed_password))
        return cursor.fetchone() is not None
    
    def add_rfid_card(self, card_data):
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                INSERT INTO rfid_cards (card_id, first_name, last_name, role, school_id, 
                                      employee_id, phone_number, program, photo, registered_by) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', card_data)
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
    
    def get_all_cards(self):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM rfid_cards ORDER BY created_at DESC")
        return cursor.fetchall()
    
    def update_card_status(self, card_id, status):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE rfid_cards SET status = ? WHERE card_id = ?", 
                      (status, card_id))
        self.conn.commit()
    
    def get_card_by_id(self, card_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM rfid_cards WHERE card_id = ?", (card_id,))
        return cursor.fetchone()
    
    def log_access(self, card_id, full_name, role, status):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO access_log (card_id, full_name, role, status, timestamp) 
            VALUES (?, ?, ?, ?, ?)
        ''', (card_id, full_name, role, status, datetime.now().strftime('%Y-%m-%d %H:%M:%S')))
        self.conn.commit()
    
    def get_access_log(self, limit=50):
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM access_log ORDER BY timestamp DESC LIMIT ?", (limit,))
        return cursor.fetchall()

    def delete_card(self, card_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM rfid_cards WHERE card_id = ?", (card_id,))
        self.conn.commit()

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('RFID Management System')
        # Remove fixed size for responsiveness
        # self.setFixedSize(450, 600)
        
        # Simple flat background colors for prototype
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0; /* Light gray background */
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #333333; /* Dark gray text */
                font-size: 14px;
            }
            QLineEdit {
                background-color: #ffffff; /* White background */
                border: 1px solid #cccccc; /* Light gray border */
                border-radius: 5px;
                padding: 8px 10px;
                font-size: 14px;
                color: #333; /* Dark gray text */
            }
            QLineEdit:focus {
                border: 1px solid #007bff; /* Blue border on focus */
            }
            QPushButton {
                background-color: #007bff; /* Blue button */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 14px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3; /* Darker blue on hover */
            }
            QPushButton:pressed {
                background-color: #004085; /* Even darker blue on pressed */
            }
        """)
        
        self.center()
        
        # Create layout
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(60, 60, 60, 60)
        
        # Title
        title = QLabel('Admin Login')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #333333; margin-bottom: 30px;")
        layout.addWidget(title)
        
        # Username
        username_label = QLabel('Username')
        username_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(username_label)
        
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText('Enter your username')
        layout.addWidget(self.username_edit)
        
        # Password
        password_label = QLabel('Password')
        password_label.setStyleSheet("font-weight: bold; margin-bottom: 5px; margin-top: 15px;")
        layout.addWidget(password_label)
        
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('Enter your password')
        layout.addWidget(self.password_edit)
        
        # Login button
        self.login_btn = QPushButton('Sign In')
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setStyleSheet(self.login_btn.styleSheet() + "margin-top: 20px;")
        layout.addWidget(self.login_btn)
        
        # Info label
        info_label = QLabel('Default: admin / admin123')
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.6); font-style: italic; margin-top: 20px;")
        layout.addWidget(info_label)
        
        self.setLayout(layout)
        
        # Connect Enter key to login
        self.username_edit.returnPressed.connect(self.login)
        self.password_edit.returnPressed.connect(self.login)
    
    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
    
    def login(self):
        username = self.username_edit.text().strip()
        password = self.password_edit.text()
        
        if not username or not password:
            QMessageBox.warning(self, 'Error', 'Please enter both username and password.')
            return
        
        if self.db.verify_admin(username, password):
            self.main_window = MainWindow(username)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, 'Login Failed', 'Invalid username or password.')
            self.password_edit.clear()

class PhotoWidget(QLabel):
    photo_changed = pyqtSignal()

    def __init__(self):
        super().__init__()
        # self.setFixedSize(150, 150) # Removed for responsiveness
        self.setMinimumSize(100, 100) # Set a minimum size
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
        # Simple camera capture dialog
        QMessageBox.information(self, "Camera", "Camera capture would be implemented here.\nFor now, please use 'Upload Photo'.")
    
    def load_photo(self, file_path):
        pixmap = QPixmap(file_path)
        if not pixmap.isNull():
            # Scale and set pixmap
            scaled_pixmap = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.setPixmap(scaled_pixmap)
            
            # Store photo data as base64
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

class MainWindow(QWidget):
    def __init__(self, admin_username):
        super().__init__()
        self.admin_username = admin_username
        self.db = DatabaseManager()
        self.serial_reader = None
        self.init_ui()
        self.setup_serial_connection()
    
    def init_ui(self):
        self.setWindowTitle('RFID Management System')
        # self.setGeometry(100, 100, 1400, 800) # Removed for responsiveness
        self.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QTabWidget::pane {
                border: 1px solid #dee2e6;
                border-radius: 8px;
                background-color: #f0f0f0; /* Light gray background */
            }
            QTabWidget::tab-bar {
                alignment: center;
            }
            QTabBar::tab {
                background-color: #e0e0e0; /* Light gray tab */
                border: 1px solid #cccccc;
                padding: 10px 20px;
                margin-right: 2px;
                border-top-left-radius: 5px;
                border-top-right-radius: 5px;
                font-weight: bold;
                color: #333333;
            }
            QTabBar::tab:selected {
                background-color: #007bff; /* Blue selected tab */
                color: white;
                border-bottom: none;
            }
            QTabBar::tab:hover:!selected {
                background-color: #d0d0d0; /* Slightly darker gray on hover */
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
                background-color: #ffffff; /* White background */
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
                color: #333333;
                font-size: 14px;
            }
            QLineEdit, QComboBox {
                background-color: #ffffff; /* White background */
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
                color: #333333;
            }
            QLineEdit:focus, QComboBox:focus {
                border-color: #007bff;

            }
            QPushButton {
                border: none;
                border-radius: 5px;
                padding: 10px 20px;
                font-size: 14px;
                font-weight: bold;
                cursor: hand;
            }
            QPushButton#primaryBtn {
                background-color: #007bff; /* Blue button */
                color: white;
            }
            QPushButton#primaryBtn:hover {
                background-color: #0056b3; /* Darker blue on hover */
            }
            QPushButton#successBtn {
                background-color: #28a745; /* Green button */
                color: white;
            }
            QPushButton#successBtn:hover {
                background-color: #218838; /* Darker green on hover */
            }
            QPushButton#dangerBtn {
                background-color: #dc3545; /* Red button */
                color: white;
            }
            QPushButton#dangerBtn:hover {
                background-color: #bd2130; /* Darker red on hover */
            }
            QTableWidget {
                gridline-color: #e0e0e0;
                background-color: #ffffff;
                alternate-background-color: #f8f8f8;
                border: 1px solid #cccccc;
                border-radius: 5px;
            }
            QTableWidget::item {
                padding: 10px;
                border-bottom: 1px solid #e0e0e0;
            }
            QHeaderView::section {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #495057, stop:1 #343a40);
                color: white;
                padding: 15px;
                border: none;
                font-weight: bold;
                font-size: 14px;
            }
            QTextEdit {
                background-color: white;
                border: 2px solid #e9ecef;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QTextEdit:focus {
                border-color: #007bff;
            }
        """)
        
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        
        # Header
        self.create_header(main_layout)
        
        # Tab widget
        self.tab_widget = QTabWidget()
        self.tab_widget.addTab(self.create_register_tab(), "📝 Register Card")
        self.tab_widget.addTab(self.create_manage_users_tab(), "👥 Manage Users")
        self.tab_widget.addTab(self.create_view_logs_tab(), "📊 View Logs")
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    
    def create_header(self, layout):
        header_widget = QWidget()
        header_widget.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea, stop:1 #764ba2);
                border-radius: 12px;
                padding: 20px;
            }
        """)
        header_widget.setFixedHeight(80)
        
        header_layout = QHBoxLayout()
        
        # Welcome message
        welcome_label = QLabel(f'Welcome back, {self.admin_username}! 👋')
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white;")
        
        # Serial status
        self.serial_status = QLabel('🔴 Serial: Disconnected')
        self.serial_status.setStyleSheet("font-size: 14px; color: white; font-weight: bold;")
        
        # Logout button
        logout_btn = QPushButton('🚪 Logout')
        logout_btn.setObjectName('dangerBtn')
        logout_btn.clicked.connect(self.logout)
        logout_btn.setFixedSize(120, 40)
        
        header_layout.addWidget(welcome_label)
        header_layout.addStretch()
        header_layout.addWidget(self.serial_status)
        header_layout.addWidget(logout_btn)
        
        header_widget.setLayout(header_layout)
        layout.addWidget(header_widget)
    
    def create_register_tab(self):
        widget = QWidget()
        layout = QHBoxLayout()
        layout.setSpacing(20)
        
        # Left panel - Registration form
        left_panel = QGroupBox('👤 User Registration')
        left_layout = QVBoxLayout()
        left_layout.setSpacing(15)
        
        # Card detection status
        self.card_status = QLabel('🔍 Waiting for RFID card...')
        self.card_status.setStyleSheet("font-size: 14px; color: #6c757d; font-style: italic; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
        left_layout.addWidget(self.card_status)
        
        # Card ID field
        left_layout.addWidget(QLabel('RFID Card ID:'))
        self.card_id_edit = QLineEdit()
        self.card_id_edit.setPlaceholderText('Scan card or enter manually')
        self.card_id_edit.setReadOnly(True)
        left_layout.addWidget(self.card_id_edit)
        
        # Manual entry button
        manual_btn = QPushButton('✏️ Manual Entry')
        manual_btn.setObjectName('primaryBtn')
        manual_btn.clicked.connect(self.toggle_manual_entry)
        left_layout.addWidget(manual_btn)
        
        # Photo widget
        photo_layout = QHBoxLayout()
        photo_layout.addWidget(QLabel('Photo:'))
        photo_layout.addStretch()
        left_layout.addLayout(photo_layout)
        
        self.photo_widget = PhotoWidget()
        photo_container = QHBoxLayout()
        photo_container.addWidget(self.photo_widget)
        photo_container.addStretch()
        left_layout.addLayout(photo_container)
        
        # Role selection
        left_layout.addWidget(QLabel('Role:'))
        self.role_combo = QComboBox()
        self.role_combo.addItems(['Student', 'Employee'])
        self.role_combo.currentTextChanged.connect(self.on_role_changed)
        left_layout.addWidget(self.role_combo)
        
        # Personal information
        left_layout.addWidget(QLabel('First Name:'))
        self.first_name_edit = QLineEdit()
        self.first_name_edit.setPlaceholderText('Enter first name')
        left_layout.addWidget(self.first_name_edit)
        
        left_layout.addWidget(QLabel('Last Name:'))
        self.last_name_edit = QLineEdit()
        self.last_name_edit.setPlaceholderText('Enter last name')
        left_layout.addWidget(self.last_name_edit)
        
        # Dynamic ID field
        self.id_label = QLabel('School ID:')
        left_layout.addWidget(self.id_label)
        self.id_edit = QLineEdit()
        self.id_edit.setPlaceholderText('Enter school ID number')
        left_layout.addWidget(self.id_edit)
        
        # Phone number
        left_layout.addWidget(QLabel('Phone Number:'))
        self.phone_edit = QLineEdit()
        self.phone_edit.setPlaceholderText('Enter phone number')
        left_layout.addWidget(self.phone_edit)
        
        # Program
        left_layout.addWidget(QLabel('Program:'))
        self.program_edit = QLineEdit()
        self.program_edit.setPlaceholderText('Enter program/department')
        left_layout.addWidget(self.program_edit)
        
        # Register button
        register_btn = QPushButton('✅ Register User')
        register_btn.setObjectName('successBtn')
        register_btn.clicked.connect(self.register_user)
        left_layout.addWidget(register_btn)
        
        left_layout.addStretch()
        left_panel.setLayout(left_layout)
        # left_panel.setMaximumWidth(400) # Removed for responsiveness
        
        # Right panel - Preview
        right_panel = QGroupBox('📋 Registration Preview')
        right_layout = QVBoxLayout()
        
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setPlaceholderText('Fill in the form to see registration preview...')
        self.preview_text.setStyleSheet("""
            QTextEdit {
                background-color: #ffffff; /* White background */
                border: 1px solid #cccccc; /* Light gray border */
                border-radius: 5px;
                padding: 10px;
                font-size: 14px;
                color: #333333;
            }
        """)
        right_layout.addWidget(self.preview_text)
        
        right_panel.setLayout(right_layout)
        
        # Connect form fields to preview update
        for field in [self.first_name_edit, self.last_name_edit, self.id_edit, 
                     self.phone_edit, self.program_edit]:
            field.textChanged.connect(self.update_preview)
        self.role_combo.currentTextChanged.connect(self.update_preview)
        self.photo_widget.photo_changed.connect(self.update_preview)
        
        layout.addWidget(left_panel)
        layout.addWidget(right_panel)
        
        widget.setLayout(layout)
        return widget
    
    def create_manage_users_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        search_label = QLabel('🔍 Search:')
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText('Search by name, ID, or program...')
        self.search_edit.textChanged.connect(self.filter_users)
        
        refresh_btn = QPushButton('🔄 Refresh')
        refresh_btn.setObjectName('primaryBtn')
        refresh_btn.clicked.connect(self.load_users)
        
        header_layout.addWidget(search_label)
        header_layout.addWidget(self.search_edit)
        header_layout.addWidget(refresh_btn)
        
        layout.addLayout(header_layout)
        
        # Users table
        self.users_table = QTableWidget()
        self.users_table.setColumnCount(9)
        self.users_table.setHorizontalHeaderLabels([
            'Card ID', 'Full Name', 'Role', 'ID Number', 'Phone', 'Program', 'Status', 'Registered By', 'Date'
        ])
        self.users_table.horizontalHeader().setStretchLastSection(True)
        self.users_table.setAlternatingRowColors(True)
        self.users_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.users_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.users_table.customContextMenuRequested.connect(self.show_user_context_menu)
        
        layout.addWidget(self.users_table)
        
        widget.setLayout(layout)
        self.load_users()
        return widget
    
    def create_view_logs_tab(self):
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Header with controls
        header_layout = QHBoxLayout()
        
        filter_label = QLabel('📅 Filter:')
        self.log_filter_combo = QComboBox()
        self.log_filter_combo.addItems(['All Logs', 'Access Granted', 'Access Denied', 'Unknown Cards'])
        self.log_filter_combo.currentTextChanged.connect(self.filter_logs)
        
        refresh_logs_btn = QPushButton('🔄 Refresh Logs')
        refresh_logs_btn.setObjectName('primaryBtn')
        refresh_logs_btn.clicked.connect(self.load_access_logs)
        
        export_btn = QPushButton('📊 Export Logs')
        export_btn.setObjectName('successBtn')
        export_btn.clicked.connect(self.export_logs)
        
        header_layout.addWidget(filter_label)
        header_layout.addWidget(self.log_filter_combo)
        header_layout.addStretch()
        header_layout.addWidget(refresh_logs_btn)
        header_layout.addWidget(export_btn)
        
        layout.addLayout(header_layout)
        
        # Access logs table
        self.logs_table = QTableWidget()
        self.logs_table.setColumnCount(5)
        self.logs_table.setHorizontalHeaderLabels([
            'Card ID', 'Full Name', 'Role', 'Status', 'Timestamp'
        ])
        self.logs_table.horizontalHeader().setStretchLastSection(True)
        self.logs_table.setAlternatingRowColors(True)
        self.logs_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        
        layout.addWidget(self.logs_table)
        
        widget.setLayout(layout)
        self.load_access_logs()
        return widget
    
    def setup_serial_connection(self):
        try:
            self.serial_reader = SerialReader('COM3', 9600)
            self.serial_reader.card_detected.connect(self.on_card_detected)
            self.serial_reader.start()
            self.serial_status.setText('🟢 Serial: Connected')
        except Exception as e:
            self.serial_status.setText('🔴 Serial: Error')
            print(f'Serial connection error: {e}')
    
    def on_card_detected(self, card_id):
        card_info = self.db.get_card_by_id(card_id)
        
        if card_info:
            full_name = f"{card_info[2]} {card_info[3]}"
            role = card_info[4]
            status = card_info[10]
            
            if status == 'Active':
                self.card_status.setText(f'✅ Access Granted: {full_name} ({role})')
                self.card_status.setStyleSheet("font-size: 14px; color: #28a745; font-weight: bold; padding: 10px; background-color: #d4edda; border-radius: 6px;")
                self.db.log_access(card_id, full_name, role, 'ACCESS_GRANTED')
                self.show_user_details(card_id)
            else:
                self.card_status.setText(f'❌ Access Denied: {full_name} ({role}) - Inactive')
                self.card_status.setStyleSheet("font-size: 14px; color: #dc3545; font-weight: bold; padding: 10px; background-color: #f8d7da; border-radius: 6px;")
                self.db.log_access(card_id, full_name, role, 'ACCESS_DENIED')
                self.show_user_details(card_id)
        else:
            self.card_status.setText(f'⚠️ Unknown Card: {card_id}')
            self.card_status.setStyleSheet("font-size: 14px; color: #ffc107; font-weight: bold; padding: 10px; background-color: #fff3cd; border-radius: 6px;")
            self.db.log_access(card_id, 'Unknown', 'Unknown', 'UNKNOWN_CARD')
            
            # Auto-fill registration form
            self.card_id_edit.setText(card_id)
        
        self.load_access_logs()
        QTimer.singleShot(5000, self.reset_card_status)
    
    def reset_card_status(self):
        self.card_status.setText('🔍 Waiting for RFID card...')
        self.card_status.setStyleSheet("font-size: 14px; color: #6c757d; font-style: italic; padding: 10px; background-color: #f8f9fa; border-radius: 6px;")
    
    def toggle_manual_entry(self):
        if self.card_id_edit.isReadOnly():
            self.card_id_edit.setReadOnly(False)
            self.card_id_edit.setPlaceholderText('Enter RFID card ID manually')
            self.card_id_edit.clear()
        else:
            self.card_id_edit.setReadOnly(True)
            self.card_id_edit.setPlaceholderText('Scan card or enter manually')
    
    def on_role_changed(self):
        role = self.role_combo.currentText()
        if role == 'Student':
            self.id_label.setText('School ID:')
            self.id_edit.setPlaceholderText('Enter school ID number')
        else:
            self.id_label.setText('Employee ID:')
            self.id_edit.setPlaceholderText('Enter employee ID number')
        self.update_preview()
    
    def update_preview(self):
        if not self.first_name_edit.text().strip():
            self.preview_text.clear()
            return
        
        role = self.role_combo.currentText()
        id_type = "School ID" if role == "Student" else "Employee ID"
        
        preview_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h3 style="color: #007bff; margin-bottom: 20px;">Registration Preview</h3>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 15px;">
                <h4 style="color: #495057; margin-top: 0;">Personal Information</h4>
                <p><strong>Name:</strong> {self.first_name_edit.text()} {self.last_name_edit.text()}</p>
                <p><strong>Role:</strong> {role}</p>
                <p><strong>{id_type}:</strong> {self.id_edit.text()}</p>
                <p><strong>Phone:</strong> {self.phone_edit.text()}</p>
                <p><strong>Program:</strong> {self.program_edit.text()}</p>
            </div>
            
            <div style="background: #e9ecef; padding: 15px; border-radius: 8px;">
                <h4 style="color: #495057; margin-top: 0;">System Information</h4>
                <p><strong>Card ID:</strong> {self.card_id_edit.text()}</p>
                <p><strong>Photo:</strong> {'✅ Uploaded' if self.photo_widget.get_photo_data() else '❌ Not uploaded'}</p>
                <p><strong>Status:</strong> Active</p>
                <p><strong>Registered By:</strong> {self.admin_username}</p>
            </div>
        </div>
        """
        
        self.preview_text.setHtml(preview_html)
    
    def register_user(self):
        # Validate required fields
        if not all([
            self.card_id_edit.text().strip(),
            self.first_name_edit.text().strip(),
            self.last_name_edit.text().strip(),
            self.id_edit.text().strip(),
            self.program_edit.text().strip()
        ]):
            QMessageBox.warning(self, 'Validation Error', 
                              'Please fill in all required fields:\n• Card ID\n• First Name\n• Last Name\n• ID Number\n• Program')
            return
        
        # Prepare data
        role = self.role_combo.currentText()
        school_id = self.id_edit.text().strip() if role == 'Student' else None
        employee_id = self.id_edit.text().strip() if role == 'Employee' else None
        
        card_data = (
            self.card_id_edit.text().strip(),
            self.first_name_edit.text().strip(),
            self.last_name_edit.text().strip(),
            role,
            school_id,
            employee_id,
            self.phone_edit.text().strip() or None,
            self.program_edit.text().strip(),
            self.photo_widget.get_photo_data(),
            self.admin_username
        )
        
        # Save to database
        if self.db.add_rfid_card(card_data):
            QMessageBox.information(self, 'Success', 
                                  f'{role} registered successfully!\n\nName: {self.first_name_edit.text()} {self.last_name_edit.text()}')
            self.clear_registration_form()
            self.load_users()
        else:
            QMessageBox.warning(self, 'Error', 'Card ID already exists in the system.')
    
    def clear_registration_form(self):
        self.card_id_edit.clear()
        self.first_name_edit.clear()
        self.last_name_edit.clear()
        self.id_edit.clear()
        self.phone_edit.clear()
        self.program_edit.clear()
        self.photo_widget.clear_photo()
        self.role_combo.setCurrentIndex(0)
        self.preview_text.clear()
    
    def load_users(self):
        users = self.db.get_all_cards()
        self.users_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            self.users_table.setItem(row, 0, QTableWidgetItem(user[1]))  # card_id
            self.users_table.setItem(row, 1, QTableWidgetItem(f"{user[2]} {user[3]}"))  # full name
            self.users_table.setItem(row, 2, QTableWidgetItem(user[4]))  # role
            
            # ID number (school_id or employee_id)
            id_number = user[5] if user[5] else user[6]
            self.users_table.setItem(row, 3, QTableWidgetItem(id_number or ''))
            
            self.users_table.setItem(row, 4, QTableWidgetItem(user[7] or ''))  # phone
            self.users_table.setItem(row, 5, QTableWidgetItem(user[8]))  # program
            
            # Status with color coding
            status_item = QTableWidgetItem(user[10])
            if user[10] == 'Active':
                status_item.setBackground(QColor('#d4edda'))
                status_item.setForeground(QColor('#155724'))
            else:
                status_item.setBackground(QColor('#f8d7da'))
                status_item.setForeground(QColor('#721c24'))
            self.users_table.setItem(row, 6, status_item)
            
            self.users_table.setItem(row, 7, QTableWidgetItem(user[11]))  # registered_by
            self.users_table.setItem(row, 8, QTableWidgetItem(user[12]))  # created_at
    
    def filter_users(self):
        search_text = self.search_edit.text().lower()
        for row in range(self.users_table.rowCount()):
            match = False
            for col in range(self.users_table.columnCount()):
                item = self.users_table.item(row, col)
                if item and search_text in item.text().lower():
                    match = True
                    break
            self.users_table.setRowHidden(row, not match)
    
    def show_user_context_menu(self, position):
        if self.users_table.itemAt(position) is None:
            return
        
        menu = QMenu()
        
        view_action = menu.addAction("👁️ View Details")
        menu.addSeparator()
        activate_action = menu.addAction("✅ Set Active")
        deactivate_action = menu.addAction("❌ Set Inactive")
        menu.addSeparator()
        delete_action = menu.addAction("🗑️ Delete User")
        
        action = menu.exec_(self.users_table.mapToGlobal(position))
        
        if action:
            row = self.users_table.currentRow()
            card_id = self.users_table.item(row, 0).text()
            
            if action == view_action:
                self.show_user_details(card_id)
            elif action == activate_action:
                self.db.update_card_status(card_id, 'Active')
                self.load_users()
            elif action == deactivate_action:
                self.db.update_card_status(card_id, 'Inactive')
                self.load_users()
            elif action == delete_action:
                reply = QMessageBox.question(self, 'Confirm Delete', 
                                           f'Are you sure you want to delete user with card ID: {card_id}?')
                if reply == QMessageBox.Yes:
                    self.db.delete_card(card_id)
                    self.load_users()
    
    def show_user_details(self, card_id):
        user_info = self.db.get_card_by_id(card_id)
        if not user_info:
            return
        
        dialog = QDialog(self)
        dialog.setWindowTitle('User Details')
        dialog.setFixedSize(500, 600)
        dialog.setStyleSheet(self.styleSheet())
        
        layout = QVBoxLayout()
        
        # Photo display
        if user_info[9]:  # photo data
            photo_label = QLabel()
            photo_label.setFixedSize(150, 150)
            photo_label.setStyleSheet("border: 2px solid #dee2e6; border-radius: 8px;")
            photo_label.setAlignment(Qt.AlignCenter)
            photo_label.setScaledContents(True)
            
            try:
                image_data = base64.b64decode(user_info[9])
                pixmap = QPixmap()
                pixmap.loadFromData(image_data)
                photo_label.setPixmap(pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation))
            except:
                photo_label.setText("Photo Error")
            
            photo_layout = QHBoxLayout()
            photo_layout.addStretch()
            photo_layout.addWidget(photo_label)
            photo_layout.addStretch()
            layout.addLayout(photo_layout)
        
        # User information
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        
        role = user_info[4]
        id_type = "School ID" if role == "Student" else "Employee ID"
        id_number = user_info[5] if user_info[5] else user_info[6]
        
        info_html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h2 style="color: #007bff; text-align: center;">{user_info[2]} {user_info[3]}</h2>
            
            <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h4 style="color: #495057; margin-top: 0;">Personal Information</h4>
                <p><strong>Full Name:</strong> {user_info[2]} {user_info[3]}</p>
                <p><strong>Role:</strong> {role}</p>
                <p><strong>{id_type}:</strong> {id_number}</p>
                <p><strong>Phone Number:</strong> {user_info[7] or 'Not provided'}</p>
                <p><strong>Program:</strong> {user_info[8]}</p>
            </div>
            
            <div style="background: #e9ecef; padding: 15px; border-radius: 8px; margin: 15px 0;">
                <h4 style="color: #495057; margin-top: 0;">System Information</h4>
                <p><strong>Card ID:</strong> {user_info[1]}</p>
                <p><strong>Status:</strong> <span style="color: {'#28a745' if user_info[10] == 'Active' else '#dc3545'};">{user_info[10]}</span></p>
                <p><strong>Registered By:</strong> {user_info[11]}</p>
                <p><strong>Registration Date:</strong> {user_info[12]}</p>
            </div>
        </div>
        """
        
        info_text.setHtml(info_html)
        layout.addWidget(info_text)
        
        # Close button
        close_btn = QPushButton('Close')
        close_btn.setObjectName('primaryBtn')
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()
    
    def load_access_logs(self):
        logs = self.db.get_access_log(200)
        self.logs_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            self.logs_table.setItem(row, 0, QTableWidgetItem(log[1]))  # card_id
            self.logs_table.setItem(row, 1, QTableWidgetItem(log[2]))  # full_name
            self.logs_table.setItem(row, 2, QTableWidgetItem(log[3]))  # role
            
            # Status with color coding
            status_item = QTableWidgetItem(log[4])
            if log[4] == 'ACCESS_GRANTED':
                status_item.setBackground(QColor('#d4edda'))
                status_item.setForeground(QColor('#155724'))
            elif log[4] == 'ACCESS_DENIED':
                status_item.setBackground(QColor('#f8d7da'))
                status_item.setForeground(QColor('#721c24'))
            else:
                status_item.setBackground(QColor('#fff3cd'))
                status_item.setForeground(QColor('#856404'))
            
            self.logs_table.setItem(row, 3, status_item)
            self.logs_table.setItem(row, 4, QTableWidgetItem(log[5]))  # timestamp
    
    def filter_logs(self):
        filter_text = self.log_filter_combo.currentText()
        
        for row in range(self.logs_table.rowCount()):
            status_item = self.logs_table.item(row, 3)
            if not status_item:
                continue
                
            status = status_item.text()
            show_row = True
            
            if filter_text == 'Access Granted' and status != 'ACCESS_GRANTED':
                show_row = False
            elif filter_text == 'Access Denied' and status != 'ACCESS_DENIED':
                show_row = False
            elif filter_text == 'Unknown Cards' and status != 'UNKNOWN_CARD':
                show_row = False
            
            self.logs_table.setRowHidden(row, not show_row)
    
    def export_logs(self):
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Access Logs", 
            f"access_logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    file.write("Card ID,Full Name,Role,Status,Timestamp\n")
                    
                    logs = self.db.get_access_log(1000)  # Export more logs
                    for log in logs:
                        file.write(f'"{log[1]}","{log[2]}","{log[3]}","{log[4]}","{log[5]}"\n')
                
                QMessageBox.information(self, 'Export Complete', 
                                      f'Access logs exported successfully to:\n{file_path}')
            except Exception as e:
                QMessageBox.warning(self, 'Export Error', f'Failed to export logs:\n{str(e)}')
    
    def logout(self):
        reply = QMessageBox.question(self, 'Logout Confirmation', 
                                   'Are you sure you want to logout?')
        if reply == QMessageBox.Yes:
            if self.serial_reader:
                self.serial_reader.stop()
            self.close()
            self.login_window = LoginWindow()
            self.login_window.show()
    
    def closeEvent(self, event):
        if self.serial_reader:
            self.serial_reader.stop()
        event.accept()

class RFIDApp(QApplication):
    def __init__(self, sys_argv):
        super().__init__(sys_argv)
        self.setApplicationName('RFID Management System')
        self.setApplicationVersion('2.0')
        self.setWindowIcon(QIcon('icon.jpg'))
        
        # Set application style
        self.setStyle('Fusion')
        
        self.login_window = LoginWindow()
        self.login_window.show()

if __name__ == '__main__':
    app = RFIDApp(sys.argv)
    sys.exit(app.exec_())