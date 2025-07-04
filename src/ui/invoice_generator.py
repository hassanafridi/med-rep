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
from database.db import Database

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
    def __init__(self, current_user):
        super().__init__()
        self.db = Database()
        self.current_user = current_user
        self.company_logo = None
        self.invoice_items = []
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Invoice header information
        header_group = QGroupBox("Invoice Information")
        header_layout = QFormLayout()
        
        # Invoice number
        self.invoice_number = QLineEdit()
        self.invoice_number.setText(self.generateInvoiceNumber())
        header_layout.addRow("Invoice Number:", self.invoice_number)
        
        # Date
        self.invoice_date = QDateEdit()
        self.invoice_date.setDate(QDate.currentDate())
        self.invoice_date.setCalendarPopup(True)
        header_layout.addRow("Invoice Date:", self.invoice_date)
        
        # Due date
        self.due_date = QDateEdit()
        self.due_date.setDate(QDate.currentDate().addDays(30))
        self.due_date.setCalendarPopup(True)
        header_layout.addRow("Due Date:", self.due_date)
        
        # Customer selection
        self.customer_combo = QComboBox()
        self.loadCustomers()
        header_layout.addRow("Customer:", self.customer_combo)
        
        # Your company info
        self.company_name = QLineEdit("Your Company Name")
        header_layout.addRow("Your Company:", self.company_name)
        
        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(80)
        self.company_address.setText("123 Business St\nAnytown, USA 12345\nPhone: (555) 123-4567\nEmail: info@yourcompany.com")
        header_layout.addRow("Your Address:", self.company_address)
        
        # Logo selection
        logo_layout = QHBoxLayout()
        self.logo_preview = QLabel("No logo")
        self.logo_preview.setFixedSize(100, 50)
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setStyleSheet("border: 1px solid #aaa;")
        
        self.select_logo_btn = QPushButton("Select Logo")
        self.select_logo_btn.clicked.connect(self.selectLogo)
        
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
        
        items_layout.addWidget(self.items_table)
        
        # Buttons for managing items
        buttons_layout = QHBoxLayout()
        
        self.add_item_btn = QPushButton("Add Item")
        self.add_item_btn.clicked.connect(self.addInvoiceItem)
        
        self.add_from_db_btn = QPushButton("Add from Transactions")
        self.add_from_db_btn.clicked.connect(self.addFromTransactions)
        
        self.clear_items_btn = QPushButton("Clear All Items")
        self.clear_items_btn.clicked.connect(self.clearItems)
        
        buttons_layout.addWidget(self.add_item_btn)
        buttons_layout.addWidget(self.add_from_db_btn)
        buttons_layout.addWidget(self.clear_items_btn)
        
        items_layout.addLayout(buttons_layout)
        
        # Totals section
        totals_layout = QFormLayout()
        
        self.subtotal_label = QLabel("$0.00")
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setValue(0)
        self.tax_rate.setSuffix("%")
        self.tax_rate.valueChanged.connect(self.updateTotals)
        totals_layout.addRow("Tax Rate:", self.tax_rate)
        
        self.tax_amount_label = QLabel("$0.00")
        totals_layout.addRow("Tax Amount:", self.tax_amount_label)
        
        self.total_label = QLabel("$0.00")
        self.total_label.setStyleSheet("font-weight: bold; font-size: 14px;")
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
        
        notes_layout.addWidget(self.notes)
        notes_group.setLayout(notes_layout)
        main_layout.addWidget(notes_group)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.preview_btn = QPushButton("Preview Invoice")
        self.preview_btn.clicked.connect(self.previewInvoice)
        
        self.save_pdf_btn = QPushButton("Save as PDF")
        self.save_pdf_btn.clicked.connect(self.saveAsPdf)
        
        self.print_btn = QPushButton("Print")
        self.print_btn.clicked.connect(self.printInvoice)
        
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
        """Load customers into combo box"""
        try:
            self.db.connect()
            
            # Get all customers
            self.db.cursor.execute('SELECT id, name, contact, address FROM customers ORDER BY name')
            customers = self.db.cursor.fetchall()
            
            # Store customer data
            self.customer_data = {}
            
            # Add to combo box
            self.customer_combo.clear()
            for customer_id, name, contact, address in customers:
                self.customer_combo.addItem(name)
                self.customer_data[name] = {
                    'id': customer_id,
                    'contact': contact,
                    'address': address
                }
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customers: {str(e)}")
        finally:
            self.db.close()
    
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
        
        # Fields
        product_name = QLineEdit()
        layout.addRow("Product:", product_name)
        
        description = QLineEdit()
        layout.addRow("Description:", description)
        
        quantity = QSpinBox()
        quantity.setMinimum(1)
        quantity.setMaximum(9999)
        layout.addRow("Quantity:", quantity)
        
        unit_price = QDoubleSpinBox()
        unit_price.setMinimum(0.01)
        unit_price.setMaximum(99999.99)
        unit_price.setPrefix("$")
        unit_price.setDecimals(2)
        layout.addRow("Unit Price:", unit_price)
        
        # Buttons
        buttons = QHBoxLayout()
        add_btn = QPushButton("Add")
        add_btn.clicked.connect(dialog.accept)
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons.addWidget(add_btn)
        buttons.addWidget(cancel_btn)
        
        layout.addRow("", buttons)
        
        dialog.setLayout(layout)
        
        if dialog.exec_() == QDialog.Accepted:
            # Add item to table
            item = {
                'product': product_name.text(),
                'description': description.text(),
                'quantity': quantity.value(),
                'unit_price': unit_price.value(),
                'total': quantity.value() * unit_price.value()
            }
            
            self.addItemToTable(item)
            self.updateTotals()
    
    def addFromTransactions(self):
        """Add items from transactions in the database"""
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
        
        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(dialog.reject)
        
        buttons_layout.addWidget(add_selected_btn)
        buttons_layout.addWidget(cancel_btn)
        
        layout.addLayout(buttons_layout)
        
        dialog.setLayout(layout)
        
        # Store selected items
        selected_items = []
        
        # Function to load transactions
        def load_transactions():
            try:
                self.db.connect()
                
                # Get customer ID
                customer_id = self.customer_data.get(customer_name, {}).get('id')
                
                if not customer_id:
                    QMessageBox.warning(dialog, "Error", "Please select a customer first.")
                    return
                
                # Get transactions for this customer
                query = """
                    SELECT 
                        e.id, e.date, p.name, e.quantity, e.unit_price,
                        (e.quantity * e.unit_price) as total
                    FROM entries e
                    JOIN products p ON e.product_id = p.id
                    WHERE e.customer_id = ? AND e.date BETWEEN ? AND ? AND e.is_credit = 0
                    ORDER BY e.date DESC
                """
                
                from_date_str = from_date.date().toString("yyyy-MM-dd")
                to_date_str = to_date.date().toString("yyyy-MM-dd")
                
                self.db.cursor.execute(query, (customer_id, from_date_str, to_date_str))
                transactions = self.db.cursor.fetchall()
                
                # Update table
                transactions_table.setRowCount(len(transactions))
                
                for row, (id, date, product, quantity, unit_price, total) in enumerate(transactions):
                    transactions_table.setItem(row, 0, QTableWidgetItem(str(id)))
                    transactions_table.setItem(row, 1, QTableWidgetItem(date))
                    transactions_table.setItem(row, 2, QTableWidgetItem(product))
                    transactions_table.setItem(row, 3, QTableWidgetItem(str(quantity)))
                    transactions_table.setItem(row, 4, QTableWidgetItem(f"${unit_price:.2f}"))
                    transactions_table.setItem(row, 5, QTableWidgetItem(f"${total:.2f}"))
                    
                    # Add checkbox for selection
                    check_box = QTableWidgetItem()
                    check_box.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    check_box.setCheckState(Qt.Unchecked)
                    transactions_table.setItem(row, 6, check_box)
                
            except Exception as e:
                QMessageBox.critical(dialog, "Database Error", f"Failed to load transactions: {str(e)}")
            finally:
                self.db.close()
        
        # Connect search button
        search_btn.clicked.connect(load_transactions)
        
        # Initial load
        load_transactions()
        
        if dialog.exec_() == QDialog.Accepted:
            # Get selected items
            for row in range(transactions_table.rowCount()):
                if transactions_table.item(row, 6).checkState() == Qt.Checked:
                    product = transactions_table.item(row, 2).text()
                    quantity = int(transactions_table.item(row, 3).text())
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
        """Generate HTML for the invoice"""
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
        
        # Generate HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <title>Invoice</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .invoice-header {{ display: flex; justify-content: space-between; margin-bottom: 20px; }}
                .company-info {{ flex: 1; }}
                .invoice-info {{ flex: 1; text-align: right; }}
                .invoice-title {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
                .customer-info {{ margin-bottom: 20px; }}
                table {{ width: 100%; border-collapse: collapse; margin-bottom: 20px; }}
                th, td {{ padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }}
                th {{ background-color: #f2f2f2; }}
                .text-right {{ text-align: right; }}
                .totals {{ margin-left: auto; width: 300px; }}
                .total-row {{ font-weight: bold; }}
                .notes {{ margin-top: 30px; }}
            </style>
        </head>
        <body>
            <div class="invoice-header">
                <div class="company-info">
                    <div class="invoice-title">{self.company_name.text()}</div>
                    <div>{self.company_address.toPlainText().replace('\n', '<br>')}</div>
                </div>
                <div class="invoice-info">
                    <div class="invoice-title">INVOICE</div>
                    <div><strong>Invoice #:</strong> {self.invoice_number.text()}</div>
                    <div><strong>Date:</strong> {self.invoice_date.date().toString("yyyy-MM-dd")}</div>
                    <div><strong>Due Date:</strong> {self.due_date.date().toString("yyyy-MM-dd")}</div>
                </div>
            </div>
            
            <div class="customer-info">
                <div><strong>Bill To:</strong></div>
                <div>{customer_name}</div>
                <div>{customer_address.replace('\n', '<br>')}</div>
                <div>{customer_contact}</div>
            </div>
            
            <table>
                <thead>
                    <tr>
                        <th>Item</th>
                        <th>Description</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th class="text-right">Total</th>
                    </tr>
                </thead>
                <tbody>
        """
        
        for item in self.invoice_items:
            html += f"""
                    <tr>
                        <td>{item['product']}</td>
                        <td>{item['description']}</td>
                        <td>{item['quantity']}</td>
                        <td>${item['unit_price']:.2f}</td>
                        <td class="text-right">${item['total']:.2f}</td>
                    </tr>
            """
        
        html += f"""
                </tbody>
            </table>
            
            <div class="totals">
                <table>
                    <tr>
                        <td>Subtotal</td>
                        <td class="text-right">${subtotal:.2f}</td>
                    </tr>
                    <tr>
                        <td>Tax ({self.tax_rate.value()}%)</td>
                        <td class="text-right">${tax_amount:.2f}</td>
                    </tr>
                    <tr class="total-row">
                        <td>Total</td>
                        <td class="text-right">${total:.2f}</td>
                    </tr>
                </table>
            </div>
            
            <div class="notes">
                <div><strong>Notes:</strong></div>
                <div>{self.notes.toPlainText().replace('\n', '<br>')}</div>
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
        """Save the invoice as a PDF file"""
        if not self.invoice_items:
            QMessageBox.warning(self, "No Items", "Please add at least one item to the invoice.")
            return
        
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Invoice as PDF", f"{self.invoice_number.text()}.pdf",
            "PDF Files (*.pdf);;All Files (*)", options=options
        )
        
        if file_name:
            # Generate HTML
            invoice_html = self.generateInvoiceHtml()
            
            # Create document
            doc = QTextDocument()
            doc.setHtml(invoice_html)
            
            # Create printer
            printer = QPrinter(QPrinter.HighResolution)
            printer.setOutputFormat(QPrinter.PdfFormat)
            printer.setOutputFileName(file_name)
            printer.setPageSize(QPrinter.A4)
            
            # Print document to PDF
            doc.print_(printer)
            
            QMessageBox.information(
                self, "PDF Saved",
                f"Invoice saved as PDF:\n{file_name}"
            )
    
    def printInvoice(self):
        """Print the invoice"""
        if not self.invoice_items:
            QMessageBox.warning(self, "No Items", "Please add at least one item to the invoice.")
            return
        
        # Generate HTML
        invoice_html = self.generateInvoiceHtml()
        
        # Create document
        doc = QTextDocument()
        doc.setHtml(invoice_html)
        
        # Show print dialog
        print_dialog = QPrintPreviewDialog()
        print_dialog.paintRequested.connect(lambda printer: doc.print_(printer))
        print_dialog.exec_()