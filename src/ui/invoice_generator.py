from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QDateEdit, QGroupBox, QFormLayout,
    QPushButton, QDialog, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtPrintSupport import QPrinter, QPrintPreviewDialog
from PyQt5.QtGui import QPixmap, QTextDocument, QFont, QTextCursor, QTextTableFormat
import os
import sys
import datetime
import tempfile

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter
from src.utils.pdf_generator import PDFGenerator

class InvoicePreviewDialog(QDialog):
    def __init__(self, invoice_html, parent=None):
        super().__init__(parent)
        self.invoice_html = invoice_html
        self.setWindowTitle("Invoice Preview")
        self.setMinimumSize(800, 600)
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        # Create text document with invoice HTML
        self.doc = QTextDocument()
        self.doc.setHtml(self.invoice_html)
        
        # Create preview
        preview = QPrintPreviewDialog()
        preview.paintRequested.connect(self.printPreview)
        
        layout.addWidget(preview)
        
        self.setLayout(layout)
        
    def printPreview(self, printer):
        """Print the invoice to the printer"""
        self.doc.print_(printer)

class InvoiceGenerator(QWidget):
    def __init__(self, current_user=None, mongo_adapter=None):
        super().__init__()
        try:
            self.mongo_adapter = mongo_adapter or MongoAdapter()
            self.current_user = current_user
            self.company_logo = None
            self.invoice_items = []
            self.customer_data = {}
            self.initUI()
        except Exception as e:
            print(f"Error initializing Invoice Generator: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Invoice Generator temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the invoice generator"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.current_user, self.mongo_adapter)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Invoice Generator: {str(e)}")
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Invoice header information
        header_group = QGroupBox("Invoice Information")
        header_layout = QFormLayout()
        
        # Invoice number
        self.invoice_number = QLineEdit()
        self.invoice_number.setText(self.generateInvoiceNumber())
        self.invoice_number.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        header_layout.addRow("Invoice Number:", self.invoice_number)
        
        # Date
        self.invoice_date = QDateEdit()
        self.invoice_date.setDate(QDate.currentDate())
        self.invoice_date.setCalendarPopup(True)
        self.invoice_date.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        header_layout.addRow("Invoice Date:", self.invoice_date)
        
        # Due date
        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(30))
        self.due_date.setCalendarPopup(True)
        self.due_date.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        header_layout.addRow("Due Date:", self.due_date)
        
        # Customer selection
        self.customer_combo = QComboBox()
        self.customer_combo.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        self.loadCustomers()
        header_layout.addRow("Customer:", self.customer_combo)
        
        # Your company info
        self.company_name = QLineEdit("Your Company Name")
        self.company_name.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        header_layout.addRow("Your Company:", self.company_name)
        
        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(80)
        self.company_address.setText("123 Business St\nAnytown, USA 12345\nPhone: (555) 123-4567\nEmail: info@yourcompany.com")
        self.company_address.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        header_layout.addRow("Your Address:", self.company_address)
        
        # Logo selection
        logo_layout = QHBoxLayout()
        self.logo_preview = QLabel("No logo")
        self.logo_preview.setFixedSize(100, 50)
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setStyleSheet("border: 1px solid #4B0082;")
        
        self.select_logo_btn = QPushButton("Select Logo")
        self.select_logo_btn.clicked.connect(self.selectLogo)
        self.select_logo_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        logo_layout.addWidget(self.logo_preview)
        logo_layout.addWidget(self.select_logo_btn)
        
        header_layout.addRow("Logo:", logo_layout)
        
        header_group.setLayout(header_layout)
        main_layout.addWidget(header_group)
        
        # Invoice items
        items_group = QGroupBox("Invoice Items")
        items_layout = QVBoxLayout()
        
        # Table for items
        self.items_table = QTableWidget()
        self.items_table.setColumnCount(6)
        self.items_table.setHorizontalHeaderLabels([
            "Product", "Description", "Quantity", "Unit Price", "Total", "Actions"
        ])
        self.items_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.items_table.setStyleSheet("border: 1px solid #4B0082;")
        
        items_layout.addWidget(self.items_table)
        
        # Buttons for managing items
        buttons_layout = QHBoxLayout()
        
        self.add_item_btn = QPushButton("Add Item")
        self.add_item_btn.clicked.connect(self.addInvoiceItem)
        self.add_item_btn.setStyleSheet("""
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
        
        self.add_from_db_btn = QPushButton("Add from Transactions")
        self.add_from_db_btn.clicked.connect(self.addFromTransactions)
        self.add_from_db_btn.setStyleSheet("""
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
        
        self.clear_items_btn = QPushButton("Clear All Items")
        self.clear_items_btn.clicked.connect(self.clearItems)
        
        buttons_layout.addWidget(self.add_item_btn)
        buttons_layout.addWidget(self.add_from_db_btn)
        buttons_layout.addWidget(self.clear_items_btn)
        
        items_layout.addLayout(buttons_layout)
        
        # Totals section
        totals_layout = QFormLayout()
        
        self.subtotal_label = QLabel("$0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setValue(0)
        self.tax_rate.setSuffix("%")
        self.tax_rate.valueChanged.connect(self.updateTotals)
        self.tax_rate.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        totals_layout.addRow("Tax Rate:", self.tax_rate)
        
        self.tax_amount_label = QLabel("$0.00")
        self.tax_amount_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Tax Amount:", self.tax_amount_label)
        
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px; color: #4B0082;")
        totals_layout.addRow("Total:", self.total_label)
        
        items_layout.addLayout(totals_layout)
        
        items_group.setLayout(items_layout)
        main_layout.addWidget(items_group)
        
        # Notes
        notes_group = QGroupBox("Notes & Terms")
        notes_layout = QVBoxLayout()
        
        self.notes = QTextEdit()
        self.notes.setPlaceholderText("Enter notes or terms and conditions...")
        self.notes.setText("Thank you for your business!\nPayment is due within 30 days.")
        self.notes.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        
        notes_layout.addWidget(self.notes)
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview Invoice")
        self.preview_btn.clicked.connect(self.previewInvoice)
        self.preview_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        self.save_pdf_btn = QPushButton("Save as PDF")
        self.save_pdf_btn.clicked.connect(self.saveAsPdf)
        self.save_pdf_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        self.print_btn = QPushButton("Print")
        self.print_btn.clicked.connect(self.printInvoice)
        self.print_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 10px;
                font-weight: bold;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        actions_layout.addWidget(self.preview_btn)
        actions_layout.addWidget(self.save_pdf_btn)
        actions_layout.addWidget(self.print_btn)
        
        main_layout.addLayout(actions_layout)
        
        self.setLayout(main_layout)
    
    def generateInvoiceNumber(self):
        """Generate a unique invoice number"""
        today = datetime.date.today()
        return f"INV-{today.year}{today.month:02d}{today.day:02d}-{1:03d}"
    
    def loadCustomers(self):
        """Load customers into combo box using MongoDB"""
        try:
            # Validate MongoDB connection
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
            
            # Get all customers from MongoDB
            customers = self.mongo_adapter.get_customers()
            
            # Clear and populate combo box
            self.customer_combo.clear()
            self.customer_data = {}
            
            for customer in customers:
                name = customer.get('name', '')
                if name:
                    self.customer_combo.addItem(name)
                    self.customer_data[name] = {
                        'id': customer.get('id', ''),
                        'contact': customer.get('contact', ''),
                        'address': customer.get('address', '')
                    }
            
            if not customers:
                self.customer_combo.addItem("No customers found")
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customers: {str(e)}")

    def selectLogo(self):
        """Select a logo image file"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Logo Image", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp);;All Files (*)", 
            options=options
        )
        
        if file_name:
            pixmap = QPixmap(file_name)
            
            if not pixmap.isNull():
                # Scale pixmap to fit preview
                scaled_pixmap = pixmap.scaled(100, 50, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.logo_preview.setPixmap(scaled_pixmap)
                
                # Store the original path
                self.company_logo = file_name
            else:
                QMessageBox.warning(self, "Invalid Image", "Could not load the selected image.")
    
    def addInvoiceItem(self):
        """Add a new invoice item"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add Invoice Item")
        dialog.setMinimumWidth(400)
        
        layout = QFormLayout()
        
        # Product selection dropdown
        product_combo = QComboBox()
        product_combo.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        
        # Load products into dropdown
        try:
            if self.mongo_adapter:
                products = self.mongo_adapter.get_products()
                self.product_data = {}
                
                product_combo.clear()
                product_combo.addItem("-- Select Product --", None)
                
                for product in products:
                    name = product.get('name', '')
                    if name:
                        display_text = f"{name} (Batch: {product.get('batch_number', 'N/A')})"
                        product_combo.addItem(display_text, product.get('id'))
                        self.product_data[product.get('id')] = product
        except Exception as e:
            print(f"Error loading products: {e}")
            product_combo.addItem("Error loading products", None)
        
        layout.addRow("Product:", product_combo)
        
        # Description field (auto-filled based on product selection)
        description = QLineEdit()
        description.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        layout.addRow("Description:", description)
        
        # Unit price field (auto-filled based on product selection)
        unit_price = QDoubleSpinBox()
        unit_price.setMinimum(0.01)
        unit_price.setMaximum(99999.99)
        unit_price.setPrefix("$")
        unit_price.setDecimals(2)
        unit_price.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        layout.addRow("Unit Price:", unit_price)
        
        # Quantity field
        quantity = QSpinBox()
        quantity.setMinimum(1)
        quantity.setMaximum(9999)
        quantity.setValue(1)
        quantity.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        layout.addRow("Quantity:", quantity)
        
        # Function to update fields when product is selected
        def on_product_changed():
            selected_product_id = product_combo.currentData()
            if selected_product_id and hasattr(self, 'product_data'):
                product_info = self.product_data.get(selected_product_id, {})
                
                # Auto-fill description
                product_description = product_info.get('description', '')
                if not product_description:
                    product_description = f"{product_info.get('name', '')} - Batch: {product_info.get('batch_number', 'N/A')}"
                description.setText(product_description)
                
                # Auto-fill unit price
                product_price = float(product_info.get('unit_price', 0))
                unit_price.setValue(product_price)
        
        # Connect product selection change
        product_combo.currentIndexChanged.connect(on_product_changed)
        
        # Buttons
        buttons = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(dialog.accept)
        add_btn.setStyleSheet("""
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
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons.addWidget(add_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addRow("", buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # Validate selection
            selected_product_id = product_combo.currentData()
            if not selected_product_id:
                QMessageBox.warning(self, "No Product Selected", "Please select a product from the dropdown.")
                return
            
            # Get product info
            product_info = self.product_data.get(selected_product_id, {})
            product_name = product_info.get('name', 'Unknown Product')
            
            # Add item to table
            item = {
                'product': product_name,
                'description': description.text(),
                'quantity': quantity.value(),
                'unit_price': unit_price.value(),
                'total': quantity.value() * unit_price.value(),
                'product_id': selected_product_id,
                'batch_number': product_info.get('batch_number', ''),
                'expiry_date': product_info.get('expiry_date', '')
            }
            
            self.addItemToTable(item)
            self.updateTotals()

    def addFromTransactions(self):
        """Add items from transactions in the database using MongoDB"""
        dialog = QDialog(self)
        dialog.setWindowTitle("Add from Transactions")
        dialog.setMinimumSize(800, 500)
        
        layout = QVBoxLayout()
        
        # Filter options
        filter_layout = QHBoxLayout()
        
        # Date range
        filter_layout.addWidget(QLabel("Date Range:"))
        
        from_date = QDateEdit()
        from_date.setDate(QDate.currentDate().addDays(-30))
        from_date.setCalendarPopup(True)
        filter_layout.addWidget(from_date)
        
        filter_layout.addWidget(QLabel("to"))
        
        to_date = QDateEdit()
        to_date.setDate(QDate.currentDate())
        to_date.setCalendarPopup(True)
        filter_layout.addWidget(to_date)
        
        # Customer filter (get current customer selection)
        customer_name = self.customer_combo.currentText()
        
        # Search button
        search_btn = QPushButton("Search")
        search_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 5px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        filter_layout.addWidget(search_btn)
        
        layout.addLayout(filter_layout)
        
        # Transactions table
        transactions_table = QTableWidget()
        transactions_table.setColumnCount(7)
        transactions_table.setHorizontalHeaderLabels([
            "ID", "Date", "Product", "Quantity", "Unit Price", "Total", "Select"
        ])
        transactions_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        transactions_table.setSelectionBehavior(QTableWidget.SelectRows)
        
        layout.addWidget(transactions_table)
        
        # Buttons
        buttons_layout = QHBoxLayout()
        
        add_selected_btn = QPushButton("Add Selected Items")
        add_selected_btn.clicked.connect(dialog.accept)
        add_selected_btn.setStyleSheet("""
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
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(add_selected_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        dialog.setLayout(layout)
        
        # Store selected items
        selected_items = []
        
        # Function to load transactions using MongoDB
        def load_transactions():
            try:
                # Validate MongoDB connection
                if not self.mongo_adapter:
                    QMessageBox.warning(dialog, "Database Error", "MongoDB connection not available")
                    return
                
                # Get customer ID
                customer_info = self.customer_data.get(customer_name, {})
                customer_id = customer_info.get('id')
                
                if not customer_id:
                    QMessageBox.warning(dialog, "Error", "Please select a customer first.")
                    return
                
                # Get all entries and products from MongoDB
                entries = self.mongo_adapter.get_entries()
                products = self.mongo_adapter.get_products()
                
                # Create product lookup
                product_lookup = {str(product.get('id')): product for product in products}
                
                # Filter entries for this customer and date range
                from_date_str = from_date.date().toString("yyyy-MM-dd")
                to_date_str = to_date.date().toString("yyyy-MM-dd")
                
                filtered_transactions = []
                for entry in entries:
                    entry_customer_id = str(entry.get('customer_id', ''))
                    entry_date = entry.get('date', '')
                    is_credit = entry.get('is_credit', True)
                    
                    # Filter by customer, date range, and debit entries (invoiceable)
                    if (entry_customer_id == customer_id and 
                        from_date_str <= entry_date <= to_date_str and 
                        not is_credit):  # Debit entries are invoiceable
                        
                        product_id = str(entry.get('product_id', ''))
                        product_info = product_lookup.get(product_id, {})
                        
                        filtered_transactions.append({
                            'id': entry.get('id', ''),
                            'date': entry_date,
                            'product_name': product_info.get('name', 'Unknown Product'),
                            'quantity': entry.get('quantity', 0),
                            'unit_price': entry.get('unit_price', 0),
                            'total': float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                        })
                
                # Sort by date (newest first)
                filtered_transactions.sort(key=lambda x: x['date'], reverse=True)
                
                # Update table
                transactions_table.setRowCount(len(filtered_transactions))
                
                for row, transaction in enumerate(filtered_transactions):
                    transactions_table.setItem(row, 0, QTableWidgetItem(str(transaction['id'])))
                    transactions_table.setItem(row, 1, QTableWidgetItem(transaction['date']))
                    transactions_table.setItem(row, 2, QTableWidgetItem(transaction['product_name']))
                    transactions_table.setItem(row, 3, QTableWidgetItem(str(transaction['quantity'])))
                    transactions_table.setItem(row, 4, QTableWidgetItem(f"${transaction['unit_price']:.2f}"))
                    transactions_table.setItem(row, 5, QTableWidgetItem(f"${transaction['total']:.2f}"))
                    
                    # Add checkbox for selection
                    check_box = QTableWidgetItem()
                    check_box.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    check_box.setCheckState(Qt.Unchecked)
                    transactions_table.setItem(row, 6, check_box)
                
                if not filtered_transactions:
                    QMessageBox.information(dialog, "No Data", "No transactions found for the selected criteria.")
                
            except Exception as e:
                QMessageBox.critical(dialog, "Database Error", f"Failed to load transactions: {str(e)}")
        
        # Connect search button
        search_btn.clicked.connect(load_transactions)
        
        # Initial load
        load_transactions()
        
        if dialog.exec_() == QDialog.Accepted:
            # Get selected items
            for row in range(transactions_table.rowCount()):
                if transactions_table.item(row, 6) and transactions_table.item(row, 6).checkState() == Qt.Checked:
                    product = transactions_table.item(row, 2).text()
                    quantity = int(float(transactions_table.item(row, 3).text()))
                    unit_price = float(transactions_table.item(row, 4).text().replace('$', ''))
                    
                    item = {
                        'product': product,
                        'description': f"Transaction from {transactions_table.item(row, 1).text()}",
                        'quantity': quantity,
                        'unit_price': unit_price,
                        'total': quantity * unit_price
                    }
                    
                    selected_items.append(item)
            
            # Add selected items to invoice
            for item in selected_items:
                self.addItemToTable(item)
            
            self.updateTotals()
    
    def addItemToTable(self, item):
        """Add an item to the invoice items table"""
        row = self.items_table.rowCount()
        self.items_table.insertRow(row)
        
        self.items_table.setItem(row, 0, QTableWidgetItem(item['product']))
        self.items_table.setItem(row, 1, QTableWidgetItem(item['description']))
        self.items_table.setItem(row, 2, QTableWidgetItem(str(item['quantity'])))
        self.items_table.setItem(row, 3, QTableWidgetItem(f"${item['unit_price']:.2f}"))
        self.items_table.setItem(row, 4, QTableWidgetItem(f"${item['total']:.2f}"))
        
        # Add remove button
        remove_btn = QPushButton("Remove")
        remove_btn.clicked.connect(lambda: self.removeItem(row))
        self.items_table.setCellWidget(row, 5, remove_btn)
        
        # Store item data
        self.invoice_items.append(item)
    
    def removeItem(self, row):
        """Remove an item from the invoice"""
        self.items_table.removeRow(row)
        self.invoice_items.pop(row)
        self.updateTotals()
    
    def clearItems(self):
        """Clear all invoice items"""
        reply = QMessageBox.question(
            self, "Confirm Clear",
            "Are you sure you want to clear all invoice items?",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.items_table.setRowCount(0)
            self.invoice_items = []
            self.updateTotals()
    
    def updateTotals(self):
        """Update the invoice totals"""
        subtotal = sum(item['total'] for item in self.invoice_items)
        tax_rate = self.tax_rate.value() / 100
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        self.subtotal_label.setText(f"${subtotal:.2f}")
        self.tax_amount_label.setText(f"${tax_amount:.2f}")
        self.total_label.setText(f"${total:.2f}")
    
    def generateInvoiceHtml(self):
        """Generate HTML for the invoice that matches the pharmaceutical format"""
        # Get customer info
        customer_name = self.customer_combo.currentText()
        customer_info = self.customer_data.get(customer_name, {})
        customer_address = customer_info.get('address', '')
        customer_contact = customer_info.get('contact', '')
        
        # Calculate totals
        subtotal = sum(item['total'] for item in self.invoice_items)
        tax_rate = self.tax_rate.value() / 100
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        # Convert amount to words (simple implementation)
        def amount_to_words(amount):
            ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
            teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
            tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
            
            try:
                amount = int(amount)
                if amount == 0:
                    return "zero rupees"
                
                result = ""
                if amount >= 1000:
                    thousands = amount // 1000
                    if thousands > 0:
                        result += f"{ones[thousands]} thousand "
                        amount %= 1000
                
                if amount >= 100:
                    hundreds = amount // 100
                    if hundreds > 0:
                        result += f"{ones[hundreds]} hundred "
                        amount %= 100
                
                if amount >= 20:
                    ten_digit = amount // 10
                    ones_digit = amount % 10
                    result += f"{tens[ten_digit]} "
                    if ones_digit > 0:
                        result += f"{ones[ones_digit]} "
                elif amount >= 10:
                    result += f"{teens[amount - 10]} "
                elif amount > 0:
                    result += f"{ones[amount]} "
                
                return f"{result.strip()} rupees"
            except:
                return "amount not specified"
        
        # Logo handling
        logo_html = ""
        if self.company_logo:
            try:
                import base64
                with open(self.company_logo, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode()
                    file_ext = self.company_logo.split('.')[-1].lower()
                    logo_html = f'<img src="data:image/{file_ext};base64,{img_data}" style="height: 50px; margin-bottom: 10px;" /><br>'
            except:
                logo_html = ""
        
        # Generate items table rows
        items_html = ""
        item_number = 1
        for item in self.invoice_items:
            # Get additional product details if available
            batch_info = ""
            if 'batch_number' in item and item['batch_number']:
                batch_info = f" (Batch: {item['batch_number']})"
            
            # Calculate discount (if any)
            discount_percent = 0  # Can be made configurable
            discount_amount = item['total'] * (discount_percent / 100)
            final_amount = item['total'] - discount_amount
            
            items_html += f"""
                <tr>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{item_number}</td>
                    <td style="border: 1px solid #666; padding: 8px;">{item['product']}{batch_info}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{item.get('product_id', 'N/A')}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{item['unit_price']:.0f}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{item['quantity']}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{item['unit_price']:.0f}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{discount_percent}%</td>
                    <td style="text-align: right; border: 1px solid #666; padding: 8px;">{final_amount:.0f}</td>
                </tr>
            """
            item_number += 1
        
        # Get transport/delivery info (can be made configurable)
        transport_name = "Standard Delivery"
        delivery_date = self.due_date.date().toString("dd-MM-yy")
        delivery_location = customer_address.split('\n')[0] if customer_address else "Customer Location"
        
        # Generate professional pharmaceutical invoice HTML
        html = f"""
       <!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Bill/Cash Memo</title>
    <style>
        body { 
            font-family: Arial, sans-serif; 
            margin: 0; 
            padding: 10px;
            font-size: 12px;
        }
        .invoice-container {
            border: 2px solid #000;
            padding: 0;
            max-width: 210mm;
            margin: 0 auto;
        }
        .header {
            background-color: #8A2BE2;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
            font-size: 16px;
        }
        .company-header {
            background-color: #8A2BE2;
            color: white;
            padding: 15px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .company-logo {
            font-size: 24px;
            font-weight: bold;
        }
        .company-contact {
            text-align: right;
            font-size: 11px;
        }
        .bill-details {
            display: flex;
            border-bottom: 2px solid #000;
        }
        .bill-to {
            flex: 1;
            padding: 15px;
            border-right: 1px solid #000;
        }
        .transport-details {
            flex: 1;
            padding: 15px;
            border-right: 1px solid #000;
        }
        .invoice-details {
            flex: 1;
            padding: 15px;
        }
        .items-header {
            background-color: #8A2BE2;
            color: white;
            padding: 8px;
            text-align: center;
            font-weight: bold;
        }
        .items-table {
            width: 100%;
            border-collapse: collapse;
            margin: 0;
        }
        .items-table th {
            background-color: #8A2BE2;
            color: white;
            padding: 8px;
            border: 1px solid #666;
            text-align: center;
            font-size: 11px;
        }
        .items-table td {
            padding: 8px;
            border: 1px solid #666;
            font-size: 11px;
        }
        .totals-section {
            display: flex;
            border-top: 1px solid #000;
        }
        .amounts-section {
            flex: 1;
            padding: 15px;
        }
        .amounts-header {
            background-color: #8A2BE2;
            color: white;
            padding: 5px;
            text-align: center;
            font-weight: bold;
            margin-bottom: 10px;
        }
        .amount-row {
            display: flex;
            justify-content: space-between;
            padding: 3px 0;
            border-bottom: 1px solid #ccc;
        }
        .amount-words {
            background-color: #8A2BE2;
            color: white;
            padding: 10px;
            text-align: center;
            font-weight: bold;
        }
        .terms-section {
            display: flex;
            border-top: 1px solid #000;
        }
        .terms {
            flex: 2;
            padding: 15px;
            font-size: 10px;
            border-right: 1px solid #000;
        }
        .signature-section {
            flex: 1;
            padding: 15px;
            text-align: center;
        }
        .bold { font-weight: bold; }
        .right-align { text-align: right; }
    </style>
</head>
<body>
    <div class="invoice-container">
        <!-- Header -->
        <div class="header">Bill/Cash Memo</div>
        
        <!-- Company Header -->
        <div class="company-header">
            <div class="company-logo">
                {logo_html}
                {self.company_name.text()}
            </div>
            <div class="company-contact">
                {customer_contact}<br>
                {self.company_address.toPlainText().replace(chr(10), '<br>')}
            </div>
        </div>
        
        <!-- Bill Details Section -->
        <div class="bill-details">
            <div class="bill-to">
                <div class="bold" style="background-color: #8A2BE2; color: white; padding: 5px; margin-bottom: 10px;">Bill To</div>
                <div class="bold">{customer_name}</div>
                <div style="margin-top: 10px;">{customer_address.replace(chr(10), '<br>')}</div>
            </div>
            
            <div class="transport-details">
                <div class="bold" style="background-color: #8A2BE2; color: white; padding: 5px; margin-bottom: 10px;">Transportation Details</div>
                <div><span class="bold">Transport Name:</span> {transport_name}</div>
                <div><span class="bold">Delivery Date:</span> {delivery_date}</div>
                <div><span class="bold">Delivery location:</span> {delivery_location}</div>
            </div>
            
            <div class="invoice-details">
                <div class="bold" style="background-color: #8A2BE2; color: white; padding: 5px; margin-bottom: 10px;">Invoice Details</div>
                <div><span class="bold">Invoice No.:</span> {self.invoice_number.text()}</div>
                <div><span class="bold">Date:</span> {self.invoice_date.date().toString("dd-MM-yy")}</div>
            </div>
        </div>
        
        <!-- Items Section -->
        <div class="items-header">
            <table class="items-table">
                <thead>
                    <tr>
                        <th style="width: 5%;">#</th>
                        <th style="width: 25%;">Item name</th>
                        <th style="width: 10%;">No.</th>
                        <th style="width: 10%;">MRP</th>
                        <th style="width: 10%;">Quantity</th>
                        <th style="width: 10%;">Rate</th>
                        <th style="width: 10%;">Discount</th>
                        <th style="width: 15%;">Amount</th>
                    </tr>
                </thead>
                <tbody>
                    {items_html}
                    <tr>
                        <td colspan="7" style="text-align: right; padding: 8px; border: 1px solid #666; font-weight: bold;">Total</td>
                        <td style="text-align: right; padding: 8px; border: 1px solid #666; font-weight: bold;">{subtotal:.0f}</td>
                    </tr>
                </tbody>
            </table>
        </div>
        
        <!-- Totals Section -->
        <div class="totals-section">
            <div class="amounts-section">
                <div class="amounts-header">Amounts</div>
                <div class="amount-row">
                    <span>Sub Total</span>
                    <span>{subtotal:.0f}</span>
                </div>
                <div class="amount-row">
                    <span>Total</span>
                    <span>{total:.0f}</span>
                </div>
                <div class="amount-row">
                    <span>Received</span>
                    <span>0.00</span>
                </div>
                <div class="amount-row bold">
                    <span>Balance</span>
                    <span>{total:.0f}</span>
                </div>
            </div>
        </div>
        
        <!-- Amount in Words -->
        <div class="amount-words">
            <div class="bold" style="margin-bottom: 5px;">Invoice Amount In Words</div>
            <div>{amount_to_words(total)}</div>
        </div>
        
        <!-- Terms and Signature -->
        <div class="terms-section">
            <div class="terms">
                <div class="bold" style="background-color: #8A2BE2; color: white; padding: 5px; margin-bottom: 10px;">Terms and Conditions</div>
                <div style="text-align: justify;">
                    {self.notes.toPlainText().replace(chr(10), '<br>')}
                    <br><br>
                    Form 2-A, as specified under Rules 19 and 30, pertains to the warranty 
                    provided under Section 23(1)(1) of the Drug Act 1976. This document, 
                    issued by {self.company_name.text()}, serves as an assurance of the quality and 
                    effectiveness of products. The warranty ensures that the drugs 
                    manufactured by {self.company_name.text()} comply with the prescribed standards and 
                    meet the necessary regulatory requirements. By utilizing Form 2-A, 
                    {self.company_name.text()} demonstrates its commitment to delivering safe and reliable 
                    pharmaceuticals to consumers. This form acts as a legal document, 
                    emphasizing {self.company_name.text()}'s responsibility and accountability in 
                    maintaining the highest standards in drug manufacturing and 
                    distribution.
                </div>
            </div>
            
            <div class="signature-section">
                <div style="margin-bottom: 20px;">For : {self.company_name.text()}</div>
                <div style="margin-top: 80px; border-top: 1px solid #000; padding-top: 10px;">
                    <div class="bold">Authorized Signatory</div>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
        """
        
        return html
    
    def previewInvoice(self):
        """Preview the invoice"""
        if not self.invoice_items:
            QMessageBox.warning(self, "No Items", "Please add at least one item to the invoice.")
            return
        
        invoice_html = self.generateInvoiceHtml()
        preview_dialog = InvoicePreviewDialog(invoice_html, self)
        preview_dialog.exec_()
    
    def saveAsPdf(self):
        """Save the invoice as a PDF file using reportlab"""
        if not self.invoice_items:
            QMessageBox.warning(self, "No Items", "Please add at least one item to the invoice.")
            return
        
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Invoice as PDF", f"{self.invoice_number.text()}.pdf",
            "PDF Files (*.pdf);;All Files (*)", options=options
        )
        
        if file_name:
            try:
                # Prepare invoice data for PDF generator
                invoice_data = self.prepareInvoiceData()
                
                # Generate PDF using reportlab
                pdf_generator = PDFGenerator()
                success = pdf_generator.generate_invoice_pdf(invoice_data, file_name)
                
                if success:
                    QMessageBox.information(
                        self, "PDF Saved",
                        f"Invoice saved as PDF:\n{file_name}"
                    )
                else:
                    QMessageBox.critical(
                        self, "Error",
                        "Failed to generate PDF. Please try again."
                    )
                    
            except ImportError:
                QMessageBox.critical(
                    self, "Missing Library",
                    "ReportLab library is required for PDF generation.\n"
                    "Please install it using: pip install reportlab"
                )
            except Exception as e:
                QMessageBox.critical(
                    self, "Error",
                    f"Failed to save PDF: {str(e)}"
                )
    
    def prepareInvoiceData(self):
        """Prepare invoice data for PDF generation"""
        # Get customer info
        customer_name = self.customer_combo.currentText()
        customer_info = self.customer_data.get(customer_name, {})
        customer_address = customer_info.get('address', '')
        customer_contact = customer_info.get('contact', '')
        
        # Calculate totals
        subtotal = sum(item['total'] for item in self.invoice_items)
        tax_rate = self.tax_rate.value() / 100
        tax_amount = subtotal * tax_rate
        total = subtotal + tax_amount
        
        # Prepare items data
        items_data = []
        for item in self.invoice_items:
            items_data.append({
                'product_name': item['product'],
                'batch_number': item.get('batch_number', 'N/A'),
                'product_id': item.get('product_id', 'N/A'),
                'quantity': item['quantity'],
                'unit_price': item['unit_price'],
                'discount': 0,  # Can be made configurable
                'amount': item['total']
            })
        
        return {
            'company_name': self.company_name.text(),
            'company_logo': self.company_logo,
            'customer_info': {
                'name': customer_name,
                'address': customer_address,
                'contact': customer_contact
            },
            'transport_info': {
                'transport_name': 'Standard Delivery',
                'delivery_date': self.due_date.date().toString("dd-MM-yy"),
                'delivery_location': customer_address.split('\n')[0] if customer_address else 'Customer Location'
            },
            'invoice_details': {
                'invoice_number': self.invoice_number.text(),
                'invoice_date': self.invoice_date.date().toString("dd-MM-yy")
            },
            'items': items_data,
            'terms': self.notes.toPlainText(),
            'total_amount': total
        }

    def printInvoice(self):
        """Print the invoice using reportlab PDF"""
        if not self.invoice_items:
            QMessageBox.warning(self, "No Items", "Please add at least one item to the invoice.")
            return
        
        try:
            # Create temporary PDF file
            temp_dir = tempfile.gettempdir()
            temp_pdf = os.path.join(temp_dir, f"temp_invoice_{self.invoice_number.text()}.pdf")
            
            # Prepare invoice data
            invoice_data = self.prepareInvoiceData()
            
            # Generate PDF
            pdf_generator = PDFGenerator()
            success = pdf_generator.generate_invoice_pdf(invoice_data, temp_pdf)
            
            if success:
                # Show print dialog using QPrinter
                from PyQt5.QtPrintSupport import QPrintDialog
                from PyQt5.QtGui import QTextDocument
                
                # For now, we'll open the PDF file for printing
                # In a real implementation, you might want to use a PDF viewer
                import subprocess
                if sys.platform == "win32":
                    os.startfile(temp_pdf)
                elif sys.platform == "darwin":
                    subprocess.call(["open", temp_pdf])
                else:
                    subprocess.call(["xdg-open", temp_pdf])
                    
                QMessageBox.information(
                    self, "Print Ready",
                    f"PDF generated and opened for printing:\n{temp_pdf}"
                )
            else:
                QMessageBox.critical(
                    self, "Error",
                    "Failed to generate PDF for printing."
                )
                
        except ImportError:
            QMessageBox.critical(
                self, "Missing Library",
                "ReportLab library is required for PDF generation.\n"
                "Please install it using: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(
                self, "Print Error",
                f"Failed to print invoice: {str(e)}"
            )