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
from database.audit_trail import AuditTrail
from database.db import Database

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
        
        info_layout.addRow("ID:", QLabel(str(self.audit_entry['id'])))
        info_layout.addRow("Timestamp:", QLabel(self.audit_entry['timestamp']))
        info_layout.addRow("User:", QLabel(self.audit_entry['username'] or "N/A"))
        info_layout.addRow("Action:", QLabel(self.audit_entry['action_type']))
        
        if self.audit_entry['table_name']:
            info_layout.addRow("Table:", QLabel(self.audit_entry['table_name']))
        
        if self.audit_entry['record_id']:
            info_layout.addRow("Record ID:", QLabel(str(self.audit_entry['record_id'])))
        
        info_group.setLayout(info_layout)
        layout.addWidget(info_group)
        
        # Details section
        if self.audit_entry['details']:
            details_group = QGroupBox("Details")
            details_layout = QVBoxLayout()
            
            details_text = QTextEdit()
            details_text.setReadOnly(True)
            details_text.setText(self.audit_entry['details'])
            
            details_layout.addWidget(details_text)
            details_group.setLayout(details_layout)
            layout.addWidget(details_group)
        
        # Values section for data changes
        if self.audit_entry['old_values'] or self.audit_entry['new_values']:
            values_group = QGroupBox("Changed Values")
            values_layout = QVBoxLayout()
            
            values_table = QTableWidget()
            values_table.setColumnCount(3)
            values_table.setHorizontalHeaderLabels(["Field", "Old Value", "New Value"])
            values_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            
            # Get all unique keys
            keys = set()
            old_values = self.audit_entry['old_values'] or {}
            new_values = self.audit_entry['new_values'] or {}
            
            if isinstance(old_values, dict):
                keys.update(old_values.keys())
            if isinstance(new_values, dict):
                keys.update(new_values.keys())
            
            # Fill table
            values_table.setRowCount(len(keys))
            
            for row, key in enumerate(sorted(keys)):
                # Field name
                values_table.setItem(row, 0, QTableWidgetItem(key))
                
                # Old value
                old_value = old_values.get(key, "")
                values_table.setItem(row, 1, QTableWidgetItem(str(old_value)))
                
                # New value
                new_value = new_values.get(key, "")
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
    def __init__(self, current_user):
        super().__init__()
        self.db = Database()
        self.audit_trail = AuditTrail(self.db.db_path)
        self.current_user = current_user
        self.page_size = 100
        self.current_page = 0
        self.total_records = 0
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Filter section
        filter_group = QGroupBox("Filter Audit Trail")
        filter_layout = QFormLayout()
        
        # Username filter
        self.username_filter = QLineEdit()
        filter_layout.addRow("Username:", self.username_filter)
        
        # Action type filter
        self.action_filter = QComboBox()
        self.action_filter.addItem("All Actions")
        self.action_filter.addItems([
            "LOGIN_SUCCESS", "LOGIN_FAILURE",
            "DATA_INSERT", "DATA_UPDATE", "DATA_DELETE",
            "BACKUP_CREATE", "BACKUP_RESTORE",
            "EXPORT_DATA", "IMPORT_DATA"
        ])
        filter_layout.addRow("Action Type:", self.action_filter)
        
        # Table filter
        self.table_filter = QComboBox()
        self.table_filter.addItem("All Tables")
        self.table_filter.addItems([
            "customers", "products", "entries", "transactions"
        ])
        filter_layout.addRow("Table:", self.table_filter)
        
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
        
        # Apply filter button
        self.apply_filter_btn = QPushButton("Apply Filters")
        self.apply_filter_btn.clicked.connect(self.loadAuditTrail)
        filter_layout.addRow("", self.apply_filter_btn)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # Audit trail table
        self.audit_table = QTableWidget()
        self.audit_table.setColumnCount(7)
        self.audit_table.setHorizontalHeaderLabels([
            "ID", "Timestamp", "User", "Action", "Table", "Record ID", "Details"
        ])
        self.audit_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.audit_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.audit_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.audit_table.doubleClicked.connect(self.viewAuditDetails)
        
        main_layout.addWidget(self.audit_table)
        
        # Navigation controls
        nav_layout = QHBoxLayout()
        
        self.prev_btn = QPushButton("Previous")
        self.prev_btn.clicked.connect(self.previousPage)
        
        self.page_info = QLabel("Page 1")
        self.page_info.setAlignment(Qt.AlignCenter)
        
        self.next_btn = QPushButton("Next")
        self.next_btn.clicked.connect(self.nextPage)
        
        nav_layout.addWidget(self.prev_btn)
        nav_layout.addWidget(self.page_info)
        nav_layout.addWidget(self.next_btn)
        
        main_layout.addLayout(nav_layout)
        
        self.setLayout(main_layout)
        
        # Load initial data
        self.loadAuditTrail()
    
    def loadAuditTrail(self):
        """Load audit trail data with current filters"""
        try:
            # Build filters
            filters = {}
            
            username = self.username_filter.text().strip()
            if username:
                filters['username'] = username
            
            action_type = self.action_filter.currentText()
            if action_type != "All Actions":
                filters['action_type'] = action_type
            
            table_name = self.table_filter.currentText()
            if table_name != "All Tables":
                filters['table_name'] = table_name
            
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd") + " 23:59:59"
            filters['from_date'] = from_date
            filters['to_date'] = to_date
            
            # Get total count for pagination
            self.total_records = self.audit_trail.get_audit_count(filters)
            
            # Get audit trail entries
            offset = self.current_page * self.page_size
            entries = self.audit_trail.get_audit_trail(
                filters=filters,
                limit=self.page_size,
                offset=offset
            )
            
            # Update table
            self.audit_table.setRowCount(0)
            self.audit_table.setRowCount(len(entries))
            
            for row, entry in enumerate(entries):
                self.audit_table.setItem(row, 0, QTableWidgetItem(str(entry['id'])))
                self.audit_table.setItem(row, 1, QTableWidgetItem(entry['timestamp']))
                self.audit_table.setItem(row, 2, QTableWidgetItem(entry['username'] or ""))
                self.audit_table.setItem(row, 3, QTableWidgetItem(entry['action_type']))
                self.audit_table.setItem(row, 4, QTableWidgetItem(entry['table_name'] or ""))
                self.audit_table.setItem(row, 5, QTableWidgetItem(str(entry['record_id'] or "")))
                
                # Create details button
                details_item = QTableWidgetItem("View Details")
                details_item.setTextAlignment(Qt.AlignCenter)
                self.audit_table.setItem(row, 6, details_item)
            
            # Update pagination controls
            self.updatePaginationControls()
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load audit trail: {str(e)}")
    
    def updatePaginationControls(self):
        """Update pagination controls based on current state"""
        total_pages = (self.total_records + self.page_size - 1) // self.page_size
        
        if total_pages == 0:
            total_pages = 1
        
        start_index = self.current_page * self.page_size + 1
        end_index = min((self.current_page + 1) * self.page_size, self.total_records)
        
        if self.total_records == 0:
            start_index = 0
            end_index = 0
        
        self.page_info.setText(
            f"Showing {start_index}-{end_index} of {self.total_records} records " +
            f"(Page {self.current_page + 1} of {total_pages})"
        )
        
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)
    
    def previousPage(self):
        """Go to previous page"""
        if self.current_page > 0:
            self.current_page -= 1
            self.loadAuditTrail()
    
    def nextPage(self):
        """Go to next page"""
        total_pages = (self.total_records + self.page_size - 1) // self.page_size
        
        if self.current_page < total_pages - 1:
            self.current_page += 1
            self.loadAuditTrail()
    
    def viewAuditDetails(self, index):
        """View details of an audit entry"""
        row = index.row()
        entry_id = int(self.audit_table.item(row, 0).text())
        
        # Get the audit entry
        entries = self.audit_trail.get_audit_trail(
            filters={'id': entry_id},
            limit=1
        )
        
        if entries:
            dialog = AuditDetailDialog(entries[0], self)
            dialog.exec_()