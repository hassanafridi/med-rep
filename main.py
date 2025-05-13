import sys
import os
import logging
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTabWidget, QMessageBox, QDialog,
    QAction, QVBoxLayout, QLabel, QPushButton, QMenuBar
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize, Qt

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.ui.new_entry_tab import NewEntryTab
from src.ui.ledger_tab import LedgerTab
from src.ui.graphs_tab import GraphsTab
from src.ui.reports_tab import ReportsTab
from src.ui.settings_tab import SettingsTab
from src.ui.manage_data_tab import ManageDataTab
from src.database.db import Database
from src.config import Config
from src.user_auth import UserAuth
from src.ui.login_dialog import LoginDialog
from src.ui.advanced_charts import AdvancedChartsTab
from src.ui.invoice_generator import InvoiceGenerator
from src.ui.help_system import HelpBrowser
from src.database.audit_trail import AuditTrail

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    filename='app.log'
)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        # Load configuration
        self.config = Config()
        
        # Set logging level from config
        log_level = getattr(logging, self.config.get('log_level', 'INFO'))
        logging.getLogger().setLevel(log_level)
                
        # Initialize database
        self.db = Database(self.config.get('db_path'))
        self.init_database()
        
        # Initialize user authentication
        self.auth_manager = UserAuth(self.db.db_path)
        self.current_user = None
        
        # Show login dialog
        if not self.login():
            # If login fails, exit application
            sys.exit(0)
            
        # # Initialize UI
        # self.initUI()
        
        # Setup UI
        self.setWindowTitle("Medical Rep Transaction Software")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set window size from config
        width = self.config.get('window_width', 1000)
        height = self.config.get('window_height', 700)
        self.resize(width, height)
        
        # Create menu bar
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu('File')
        
        # Exit action
        exit_action = QAction('Exit', self)
        exit_action.setShortcut('Ctrl+Q')
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Tools menu
        tools_menu = menubar.addMenu('Tools')
        
        # Invoice Generator action
        invoice_action = QAction('Invoice Generator', self)
        invoice_action.triggered.connect(self.showInvoiceGenerator)
        tools_menu.addAction(invoice_action)
        
        # Advanced Charts action
        charts_action = QAction('Advanced Charts', self)
        charts_action.triggered.connect(self.showAdvancedCharts)
        tools_menu.addAction(charts_action)
        
        # Help menu
        help_menu = menubar.addMenu('Help')
        
        # Help action
        help_action = QAction('Help Contents', self)
        help_action.setShortcut('F1')
        help_action.triggered.connect(self.showHelp)
        help_menu.addAction(help_action)
        
        # About action
        about_action = QAction('About', self)
        about_action.triggered.connect(self.showAbout)
        help_menu.addAction(about_action)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create tab content
        self.create_new_entry_tab()
        self.create_ledger_tab()
        self.create_graphs_tab()
        self.create_reports_tab()
        self.create_manage_data_tab()
        self.create_settings_tab()
        
    def showInvoiceGenerator(self):
        """Show the invoice generator dialog"""
        invoice_generator = InvoiceGenerator(self.current_user)
        invoice_generator.show()

    def showAdvancedCharts(self):
        """Show the advanced charts window"""
        charts_window = QMainWindow(self)
        charts_window.setWindowTitle("Advanced Charts")
        charts_window.setMinimumSize(900, 600)
        
        charts_tab = AdvancedChartsTab()
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
        
    def login(self):
        """Show login dialog and authenticate user"""
        dialog = LoginDialog(self.auth_manager)
        result = dialog.exec_()
        
        if result == QDialog.Accepted:
            self.current_user = dialog.user_info
            return True
        
        return False
    
    def create_reports_tab(self):
        """Create and add the Reports tab"""
        reports_tab = ReportsTab()
        self.tabs.addTab(reports_tab, "Reports")
        
    def init_database(self):
        """Initialize the database and add sample data if needed"""
        try:
            # Use database path from config
            db_path = self.config.get('db_path')
            db = Database(db_path)
            db.init_db()
            
            # Check if we need to add sample data
            db.connect()
            db.cursor.execute("SELECT COUNT(*) FROM customers")
            count = db.cursor.fetchone()[0]
            db.close()
            
            if count == 0:
                db.insert_sample_data()
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", 
                                f"Failed to initialize database: {str(e)}\n"
                                "Please check the application log for details.")
    
    def create_new_entry_tab(self):
        """Create and add the New Entry tab"""
        new_entry_tab = NewEntryTab()
        self.tabs.addTab(new_entry_tab, "New Entry")
    
    def create_ledger_tab(self):
        """Create and add the Ledger tab"""
        ledger_tab = LedgerTab()
        self.tabs.addTab(ledger_tab, "Ledger")
    
    def create_graphs_tab(self):
        """Create and add the Graphs tab"""
        graphs_tab = GraphsTab()
        self.tabs.addTab(graphs_tab, "Graphs")
        
    def create_manage_data_tab(self):
        """Create and add the Manage Data tab"""
        manage_data_tab = ManageDataTab()
        self.tabs.addTab(manage_data_tab, "Manage Data")
    
    def create_settings_tab(self):
        """Create and add the Settings tab"""
        settings_tab = SettingsTab(self.config)
        self.tabs.addTab(settings_tab, "Settings")
    
    def closeEvent(self, event):
        """Handle window close event"""
        # Save window size to config
        self.config.set('window_width', self.width())
        self.config.set('window_height', self.height())
        
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())