import os
import sys
import json
import logging
import urllib.request
import tempfile
import shutil
import zipfile
import hashlib
import subprocess
from PyQt5.QtWidgets import QProgressDialog, QMessageBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal

class UpdateWorker(QThread):
    """Worker thread for downloading updates"""
    progress_updated = pyqtSignal(int)
    download_complete = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, download_url, destination_path):
        super().__init__()
        self.download_url = download_url
        self.destination_path = destination_path
    
    def run(self):
        """Run the download process"""
        try:
            # Create temp file for download
            temp_file, temp_path = tempfile.mkstemp()
            os.close(temp_file)
            
            # Download the file
            def report_progress(block_num, block_size, total_size):
                if total_size > 0:
                    percent = min(int((block_num * block_size / total_size) * 100), 100)
                    self.progress_updated.emit(percent)
            
            urllib.request.urlretrieve(self.download_url, temp_path, report_progress)
            
            # Move to destination
            shutil.move(temp_path, self.destination_path)
            
            # Signal completion
            self.download_complete.emit(self.destination_path)
            
        except Exception as e:
            self.error_occurred.emit(str(e))
            # Clean up temp file if it exists
            if 'temp_path' in locals() and os.path.exists(temp_path):
                os.remove(temp_path)

class AutoUpdater:
    """Automatic application update system"""
    
    def __init__(self, current_version, update_url, parent=None):
        self.current_version = current_version
        self.update_url = update_url
        self.parent = parent
        self.download_worker = None
    
    def check_for_updates(self):
        """Check if updates are available"""
        try:
            # Get update info from server
            response = urllib.request.urlopen(f"{self.update_url}/update_info.json")
            update_info = json.loads(response.read().decode())
            
            latest_version = update_info.get('version')
            
            if self.compare_versions(latest_version, self.current_version) > 0:
                # Update available
                return True, update_info
            else:
                # Already up to date
                return False, None
            
        except Exception as e:
            logging.error(f"Error checking for updates: {e}")
            return False, None
    
    def compare_versions(self, version1, version2):
        """Compare two version strings
        Returns:
            1 if version1 > version2
            0 if version1 == version2
            -1 if version1 < version2
        """
        v1_parts = [int(x) for x in version1.split('.')]
        v2_parts = [int(x) for x in version2.split('.')]
        
        for i in range(max(len(v1_parts), len(v2_parts))):
            v1 = v1_parts[i] if i < len(v1_parts) else 0
            v2 = v2_parts[i] if i < len(v2_parts) else 0
            
            if v1 > v2:
                return 1
            elif v1 < v2:
                return -1
        
        return 0
    
    def download_update(self, update_info):
        """Download the update package"""
        download_url = update_info.get('download_url')
        
        if not download_url:
            return False, "Invalid update information"
        
        # Create updates directory if it doesn't exist
        updates_dir = os.path.join(os.path.dirname(sys.executable), 'updates')
        os.makedirs(updates_dir, exist_ok=True)
        
        # Destination path for the update package
        update_filename = os.path.basename(download_url)
        destination_path = os.path.join(updates_dir, update_filename)
        
        # Show progress dialog
        progress = QProgressDialog("Downloading update...", "Cancel", 0, 100, self.parent)
        progress.setWindowTitle("Update Download")
        progress.setWindowModality(Qt.WindowModal)
        
        # Create download worker
        self.download_worker = UpdateWorker(download_url, destination_path)
        self.download_worker.progress_updated.connect(progress.setValue)
        self.download_worker.download_complete.connect(lambda path: self.install_update(path, update_info))
        self.download_worker.error_occurred.connect(lambda error: self.show_error(error))
        
        # Connect cancel button
        progress.canceled.connect(self.download_worker.terminate)
        
        # Start download
        self.download_worker.start()
        
        # Show progress dialog
        progress.exec_()
    
    def install_update(self, update_path, update_info):
        """Install the downloaded update"""
        try:
            # Verify file integrity
            if 'checksum' in update_info:
                if not self.verify_checksum(update_path, update_info['checksum']):
                    raise Exception("Update file integrity check failed")
            
            # Check if it's a zip file
            if update_path.endswith('.zip'):
                # Extract update
                extract_dir = os.path.join(os.path.dirname(update_path), 'extracted')
                os.makedirs(extract_dir, exist_ok=True)
                
                with zipfile.ZipFile(update_path, 'r') as zip_ref:
                    zip_ref.extractall(extract_dir)
                
                # Look for installer or executable
                installer = None
                
                for file in os.listdir(extract_dir):
                    if file.endswith('.exe') and 'install' in file.lower():
                        installer = os.path.join(extract_dir, file)
                        break
                
                if installer:
                    # Ask user to install
                    reply = QMessageBox.question(
                        self.parent, "Install Update",
                        f"Update downloaded successfully. Install now?\n\n"
                        f"The application will close and the installer will start.",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes
                    )
                    
                    if reply == QMessageBox.Yes:
                        # Start installer and exit
                        subprocess.Popen(installer)
                        sys.exit(0)
                else:
                    QMessageBox.information(
                        self.parent, "Update Downloaded",
                        f"Update downloaded to:\n{extract_dir}\n\n"
                        f"Please manually update the application."
                    )
            else:
                QMessageBox.information(
                    self.parent, "Update Downloaded",
                    f"Update downloaded to:\n{update_path}\n\n"
                    f"Please manually update the application."
                )
                
        except Exception as e:
            self.show_error(str(e))
    
    def verify_checksum(self, file_path, expected_checksum):
        """Verify file integrity using checksum"""
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                
            # Calculate SHA-256 hash
            file_hash = hashlib.sha256(file_data).hexdigest()
            
            return file_hash == expected_checksum
            
        except Exception as e:
            logging.error(f"Checksum verification error: {e}")
            return False
    
    def show_error(self, error_message):
        """Show error message"""
        QMessageBox.critical(
            self.parent, "Update Error",
            f"An error occurred during the update:\n{error_message}"
        )