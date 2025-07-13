"""
Enhanced Ledger Tab with Invoice Download functionality
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

# Import the auto invoice generator
from src.utils.auto_invoice_generator import AutoInvoiceGenerator

# Import database module
from src.database.mongo_adapter import MongoAdapter


class LedgerTab(QWidget):
    """
    Enhanced Ledger tab with invoice download functionality
    """
    
    def __init__(self):
        super().__init__()
        self.db = MongoAdapter()
        self.db.init_db()
        self.db.connect()
        self.invoice_generator = AutoInvoiceGenerator()
        self.initUI()
        self.loadEntries()
    
    def initUI(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("Ledger")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title)
        
        # Filter section
        filter_group = QGroupBox("Filters")
        filter_layout = QFormLayout()
        
        # Date range
        date_layout = QHBoxLayout()
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setCalendarPopup(True)
        self.from_date_edit.setDate(QDate.currentDate().addMonths(-1))
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setCalendarPopup(True)
        self.to_date_edit.setDate(QDate.currentDate())
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.from_date_edit)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.to_date_edit)
        filter_layout.addRow("Date Range:", date_layout)
        
        # Customer filter
        self.customer_filter = QComboBox()
        self.customer_filter.addItem("All Customers")
        self.loadCustomers()
        filter_layout.addRow("Customer:", self.customer_filter)
        
        # Search notes
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Search in notes...")
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
        main_layout.addWidget(self.entries_table)
        
        # Summary section
        summary_layout = QHBoxLayout()
        self.total_credit_label = QLabel("Total Credit: Rs 0.00")
        self.total_credit_label.setStyleSheet("color: green; font-weight: bold;")
        self.total_debit_label = QLabel("Total Debit: Rs 0.00")
        self.total_debit_label.setStyleSheet("color: red; font-weight: bold;")
        self.balance_label = QLabel("Balance: Rs 0.00")
        self.balance_label.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
        
        summary_layout.addWidget(self.total_credit_label)
        summary_layout.addWidget(self.total_debit_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.balance_label)
        
        main_layout.addLayout(summary_layout)
        
        # Export buttons
        export_layout = QHBoxLayout()
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.exportToCSV)
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.loadEntries)
        
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
        """Load customers for filter"""
        try:
            self.db.connect()
            self.db.cursor.execute('SELECT name FROM customers ORDER BY name')
            customers = self.db.cursor.fetchall()
            
            for customer in customers:
                self.customer_filter.addItem(customer[0])
                
        except Exception as e:
            print(f"Error loading customers: {e}")
        finally:
            self.db.close()
    
    def loadEntries(self):
        """Load entries based on filters"""
        try:
            self.db.connect()
            
            # Build query based on filters
            query = '''
                SELECT e.id, e.date, c.name, p.name, e.quantity, e.unit_price,
                       t.amount, e.is_credit, t.balance, e.notes,
                       p.batch_number, p.expiry_date
                FROM entries e
                LEFT JOIN customers c ON e.customer_id = c.id
                LEFT JOIN products p ON e.product_id = p.id
                LEFT JOIN transactions t ON t.entry_id = e.id
                WHERE 1=1
            '''
            params = []
            
            # Date filter
            from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
            to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
            query += " AND e.date BETWEEN ? AND ?"
            params.extend([from_date, to_date])
            
            # Customer filter
            if self.customer_filter.currentIndex() > 0:
                query += " AND c.name = ?"
                params.append(self.customer_filter.currentText())
            
            # Search filter
            if self.search_edit.text():
                query += " AND e.notes LIKE ?"
                params.append(f"%{self.search_edit.text()}%")
            
            # Type filter
            if not self.all_type_check.isChecked():
                if self.credit_check.isChecked() and not self.debit_check.isChecked():
                    query += " AND e.is_credit = 1"
                elif self.debit_check.isChecked() and not self.credit_check.isChecked():
                    query += " AND e.is_credit = 0"
            
            query += " ORDER BY e.date DESC, e.id DESC"
            
            self.db.cursor.execute(query, params)
            entries = self.db.cursor.fetchall()
            
            # Clear table
            self.entries_table.setRowCount(0)
            
            # Variables for summary
            total_credit = 0
            total_debit = 0
            
            # Populate table
            for entry in entries:
                row_position = self.entries_table.rowCount()
                self.entries_table.insertRow(row_position)
                
                entry_id, date, customer, product, quantity, unit_price, amount, is_credit, balance, notes, batch, expiry = entry
                
                # Add data to columns
                self.entries_table.setItem(row_position, 0, QTableWidgetItem(date))
                self.entries_table.setItem(row_position, 1, QTableWidgetItem(customer or ""))
                self.entries_table.setItem(row_position, 2, QTableWidgetItem(product or ""))
                self.entries_table.setItem(row_position, 3, QTableWidgetItem(str(quantity)))
                self.entries_table.setItem(row_position, 4, QTableWidgetItem(f"{unit_price:.2f}"))
                self.entries_table.setItem(row_position, 5, QTableWidgetItem(f"{amount:.2f}"))
                
                # Type
                type_item = QTableWidgetItem("CREDIT" if is_credit else "DEBIT")
                type_item.setForeground(Qt.green if is_credit else Qt.red)
                self.entries_table.setItem(row_position, 6, type_item)
                
                self.entries_table.setItem(row_position, 7, QTableWidgetItem(f"{balance:.2f}"))
                self.entries_table.setItem(row_position, 8, QTableWidgetItem(notes or ""))
                
                # Add download invoice button
                invoice_btn = QPushButton("Download Invoice")
                invoice_btn.setToolTip("Download or regenerate invoice for this entry")
                invoice_btn.clicked.connect(lambda checked, eid=entry_id, row=row_position: 
                                         self.downloadInvoice(eid, row))
                
                # Check if invoice already exists
                if notes and "Invoice: INV-" in notes:
                    invoice_btn.setText("📄 Invoice")
                    invoice_btn.setStyleSheet("background-color: #90EE90;")  # Light green
                else:
                    invoice_btn.setText("Generate Invoice")
                    invoice_btn.setStyleSheet("background-color: #FFE4B5;")  # Light orange
                
                self.entries_table.setCellWidget(row_position, 9, invoice_btn)
                
                # Update totals
                if is_credit:
                    total_credit += amount
                else:
                    total_debit += amount
            
            # Update summary
            self.total_credit_label.setText(f"Total Credit: Rs {total_credit:.2f}")
            self.total_debit_label.setText(f"Total Debit: Rs {total_debit:.2f}")
            
            # Get current balance (last balance in the filtered results)
            if entries:
                current_balance = entries[0][8]  # Most recent entry's balance
                self.balance_label.setText(f"Balance: Rs {current_balance:.2f}")
            else:
                self.balance_label.setText("Balance: Rs 0.00")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load entries: {str(e)}")
        finally:
            self.db.close()
    
    def downloadInvoice(self, entry_id, row):
        """Download or regenerate invoice for an entry"""
        try:
            self.db.connect()
            
            # Get entry details
            self.db.cursor.execute('''
                SELECT e.*, c.name as customer_name, c.address, 
                       p.name as product_name, p.batch_number, p.expiry_date,
                       t.amount, t.balance
                FROM entries e
                LEFT JOIN customers c ON e.customer_id = c.id
                LEFT JOIN products p ON e.product_id = p.id
                LEFT JOIN transactions t ON t.entry_id = e.id
                WHERE e.id = ?
            ''', (entry_id,))
            
            entry = self.db.cursor.fetchone()
            if not entry:
                QMessageBox.warning(self, "Error", "Entry not found!")
                return
            
            # Check if entry has multiple products (stored in notes as JSON)
            notes = entry[7]  # Assuming notes is at index 7
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
                    'product_name': entry[15],  # product_name from query
                    'batch_number': entry[16],
                    'expiry_date': entry[17],
                    'quantity': entry[4],
                    'unit_price': entry[5],
                    'discount': 0,  # Default if not stored
                    'amount': entry[18]  # amount from transactions
                }]
            
            # Prepare entry data for invoice
            entry_data = {
                'entry_id': entry_id,
                'date': entry[1],
                'customer_id': entry[2],
                'customer_name': entry[13],  # customer_name from query
                'items': items,
                'total_amount': entry[18],  # amount from transactions
                'is_credit': entry[6],
                'notes': notes,
                'balance': entry[19],  # balance from transactions
                'transport_name': 'N/A',  # Default, update if stored elsewhere
                'delivery_date': entry[1],  # Use entry date as default
                'delivery_location': entry[14] or ''  # customer address
            }
            
            # Generate invoice
            try:
                invoice_path = self.invoice_generator.generate_invoice_from_entry(
                    entry_data, self.db.conn
                )
                
                # Update button appearance
                button = self.entries_table.cellWidget(row, 9)
                if button:
                    button.setText("📄 Invoice")
                    button.setStyleSheet("background-color: #90EE90;")
                
                # Ask if user wants to open the invoice
                reply = QMessageBox.question(
                    self, "Invoice Generated",
                    f"Invoice generated successfully!\n\n{os.path.basename(invoice_path)}\n\nDo you want to open it?",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    self.openInvoice(invoice_path)
                    
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate invoice: {str(e)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process invoice: {str(e)}")
        finally:
            self.db.close()
    
    def openInvoice(self, invoice_path):
        """Open the invoice PDF"""
        import subprocess
        import sys
        
        try:
            if sys.platform == "win32":
                os.startfile(invoice_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", invoice_path])
            else:
                subprocess.call(["xdg-open", invoice_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open invoice: {str(e)}")
    
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