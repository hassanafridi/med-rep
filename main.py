import sys
import os
import logging
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QMessageBox
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QSize

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.ui.new_entry_tab import NewEntryTab
from src.ui.ledger_tab import LedgerTab
from src.ui.graphs_tab import GraphsTab
from src.ui.settings_tab import SettingsTab
from src.ui.manage_data_tab import ManageDataTab
from src.database.db import Database
from src.config import Config

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
        
        # Setup UI
        self.setWindowTitle("Medical Rep Transaction Software")
        self.setGeometry(100, 100, 1000, 700)
        
        # Set window size from config
        width = self.config.get('window_width', 1000)
        height = self.config.get('window_height', 700)
        self.resize(width, height)
        
        # Initialize database
        self.init_database()
        
        # Create tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create tab content
        self.create_new_entry_tab()
        self.create_ledger_tab()
        self.create_graphs_tab()
        self.create_manage_data_tab()
        self.create_settings_tab()
    
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