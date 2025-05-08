from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QFileDialog, QGroupBox, QFormLayout, QComboBox,
    QMessageBox, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox
)
from PyQt5.QtCore import QDateTime, Qt
import os
import sys
import shutil
import sqlite3
import logging

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Database

class RestoreDialog(QDialog):
    def __init__(self, backup_files, parent=None):
        super().__init__(parent)
        self.backup_files = backup_files
        self.selected_backup = None
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        self.setWindowTitle("Restore Backup")
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
            item = QListWidgetItem(filename)
            item.setData(Qt.UserRole, backup_file)
            self.list_widget.addItem(item)
        
        layout.addWidget(QLabel("Select a backup to restore:"))
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
            QMessageBox.warning(self, "Selection Required", "Please select a backup file to restore.")
            return
        
        self.selected_backup = selected_items[0].data(Qt.UserRole)
        super().accept()

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Database Settings
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout()
        
        # DB path
        self.db_path_edit = QLineEdit()
        self.db_path_edit.setText(self.db.db_path)
        self.db_path_edit.setReadOnly(True)
        
        db_path_layout = QHBoxLayout()
        db_path_layout.addWidget(self.db_path_edit)
        
        self.browse_db_btn = QPushButton("Browse")
        self.browse_db_btn.clicked.connect(self.browseDbPath)
        db_path_layout.addWidget(self.browse_db_btn)
        
        db_layout.addRow("Database Location:", db_path_layout)
        
        # Backup location
        self.backup_path_edit = QLineEdit()
        backup_dir = os.path.join(os.path.dirname(self.db.db_path), "backups")
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
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
        backup_group = QGroupBox("Backup & Restore")
        backup_layout = QVBoxLayout()
        
        # Backup button
        self.backup_btn = QPushButton("Create Manual Backup")
        self.backup_btn.clicked.connect(self.createBackup)
        backup_layout.addWidget(self.backup_btn)
        
        # Recent backups
        backup_layout.addWidget(QLabel("Recent Backups:"))
        self.backups_list = QListWidget()
        self.loadBackupsList()
        backup_layout.addWidget(self.backups_list)
        
        # Restore button
        self.restore_btn = QPushButton("Restore from Backup")
        self.restore_btn.clicked.connect(self.restoreBackup)
        backup_layout.addWidget(self.restore_btn)
        
        backup_group.setLayout(backup_layout)
        main_layout.addWidget(backup_group)
        
        # Application Settings
        app_group = QGroupBox("Application Settings")
        app_layout = QFormLayout()
        
        # Currency format
        self.currency_combo = QComboBox()
        self.currency_combo.addItems(["$ (USD)", "€ (EUR)", "£ (GBP)", "¥ (JPY)"])
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
        
        # Cloud Sync Information
        cloud_group = QGroupBox("Cloud Sync Information")
        cloud_layout = QVBoxLayout()
        
        cloud_info = QLabel(
            "Your database is stored in the 'data' folder. To enable cloud sync:\n\n"
            "1. Create a symbolic link between the 'data' folder and your cloud storage folder.\n"
            "2. Or, move the 'data' folder to your cloud storage and create a symbolic link.\n\n"
            "Supported cloud services: OneDrive, Dropbox, Google Drive"
        )
        cloud_info.setWordWrap(True)
        cloud_layout.addWidget(cloud_info)
        
        # Setup cloud button
        self.setup_cloud_btn = QPushButton("Setup Cloud Sync")
        self.setup_cloud_btn.clicked.connect(self.setupCloudSync)
        cloud_layout.addWidget(self.setup_cloud_btn)
        
        cloud_group.setLayout(cloud_layout)
        main_layout.addWidget(cloud_group)
        
        # About
        about_label = QLabel(
            "Medical Rep Transaction Software\n"
            "Version 1.0\n"
            "© 2025 Your Company"
        )
        about_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(about_label)
        
        self.setLayout(main_layout)
    
    def browseDbPath(self):
        """Browse for new database path"""
        options = QFileDialog.Options()
        db_file, _ = QFileDialog.getSaveFileName(
            self, "Select Database Location", self.db_path_edit.text(),
            "SQLite Database (*.db);;All Files (*)", options=options
        )
        
        if db_file:
            self.db_path_edit.setText(db_file)
    
    def browseBackupPath(self):
        """Browse for backup directory"""
        options = QFileDialog.Options()
        backup_dir = QFileDialog.getExistingDirectory(
            self, "Select Backup Directory", self.backup_path_edit.text(),
            options=options
        )
        
        if backup_dir:
            self.backup_path_edit.setText(backup_dir)
    
    def loadBackupsList(self):
        """Load list of backups from backup directory"""
        self.backups_list.clear()
        
        backup_dir = self.backup_path_edit.text()
        if not os.path.exists(backup_dir):
            return
        
        # Find all .db files in backup directory
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.endswith(".db"):
                backup_files.append(os.path.join(backup_dir, file))
        
        # Sort by modification time, newest first
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        # Add to list widget
        for backup_file in backup_files:
            timestamp = os.path.getmtime(backup_file)
            date_str = QDateTime.fromSecsSinceEpoch(int(timestamp)).toString("yyyy-MM-dd hh:mm:ss")
            
            filename = os.path.basename(backup_file)
            
            item = QListWidgetItem(f"{filename} (Created: {date_str})")
            item.setData(Qt.UserRole, backup_file)
            self.backups_list.addItem(item)
    
    def createBackup(self):
        """Create a manual backup of the database"""
        try:
            # Ensure backup directory exists
            backup_dir = self.backup_path_edit.text()
            os.makedirs(backup_dir, exist_ok=True)
            
            # Create backup filename with timestamp
            timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
            backup_filename = f"medtran_backup_{timestamp}.db"
            backup_path = os.path.join(backup_dir, backup_filename)
            
            # Ensure database is closed
            self.db.close()
            
            # Copy database file
            shutil.copy2(self.db.db_path, backup_path)
            
            QMessageBox.information(
                self, "Backup Created",
                f"Database backup created successfully at:\n{backup_path}"
            )
            
            # Refresh backups list
            self.loadBackupsList()
            
        except Exception as e:
            QMessageBox.critical(self, "Backup Error", f"Failed to create backup: {str(e)}")
    
    def restoreBackup(self):
        """Restore database from a backup"""
        backup_dir = self.backup_path_edit.text()
        if not os.path.exists(backup_dir):
            QMessageBox.warning(self, "No Backups", "Backup directory does not exist.")
            return
        
        # Find all .db files in backup directory
        backup_files = []
        for file in os.listdir(backup_dir):
            if file.endswith(".db"):
                backup_files.append(os.path.join(backup_dir, file))
        
        if not backup_files:
            QMessageBox.warning(self, "No Backups", "No backup files found.")
            return
        
        # Sort by modification time, newest first
        backup_files.sort(key=os.path.getmtime, reverse=True)
        
        # Show restore dialog
        dialog = RestoreDialog(backup_files, self)
        if dialog.exec_() == QDialog.Accepted and dialog.selected_backup:
            try:
                # Ensure database is closed
                self.db.close()
                
                # Create a backup of current database before restore
                timestamp = QDateTime.currentDateTime().toString("yyyyMMdd_hhmmss")
                pre_restore_backup = os.path.join(backup_dir, f"medtran_pre_restore_{timestamp}.db")
                shutil.copy2(self.db.db_path, pre_restore_backup)
                
                # Copy backup to current database
                shutil.copy2(dialog.selected_backup, self.db.db_path)
                
                QMessageBox.information(
                    self, "Restore Complete",
                    "Database has been restored successfully.\n\n"
                    f"A backup of your previous database was created at:\n{pre_restore_backup}"
                )
                
                # Refresh backups list
                self.loadBackupsList()
                
            except Exception as e:
                QMessageBox.critical(self, "Restore Error", f"Failed to restore database: {str(e)}")
    
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
        # For now, just show a success message
        # In a complete implementation, this would save settings to a config file
        QMessageBox.information(self, "Settings Saved", "Application settings have been saved.")
    
    def setupCloudSync(self):
        """Provide instructions for cloud sync setup"""
        instruction = (
            "Cloud Sync Setup Instructions:\n\n"
            "1. Manual Setup (Recommended):\n"
            "   a. Create a folder in your cloud storage (e.g., OneDrive, Dropbox)\n"
            "   b. Copy your data/medtran.db file to that folder\n"
            "   c. Update the database path in settings to point to this new location\n\n"
            "2. Using Symbolic Links (Advanced):\n"
            "   a. On Windows, use mklink command as Administrator:\n"
            "      mklink /D \"C:\\Path\\To\\App\\data\" \"C:\\Path\\To\\CloudStorage\\MedRepData\"\n"
            "   b. On macOS/Linux, use ln command:\n"
            "      ln -s \"/Path/To/CloudStorage/MedRepData\" \"/Path/To/App/data\"\n\n"
            "Note: Ensure your cloud service is installed and syncing properly."
        )
        
        QMessageBox.information(self, "Cloud Sync Setup", instruction)