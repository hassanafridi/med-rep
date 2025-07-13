from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QDateEdit, QComboBox, QMessageBox, QHeaderView,
    QGroupBox, QFormLayout, QLineEdit, QDialog, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
import sys
import os
import json
import datetime

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter

class AuditDetailDialog(QDialog):
    def __init__(self, audit_entry, parent=None):
        super().__init__(parent)
        self.audit_entry = audit_entry
        self.setWindowTitle("Audit Details")
        self.setMinimumSize(600, 400)
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        # Basic info section
        info_group = QGroupBox("Basic Information")
        info_layout = QFormLayout()
        
        info_layout.addRow("ID:", QLabel(str(self.audit_entry.get('id', 'N/A'))))
        info_layout.addRow("Timestamp:", QLabel(str(self.audit_entry.get('timestamp', 'N/A'))))
        info_layout.addRow("User:", QLabel(str(self.audit_entry.get('username', 'N/A'))))
        info_layout.addRow("Action:", QLabel(str(self.audit_entry.get('action_type', 'N/A'))))
        
        if self.audit_entry.get('table_name'):
            info_layout.addRow("Collection:", QLabel(str(self.audit_entry['table_name'])))
        
        if self.audit_entry.get('record_id'):
            info_layout.addRow("Record ID:", QLabel(str(self.audit_entry['record_id'])))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Details section
        if self.audit_entry.get('details'):
            details_group = QGroupBox("Details")
            details_layout = QVBoxLayout()
            
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_text.setText(str(self.audit_entry['details']))
            
            details_layout.addWidget(details_text)
            details_group.setLayout(details_layout)
            layout.addWidget(details_group)
        
        # Values section for data changes
        old_values = self.audit_entry.get('old_values')
        new_values = self.audit_entry.get('new_values')
        
        if old_values or new_values:
            values_group = QGroupBox("Changed Values")
            values_layout = QVBoxLayout()
            
            values_table = QTableWidget()
            values_table.setColumnCount(3)
            values_table.setHorizontalHeaderLabels(["Field", "Old Value", "New Value"])
            values_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            # Get all unique keys
            keys = set()
            if isinstance(old_values, dict):
                keys.update(old_values.keys())
            if isinstance(new_values, dict):
                keys.update(new_values.keys())
            
            # Fill table
            values_table.setRowCount(len(keys))
            
            for row, key in enumerate(sorted(keys)):
                # Field name
                values_table.setItem(row, 0, QTableWidgetItem(str(key)))
                
                # Old value
                old_value = old_values.get(key, "") if old_values else ""
                values_table.setItem(row, 1, QTableWidgetItem(str(old_value)))
                
                # New value
                new_value = new_values.get(key, "") if new_values else ""
                values_table.setItem(row, 2, QTableWidgetItem(str(new_value)))
                
                # Highlight changes
                if str(old_value) != str(new_value):
                    for col in range(1, 3):
                        item = values_table.item(row, col)
                        item.setBackground(Qt.yellow)
            
            values_layout.addWidget(values_table)
            values_group.setLayout(values_layout)
            layout.addWidget(values_group)
        
        # Close button
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)
        
        self.setLayout(layout)

class AuditTrailTab(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        try:
            self.db = MongoAdapter()
            self.current_user = current_user or {'username': 'unknown', 'user_id': None}
            self.page_size = 100
            self.current_page = 0
            self.total_records = 0
            self.audit_data = []  # Store audit data
            self.initUI()
            self.loadAuditTrail()
        except Exception as e:
            print(f"Error initializing Audit Trail tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Audit Trail tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the audit trail tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.current_user)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Audit Trail tab: {str(e)}")
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Audit Trail - MongoDB Activity Log")
        title.setStyleSheet("font-size: 16px; font-weight: bold; margin: 10px;")
        main_layout.addWidget(title)
        
        # Filter section
        filter_group = QGroupBox("Filter Audit Trail")
        filter_layout = QFormLayout()
        
        # Username filter
        self.username_filter = QLineEdit()
        self.username_filter.setPlaceholderText("Enter username to filter")
        filter_layout.addRow("Username:", self.username_filter)
        
        # Action type filter
        self.action_filter = QComboBox()
        self.action_filter.addItem("All Actions")
        self.action_filter.addItems([
            "LOGIN_SUCCESS", "LOGIN_FAILURE",
            "DATA_INSERT", "DATA_UPDATE", "DATA_DELETE",
            "BACKUP_CREATE", "BACKUP_RESTORE",
            "EXPORT_DATA", "IMPORT_DATA",
            "ENTRY_CREATE", "PRODUCT_ADD", "CUSTOMER_ADD"
        ])
        filter_layout.addRow("Action Type:", self.action_filter)
        
        # Collection filter (MongoDB collections)
        self.collection_filter = QComboBox()
        self.collection_filter.addItem("All Collections")
        self.collection_filter.addItems([
            "customers", "products", "entries", "transactions"
        ])
        filter_layout.addRow("Collection:", self.collection_filter)
        
        # Date range
        date_layout = QHBoxLayout()
        
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addDays(-30))
        self.from_date.setCalendarPopup(True)
        
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.to_date)
        
        filter_layout.addRow("Date Range:", date_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.apply_filter_btn = QPushButton("Apply Filters")
        self.apply_filter_btn.clicked.connect(self.loadAuditTrail)
        self.apply_filter_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        self.clear_filter_btn = QPushButton("Clear Filters")
        self.clear_filter_btn.clicked.connect(self.clearFilters)
        
        self.export_btn = QPushButton("Export Audit Log")
        self.export_btn.clicked.connect(self.exportAuditLog)
        
        button_layout.addWidget(self.apply_filter_btn)
        button_layout.addWidget(self.clear_filter_btn)
        button_layout.addWidget(self.export_btn)
        button_layout.addStretch()
        
        filter_layout.addRow("", button_layout)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # Audit trail table
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(7)
        self.audit_table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "User", "Action", "Collection", "Record ID", "Details"
        ])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.audit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.audit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.audit_table.doubleClicked.connect(self.viewAuditDetails)
        self.audit_table.setAlternatingRowColors(True)
        
        main_layout.addWidget(self.audit_table)
        
        # Statistics section
        stats_layout = QHBoxLayout()
        self.stats_label = QLabel("No audit data loaded")
        self.stats_label.setStyleSheet("color: #666; font-style: italic;")
        stats_layout.addWidget(self.stats_label)
        stats_layout.addStretch()
        
        main_layout.addLayout(stats_layout)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.previousPage)
        self.prev_btn.setEnabled(False)
        
        self.page_info = QLabel("Page 1 of 1")
        self.page_info.setAlignment(Qt.AlignCenter)
        self.page_info.setStyleSheet("font-weight: bold;")
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.nextPage)
        self.next_btn.setEnabled(False)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_info)
        nav_layout.addWidget(self.next_btn)
        
        main_layout.addLayout(nav_layout)
        
        self.setLayout(main_layout)
    
    def generateSampleAuditData(self):
        """Generate sample audit data for demonstration"""
        try:
            from datetime import datetime, timedelta
            import random
            
            sample_data = []
            users = ['admin', 'user1', 'doctor', 'pharmacist']
            actions = ['DATA_INSERT', 'DATA_UPDATE', 'LOGIN_SUCCESS', 'EXPORT_DATA', 'BACKUP_CREATE']
            collections = ['customers', 'products', 'entries', 'transactions']
            
            # Generate 50 sample audit entries
            for i in range(50):
                # Random date within last 30 days
                days_ago = random.randint(0, 30)
                timestamp = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d %H:%M:%S')
                
                audit_entry = {
                    'id': str(i + 1),
                    'timestamp': timestamp,
                    'username': random.choice(users),
                    'action_type': random.choice(actions),
                    'table_name': random.choice(collections),
                    'record_id': str(random.randint(1, 1000)),
                    'details': f"Sample audit entry {i + 1} - {random.choice(actions)}",
                    'old_values': {'sample_field': f'old_value_{i}'} if random.choice([True, False]) else None,
                    'new_values': {'sample_field': f'new_value_{i}'} if random.choice([True, False]) else None
                }
                sample_data.append(audit_entry)
            
            return sample_data
            
        except Exception as e:
            print(f"Error generating sample audit data: {e}")
            return []
    
    def loadAuditTrail(self):
        """Load audit trail data with current filters"""
        try:
            # For now, generate sample data since we don't have a full audit system
            # In a real implementation, this would query MongoDB audit collection
            all_audit_data = self.generateSampleAuditData()
            
            # Apply filters
            filtered_data = self.applyFilters(all_audit_data)
            
            # Store filtered data
            self.audit_data = filtered_data
            self.total_records = len(filtered_data)
            
            # Apply pagination
            start_index = self.current_page * self.page_size
            end_index = start_index + self.page_size
            page_data = filtered_data[start_index:end_index]
            
            # Update table
            self.updateAuditTable(page_data)
            
            # Update statistics
            self.updateStatistics()
            
            # Update pagination controls
            self.updatePaginationControls()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load audit trail: {str(e)}")
            print(f"Audit trail load error: {e}")
            import traceback
            traceback.print_exc()
    
    def applyFilters(self, data):
        """Apply current filters to audit data"""
        try:
            filtered_data = data.copy()
            
            # Username filter
            username = self.username_filter.text().strip()
            if username:
                filtered_data = [entry for entry in filtered_data 
                               if username.lower() in entry.get('username', '').lower()]
            
            # Action type filter
            action_type = self.action_filter.currentText()
            if action_type != "All Actions":
                filtered_data = [entry for entry in filtered_data 
                               if entry.get('action_type') == action_type]
            
            # Collection filter
            collection = self.collection_filter.currentText()
            if collection != "All Collections":
                filtered_data = [entry for entry in filtered_data 
                               if entry.get('table_name') == collection]
            
            # Date range filter
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd")
            
            filtered_data = [entry for entry in filtered_data 
                           if from_date <= entry.get('timestamp', '')[:10] <= to_date]
            
            return filtered_data
            
        except Exception as e:
            print(f"Error applying filters: {e}")
            return data
    
    def updateAuditTable(self, data):
        """Update the audit table with data"""
        try:
            self.audit_table.setRowCount(0)
            self.audit_table.setRowCount(len(data))
            
            for row, entry in enumerate(data):
                # ID
                self.audit_table.setItem(row, 0, QTableWidgetItem(str(entry.get('id', ''))))
                
                # Timestamp
                timestamp = entry.get('timestamp', '')
                self.audit_table.setItem(row, 1, QTableWidgetItem(timestamp))
                
                # User
                username = entry.get('username', 'Unknown')
                self.audit_table.setItem(row, 2, QTableWidgetItem(username))
                
                # Action
                action = entry.get('action_type', '')
                action_item = QTableWidgetItem(action)
                
                # Color code actions
                if action.startswith('LOGIN'):
                    action_item.setBackground(Qt.lightGray)
                elif action.startswith('DATA'):
                    action_item.setBackground(Qt.lightBlue)
                elif action.startswith('BACKUP') or action.startswith('EXPORT'):
                    action_item.setBackground(Qt.lightGreen)
                
                self.audit_table.setItem(row, 3, action_item)
                
                # Collection
                collection = entry.get('table_name', '')
                self.audit_table.setItem(row, 4, QTableWidgetItem(collection))
                
                # Record ID
                record_id = str(entry.get('record_id', ''))
                self.audit_table.setItem(row, 5, QTableWidgetItem(record_id))
                
                # Details (truncated)
                details = entry.get('details', '')
                if len(details) > 50:
                    details = details[:47] + "..."
                self.audit_table.setItem(row, 6, QTableWidgetItem(details))
            
        except Exception as e:
            print(f"Error updating audit table: {e}")
    
    def updateStatistics(self):
        """Update audit statistics"""
        try:
            if not self.audit_data:
                self.stats_label.setText("No audit data loaded")
                return
            
            # Count actions by type
            action_counts = {}
            user_counts = {}
            
            for entry in self.audit_data:
                action = entry.get('action_type', 'Unknown')
                user = entry.get('username', 'Unknown')
                
                action_counts[action] = action_counts.get(action, 0) + 1
                user_counts[user] = user_counts.get(user, 0) + 1
            
            # Most active user
            most_active_user = max(user_counts.items(), key=lambda x: x[1]) if user_counts else ('None', 0)
            
            # Most common action
            most_common_action = max(action_counts.items(), key=lambda x: x[1]) if action_counts else ('None', 0)
            
            stats_text = (f"Total: {len(self.audit_data)} entries | "
                         f"Most active user: {most_active_user[0]} ({most_active_user[1]}) | "
                         f"Most common action: {most_common_action[0]} ({most_common_action[1]})")
            
            self.stats_label.setText(stats_text)
            
        except Exception as e:
            print(f"Error updating statistics: {e}")
            self.stats_label.setText("Error calculating statistics")
    
    def updatePaginationControls(self):
        """Update pagination controls based on current state"""
        try:
            total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
            
            start_index = self.current_page * self.page_size + 1 if self.total_records > 0 else 0
            end_index = min((self.current_page + 1) * self.page_size, self.total_records)
            
            self.page_info.setText(
                f"Showing {start_index}-{end_index} of {self.total_records} records "
                f"(Page {self.current_page + 1} of {total_pages})"
            )
            
            self.prev_btn.setEnabled(self.current_page > 0)
            self.next_btn.setEnabled(self.current_page < total_pages - 1)
            
        except Exception as e:
            print(f"Error updating pagination controls: {e}")
    
    def previousPage(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.loadAuditTrail()
    
    def nextPage(self):
        """Go to next page"""
        total_pages = max(1, (self.total_records + self.page_size - 1) // self.page_size)
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.loadAuditTrail()
    
    def clearFilters(self):
        """Clear all filters"""
        try:
            self.username_filter.clear()
            self.action_filter.setCurrentIndex(0)
            self.collection_filter.setCurrentIndex(0)
            self.from_date.setDate(QDate.currentDate().addDays(-30))
            self.to_date.setDate(QDate.currentDate())
            self.current_page = 0
            self.loadAuditTrail()
            
        except Exception as e:
            print(f"Error clearing filters: {e}")
    
    def exportAuditLog(self):
        """Export audit log to CSV"""
        try:
            from PyQt5.QtWidgets import QFileDialog
            import csv
            
            if not self.audit_data:
                QMessageBox.warning(self, "No Data", "No audit data to export.")
                return
            
            # Get save location
            file_path, _ = QFileDialog.getSaveFileName(
                self, "Export Audit Log", 
                f"audit_log_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                "CSV Files (*.csv);;All Files (*)"
            )
            
            if not file_path:
                return
            
            # Write CSV
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['ID', 'Timestamp', 'Username', 'Action', 'Collection', 'Record ID', 'Details']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for entry in self.audit_data:
                    writer.writerow({
                        'ID': entry.get('id', ''),
                        'Timestamp': entry.get('timestamp', ''),
                        'Username': entry.get('username', ''),
                        'Action': entry.get('action_type', ''),
                        'Collection': entry.get('table_name', ''),
                        'Record ID': entry.get('record_id', ''),
                        'Details': entry.get('details', '')
                    })
            
            QMessageBox.information(self, "Export Complete", 
                                  f"Audit log exported successfully to:\n{file_path}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export audit log:\n{str(e)}")
    
    def viewAuditDetails(self, index):
        """View details of an audit entry"""
        try:
            row = index.row()
            if 0 <= row < len(self.audit_data):
                # Get the current page data
                start_index = self.current_page * self.page_size
                entry_index = start_index + row
                
                if entry_index < len(self.audit_data):
                    entry = self.audit_data[entry_index]
                    dialog = AuditDetailDialog(entry, self)
                    dialog.exec_()
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not view audit details:\n{str(e)}")