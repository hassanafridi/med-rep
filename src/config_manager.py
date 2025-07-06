# src/config_manager.py

"""
Configuration manager for switching between SQLite and MongoDB databases
"""

import json
import os
from typing import Dict, Any
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGroupBox, QRadioButton,
    QLineEdit, QLabel, QPushButton, QMessageBox, QFormLayout,
    QSpinBox, QCheckBox, QTabWidget, QWidget, QTextEdit
)
from PyQt5.QtCore import Qt

class DatabaseConfigDialog(QDialog):
    def __init__(self, current_config: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.current_config = current_config.copy()
        self.setWindowTitle("Database Configuration")
        self.setMinimumSize(500, 400)
        self.initUI()
        self.load_current_config()
    
    def initUI(self):
        """Initialize the configuration UI"""
        layout = QVBoxLayout()
        
        # Create tabs
        tab_widget = QTabWidget()
        
        # Database Selection Tab
        self.db_tab = self.create_database_tab()
        tab_widget.addTab(self.db_tab, "Database Selection")
        
        # MongoDB Settings Tab
        self.mongo_tab = self.create_mongodb_tab()
        tab_widget.addTab(self.mongo_tab, "MongoDB Settings")
        
        # Advanced Settings Tab
        self.advanced_tab = self.create_advanced_tab()
        tab_widget.addTab(self.advanced_tab, "Advanced Settings")
        
        layout.addWidget(tab_widget)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        test_btn = QPushButton("Test Connection")
        test_btn.clicked.connect(self.test_connection)
        button_layout.addWidget(test_btn)
        
        button_layout.addStretch()
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        save_btn = QPushButton("Save & Apply")
        save_btn.clicked.connect(self.save_config)
        button_layout.addWidget(save_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def create_database_tab(self) -> QWidget:
        """Create database selection tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Database type selection
        db_group = QGroupBox("Database Type")
        db_layout = QVBoxLayout()
        
        self.sqlite_radio = QRadioButton("SQLite Database")
        self.sqlite_radio.setChecked(True)
        self.sqlite_radio.toggled.connect(self.on_database_type_changed)
        db_layout.addWidget(self.sqlite_radio)
        
        self.mongodb_radio = QRadioButton("MongoDB Database")
        self.mongodb_radio.toggled.connect(self.on_database_type_changed)
        db_layout.addWidget(self.mongodb_radio)
        
        db_group.setLayout(db_layout)
        layout.addWidget(db_group)
        
        # SQLite settings
        self.sqlite_group = QGroupBox("SQLite Settings")
        sqlite_layout = QFormLayout()
        
        self.sqlite_path_edit = QLineEdit()
        self.sqlite_path_edit.setPlaceholderText("data/medtran.db")
        sqlite_layout.addRow("Database File:", self.sqlite_path_edit)
        
        self.sqlite_group.setLayout(sqlite_layout)
        layout.addWidget(self.sqlite_group)
        
        # MongoDB basic settings
        self.mongodb_group = QGroupBox("MongoDB Basic Settings")
        mongodb_layout = QFormLayout()
        
        self.mongo_host_edit = QLineEdit()
        self.mongo_host_edit.setPlaceholderText("localhost")
        mongodb_layout.addRow("Host:", self.mongo_host_edit)
        
        self.mongo_port_spin = QSpinBox()
        self.mongo_port_spin.setRange(1, 65535)
        self.mongo_port_spin.setValue(27017)
        mongodb_layout.addRow("Port:", self.mongo_port_spin)
        
        self.mongo_database_edit = QLineEdit()
        self.mongo_database_edit.setPlaceholderText("medtran_db")
        mongodb_layout.addRow("Database Name:", self.mongo_database_edit)
        
        self.mongodb_group.setLayout(mongodb_layout)
        layout.addWidget(self.mongodb_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_mongodb_tab(self) -> QWidget:
        """Create MongoDB advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Connection settings
        conn_group = QGroupBox("Connection Settings")
        conn_layout = QFormLayout()
        
        # Authentication
        self.mongo_username_edit = QLineEdit()
        self.mongo_username_edit.setPlaceholderText("Optional")
        conn_layout.addRow("Username:", self.mongo_username_edit)
        
        self.mongo_password_edit = QLineEdit()
        self.mongo_password_edit.setEchoMode(QLineEdit.Password)
        self.mongo_password_edit.setPlaceholderText("Optional")
        conn_layout.addRow("Password:", self.mongo_password_edit)
        
        # Authentication database
        self.mongo_auth_db_edit = QLineEdit()
        self.mongo_auth_db_edit.setPlaceholderText("admin")
        conn_layout.addRow("Auth Database:", self.mongo_auth_db_edit)
        
        # SSL/TLS
        self.mongo_ssl_checkbox = QCheckBox("Use SSL/TLS")
        conn_layout.addRow("Security:", self.mongo_ssl_checkbox)
        
        # Connection timeout
        self.mongo_timeout_spin = QSpinBox()
        self.mongo_timeout_spin.setRange(1000, 30000)
        self.mongo_timeout_spin.setValue(5000)
        self.mongo_timeout_spin.setSuffix(" ms")
        conn_layout.addRow("Timeout:", self.mongo_timeout_spin)
        
        conn_group.setLayout(conn_layout)
        layout.addWidget(conn_group)
        
        # MongoDB Atlas/Cloud settings
        atlas_group = QGroupBox("MongoDB Atlas (Cloud)")
        atlas_layout = QVBoxLayout()
        
        self.use_atlas_checkbox = QCheckBox("Use MongoDB Atlas")
        self.use_atlas_checkbox.toggled.connect(self.on_atlas_toggled)
        atlas_layout.addWidget(self.use_atlas_checkbox)
        
        atlas_form = QFormLayout()
        
        self.atlas_connection_edit = QLineEdit()
        self.atlas_connection_edit.setPlaceholderText("mongodb+srv://username:password@cluster.mongodb.net/database")
        atlas_form.addRow("Connection String:", self.atlas_connection_edit)
        
        atlas_layout.addLayout(atlas_form)
        atlas_group.setLayout(atlas_layout)
        layout.addWidget(atlas_group)
        
        # Custom connection string
        custom_group = QGroupBox("Custom Connection String")
        custom_layout = QVBoxLayout()
        
        self.use_custom_checkbox = QCheckBox("Use custom connection string")
        self.use_custom_checkbox.toggled.connect(self.on_custom_toggled)
        custom_layout.addWidget(self.use_custom_checkbox)
        
        self.custom_connection_edit = QTextEdit()
        self.custom_connection_edit.setMaximumHeight(60)
        self.custom_connection_edit.setPlaceholderText("mongodb://username:password@host:port/database?options")
        custom_layout.addWidget(self.custom_connection_edit)
        
        custom_group.setLayout(custom_layout)
        layout.addWidget(custom_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def create_advanced_tab(self) -> QWidget:
        """Create advanced settings tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Performance settings
        perf_group = QGroupBox("Performance Settings")
        perf_layout = QFormLayout()
        
        self.connection_pool_spin = QSpinBox()
        self.connection_pool_spin.setRange(1, 100)
        self.connection_pool_spin.setValue(10)
        perf_layout.addRow("Connection Pool Size:", self.connection_pool_spin)
        
        self.read_preference_combo = QLineEdit()
        self.read_preference_combo.setPlaceholderText("primary")
        perf_layout.addRow("Read Preference:", self.read_preference_combo)
        
        self.write_concern_spin = QSpinBox()
        self.write_concern_spin.setRange(0, 5)
        self.write_concern_spin.setValue(1)
        perf_layout.addRow("Write Concern:", self.write_concern_spin)
        
        perf_group.setLayout(perf_layout)
        layout.addWidget(perf_group)
        
        # Backup settings
        backup_group = QGroupBox("Backup Settings")
        backup_layout = QFormLayout()
        
        self.auto_backup_checkbox = QCheckBox("Enable automatic backups")
        backup_layout.addRow("Auto Backup:", self.auto_backup_checkbox)
        
        self.backup_interval_spin = QSpinBox()
        self.backup_interval_spin.setRange(1, 24)
        self.backup_interval_spin.setValue(24)
        self.backup_interval_spin.setSuffix(" hours")
        backup_layout.addRow("Backup Interval:", self.backup_interval_spin)
        
        self.backup_path_edit = QLineEdit()
        self.backup_path_edit.setPlaceholderText("data/backups/")
        backup_layout.addRow("Backup Directory:", self.backup_path_edit)
        
        backup_group.setLayout(backup_layout)
        layout.addWidget(backup_group)
        
        # Migration settings
        migration_group = QGroupBox("Migration Settings")
        migration_layout = QFormLayout()
        
        self.keep_sqlite_checkbox = QCheckBox("Keep SQLite after migration")
        migration_layout.addRow("Preserve SQLite:", self.keep_sqlite_checkbox)
        
        self.migration_backup_checkbox = QCheckBox("Create backup before migration")
        self.migration_backup_checkbox.setChecked(True)
        migration_layout.addRow("Migration Backup:", self.migration_backup_checkbox)
        
        migration_group.setLayout(migration_layout)
        layout.addWidget(migration_group)
        
        layout.addStretch()
        widget.setLayout(layout)
        return widget
    
    def on_database_type_changed(self):
        """Handle database type change"""
        if self.sqlite_radio.isChecked():
            self.sqlite_group.setEnabled(True)
            self.mongodb_group.setEnabled(False)
        else:
            self.sqlite_group.setEnabled(False)
            self.mongodb_group.setEnabled(True)
    
    def on_atlas_toggled(self, checked):
        """Handle Atlas toggle"""
        if checked:
            self.use_custom_checkbox.setChecked(False)
    
    def on_custom_toggled(self, checked):
        """Handle custom connection string toggle"""
        if checked:
            self.use_atlas_checkbox.setChecked(False)
    
    def load_current_config(self):
        """Load current configuration into the form"""
        # Database type
        db_type = self.current_config.get('database_type', 'sqlite')
        if db_type == 'mongodb':
            self.mongodb_radio.setChecked(True)
        else:
            self.sqlite_radio.setChecked(True)
        
        # SQLite settings
        self.sqlite_path_edit.setText(self.current_config.get('sqlite_path', 'data/medtran.db'))
        
        # MongoDB settings
        mongo_config = self.current_config.get('mongodb', {})
        self.mongo_host_edit.setText(mongo_config.get('host', 'localhost'))
        self.mongo_port_spin.setValue(mongo_config.get('port', 27017))
        self.mongo_database_edit.setText(mongo_config.get('database', 'medtran_db'))
        self.mongo_username_edit.setText(mongo_config.get('username', ''))
        self.mongo_password_edit.setText(mongo_config.get('password', ''))
        self.mongo_auth_db_edit.setText(mongo_config.get('auth_database', 'admin'))
        self.mongo_ssl_checkbox.setChecked(mongo_config.get('use_ssl', False))
        self.mongo_timeout_spin.setValue(mongo_config.get('timeout', 5000))
        
        # Atlas settings
        atlas_connection = mongo_config.get('atlas_connection_string', '')
        if atlas_connection:
            self.use_atlas_checkbox.setChecked(True)
            self.atlas_connection_edit.setText(atlas_connection)
        
        # Custom connection string
        custom_connection = mongo_config.get('custom_connection_string', '')
        if custom_connection:
            self.use_custom_checkbox.setChecked(True)
            self.custom_connection_edit.setPlainText(custom_connection)
        
        # Advanced settings
        advanced_config = self.current_config.get('advanced', {})
        self.connection_pool_spin.setValue(advanced_config.get('connection_pool_size', 10))
        self.read_preference_combo.setText(advanced_config.get('read_preference', 'primary'))
        self.write_concern_spin.setValue(advanced_config.get('write_concern', 1))
        
        # Backup settings
        backup_config = self.current_config.get('backup', {})
        self.auto_backup_checkbox.setChecked(backup_config.get('auto_backup', False))
        self.backup_interval_spin.setValue(backup_config.get('interval_hours', 24))
        self.backup_path_edit.setText(backup_config.get('backup_directory', 'data/backups/'))
        
        # Migration settings
        migration_config = self.current_config.get('migration', {})
        self.keep_sqlite_checkbox.setChecked(migration_config.get('keep_sqlite', True))
        self.migration_backup_checkbox.setChecked(migration_config.get('create_backup', True))
        
        # Update UI state
        self.on_database_type_changed()
    
    def get_configuration(self) -> Dict[str, Any]:
        """Get configuration from form"""
        config = {
            'database_type': 'mongodb' if self.mongodb_radio.isChecked() else 'sqlite',
            'sqlite_path': self.sqlite_path_edit.text() or 'data/medtran.db',
            'mongodb': {
                'host': self.mongo_host_edit.text() or 'localhost',
                'port': self.mongo_port_spin.value(),
                'database': self.mongo_database_edit.text() or 'medtran_db',
                'username': self.mongo_username_edit.text(),
                'password': self.mongo_password_edit.text(),
                'auth_database': self.mongo_auth_db_edit.text() or 'admin',
                'use_ssl': self.mongo_ssl_checkbox.isChecked(),
                'timeout': self.mongo_timeout_spin.value(),
                'atlas_connection_string': self.atlas_connection_edit.text() if self.use_atlas_checkbox.isChecked() else '',
                'custom_connection_string': self.custom_connection_edit.toPlainText() if self.use_custom_checkbox.isChecked() else ''
            },
            'advanced': {
                'connection_pool_size': self.connection_pool_spin.value(),
                'read_preference': self.read_preference_combo.text() or 'primary',
                'write_concern': self.write_concern_spin.value()
            },
            'backup': {
                'auto_backup': self.auto_backup_checkbox.isChecked(),
                'interval_hours': self.backup_interval_spin.value(),
                'backup_directory': self.backup_path_edit.text() or 'data/backups/'
            },
            'migration': {
                'keep_sqlite': self.keep_sqlite_checkbox.isChecked(),
                'create_backup': self.migration_backup_checkbox.isChecked()
            }
        }
        return config
    
    def build_mongodb_connection_string(self) -> str:
        """Build MongoDB connection string from settings"""
        if self.use_atlas_checkbox.isChecked():
            return self.atlas_connection_edit.text()
        
        if self.use_custom_checkbox.isChecked():
            return self.custom_connection_edit.toPlainText()
        
        # Build connection string from individual settings
        host = self.mongo_host_edit.text() or 'localhost'
        port = self.mongo_port_spin.value()
        database = self.mongo_database_edit.text() or 'medtran_db'
        username = self.mongo_username_edit.text()
        password = self.mongo_password_edit.text()
        
        if username and password:
            connection_string = f"mongodb://{username}:{password}@{host}:{port}/{database}"
        else:
            connection_string = f"mongodb://{host}:{port}/{database}"
        
        # Add options
        options = []
        if self.mongo_ssl_checkbox.isChecked():
            options.append("ssl=true")
        
        auth_db = self.mongo_auth_db_edit.text()
        if auth_db and auth_db != "admin":
            options.append(f"authSource={auth_db}")
        
        if options:
            connection_string += "?" + "&".join(options)
        
        return connection_string
    
    def test_connection(self):
        """Test database connection"""
        try:
            if self.mongodb_radio.isChecked():
                # Test MongoDB connection
                from database.mongo_db import MongoDB
                
                connection_string = self.build_mongodb_connection_string()
                database_name = self.mongo_database_edit.text() or 'medtran_db'
                
                mongo_db = MongoDB(connection_string, database_name)
                if mongo_db.connect():
                    info = mongo_db.get_database_info()
                    mongo_db.close()
                    
                    QMessageBox.information(
                        self, "Connection Success",
                        f"Successfully connected to MongoDB!\n\n"
                        f"Database: {info.get('database_name', 'Unknown')}\n"
                        f"Collections: {len(info.get('collections', {}))}\n"
                        f"Total Documents: {info.get('total_documents', 0)}"
                    )
                else:
                    QMessageBox.critical(self, "Connection Failed", "Failed to connect to MongoDB.")
            else:
                # Test SQLite connection
                import sqlite3
                sqlite_path = self.sqlite_path_edit.text() or 'data/medtran.db'
                
                if not os.path.exists(sqlite_path):
                    QMessageBox.warning(
                        self, "File Not Found",
                        f"SQLite database file not found: {sqlite_path}"
                    )
                    return
                
                conn = sqlite3.connect(sqlite_path)
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = cursor.fetchall()
                conn.close()
                
                QMessageBox.information(
                    self, "Connection Success",
                    f"Successfully connected to SQLite!\n\n"
                    f"Database: {sqlite_path}\n"
                    f"Tables: {len(tables)}"
                )
                
        except Exception as e:
            QMessageBox.critical(self, "Connection Error", f"Connection test failed:\n{str(e)}")
    
    def save_config(self):
        """Save configuration and close dialog"""
        try:
            config = self.get_configuration()
            
            # Validate configuration
            if config['database_type'] == 'mongodb':
                if self.use_atlas_checkbox.isChecked() and not self.atlas_connection_edit.text():
                    QMessageBox.warning(self, "Invalid Configuration", "Atlas connection string is required.")
                    return
                
                if self.use_custom_checkbox.isChecked() and not self.custom_connection_edit.toPlainText():
                    QMessageBox.warning(self, "Invalid Configuration", "Custom connection string is required.")
                    return
            
            self.current_config = config
            self.accept()
            
        except Exception as e:
            QMessageBox.critical(self, "Save Error", f"Failed to save configuration:\n{str(e)}")


class ConfigManager:
    """Configuration manager for the application"""
    
    def __init__(self, config_file: str = "data/config.json"):
        self.config_file = config_file
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            'database_type': 'sqlite',
            'sqlite_path': 'data/medtran.db',
            'mongodb': {
                'host': 'localhost',
                'port': 27017,
                'database': 'medtran_db',
                'username': '',
                'password': '',
                'auth_database': 'admin',
                'use_ssl': False,
                'timeout': 5000,
                'atlas_connection_string': '',
                'custom_connection_string': ''
            },
            'advanced': {
                'connection_pool_size': 10,
                'read_preference': 'primary',
                'write_concern': 1
            },
            'backup': {
                'auto_backup': False,
                'interval_hours': 24,
                'backup_directory': 'data/backups/'
            },
            'migration': {
                'keep_sqlite': True,
                'create_backup': True
            }
        }
        
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    return {**default_config, **loaded_config}
            else:
                # Create directory if it doesn't exist
                os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
                return default_config
                
        except Exception as e:
            print(f"Error loading config: {e}")
            return default_config
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to file"""
        try:
            if config:
                self.config = config
            
            os.makedirs(os.path.dirname(self.config_file), exist_ok=True)
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
            return True
            
        except Exception as e:
            print(f"Error saving config: {e}")
            return False
    
    def get_database_type(self) -> str:
        """Get current database type"""
        return self.config.get('database_type', 'sqlite')
    
    def get_sqlite_path(self) -> str:
        """Get SQLite database path"""
        return self.config.get('sqlite_path', 'data/medtran.db')
    
    def get_mongodb_connection_string(self) -> str:
        """Get MongoDB connection string"""
        mongo_config = self.config.get('mongodb', {})
        
        # Check for Atlas connection
        atlas_string = mongo_config.get('atlas_connection_string', '')
        if atlas_string:
            return atlas_string
        
        # Check for custom connection string
        custom_string = mongo_config.get('custom_connection_string', '')
        if custom_string:
            return custom_string
        
        # Build from individual settings
        host = mongo_config.get('host', 'localhost')
        port = mongo_config.get('port', 27017)
        username = mongo_config.get('username', '')
        password = mongo_config.get('password', '')
        
        if username and password:
            return f"mongodb://{username}:{password}@{host}:{port}/"
        else:
            return f"mongodb://{host}:{port}/"
    
    def get_mongodb_database_name(self) -> str:
        """Get MongoDB database name"""
        return self.config.get('mongodb', {}).get('database', 'medtran_db')
    
    def show_config_dialog(self, parent=None) -> bool:
        """Show configuration dialog"""
        dialog = DatabaseConfigDialog(self.config, parent)
        if dialog.exec_() == QDialog.Accepted:
            self.config = dialog.current_config
            return self.save_config()
        return False
    
    def get_backup_config(self) -> Dict[str, Any]:
        """Get backup configuration"""
        return self.config.get('backup', {})
    
    def is_auto_backup_enabled(self) -> bool:
        """Check if auto backup is enabled"""
        return self.config.get('backup', {}).get('auto_backup', False)