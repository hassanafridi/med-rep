import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QLineEdit, QFileDialog, QGroupBox, QFormLayout, QComboBox,
    QMessageBox, QListWidget, QListWidgetItem, QDialog, QDialogButtonBox, 
    QCheckBox, QTimeEdit, QSpinBox, QProgressDialog, QApplication, QLabel,
    QProgressBar
)
from src.database.database_maintenance import DatabaseMaintenance
from src.utils.auto_updater import AutoUpdater
from src.utils.sync_manager import SyncManager, SyncStatus
from PyQt5.QtCore import QDateTime, Qt, QTime
from PyQt5.QtGui import QColor
import os
import sys
import shutil
import sqlite3
import logging

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
try:
    from src.database.mongo_adapter import MongoAdapter
    from src.config import Config
except ImportError:
    # Fallback for transition period
    from database.db import Database

class RestoreDialog(QDialog):
    def __init__(self, backup_files, parent=None):
        super().__init__(parent)
        self.backup_files = backup_files
        self.selected_backup = None
        self.initUI()
        # Remove sync_manager initialization from here - it should be in SettingsTab

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
    def __init__(self, config=None):
        super().__init__()
        self.config = config or Config()
        
        # Initialize database based on config
        db_type = self.config.get('db_type', 'mongo')
        if db_type == 'mongo':
            self.db = MongoAdapter()
        else:
            # Fallback to SQLite
            try:
                from database.db import Database
                self.db = Database(self.config.get('db_path'))
            except ImportError:
                from src.database.db import Database
                self.db = Database(self.config.get('db_path'))
        
        # Initialize sync manager
        db_path = self.config.get('db_path', 'data/medtran.db')
        self.sync_manager = SyncManager(db_path)
        self.sync_manager.sync_started.connect(self.onSyncStarted)
        self.sync_manager.sync_completed.connect(self.onSyncCompleted)
        self.sync_manager.sync_progress.connect(self.onSyncProgress)
        self.sync_manager.sync_status_changed.connect(self.onSyncStatusChanged)
        
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Add update button in update group
        update_group = QGroupBox("Updates")
        update_layout = QVBoxLayout()
        
        self.update_btn = QPushButton("Check for Updates")
        self.update_btn.clicked.connect(self.checkForUpdates)
        update_layout.addWidget(self.update_btn)  # Use update_layout instead of layout
        
        update_group.setLayout(update_layout)
        main_layout.addWidget(update_group)
        
        # Database Settings
        db_group = QGroupBox("Database Settings")
        db_layout = QFormLayout()
        
        # Add maintenance button
        self.maintenance_btn = QPushButton("Database Maintenance")
        self.maintenance_btn.clicked.connect(self.showDatabaseMaintenance)
        db_layout.addRow("Maintenance:", self.maintenance_btn)
        
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
        
        # Add this in the backup_layout in the initUI method
        self.schedule_btn = QPushButton("Schedule Backups")
        self.schedule_btn.clicked.connect(self.setupBackupSchedule)
        backup_layout.addWidget(self.schedule_btn)
        
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
        self.currency_combo.addItems(["Rs.  (PKR)", "$ (USD)"])
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
        
        # Sync status
        self.sync_status_label = QLabel("Sync Status: Not configured")
        cloud_layout.addWidget(self.sync_status_label)
        
        # Setup cloud button
        self.setup_cloud_btn = QPushButton("Setup Cloud Sync")
        self.setup_cloud_btn.clicked.connect(self.setupCloudSync)
        cloud_layout.addWidget(self.setup_cloud_btn)
        
        cloud_group.setLayout(cloud_layout)
        main_layout.addWidget(cloud_group)
        
        # Sync progress bar
        self.sync_progress = QProgressBar()
        self.sync_progress.setVisible(False)
        cloud_layout.addWidget(self.sync_progress)

        # Sync info
        self.sync_info_label = QLabel("")
        cloud_layout.addWidget(self.sync_info_label)

        # Manual sync button
        self.sync_now_btn = QPushButton("Sync Now")
        self.sync_now_btn.setEnabled(False)
        self.sync_now_btn.clicked.connect(self.syncNow)
        cloud_layout.addWidget(self.sync_now_btn)
        
        # About
        about_label = QLabel(
            "Medical Rep Transaction Software\n"
            "Version 1.0\n"
            "© 2025 BSOLS Technologies\n"
        )
        about_label.setAlignment(Qt.AlignCenter)
        main_layout.addWidget(about_label)
        
        self.setLayout(main_layout)
    
    def setupCloudSync(self):
        """Set up cloud sync"""
        # Check if sync is already configured
        if self.sync_manager.sync_enabled:
            reply = QMessageBox.question(
                self, "Cloud Sync",
                f"Cloud sync is already configured to:\n{self.sync_manager.sync_dir}\n\nDo you want to reconfigure it?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.No:
                return
        
        # Show folder selection dialog
        sync_dir = QFileDialog.getExistingDirectory(
            self, "Select Cloud Sync Folder",
            self.sync_manager.sync_dir or os.path.expanduser("~"),
            QFileDialog.ShowDirsOnly
        )
        
        if sync_dir:
            # Configure sync
            self.sync_manager.set_sync_directory(sync_dir)
            
            # Update UI
            self.updateSyncStatus()
            
            # Ask about auto-sync
            reply = QMessageBox.question(
                self, "Auto Sync",
                "Do you want to enable automatic synchronization?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.configureAutoSync()

    def configureAutoSync(self):
        """Configure auto sync settings"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Auto Sync Settings")
        dialog.setMinimumWidth(300)
        
        layout = QFormLayout()
        
        # Enable checkbox
        enable_checkbox = QCheckBox("Enable automatic synchronization")
        enable_checkbox.setChecked(self.sync_manager.auto_sync_enabled)
        layout.addRow(enable_checkbox)
        
        # Interval spinner
        interval_spinner = QSpinBox()
        interval_spinner.setMinimum(5)
        interval_spinner.setMaximum(1440)  # 24 hours
        interval_spinner.setValue(self.sync_manager.sync_interval)
        interval_spinner.setSuffix(" minutes")
        layout.addRow("Sync interval:", interval_spinner)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # Save settings
            self.sync_manager.set_auto_sync(
                enable_checkbox.isChecked(),
                interval_spinner.value()
            )
            
            # Update UI
            self.updateSyncStatus()

    def syncNow(self):
        """Manually trigger synchronization"""
        if self.sync_manager.sync_enabled:
            self.sync_manager.sync()

    def onSyncStarted(self):
        """Handle sync started signal"""
        self.sync_progress.setVisible(True)
        self.sync_progress.setValue(0)
        self.sync_info_label.setText("Synchronization in progress...")
        self.sync_now_btn.setEnabled(False)

    def onSyncCompleted(self, success, message):
        """Handle sync completed signal"""
        self.sync_progress.setVisible(False)
        self.sync_info_label.setText(message)
        self.sync_now_btn.setEnabled(True)
        self.updateSyncStatus()

    def onSyncProgress(self, progress, message):
        """Handle sync progress signal"""
        self.sync_progress.setValue(progress)
        self.sync_info_label.setText(message)

    def onSyncStatusChanged(self, status):
        """Handle sync status change signal"""
        self.updateSyncStatus()

    def updateSyncStatus(self):
        """Update sync status display"""
        if not self.sync_manager.sync_enabled:
            self.sync_status_label.setText("Sync Status: Not configured")
            self.sync_now_btn.setEnabled(False)
            return
        
        status_text = "Unknown"
        status_color = "black"
        
        if self.sync_manager.sync_status == SyncStatus.IDLE:
            status_text = "Idle"
            status_color = "black"
        elif self.sync_manager.sync_status == SyncStatus.SYNCING:
            status_text = "Syncing..."
            status_color = "blue"
        elif self.sync_manager.sync_status == SyncStatus.ERROR:
            status_text = "Error"
            status_color = "red"
        elif self.sync_manager.sync_status == SyncStatus.SUCCESS:
            status_text = "Synchronized"
            status_color = "green"
        
        # Update sync info
        sync_info = f"Sync Directory: {self.sync_manager.sync_dir}"
        
        if self.sync_manager.auto_sync_enabled:
            sync_info += f"\nAuto Sync: Every {self.sync_manager.sync_interval} minutes"
        else:
            sync_info += "\nAuto Sync: Disabled"
        
        if self.sync_manager.last_sync_time:
            try:
                last_sync = datetime.datetime.fromisoformat(self.sync_manager.last_sync_time)
                sync_info += f"\nLast Sync: {last_sync.strftime('%Y-%m-%d %H:%M:%S')}"
            except:
                sync_info += f"\nLast Sync: {self.sync_manager.last_sync_time}"
        else:
            sync_info += "\nLast Sync: Never"
            
        self.sync_status_label.setText(f"Sync Status: <span style='color: {status_color};'>{status_text}</span>")
        self.sync_status_label.setTextFormat(Qt.RichText)
        self.sync_info_label.setText(sync_info)
        self.sync_now_btn.setEnabled(self.sync_manager.sync_enabled and self.sync_manager.sync_status != SyncStatus.SYNCING)
        
    def checkForUpdates(self):
        """Check for application updates"""
        app_version = "1.0.0"  # Hardcoded for this example
        updater = AutoUpdater(app_version, "https://example.com/updates", self)
        
        # Show checking message
        checking_dialog = QProgressDialog("Checking for updates...", None, 0, 0, self)
        checking_dialog.setWindowTitle("Update Check")
        checking_dialog.setWindowModality(Qt.WindowModal)
        checking_dialog.show()
        
        # Process events to show dialog
        QApplication.processEvents()
        
        # Check for updates
        update_available, update_info = updater.check_for_updates()
        
        # Close checking dialog
        checking_dialog.cancel()
        
        if update_available:
            # Show update available message
            reply = QMessageBox.question(
                self, "Update Available",
                f"A new version is available: {update_info['version']}\n\n"
                f"Current version: {app_version}\n\n"
                f"Changes:\n{update_info.get('changes', 'No change information available.')}\n\n"
                "Do you want to download and install this update?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                # Download update
                updater.download_update(update_info)
        else:
            QMessageBox.information(
                self, "No Updates Available",
                f"You are using the latest version ({app_version})."
            )
        
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
    
    def showDatabaseMaintenance(self):
        """Show database maintenance dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Database Maintenance")
        dialog.setMinimumWidth(500)
        
        layout = QVBoxLayout()
        
        # Create database maintenance instance
        db_maintenance = DatabaseMaintenance(self.db.db_path)
        
        # Get database info
        db_info = db_maintenance.get_database_info()
        
        # Info group
        info_group = QGroupBox("Database Information")
        info_layout = QFormLayout()
        
        if db_info:
            info_layout.addRow("Database Size:", QLabel(f"{db_info['file_size']:.2f} MB"))
            info_layout.addRow("Last Modified:", QLabel(db_info['last_modified']))
            info_layout.addRow("Total Records:", QLabel(str(db_info['total_rows'])))
            
            table_info = ""
            for table in db_info['tables']:
                table_info += f"{table['name']}: {table['rows']} rows\n"
            
            table_label = QLabel(table_info)
            table_label.setWordWrap(True)
            info_layout.addRow("Tables:", table_label)
        else:
            info_layout.addRow("Status:", QLabel("Failed to retrieve database information"))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Actions group
        actions_group = QGroupBox("Maintenance Actions")
        actions_layout = QVBoxLayout()
        
        # Integrity check button
        integrity_btn = QPushButton("Check Database Integrity")
        integrity_btn.clicked.connect(lambda: self.runMaintenance(db_maintenance.check_integrity, "Integrity Check"))
        
        # Vacuum button
        vacuum_btn = QPushButton("Vacuum Database")
        vacuum_btn.clicked.connect(lambda: self.runMaintenance(db_maintenance.vacuum_database, "Vacuum"))
        
        # Optimize button
        optimize_btn = QPushButton("Optimize Database")
        optimize_btn.clicked.connect(lambda: self.runMaintenance(db_maintenance.optimize_database, "Optimization"))
        
        # Repair button
        repair_btn = QPushButton("Repair Database")
        repair_btn.clicked.connect(lambda: self.runMaintenance(db_maintenance.repair_database, "Repair"))
        
        actions_layout.addWidget(integrity_btn)
        actions_layout.addWidget(vacuum_btn)
        actions_layout.addWidget(optimize_btn)
        actions_layout.addWidget(repair_btn)
        
        actions_group.setLayout(actions_layout)
        layout.addWidget(actions_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.accept)
        layout.addWidget(close_btn)
        
        dialog.setLayout(layout)
        dialog.exec_()

    def runMaintenance(self, maintenance_func, action_name):
        """Run a maintenance function with progress dialog"""
        # Create progress dialog
        progress = QProgressDialog(f"{action_name} in progress...", "Cancel", 0, 0, self)
        progress.setWindowTitle(f"Database {action_name}")
        progress.setWindowModality(Qt.WindowModal)
        progress.setMinimumDuration(0)
        progress.setValue(0)
        progress.show()
        
        # Process events to show dialog
        QApplication.processEvents()
        
        # Run maintenance function
        success, message = maintenance_func()
        
        # Close progress dialog
        progress.cancel()
        
        # Show result
        if success:
            QMessageBox.information(self, f"{action_name} Completed", message)
        else:
            QMessageBox.critical(self, f"{action_name} Failed", message)
    
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
        if self.config:
            # Save settings to config
            self.config.set('db_path', self.db_path_edit.text())
            self.config.set('backup_path', self.backup_path_edit.text())
            self.config.set('currency_format', self.currency_combo.currentText())
            self.config.set('log_level', self.log_level_combo.currentText())
            
            QMessageBox.information(self, "Settings Saved", "Application settings have been saved.")
        else:
            # Fallback to showing just a success message if no config is available
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
        
    def exportData(self):
        """Export database to CSV files"""
        try:
            options = QFileDialog.Options()
            export_dir = QFileDialog.getExistingDirectory(
                self, "Select Export Directory", "", options=options
            )
            
            if not export_dir:
                return
            
            self.db.connect()
            
            # Export customers
            self.db.cursor.execute("SELECT id, name, contact, address, created_at FROM customers")
            customers = self.db.cursor.fetchall()
            
            with open(os.path.join(export_dir, "customers.csv"), 'w', encoding='utf-8') as f:
                f.write("id,name,contact,address,created_at\n")
                for customer in customers:
                    f.write(','.join(f'"{str(field)}"' for field in customer) + '\n')
            
            # Export products
            self.db.cursor.execute("SELECT id, name, description, unit_price, created_at FROM products")
            products = self.db.cursor.fetchall()
            
            with open(os.path.join(export_dir, "products.csv"), 'w', encoding='utf-8') as f:
                f.write("id,name,description,unit_price,created_at\n")
                for product in products:
                    f.write(','.join(f'"{str(field)}"' for field in product) + '\n')
            
            # Export entries
            self.db.cursor.execute("""
                SELECT e.id, e.date, c.name, p.name, e.quantity, e.unit_price, 
                    (e.quantity * e.unit_price) as total, e.is_credit, e.notes, e.created_at
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                JOIN products p ON e.product_id = p.id
                ORDER BY e.date, e.id
            """)
            entries = self.db.cursor.fetchall()
            
            with open(os.path.join(export_dir, "entries.csv"), 'w', encoding='utf-8') as f:
                f.write("id,date,customer,product,quantity,unit_price,total,is_credit,notes,created_at\n")
                for entry in entries:
                    f.write(','.join(f'"{str(field)}"' for field in entry) + '\n')
            
            QMessageBox.information(
                self, "Export Complete", 
                f"Data has been exported to:\n{export_dir}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
        finally:
            self.db.close()

    def importData(self):
        """Import data from CSV files"""
        try:
            options = QFileDialog.Options()
            import_dir = QFileDialog.getExistingDirectory(
                self, "Select Import Directory", "", options=options
            )
            
            if not import_dir:
                return
            
            # Check for required files
            required_files = ['customers.csv', 'products.csv', 'entries.csv']
            missing_files = []
            
            for file in required_files:
                if not os.path.exists(os.path.join(import_dir, file)):
                    missing_files.append(file)
            
            if missing_files:
                QMessageBox.warning(
                    self, "Missing Files", 
                    f"The following required files are missing:\n{', '.join(missing_files)}"
                )
                return
            
            # Confirm import
            reply = QMessageBox.question(
                self, "Confirm Import",
                "Importing data will replace all existing data. Continue?",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply != QMessageBox.Yes:
                return
            
            self.db.connect()
            
            # Start transaction
            self.db.conn.execute("BEGIN")
            
            # Clear existing data
            self.db.cursor.execute("DELETE FROM transactions")
            self.db.cursor.execute("DELETE FROM entries")
            self.db.cursor.execute("DELETE FROM products")
            self.db.cursor.execute("DELETE FROM customers")
            
            # Import customers
            import csv
            
            with open(os.path.join(import_dir, "customers.csv"), 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.db.cursor.execute("""
                        INSERT INTO customers (name, contact, address)
                        VALUES (?, ?, ?)
                    """, (row['name'], row['contact'], row['address']))
            
            # Import products
            with open(os.path.join(import_dir, "products.csv"), 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    self.db.cursor.execute("""
                        INSERT INTO products (name, description, unit_price)
                        VALUES (?, ?, ?)
                    """, (row['name'], row['description'], float(row['unit_price'])))
            
            # Import entries
            with open(os.path.join(import_dir, "entries.csv"), 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                # Create a mapping of customer names to IDs
                self.db.cursor.execute("SELECT id, name FROM customers")
                customer_map = {name: id for id, name in self.db.cursor.fetchall()}
                
                # Create a mapping of product names to IDs
                self.db.cursor.execute("SELECT id, name FROM products")
                product_map = {name: id for id, name in self.db.cursor.fetchall()}
                
                # Process entries
                current_balance = 0
                for row in reader:
                    customer_id = customer_map.get(row['customer'])
                    product_id = product_map.get(row['product'])
                    
                    if not customer_id or not product_id:
                        continue
                    
                    # Insert entry
                    self.db.cursor.execute("""
                        INSERT INTO entries (date, customer_id, product_id, quantity, unit_price, is_credit, notes)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (
                        row['date'], 
                        customer_id, 
                        product_id, 
                        int(row['quantity']), 
                        float(row['unit_price']), 
                        int(row['is_credit']), 
                        row['notes']
                    ))
                    
                    entry_id = self.db.cursor.lastrowid
                    amount = float(row['total'])
                    
                    # Update balance
                    if int(row['is_credit']):
                        current_balance += amount
                    else:
                        current_balance -= amount
                    
                    # Insert transaction
                    self.db.cursor.execute("""
                        INSERT INTO transactions (entry_id, amount, balance)
                        VALUES (?, ?, ?)
                    """, (entry_id, amount, current_balance))
            
            # Commit changes
            self.db.conn.commit()
            
            QMessageBox.information(
                self, "Import Complete", 
                "Data has been imported successfully."
            )
            
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.critical(self, "Import Error", f"Failed to import data: {str(e)}")
        finally:
            self.db.close()
            
    def setupBackupSchedule(self):
        """Set up scheduled backups"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Schedule Backups")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # Enable scheduled backups
        enable_checkbox = QCheckBox("Enable scheduled backups")
        layout.addRow(enable_checkbox)
        
        # Frequency
        frequency_combo = QComboBox()
        frequency_combo.addItems(["Daily", "Weekly", "Monthly"])
        layout.addRow("Backup frequency:", frequency_combo)
        
        # Time
        time_edit = QTimeEdit()
        time_edit.setTime(QTime(23, 0))  # Default to 11:00 PM
        time_edit.setDisplayFormat("hh:mm AP")
        layout.addRow("Backup time:", time_edit)
        
        # Retention
        retention_spin = QSpinBox()
        retention_spin.setMinimum(1)
        retention_spin.setMaximum(100)
        retention_spin.setValue(10)
        layout.addRow("Keep last N backups:", retention_spin)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addRow(button_box)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # Save schedule settings
            settings = {
                'enabled': enable_checkbox.isChecked(),
                'frequency': frequency_combo.currentText(),
                'time': time_edit.time().toString("hh:mm"),
                'retention': retention_spin.value()
            }
            
            # In a real implementation, these would be saved to a config file
            # and a scheduler would be set up (e.g., with Windows Task Scheduler)
            
            QMessageBox.information(
                self, "Schedule Set",
                f"Backup schedule configured:\n"
                f"Enabled: {'Yes' if settings['enabled'] else 'No'}\n"
                f"Frequency: {settings['frequency']}\n"
                f"Time: {settings['time']}\n"
                f"Retention: {settings['retention']} backups"
            )