"""
Enhanced New Entry Tab for MedRep with Multi-Product Support - MongoDB Only
Automatically generates Tru-Pharma style invoice when saving entries
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QComboBox, QDateEdit, QSpinBox, QDoubleSpinBox,
                             QCheckBox, QPushButton, QGroupBox, QFormLayout,
                             QMessageBox, QLineEdit, QTableWidget, QTableWidgetItem,
                             QDialog, QDialogButtonBox, QHeaderView, QTextEdit,
                             QFileDialog)
from PyQt5.QtCore import QDate, pyqtSignal, Qt
from PyQt5.QtGui import QFont, QColor, QPixmap
from datetime import datetime
import os
import sys
import json

# Add the auto invoice generator
try:
    from src.utils.auto_invoice_generator import AutoInvoiceGenerator
except ImportError:
    print("Warning: Auto invoice generator not available")
    AutoInvoiceGenerator = None

# Import MongoDB database module only
from src.database.mongo_adapter import MongoAdapter


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


class InvoiceDetailsDialog(QDialog):
    """Dialog to collect invoice generation details"""
    
    def __init__(self, parent=None, customer_info=None):
        super().__init__(parent)
        self.setWindowTitle("Invoice Generation Details")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.customer_info = customer_info or {}
        self.company_logo_path = None
        self.initUI()
    
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        # Instructions
        instruction_label = QLabel("Please provide the following details for invoice generation:")
        instruction_label.setStyleSheet("font-weight: bold; color: #4B0082; margin-bottom: 15px; font-size: 14px;")
        layout.addWidget(instruction_label)
        
        # Company Information Group
        company_group = QGroupBox("Company Information")
        company_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        company_layout = QFormLayout()
        
        # Company name
        self.company_name = QLineEdit()
        self.company_name.setText("Tru_pharma")
        self.company_name.setStyleSheet("border: 1px solid #4B0082; padding: 8px; font-size: 12px;")
        company_layout.addRow("Company Name:", self.company_name)
        
        # Company contact
        self.company_contact = QLineEdit()
        self.company_contact.setText("0333-99-11-514")
        self.company_contact.setStyleSheet("border: 1px solid #4B0082; padding: 8px; font-size: 12px;")
        company_layout.addRow("Company Contact:", self.company_contact)
        
        # Company address
        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(100)
        self.company_address.setText("Main Market, Faisalabad\nPunjab, Pakistan\nPhone: 0333-99-11-514\nEmail: info@trupharma.com")
        self.company_address.setStyleSheet("border: 1px solid #4B0082; padding: 8px; font-size: 12px;")
        company_layout.addRow("Company Address:", self.company_address)
        
        # Logo selection
        logo_layout = QHBoxLayout()
        self.logo_preview = QLabel("No logo selected")
        self.logo_preview.setFixedSize(120, 60)
        self.logo_preview.setAlignment(Qt.AlignCenter)
        self.logo_preview.setStyleSheet("border: 2px dashed #4B0082; background-color: #f8f8f8;")
        
        self.select_logo_btn = QPushButton("Select Logo")
        self.select_logo_btn.clicked.connect(self.selectLogo)
        self.select_logo_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 8px 15px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        self.remove_logo_btn = QPushButton("Remove Logo")
        self.remove_logo_btn.clicked.connect(self.removeLogo)
        self.remove_logo_btn.setEnabled(False)
        
        logo_layout.addWidget(self.logo_preview)
        logo_layout.addWidget(self.select_logo_btn)
        logo_layout.addWidget(self.remove_logo_btn)
        logo_layout.addStretch()
        
        company_layout.addRow("Company Logo:", logo_layout)
        
        company_group.setLayout(company_layout)
        layout.addWidget(company_group)
        
        # Transport & Delivery Information Group
        transport_group = QGroupBox("Transport & Delivery Information")
        transport_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        transport_layout = QFormLayout()
        
        # Transport name
        self.transport_name = QLineEdit()
        self.transport_name.setPlaceholderText("e.g., Jawad Aslam, TCS, Standard Delivery")
        self.transport_name.setText("Standard Delivery")
        self.transport_name.setStyleSheet("border: 1px solid #4B0082; padding: 8px; font-size: 12px;")
        transport_layout.addRow("Transport Name:", self.transport_name)
        
        # Delivery date
        self.delivery_date = QDateEdit()
        self.delivery_date.setCalendarPopup(True)
        self.delivery_date.setDate(QDate.currentDate())
        self.delivery_date.setStyleSheet("border: 1px solid #4B0082; padding: 8px; font-size: 12px;")
        transport_layout.addRow("Delivery Date:", self.delivery_date)
        
        # Delivery location
        self.delivery_location = QLineEdit()
        self.delivery_location.setPlaceholderText("e.g., adda johal, Main Market Faisalabad")
        # Auto-fill from customer address if available
        customer_address = self.customer_info.get('address', '')
        if customer_address:
            first_line = customer_address.split('\n')[0].strip()
            self.delivery_location.setText(first_line)
        self.delivery_location.setStyleSheet("border: 1px solid #4B0082; padding: 8px; font-size: 12px;")
        transport_layout.addRow("Delivery Location:", self.delivery_location)
        
        transport_group.setLayout(transport_layout)
        layout.addWidget(transport_group)
        
        # # Terms & Conditions Group
        # terms_group = QGroupBox("Terms & Conditions")
        # terms_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        # terms_layout = QVBoxLayout()
        
        # self.terms_text = QTextEdit()
        # self.terms_text.setMaximumHeight(120)
        # default_terms = ("Thank you for your business! Payment is due within 30 days.\n"
        #                 "All products are subject to our standard terms and conditions.\n"
        #                 "Please check all items upon delivery.")
        # self.terms_text.setText(default_terms)
        # self.terms_text.setStyleSheet("border: 1px solid #4B0082; padding: 8px; font-size: 12px;")
        # terms_layout.addWidget(self.terms_text)
        
        # terms_group.setLayout(terms_layout)
        # layout.addWidget(terms_group)
        
        # Customer Information (read-only display)
        customer_group = QGroupBox("Customer Information (from entry)")
        customer_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        customer_layout = QFormLayout()
        
        customer_name = self.customer_info.get('name', 'N/A')
        customer_address = self.customer_info.get('address', 'N/A')
        customer_contact = self.customer_info.get('contact', 'N/A')
        
        customer_info_text = f"Name: {customer_name}\nAddress: {customer_address}\nContact: {customer_contact}"
        customer_info_label = QLabel(customer_info_text)
        customer_info_label.setStyleSheet("background-color: #f5f5f5; padding: 10px; border: 1px solid #ccc; font-size: 11px;")
        customer_info_label.setWordWrap(True)
        customer_layout.addRow("Customer Details:", customer_info_label)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Invoice")
        self.generate_btn.clicked.connect(self.accept)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 12px 25px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        self.cancel_btn = QPushButton("Skip Invoice Generation")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 12px 25px;
                font-size: 14px;
                border-radius: 5px;
                border: 1px solid #ccc;
            }
        """)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.generate_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def selectLogo(self):
        """Select a company logo image file"""
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getOpenFileName(
            self, "Select Company Logo", "", 
            "Image Files (*.png *.jpg *.jpeg *.bmp *.gif);;All Files (*)", 
            options=options
        )
        
        if file_name:
            try:
                pixmap = QPixmap(file_name)
                
                if not pixmap.isNull():
                    # Scale pixmap to fit preview
                    scaled_pixmap = pixmap.scaled(120, 60, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.logo_preview.setPixmap(scaled_pixmap)
                    self.logo_preview.setText("")  # Clear text when image is set
                    
                    # Store the original path
                    self.company_logo_path = file_name
                    
                    # Enable remove button
                    self.remove_logo_btn.setEnabled(True)
                    
                    # Update button text
                    self.select_logo_btn.setText("Change Logo")
                else:
                    QMessageBox.warning(self, "Invalid Image", "Could not load the selected image file.")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load image: {str(e)}")
    
    def removeLogo(self):
        """Remove the selected logo"""
        self.logo_preview.clear()
        self.logo_preview.setText("No logo selected")
        self.company_logo_path = None
        self.remove_logo_btn.setEnabled(False)
        self.select_logo_btn.setText("Select Logo")
    
    def get_invoice_data(self):
        """Get the collected invoice data"""
        return {
            'company_name': self.company_name.text().strip() or 'Tru_pharma',
            'company_contact': self.company_contact.text().strip() or '0333-99-11-514',
            'company_address': self.company_address.toPlainText().strip(),
            'company_logo': self.company_logo_path,
            'transport_name': self.transport_name.text().strip() or 'Standard Delivery',
            'delivery_date': self.delivery_date.date().toString("dd-MM-yy"),
            'delivery_location': self.delivery_location.text().strip() or 'Customer Location',
            'terms': self.terms_text.toPlainText().strip()
        }


class NewEntryTab(QWidget):
    """
    Enhanced New Entry tab with multi-product support and automatic invoicing - MongoDB Only
    """
    
    # Signal emitted when entry is saved with invoice path
    entry_saved = pyqtSignal(str)  # invoice_path
    
    def __init__(self):
        super().__init__()
        try:
            self.db = MongoAdapter()
            if AutoInvoiceGenerator:
                self.invoice_generator = AutoInvoiceGenerator()
            else:
                self.invoice_generator = None
            self.customer_data = {}
            self.product_data = {}
            self.product_items = []  # List of products in current entry
            self.initUI()
            self.loadCustomersAndProducts()
        except Exception as e:
            print(f"Error initializing New Entry tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"New Entry tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the new entry tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__()
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize New Entry tab: {str(e)}")

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
        
        # # Transport name
        # self.transport_name_edit = QLineEdit()
        # self.transport_name_edit.setPlaceholderText("e.g., Jawad Aslam")
        # invoice_layout.addRow("Transport Name:", self.transport_name_edit)
        
        # # Delivery date
        # self.delivery_date_edit = QDateEdit()
        # self.delivery_date_edit.setCalendarPopup(True)
        # self.delivery_date_edit.setDate(QDate.currentDate())
        # invoice_layout.addRow("Delivery Date:", self.delivery_date_edit)
        
        # # Delivery location
        # self.delivery_location_edit = QLineEdit()
        # self.delivery_location_edit.setPlaceholderText("e.g., adda johal")
        # invoice_layout.addRow("Delivery Location:", self.delivery_location_edit)
        
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
        """Load customers and products from MongoDB database"""
        try:
            # Ensure we have a valid database connection
            if not self.db:
                self.db = MongoAdapter()
            
            if not self.db.connected:
                self.db.connect()
            
            # Load customers from MongoDB
            self.customer_data = {}
            self.customer_combo.clear()
            self.customer_combo.addItem("-- Select Customer --")
            
            customers = self.db.get_customers()
            
            for customer in customers:
                customer_id = str(customer.get('id', ''))
                name = customer.get('name', 'Unknown')
                contact = customer.get('contact', '')
                
                display_name = f"{name} ({contact})" if contact else name
                self.customer_combo.addItem(display_name)
                self.customer_data[display_name] = customer_id
            
            # Load products from MongoDB
            self.product_data = {}
            
            products = self.db.get_products()
            
            for product in products:
                product_id = str(product.get('id', ''))
                name = product.get('name', 'Unknown')
                batch = product.get('batch_number', 'No batch')
                expiry = product.get('expiry_date', 'No expiry')
                
                try:
                    price = float(product.get('unit_price', 0))
                except (ValueError, TypeError):
                    price = 0.0
                
                display_name = f"{name} - {batch} (Exp: {expiry}) - Rs. {price:.2f}"
                self.product_data[display_name] = {
                    'id': product_id,
                    'name': name,
                    'batch_number': batch,
                    'expiry_date': expiry,
                    'unit_price': price
                }
                
                # Check if expired
                if expiry and expiry != 'No expiry':
                    try:
                        exp_date = datetime.strptime(expiry, '%Y-%m-%d')
                        if exp_date < datetime.now():
                            self.product_data[display_name]['is_expired'] = True
                    except Exception:
                        pass
            
            print(f"Loaded {len(customers)} customers and {len(products)} products from MongoDB")
                
        except Exception as e:
            error_msg = f"Failed to load data from MongoDB: {str(e)}"
            print(f"MongoDB load error: {e}")
            import traceback
            traceback.print_exc()
            
            # Show user-friendly error message
            QMessageBox.critical(self, "MongoDB Error", error_msg)
            
            # Set default empty data to prevent further errors
            if not hasattr(self, 'customer_data') or not self.customer_data:
                self.customer_data = {}
                self.customer_combo.clear()
                self.customer_combo.addItem("-- No Customers Available --")
            
            if not hasattr(self, 'product_data') or not self.product_data:
                self.product_data = {}

    def add_product_item(self):
        """Add a product to the entry"""
        if not self.product_data:
            QMessageBox.warning(self, "No Products", 
                              "No products available. Please add products first or refresh the data.")
            return
            
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
        """Save the entry to MongoDB with invoice number generation"""
        try:
            # Validate inputs
            if not self.validateInputs():
                return
            
            # Generate invoice number for this entry
            invoice_number = self.generateInvoiceNumber()
            
            # Get values
            date = self.date_edit.date().toString("yyyy-MM-dd")
            customer_display_name = self.customer_combo.currentText()
            
            # Get customer ID from customer_data
            customer_id = None
            if customer_display_name in self.customer_data:
                customer_id = self.customer_data[customer_display_name]
            
            if not customer_id:
                QMessageBox.warning(self, "Error", "Please select a valid customer.")
                return
            
            is_credit = self.is_credit.isChecked()
            
            # If auto-invoice is checked, show invoice details dialog
            invoice_details = None
            if self.auto_invoice_check.isChecked():
                # Get customer info for the dialog
                customers = self.db.get_customers()
                customer_info = next((c for c in customers if str(c.get('id')) == str(customer_id)), {})
                
                # Show invoice details dialog
                invoice_dialog = InvoiceDetailsDialog(self, customer_info)
                if invoice_dialog.exec_() == QDialog.Accepted:
                    invoice_details = invoice_dialog.get_invoice_data()
                else:
                    # User cancelled invoice generation, ask if they want to continue without invoice
                    reply = QMessageBox.question(
                        self, "Continue Without Invoice?",
                        "Do you want to save the entry without generating an invoice?",
                        QMessageBox.Yes | QMessageBox.No,
                        QMessageBox.No
                    )
                    if reply == QMessageBox.No:
                        return
                    # Continue without invoice
                    self.auto_invoice_check.setChecked(False)
            
            # Prepare notes with invoice information
            base_notes = self.notes_edit.text().strip()
            invoice_info = f"Invoice: {invoice_number}"
            
            # Add transport and delivery info if invoice details were provided
            if invoice_details:
                transport_name = invoice_details['transport_name']
                delivery_location = invoice_details['delivery_location']
                delivery_date = invoice_details['delivery_date']
                
                invoice_info += f" | Transport: {transport_name} | Delivery: {delivery_location} ({delivery_date})"
            elif self.auto_invoice_check.isChecked():
                # Fallback to form values if dialog wasn't shown but auto-invoice is checked
                transport_name = self.transport_name_edit.text().strip() or "Standard Delivery"
                delivery_location = self.delivery_location_edit.text().strip() or "Customer Location"
                delivery_date = self.delivery_date_edit.date().toString("dd-MM-yy")
                
                invoice_info += f" | Transport: {transport_name} | Delivery: {delivery_location} ({delivery_date})"
            
            # Add products information as JSON for multi-product invoices
            if len(self.product_items) > 1:
                products_json = json.dumps([{
                    'product_name': item['product_name'],
                    'batch_number': item.get('batch_number', ''),
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'amount': item['amount']
                } for item in self.product_items])
                invoice_info += f" | Products: {products_json}"
            
            # Combine base notes with invoice info
            final_notes = f"{base_notes} | {invoice_info}" if base_notes else invoice_info
            
            # Calculate total amount
            total_amount = sum(item['amount'] for item in self.product_items)
            
            # For multi-product entries, use the first product for the main entry
            # and store others in notes
            main_product = self.product_items[0] if self.product_items else None
            if not main_product:
                QMessageBox.warning(self, "Error", "Please add at least one product.")
                return
            
            # Save entry with invoice number in notes
            success = self.db.add_entry(
                date=date,
                customer_id=customer_id,
                product_id=main_product['product_id'],
                quantity=main_product['quantity'],
                unit_price=main_product['unit_price'],
                is_credit=is_credit,
                notes=final_notes
            )
            
            if success:
                # Generate invoice if auto-invoice is enabled and details were provided
                invoice_path = None
                if self.auto_invoice_check.isChecked() and invoice_details:
                    try:
                        invoice_path = self.generateAutoInvoiceWithDetails(
                            invoice_number, customer_id, date, total_amount, invoice_details
                        )
                    except Exception as e:
                        print(f"Auto-invoice generation failed: {e}")
                        QMessageBox.warning(
                            self, "Invoice Generation Failed",
                            f"Entry saved successfully but invoice generation failed:\n{str(e)}\n\n"
                            "You can regenerate the invoice later from the Ledger tab."
                        )
                
                # Show success message with balance info
                customer_name = customer_display_name.split(' (')[0]  # Remove contact info
                balance = self.db.get_customer_balance(customer_id)
                
                balance_text = f"PKR{balance:,.2f}"
                balance_status = "Credit Balance" if balance > 0 else "No Balance"
                
                success_msg = (
                    f"Entry saved successfully!\n\n"
                    f"Invoice Number: {invoice_number}\n"
                    f"Customer: {customer_name}\n"
                    f"Amount: PKR{total_amount:,.2f} ({'Credit' if is_credit else 'Debit'})\n"
                    f"Customer Balance: {balance_text} ({balance_status})"
                )
                
                if invoice_path:
                    success_msg += f"\n\nInvoice saved to: {invoice_path}"
                    
                    # Show invoice quick view dialog
                    quick_view = InvoiceQuickViewDialog(invoice_path, self)
                    quick_view.exec_()
                else:
                    QMessageBox.information(self, "Entry Saved", success_msg)
                
                self.clearForm()
                
                # Emit signal to refresh other tabs
                if hasattr(self, 'entry_saved'):
                    self.entry_saved.emit(invoice_path or "")
                
            else:
                QMessageBox.critical(self, "Error", "Failed to save entry. Please try again.")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save entry: {str(e)}")
    
    def generateInvoiceNumber(self):
        """Generate a unique invoice number"""
        import random
        today = datetime.now()
        # Format: INV-YYYYMMDD-XXX (where XXX is a random 3-digit number)
        random_suffix = random.randint(100, 999)
        return f"INV-{today.year}{today.month:02d}{today.day:02d}-{random_suffix}"
    
    def generateAutoInvoice(self, invoice_number, customer_id, date, total_amount):
        """Generate invoice automatically using the improved PDF generator"""
        try:
            # Get customer and product details
            customers = self.db.get_customers()
            customer = next((c for c in customers if str(c.get('id')) == str(customer_id)), None)
            
            if not customer:
                raise Exception("Customer not found")
            
            # Prepare invoice data for the improved PDF generator
            invoice_data = {
                'company_name': 'Tru_pharma',
                'company_logo': None,
                'company_contact': '0333-99-11-514',
                'company_address': 'Main Market, Faisalabad\nPunjab, Pakistan\nPhone: 0333-99-11-514',
                'customer_info': {
                    'name': customer.get('name', ''),
                    'address': customer.get('address', ''),
                    'contact': customer.get('contact', '')
                },
                'transport_info': {
                    'transport_name': self.transport_name_edit.text().strip() or "Standard Delivery",
                    'delivery_date': self.delivery_date_edit.date().toString("dd-MM-yy"),
                    'delivery_location': self.delivery_location_edit.text().strip() or customer.get('address', '').split('\n')[0] if customer.get('address') else 'Customer Location'
                },
                'invoice_details': {
                    'invoice_number': invoice_number,
                    'invoice_date': date
                },
                'items': [{
                    'product_name': item['product_name'],
                    'batch_number': item.get('batch_number', 'N/A'),
                    'product_id': item.get('product_id', 'N/A'),
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'discount': item.get('discount', 0),
                    'amount': item['amount']
                } for item in self.product_items],
                'terms': self.notes_edit.text().strip() or 'Thank you for your business!',
                'total_amount': total_amount
            }
            
            # Create invoices directory if it doesn't exist
            invoice_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'invoices')
            os.makedirs(invoice_dir, exist_ok=True)
            
            # Generate invoice file path
            invoice_filename = f"{invoice_number}_{customer.get('name', 'customer').replace(' ', '_')}.pdf"
            invoice_path = os.path.join(invoice_dir, invoice_filename)
            
            # Generate invoice using the improved PDF generator
            from src.utils.pdf_generator import ImprovedPDFGenerator
            pdf_generator = ImprovedPDFGenerator()
            success = pdf_generator.generate_invoice_pdf(invoice_data, invoice_path)
            
            if success:
                return invoice_path
            else:
                raise Exception("PDF generation failed")
            
        except Exception as e:
            print(f"Error generating auto invoice: {e}")
            raise e
    
    def generateAutoInvoiceWithDetails(self, invoice_number, customer_id, date, total_amount, invoice_details):
        """Generate invoice automatically with the provided details"""
        try:
            # Get customer details
            customers = self.db.get_customers()
            customer = next((c for c in customers if str(c.get('id')) == str(customer_id)), None)
            
            if not customer:
                raise Exception("Customer not found")
            
            # Prepare invoice data for the improved PDF generator with custom details
            invoice_data = {
                'company_name': invoice_details['company_name'],
                'company_logo': invoice_details['company_logo'],
                'company_contact': invoice_details['company_contact'],
                'company_address': invoice_details['company_address'],
                'customer_info': {
                    'name': customer.get('name', ''),
                    'address': customer.get('address', ''),
                    'contact': customer.get('contact', '')
                },
                'transport_info': {
                    'transport_name': invoice_details['transport_name'],
                    'delivery_date': invoice_details['delivery_date'],
                    'delivery_location': invoice_details['delivery_location']
                },
                'invoice_details': {
                    'invoice_number': invoice_number,
                    'invoice_date': date
                },
                'items': [{
                    'product_name': item['product_name'],
                    'batch_number': item.get('batch_number', 'N/A'),
                    'product_id': item.get('product_id', 'N/A'),
                    'quantity': item['quantity'],
                    'unit_price': item['unit_price'],
                    'discount': item.get('discount', 0),
                    'amount': item['amount']
                } for item in self.product_items],
                'terms': invoice_details['terms'],
                'total_amount': total_amount
            }
            
            # Create invoices directory if it doesn't exist
            invoice_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'invoices')
            os.makedirs(invoice_dir, exist_ok=True)
            
            # Generate invoice file path
            invoice_filename = f"{invoice_number}_{customer.get('name', 'customer').replace(' ', '_')}.pdf"
            invoice_path = os.path.join(invoice_dir, invoice_filename)
            
            # Generate invoice using the improved PDF generator
            from src.utils.pdf_generator import ImprovedPDFGenerator
            pdf_generator = ImprovedPDFGenerator()
            success = pdf_generator.generate_invoice_pdf(invoice_data, invoice_path)
            
            if success:
                return invoice_path
            else:
                raise Exception("PDF generation failed")
            
        except Exception as e:
            print(f"Error generating auto invoice with details: {e}")
            raise e

    def validateInputs(self):
        """Validate form inputs"""
        if self.customer_combo.currentIndex() == 0:
            QMessageBox.warning(self, "Validation Error", "Please select a customer.")
            return False
        
        if not self.product_items:
            QMessageBox.warning(self, "Validation Error", "Please add at least one product.")
            return False
        
        return True
    
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