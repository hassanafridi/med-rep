"""
Enhanced Ledger Tab with Invoice Download functionality - 
Allows downloading/regenerating invoices for any entry
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QHeaderView, QFileDialog,
                             QComboBox, QLineEdit, QDateEdit, QGroupBox,
                             QFormLayout, QCheckBox)
from PyQt5.QtCore import Qt, QDate, pyqtSignal
from PyQt5.QtGui import QFont, QIcon, QColor
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
    Enhanced Ledger tab with invoice download functionality - 
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
        title = QLabel("Ledger - Customer Balance Tracking")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setStyleSheet("color: #4B0082; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Customer Balance Summary section
        balance_group = QGroupBox("Customer Balance Summary")
        balance_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        balance_layout = QVBoxLayout()
        
        # Customer balance table
        self.balance_table = QTableWidget()
        self.balance_table.setColumnCount(5)
        self.balance_table.setHorizontalHeaderLabels([
            'Customer', 'Total Credit', 'Total Debit', 'Balance', 'Status'
        ])
        self.balance_table.setMaximumHeight(200)
        self.balance_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.balance_table.setAlternatingRowColors(True)
        balance_layout.addWidget(self.balance_table)
        
        balance_group.setLayout(balance_layout)
        main_layout.addWidget(balance_group)
        
        # Filter section
        filter_group = QGroupBox("Transaction Filters")
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
        self.entries_table.setColumnCount(10)
        self.entries_table.setHorizontalHeaderLabels([
            'Date', 'Customer', 'Product', 'Quantity', 'Unit Price', 
            'Amount', 'Type', 'Running Balance', 'Notes', 'Invoice'
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
        self.total_debit_label = QLabel("Total Debit: PKR0.00")
        self.total_debit_label.setStyleSheet("color: red; font-weight: bold;")
        self.total_credit_label = QLabel("Total Credit: PKR0.00")
        self.total_credit_label.setStyleSheet("color: green; font-weight: bold;")
        self.net_label = QLabel("Net Balance: PKR0.00")
        self.net_label.setStyleSheet("color: blue; font-weight: bold; font-size: 14px;")
        
        summary_layout.addWidget(self.total_credit_label)
        summary_layout.addWidget(self.total_debit_label)
        summary_layout.addStretch()
        summary_layout.addWidget(self.net_label)
        
        main_layout.addLayout(summary_layout)
        
        # Export buttons
        export_layout = QHBoxLayout()
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.exportToCSV)
        
        self.refresh_btn = QPushButton("Refresh")
        self.refresh_btn.clicked.connect(self.loadData)
        
        export_layout.addWidget(self.export_csv_btn)
        export_layout.addWidget(self.refresh_btn)
        export_layout.addStretch()
        
        main_layout.addLayout(export_layout)
        
        self.setLayout(main_layout)
        
        # Connect type checkboxes
        self.all_type_check.toggled.connect(self.onAllTypeToggled)
        self.credit_check.toggled.connect(self.onTypeToggled)
        self.debit_check.toggled.connect(self.onTypeToggled)
        
        # Load initial data
        self.loadData()
    
    def loadData(self):
        """Load both customer balances and entries"""
        self.loadCustomerBalances()
        self.loadEntries()
    
    def loadCustomerBalances(self):
        """Load customer balance summary"""
        try:
            customer_balances = self.mongo_adapter.get_all_customer_balances()
            
            # Sort by balance (highest first)
            customer_balances.sort(key=lambda x: x['balance'], reverse=True)
            
            # Setup table
            self.balance_table.setRowCount(len(customer_balances))
            
            for row, customer in enumerate(customer_balances):
                # Customer name
                self.balance_table.setItem(row, 0, QTableWidgetItem(customer['name']))
                
                # Total Credit
                credit_item = QTableWidgetItem(f"PKR{customer['credit_total']:,.2f}")
                credit_item.setForeground(QColor(0, 128, 0))  # Green
                self.balance_table.setItem(row, 1, credit_item)
                
                # Total Debit
                debit_item = QTableWidgetItem(f"PKR{customer['debit_total']:,.2f}")
                debit_item.setForeground(QColor(0, 128, 0))  # Red
                self.balance_table.setItem(row, 2, debit_item)
                
                # Balance (Credit - Debit, but show 0 if negative)
                raw_balance = customer.get('raw_balance', customer['balance'])
                display_balance = customer['balance']  # This is already max(0, raw_balance)
                balance_item = QTableWidgetItem(f"PKR{display_balance:,.2f}")
                
                # Determine status based on raw balance
                if raw_balance > 0:
                    balance_item.setForeground(QColor(0, 128, 0))  # Green for positive
                    balance_item.setBackground(QColor(240, 255, 240))  # Light green background
                    status = "Credit Balance"
                elif raw_balance < 0:
                    # Show 0.00 but indicate it's actually a debit situation
                    balance_item.setForeground(QColor(128, 128, 128))  # Gray for zero display
                    balance_item.setBackground(QColor(245, 245, 245))  # Light gray background
                    status = "No Balance"
                else:
                    balance_item.setForeground(QColor(128, 128, 128))  # Gray for zero
                    status = "Balanced"
                
                self.balance_table.setItem(row, 3, balance_item)
                
                # Status
                status_item = QTableWidgetItem(status)
                if raw_balance > 0:
                    status_item.setForeground(QColor(0, 128, 0))
                elif raw_balance < 0:
                    status_item.setForeground(QColor(128, 128, 128))
                self.balance_table.setItem(row, 4, status_item)
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load customer balances: {str(e)}")
    
    def loadEntries(self):
        """Load entries with filters applied"""
        try:
            # Prepare filters
            filters = {}
            
            # Date range
            filters['from_date'] = self.from_date_edit.date().toString("yyyy-MM-dd")
            filters['to_date'] = self.to_date_edit.date().toString("yyyy-MM-dd")
            
            # Customer filter
            if self.customer_filter.currentIndex() > 0:
                customer_name = self.customer_filter.currentText()
                customers = self.mongo_adapter.get_customers()
                for customer in customers:
                    if customer.get('name') == customer_name:
                        filters['customer_id'] = customer.get('id')
                        break
        
            # Entry type filter
            if not self.all_type_check.isChecked():
                if self.credit_check.isChecked() and not self.debit_check.isChecked():
                    filters['entry_type'] = 'credit'
                elif self.debit_check.isChecked() and not self.credit_check.isChecked():
                    filters['entry_type'] = 'debit'
        
            # Notes search
            search_text = self.search_edit.text().strip()
            if search_text:
                filters['notes_search'] = search_text
        
            # Get filtered entries with balance
            entries = self.mongo_adapter.get_entries_with_balance(filters)
        
            # Setup table
            self.entries_table.setRowCount(len(entries))
        
            total_credit = 0
            total_debit = 0
        
            for row, entry in enumerate(entries):
                # Date
                self.entries_table.setItem(row, 0, QTableWidgetItem(entry['date']))
                
                # Customer
                self.entries_table.setItem(row, 1, QTableWidgetItem(entry['customer_name']))
                
                # Product
                self.entries_table.setItem(row, 2, QTableWidgetItem(entry['product_name']))
                
                # Quantity
                self.entries_table.setItem(row, 3, QTableWidgetItem(str(entry['quantity'])))
                
                # Unit Price
                self.entries_table.setItem(row, 4, QTableWidgetItem(f"PKR{entry['unit_price']:,.2f}"))
                
                # Amount
                amount_item = QTableWidgetItem(f"PKR{entry['amount']:,.2f}")
                self.entries_table.setItem(row, 5, amount_item)
                
                # Type
                type_item = QTableWidgetItem(entry['type'])
                if entry['is_credit']:
                    type_item.setForeground(QColor(255, 0, 0))  
                    total_credit += entry['amount']
                else:
                    type_item.setForeground(QColor(0, 128, 0))  
                    total_debit += entry['amount']
                
                self.entries_table.setItem(row, 6, type_item)
                
                # Running Balance (already handled in database adapter)
                balance_item = QTableWidgetItem(f"PKR{entry['running_balance']:,.2f}")
                if entry['running_balance'] > 0:
                    balance_item.setForeground(QColor(0, 128, 0))
                else:
                    balance_item.setForeground(QColor(128, 128, 128)) 
                
                self.entries_table.setItem(row, 7, balance_item)
                
                # Notes
                self.entries_table.setItem(row, 8, QTableWidgetItem(entry['notes']))
                
                # Invoice button
                invoice_btn = QPushButton("Download")
                invoice_btn.clicked.connect(lambda checked, entry_id=entry['id'], r=row: self.downloadInvoice(entry_id, r))
                self.entries_table.setCellWidget(row, 9, invoice_btn)
        
            # Update summary
            net_balance = max(0, total_credit - total_debit)  # Show 0 if negative
            self.total_credit_label.setText(f"Total Credit: PKR{total_credit:,.2f}")
            self.total_debit_label.setText(f"Total Debit: PKR{total_debit:,.2f}")
            self.net_label.setText(f"Net Balance: PKR{net_balance:,.2f}")
        
            # Color code net balance
            raw_net = total_credit - total_debit
            if raw_net > 0:
                self.net_label.setStyleSheet("color: green; font-weight: bold; font-size: 14px;")
            else:
                self.net_label.setStyleSheet("color: gray; font-weight: bold; font-size: 14px;")
        
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to load entries: {str(e)}")
    
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
    
    def downloadInvoice(self, entry_id, row):
        """Download or regenerate invoice for an entry using existing invoice number"""
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
            
            # Extract invoice number from notes
            invoice_number = self.extractInvoiceNumber(entry.get('notes', ''))
            
            if not invoice_number:
                # Generate new invoice number if none exists
                invoice_number = self.generateInvoiceNumber()
                
                # Update entry notes with new invoice number
                self.updateEntryWithInvoiceNumber(entry_id, invoice_number)
            
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
            items = self.extractProductsFromNotes(notes, product, entry)
            
            # Extract transport and delivery info from notes
            transport_info = self.extractTransportInfo(notes)
            
            # Prepare entry data for invoice with original invoice number
            entry_data = {
                'entry_id': entry_id,
                'invoice_number': invoice_number,  # Use existing or new invoice number
                'date': entry.get('date', ''),
                'customer_id': customer_id,
                'customer_name': customer.get('name', ''),
                'customer_address': customer.get('address', ''),
                'customer_contact': customer.get('contact', ''),
                'items': items,
                'total_amount': transaction.get('amount', 0) if transaction else sum(item.get('amount', 0) for item in items),
                'is_credit': entry.get('is_credit', True),
                'notes': self.cleanNotesForInvoice(notes),
                'balance': transaction.get('balance', 0) if transaction else 0,
                'transport_name': transport_info.get('transport_name', 'Standard Delivery'),
                'delivery_date': transport_info.get('delivery_date', entry.get('date', '')),
                'delivery_location': transport_info.get('delivery_location', customer.get('address', '').split('\n')[0] if customer.get('address') else 'Customer Location')
            }
            
            # Generate invoice using improved PDF generator
            try:
                from src.utils.pdf_generator import ImprovedPDFGenerator
                
                # Prepare invoice data for PDF generator
                invoice_data = {
                    'company_name': 'Tru_pharma',
                    'company_logo': None,
                    'company_contact': '0333-99-11-514',
                    'company_address': 'Main Market, Faisalabad\nPunjab, Pakistan\nPhone: 0333-99-11-514',
                    'customer_info': {
                        'name': entry_data['customer_name'],
                        'address': entry_data['customer_address'],
                        'contact': entry_data['customer_contact']
                    },
                    'transport_info': {
                        'transport_name': entry_data['transport_name'],
                        'delivery_date': entry_data['delivery_date'],
                        'delivery_location': entry_data['delivery_location']
                    },
                    'invoice_details': {
                        'invoice_number': entry_data['invoice_number'],
                        'invoice_date': entry_data['date']
                    },
                    'items': entry_data['items'],
                    'terms': entry_data['notes'] or 'Thank you for your business!',
                    'total_amount': entry_data['total_amount']
                }
                
                # Get file save location
                default_filename = f"{invoice_number}.pdf"
                file_path, _ = QFileDialog.getSaveFileName(
                    self, "Save Invoice", default_filename,
                    "PDF Files (*.pdf);;All Files (*)"
                )
                
                if file_path:
                    pdf_generator = ImprovedPDFGenerator()
                    success = pdf_generator.generate_invoice_pdf(invoice_data, file_path)
                    
                    if success:
                        QMessageBox.information(
                            self, "Invoice Generated",
                            f"Invoice regenerated successfully:\n{file_path}\n\n"
                            f"Invoice Number: {invoice_number}\n"
                            f"Customer: {entry_data['customer_name']}\n"
                            f"Amount: PKR{entry_data['total_amount']:.2f}\n"
                            f"Items: {len(items)}"
                        )
                        
                        # Update button appearance
                        button = self.entries_table.cellWidget(row, 9)
                        if button:
                            button.setText("📄 Downloaded")
                            button.setStyleSheet("background-color: #90EE90; padding: 5px; font-weight: bold;")
                    else:
                        QMessageBox.critical(self, "Error", "Failed to generate PDF invoice.")
                
            except ImportError:
                QMessageBox.critical(
                    self, "Missing Library",
                    "ReportLab library is required for PDF generation.\n"
                    "Please install it using: pip install reportlab"
                )
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to generate invoice: {str(e)}")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to process invoice: {str(e)}")
    
    def extractInvoiceNumber(self, notes):
        """Extract invoice number from notes"""
        try:
            import re
            # Look for pattern like "Invoice: INV-20241201-123"
            pattern = r"Invoice:\s*(INV-\d{8}-\d{3})"
            match = re.search(pattern, notes)
            if match:
                return match.group(1)
            return None
        except Exception as e:
            print(f"Error extracting invoice number: {e}")
            return None
    
    def extractProductsFromNotes(self, notes, default_product, entry):
        """Extract products information from notes"""
        try:
            # Try to extract JSON products list
            import re
            json_match = re.search(r'Products:\s*(\[.*?\])', notes)
            if json_match:
                products_json = json_match.group(1)
                items = json.loads(products_json)
                # Ensure each item has required fields
                for item in items:
                    if 'product_id' not in item:
                        item['product_id'] = 'N/A'
                    if 'batch_number' not in item:
                        item['batch_number'] = 'N/A'
                    if 'expiry_date' not in item:
                        item['expiry_date'] = 'N/A'
                return items
        except Exception as e:
            print(f"Error parsing products JSON: {e}")
        
        # Fallback to single product from entry
        return [{
            'product_name': default_product.get('name', 'Unknown Product'),
            'batch_number': default_product.get('batch_number', 'N/A'),
            'expiry_date': default_product.get('expiry_date', 'N/A'),
            'quantity': entry.get('quantity', 0),
            'unit_price': entry.get('unit_price', 0),
            'discount': 0,
            'amount': float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
        }]
    
    def extractTransportInfo(self, notes):
        """Extract transport and delivery information from notes"""
        try:
            import re
            
            # Extract transport name
            transport_match = re.search(r'Transport:\s*([^|]+)', notes)
            transport_name = transport_match.group(1).strip() if transport_match else "Standard Delivery"
            
            # Extract delivery location and date
            delivery_match = re.search(r'Delivery:\s*([^(]+)\s*\(([^)]+)\)', notes)
            if delivery_match:
                delivery_location = delivery_match.group(1).strip()
                delivery_date = delivery_match.group(2).strip()
            else:
                delivery_location = "Customer Location"
                delivery_date = ""
            
            return {
                'transport_name': transport_name,
                'delivery_location': delivery_location,
                'delivery_date': delivery_date
            }
        except Exception as e:
            print(f"Error extracting transport info: {e}")
            return {
                'transport_name': "Standard Delivery",
                'delivery_location': "Customer Location",
                'delivery_date': ""
            }
    
    def cleanNotesForInvoice(self, notes):
        """Clean notes by removing invoice metadata for display"""
        try:
            import re
            # Remove invoice number, transport info, and products JSON
            cleaned = re.sub(r'\s*\|\s*Invoice:[^|]*', '', notes)
            cleaned = re.sub(r'\s*\|\s*Transport:[^|]*', '', cleaned)
            cleaned = re.sub(r'\s*\|\s*Delivery:[^|]*', '', cleaned)
            cleaned = re.sub(r'\s*\|\s*Products:\s*\[.*?\]', '', cleaned)
            return cleaned.strip()
        except Exception as e:
            print(f"Error cleaning notes: {e}")
            return notes
    
    def generateInvoiceNumber(self):
        """Generate a new invoice number"""
        import random
        from datetime import datetime
        today = datetime.now()
        random_suffix = random.randint(100, 999)
        return f"INV-{today.year}{today.month:02d}{today.day:02d}-{random_suffix}"
    
    def updateEntryWithInvoiceNumber(self, entry_id, invoice_number):
        """Update entry notes with invoice number"""
        try:
            # Get current entry
            entry = self.mongo_adapter.get_entry_by_id(entry_id)
            if not entry:
                print(f"Entry {entry_id} not found")
                return
            
            # Get current notes and add invoice number
            current_notes = entry.get('notes', '')
            
            # Check if invoice number already exists
            if f"Invoice: {invoice_number}" not in current_notes:
                # Add invoice number to notes
                if current_notes:
                    new_notes = f"{current_notes} | Invoice: {invoice_number}"
                else:
                    new_notes = f"Invoice: {invoice_number}"
                
                # Update the entry
                success = self.mongo_adapter.update_entry_notes(entry_id, new_notes)
                if success:
                    print(f"Updated entry {entry_id} with invoice number {invoice_number}")
                else:
                    print(f"Failed to update entry {entry_id}")
        except Exception as e:
            print(f"Error updating entry with invoice number: {e}")
    
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