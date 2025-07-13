import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QFileDialog, QGroupBox, QFormLayout, QComboBox,
    QMessageBox, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, 
    QCheckBox, QTimeEdit, QSpinBox, QProgressDialog, QApplication, QLabel,
    QProgressBar
)
from PyQt5.QtCore import QDateTime, Qt, QTime
from PyQt5.QtGui import QColor
import os
import sys
import json
import logging

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.database.mongo_adapter import MongoAdapter
    from src.config import Config
except ImportError:
    # Fallback for transition period
    print("Warning: Could not import MongoDB components")

class RestoreDialog(QDialog):
    def __init__(self, backup_files, parent=None):
        super().__init__(parent)
        self.backup_files = backup_files
        self.selected_backup = None
        self.initUI()

    def initUI(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Restore MongoDB Backup")
        self.setMinimumWidth(400)
        
        # Main layout
        layout = QVBoxLayout()
        
        # Add warning label
        warning_label = QLabel(
            "<b>Warning:</b> Restoring a backup will overwrite current data. "
            "Make sure to create a backup of your current data first."
        )
        warning_label.setWordWrap(True)
        warning_label.setStyleSheet("color: red;")
        layout.addWidget(warning_label)
        
        # Add list widget
        self.list_widget = QListWidget()
        for backup_file in self.backup_files:
            # Extract timestamp from filename
            filename = os.path.basename(backup_file)
            item = QListWidgetItem(f"MongoDB Backup - {filename}")
            item.setData(Qt.UserRole, backup_file)
            self.list_widget.addItem(item)
        
        layout.addWidget(QLabel("Select a MongoDB backup to restore:"))
        layout.addWidget(self.list_widget)
        
        # Add buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
        
        self.setLayout(layout)
    
    def accept(self):
        """Handle dialog acceptance"""
        selected_items = self.list_widget.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Selection Required", "Please select a backup to restore.")
            return
        
        self.selected_backup = selected_items[0].data(Qt.UserRole)
        super().accept()

class SettingsTab(QWidget):
    def __init__(self, config=None):
        super().__init__()
        try:
            self.config = config
            self.db = MongoAdapter()
            self.initUI()
            
        except Exception as e:
            print(f"Error initializing Settings tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Settings tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the settings tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.config if hasattr(self, 'config') else None)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Settings tab: {str(e)}")
    
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Database Settings
        db_group = QGroupBox("MongoDB Database Settings")
        db_layout = QFormLayout()
        
        # MongoDB connection info
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setText("MongoDB Atlas Connection")
        self.db_path_edit.setReadOnly(True)
        db_layout.addRow("Database:", self.db_path_edit)
        
        # Connection status
        self.connection_status_label = QLabel("Checking connection...")
        self.checkConnectionStatus()
        db_layout.addRow("Status:", self.connection_status_label)
        
        # Test connection button
        self.test_connection_btn = QPushButton("Test Connection")
        self.test_connection_btn.clicked.connect(self.testConnection)
        db_layout.addRow("", self.test_connection_btn)
              
        # Backup location
        self.backup_path_edit = QLineEdit()
        backup_dir = os.path.join(os.getcwd(), "data", "backups")
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir, exist_ok=True)
        self.backup_path_edit.setText(backup_dir)
        
        backup_path_layout = QHBoxLayout()
        backup_path_layout.addWidget(self.backup_path_edit)
        
        self.browse_backup_btn = QPushButton("Browse")
        self.browse_backup_btn.clicked.connect(self.browseBackupPath)
        backup_path_layout.addWidget(self.browse_backup_btn)
        
        db_layout.addRow("Backup Location:", backup_path_layout)
        
        db_group.setLayout(db_layout)
        main_layout.addWidget(db_group)
        
        # Backup & Restore
        backup_group = QGroupBox("MongoDB Backup & Restore")
        backup_layout = QVBoxLayout()
        
        # Backup button
        self.backup_btn = QPushButton("Create MongoDB Backup")
        self.backup_btn.clicked.connect(self.createBackup)
        backup_layout.addWidget(self.backup_btn)
        
        # Recent backups
        backup_layout.addWidget(QLabel("Recent MongoDB Backups:"))
        self.backups_list = QListWidget()
        self.loadBackupsList()
        backup_layout.addWidget(self.backups_list)
        
        # Restore button
        self.restore_btn = QPushButton("Restore from MongoDB Backup")
        self.restore_btn.clicked.connect(self.restoreBackup)
        backup_layout.addWidget(self.restore_btn)
        
        # Export button
        self.export_btn = QPushButton("Export Data to CSV")
        self.export_btn.clicked.connect(self.exportData)
        backup_layout.addWidget(self.export_btn)

        # Import button
        self.import_btn = QPushButton("Import Data from CSV")
        self.import_btn.clicked.connect(self.importData)
        backup_layout.addWidget(self.import_btn)

        backup_group.setLayout(backup_layout)
        main_layout.addWidget(backup_group)
        
        # Application Settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout()
        
        # Currency format
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["Rs. (PKR)", "$ (USD)", "€ (EUR)"])
        app_layout.addRow("Currency Format:", self.currency_combo)
        
        # Log level
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["INFO", "DEBUG", "WARNING", "ERROR"])
        self.log_level_combo.currentIndexChanged.connect(self.setLogLevel)
        app_layout.addRow("Logging Level:", self.log_level_combo)
        
        # Save settings button
        self.save_settings_btn = QPushButton("Save Settings")
        self.save_settings_btn.clicked.connect(self.saveSettings)
        app_layout.addRow("", self.save_settings_btn)
        
        app_group.setLayout(app_layout)
        main_layout.addWidget(app_group)
        
        # Cloud Information
        cloud_group = QGroupBox("Cloud Information")
        cloud_layout = QVBoxLayout()
        
        cloud_info = QLabel(
            "MongoDB Atlas Cloud Features:\n\n"
            "✓ Automatic cloud backup and redundancy\n"
            "✓ Global data distribution\n"
            "✓ Built-in security and monitoring\n"
            "✓ Automatic scaling and performance optimization\n\n"
            "Local Backup: Use the backup buttons above for additional local copies."
        )
        cloud_info.setWordWrap(True)
        cloud_layout.addWidget(cloud_info)
        
        cloud_group.setLayout(cloud_layout)
        main_layout.addWidget(cloud_group)
        
        # About
        about_label = QLabel(
            "Medical Rep Transaction Software\n"
            "Version 2.0 - \n"
            "© 2025 BSOLS Technologies\n"
        )
        about_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(about_label)
        
        self.setLayout(main_layout)

    def checkConnectionStatus(self):
        """Check MongoDB connection status"""
        try:
            if self.db.connected:
                self.connection_status_label.setText("✓ Connected to MongoDB Atlas")
                self.connection_status_label.setStyleSheet("color: green; font-weight: bold;")
            else:
                self.connection_status_label.setText("✗ Not Connected")
                self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")
        except Exception as e:
            self.connection_status_label.setText(f"✗ Connection Error: {str(e)}")
            self.connection_status_label.setStyleSheet("color: red; font-weight: bold;")

    def testConnection(self):
        """Test MongoDB connection"""
        try:
            # Test connection by getting collection count
            customers = self.db.get_customers()
            products = self.db.get_products()
            
            QMessageBox.information(
                self, "Connection Test",
                f"✓ Connection successful!\n\n"
                f"Database contains:\n"
                f"• {len(customers)} customers\n"
                f"• {len(products)} products"
            )
            self.checkConnectionStatus()
            
        except Exception as e:
            QMessageBox.critical(
                self, "Connection Test Failed",
                f"✗ Could not connect to MongoDB:\n{str(e)}"
            )
            self.checkConnectionStatus()

    def browseBackupPath(self):
        """Browse for backup directory"""
        backup_dir = QFileDialog.getExistingDirectory(
            self, "Select Backup Directory", self.backup_path_edit.text()
        )
        
        if backup_dir:
            self.backup_path_edit.setText(backup_dir)
    
    def loadBackupsList(self):
        """Load list of MongoDB backups from backup directory"""
        self.backups_list.clear()
        
        backup_dir = self.backup_path_edit.text()
        if not os.path.exists(backup_dir):
            return
        
        # Find all MongoDB backup directories
        backup_items = []
        for item in os.listdir(backup_dir):
            item_path = os.path.join(backup_dir, item)
            if os.path.isdir(item_path) and item.startswith("mongodb_backup_"):
                backup_items.append(item_path)
        
        # Sort by modification time, newest first
        backup_items.sort(key=os.path.getmtime, reverse=True)
        
        # Add to list widget
        for backup_item in backup_items:
            timestamp = os.path.getmtime(backup_item)
            date_str = QDateTime.fromSecsSinceEpoch(int(timestamp)).toString("yyyy-MM-dd hh:mm:ss")
            
            filename = os.path.basename(backup_item)
            
            item = QListWidgetItem(f"{filename} - Created: {date_str}")
            item.setData(Qt.UserRole, backup_item)
            self.backups_list.addItem(item)

    def createBackup(self):
        """Create a manual backup of the MongoDB database"""
        try:
            backup_dir = self.backup_path_edit.text()
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            backup_filename = f"mongodb_backup_{timestamp}"
            backup_path = os.path.join(backup_dir, backup_filename)
            os.makedirs(backup_path, exist_ok=True)
            
            # Show progress dialog
            progress = QProgressDialog("Creating MongoDB backup...", "Cancel", 0, 4, self)
            progress.setWindowTitle("Backup Progress")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Export each collection to JSON
            collections = ['customers', 'products', 'entries', 'transactions']
            
            for i, collection in enumerate(collections):
                if progress.wasCanceled():
                    return
                
                progress.setValue(i)
                progress.setLabelText(f"Backing up {collection}...")
                QApplication.processEvents()
                
                if collection == 'customers':
                    data = self.db.get_customers()
                elif collection == 'products':
                    data = self.db.get_products()
                elif collection == 'entries':
                    data = self.db.get_entries()
                elif collection == 'transactions':
                    data = self.db.get_transactions()
                else:
                    data = []
                
                # Save to JSON file
                json_file = os.path.join(backup_path, f"{collection}.json")
                with open(json_file, 'w', encoding='utf-8') as f:
                    json.dump(data, f, indent=2, default=str)
            
            progress.setValue(4)
            progress.close()
            
            QMessageBox.information(
                self, "Backup Created",
                f"MongoDB backup created successfully!\n\nLocation: {backup_path}"
            )
            
            # Refresh backups list
            self.loadBackupsList()
            
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup:\n{str(e)}")

    def restoreBackup(self):
        """Restore MongoDB database from a backup"""
        try:
            backup_dir = self.backup_path_edit.text()
            if not os.path.exists(backup_dir):
                QMessageBox.warning(self, "No Backups", "No backup directory found.")
                return
            
            # Get list of MongoDB backup folders
            backup_items = []
            for item in os.listdir(backup_dir):
                item_path = os.path.join(backup_dir, item)
                if os.path.isdir(item_path) and item.startswith("mongodb_backup_"):
                    backup_items.append(item_path)
            
            if not backup_items:
                QMessageBox.warning(self, "No Backups", "No MongoDB backup files found.")
                return
            
            # Show restore dialog
            dialog = RestoreDialog(backup_items, self)
            if dialog.exec_() == QDialog.Accepted:
                self.restoreMongoDBBackup(dialog.selected_backup)
                    
        except Exception as e:
            QMessageBox.critical(self, "Restore Error", f"Failed to restore backup:\n{str(e)}")
    
    def restoreMongoDBBackup(self, backup_path):
        """Restore MongoDB backup from JSON files"""
        try:
            # Confirm restore
            reply = QMessageBox.question(
                self, "Confirm Restore",
                "This will replace ALL current data with the backup data.\n\n"
                "Are you sure you want to continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            # Check if all required files exist
            required_files = ['customers.json', 'products.json', 'entries.json', 'transactions.json']
            missing_files = []
            
            for file in required_files:
                file_path = os.path.join(backup_path, file)
                if not os.path.exists(file_path):
                    missing_files.append(file)
            
            if missing_files:
                QMessageBox.warning(
                    self, "Incomplete Backup",
                    f"Backup is missing files:\n{', '.join(missing_files)}\n\nRestore cancelled."
                )
                return
            
            # Show progress dialog
            progress = QProgressDialog("Restoring MongoDB backup...", "Cancel", 0, len(required_files), self)
            progress.setWindowTitle("Restore Progress")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Clear existing data first
            progress.setLabelText("Clearing existing data...")
            QApplication.processEvents()
            
            if hasattr(self.db, 'clear_all_collections'):
                self.db.clear_all_collections()
            
            # Restore each collection
            for i, file in enumerate(required_files):
                if progress.wasCanceled():
                    return
                
                collection_name = file.replace('.json', '')
                progress.setValue(i)
                progress.setLabelText(f"Restoring {collection_name}...")
                QApplication.processEvents()
                
                file_path = os.path.join(backup_path, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                # Insert data using MongoDB adapter methods
                if data and hasattr(self.db, f'restore_{collection_name}'):
                    getattr(self.db, f'restore_{collection_name}')(data)
                elif data:
                    # Fallback to individual inserts
                    for item in data:
                        if collection_name == 'customers':
                            self.db.add_customer(
                                item.get('name', ''), 
                                item.get('contact', ''), 
                                item.get('address', '')
                            )
                        elif collection_name == 'products':
                            self.db.add_product(
                                item.get('name', ''), 
                                item.get('description', ''), 
                                item.get('unit_price', 0),
                                item.get('batch_number', ''),
                                item.get('expiry_date', '')
                            )
            
            progress.setValue(len(required_files))
            progress.close()
            
            QMessageBox.information(
                self, "Restore Complete",
                "MongoDB database has been restored successfully from backup!"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Restore Error", f"Failed to restore MongoDB backup:\n{str(e)}")

    def exportData(self):
        """Export MongoDB database to CSV files"""
        try:
            # Get export directory
            export_dir = QFileDialog.getExistingDirectory(
                self, "Select Export Directory", os.path.expanduser("~")
            )
            
            if not export_dir:
                return
            
            # Create timestamp folder
            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            export_folder = os.path.join(export_dir, f"medtran_export_{timestamp}")
            os.makedirs(export_folder, exist_ok=True)
            
            # Show progress dialog
            progress = QProgressDialog("Exporting data to CSV...", "Cancel", 0, 4, self)
            progress.setWindowTitle("Export Progress")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            import csv
            
            # Export customers
            progress.setValue(0)
            progress.setLabelText("Exporting customers...")
            QApplication.processEvents()
            
            customers = self.db.get_customers()
            if customers:
                with open(os.path.join(export_folder, "customers.csv"), 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=customers[0].keys())
                    writer.writeheader()
                    writer.writerows(customers)
            
            # Export products
            progress.setValue(1)
            progress.setLabelText("Exporting products...")
            QApplication.processEvents()
            
            products = self.db.get_products()
            if products:
                with open(os.path.join(export_folder, "products.csv"), 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=products[0].keys())
                    writer.writeheader()
                    writer.writerows(products)
            
            # Export entries
            progress.setValue(2)
            progress.setLabelText("Exporting entries...")
            QApplication.processEvents()
            
            entries = self.db.get_entries()
            if entries:
                with open(os.path.join(export_folder, "entries.csv"), 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=entries[0].keys())
                    writer.writeheader()
                    writer.writerows(entries)
            
            # Export transactions
            progress.setValue(3)
            progress.setLabelText("Exporting transactions...")
            QApplication.processEvents()
            
            transactions = self.db.get_transactions()
            if transactions:
                with open(os.path.join(export_folder, "transactions.csv"), 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=transactions[0].keys())
                    writer.writeheader()
                    writer.writerows(transactions)
            
            progress.setValue(4)
            progress.close()
            
            QMessageBox.information(
                self, "Export Complete",
                f"Data exported successfully!\n\nLocation: {export_folder}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data:\n{str(e)}")
    
    def importData(self):
        """Import data from CSV files to MongoDB"""
        try:
            import_dir = QFileDialog.getExistingDirectory(
                self, "Select Import Directory containing CSV files"
            )
            
            if not import_dir:
                return
            
            # Check for required files
            required_files = ['customers.csv', 'products.csv']
            available_files = []
            
            for file in ['customers.csv', 'products.csv', 'entries.csv', 'transactions.csv']:
                if os.path.exists(os.path.join(import_dir, file)):
                    available_files.append(file)
            
            if not available_files:
                QMessageBox.warning(
                    self, "No CSV Files", 
                    "No CSV files found in the selected directory."
                )
                return
            
            # Confirm import
            reply = QMessageBox.question(
                self, "Confirm Import",
                f"This will import data from:\n{', '.join(available_files)}\n\n"
                "This may add to or modify existing data. Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            import csv
            
            # Show progress dialog
            progress = QProgressDialog("Importing CSV data...", "Cancel", 0, len(available_files), self)
            progress.setWindowTitle("Import Progress")
            progress.setWindowModality(Qt.WindowModal)
            progress.show()
            
            # Import each available file
            for i, file in enumerate(available_files):
                if progress.wasCanceled():
                    return
                
                progress.setValue(i)
                progress.setLabelText(f"Importing {file}...")
                QApplication.processEvents()
                
                file_path = os.path.join(import_dir, file)
                
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    
                    if file == 'customers.csv':
                        for row in reader:
                            self.db.add_customer(
                                row.get('name', ''), 
                                row.get('contact', ''), 
                                row.get('address', '')
                            )
                    elif file == 'products.csv':
                        for row in reader:
                            self.db.add_product(
                                row.get('name', ''), 
                                row.get('description', ''), 
                                float(row.get('unit_price', 0)),
                                row.get('batch_number', ''),
                                row.get('expiry_date', '')
                            )
            
            progress.setValue(len(available_files))
            progress.close()
            
            QMessageBox.information(
                self, "Import Complete", 
                f"Successfully imported {len(available_files)} CSV files."
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import data:\n{str(e)}")

    def setLogLevel(self):
        """Update logging level based on selection"""
        level_map = {
            "INFO": logging.INFO,
            "DEBUG": logging.DEBUG,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR
        }
        
        level = self.log_level_combo.currentText()
        logging.getLogger().setLevel(level_map[level])
        
        logging.info(f"Log level changed to {level}")
    
    def saveSettings(self):
        """Save application settings"""
        try:
            settings = {
                'currency_format': self.currency_combo.currentText(),
                'log_level': self.log_level_combo.currentText(),
                'backup_path': self.backup_path_edit.text()
            }
            
            # Save to a simple JSON file
            settings_file = os.path.join(os.getcwd(), "data", "settings.json")
            os.makedirs(os.path.dirname(settings_file), exist_ok=True)
            
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            QMessageBox.information(self, "Settings Saved", "Application settings have been saved successfully!")
            
        except Exception as e:
            QMessageBox.warning(self, "Save Error", f"Could not save settings:\n{str(e)}")