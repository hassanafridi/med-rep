"""
Enhanced New Entry Tab for MedRep with Multi-Product Support
Automatically generates Tru-Pharma style invoice when saving entries
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QPushButton, QGroupBox, QFormLayout,
                             QMessageBox, QLineEdit, QTableWidget, QTableWidgetItem,
                             QDialog, QDialogButtonBox, QHeaderView)
from PyQt5.QtCore import QDate, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor
from datetime import datetime
import os
import sys
import json

# Add the auto invoice generator
from src.utils.auto_invoice_generator import AutoInvoiceGenerator

# Import your existing database module
from src.database.db import Database
from src.database.audit_trail import AuditTrail


class ProductItemDialog(QDialog):
    """Dialog for adding/editing product items"""
    
    def __init__(self, parent=None, product_data=None, item_data=None):
        super().__init__(parent)
        self.setWindowTitle("Add/Edit Product Item")
        self.setModal(True)
        self.setMinimumWidth(450)
        self.product_data = product_data or {}
        
        layout = QFormLayout()
        
        # Product selection
        self.product_combo = QComboBox()
        self.product_combo.addItem("-- Select Product --")
        
        # Populate products
        for display_name, data in self.product_data.items():
            self.product_combo.addItem(display_name)
        
        self.product_combo.currentIndexChanged.connect(self.on_product_changed)
        layout.addRow("Product:", self.product_combo)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(9999)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self.calculate_amount)
        layout.addRow("Quantity:", self.quantity_spin)
        
        # Unit price
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setMinimum(0.0)
        self.unit_price_spin.setMaximum(999999.99)
        self.unit_price_spin.setDecimals(2)
        self.unit_price_spin.valueChanged.connect(self.calculate_amount)
        layout.addRow("Unit Price:", self.unit_price_spin)
        
        # Discount
        self.discount_spin = QSpinBox()
        self.discount_spin.setMinimum(0)
        self.discount_spin.setMaximum(100)
        self.discount_spin.setSuffix("%")
        self.discount_spin.valueChanged.connect(self.calculate_amount)
        layout.addRow("Discount:", self.discount_spin)
        
        # Amount (read-only)
        self.amount_label = QLabel("Rs 0.00")
        self.amount_label.setStyleSheet("font-weight: bold; color: #4B0082;")
        layout.addRow("Amount:", self.amount_label)
        
        # Pre-fill if editing
        if item_data:
            # Find and select the product
            for i in range(self.product_combo.count()):
                if self.product_combo.itemText(i) == item_data.get('display_name'):
                    self.product_combo.setCurrentIndex(i)
                    break
            self.quantity_spin.setValue(item_data.get('quantity', 1))
            self.unit_price_spin.setValue(item_data.get('unit_price', 0))
            self.discount_spin.setValue(item_data.get('discount', 0))
        
        # Buttons
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)
        
        self.setLayout(layout)
        self.calculate_amount()
    
    def on_product_changed(self, index):
        """Handle product selection change"""
        if index > 0:
            product_name = self.product_combo.currentText()
            if product_name in self.product_data:
                product_info = self.product_data[product_name]
                self.unit_price_spin.setValue(product_info.get('unit_price', 0))
                
                # Check if expired and show warning
                expiry_date = product_info.get('expiry_date', '')
                if expiry_date:
                    try:
                        exp_date = datetime.strptime(expiry_date, '%Y-%m-%d')
                        if exp_date < datetime.now():
                            self.product_combo.setStyleSheet("color: red; font-weight: bold;")
                            QMessageBox.warning(self, "Expired Product", 
                                              f"Warning: This product expired on {expiry_date}")
                        else:
                            self.product_combo.setStyleSheet("")
                    except:
                        pass
    
    def calculate_amount(self):
        """Calculate and display the amount"""
        quantity = self.quantity_spin.value()
        unit_price = self.unit_price_spin.value()
        discount = self.discount_spin.value()
        
        amount = quantity * unit_price
        if discount > 0:
            amount = amount * (1 - discount / 100)
        
        self.amount_label.setText(f"Rs {amount:.2f}")
    
    def get_item_data(self):
        """Get the item data"""
        if self.product_combo.currentIndex() == 0:
            return None
        
        product_name = self.product_combo.currentText()
        product_info = self.product_data.get(product_name, {})
        
        quantity = self.quantity_spin.value()
        unit_price = self.unit_price_spin.value()
        discount = self.discount_spin.value()
        
        amount = quantity * unit_price
        if discount > 0:
            amount = amount * (1 - discount / 100)
        
        return {
            'display_name': product_name,
            'product_id': product_info.get('id'),
            'product_name': product_info.get('name'),
            'batch_number': product_info.get('batch_number'),
            'expiry_date': product_info.get('expiry_date'),
            'quantity': quantity,
            'unit_price': unit_price,
            'discount': discount,
            'amount': round(amount, 2)
        }


class NewEntryTab(QWidget):
    """
    Enhanced New Entry tab with multi-product support and automatic invoicing
    """
    
    # Signal emitted when entry is saved with invoice path
    entry_saved = pyqtSignal(str)  # invoice_path
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.invoice_generator = AutoInvoiceGenerator()
        self.customer_data = {}
        self.product_data = {}
        self.product_items = []  # List of products in current entry
        self.initUI()
        self.loadCustomersAndProducts()
    
    def initUI(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("New Entry")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title)
        
        # Customer and date section
        customer_group = QGroupBox("Customer Information")
        customer_layout = QFormLayout()
        
        # Date picker
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        customer_layout.addRow("Date:", self.date_edit)
        
        # Customer dropdown
        self.customer_combo = QComboBox()
        customer_layout.addRow("Customer:", self.customer_combo)
        
        # Transaction type
        self.is_credit = QCheckBox("Credit Entry")
        self.is_credit.setToolTip("Check for Credit (money in), uncheck for Debit (money out)")
        self.is_credit.setChecked(True)  # Default to credit
        customer_layout.addRow("Entry Type:", self.is_credit)
        
        # Notes field
        self.notes_edit = QLineEdit()
        customer_layout.addRow("Notes:", self.notes_edit)
        
        customer_group.setLayout(customer_layout)
        main_layout.addWidget(customer_group)
        
        # Products section
        products_group = QGroupBox("Products")
        products_layout = QVBoxLayout()
        
        # Products toolbar
        products_toolbar = QHBoxLayout()
        self.add_product_btn = QPushButton("Add Product")
        self.add_product_btn.clicked.connect(self.add_product_item)
        self.edit_product_btn = QPushButton("Edit Product")
        self.edit_product_btn.clicked.connect(self.edit_product_item)
        self.delete_product_btn = QPushButton("Delete Product")
        self.delete_product_btn.clicked.connect(self.delete_product_item)
        
        products_toolbar.addWidget(self.add_product_btn)
        products_toolbar.addWidget(self.edit_product_btn)
        products_toolbar.addWidget(self.delete_product_btn)
        products_toolbar.addStretch()
        products_layout.addLayout(products_toolbar)
        
        # Products table
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(7)
        self.products_table.setHorizontalHeaderLabels([
            'Product', 'Batch', 'Expiry', 'Quantity', 'Unit Price', 'Discount', 'Amount'
        ])
        self.products_table.horizontalHeader().setStretchLastSection(True)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        products_layout.addWidget(self.products_table)
        
        # Total amount
        total_layout = QHBoxLayout()
        total_layout.addStretch()
        self.total_label = QLabel("Total: Rs 0.00")
        self.total_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4B0082;")
        total_layout.addWidget(self.total_label)
        products_layout.addLayout(total_layout)
        
        products_group.setLayout(products_layout)
        main_layout.addWidget(products_group)
        
        # Invoice options group
        invoice_group = QGroupBox("Invoice Options")
        invoice_layout = QFormLayout()
        
        # Auto-generate invoice checkbox
        self.auto_invoice_check = QCheckBox("Auto-generate Invoice")
        self.auto_invoice_check.setChecked(True)
        self.auto_invoice_check.setToolTip("Automatically generate PDF invoice when saving entry")
        invoice_layout.addRow("", self.auto_invoice_check)
        
        # Transport name
        self.transport_name_edit = QLineEdit()
        self.transport_name_edit.setPlaceholderText("e.g., Jawad Aslam")
        invoice_layout.addRow("Transport Name:", self.transport_name_edit)
        
        # Delivery date
        self.delivery_date_edit = QDateEdit()
        self.delivery_date_edit.setCalendarPopup(True)
        self.delivery_date_edit.setDate(QDate.currentDate())
        invoice_layout.addRow("Delivery Date:", self.delivery_date_edit)
        
        # Delivery location
        self.delivery_location_edit = QLineEdit()
        self.delivery_location_edit.setPlaceholderText("e.g., adda johal")
        invoice_layout.addRow("Delivery Location:", self.delivery_location_edit)
        
        invoice_group.setLayout(invoice_layout)
        main_layout.addWidget(invoice_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Entry & Generate Invoice")
        self.save_button.clicked.connect(self.saveEntry)
        self.save_button.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clearForm)
        
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.loadCustomersAndProducts)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: green; font-weight: bold;")
        main_layout.addWidget(self.status_label)
        
        self.setLayout(main_layout)
    
    def loadCustomersAndProducts(self):
        """Load customers and products from database"""
        try:
            self.db.connect()
            
            # Load customers
            self.customer_data = {}
            self.customer_combo.clear()
            self.customer_combo.addItem("-- Select Customer --")
            
            self.db.cursor.execute('SELECT id, name FROM customers ORDER BY name')
            customers = self.db.cursor.fetchall()
            
            for customer_id, name in customers:
                self.customer_combo.addItem(name)
                self.customer_data[name] = customer_id
            
            # Load products
            self.product_data = {}
            
            self.db.cursor.execute('''
                SELECT id, name, batch_number, expiry_date, unit_price 
                FROM products 
                ORDER BY name
            ''')
            products = self.db.cursor.fetchall()
            
            for product_id, name, batch, expiry, price in products:
                display_name = f"{name} (Batch: {batch}, Exp: {expiry})"
                self.product_data[display_name] = {
                    'id': product_id,
                    'name': name,
                    'batch_number': batch,
                    'expiry_date': expiry,
                    'unit_price': price
                }
                
                # Check if expired
                try:
                    exp_date = datetime.strptime(expiry, '%Y-%m-%d')
                    if exp_date < datetime.now():
                        self.product_data[display_name]['is_expired'] = True
                except:
                    pass
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", 
                               f"Failed to load data: {str(e)}")
        finally:
            self.db.close()
    
    def add_product_item(self):
        """Add a product to the entry"""
        dialog = ProductItemDialog(self, self.product_data)
        if dialog.exec_() == QDialog.Accepted:
            item_data = dialog.get_item_data()
            if item_data:
                self.product_items.append(item_data)
                self.refresh_products_table()
                self.calculate_total()
    
    def edit_product_item(self):
        """Edit selected product item"""
        current_row = self.products_table.currentRow()
        if 0 <= current_row < len(self.product_items):
            item_data = self.product_items[current_row]
            dialog = ProductItemDialog(self, self.product_data, item_data)
            if dialog.exec_() == QDialog.Accepted:
                new_data = dialog.get_item_data()
                if new_data:
                    self.product_items[current_row] = new_data
                    self.refresh_products_table()
                    self.calculate_total()
    
    def delete_product_item(self):
        """Delete selected product item"""
        current_row = self.products_table.currentRow()
        if 0 <= current_row < len(self.product_items):
            reply = QMessageBox.question(self, "Delete Product", 
                                       "Are you sure you want to delete this product?",
                                       QMessageBox.Yes | QMessageBox.No)
            if reply == QMessageBox.Yes:
                del self.product_items[current_row]
                self.refresh_products_table()
                self.calculate_total()
    
    def refresh_products_table(self):
        """Refresh the products table"""
        self.products_table.setRowCount(len(self.product_items))
        
        for row, item in enumerate(self.product_items):
            # Product name
            product_item = QTableWidgetItem(item['product_name'])
            
            # Check if expired and color red
            if item.get('expiry_date'):
                try:
                    exp_date = datetime.strptime(item['expiry_date'], '%Y-%m-%d')
                    if exp_date < datetime.now():
                        product_item.setForeground(QColor('red'))
                        product_item.setToolTip(f"EXPIRED on {item['expiry_date']}")
                except:
                    pass
            
            self.products_table.setItem(row, 0, product_item)
            self.products_table.setItem(row, 1, QTableWidgetItem(item.get('batch_number', '')))
            self.products_table.setItem(row, 2, QTableWidgetItem(item.get('expiry_date', '')))
            self.products_table.setItem(row, 3, QTableWidgetItem(str(item['quantity'])))
            self.products_table.setItem(row, 4, QTableWidgetItem(f"{item['unit_price']:.2f}"))
            self.products_table.setItem(row, 5, QTableWidgetItem(f"{item['discount']}%"))
            self.products_table.setItem(row, 6, QTableWidgetItem(f"Rs {item['amount']:.2f}"))
            
            # Center align numeric columns
            for col in [3, 4, 5, 6]:
                self.products_table.item(row, col).setTextAlignment(Qt.AlignCenter)
    
    def calculate_total(self):
        """Calculate and display total amount"""
        total = sum(item['amount'] for item in self.product_items)
        self.total_label.setText(f"Total: Rs {total:.2f}")
    
    def saveEntry(self):
        """Save the entry and generate invoice if enabled"""
        # Validate inputs
        if self.customer_combo.currentIndex() == 0:
            QMessageBox.warning(self, "Validation Error", "Please select a customer")
            return
        
        if not self.product_items:
            QMessageBox.warning(self, "Validation Error", "Please add at least one product")
            return
        
        try:
            self.db.connect()
            
            # Get form data
            date = self.date_edit.date().toString("yyyy-MM-dd")
            customer_name = self.customer_combo.currentText()
            customer_id = self.customer_data[customer_name]
            is_credit = 1 if self.is_credit.isChecked() else 0
            notes = self.notes_edit.text()
            
            # Calculate total
            total_amount = sum(item['amount'] for item in self.product_items)
            
            # Begin transaction
            self.db.conn.execute('BEGIN TRANSACTION')
            
            # Get current balance
            self.db.cursor.execute("SELECT MAX(balance) FROM transactions")
            result = self.db.cursor.fetchone()
            current_balance = result[0] if result[0] is not None else 0
            
            # Calculate new balance
            new_balance = current_balance + total_amount if is_credit else current_balance - total_amount
            
            # Create a combined entry for all products
            products_json = json.dumps(self.product_items)
            
            # Insert into entries table (simplified - you may need to adjust based on your schema)
            self.db.cursor.execute('''
                INSERT INTO entries
                (date, customer_id, product_id, quantity, unit_price, is_credit, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (date, customer_id, 
                  self.product_items[0]['product_id'],  # Use first product ID
                  1,  # Quantity 1 for the entry
                  total_amount,  # Total as unit price
                  is_credit, 
                  f"{notes} | Products: {products_json}"))
            
            entry_id = self.db.cursor.lastrowid
            
            # Insert into transactions table
            self.db.cursor.execute('''
                INSERT INTO transactions
                (entry_id, amount, balance)
                VALUES (?, ?, ?)
            ''', (entry_id, total_amount, new_balance))
            
            # Prepare entry data for invoice
            entry_data = {
                'entry_id': entry_id,
                'date': date,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'items': self.product_items,  # Multiple products
                'total_amount': total_amount,
                'is_credit': is_credit,
                'notes': notes,
                'balance': new_balance,
                'transport_name': self.transport_name_edit.text() or 'N/A',
                'delivery_date': self.delivery_date_edit.date().toString("dd-MM-yy"),
                'delivery_location': self.delivery_location_edit.text()
            }
            
            # Generate invoice if enabled
            invoice_path = None
            invoice_number = None
            if self.auto_invoice_check.isChecked():
                try:
                    invoice_path = self.invoice_generator.generate_invoice_from_entry(
                        entry_data, self.db.conn
                    )
                    
                    # Extract invoice number
                    invoice_filename = os.path.basename(invoice_path)
                    invoice_number = invoice_filename.split('_')[1]
                    
                    # Update notes with invoice number
                    updated_notes = f"{notes} [Invoice: INV-{invoice_number}]" if notes else f"Invoice: INV-{invoice_number}"
                    
                    self.db.cursor.execute(
                        "UPDATE entries SET notes = ? WHERE id = ?",
                        (updated_notes, entry_id)
                    )
                    
                except Exception as e:
                    print(f"Invoice generation error: {e}")
                    QMessageBox.warning(self, "Invoice Warning", 
                                      f"Entry saved but invoice generation failed: {str(e)}")
            
            # Log audit trail
            try:
                main_window = self.window()
                user_id = main_window.current_user['user_id'] if hasattr(main_window, 'current_user') else None
                username = main_window.current_user['username'] if hasattr(main_window, 'current_user') else 'system'
                
                audit_trail = AuditTrail(self.db.db_path)
                audit_trail.log_data_change(
                    user_id=user_id,
                    username=username,
                    operation="INSERT",
                    table_name="entries",
                    record_id=entry_id,
                    new_values=entry_data
                )
            except Exception as e:
                print(f"Audit trail error: {e}")
            
            # Commit transaction
            self.db.conn.commit()
            
            # Show success message
            success_message = f"Entry saved successfully!\n\n"
            success_message += f"Products: {len(self.product_items)}\n"
            success_message += f"Total Amount: Rs. {total_amount:.2f}\n"
            success_message += f"New Balance: Rs. {new_balance:.2f}"
            
            if invoice_path:
                success_message += f"\n\nInvoice generated: {os.path.basename(invoice_path)}"
                self.status_label.setText(f"✓ Invoice saved: {invoice_path}")
                self.status_label.setStyleSheet("color: green; font-weight: bold;")
                
                # Emit signal with invoice path
                self.entry_saved.emit(invoice_path)
            
            QMessageBox.information(self, "Success", success_message)
            
            # Clear form after successful save
            self.clearForm()
            
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.critical(self, "Error", f"Failed to save entry: {str(e)}")
            
        finally:
            self.db.close()
    
    def clearForm(self):
        """Clear all form fields"""
        self.date_edit.setDate(QDate.currentDate())
        self.customer_combo.setCurrentIndex(0)
        self.product_items = []
        self.refresh_products_table()
        self.calculate_total()
        self.is_credit.setChecked(True)
        self.notes_edit.clear()
        self.transport_name_edit.clear()
        self.delivery_date_edit.setDate(QDate.currentDate())
        self.delivery_location_edit.clear()
        self.status_label.clear()


# Quick view dialog (same as before)
class InvoiceQuickViewDialog(QDialog):
    """Quick view dialog to show invoice path and open options"""
    
    def __init__(self, invoice_path, parent=None):
        super().__init__(parent)
        self.invoice_path = invoice_path
        self.setWindowTitle("Invoice Generated")
        self.setModal(True)
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout()
        
        # Success icon and message
        success_label = QLabel("✓ Invoice Generated Successfully!")
        success_label.setStyleSheet("color: green; font-size: 16px; font-weight: bold;")
        layout.addWidget(success_label)
        
        # Invoice path
        path_label = QLabel(f"Saved to:\n{invoice_path}")
        path_label.setWordWrap(True)
        path_label.setStyleSheet("margin: 10px; padding: 10px; background-color: #f0f0f0;")
        layout.addWidget(path_label)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        open_button = QPushButton("Open Invoice")
        open_button.clicked.connect(self.open_invoice)
        
        open_folder_button = QPushButton("Open Folder")
        open_folder_button.clicked.connect(self.open_folder)
        
        close_button = QPushButton("Close")
        close_button.clicked.connect(self.accept)
        
        button_layout.addWidget(open_button)
        button_layout.addWidget(open_folder_button)
        button_layout.addWidget(close_button)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def open_invoice(self):
        """Open the invoice PDF"""
        import subprocess
        try:
            if sys.platform == "win32":
                os.startfile(self.invoice_path)
            elif sys.platform == "darwin":
                subprocess.call(["open", self.invoice_path])
            else:
                subprocess.call(["xdg-open", self.invoice_path])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open invoice: {str(e)}")
    
    def open_folder(self):
        """Open the folder containing the invoice"""
        import subprocess
        try:
            folder = os.path.dirname(self.invoice_path)
            if sys.platform == "win32":
                os.startfile(folder)
            elif sys.platform == "darwin":
                subprocess.call(["open", folder])
            else:
                subprocess.call(["xdg-open", folder])
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Could not open folder: {str(e)}")