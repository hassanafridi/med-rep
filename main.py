"""
Main Application Integration for Enhanced MedRep - Fixed for MongoDB
"""

import sys
import os
import logging
import subprocess
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox, QDialog,
    QAction, QVBoxLayout, QLabel, QPushButton, QMenuBar, QStatusBar, QHBoxLayout
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSignal, QTimer, QSettings

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the enhanced tabs
from src.ui.new_entry_tab import NewEntryTab
from src.ui.ledger_tab import LedgerTab
from src.ui.graphs_tab import GraphsTab
from src.ui.reports_tab import ReportsTab
from src.ui.settings_tab import SettingsTab
from src.ui.manage_data_tab import ManageDataTab
from src.database.mongo_db import MongoDB
from src.database.mongo_adapter import MongoAdapter
from src.config import Config
from src.user_auth import UserAuth
from src.ui.login_dialog import LoginDialog
from src.ui.dashboard_tab import DashboardTab

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)

class MainWindow(QMainWindow):
    """
    Enhanced Main Window with proper MongoDB integration
    """
    
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = Config()
        
        # Set logging level from config
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.getLogger().setLevel(log_level)
        
        # Initialize MongoDB as primary database
        self.db = self.initialize_mongodb()
        if not self.db:
            # Show error and exit gracefully
            QMessageBox.critical(None, "Database Error", 
                               "Failed to initialize database connection.\n"
                               "Please check your MongoDB configuration and try again.")
            sys.exit(1)
        
        # Initialize user authentication with MongoDB
        try:
            # Create MongoAdapter for UserAuth
            self.mongo_adapter = MongoAdapter(mongo_db_instance=self.db)
            self.mongo_adapter.connect()
            
            self.auth_manager = UserAuth(self.mongo_adapter)
            self.current_user = None
            
            # Show login dialog
            if not self.login():
                sys.exit(0)
                
        except Exception as e:
            logging.error(f"Authentication initialization error: {e}")
            QMessageBox.critical(None, "Authentication Error",
                               f"Failed to initialize authentication:\n{str(e)}")
            sys.exit(1)
        
        self.initUI()
    
    def initialize_mongodb(self):
        """Initialize MongoDB connection"""
        try:
            # Get MongoDB connection details from config
            mongo_uri = self.config.get('mongo_uri')
            mongo_dbname = self.config.get('mongo_dbname', 'medrep')
            
            if not mongo_uri:
                # Use default Atlas connection if not configured
                logging.warning("No mongo_uri in config, using default Atlas connection")
                mongo_uri = "mongodb+srv://medrep:Dk9Glbs2B2E0Dxof@cluster0.tgwmarr.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
            
            # Create MongoDB instance
            db = MongoDB(connection_string=mongo_uri, database_name=mongo_dbname)
            
            # Test connection
            try:
                connection_result = db.connect()
                if connection_result is None or connection_result is False:
                    logging.error("Failed to connect to MongoDB - connection returned None or False")
                    return None
                logging.info("MongoDB connection successful")
            except Exception as conn_error:
                logging.error(f"MongoDB connection failed with exception: {conn_error}")
                return None
            
            # Initialize database collections and indexes
            try:
                init_result = db.init_db()
                if init_result is None or init_result is False:
                    logging.error("Failed to initialize MongoDB collections")
                    return None
                logging.info("MongoDB initialization successful")
            except Exception as init_error:
                logging.error(f"MongoDB initialization failed with exception: {init_error}")
                return None
            
            logging.info("Successfully connected to MongoDB Atlas")
            return db
            
        except Exception as e:
            logging.error(f"MongoDB initialization error: {e}")
            return None

    def initUI(self):
        """Initialize the main window UI"""
        self.setWindowTitle("MedRep - Medical Representative Transaction Manager")
        
        # Set window size from config
        width = self.config.get('window_width', 1200)
        height = self.config.get('window_height', 800)
        self.setGeometry(100, 100, width, height)
        
        # Create menu bar
        self.create_menus()
        
        # Create tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create all tabs
        self.create_all_tabs()
        
        # Show welcome message
        self.status_bar.showMessage("Welcome to MedRep - Enhanced with MongoDB Atlas", 5000)

    def create_menus(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Add logout action
        logout_action = QAction('Logout', self)
        logout_action.setShortcut('Ctrl+L')
        logout_action.triggered.connect(self.logoutUser)
        file_menu.addAction(logout_action)
        
        # Add separator
        file_menu.addSeparator()
        
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        about_action = QAction('About', self)
        about_action.triggered.connect(self.showAbout)
        help_menu.addAction(about_action)

    def create_all_tabs(self):
        """Create all application tabs with proper MongoDB support"""
        try:
            self.create_dashboard_tab()
            self.create_new_entry_tab()
            self.create_ledger_tab()
            self.create_manage_data_tab()
            self.create_graphs_tab()
            self.create_reports_tab()
            self.create_settings_tab()
        except Exception as e:
            logging.error(f"Error creating tabs: {e}")
    
    def create_dashboard_tab(self):
        """Create the dashboard tab with MongoDB data"""
        try:
            dashboard_tab = DashboardTab(self.current_user)
            # Set the MongoDB adapter properly
            dashboard_tab.db = MongoAdapter(mongo_db_instance=self.db)
            dashboard_tab.db.connect()  # Ensure connection
            
            self.tabs.addTab(dashboard_tab, "Dashboard")
            
            # Use QTimer to load data after UI is fully initialized
            def load_dashboard_data():
                try:
                    if hasattr(dashboard_tab, 'refresh'):
                        dashboard_tab.refresh()
                    logging.info("Dashboard data refreshed")
                except Exception as e:
                    logging.error(f"Error refreshing dashboard: {e}")
            
            QTimer.singleShot(500, load_dashboard_data)
            
        except Exception as e:
            logging.error(f"Error creating dashboard tab: {e}")
            placeholder = QLabel("Dashboard temporarily unavailable")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(placeholder, "Dashboard")

    def create_new_entry_tab(self):
        """Create the enhanced new entry tab with MongoDB support"""
        try:
            self.new_entry_tab = NewEntryTab()
            # Set the MongoDB adapter properly
            self.new_entry_tab.db = MongoAdapter(mongo_db_instance=self.db)
            self.new_entry_tab.db.connect()  # Ensure connection
            
            # Load data after UI is ready
            def load_entry_data():
                try:
                    self.new_entry_tab.loadCustomersAndProducts()
                    logging.info("New entry tab data loaded successfully")
                except Exception as e:
                    logging.error(f"Error loading new entry data: {e}")
            
            QTimer.singleShot(300, load_entry_data)
            
            self.tabs.addTab(self.new_entry_tab, "New Entry")
            
        except Exception as e:
            logging.error(f"Error creating new entry tab: {e}")
            placeholder = QLabel("New Entry temporarily unavailable")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(placeholder, "New Entry")

    def create_ledger_tab(self):
        """Create the enhanced ledger tab with MongoDB support"""
        try:
            self.ledger_tab = LedgerTab()
            # Set the MongoDB adapter properly
            self.ledger_tab.db = MongoAdapter(mongo_db_instance=self.db)
            self.ledger_tab.db.connect()  # Ensure connection
            
            # Load data after UI is ready
            def load_ledger_data():
                try:
                    self.ledger_tab.loadCustomers()
                    self.ledger_tab.loadEntries()
                    logging.info("Ledger tab data loaded successfully")
                except Exception as e:
                    logging.error(f"Error loading ledger data: {e}")
            
            QTimer.singleShot(400, load_ledger_data)
            
            self.tabs.addTab(self.ledger_tab, "Ledger")
            
        except Exception as e:
            logging.error(f"Error creating ledger tab: {e}")
            placeholder = QLabel("Ledger temporarily unavailable")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(placeholder, "Ledger")

    def create_manage_data_tab(self):
        """Create the manage data tab with MongoDB support"""
        try:
            self.manage_data_tab = ManageDataTab()
            # Set the MongoDB adapter properly
            self.manage_data_tab.db = MongoAdapter(mongo_db_instance=self.db)
            self.manage_data_tab.db.connect()  # Ensure connection
            
            # Load data after UI is ready
            def load_manage_data():
                try:
                    self.manage_data_tab.loadCustomers()
                    self.manage_data_tab.loadProducts()
                    logging.info("Manage data tab loaded successfully")
                except Exception as e:
                    logging.error(f"Error loading manage data: {e}")
            
            QTimer.singleShot(200, load_manage_data)
            
            self.tabs.addTab(self.manage_data_tab, "Manage Data")
            
        except Exception as e:
            logging.error(f"Error creating manage data tab: {e}")
            placeholder = QLabel("Manage Data temporarily unavailable")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(placeholder, "Manage Data")

    def create_graphs_tab(self):
        """Create the graphs tab with MongoDB data"""
        try:
            graphs_tab = GraphsTab()
            # Set the MongoDB adapter properly
            graphs_tab.db = MongoAdapter(mongo_db_instance=self.db)
            graphs_tab.db.connect()  # Ensure connection
            
            self.tabs.addTab(graphs_tab, "Graphs")
            
        except Exception as e:
            logging.error(f"Error creating graphs tab: {e}")
            placeholder = QLabel("Graphs temporarily unavailable")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(placeholder, "Graphs")

    def create_reports_tab(self):
        """Create and add the Reports tab with MongoDB support"""
        try:
            reports_tab = ReportsTab()
            # Set the MongoDB adapter properly
            reports_tab.db = MongoAdapter(mongo_db_instance=self.db)
            reports_tab.db.connect()  # Ensure connection
            
            self.tabs.addTab(reports_tab, "Reports")
            
        except Exception as e:
            logging.error(f"Error creating reports tab: {e}")
            placeholder = QLabel("Reports temporarily unavailable")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(placeholder, "Reports")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        try:
            self.settings_tab = SettingsTab(self.config)
            # Set the MongoDB adapter properly
            self.settings_tab.db = MongoAdapter(mongo_db_instance=self.db)
            self.settings_tab.db.connect()  # Ensure connection
            
            # Connect logout signal
            if hasattr(self.settings_tab, 'logout_requested'):
                self.settings_tab.logout_requested.connect(self.handleLogout)
            
            self.tabs.addTab(self.settings_tab, "Settings")
            
        except Exception as e:
            logging.error(f"Error creating settings tab: {e}")
            placeholder = QLabel("Settings temporarily unavailable")
            placeholder.setAlignment(Qt.AlignCenter)
            self.tabs.addTab(placeholder, "Settings")

    def login(self):
        """Show login dialog and authenticate user"""
        try:
            # First check if user is already logged in
            from src.ui.login_dialog import LoginDialog
            if LoginDialog.isUserLoggedIn():
                # Try to validate existing session without showing dialog
                settings = QSettings("MedRepApp", "Session")
                session_data = settings.value("session_data", None)
                if session_data:
                    if isinstance(session_data, str):
                        import json
                        user_info = json.loads(session_data)
                    else:
                        user_info = session_data
                    
                    self.current_user = user_info
                    logging.info(f"Auto-login successful for user: {user_info.get('username')}")
                    return True
            
            # Show login dialog if no valid session
            dialog = LoginDialog(self.mongo_adapter)
            result = dialog.exec_()
            
            if result == QDialog.Accepted and dialog.user_info:
                self.current_user = dialog.user_info
                logging.info(f"User {self.current_user.get('username')} logged in successfully")
                return True
            
            return False
            
        except Exception as e:
            logging.error(f"Login error: {e}")
            QMessageBox.critical(None, "Login Error", f"Failed to login: {str(e)}")
            return False

    def showAbout(self):
        """Show the About dialog"""
        about_dialog = QDialog(self)
        about_dialog.setWindowTitle("About Medical Rep Transaction Software")
        about_dialog.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # App title
        title_label = QLabel("Medical Rep Transaction Software")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Version
        version_label = QLabel("Version 1.0.0 - MongoDB Atlas Edition")
        version_label.setAlignment(Qt.AlignCenter)
        
        # Description
        description = QLabel(
            "A comprehensive solution for medical representatives to manage "
            "their sales, customers, and financial transactions with MongoDB Atlas."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        
        # Copyright
        copyright_label = QLabel("© 2025 BSOLS Technologies")
        copyright_label.setAlignment(Qt.AlignCenter)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(about_dialog.accept)
        
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addSpacing(10)
        layout.addWidget(description)
        layout.addSpacing(10)
        layout.addWidget(copyright_label)
        layout.addSpacing(20)
        layout.addWidget(close_btn)
        
        about_dialog.setLayout(layout)
        about_dialog.exec_()
    
    def logoutUser(self):
        """Handle user logout from menu"""
        try:
            reply = QMessageBox.question(
                self, "Confirm Logout",
                "Are you sure you want to logout?\n\nThe application will restart and you'll need to login again.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                from src.ui.login_dialog import LoginDialog
                if LoginDialog.logout():
                    logging.info(f"User {self.current_user.get('username', 'Unknown')} logged out")
                    self.handleLogout()
                else:
                    QMessageBox.warning(
                        self, "Logout Error",
                        "There was an error during logout. Please try again."
                    )
                
        except Exception as e:
            logging.error(f"Logout error: {e}")
            QMessageBox.critical(self, "Logout Error", f"Failed to logout: {str(e)}")
    
    def handleLogout(self):
        """Handle user logout by restarting the application"""
        try:
            logging.info("Handling logout - restarting application")
            
            # Close current window and database connections
            if self.db:
                self.db.close()
                logging.info("MongoDB connection closed for logout")
            
            # Get the current script path
            script_path = os.path.abspath(sys.argv[0])
            
            # Start new instance
            if getattr(sys, 'frozen', False):
                # If running as executable
                subprocess.Popen([sys.executable])
                logging.info("Restarting as executable")
            else:
                # If running as script
                subprocess.Popen([sys.executable, script_path])
                logging.info(f"Restarting script: {script_path}")
            
            # Exit current instance
            QApplication.quit()
            sys.exit(0)
            
        except Exception as e:
            logging.error(f"Error during logout restart: {e}")
            # Fallback: show message and exit
            QMessageBox.information(
                self, "Logout Complete",
                "Logout successful. Please restart the application manually to login again."
            )
            QApplication.quit()
            sys.exit(0)

    def closeEvent(self, event):
        """Handle window close event"""
        # Save window size to config
        self.config.set('window_width', self.width())
        self.config.set('window_height', self.height())
        
        # Close MongoDB connection
        if self.db:
            self.db.close()
            logging.info("MongoDB connection closed")
        
        event.accept()


# Startup check for invoice folder
def ensure_invoice_folder():
    """Ensure the invoice folder exists"""
    invoice_folder = "invoices"
    if not os.path.exists(invoice_folder):
        os.makedirs(invoice_folder)
        print(f"Created invoice folder: {invoice_folder}")


# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Ensure invoice folder exists
    ensure_invoice_folder()
    
    print("Using MongoDB Atlas as primary database")
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application startup error: {e}")
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application:\n{str(e)}\n\n"
                           "Please check your MongoDB connection and configuration.")
        sys.exit(1)