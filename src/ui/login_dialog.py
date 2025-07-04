from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, QSettings

class LoginDialog(QDialog):
    def __init__(self, auth_manager, parent=None):
        super().__init__(parent)
        self.auth_manager = auth_manager
        self.user_info = None
        
        self.setWindowTitle("Login")
        self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
        self.setMinimumWidth(300)
        
        self.initUI()
        self.loadSavedUsername()
    
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        form_layout = QFormLayout()
        
        # Username
        self.username_input = QLineEdit()
        form_layout.addRow("Username:", self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        form_layout.addRow("Password:", self.password_input)
        
        # Remember username
        self.remember_checkbox = QCheckBox("Remember username")
        form_layout.addRow("", self.remember_checkbox)
        
        layout.addLayout(form_layout)
        
        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        layout.addWidget(self.login_btn)
        
        # Set enter key to trigger login
        self.login_btn.setDefault(True)
        
        self.setLayout(layout)
    
    def login(self):
        """Attempt to login with provided credentials"""
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both username and password.")
            return
        
        # Attempt to authenticate
        success, result = self.auth_manager.authenticate(username, password)
        
        if success:
            # Save username if remember is checked
            if self.remember_checkbox.isChecked():
                self.saveUsername(username)
            else:
                self.clearSavedUsername()
            
            # Store user info
            self.user_info = result
            
            # Accept dialog
            self.accept()
        else:
            QMessageBox.warning(self, "Login Failed", result)
    
    def saveUsername(self, username):
        """Save username for future logins"""
        settings = QSettings("MedRepApp", "Login")
        settings.setValue("username", username)
        settings.setValue("remember", True)
    
    def clearSavedUsername(self):
        """Clear saved username"""
        settings = QSettings("MedRepApp", "Login")
        settings.remove("username")
        settings.setValue("remember", False)
    
    def loadSavedUsername(self):
        """Load saved username if available"""
        settings = QSettings("MedRepApp", "Login")
        username = settings.value("username", "")
        remember = settings.value("remember", False, type=bool)
        
        if username and remember:
            self.username_input.setText(username)
            self.remember_checkbox.setChecked(True)
            self.password_input.setFocus()