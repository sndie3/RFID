from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox, QDesktopWidget
from PyQt5.QtCore import Qt
from database import DatabaseManager

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.db = DatabaseManager()
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle('CTU-CC RFID MANAGEMENT SYSTEM')
        self.setStyleSheet("""
            QWidget {
                background-color: #f0f0f0;
                font-family: 'Segoe UI', Arial, sans-serif;
            }
            QLabel {
                color: #333333;
                font-size: 14px;
            }
            QLineEdit {
                background-color: #ffffff;
                border: 1px solid #cccccc;
                border-radius: 5px;
                padding: 8px 10px;
                font-size: 14px;
                color: #333;
            }
            QLineEdit:focus {
                border: 1px solid #007bff;
            }
            QPushButton {
                background-color: #007bff;
                color: white;
                border: none;
                border-radius: 5px;
                padding: 14px;
                font-size: 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0056b3;
            }
            QPushButton:pressed {
                background-color: #004085;
            }
        """)
        self.center()
        layout = QVBoxLayout()
        layout.setSpacing(25)
        layout.setContentsMargins(60, 60, 60, 60)
        title = QLabel('Admin Login')
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #333333; margin-bottom: 30px;")
        layout.addWidget(title)
        username_label = QLabel('Username')
        username_label.setStyleSheet("font-weight: bold; margin-bottom: 5px;")
        layout.addWidget(username_label)
        self.username_edit = QLineEdit()
        self.username_edit.setPlaceholderText('Enter your username')
        layout.addWidget(self.username_edit)
        password_label = QLabel('Password')
        password_label.setStyleSheet("font-weight: bold; margin-bottom: 5px; margin-top: 15px;")
        layout.addWidget(password_label)
        self.password_edit = QLineEdit()
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.password_edit.setPlaceholderText('Enter your password')
        layout.addWidget(self.password_edit)
        self.login_btn = QPushButton('Sign In')
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setStyleSheet(self.login_btn.styleSheet() + "margin-top: 20px;")
        layout.addWidget(self.login_btn)
        info_label = QLabel('Default: admin / admin123')
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setStyleSheet("font-size: 12px; color: rgba(255,255,255,0.6); font-style: italic; margin-top: 20px;")
        layout.addWidget(info_label)
        self.setLayout(layout)
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
            from ui_main import MainWindow
            self.main_window = MainWindow(username)
            self.main_window.show()
            self.close()
        else:
            QMessageBox.warning(self, 'Login Failed', 'Invalid username or password.')
            self.password_edit.clear() 