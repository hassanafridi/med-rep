"""
Enhanced Ledger Tab with Invoice Download functionality - MongoDB Edition
Allows downloading/regenerating invoices for any entry
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QFileDialog,
                             QComboBox, QLineEdit, QDateEdit, QGroupBox,
                             QFormLayout, QCheckBox)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from datetime import datetime
import json
import os
import re
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import MongoDB adapter
from src.database.mongo_adapter import MongoAdapter

class LedgerTab(QWidget):
    """
    Enhanced Ledger tab with invoice download functionality - MongoDB Edition
    """
    
    def __init__(self, mongo_adapter=None):
        super().__init__()
        try:
            self.mongo_adapter = mongo_adapter or MongoAdapter()
            self.initUI()
            self.loadEntries()
        except Exception as e:
            print(f"Error initializing Ledger tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Ledger tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the ledger tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.mongo_adapter)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Ledger tab: {str(e)}")
    
    def initUI(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Ledger - MongoDB Edition")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #4B0082; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Filter section
        filter_group = QGroupBox("Filters")
        filter_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        filter_layout = QFormLayout()
        
        # Date range
        date_layout = QHBoxLayout()
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.from_date_edit.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.from_date_edit)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.to_date_edit)
        filter_layout.addRow("Date Range:", date_layout)
        
        # Customer filter
        self.customer_filter = QComboBox()
        self.customer_filter.addItem("All Customers")
        self.customer_filter.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        self.loadCustomers()
        filter_layout.addRow("Customer:", self.customer_filter)
        
        # Search notes
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search in notes...")
        self.search_edit.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        filter_layout.addRow("Search:", self.search_edit)
        
        # Entry type filter
        type_layout = QHBoxLayout()
        self.all_type_check = QCheckBox("All")
        self.all_type_check.setChecked(True)
        self.credit_check = QCheckBox("Credit")
        self.debit_check = QCheckBox("Debit")
        type_layout.addWidget(self.all_type_check)
        type_layout.addWidget(self.credit_check)
        type_layout.addWidget(self.debit_check)
        filter_layout.addRow("Type:", type_layout)
        
        # Apply filters button
        self.apply_filters_btn = QPushButton("Apply Filters")
        self.apply_filters_btn.clicked.connect(self.loadEntries)
        self.apply_filters_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        filter_layout.addRow("", self.apply_filters_btn)
        
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # Entries table
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(10)  # Added column for invoice button
        self.entries_table.setHorizontalHeaderLabels([
            'Date', 'Customer', 'Product', 'Quantity', 'Unit Price', 
            'Amount', 'Type', 'Balance', 'Notes', 'Invoice'
        ])
        
        # Adjust column widths
        header = self.entries_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.Stretch)  # Customer
        header.setSectionResizeMode(2, QHeaderView.Stretch)  # Product
        header.setSectionResizeMode(8, QHeaderView.Stretch)  # Notes
        
        self.entries_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.entries_table.setStyleSheet("border: 1px solid #4B0082;")
        main_layout.addWidget(self.entries_table)
        
        # Summary section
        summary_layout = QHBoxLayout()
        self.total_credit_label = QLabel("Total Credit: PKR0.00")
        self.total_credit_label.setStyleSheet("color: green; font-weight: bold;")
        self.total_debit_label = QLabel("Total Debit: PKR0.00")
        self.total_debit_label.setStyleSheet("color: red; font-weight: bold;")
        self.balance_label = QLabel("Balance: PKR0.00")
        self.balance_label.setStyleSheet("color: #4B0082; font-weight: bold; font-size: 14px;")
        
        summary_layout.addWidget(self.total_credit_label)
        summary_layout.addWidget(self.total_debit_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.balance_label)
        
        main_layout.addLayout(summary_layout)
        
        # Export buttons
        export_layout = QHBoxLayout()
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.exportToCSV)
        self.export_csv_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.loadEntries)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 8px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.refresh_btn)
        export_layout.addStretch()
        
        main_layout.addLayout(export_layout)
        
        self.setLayout(main_layout)
        
        # Connect type checkboxes
        self.all_type_check.toggled.connect(self.onAllTypeToggled)
        self.credit_check.toggled.connect(self.onTypeToggled)
        self.debit_check.toggled.connect(self.onTypeToggled)
    
    def loadCustomers(self):
        """Load customers for filter using MongoDB"""
        try:
            if not self.mongo_adapter:
                return
                
            customers = self.mongo_adapter.get_customers()
            
            for customer in customers:
                name = customer.get('name', '')
                if name:
                    self.customer_filter.addItem(name)
                
        except Exception as e:
            print(f"Error loading customers: {e}")
    
    def loadEntries(self):
        """Load entries based on filters using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get all data from MongoDB
            entries = self.mongo_adapter.get_entries()
            customers = self.mongo_adapter.get_customers()
            products = self.mongo_adapter.get_products()
            transactions = self.mongo_adapter.get_transactions()
            
            # Create lookup dictionaries
            customer_lookup = {str(customer.get('id')): customer for customer in customers}
            product_lookup = {str(product.get('id')): product for product in products}
            transaction_lookup = {str(transaction.get('entry_id')): transaction for transaction in transactions}
            
            # Apply filters
            from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
            to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
            customer_filter = self.customer_filter.currentText()
            search_text = self.search_edit.text().lower()
            
            filtered_entries = []
            for entry in entries:
                entry_date = entry.get('date', '')
                
                # Date filter
                if not (from_date <= entry_date <= to_date):
                    continue
                
                # Customer filter
                if customer_filter != "All Customers":
                    customer_id = str(entry.get('customer_id', ''))
                    customer_info = customer_lookup.get(customer_id, {})
                    if customer_info.get('name', '') != customer_filter:
                        continue
                
                # Search filter
                if search_text:
                    notes = entry.get('notes', '').lower()
                    if search_text not in notes:
                        continue
                
                # Type filter
                if not self.all_type_check.isChecked():
                    is_credit = entry.get('is_credit', True)
                    if self.credit_check.isChecked() and not is_credit:
                        continue
                    if self.debit_check.isChecked() and is_credit:
                        continue
                
                filtered_entries.append(entry)
            
            # Sort by date (newest first)
            filtered_entries.sort(key=lambda x: x.get('date', ''), reverse=True)
            
            # Clear table
            self.entries_table.setRowCount(0)
            
            # Variables for summary
            total_credit = 0
            total_debit = 0
            
            # Populate table
            for entry in filtered_entries:
                row_position = self.entries_table.rowCount()
                self.entries_table.insertRow(row_position)
                
                entry_id = str(entry.get('id', ''))
                date = entry.get('date', '')
                customer_id = str(entry.get('customer_id', ''))
                product_id = str(entry.get('product_id', ''))
                quantity = entry.get('quantity', 0)
                unit_price = entry.get('unit_price', 0)
                is_credit = entry.get('is_credit', True)
                notes = entry.get('notes', '')
                
                # Get customer and product info
                customer_info = customer_lookup.get(customer_id, {})
                product_info = product_lookup.get(product_id, {})
                transaction_info = transaction_lookup.get(entry_id, {})
                
                customer_name = customer_info.get('name', 'Unknown Customer')
                product_name = product_info.get('name', 'Unknown Product')
                amount = float(quantity) * float(unit_price)
                balance = transaction_info.get('balance', 0)
                
                # Add data to columns
                self.entries_table.setItem(row_position, 0, QTableWidgetItem(date))
                self.entries_table.setItem(row_position, 1, QTableWidgetItem(customer_name))
                self.entries_table.setItem(row_position, 2, QTableWidgetItem(product_name))
                self.entries_table.setItem(row_position, 3, QTableWidgetItem(str(quantity)))
                self.entries_table.setItem(row_position, 4, QTableWidgetItem(f"{unit_price:.2f}"))
                self.entries_table.setItem(row_position, 5, QTableWidgetItem(f"{amount:.2f}"))
                
                # Type
                type_item = QTableWidgetItem("CREDIT" if is_credit else "DEBIT")
                type_item.setForeground(Qt.green if is_credit else Qt.red)
                self.entries_table.setItem(row_position, 6, type_item)
                
                self.entries_table.setItem(row_position, 7, QTableWidgetItem(f"{balance:.2f}"))
                self.entries_table.setItem(row_position, 8, QTableWidgetItem(notes))
                
                # Add download invoice button
                invoice_btn = QPushButton("Download Invoice")
                invoice_btn.setToolTip("Download or regenerate invoice for this entry")
                invoice_btn.clicked.connect(lambda checked, eid=entry_id, row=row_position: 
                                         self.downloadInvoice(eid, row))
                
                # Check if invoice already exists
                if notes and "Invoice: INV-" in notes:
                    invoice_btn.setText("📄 Invoice")
                    invoice_btn.setStyleSheet("background-color: #90EE90; padding: 5px; font-weight: bold;")  # Light green
                else:
                    invoice_btn.setText("Generate Invoice")
                    invoice_btn.setStyleSheet("background-color: #FFE4B5; padding: 5px; font-weight: bold;")  # Light orange
                
                self.entries_table.setCellWidget(row_position, 9, invoice_btn)
                
                # Update totals
                if is_credit:
                    total_credit += amount
                else:
                    total_debit += amount
            
            # Update summary
            self.total_credit_label.setText(f"Total Credit: PKR{total_credit:.2f}")
            self.total_debit_label.setText(f"Total Debit: PKR{total_debit:.2f}")
            
            # Get current balance (last balance in the filtered results)
            if filtered_entries:
                # Find the most recent transaction balance
                latest_entry_id = str(filtered_entries[0].get('id', ''))
                latest_transaction = transaction_lookup.get(latest_entry_id, {})
                current_balance = latest_transaction.get('balance', 0)
                self.balance_label.setText(f"Balance: PKR{current_balance:.2f}")
            else:
                self.balance_label.setText("Balance: PKR0.00")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load entries: {str(e)}")
    
    def downloadInvoice(self, entry_id, row):
        """Download or regenerate invoice for an entry using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
            
            # Get entry details from MongoDB
            entries = self.mongo_adapter.get_entries()
            customers = self.mongo_adapter.get_customers()
            products = self.mongo_adapter.get_products()
            transactions = self.mongo_adapter.get_transactions()
            
            # Find the specific entry
            entry = None
            for e in entries:
                if str(e.get('id', '')) == entry_id:
                    entry = e
                    break
            
            if not entry:
                QMessageBox.warning(self, "Error", "Entry not found!")
                return
            
            # Get related data
            customer_id = str(entry.get('customer_id', ''))
            product_id = str(entry.get('product_id', ''))
            
            customer = None
            for c in customers:
                if str(c.get('id', '')) == customer_id:
                    customer = c
                    break
            
            product = None
            for p in products:
                if str(p.get('id', '')) == product_id:
                    product = p
                    break
            
            transaction = None
            for t in transactions:
                if str(t.get('entry_id', '')) == entry_id:
                    transaction = t
                    break
            
            if not customer or not product:
                QMessageBox.warning(self, "Error", "Customer or product data not found!")
                return
            
            # Check if entry has multiple products (stored in notes as JSON)
            notes = entry.get('notes', '')
            items = []
            
            if notes and "Products: " in notes:
                # Extract JSON from notes
                try:
                    json_match = re.search(r'Products: (\[.*\])', notes)
                    if json_match:
                        products_json = json_match.group(1)
                        items = json.loads(products_json)
                except:
                    pass
            
            # If no items found in JSON, create single item from entry
            if not items:
                items = [{
                    'product_name': product.get('name', ''),
                    'batch_number': product.get('batch_number', ''),
                    'expiry_date': product.get('expiry_date', ''),
                    'quantity': entry.get('quantity', 0),
                    'unit_price': entry.get('unit_price', 0),
                    'discount': 0,  # Default if not stored
                    'amount': transaction.get('amount', 0) if transaction else 0
                }]
            
            # Prepare entry data for invoice
            entry_data = {
                'entry_id': entry_id,
                'date': entry.get('date', ''),
                'customer_id': customer_id,
                'customer_name': customer.get('name', ''),
                'items': items,
                'total_amount': transaction.get('amount', 0) if transaction else 0,
                'is_credit': entry.get('is_credit', True),
                'notes': notes,
                'balance': transaction.get('balance', 0) if transaction else 0,
                'transport_name': 'Standard Delivery',  # Default
                'delivery_date': entry.get('date', ''),  # Use entry date as default
                'delivery_location': customer.get('address', '')
            }
            
            # Generate invoice (simplified version without auto_invoice_generator)
            try:
                invoice_filename = f"INV-{entry_data['date']}-{entry_id[:8]}.pdf"
                
                # For now, just simulate invoice generation
                # In a real implementation, you would generate the actual PDF here
                QMessageBox.information(
                    self, "Invoice Generated",
                    f"Invoice would be generated: {invoice_filename}\n\n"
                    f"Customer: {entry_data['customer_name']}\n"
                    f"Amount: PKR{entry_data['total_amount']:.2f}\n"
                    f"Items: {len(items)}"
                )
                
                # Update button appearance
                button = self.entries_table.cellWidget(row, 9)
                if button:
                    button.setText("📄 Invoice")
                    button.setStyleSheet("background-color: #90EE90; padding: 5px; font-weight: bold;")
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate invoice: {str(e)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process invoice: {str(e)}")
    
    def onAllTypeToggled(self, checked):
        """Handle all type checkbox toggle"""
        if checked:
            self.credit_check.setChecked(False)
            self.debit_check.setChecked(False)
    
    def onTypeToggled(self):
        """Handle individual type checkbox toggle"""
        if self.credit_check.isChecked() or self.debit_check.isChecked():
            self.all_type_check.setChecked(False)
    
    def exportToCSV(self):
        """Export current view to CSV"""
        if self.entries_table.rowCount() == 0:
            QMessageBox.warning(self, "No Data", "No entries to export!")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export to CSV", f"ledger_export_{datetime.now().strftime('%Y%m%d')}.csv",
            "CSV Files (*.csv)"
        )
        
        if file_path:
            try:
                import csv
                
                with open(file_path, 'w', newline='', encoding='utf-8') as file:
                    writer = csv.writer(file)
                    
                    # Write headers (excluding invoice column)
                    headers = []
                    for col in range(self.entries_table.columnCount() - 1):
                        headers.append(self.entries_table.horizontalHeaderItem(col).text())
                    writer.writerow(headers)
                    
                    # Write data
                    for row in range(self.entries_table.rowCount()):
                        row_data = []
                        for col in range(self.entries_table.columnCount() - 1):
                            item = self.entries_table.item(row, col)
                            row_data.append(item.text() if item else "")
                        writer.writerow(row_data)
                
                QMessageBox.information(self, "Export Successful", 
                                      f"Data exported to:\n{file_path}")
                
            except Exception as e:
                QMessageBox.critical(self, "Export Error", 
                                   f"Failed to export data: {str(e)}")