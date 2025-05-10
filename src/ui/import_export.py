from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, QPushButton,
    QFileDialog, QMessageBox, QTableWidget, QTableWidgetItem, QHeaderView,
    QGroupBox, QFormLayout, QCheckBox, QProgressBar
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
import os
import csv
import sqlite3
import sys

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Database

class ImportThread(QThread):
    """Thread for importing data to avoid UI freezing"""
    progress_updated = pyqtSignal(int)
    import_complete = pyqtSignal(int, int)  # success_count, error_count
    error_occurred = pyqtSignal(str)
    
    def __init__(self, import_type, file_path, mappings, header_row, db_path):
        super().__init__()
        self.import_type = import_type
        self.file_path = file_path
        self.mappings = mappings
        self.header_row = header_row
        self.db_path = db_path
    
    def run(self):
        """Run the import process"""
        try:
            # Connect to database
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Read CSV file
            with open(self.file_path, 'r', newline='', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                
                # Skip header row if needed
                if self.header_row:
                    next(csv_reader)
                
                # Get all rows
                rows = list(csv_reader)
                
                # Initialize counters
                success_count = 0
                error_count = 0
                
                # Process each row
                for index, row in enumerate(rows):
                    try:
                        # Update progress
                        self.progress_updated.emit(int((index / len(rows)) * 100))
                        
                        # Skip empty rows
                        if not any(row):
                            continue
                        
                        # Process based on import type
                        if self.import_type == "Customers":
                            name_idx = self.mappings.get('name', -1)
                            contact_idx = self.mappings.get('contact', -1)
                            address_idx = self.mappings.get('address', -1)
                            
                            # Skip if name is missing
                            if name_idx == -1 or not row[name_idx]:
                                error_count += 1
                                continue
                            
                            # Get values
                            name = row[name_idx] if name_idx != -1 else ""
                            contact = row[contact_idx] if contact_idx != -1 and contact_idx < len(row) else ""
                            address = row[address_idx] if address_idx != -1 and address_idx < len(row) else ""
                            
                            # Insert customer
                            cursor.execute(
                                'INSERT INTO customers (name, contact, address) VALUES (?, ?, ?)',
                                (name, contact, address)
                            )
                            
                        elif self.import_type == "Products":
                            name_idx = self.mappings.get('name', -1)
                            desc_idx = self.mappings.get('description', -1)
                            price_idx = self.mappings.get('price', -1)
                            
                            # Skip if name or price is missing
                            if name_idx == -1 or not row[name_idx] or price_idx == -1 or not row[price_idx]:
                                error_count += 1
                                continue
                            
                            # Get values
                            name = row[name_idx] if name_idx != -1 else ""
                            description = row[desc_idx] if desc_idx != -1 and desc_idx < len(row) else ""
                            
                            # Parse price
                            try:
                                price_str = row[price_idx].replace('$', '').replace(',', '')
                                price = float(price_str)
                            except (ValueError, IndexError):
                                error_count += 1
                                continue
                            
                            # Insert product
                            cursor.execute(
                                'INSERT INTO products (name, description, unit_price) VALUES (?, ?, ?)',
                                (name, description, price)
                            )
                        
                        success_count += 1
                        
                    except Exception as e:
                        error_count += 1
                        self.error_occurred.emit(f"Error processing row {index+1}: {str(e)}")
                        continue
                
                # Commit changes
                conn.commit()
                
                # Update progress to 100%
                self.progress_updated.emit(100)
                
                # Emit completion signal
                self.import_complete.emit(success_count, error_count)
                
        except Exception as e:
            self.error_occurred.emit(f"Import error: {str(e)}")
        finally:
            # Close connection
            if 'conn' in locals():
                conn.close()

class ImportDialog(QDialog):
    def __init__(self, parent=None, db_path=None):
        super().__init__(parent)
        self.db_path = db_path or Database().db_path
        self.file_path = None
        self.csv_headers = []
        self.import_thread = None
        
        self.setWindowTitle("Import Data")
        self.setMinimumSize(600, 500)
        self.initUI()
    
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        # File selection
        file_group = QGroupBox("Select File")
        file_layout = QHBoxLayout()
        
        self.file_label = QLabel("No file selected")
        self.browse_btn = QPushButton("Browse")
        self.browse_btn.clicked.connect(self.browseFile)
        
        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.browse_btn)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # Import type
        type_group = QGroupBox("Import Settings")
        type_layout = QFormLayout()
        
        self.import_type = QComboBox()
        self.import_type.addItems(["Customers", "Products"])
        self.import_type.currentIndexChanged.connect(self.updateMappingFields)
        
        self.header_checkbox = QCheckBox("File has header row")
        self.header_checkbox.setChecked(True)
        self.header_checkbox.toggled.connect(self.loadCSVHeaders)
        
        type_layout.addRow("Import Type:", self.import_type)
        type_layout.addRow("", self.header_checkbox)
        
        type_group.setLayout(type_layout)
        layout.addWidget(type_group)
        
        # Field mapping
        self.mapping_group = QGroupBox("Field Mapping")
        self.mapping_layout = QFormLayout()
        self.mapping_group.setLayout(self.mapping_layout)
        layout.addWidget(self.mapping_group)
        
        # Preview table
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout()
        
        self.preview_table = QTableWidget()
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        
        preview_layout.addWidget(self.preview_table)
        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        self.import_btn = QPushButton("Import")
        self.import_btn.clicked.connect(self.importData)
        self.import_btn.setEnabled(False)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        
        buttons_layout.addWidget(self.import_btn)
        buttons_layout.addWidget(self.cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        self.setLayout(layout)
        
        # Initialize mapping fields
        self.updateMappingFields()
    
    def browseFile(self):
        """Browse for CSV file"""
        options = QFileDialog.Options()
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select CSV File", "", "CSV Files (*.csv);;All Files (*)", options=options
        )
        
        if file_path:
            self.file_path = file_path
            self.file_label.setText(os.path.basename(file_path))
            self.import_btn.setEnabled(True)
            
            # Load CSV headers
            self.loadCSVHeaders()
    
    def loadCSVHeaders(self):
        """Load headers from CSV file"""
        if not self.file_path:
            return
        
        try:
            with open(self.file_path, 'r', newline='', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                
                # Read first row
                self.csv_headers = next(csv_reader)
                
                # Update mapping options
                self.updateMappingFields()
                
                # Load preview data
                self.loadPreviewData()
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to read CSV file: {str(e)}")
    
    def updateMappingFields(self):
        """Update mapping fields based on import type"""
        # Clear existing layout
        while self.mapping_layout.count():
            item = self.mapping_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add mapping fields based on import type
        import_type = self.import_type.currentText()
        
        if import_type == "Customers":
            self.name_mapping = QComboBox()
            self.contact_mapping = QComboBox()
            self.address_mapping = QComboBox()
            
            self.mapping_layout.addRow("Name* (required):", self.name_mapping)
            self.mapping_layout.addRow("Contact:", self.contact_mapping)
            self.mapping_layout.addRow("Address:", self.address_mapping)
            
        elif import_type == "Products":
            self.name_mapping = QComboBox()
            self.description_mapping = QComboBox()
            self.price_mapping = QComboBox()
            
            self.mapping_layout.addRow("Name* (required):", self.name_mapping)
            self.mapping_layout.addRow("Description:", self.description_mapping)
            self.mapping_layout.addRow("Unit Price* (required):", self.price_mapping)
        
        # Update mapping options
        self.updateMappingOptions()
    
    def updateMappingOptions(self):
        """Update mapping dropdown options"""
        if not hasattr(self, 'name_mapping'):
            return
            
        # Get all comboboxes directly
        dropdowns = []
        for i in range(self.mapping_layout.rowCount()):
            item = self.mapping_layout.itemAt(i * 2 + 1)  # Field items are at odd indices
            if item and isinstance(item.widget(), QComboBox):
                dropdowns.append(item.widget())
        
        # Update options for each dropdown
        for dropdown in dropdowns:
            dropdown.clear()
            dropdown.addItem("-- Select Column --", -1)
            
            for idx, header in enumerate(self.csv_headers):
                dropdown.addItem(header, idx)
            
            # Try to auto-select based on header name
            label_item = self.mapping_layout.itemAt(dropdowns.index(dropdown) * 2)  # Get corresponding label
            if label_item and label_item.widget():
                field_name = label_item.widget().text().split("*")[0].strip().lower()
                
                for idx, header in enumerate(self.csv_headers):
                    if field_name in header.lower():
                        dropdown.setCurrentIndex(idx + 1)  # +1 for the "Select Column" item
                        break
    
    def loadPreviewData(self):
        """Load preview data from CSV file"""
        if not self.file_path:
            return
        
        try:
            # Read up to 10 rows for preview
            with open(self.file_path, 'r', newline='', encoding='utf-8') as csv_file:
                csv_reader = csv.reader(csv_file)
                
                # Read header row
                headers = next(csv_reader)
                
                # Read preview rows
                preview_rows = []
                for _ in range(10):
                    try:
                        preview_rows.append(next(csv_reader))
                    except StopIteration:
                        break
            
            # Set up table
            self.preview_table.setRowCount(len(preview_rows))
            self.preview_table.setColumnCount(len(headers))
            self.preview_table.setHorizontalHeaderLabels(headers)
            
            # Fill table
            for row_idx, row in enumerate(preview_rows):
                for col_idx, value in enumerate(row):
                    if col_idx < len(headers):  # Ensure we don't exceed columns
                        self.preview_table.setItem(row_idx, col_idx, QTableWidgetItem(value))
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load preview data: {str(e)}")
    
    def importData(self):
        """Import data from CSV file"""
        if not self.file_path:
            QMessageBox.warning(self, "No File", "Please select a CSV file to import.")
            return
        
        # Get import type
        import_type = self.import_type.currentText()
        
        # Get field mappings
        mappings = {}
        
        if import_type == "Customers":
            # Check required fields
            if self.name_mapping.currentData() == -1:
                QMessageBox.warning(self, "Missing Field", "Name field is required.")
                return
            
            mappings = {
                'name': self.name_mapping.currentData(),
                'contact': self.contact_mapping.currentData(),
                'address': self.address_mapping.currentData()
            }
            
        elif import_type == "Products":
            # Check required fields
            if self.name_mapping.currentData() == -1:
                QMessageBox.warning(self, "Missing Field", "Name field is required.")
                return
                
            if self.price_mapping.currentData() == -1:
                QMessageBox.warning(self, "Missing Field", "Unit Price field is required.")
                return
            
            mappings = {
                'name': self.name_mapping.currentData(),
                'description': self.description_mapping.currentData(),
                'price': self.price_mapping.currentData()
            }
        
        # Confirm import
        reply = QMessageBox.question(
            self, "Confirm Import",
            f"Are you sure you want to import {import_type} from the selected file?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            # Start import
            self.progress_bar.setVisible(True)
            self.import_btn.setEnabled(False)
            self.cancel_btn.setEnabled(False)
            
            # Create import thread
            self.import_thread = ImportThread(
                import_type,
                self.file_path,
                mappings,
                self.header_checkbox.isChecked(),
                self.db_path
            )
            
            # Connect signals
            self.import_thread.progress_updated.connect(self.progress_bar.setValue)
            self.import_thread.import_complete.connect(self.importComplete)
            self.import_thread.error_occurred.connect(self.showError)
            
            # Start thread
            self.import_thread.start()
    
    def importComplete(self, success_count, error_count):
        """Handle import completion"""
        self.progress_bar.setVisible(False)
        self.cancel_btn.setEnabled(True)
        
        # Show results
        QMessageBox.information(
            self, "Import Complete",
            f"Import completed with {success_count} successful records and {error_count} errors."
        )
        
        # Close dialog if successful
        if success_count > 0:
            self.accept()
    
    def showError(self, error_message):
        """Show error message"""
        QMessageBox.critical(self, "Import Error", error_message)
        
        # Re-enable buttons
        self.import_btn.setEnabled(True)
        self.cancel_btn.setEnabled(True)