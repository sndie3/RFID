import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QIcon
from ui_login import LoginWindow

if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon('icon.ico'))
    login_window = LoginWindow()
    login_window.setWindowIcon(QIcon('icon.ico'))
    login_window.show()
    sys.exit(app.exec_())