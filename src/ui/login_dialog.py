from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLabel, QLineEdit, 
    QPushButton, QMessageBox, QCheckBox
)
from PyQt5.QtCore import Qt, QSettings
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LoginDialog(QDialog):
    def __init__(self, mongo_adapter=None, parent=None):
        super().__init__(parent)
        try:
            from src.database.mongo_adapter import MongoAdapter
            from src.user_auth import UserAuth  # Import UserAuth
            
            self.mongo_adapter = mongo_adapter or MongoAdapter()
            # Initialize UserAuth with the mongo adapter
            self.user_auth = UserAuth(self.mongo_adapter)
            self.user_info = None
            
            self.setWindowTitle("Login - ")
            self.setWindowFlag(Qt.WindowContextHelpButtonHint, False)
            self.setMinimumWidth(350)
            
            self.initUI()
            self.loadSavedUsername()
        except Exception as e:
            print(f"Error initializing Login Dialog: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Login system temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the login dialog"""
        try:
            # Clear current layout
            if self.layout():
                for i in reversed(range(self.layout().count())):
                    self.layout().itemAt(i).widget().setParent(None)
            
            # Retry initialization
            self.__init__(self.mongo_adapter)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Login Dialog: {str(e)}")
    
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Medical Rep Transaction Software")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: #4B0082;
                margin-bottom: 10px;
            }
        """)
        layout.addWidget(title_label)
        
      
        form_layout = QFormLayout()
        
        # Username
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Enter your username")
        self.username_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #4B0082;
                padding: 8px;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6B0AC2;
            }
        """)
        form_layout.addRow("Username:", self.username_input)
        
        # Password
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.password_input.setPlaceholderText("Enter your password")
        self.password_input.setStyleSheet("""
            QLineEdit {
                border: 2px solid #4B0082;
                padding: 8px;
                border-radius: 5px;
                font-size: 14px;
            }
            QLineEdit:focus {
                border-color: #6B0AC2;
            }
        """)
        form_layout.addRow("Password:", self.password_input)
        
        # Remember username
        self.remember_checkbox = QCheckBox("Remember username")
        self.remember_checkbox.setStyleSheet("color: #4B0082; font-weight: bold;")
        form_layout.addRow("", self.remember_checkbox)
        
        layout.addLayout(form_layout)
        
        # Login button
        self.login_btn = QPushButton("Login")
        self.login_btn.clicked.connect(self.login)
        self.login_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 12px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
                margin-top: 10px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
            QPushButton:pressed {
                background-color: #3A0062;
            }
        """)
        layout.addWidget(self.login_btn)
        
        # # Create default user button for demo
        # self.create_user_btn = QPushButton("Create Demo User")
        # self.create_user_btn.clicked.connect(self.createDemoUser)
        # self.create_user_btn.setStyleSheet("""
        #     QPushButton {
        #         background-color: #666;
        #         color: white;
        #         padding: 8px;
        #         font-weight: bold;
        #         border-radius: 5px;
        #         margin-top: 5px;
        #     }
        #     QPushButton:hover {
        #         background-color: #888;
        #     }
        # """)
        # layout.addWidget(self.create_user_btn)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; margin-top: 10px;")
        layout.addWidget(self.status_label)
        
        # Set enter key to trigger login
        self.login_btn.setDefault(True)
        
        self.setLayout(layout)
        
        # Check MongoDB connection status
        self.checkConnectionStatus()
    
    def checkConnectionStatus(self):
        """Check MongoDB connection status"""
        try:
            # Check connection through mongo_adapter, not user_auth
            if self.mongo_adapter and self.mongo_adapter.connect():
                self.status_label.setText("✅ Connected to MongoDB")
                self.status_label.setStyleSheet("color: green; margin-top: 10px;")
            else:
                self.status_label.setText("❌ MongoDB connection failed")
                self.status_label.setStyleSheet("color: red; margin-top: 10px;")
        except Exception as e:
            # self.status_label.setText(f"❌ Connection error: {str(e)}")
            self.status_label.setStyleSheet("color: red; margin-top: 10px;")
    
    def createDemoUser(self):
        """Create a demo user for testing using UserAuth"""
        try:
            if not self.user_auth:
                QMessageBox.warning(self, "Error", "UserAuth not available")
                return
            
            # Check if admin user already exists
            success, result = self.user_auth.authenticate("admin", "admin")
            if success:
                QMessageBox.information(self, "Demo User", 
                                      "Demo user already exists!\n\nUsername: admin\nPassword: admin")
                self.username_input.setText("admin")
                self.password_input.setText("admin")
                return
            
            # Create demo user using UserAuth (this will properly hash the password)
            success, message = self.user_auth.add_user("demo", "demo123", "Demo User", "user")
            if success:
                QMessageBox.information(self, "Demo User Created", 
                                      "Demo user created successfully!\n\nUsername: demo\nPassword: demo123")
                self.username_input.setText("demo")
                self.password_input.setText("demo123")
            else:
                QMessageBox.warning(self, "Error", f"Failed to create demo user: {message}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to create demo user: {str(e)}")
    
    def login(self):
        """Attempt to login with provided credentials using UserAuth"""
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Failed", "Please enter both username and password.")
            return
        
        try:
            if not self.user_auth:
                QMessageBox.warning(self, "Login Failed", "UserAuth not available")
                return
            
            # Authenticate user using UserAuth (this handles proper password hashing)
            success, result = self.user_auth.authenticate(username, password)
            
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
                
        except Exception as e:
            QMessageBox.critical(self, "Login Error", f"Login error: {str(e)}")
    
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