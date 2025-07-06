"""
Modified New Entry Tab for MedRep
Automatically generates Tru-Pharma style invoice when saving entries
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QPushButton, QGroupBox, QFormLayout,
                             QMessageBox, QLineEdit, QDialog, QApplication)
from PyQt5.QtCore import QDate, pyqtSignal
from PyQt5.QtGui import QFont
from datetime import datetime
import os
import sys

# Add the auto invoice generator
from src.utils.auto_invoice_generator import AutoInvoiceGenerator

# Import your existing database module
from src.database.db import Database
from src.database.audit_trail import AuditTrail


class NewEntryTab(QWidget):
    """
    Modified New Entry tab that automatically generates invoices
    """
    
    # Signal emitted when entry is saved with invoice path
    entry_saved = pyqtSignal(str)  # invoice_path
    
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.invoice_generator = AutoInvoiceGenerator()
        self.customer_data = {}
        self.product_data = {}
        self.initUI()
        self.loadCustomersAndProducts()
    
    def initUI(self):
        """Initialize the UI"""
        main_layout = QVBoxLayout()
        
        # Title
        title = QLabel("New Entry")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        main_layout.addWidget(title)
        
        # Form layout for entry details
        form_layout = QFormLayout()
        
        # Date picker
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDate(QDate.currentDate())
        form_layout.addRow("Date:", self.date_edit)
        
        # Customer dropdown
        self.customer_combo = QComboBox()
        self.customer_combo.currentIndexChanged.connect(self.onCustomerChanged)
        form_layout.addRow("Customer:", self.customer_combo)
        
        # Product dropdown
        self.product_combo = QComboBox()
        self.product_combo.currentIndexChanged.connect(self.onProductChanged)
        form_layout.addRow("Product:", self.product_combo)
        
        # Quantity
        self.quantity_spin = QSpinBox()
        self.quantity_spin.setMinimum(1)
        self.quantity_spin.setMaximum(9999)
        self.quantity_spin.valueChanged.connect(self.calculateTotal)
        form_layout.addRow("Quantity:", self.quantity_spin)
        
        # Unit price
        self.unit_price_spin = QDoubleSpinBox()
        self.unit_price_spin.setMinimum(0.0)
        self.unit_price_spin.setMaximum(999999.99)
        self.unit_price_spin.setDecimals(2)
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
        
        # NEW: Invoice options group
        invoice_group = QGroupBox("Invoice Options")
        invoice_layout = QFormLayout()
        
        # Auto-generate invoice checkbox (default: checked)
        self.auto_invoice_check = QCheckBox("Auto-generate Invoice")
        self.auto_invoice_check.setChecked(True)
        self.auto_invoice_check.setToolTip("Automatically generate PDF invoice when saving entry")
        invoice_layout.addRow("", self.auto_invoice_check)
        
        # Transport name (optional)
        self.transport_name_edit = QLineEdit()
        self.transport_name_edit.setPlaceholderText("e.g., Jawad Aslam")
        invoice_layout.addRow("Transport Name:", self.transport_name_edit)
        
        # Delivery location (optional)
        self.delivery_location_edit = QLineEdit()
        self.delivery_location_edit.setPlaceholderText("e.g., adda johal")
        invoice_layout.addRow("Delivery Location:", self.delivery_location_edit)
        
        invoice_group.setLayout(invoice_layout)
        
        # Group the form elements
        details_group = QGroupBox("Entry Details")
        details_group.setLayout(form_layout)
        main_layout.addWidget(details_group)
        main_layout.addWidget(invoice_group)
        
        # Buttons for actions
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
        
        # Status label for invoice generation
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
            self.product_combo.clear()
            self.product_combo.addItem("-- Select Product --")
            
            self.db.cursor.execute('''
                SELECT id, name, batch_number, expiry_date, unit_price 
                FROM products 
                ORDER BY name
            ''')
            products = self.db.cursor.fetchall()
            
            for product_id, name, batch, expiry, price in products:
                display_name = f"{name} (Batch: {batch}, Exp: {expiry})"
                self.product_combo.addItem(display_name)
                self.product_data[display_name] = {
                    'id': product_id,
                    'name': name,
                    'batch_number': batch,
                    'expiry_date': expiry,
                    'unit_price': price
                }
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", 
                               f"Failed to load data: {str(e)}")
        finally:
            self.db.close()
    
    def onCustomerChanged(self, index):
        """Handle customer selection change"""
        if index > 0:  # Valid selection
            # Could load customer-specific data here if needed
            pass
    
    def onProductChanged(self, index):
        """Handle product selection change"""
        if index > 0:  # Valid selection
            product_name = self.product_combo.currentText()
            if product_name in self.product_data:
                product_info = self.product_data[product_name]
                self.unit_price_spin.setValue(product_info['unit_price'])
    
    def calculateTotal(self):
        """Calculate and display total amount"""
        quantity = self.quantity_spin.value()
        unit_price = self.unit_price_spin.value()
        total = quantity * unit_price
        self.total_amount.setText(f"Rs{total:.2f}")
    
    def saveEntry(self):
        """Save the entry and generate invoice if enabled"""
        # Validate inputs
        if self.customer_combo.currentIndex() == 0:
            QMessageBox.warning(self, "Validation Error", 
                              "Please select a customer")
            return
        
        if self.product_combo.currentIndex() == 0:
            QMessageBox.warning(self, "Validation Error", 
                              "Please select a product")
            return
        
        try:
            self.db.connect()
            
            # Get form data
            date = self.date_edit.date().toString("yyyy-MM-dd")
            customer_name = self.customer_combo.currentText()
            customer_id = self.customer_data[customer_name]
            product_name = self.product_combo.currentText()
            product_info = self.product_data[product_name]
            product_id = product_info['id']
            quantity = self.quantity_spin.value()
            unit_price = self.unit_price_spin.value()
            is_credit = 1 if self.is_credit.isChecked() else 0
            notes = self.notes_edit.text()
            
            # Begin transaction
            self.db.conn.execute('BEGIN TRANSACTION')
            
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
            
            # Prepare entry data for invoice
            entry_data = {
                'date': date,
                'customer_id': customer_id,
                'customer_name': customer_name,
                'product_id': product_id,
                'product_name': product_info['name'],
                'batch_number': product_info['batch_number'],
                'expiry_date': product_info['expiry_date'],
                'quantity': quantity,
                'unit_price': unit_price,
                'total_amount': total_amount,
                'is_credit': is_credit,
                'notes': notes,
                'balance': new_balance,
                'transport_name': self.transport_name_edit.text() or 'N/A',
                'delivery_location': self.delivery_location_edit.text()
            }
            
            # Generate invoice if enabled
            invoice_path = None
            if self.auto_invoice_check.isChecked():
                try:
                    invoice_path = self.invoice_generator.generate_invoice_from_entry(
                        entry_data, self.db.conn
                    )
                    
                    # Update notes with invoice number
                    invoice_filename = os.path.basename(invoice_path)
                    invoice_number = invoice_filename.split('_')[1]  # Extract invoice number
                    updated_notes = f"{notes} [Invoice: INV-{invoice_number}]" if notes else f"Invoice: INV-{invoice_number}"
                    
                    self.db.cursor.execute(
                        "UPDATE entries SET notes = ? WHERE id = ?",
                        (updated_notes, entry_id)
                    )
                    
                except Exception as e:
                    # Log error but don't fail the transaction
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
            success_message = f"Entry saved successfully!\n\nProduct: {product_info['name']}\n"
            success_message += f"Batch: {product_info['batch_number']}\n"
            success_message += f"Expiry: {product_info['expiry_date']}\n"
            success_message += f"Amount: Rs. {total_amount:.2f}\n"
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
        self.product_combo.setCurrentIndex(0)
        self.quantity_spin.setValue(1)
        self.unit_price_spin.setValue(0.0)
        self.total_amount.setText("Rs0.00")
        self.is_credit.setChecked(False)
        self.notes_edit.clear()
        self.transport_name_edit.clear()
        self.delivery_location_edit.clear()
        self.status_label.clear()


# Optional: Quick view dialog for generated invoices
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


# Example of how to integrate into main window
def integrate_with_main_window(main_window):
    """
    Example of how to integrate the modified New Entry tab with auto invoice
    """
    # Replace the existing new entry tab
    new_entry_tab = NewEntryTab()
    
    # Connect signal to show quick view dialog
    def on_invoice_generated(invoice_path):
        dialog = InvoiceQuickViewDialog(invoice_path, main_window)
        dialog.exec_()
    
    new_entry_tab.entry_saved.connect(on_invoice_generated)
    
    # Add to main window tabs
    main_window.tabs.addTab(new_entry_tab, "New Entry")
    
    return new_entry_tab


if __name__ == "__main__":
    # Test the modified new entry tab
    app = QApplication(sys.argv)
    
    # Create test window
    test_window = QWidget()
    test_window.setWindowTitle("MedRep - New Entry with Auto Invoice")
    test_window.resize(600, 700)
    
    layout = QVBoxLayout()
    new_entry = NewEntryTab()
    
    # Connect to show invoice path
    def show_invoice_path(path):
        dialog = InvoiceQuickViewDialog(path, test_window)
        dialog.exec_()
    
    new_entry.entry_saved.connect(show_invoice_path)
    
    layout.addWidget(new_entry)
    test_window.setLayout(layout)
    
    test_window.show()
    sys.exit(app.exec_())