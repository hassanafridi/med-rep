from PyQt5.QtWidgets import (
    QWidget, QFormLayout, QLabel, QComboBox, 
    QDateEdit, QSpinBox, QDoubleSpinBox, 
    QLineEdit, QPushButton, QCheckBox, QMessageBox,
    QVBoxLayout, QHBoxLayout, QGroupBox
)
from PyQt5.QtCore import QDate
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
        
        # Product dropdown
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.updateUnitPrice)
        form_layout.addRow("Product:", self.product_combo)
        
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
        self.unit_price_spin.setPrefix("$")
        self.unit_price_spin.valueChanged.connect(self.calculateTotal)
        form_layout.addRow("Unit Price:", self.unit_price_spin)
        
        # Total amount (read-only)
        self.total_amount = QLineEdit()
        self.total_amount.setReadOnly(True)
        self.total_amount.setText("$0.00")
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
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(self.clear_button)
        
        main_layout.addLayout(button_layout)
        self.setLayout(main_layout)
    
    def loadCustomersAndProducts(self):
        """Load customers and products from database"""
        try:
            self.db.connect()
            
            # Load customers
            self.customer_data = {}
            self.db.cursor.execute('SELECT id, name FROM customers')
            customers = self.db.cursor.fetchall()
            
            self.customer_combo.clear()
            for customer_id, name in customers:
                self.customer_combo.addItem(name)
                self.customer_data[name] = customer_id
            
            # Load products
            self.product_data = {}
            self.db.cursor.execute('SELECT id, name, unit_price FROM products')
            products = self.db.cursor.fetchall()
            
            self.product_combo.clear()
            for product_id, name, price in products:
                self.product_combo.addItem(name)
                self.product_data[name] = (product_id, price)
            
            # Update unit price based on first product
            if products:
                self.updateUnitPrice()
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load data: {str(e)}")
        finally:
            self.db.close()
    
    def updateUnitPrice(self):
        """Update unit price based on selected product"""
        current_product = self.product_combo.currentText()
        if current_product in self.product_data:
            _, price = self.product_data[current_product]
            self.unit_price_spin.setValue(price)
            self.calculateTotal()
    
    def calculateTotal(self):
        """Calculate and display total amount"""
        quantity = self.quantity_spin.value()
        unit_price = self.unit_price_spin.value()
        total = quantity * unit_price
        self.total_amount.setText(f"${total:.2f}")
    
    def saveEntry(self):
        """Save the entry to database"""
        # Validate form first
        if not self.validateForm():
            return
        
        try:
            date = self.date_edit.date().toString("yyyy-MM-dd")
            customer_name = self.customer_combo.currentText()
            product_name = self.product_combo.currentText()
            quantity = self.quantity_spin.value()
            unit_price = self.unit_price_spin.value()
            is_credit = self.is_credit.isChecked()
            notes = self.notes_edit.text()
            
            # Get IDs from the combo box data
            customer_id = self.customer_data.get(customer_name)
            product_id, _ = self.product_data.get(product_name, (None, None))
            
            if not customer_id or not product_id:
                QMessageBox.warning(self, "Validation Error", "Please select valid customer and product.")
                return
            
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
                
                # Prepare audit data
                entry_data = {
                    'date': date,
                    'customer_id': customer_id,
                    'customer_name': customer_name,
                    'product_id': product_id,
                    'product_name': product_name,
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
                
                QMessageBox.information(self, "Success", "Entry saved successfully!")
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
        # We don't reset customer and product combo boxes
        # But we do update the unit price based on selected product
        self.updateUnitPrice()
        
    def validateForm(self):
        """Validate form fields"""
        # Check if customer is selected
        if self.customer_combo.currentIndex() == -1:
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return False
        
        # Check if product is selected
        if self.product_combo.currentIndex() == -1:
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
        
        return True