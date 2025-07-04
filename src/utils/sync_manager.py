import os
import sys
import time
import threading
import logging
import shutil
import sqlite3
import datetime
from PyQt5.QtCore import QObject, pyqtSignal, QTimer, QSettings

class SyncStatus:
    IDLE = 0
    SYNCING = 1
    ERROR = 2
    SUCCESS = 3

class SyncManager(QObject):
    """Manages data synchronization with cloud storage"""
    
    # Signals
    sync_started = pyqtSignal()
    sync_completed = pyqtSignal(bool, str)  # success, message
    sync_progress = pyqtSignal(int, str)  # progress percentage, message
    sync_status_changed = pyqtSignal(int)  # status code
    
    def __init__(self, db_path):
        super().__init__()
        self.db_path = db_path
        self.sync_dir = None
        self.sync_enabled = False
        self.auto_sync_enabled = False
        self.sync_interval = 30  # minutes
        self.last_sync_time = None
        self.sync_status = SyncStatus.IDLE
        self.sync_timer = QTimer()
        self.sync_timer.timeout.connect(self.auto_sync)
        
        # Load settings
        self.load_settings()
    
    def load_settings(self):
        """Load sync settings"""
        settings = QSettings("MedRepApp", "Sync")
        self.sync_dir = settings.value("sync_dir", None)
        self.sync_enabled = settings.value("sync_enabled", False, type=bool)
        self.auto_sync_enabled = settings.value("auto_sync_enabled", False, type=bool)
        self.sync_interval = settings.value("sync_interval", 30, type=int)
        self.last_sync_time = settings.value("last_sync_time", None)
        
        # Start sync timer if auto-sync is enabled
        if self.auto_sync_enabled:
            self.start_sync_timer()
    
    def save_settings(self):
        """Save sync settings"""
        settings = QSettings("MedRepApp", "Sync")
        settings.setValue("sync_dir", self.sync_dir)
        settings.setValue("sync_enabled", self.sync_enabled)
        settings.setValue("auto_sync_enabled", self.auto_sync_enabled)
        settings.setValue("sync_interval", self.sync_interval)
        settings.setValue("last_sync_time", self.last_sync_time)
    
    def set_sync_directory(self, sync_dir):
        """Set the sync directory"""
        self.sync_dir = sync_dir
        self.sync_enabled = bool(sync_dir)
        self.save_settings()
    
    def set_auto_sync(self, enabled, interval=None):
        """Enable/disable auto sync"""
        self.auto_sync_enabled = enabled
        
        if interval is not None:
            self.sync_interval = interval
        
        if enabled:
            self.start_sync_timer()
        else:
            self.sync_timer.stop()
        
        self.save_settings()
    
    def start_sync_timer(self):
        """Start the auto sync timer"""
        # Convert minutes to milliseconds
        self.sync_timer.start(self.sync_interval * 60 * 1000)
    
    def auto_sync(self):
        """Perform auto synchronization"""
        if self.sync_enabled and self.auto_sync_enabled:
            self.sync()
    
    def sync(self):
        """Synchronize database with cloud storage"""
        if not self.sync_enabled or not self.sync_dir:
            self.sync_status_changed.emit(SyncStatus.IDLE)
            return
        
        # Don't start a new sync if one is already in progress
        if self.sync_status == SyncStatus.SYNCING:
            return
        
        # Set status to syncing
        self.sync_status = SyncStatus.SYNCING
        self.sync_status_changed.emit(self.sync_status)
        
        # Start sync in a separate thread
        self.sync_started.emit()
        sync_thread = threading.Thread(target=self._sync_thread)
        sync_thread.daemon = True
        sync_thread.start()
    
    def _sync_thread(self):
        """Thread function for sync operation"""
        try:
            # Check if sync directory exists
            if not os.path.exists(self.sync_dir):
                os.makedirs(self.sync_dir, exist_ok=True)
            
            self.sync_progress.emit(10, "Checking sync directory...")
            
            # Sync file path in cloud directory
            sync_file = os.path.join(self.sync_dir, os.path.basename(self.db_path))
            
            # Check if we need to upload or download
            local_mod_time = os.path.getmtime(self.db_path) if os.path.exists(self.db_path) else 0
            remote_mod_time = os.path.getmtime(sync_file) if os.path.exists(sync_file) else 0
            
            self.sync_progress.emit(20, "Comparing file versions...")
            
            if not os.path.exists(sync_file):
                # No remote file, upload local
                self.sync_progress.emit(30, "Uploading database...")
                shutil.copy2(self.db_path, sync_file)
                self.sync_progress.emit(90, "Upload complete")
                
            elif local_mod_time > remote_mod_time:
                # Local is newer, upload
                self.sync_progress.emit(30, "Uploading database...")
                
                # Create a backup of remote file first
                backup_file = f"{sync_file}.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                shutil.copy2(sync_file, backup_file)
                
                self.sync_progress.emit(50, "Remote backup created...")
                
                # Copy local to remote
                shutil.copy2(self.db_path, sync_file)
                self.sync_progress.emit(90, "Upload complete")
                
            elif remote_mod_time > local_mod_time:
                # Remote is newer, download
                self.sync_progress.emit(30, "Downloading database...")
                
                # Create a backup of local file first
                backup_file = f"{self.db_path}.{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}.bak"
                if os.path.exists(self.db_path):
                    shutil.copy2(self.db_path, backup_file)
                
                self.sync_progress.emit(50, "Local backup created...")
                
                # Copy remote to local
                shutil.copy2(sync_file, self.db_path)
                self.sync_progress.emit(90, "Download complete")
                
            else:
                # Files are the same
                self.sync_progress.emit(50, "Files are already synchronized")
            
            # Update last sync time
            self.last_sync_time = datetime.datetime.now().isoformat()
            self.save_settings()
            
            self.sync_progress.emit(100, "Synchronization complete")
            
            # Set success status
            self.sync_status = SyncStatus.SUCCESS
            self.sync_status_changed.emit(self.sync_status)
            
            # Reset status after a delay
            def reset_status():
                time.sleep(5)  # 5 seconds
                self.sync_status = SyncStatus.IDLE
                self.sync_status_changed.emit(self.sync_status)
            
            threading.Thread(target=reset_status, daemon=True).start()
            
            # Emit completion signal
            self.sync_completed.emit(True, "Synchronization completed successfully")
            
        except Exception as e:
            logging.error(f"Sync error: {e}")
            
            # Set error status
            self.sync_status = SyncStatus.ERROR
            self.sync_status_changed.emit(self.sync_status)
            
            # Reset status after a delay
            def reset_status():
                time.sleep(5)  # 5 seconds
                self.sync_status = SyncStatus.IDLE
                self.sync_status_changed.emit(self.sync_status)
            
            threading.Thread(target=reset_status, daemon=True).start()
            
            # Emit completion signal with error
            self.sync_completed.emit(False, f"Synchronization failed: {str(e)}")