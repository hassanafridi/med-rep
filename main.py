"""
Main Application Integration for Enhanced MedRep
Updates to integrate the new features into your existing application
"""

# In your main.py or main_window.py

from PyQt5.QtWidgets import QMainWindow, QTabWidget, QStatusBar, QMessageBox, QApplication, QHBoxLayout
from PyQt5.QtCore import pyqtSignal
import sys
import os

# Import the enhanced tabs
from src.ui.new_entry_tab import NewEntryTab, InvoiceQuickViewDialog
from src.ui.ledger_tab import LedgerTab

# Import other existing tabs
from src.ui.dashboard_tab import DashboardTab
from src.ui.graphs_tab import GraphsTab
from src.ui.manage_data_tab import ManageDataTab
from src.ui.settings_tab import SettingsTab


class MainWindow(QMainWindow):
    """
    Enhanced Main Window with invoice integration
    """
    
    def __init__(self):
        super().__init__()
        self.current_user = {'user_id': 1, 'username': 'admin'}  # Example
        self.config = {'db_path': 'data/medtran.db'}  # Your config object with default db path
        self.initUI()
        
    def initUI(self):
        """Initialize the main window UI"""
        self.setWindowTitle("MedRep - Medical Representative Transaction Manager")
        self.setGeometry(100, 100, 1200, 800)
        
        # Create central widget with tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create status bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # Create all tabs
        self.create_dashboard_tab()
        self.create_new_entry_tab()
        self.create_ledger_tab()
        self.create_graphs_tab()
        self.create_manage_data_tab()
        self.create_settings_tab()
        
        # Show welcome message
        self.status_bar.showMessage("Welcome to MedRep - Enhanced with Auto Invoice Generation", 5000)
    
    def create_dashboard_tab(self):
        """Create the dashboard tab"""
        dashboard_tab = DashboardTab(self.current_user)
        self.tabs.addTab(dashboard_tab, "Dashboard")
    
    def create_new_entry_tab(self):
        """Create the enhanced new entry tab with invoice generation"""
        self.new_entry_tab = NewEntryTab()
        
        # Connect invoice generation signal
        self.new_entry_tab.entry_saved.connect(self.on_invoice_generated)
        
        self.tabs.addTab(self.new_entry_tab, "New Entry")
    
    def create_ledger_tab(self):
        """Create the enhanced ledger tab with invoice download"""
        self.ledger_tab = LedgerTab()
        self.tabs.addTab(self.ledger_tab, "Ledger")
        
        # Connect tab change to refresh ledger when selected
        self.tabs.currentChanged.connect(self.on_tab_changed)
    
    def create_graphs_tab(self):
        """Create the graphs tab"""
        graphs_tab = GraphsTab()
        self.tabs.addTab(graphs_tab, "Graphs")
    
    def create_manage_data_tab(self):
        """Create the manage data tab"""
        manage_data_tab = ManageDataTab()
        self.tabs.addTab(manage_data_tab, "Manage Data")
    
    def create_settings_tab(self):
        """Create the settings tab"""
        settings_tab = SettingsTab(self.config)
        self.tabs.addTab(settings_tab, "Settings")
    
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


# Utility functions for invoice management
class InvoiceManager:
    """
    Utility class for invoice management operations
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
    def get_invoice_statistics(db_connection):
        """Get invoice generation statistics"""
        try:
            cursor = db_connection.cursor()
            
            # Total invoices
            cursor.execute("SELECT COUNT(*) FROM entries WHERE notes LIKE '%Invoice: INV-%'")
            total_invoices = cursor.fetchone()[0]
            
            # This month's invoices
            cursor.execute("""
                SELECT COUNT(*) FROM entries 
                WHERE notes LIKE '%Invoice: INV-%' 
                AND date >= date('now', 'start of month')
            """)
            month_invoices = cursor.fetchone()[0]
            
            # Today's invoices
            cursor.execute("""
                SELECT COUNT(*) FROM entries 
                WHERE notes LIKE '%Invoice: INV-%' 
                AND date = date('now')
            """)
            today_invoices = cursor.fetchone()[0]
            
            return {
                'total': total_invoices,
                'this_month': month_invoices,
                'today': today_invoices
            }
            
        except Exception as e:
            print(f"Error getting invoice statistics: {e}")
            return {'total': 0, 'this_month': 0, 'today': 0}
    
    @staticmethod
    def cleanup_old_invoices(days_to_keep=90):
        """Clean up old invoice files"""
        import time
        
        invoice_folder = "invoices"
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
    
    # Optional: Run database migration
    db_path = "data/medtran.db"
    if os.path.exists(db_path):
        migrate_database_for_invoices(db_path)
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec_())