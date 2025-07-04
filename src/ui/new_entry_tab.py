from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QLabel, QComboBox, 
    QDateEdit, QSpinBox, QDoubleSpinBox, 
    QLineEdit, QPushButton, QCheckBox, QMessageBox,
    QVBoxLayout, QHBoxLayout, QGroupBox
)
from PyQt5.QtCore import QDate, Qt
import sys
import os

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Database
from database.audit_trail import AuditTrail  # Add this line

class NewEntryTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.initUI()
        self.loadCustomersAndProducts()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Create form layout for entry details
        form_layout = QFormLayout()
        
        # Date picker
        self.date_edit = QDateEdit()
        self.date_edit.setDate(QDate.currentDate())
        self.date_edit.setCalendarPopup(True)
        form_layout.addRow("Date:", self.date_edit)
        
        # Customer dropdown
        self.customer_combo = QComboBox()
        form_layout.addRow("Customer:", self.customer_combo)
        
        # Product dropdown with improved display
        self.product_combo = QComboBox()
        self.product_combo.setMinimumWidth(400)  # Make wider to show batch and expiry info
        self.product_combo.currentIndexChanged.connect(self.updateUnitPrice)
        form_layout.addRow("Product (Batch - Expiry):", self.product_combo)
        
        # Product details display (read-only)
        self.product_details = QLineEdit()
        self.product_details.setReadOnly(True)
        self.product_details.setStyleSheet("background-color: #f0f0f0;")
        form_layout.addRow("Selected Product Details:", self.product_details)
        
        # Quantity spinner
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(1000)
        self.quantity_spin.setValue(1)
        self.quantity_spin.valueChanged.connect(self.calculateTotal)
        form_layout.addRow("Quantity:", self.quantity_spin)
        
        # Unit price
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setMinimum(0.01)
        self.unit_price_spin.setMaximum(99999.99)
        self.unit_price_spin.setValue(0.00)
        self.unit_price_spin.setPrefix("Rs. ")
        self.unit_price_spin.valueChanged.connect(self.calculateTotal)
        form_layout.addRow("Unit Price:", self.unit_price_spin)
        
        # Total amount (read-only)
        self.total_amount = QLineEdit()
        self.total_amount.setReadOnly(True)
        self.total_amount.setText("Rs0.00")
        form_layout.addRow("Total Amount:", self.total_amount)
        
        # Transaction type (credit/debit)
        self.is_credit = QCheckBox("Credit Entry")
        self.is_credit.setToolTip("Check for Credit, uncheck for Debit")
        form_layout.addRow("Entry Type:", self.is_credit)
        
        # Notes field
        self.notes_edit = QLineEdit()
        form_layout.addRow("Notes:", self.notes_edit)
        
        # Group the form elements
        details_group = QGroupBox("Entry Details")
        details_group.setLayout(form_layout)
        main_layout.addWidget(details_group)
        
        # Buttons for actions
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Save Entry")
        self.save_button.clicked.connect(self.saveEntry)
        
        self.clear_button = QPushButton("Clear Form")
        self.clear_button.clicked.connect(self.clearForm)
        
        self.refresh_button = QPushButton("Refresh Data")
        self.refresh_button.clicked.connect(self.loadCustomersAndProducts)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.clear_button)
        button_layout.addWidget(self.refresh_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def loadCustomersAndProducts(self):
        """Load customers and products from database"""
        try:
            self.db.connect()
            
            # Load customers
            self.customer_data = {}
            self.db.cursor.execute('SELECT id, name FROM customers ORDER BY name')
            customers = self.db.cursor.fetchall()
            
            self.customer_combo.clear()
            for customer_id, name in customers:
                self.customer_combo.addItem(name)
                self.customer_data[name] = customer_id
            
            # Load products with batch numbers and expiry dates
            self.product_data = {}
            self.db.cursor.execute('''
                SELECT id, name, unit_price, batch_number, expiry_date, description 
                FROM products 
                ORDER BY name, expiry_date DESC
            ''')
            products = self.db.cursor.fetchall()
            
            self.product_combo.clear()
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            
            for product_id, name, price, batch_number, expiry_date, description in products:
                # Create display text with product name, batch, and expiry
                expiry_status = ""
                try:
                    expiry_qdate = QDate.fromString(expiry_date, "yyyy-MM-dd")
                    if expiry_qdate.isValid():
                        if expiry_qdate < QDate.currentDate():
                            expiry_status = " [EXPIRED]"
                        elif expiry_qdate < QDate.currentDate().addDays(30):
                            expiry_status = " [EXPIRING SOON]"
                except:
                    pass
                
                display_text = f"{name} | Batch: {batch_number} | Exp: {expiry_date}{expiry_status}"
                
                self.product_combo.addItem(display_text)
                self.product_data[display_text] = {
                    'id': product_id,
                    'name': name,
                    'price': price,
                    'batch_number': batch_number,
                    'expiry_date': expiry_date,
                    'description': description
                }
            
            # Update unit price based on first product
            if products:
                self.updateUnitPrice()
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load data: {str(e)}")
        finally:
            self.db.close()
    
    def updateUnitPrice(self):
        """Update unit price and details based on selected product"""
        current_product = self.product_combo.currentText()
        if current_product in self.product_data:
            product_info = self.product_data[current_product]
            
            # Update price
            self.unit_price_spin.setValue(product_info['price'])
            
            # Update product details display
            details = f"Name: {product_info['name']} | Batch: {product_info['batch_number']} | Expiry: {product_info['expiry_date']}"
            if product_info['description']:
                details += f" | Description: {product_info['description']}"
            
            self.product_details.setText(details)
            
            # Check if product is expired and warn user
            try:
                expiry_date = QDate.fromString(product_info['expiry_date'], "yyyy-MM-dd")
                if expiry_date.isValid():
                    if expiry_date < QDate.currentDate():
                        self.product_details.setStyleSheet("background-color: #ffcccc; color: #cc0000;")
                        QMessageBox.warning(
                            self, "Expired Product Warning", 
                            f"Warning: The selected product has expired on {product_info['expiry_date']}. "
                            "Please verify before proceeding with the transaction."
                        )
                    elif expiry_date < QDate.currentDate().addDays(30):
                        self.product_details.setStyleSheet("background-color: #fff3cd; color: #856404;")
                    else:
                        self.product_details.setStyleSheet("background-color: #d4edda; color: #155724;")
                else:
                    self.product_details.setStyleSheet("background-color: #f0f0f0;")
            except:
                self.product_details.setStyleSheet("background-color: #f0f0f0;")
            
            self.calculateTotal()
        else:
            self.product_details.clear()
            self.product_details.setStyleSheet("background-color: #f0f0f0;")
    
    def calculateTotal(self):
        """Calculate and display total amount"""
        quantity = self.quantity_spin.value()
        unit_price = self.unit_price_spin.value()
        total = quantity * unit_price
        self.total_amount.setText(f"Rs. {total:.2f}")
    
    def saveEntry(self):
        """Save the entry to database"""
        # Validate form first
        if not self.validateForm():
            return
        
        try:
            date = self.date_edit.date().toString("yyyy-MM-dd")
            customer_name = self.customer_combo.currentText()
            product_display = self.product_combo.currentText()
            quantity = self.quantity_spin.value()
            unit_price = self.unit_price_spin.value()
            is_credit = self.is_credit.isChecked()
            notes = self.notes_edit.text()
            
            # Get IDs from the combo box data
            customer_id = self.customer_data.get(customer_name)
            product_info = self.product_data.get(product_display)
            
            if not customer_id or not product_info:
                QMessageBox.warning(self, "Validation Error", "Please select valid customer and product.")
                return
            
            product_id = product_info['id']
            product_name = product_info['name']
            batch_number = product_info['batch_number']
            expiry_date = product_info['expiry_date']
            
            # Final check for expired products
            try:
                expiry_qdate = QDate.fromString(expiry_date, "yyyy-MM-dd")
                if expiry_qdate.isValid() and expiry_qdate < QDate.currentDate():
                    reply = QMessageBox.question(
                        self, "Expired Product Confirmation",
                        f"The selected product (Batch: {batch_number}) expired on {expiry_date}. "
                        "Are you sure you want to proceed with this transaction?",
                        QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
            except:
                pass
            
            # Connect to database
            self.db.connect()
            
            # Start transaction
            self.db.conn.execute("BEGIN")
            
            try:
                # Insert into entries table
                self.db.cursor.execute('''
                    INSERT INTO entries 
                    (date, customer_id, product_id, quantity, unit_price, is_credit, notes) 
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (date, customer_id, product_id, quantity, unit_price, is_credit, notes))
                
                entry_id = self.db.cursor.lastrowid
                total_amount = quantity * unit_price
                
                # Get current balance
                self.db.cursor.execute("SELECT MAX(balance) FROM transactions")
                result = self.db.cursor.fetchone()
                current_balance = result[0] if result[0] is not None else 0
                
                # Calculate new balance
                new_balance = current_balance + total_amount if is_credit else current_balance - total_amount
                
                # Insert into transactions table
                self.db.cursor.execute('''
                    INSERT INTO transactions
                    (entry_id, amount, balance)
                    VALUES (?, ?, ?)
                ''', (entry_id, total_amount, new_balance))
                
                # Prepare audit data with batch information
                entry_data = {
                    'date': date,
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'product_id': product_id,
                    'product_name': product_name,
                    'batch_number': batch_number,
                    'expiry_date': expiry_date,
                    'quantity': quantity,
                    'unit_price': unit_price,
                    'total_amount': total_amount,
                    'is_credit': is_credit,
                    'notes': notes,
                    'balance': new_balance
                }
                
                # Get current user info from main window
                main_window = self.window()
                user_id = main_window.current_user['user_id'] if hasattr(main_window, 'current_user') else None
                username = main_window.current_user['username'] if hasattr(main_window, 'current_user') else 'system'
                
                # Log the action in audit trail
                audit_trail = AuditTrail(self.db.db_path)
                audit_trail.log_data_change(
                    user_id=user_id,
                    username=username,
                    operation="INSERT",
                    table_name="entries",
                    record_id=entry_id,
                    new_values=entry_data
                )
                
                # Commit transaction
                self.db.conn.commit()
                
                success_message = f"Entry saved successfully!\n\nProduct: {product_name}\nBatch: {batch_number}\nExpiry: {expiry_date}\nAmount: Rs. {total_amount:.2f}\nNew Balance: Rs. {new_balance:.2f}"
                QMessageBox.information(self, "Success", success_message)
                self.clearForm()
                
            except Exception as e:
                # Rollback transaction on error
                self.db.conn.rollback()
                raise e
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save entry: {str(e)}")
        finally:
            self.db.close()
    
    def clearForm(self):
        """Reset the form to default values"""
        self.date_edit.setDate(QDate.currentDate())
        self.quantity_spin.setValue(1)
        self.notes_edit.clear()
        self.is_credit.setChecked(False)
        self.product_details.clear()
        self.product_details.setStyleSheet("background-color: #f0f0f0;")
        # We don't reset customer and product combo boxes
        # But we do update the unit price based on selected product
        self.updateUnitPrice()
        
    def validateForm(self):
        """Validate form fields"""
        # Check if customer is selected
        if self.customer_combo.currentIndex() == -1 or not self.customer_combo.currentText():
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return False
        
        # Check if product is selected
        if self.product_combo.currentIndex() == -1 or not self.product_combo.currentText():
            QMessageBox.warning(self, "Validation Error", "Please select a product.")
            return False
        
        # Check quantity
        if self.quantity_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Quantity must be greater than zero.")
            return False
        
        # Check unit price
        if self.unit_price_spin.value() <= 0:
            QMessageBox.warning(self, "Validation Error", "Unit price must be greater than zero.")
            return False
        
        # Validate that customer exists in data
        customer_name = self.customer_combo.currentText()
        if customer_name not in self.customer_data:
            QMessageBox.warning(self, "Validation Error", "Invalid customer selected. Please refresh and try again.")
            return False
        
        # Validate that product exists in data
        product_display = self.product_combo.currentText()
        if product_display not in self.product_data:
            QMessageBox.warning(self, "Validation Error", "Invalid product selected. Please refresh and try again.")
            return False
        
        return True
    
    def getSelectedProductInfo(self):
        """Get detailed information about the currently selected product"""
        current_product = self.product_combo.currentText()
        if current_product in self.product_data:
            return self.product_data[current_product]
        return None