import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTabWidget, QMessageBox
from PyQt5.QtGui import QIcon

# Add src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))
from src.ui.new_entry_tab import NewEntryTab
from src.ui.ledger_tab import LedgerTab
from src.ui.graphs_tab import GraphsTab
from src.database.db import Database

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Medical Rep Transaction Software")
        self.setGeometry(100, 100, 1000, 700)
        
        # Initialize database
        self.init_database()
        
        # Create tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create tab content
        self.create_new_entry_tab()
        self.create_ledger_tab()
        self.create_graphs_tab()
        self.create_settings_tab()
    
    def init_database(self):
        """Initialize the database and add sample data if needed"""
        try:
            db = Database()
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
    
    def create_settings_tab(self):
        """Create and add the Settings tab (placeholder for now)"""
        tab = QLabel("Settings Tab - Coming Soon")
        self.tabs.addTab(tab, "Settings")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())