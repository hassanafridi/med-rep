"""
Main Application Integration for Enhanced MedRep
Updates to integrate the new features into your existing application
"""

import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox, QDialog,
    QAction, QVBoxLayout, QLabel, QPushButton, QMenuBar, QStatusBar, QHBoxLayout
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt, pyqtSignal

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

# Import the enhanced tabs
from src.ui.new_entry_tab import NewEntryTab, InvoiceQuickViewDialog
from src.ui.ledger_tab import LedgerTab
from src.ui.graphs_tab import GraphsTab
from src.ui.reports_tab import ReportsTab
from src.ui.settings_tab import SettingsTab
from src.ui.manage_data_tab import ManageDataTab
from src.database.mongo_db import MongoDB
from src.database.mongo_adapter import MongoAdapter
from src.database.db import Database
from src.config import Config
from src.user_auth import UserAuth
from src.ui.login_dialog import LoginDialog
from src.ui.advanced_charts import AdvancedChartsTab
from src.ui.invoice_generator import InvoiceGenerator
from src.ui.help_system import HelpBrowser
from src.database.audit_trail import AuditTrail
from src.ui.dashboard_tab import DashboardTab

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)

class MainWindow(QMainWindow):
    """
    Enhanced Main Window with MongoDB integration
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
            sys.exit(1)
        
        # Initialize user authentication with MongoDB
        self.auth_manager = UserAuth(self.db)
        self.current_user = None
        
        # Show login dialog
        if not self.login():
            sys.exit(0)
        
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
            if not db.connect():
                QMessageBox.critical(self, "Database Connection Error",
                    "Cannot connect to MongoDB Atlas!\n\n"
                    "Please check:\n"
                    "1. Your internet connection\n"
                    "2. MongoDB Atlas cluster is running\n"
                    "3. Your IP address is whitelisted\n"
                    "4. Connection string is correct\n\n"
                    "Check data/config.json for mongo_uri setting.")
                return None
            
            # Initialize database collections and indexes
            if not db.init_db():
                QMessageBox.critical(self, "Database Initialization Error",
                    "Failed to initialize MongoDB collections and indexes.")
                return None
            
            logging.info("Successfully connected to MongoDB Atlas")
            return db
            
        except Exception as e:
            logging.error(f"MongoDB initialization error: {e}")
            QMessageBox.critical(self, "Database Error",
                f"Failed to initialize MongoDB:\n{str(e)}\n\n"
                "Please check your MongoDB configuration.")
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
        self.status_bar.showMessage("Welcome to MedRep - Enhanced with Auto Invoice Generation", 5000)

    def create_menus(self):
        """Create the menu bar"""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        invoice_action = QAction('Invoice Generator', self)
        invoice_action.triggered.connect(self.showInvoiceGenerator)
        tools_menu.addAction(invoice_action)
        
        charts_action = QAction('Advanced Charts', self)
        charts_action.triggered.connect(self.showAdvancedCharts)
        tools_menu.addAction(charts_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        help_action = QAction('Help Contents', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.showHelp)
        help_menu.addAction(help_action)
        
        about_action = QAction('About', self)
        about_action.triggered.connect(self.showAbout)
        help_menu.addAction(about_action)

    def create_all_tabs(self):
        """Create all application tabs with MongoDB support"""
        self.create_dashboard_tab()
        self.create_new_entry_tab()
        self.create_ledger_tab()
        self.create_graphs_tab()
        self.create_reports_tab()
        self.create_manage_data_tab()
        self.create_settings_tab()
    
    def create_dashboard_tab(self):
        """Create the dashboard tab with MongoDB data"""
        # DashboardTab expects only current_user parameter, uses Database() internally
        dashboard_tab = DashboardTab(self.current_user)
        # Replace the internal Database instance with MongoAdapter for compatibility
        if hasattr(dashboard_tab, 'db'):
            # Use MongoAdapter to make MongoDB compatible with SQLite interface
            dashboard_tab.db = MongoAdapter(self.db)
        self.tabs.addTab(dashboard_tab, "Dashboard")
    
    def create_new_entry_tab(self):
        """Create the enhanced new entry tab with MongoDB support"""
        # Create NewEntryTab with SQLite compatibility
        self.new_entry_tab = NewEntryTab()
        if hasattr(self.new_entry_tab, 'db'):
            # Use MongoAdapter to make MongoDB compatible with SQLite interface
            self.new_entry_tab.db = MongoAdapter(self.db)
        
        # Connect invoice generation signal if it exists
        if hasattr(self.new_entry_tab, 'entry_saved'):
            self.new_entry_tab.entry_saved.connect(self.on_invoice_generated)
        
        self.tabs.addTab(self.new_entry_tab, "New Entry")
    
    def create_ledger_tab(self):
        """Create the enhanced ledger tab with MongoDB support"""
        # Create LedgerTab with SQLite compatibility
        self.ledger_tab = LedgerTab()
        if hasattr(self.ledger_tab, 'db'):
            # Use MongoAdapter to make MongoDB compatible with SQLite interface
            self.ledger_tab.db = MongoAdapter(self.db)
        
        self.tabs.addTab(self.ledger_tab, "Ledger")
        
        # Connect tab change to refresh ledger when selected
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def create_graphs_tab(self):
        """Create the graphs tab with MongoDB data"""
        # GraphsTab constructor shows it expects no parameters, uses Database() internally
        graphs_tab = GraphsTab()
        # Replace the internal Database instance with MongoAdapter for compatibility
        if hasattr(graphs_tab, 'db'):
            graphs_tab.db = MongoAdapter(self.db)
        self.tabs.addTab(graphs_tab, "Graphs")
    
    def create_manage_data_tab(self):
        """Create the manage data tab with MongoDB support"""
        # Create ManageDataTab with SQLite compatibility
        manage_data_tab = ManageDataTab()
        if hasattr(manage_data_tab, 'db'):
            # Use MongoAdapter to make MongoDB compatible with SQLite interface
            manage_data_tab.db = MongoAdapter(self.db)
        self.tabs.addTab(manage_data_tab, "Manage Data")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        # SettingsTab expects config parameter and uses Database internally
        settings_tab = SettingsTab(self.config)
        # Replace the internal Database instance with MongoAdapter for compatibility
        if hasattr(settings_tab, 'db'):
            settings_tab.db = MongoAdapter(self.db)
        self.tabs.addTab(settings_tab, "Settings")
    
    def create_reports_tab(self):
        """Create and add the Reports tab with MongoDB support"""
        # ReportsTab constructor shows it expects no parameters, uses Database() internally
        reports_tab = ReportsTab()
        # Replace the internal Database instance with MongoAdapter for compatibility
        if hasattr(reports_tab, 'db'):
            reports_tab.db = MongoAdapter(self.db)
        self.tabs.addTab(reports_tab, "Reports")
    
    def login(self):
        """Show login dialog and authenticate user"""
        dialog = LoginDialog(self.auth_manager)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self.current_user = dialog.user_info
            logging.info(f"User {self.current_user.get('username')} logged in successfully")
            return True
        
        return False
    
    def showInvoiceGenerator(self):
        """Show the invoice generator dialog with MongoDB support"""
        invoice_generator = InvoiceGenerator(self.current_user, self.db)
        invoice_generator.show()

    def showAdvancedCharts(self):
        """Show the advanced charts window with MongoDB data"""
        charts_window = QMainWindow(self)
        charts_window.setWindowTitle("Advanced Charts")
        charts_window.setMinimumSize(900, 600)
        
        charts_tab = AdvancedChartsTab()
        # Replace the internal Database instance with MongoAdapter for compatibility
        if hasattr(charts_tab, 'db'):
            charts_tab.db = MongoAdapter(self.db)
        charts_window.setCentralWidget(charts_tab)
        
        charts_window.show()

    def showHelp(self):
        """Show the help browser"""
        self.help_browser = HelpBrowser()
        self.help_browser.show()

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
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        
        # Description
        description = QLabel(
            "A comprehensive solution for medical representatives to manage "
            "their sales, customers, and financial transactions."
        )
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignCenter)
        
        # Copyright
        copyright_label = QLabel("© 2025 Your Company")
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

    def on_invoice_generated(self, invoice_path):
        """Handle invoice generation event"""
        # Show status message
        self.status_bar.showMessage(f"✓ Invoice saved: {os.path.basename(invoice_path)}", 5000)
        
        # Show quick view dialog
        dialog = InvoiceQuickViewDialog(invoice_path, self)
        dialog.exec_()
        
        # Refresh ledger if it's currently visible
        if self.tabs.currentWidget() == self.ledger_tab:
            self.ledger_tab.loadEntries()
    
    def on_tab_changed(self, index):
        """Handle tab change event"""
        # Refresh ledger when switching to it
        if self.tabs.widget(index) == self.ledger_tab:
            self.ledger_tab.loadEntries()
            self.status_bar.showMessage("Ledger refreshed", 2000)


# Startup check for invoice folder
def ensure_invoice_folder():
    """Ensure the invoice folder exists"""
    invoice_folder = "invoices"
    if not os.path.exists(invoice_folder):
        os.makedirs(invoice_folder)
        print(f"Created invoice folder: {invoice_folder}")


# Settings additions for invoice configuration
class InvoiceSettings:
    """
    Invoice-related settings that can be added to your settings tab
    """
    
    @staticmethod
    def get_invoice_settings_widget():
        """Create a widget for invoice settings"""
        from PyQt5.QtWidgets import QGroupBox, QFormLayout, QLineEdit, QPushButton, QCheckBox
        
        group = QGroupBox("Invoice Settings")
        layout = QFormLayout()
        
        # Company settings
        company_name = QLineEdit("Tru-Pharma")
        company_email = QLineEdit("trupharmaceuticalfsd@gmail.com")
        layout.addRow("Company Name:", company_name)
        layout.addRow("Company Email:", company_email)
        
        # Invoice options
        auto_generate = QCheckBox("Auto-generate invoices by default")
        auto_generate.setChecked(True)
        layout.addRow("", auto_generate)
        
        # Invoice folder
        invoice_folder = QLineEdit("invoices")
        browse_btn = QPushButton("Browse...")
        folder_layout = QHBoxLayout()
        folder_layout.addWidget(invoice_folder)
        folder_layout.addWidget(browse_btn)
        layout.addRow("Invoice Folder:", folder_layout)
        
        # Logo settings
        logo_path = QLineEdit("")
        logo_btn = QPushButton("Select Logo...")
        logo_layout = QHBoxLayout()
        logo_layout.addWidget(logo_path)
        logo_layout.addWidget(logo_btn)
        layout.addRow("Company Logo:", logo_layout)
        
        group.setLayout(layout)
        return group


# Database migration for existing installations
def migrate_database_for_invoices(db_path):
    """
    Add invoice-related columns to existing database
    """
    import sqlite3
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns exist before adding
        cursor.execute("PRAGMA table_info(entries)")
        columns = [column[1] for column in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'transport_name' not in columns:
            cursor.execute("ALTER TABLE entries ADD COLUMN transport_name TEXT")
            print("Added transport_name column")
            
        if 'delivery_date' not in columns:
            cursor.execute("ALTER TABLE entries ADD COLUMN delivery_date TEXT")
            print("Added delivery_date column")
            
        if 'delivery_location' not in columns:
            cursor.execute("ALTER TABLE entries ADD COLUMN delivery_location TEXT")
            print("Added delivery_location column")
        
        # Create invoices table if it doesn't exist
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER,
                invoice_number TEXT UNIQUE,
                invoice_path TEXT,
                generated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (entry_id) REFERENCES entries(id)
            )
        ''')
        print("Invoices table ready")
        
        conn.commit()
        conn.close()
        print("Database migration completed successfully")
        
    except Exception as e:
        print(f"Migration error: {e}")


# Update the InvoiceManager to work with MongoDB
class InvoiceManager:
    """
    Utility class for invoice management operations with MongoDB
    """
    
    @staticmethod
    def find_invoice_by_number(invoice_number):
        """Find invoice file by invoice number"""
        invoice_folder = "invoices"
        for filename in os.listdir(invoice_folder):
            if invoice_number in filename and filename.endswith('.pdf'):
                return os.path.join(invoice_folder, filename)
        return None

    @staticmethod
    def get_invoice_statistics(mongo_db):
        """Get invoice generation statistics from MongoDB"""
        try:
            # Total invoices (entries with invoice numbers)
            total_invoices = mongo_db.db.entries.count_documents({
                "notes": {"$regex": "Invoice: INV-"},
            })
            
            # This month's invoices
            from datetime import datetime, timezone
            start_of_month = datetime.now(timezone.utc).replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            month_invoices = mongo_db.db.entries.count_documents({
                "notes": {"$regex": "Invoice: INV-"},
                "date": {"$gte": start_of_month}
            })
            
            # Today's invoices
            start_of_day = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
            today_invoices = mongo_db.db.entries.count_documents({
                "notes": {"$regex": "Invoice: INV-"},
                "date": {"$gte": start_of_day}
            })
            
            return {
                'total': total_invoices,
                'this_month': month_invoices,
                'today': today_invoices
            }
            
        except Exception as e:
            logging.error(f"Error getting invoice statistics: {e}")
            return {'total': 0, 'this_month': 0, 'today': 0}
    
    @staticmethod
    def cleanup_old_invoices(days_to_keep=90):
        """Clean up old invoice files"""
        import time
        
        invoice_folder = "invoices"
        if not os.path.exists(invoice_folder):
            return 0
            
        current_time = time.time()
        deleted_count = 0
        
        for filename in os.listdir(invoice_folder):
            if filename.endswith('.pdf'):
                file_path = os.path.join(invoice_folder, filename)
                file_age_days = (current_time - os.path.getmtime(file_path)) / 86400
                
                if file_age_days > days_to_keep:
                    try:
                        os.remove(file_path)
                        deleted_count += 1
                    except Exception as e:
                        print(f"Error deleting {filename}: {e}")
        
        return deleted_count


# Main execution
if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Ensure invoice folder exists
    ensure_invoice_folder()
    
    # Check if migration is needed
    config = Config()
    db_path = config.get('db_path', 'data/medtran.db')
    
    if os.path.exists(db_path):
        # Check if we need to migrate from SQLite to MongoDB
        print("SQLite database found. Consider running migration:")
        print("python migration/sqlite_to_mongo.py --sqlite-path data/medtran.db --create-backup")
    
    # Create and show main window
    try:
        window = MainWindow()
        window.show()
        sys.exit(app.exec_())
    except Exception as e:
        logging.error(f"Application startup error: {e}")
        QMessageBox.critical(None, "Startup Error", 
                           f"Failed to start application:\n{str(e)}")
        sys.exit(1)
