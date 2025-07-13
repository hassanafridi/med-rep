import sys
import os
import time
import threading
from PyQt5.QtWidgets import QApplication, QSplashScreen, QProgressBar, QLabel, QVBoxLayout, QWidget, QMessageBox
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QPixmap, QFont

from src.database.mongo_adapter import MongoAdapter
from src.database.database_maintenance import DatabaseMaintenance
from src.user_auth import UserAuth
from main import MainWindow

class StartupSignals(QObject):
    """Signals for startup process"""
    progress = pyqtSignal(int, str)
    error = pyqtSignal(str)
    complete = pyqtSignal()

class SplashScreen(QSplashScreen):
    """Custom splash screen with progress bar"""
    def __init__(self):
        splash_pixmap = QPixmap(500, 300)
        splash_pixmap.fill(Qt.white)
        super().__init__(splash_pixmap)
        
        # Create layout
        layout = QVBoxLayout()
        
        # App title
        title_label = QLabel("Medical Rep Transaction Software")
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #0055A4;")
        title_label.setAlignment(Qt.AlignCenter)
        
        # Version
        version_label = QLabel("Version 1.0.0")
        version_label.setAlignment(Qt.AlignCenter)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setAlignment(Qt.AlignCenter)
        
        # Status label
        self.status_label = QLabel("Initializing...")
        self.status_label.setAlignment(Qt.AlignCenter)
        
        # Add widgets to layout
        layout.addStretch(1)
        layout.addWidget(title_label)
        layout.addWidget(version_label)
        layout.addStretch(1)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.status_label)
        layout.addStretch(1)
        
        # Create a widget to hold the layout
        container = QWidget(self)
        container.setLayout(layout)
        container.setGeometry(self.rect())
    
    def update_progress(self, value, message):
        """Update progress bar and status message"""
        self.progress_bar.setValue(value)
        self.status_label.setText(message)
        self.repaint()  # Force update

def initialize_application():
    """Initialize the application and perform startup checks"""
    signals = StartupSignals()
    
    def run_startup_tasks():
        try:
            # Step 1: Check directories
            signals.progress.emit(10, "Checking directories...")
            time.sleep(0.5)  # Simulate work
            os.makedirs(os.path.join(os.path.dirname(__file__), 'data'), exist_ok=True)
            os.makedirs(os.path.join(os.path.dirname(__file__), 'data', 'backups'), exist_ok=True)
            
            # Step 2: Initialize database
            signals.progress.emit(25, "Initializing database...")
            time.sleep(0.5)  # Simulate work
            
            # Check database type from config
            from src.config import Config
            config = Config()
            db_type = config.get('db_type', 'mongo')  # Default to MongoDB
            
            if db_type == 'mongo':
                db = MongoAdapter()  # Uses your Atlas URI automatically
                db.connect()
                db.init_db()
                
                # Check for sample data using MongoDB methods
                customers = db.get_customers_mongo()
                if len(customers) == 0:
                    signals.progress.emit(40, "Adding sample data...")
                    time.sleep(0.5)
                    db.insert_sample_data()
            else:
                # SQLite fallback
                db = MongoAdapter()  # Still use adapter for compatibility
                db.connect()
                db.init_db()
            
            # Step 3: Skip SQLite-specific integrity checks for MongoDB
            signals.progress.emit(55, "Verifying database connection...")
            time.sleep(0.5)
            
            if db_type == 'sqlite' and hasattr(db, 'db_path') and os.path.exists(db.db_path):
                db_maintenance = DatabaseMaintenance(db.db_path)
                integrity_ok, _ = db_maintenance.check_integrity()
                
                if not integrity_ok:
                    signals.error.emit("Database integrity check failed. Running repair...")
                    repair_ok, _ = db_maintenance.repair_database()
                    
                    if not repair_ok:
                        signals.error.emit("Database repair failed. Please contact support.")
                        return
            
            # Step 4: Initialize user authentication
            signals.progress.emit(70, "Initializing authentication...")
            time.sleep(0.5)
            
            # Pass the appropriate object to UserAuth
            auth = UserAuth(db)  # MongoAdapter will be detected correctly
            # Note: UserAuth automatically initializes users in __init__, no need to call init_user_table()
            
            # Step 5: Skip SQLite-specific optimization for MongoDB
            signals.progress.emit(85, "Finalizing setup...")
            time.sleep(0.5)
            
            if db_type == 'sqlite' and hasattr(db, 'db_path') and os.path.exists(db.db_path):
                try:
                    db_maintenance = DatabaseMaintenance(db.db_path)
                    db_maintenance.analyze_database()
                except:
                    pass  # Skip if DatabaseMaintenance doesn't work with MongoDB adapter
            
            # All done
            signals.progress.emit(100, "Startup complete!")
            time.sleep(0.5)
            signals.complete.emit()
            
        except Exception as e:
            signals.error.emit(f"Startup error: {str(e)}")
    
    # Run startup tasks in a separate thread
    startup_thread = threading.Thread(target=run_startup_tasks)
    startup_thread.start()
    
    return signals

def main():
    """Main application entry point"""
    # Create application
    app = QApplication(sys.argv)
    app.setApplicationName("Medical Rep Transaction Software")
    
    # Create and show splash screen
    splash = SplashScreen()
    splash.show()
    
    # Start initialization
    startup_signals = initialize_application()
    startup_signals.progress.connect(splash.update_progress)
    
    # Error handler
    def handle_error(message):
        QMessageBox.critical(None, "Startup Error", message)
        app.quit()
    
    startup_signals.error.connect(handle_error)
    
    # Launch main window when initialization is complete
    def launch_main_window():
        # Create and show main window
        main_window = MainWindow()
        main_window.show()
        
        # Close splash screen
        splash.finish(main_window)
    
    startup_signals.complete.connect(launch_main_window)
    
    # Start the event loop
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()