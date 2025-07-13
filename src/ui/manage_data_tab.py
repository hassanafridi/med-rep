from PyQt5.QtWidgets import (
    QWidget, QTabWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QMessageBox, QHeaderView, QGroupBox, QFormLayout,
    QDialog, QDialogButtonBox, QDoubleSpinBox, QTextEdit, QFileDialog, QAction, QMenu,
    QDateEdit
)
from PyQt5.QtCore import Qt, QDate
import sys
import os
import csv

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.customer_data = customer_data  # (id, name, contact, address)
        self.setWindowTitle("Customer Details - ")
        self.setMinimumWidth(400)
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QFormLayout()
        
        # Customer name
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        if self.customer_data:
            self.name_input.setText(self.customer_data[1])
        layout.addRow("Name:", self.name_input)
        
        # Contact
        self.contact_input = QLineEdit()
        self.contact_input.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        if self.customer_data:
            self.contact_input.setText(self.customer_data[2] or "")
        layout.addRow("Contact:", self.contact_input)
        
        # Address
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(100)
        self.address_input.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        if self.customer_data:
            self.address_input.setText(self.customer_data[3] or "")
        layout.addRow("Address:", self.address_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
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
        layout.addRow(button_box)
        
        self.setLayout(layout)
    
    def getCustomerData(self):
        """Return the customer data from the form"""
        return {
            'name': self.name_input.text(),
            'contact': self.contact_input.text(),
            'address': self.address_input.toPlainText()
        }

class ProductDialog(QDialog):
    def __init__(self, parent=None, product_data=None):
        super().__init__(parent)
        self.product_data = product_data  # (id, name, description, unit_price, batch_number, expiry_date)
        self.setWindowTitle("Product Details - ")
        self.setMinimumWidth(500)
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QFormLayout()
        
        # Product name
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        if self.product_data:
            self.name_input.setText(self.product_data[1])
        layout.addRow("Name:", self.name_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        self.description_input.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        if self.product_data:
            self.description_input.setText(self.product_data[2] or "")
        layout.addRow("Description:", self.description_input)
        
        # Unit price
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.01)
        self.price_input.setMaximum(99999.99)
        self.price_input.setPrefix("PKR ")
        self.price_input.setDecimals(2)
        self.price_input.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        if self.product_data:
            self.price_input.setValue(self.product_data[3])
        layout.addRow("Unit Price:", self.price_input)
        
        # Batch number
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("e.g., MCR-2024-001")
        self.batch_input.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        if self.product_data:
            self.batch_input.setText(self.product_data[4] or "")
        layout.addRow("Batch Number:", self.batch_input)
        
        # Expiry date
        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDate(QDate.currentDate().addYears(1))  # Default to 1 year from now
        self.expiry_input.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        if self.product_data and self.product_data[5]:
            try:
                expiry_date = QDate.fromString(self.product_data[5], "yyyy-MM-dd")
                if expiry_date.isValid():
                    self.expiry_input.setDate(expiry_date)
            except:
                pass  # Use default date if parsing fails
        layout.addRow("Expiry Date:", self.expiry_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.setStyleSheet("""
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
        layout.addRow(button_box)
        
        self.setLayout(layout)
    
    def getProductData(self):
        """Return the product data from the form"""
        return {
            'name': self.name_input.text(),
            'description': self.description_input.toPlainText(),
            'unit_price': self.price_input.value(),
            'batch_number': self.batch_input.text(),
            'expiry_date': self.expiry_input.date().toString("yyyy-MM-dd")
        }

class ManageDataTab(QWidget):
    def __init__(self, mongo_adapter=None):
        super().__init__()
        try:
            self.mongo_adapter = mongo_adapter or MongoAdapter()
            self.initUI()
        except Exception as e:
            print(f"Error initializing Manage Data tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Manage Data tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the manage data tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.mongo_adapter)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Manage Data tab: {str(e)}")
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Data Management - ")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4B0082; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Create tabs for customers and products
        tabs = QTabWidget()
        tabs.setStyleSheet("QTabWidget { border: 1px solid #4B0082; }")
        
        # Customers tab
        customers_tab = QWidget()
        customers_layout = QVBoxLayout()
        
        # Customer controls
        customer_controls = QHBoxLayout()
        
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("Search customers...")
        self.customer_search.textChanged.connect(self.filterCustomers)
        self.customer_search.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        
        self.add_customer_btn = QPushButton("Add Customer")
        self.add_customer_btn.clicked.connect(self.addCustomer)
        self.add_customer_btn.setStyleSheet("""
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
        
        self.import_customers_btn = QPushButton("Import")
        self.import_customers_btn.clicked.connect(lambda: self.importData("Customers"))
        self.import_customers_btn.setStyleSheet("""
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
        
        self.export_customers_btn = QPushButton("Export")
        self.export_customers_btn.clicked.connect(lambda: self.exportData("Customers"))
        self.export_customers_btn.setStyleSheet("""
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
            
        customer_controls.addWidget(QLabel("Search:"))
        customer_controls.addWidget(self.customer_search, 1)
        customer_controls.addWidget(self.add_customer_btn)
        customer_controls.addWidget(self.import_customers_btn)
        customer_controls.addWidget(self.export_customers_btn)
        
        customers_layout.addLayout(customer_controls)
        
        # Customer table
        self.customers_table = QTableWidget()
        self.customers_table.setColumnCount(4)
        self.customers_table.setHorizontalHeaderLabels(["ID", "Name", "Contact", "Address"])
        self.customers_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.customers_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.customers_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.customers_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customers_table.customContextMenuRequested.connect(self.showCustomerContextMenu)
        self.customers_table.setStyleSheet("border: 1px solid #4B0082;")
        
        customers_layout.addWidget(self.customers_table)
        customers_tab.setLayout(customers_layout)
        
        # Products tab
        products_tab = QWidget()
        products_layout = QVBoxLayout()
        
        # Product controls
        product_controls = QHBoxLayout()
        
        self.product_search = QLineEdit()
        self.product_search.setPlaceholderText("Search products...")
        self.product_search.textChanged.connect(self.filterProducts)
        self.product_search.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        
        self.add_product_btn = QPushButton("Add Product")
        self.add_product_btn.clicked.connect(self.addProduct)
        self.add_product_btn.setStyleSheet("""
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
        
        self.check_expiry_btn = QPushButton("Check Expiry")
        self.check_expiry_btn.clicked.connect(self.checkExpiredProducts)
        self.check_expiry_btn.setStyleSheet("""
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
        
        product_controls.addWidget(QLabel("Search:"))
        product_controls.addWidget(self.product_search, 1)
        product_controls.addWidget(self.add_product_btn)
        product_controls.addWidget(self.check_expiry_btn)
        
        products_layout.addLayout(product_controls)
        
        # Product table with new columns
        self.products_table = QTableWidget()
        self.products_table.setColumnCount(6)
        self.products_table.setHorizontalHeaderLabels(["ID", "Name", "Description", "Unit Price", "Batch Number", "Expiry Date"])
        self.products_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.products_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.products_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.products_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.products_table.customContextMenuRequested.connect(self.showProductContextMenu)
        self.products_table.setStyleSheet("border: 1px solid #4B0082;")
        
        products_layout.addWidget(self.products_table)
        products_tab.setLayout(products_layout)
        
        # Add tabs to tab widget
        tabs.addTab(customers_tab, "Customers")
        tabs.addTab(products_tab, "Products")
        
        main_layout.addWidget(tabs)
        self.setLayout(main_layout)
        
        # Load initial data
        self.loadCustomers()
        self.loadProducts()
    
    def loadCustomers(self):
        """Load customers from database using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
            
            # Use MongoDB adapter to get customers
            customers = self.mongo_adapter.get_customers()
            
            # Clear and set row count
            self.customers_table.setRowCount(0)
            self.customers_table.setRowCount(len(customers))
            
            # Fill table with data
            for row, customer in enumerate(customers):
                # Customer data: {'id': '...', 'name': '...', 'contact': '...', 'address': '...'}
                self.customers_table.setItem(row, 0, QTableWidgetItem(str(customer.get('id', ''))))
                self.customers_table.setItem(row, 1, QTableWidgetItem(str(customer.get('name', ''))))
                self.customers_table.setItem(row, 2, QTableWidgetItem(str(customer.get('contact', ''))))
                self.customers_table.setItem(row, 3, QTableWidgetItem(str(customer.get('address', ''))))
                
            print(f"Loaded {len(customers)} customers into table")
            
        except Exception as e:
            print(f"Error loading customers: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load customers: {str(e)}")

    def loadProducts(self):
        """Load products from database using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
            
            # Use MongoDB adapter to get products
            products = self.mongo_adapter.get_products()
            
            # Clear and set row count
            self.products_table.setRowCount(0)
            self.products_table.setRowCount(len(products))
            
            # Fill table with data
            for row, product in enumerate(products):
                # Product data: {'id': '...', 'name': '...', 'description': '...', 'unit_price': 0.0, 'batch_number': '...', 'expiry_date': '...'}
                self.products_table.setItem(row, 0, QTableWidgetItem(str(product.get('id', ''))))
                self.products_table.setItem(row, 1, QTableWidgetItem(str(product.get('name', ''))))
                self.products_table.setItem(row, 2, QTableWidgetItem(str(product.get('description', ''))))
                
                # Format price
                price = product.get('unit_price', 0)
                self.products_table.setItem(row, 3, QTableWidgetItem(f"PKR{float(price):.2f}"))
                
                self.products_table.setItem(row, 4, QTableWidgetItem(str(product.get('batch_number', ''))))
                
                # Format expiry date with warnings
                expiry_date = product.get('expiry_date', '')
                try:
                    expiry_qdate = QDate.fromString(str(expiry_date), "yyyy-MM-dd")
                    if expiry_qdate.isValid():
                        # Check if expired and highlight
                        if expiry_qdate < QDate.currentDate():
                            text = f"{expiry_date} (EXPIRED)"
                            item = QTableWidgetItem(text)
                            item.setBackground(Qt.red)
                        elif expiry_qdate < QDate.currentDate().addDays(30):
                            text = f"{expiry_date} (EXPIRING SOON)"
                            item = QTableWidgetItem(text)
                            item.setBackground(Qt.yellow)
                        else:
                            item = QTableWidgetItem(str(expiry_date))
                    else:
                        item = QTableWidgetItem(str(expiry_date))
                except:
                    item = QTableWidgetItem(str(expiry_date))
                
                self.products_table.setItem(row, 5, item)
                
            print(f"Loaded {len(products)} products into table")
            
        except Exception as e:
            print(f"Error loading products: {e}")
            QMessageBox.critical(self, "Database Error", f"Failed to load products: {str(e)}")

    def filterCustomers(self):
        """Filter customers based on search text"""
        search_text = self.customer_search.text().lower()
        
        for row in range(self.customers_table.rowCount()):
            visible = False
            for col in range(1, 4):  # Skip ID column
                item = self.customers_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            
            self.customers_table.setRowHidden(row, not visible)
    
    def filterProducts(self):
        """Filter products based on search text"""
        search_text = self.product_search.text().lower()
        
        for row in range(self.products_table.rowCount()):
            visible = False
            for col in range(1, 6):  # Skip ID column
                item = self.products_table.item(row, col)
                if item and search_text in item.text().lower():
                    visible = True
                    break
            
            self.products_table.setRowHidden(row, not visible)
    
    def addCustomer(self):
        """Add a new customer using MongoDB"""
        dialog = CustomerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            customer_data = dialog.getCustomerData()
            
            # Validate input
            if not customer_data['name']:
                QMessageBox.warning(self, "Validation Error", "Customer name is required.")
                return
            
            try:
                if not self.mongo_adapter:
                    QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                    return
                    
                # Use MongoDB adapter to add customer
                result = self.mongo_adapter.add_customer(
                    customer_data['name'], 
                    customer_data['contact'], 
                    customer_data['address']
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Customer added successfully.")
                    # Reload customers
                    self.loadCustomers()
                else:
                    QMessageBox.critical(self, "Error", "Failed to add customer.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add customer: {str(e)}")

    def editCustomer(self, customer_id):
        """Edit an existing customer using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get all customers and find the one with matching ID
            customers = self.mongo_adapter.get_customers()
            customer = None
            
            for c in customers:
                if str(c.get('id')) == str(customer_id):
                    customer = (c.get('id'), c.get('name'), c.get('contact'), c.get('address'))
                    break
            
            if not customer:
                QMessageBox.warning(self, "Customer Not Found", f"Customer with ID {customer_id} not found.")
                return
            
            dialog = CustomerDialog(self, customer)
            
            if dialog.exec_() == QDialog.Accepted:
                customer_data = dialog.getCustomerData()
                
                # Validate input
                if not customer_data['name']:
                    QMessageBox.warning(self, "Validation Error", "Customer name is required.")
                    return
                
                # Use MongoDB adapter to update customer
                result = self.mongo_adapter.mongo_db.update_customer(
                    customer_id,
                    customer_data['name'], 
                    customer_data['contact'], 
                    customer_data['address']
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Customer updated successfully.")
                    # Reload customers
                    self.loadCustomers()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update customer.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update customer: {str(e)}")

    def deleteCustomer(self, customer_id):
        """Delete a customer using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Check if customer has entries
            entries = self.mongo_adapter.get_entries()
            entry_count = sum(1 for entry in entries if str(entry.get('customer_id')) == str(customer_id))
            
            if entry_count > 0:
                QMessageBox.warning(
                    self, "Cannot Delete",
                    f"This customer has {entry_count} entries. Delete all entries first."
                )
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                "Are you sure you want to delete this customer?\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Use MongoDB adapter to delete customer
                result = self.mongo_adapter.mongo_db.delete_customer(customer_id)
                
                if result:
                    QMessageBox.information(self, "Success", "Customer deleted successfully.")
                    # Reload customers
                    self.loadCustomers()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete customer.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete customer: {str(e)}")

    def addProduct(self):
        """Add a new product using MongoDB"""
        dialog = ProductDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            product_data = dialog.getProductData()
            
            # Validate input
            if not product_data['name']:
                QMessageBox.warning(self, "Validation Error", "Product name is required.")
                return
            
            if not product_data['batch_number']:
                QMessageBox.warning(self, "Validation Error", "Batch number is required.")
                return
            
            if product_data['unit_price'] <= 0:
                QMessageBox.warning(self, "Validation Error", "Unit price must be greater than zero.")
                return
            
            try:
                if not self.mongo_adapter:
                    QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                    return
                    
                # Check if batch number already exists
                products = self.mongo_adapter.get_products()
                for product in products:
                    if product.get('batch_number') == product_data['batch_number']:
                        QMessageBox.warning(self, "Validation Error", "Batch number already exists. Please use a unique batch number.")
                        return
                
                # Use MongoDB adapter to add product
                result = self.mongo_adapter.add_product(
                    product_data['name'],
                    product_data['description'],
                    product_data['unit_price'],
                    product_data['batch_number'],
                    product_data['expiry_date']
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Product added successfully.")
                    # Reload products
                    self.loadProducts()
                else:
                    QMessageBox.critical(self, "Error", "Failed to add product.")
                    
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add product: {str(e)}")

    def editProduct(self, product_id):
        """Edit an existing product using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get all products and find the one with matching ID
            products = self.mongo_adapter.get_products()
            product = None
            
            for p in products:
                if str(p.get('id')) == str(product_id):
                    product = (
                        p.get('id'), 
                        p.get('name'), 
                        p.get('description'), 
                        p.get('unit_price'),
                        p.get('batch_number'),
                        p.get('expiry_date')
                    )
                    break
            
            if not product:
                QMessageBox.warning(self, "Product Not Found", f"Product with ID {product_id} not found.")
                return
            
            dialog = ProductDialog(self, product)
            
            if dialog.exec_() == QDialog.Accepted:
                product_data = dialog.getProductData()
                
                # Validate input
                if not product_data['name']:
                    QMessageBox.warning(self, "Validation Error", "Product name is required.")
                    return
                
                if not product_data['batch_number']:
                    QMessageBox.warning(self, "Validation Error", "Batch number is required.")
                    return
                
                if product_data['unit_price'] <= 0:
                    QMessageBox.warning(self, "Validation Error", "Unit price must be greater than zero.")
                    return
                
                # Check if batch number already exists (excluding current product)
                all_products = self.mongo_adapter.get_products()
                for p in all_products:
                    if (p.get('batch_number') == product_data['batch_number'] and 
                        str(p.get('id')) != str(product_id)):
                        QMessageBox.warning(self, "Validation Error", "Batch number already exists. Please use a unique batch number.")
                        return
                
                # Use MongoDB adapter to update product
                result = self.mongo_adapter.mongo_db.update_product(
                    product_id,
                    product_data['name'],
                    product_data['description'],
                    product_data['unit_price'],
                    product_data['batch_number'],
                    product_data['expiry_date']
                )
                
                if result:
                    QMessageBox.information(self, "Success", "Product updated successfully.")
                    # Reload products
                    self.loadProducts()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update product.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update product: {str(e)}")

    def deleteProduct(self, product_id):
        """Delete a product using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Check if product has entries
            entries = self.mongo_adapter.get_entries()
            entry_count = sum(1 for entry in entries if str(entry.get('product_id')) == str(product_id))
            
            if entry_count > 0:
                QMessageBox.warning(
                    self, "Cannot Delete",
                    f"This product has {entry_count} entries. Delete all entries first."
                )
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                "Are you sure you want to delete this product?\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Use MongoDB adapter to delete product
                result = self.mongo_adapter.mongo_db.delete_product(product_id)
                
                if result:
                    QMessageBox.information(self, "Success", "Product deleted successfully.")
                    # Reload products
                    self.loadProducts()
                else:
                    QMessageBox.critical(self, "Error", "Failed to delete product.")
                    
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete product: {str(e)}")

    def checkExpiredProducts(self):
        """Check for expired or expiring products using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            current_date = QDate.currentDate()
            upcoming_date = current_date.addDays(30)
            
            # Get all products
            products = self.mongo_adapter.get_products()
            
            expired_products = []
            expiring_products = []
            
            for product in products:
                expiry_date_str = product.get('expiry_date', '')
                if expiry_date_str:
                    try:
                        expiry_date = QDate.fromString(expiry_date_str, "yyyy-MM-dd")
                        if expiry_date.isValid():
                            if expiry_date < current_date:
                                expired_products.append(product)
                            elif expiry_date <= upcoming_date:
                                expiring_products.append(product)
                    except:
                        pass  # Skip invalid dates
            
            message = ""
            
            if expired_products:
                message += "EXPIRED PRODUCTS:\n"
                for product in expired_products:
                    message += f"• {product.get('name', 'Unknown')} (Batch: {product.get('batch_number', 'Unknown')}) - Expired: {product.get('expiry_date', 'Unknown')}\n"
                message += "\n"
            
            if expiring_products:
                message += "PRODUCTS EXPIRING IN 30 DAYS:\n"
                for product in expiring_products:
                    message += f"• {product.get('name', 'Unknown')} (Batch: {product.get('batch_number', 'Unknown')}) - Expires: {product.get('expiry_date', 'Unknown')}\n"
            
            if not message:
                message = "No expired or expiring products found."
            
            QMessageBox.information(self, "Product Expiry Check", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to check expired products: {str(e)}")

    def showCustomerContextMenu(self, position):
        """Show context menu for customer table"""
        # Get the selected row
        selected_rows = self.customers_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Get customer ID from the first column
        row = selected_rows[0].row()
        customer_id_item = self.customers_table.item(row, 0)
        if not customer_id_item:
            return
            
        customer_id = customer_id_item.text()
        
        # Create context menu
        context_menu = QMenu(self)
        
        edit_action = QAction("Edit Customer", self)
        edit_action.triggered.connect(lambda: self.editCustomer(customer_id))
        
        delete_action = QAction("Delete Customer", self)
        delete_action.triggered.connect(lambda: self.deleteCustomer(customer_id))
        
        context_menu.addAction(edit_action)
        context_menu.addAction(delete_action)
        
        # Show context menu at cursor position
        context_menu.exec_(self.customers_table.viewport().mapToGlobal(position))
    
    def showProductContextMenu(self, position):
        """Show context menu for product table"""
        # Get the selected row
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Get product ID from the first column
        row = selected_rows[0].row()
        product_id_item = self.products_table.item(row, 0)
        if not product_id_item:
            return
            
        product_id = product_id_item.text()
        
        # Create context menu
        context_menu = QMenu(self)
        
        edit_action = QAction("Edit Product", self)
        edit_action.triggered.connect(lambda: self.editProduct(product_id))
        
        delete_action = QAction("Delete Product", self)
        delete_action.triggered.connect(lambda: self.deleteProduct(product_id))
        
        context_menu.addAction(edit_action)
        context_menu.addAction(delete_action)
        
        # Show context menu at cursor position
        context_menu.exec_(self.products_table.viewport().mapToGlobal(position))
        
    def importData(self, data_type):
        """Import data from CSV using MongoDB"""
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getOpenFileName(
                self, f"Import {data_type}", "",
                "CSV Files (*.csv);;All Files (*)", options=options
            )
            
            if not file_name:
                return
            
            import csv
            
            success_count = 0
            error_count = 0
            
            try:
                with open(file_name, 'r', newline='', encoding='utf-8') as csv_file:
                    csv_reader = csv.DictReader(csv_file)
                    
                    for row in csv_reader:
                        try:
                            if data_type == "Customers":
                                result = self.mongo_adapter.add_customer(
                                    row.get('Name', ''),
                                    row.get('Contact', ''),
                                    row.get('Address', '')
                                )
                            else:  # Products
                                result = self.mongo_adapter.add_product(
                                    row.get('Name', ''),
                                    row.get('Description', ''),
                                    float(row.get('Unit Price', 0)),
                                    row.get('Batch Number', ''),
                                    row.get('Expiry Date', '')
                                )
                            
                            if result:
                                success_count += 1
                            else:
                                error_count += 1
                                
                        except Exception as e:
                            error_count += 1
                            print(f"Error importing row: {e}")
                
                QMessageBox.information(
                    self, "Import Complete",
                    f"Import completed:\nSuccessful: {success_count}\nErrors: {error_count}"
                )
                
                # Reload data
                if data_type == "Customers":
                    self.loadCustomers()
                else:
                    self.loadProducts()
                    
            except Exception as e:
                QMessageBox.critical(self, "Import Error", f"Failed to read CSV file: {str(e)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Import Error", f"Failed to import data: {str(e)}")

    def exportData(self, data_type):
        """Export data to CSV using MongoDB"""
        try:
            options = QFileDialog.Options()
            default_name = f"{data_type.lower()}.csv"
            file_name, _ = QFileDialog.getSaveFileName(
                self, f"Export {data_type}", default_name,
                "CSV Files (*.csv);;All Files (*)", options=options
            )
            
            if not file_name:
                return
            
            # Add .csv extension if not present
            if not file_name.endswith('.csv'):
                file_name += '.csv'
            
            import csv
            
            # Get data based on type
            if data_type == "Customers":
                data = self.mongo_adapter.get_customers()
                headers = ["ID", "Name", "Contact", "Address"]
                
                # Write to CSV
                with open(file_name, 'w', newline='', encoding='utf-8') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(headers)
                    
                    for customer in data:
                        writer.writerow([
                            customer.get('id', ''),
                            customer.get('name', ''),
                            customer.get('contact', ''),
                            customer.get('address', '')
                        ])
            else:  # Products
                data = self.mongo_adapter.get_products()
                headers = ["ID", "Name", "Description", "Unit Price", "Batch Number", "Expiry Date"]
                
                # Write to CSV
                with open(file_name, 'w', newline='', encoding='utf-8') as csv_file:
                    writer = csv.writer(csv_file)
                    writer.writerow(headers)
                    
                    for product in data:
                        writer.writerow([
                            product.get('id', ''),
                            product.get('name', ''),
                            product.get('description', ''),
                            product.get('unit_price', 0),
                            product.get('batch_number', ''),
                            product.get('expiry_date', '')
                        ])
            
            QMessageBox.information(
                self, "Export Complete",
                f"{data_type} exported successfully to:\n{file_name}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")