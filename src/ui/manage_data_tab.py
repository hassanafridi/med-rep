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
from src.ui.import_export import ImportDialog  # Add this line


# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Database

class CustomerDialog(QDialog):
    def __init__(self, parent=None, customer_data=None):
        super().__init__(parent)
        self.customer_data = customer_data  # (id, name, contact, address)
        self.setWindowTitle("Customer Details")
        self.setMinimumWidth(400)
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QFormLayout()
        
        # Customer name
        self.name_input = QLineEdit()
        if self.customer_data:
            self.name_input.setText(self.customer_data[1])
        layout.addRow("Name:", self.name_input)
        
        # Contact
        self.contact_input = QLineEdit()
        if self.customer_data:
            self.contact_input.setText(self.customer_data[2] or "")
        layout.addRow("Contact:", self.contact_input)
        
        # Address
        self.address_input = QTextEdit()
        self.address_input.setMaximumHeight(100)
        if self.customer_data:
            self.address_input.setText(self.customer_data[3] or "")
        layout.addRow("Address:", self.address_input)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
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
        self.setWindowTitle("Product Details")
        self.setMinimumWidth(500)
        self.initUI()
        
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QFormLayout()
        
        # Product name
        self.name_input = QLineEdit()
        if self.product_data:
            self.name_input.setText(self.product_data[1])
        layout.addRow("Name:", self.name_input)
        
        # Description
        self.description_input = QTextEdit()
        self.description_input.setMaximumHeight(100)
        if self.product_data:
            self.description_input.setText(self.product_data[2] or "")
        layout.addRow("Description:", self.description_input)
        
        # Unit price
        self.price_input = QDoubleSpinBox()
        self.price_input.setMinimum(0.01)
        self.price_input.setMaximum(99999.99)
        self.price_input.setPrefix("Rs. ")
        self.price_input.setDecimals(2)
        if self.product_data:
            self.price_input.setValue(self.product_data[3])
        layout.addRow("Unit Price:", self.price_input)
        
        # Batch number
        self.batch_input = QLineEdit()
        self.batch_input.setPlaceholderText("e.g., MCR-2024-001")
        if self.product_data:
            self.batch_input.setText(self.product_data[4] or "")
        layout.addRow("Batch Number:", self.batch_input)
        
        # Expiry date
        self.expiry_input = QDateEdit()
        self.expiry_input.setCalendarPopup(True)
        self.expiry_input.setDate(QDate.currentDate().addYears(1))  # Default to 1 year from now
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
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Create tabs for customers and products
        tabs = QTabWidget()
        
        # Customers tab
        customers_tab = QWidget()
        customers_layout = QVBoxLayout()
        
        # Customer controls
        customer_controls = QHBoxLayout()
        
        self.customer_search = QLineEdit()
        self.customer_search.setPlaceholderText("Search customers...")
        self.customer_search.textChanged.connect(self.filterCustomers)
        
        self.add_customer_btn = QPushButton("Add Customer")
        self.add_customer_btn.clicked.connect(self.addCustomer)
        
        self.import_customers_btn = QPushButton("Import")
        self.import_customers_btn.clicked.connect(lambda: self.importData("Customers"))
        
        self.export_customers_btn = QPushButton("Export")
        self.export_customers_btn.clicked.connect(lambda: self.exportData("Customers"))
            
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
        
        self.add_product_btn = QPushButton("Add Product")
        self.add_product_btn.clicked.connect(self.addProduct)
        
        self.check_expiry_btn = QPushButton("Check Expiry")
        self.check_expiry_btn.clicked.connect(self.checkExpiredProducts)
        
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
        """Load customers from database"""
        try:
            self.db.connect()
            
            # Get all customers
            self.db.cursor.execute('SELECT id, name, contact, address FROM customers ORDER BY name')
            customers = self.db.cursor.fetchall()
            
            # Clear and set row count
            self.customers_table.setRowCount(0)
            self.customers_table.setRowCount(len(customers))
            
            # Fill table with data
            for row, customer in enumerate(customers):
                for col, value in enumerate(customer):
                    item = QTableWidgetItem(str(value) if value else "")
                    self.customers_table.setItem(row, col, item)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customers: {str(e)}")
        finally:
            self.db.close()
    
    def loadProducts(self):
        """Load products from database"""
        try:
            self.db.connect()
            
            # Get all products with new fields
            self.db.cursor.execute(
                'SELECT id, name, description, unit_price, batch_number, expiry_date FROM products ORDER BY name, expiry_date DESC'
            )
            products = self.db.cursor.fetchall()
            
            # Clear and set row count
            self.products_table.setRowCount(0)
            self.products_table.setRowCount(len(products))
            
            # Fill table with data
            for row, product in enumerate(products):
                for col, value in enumerate(product):
                    if col == 3:  # Format price
                        text = f"Rs. {value:.2f}"
                    elif col == 5:  # Format expiry date
                        try:
                            expiry_date = QDate.fromString(str(value), "yyyy-MM-dd")
                            if expiry_date.isValid():
                                # Check if expired and highlight
                                if expiry_date < QDate.currentDate():
                                    text = f"{value} (EXPIRED)"
                                elif expiry_date < QDate.currentDate().addDays(30):
                                    text = f"{value} (EXPIRING SOON)"
                                else:
                                    text = str(value)
                            else:
                                text = str(value)
                        except:
                            text = str(value) if value else ""
                    else:
                        text = str(value) if value else ""
                    
                    item = QTableWidgetItem(text)
                    
                    # Color code expired/expiring products
                    if col == 5 and "EXPIRED" in text:
                        item.setBackground(Qt.red)
                    elif col == 5 and "EXPIRING SOON" in text:
                        item.setBackground(Qt.yellow)
                    
                    self.products_table.setItem(row, col, item)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load products: {str(e)}")
        finally:
            self.db.close()
    
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
        """Add a new customer"""
        dialog = CustomerDialog(self)
        if dialog.exec_() == QDialog.Accepted:
            customer_data = dialog.getCustomerData()
            
            # Validate input
            if not customer_data['name']:
                QMessageBox.warning(self, "Validation Error", "Customer name is required.")
                return
            
            try:
                self.db.connect()
                
                # Insert new customer
                self.db.cursor.execute(
                    'INSERT INTO customers (name, contact, address) VALUES (?, ?, ?)',
                    (customer_data['name'], customer_data['contact'], customer_data['address'])
                )
                
                self.db.conn.commit()
                QMessageBox.information(self, "Success", "Customer added successfully.")
                
                # Reload customers
                self.loadCustomers()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add customer: {str(e)}")
            finally:
                self.db.close()
    
    def editCustomer(self, customer_id):
        """Edit an existing customer"""
        try:
            self.db.connect()
            
            # Get customer data
            self.db.cursor.execute(
                'SELECT id, name, contact, address FROM customers WHERE id = ?',
                (customer_id,)
            )
            
            customer = self.db.cursor.fetchone()
            
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
                
                # Update customer
                self.db.cursor.execute(
                    'UPDATE customers SET name = ?, contact = ?, address = ? WHERE id = ?',
                    (customer_data['name'], customer_data['contact'], customer_data['address'], customer_id)
                )
                
                self.db.conn.commit()
                QMessageBox.information(self, "Success", "Customer updated successfully.")
                
                # Reload customers
                self.loadCustomers()
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update customer: {str(e)}")
        finally:
            self.db.close()
    
    def deleteCustomer(self, customer_id):
        """Delete a customer"""
        try:
            self.db.connect()
            
            # Check if customer has entries
            self.db.cursor.execute('SELECT COUNT(*) FROM entries WHERE customer_id = ?', (customer_id,))
            count = self.db.cursor.fetchone()[0]
            
            if count > 0:
                QMessageBox.warning(
                    self, "Cannot Delete",
                    f"This customer has {count} entries. Delete all entries first."
                )
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                "Are you sure you want to delete this customer?\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Delete customer
                self.db.cursor.execute('DELETE FROM customers WHERE id = ?', (customer_id,))
                self.db.conn.commit()
                
                QMessageBox.information(self, "Success", "Customer deleted successfully.")
                
                # Reload customers
                self.loadCustomers()
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete customer: {str(e)}")
        finally:
            self.db.close()
    
    def addProduct(self):
        """Add a new product"""
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
                self.db.connect()
                
                # Check if batch number already exists
                self.db.cursor.execute(
                    'SELECT COUNT(*) FROM products WHERE batch_number = ?',
                    (product_data['batch_number'],)
                )
                
                if self.db.cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Validation Error", "Batch number already exists. Please use a unique batch number.")
                    return
                
                # Insert new product
                self.db.cursor.execute(
                    'INSERT INTO products (name, description, unit_price, batch_number, expiry_date) VALUES (?, ?, ?, ?, ?)',
                    (product_data['name'], product_data['description'], product_data['unit_price'], 
                     product_data['batch_number'], product_data['expiry_date'])
                )
                
                self.db.conn.commit()
                QMessageBox.information(self, "Success", "Product added successfully.")
                
                # Reload products
                self.loadProducts()
                
            except Exception as e:
                QMessageBox.critical(self, "Database Error", f"Failed to add product: {str(e)}")
            finally:
                self.db.close()
    
    def editProduct(self, product_id):
        """Edit an existing product"""
        try:
            self.db.connect()
            
            # Get product data
            self.db.cursor.execute(
                'SELECT id, name, description, unit_price, batch_number, expiry_date FROM products WHERE id = ?',
                (product_id,)
            )
            
            product = self.db.cursor.fetchone()
            
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
                self.db.cursor.execute(
                    'SELECT COUNT(*) FROM products WHERE batch_number = ? AND id != ?',
                    (product_data['batch_number'], product_id)
                )
                
                if self.db.cursor.fetchone()[0] > 0:
                    QMessageBox.warning(self, "Validation Error", "Batch number already exists. Please use a unique batch number.")
                    return
                
                # Update product
                self.db.cursor.execute(
                    'UPDATE products SET name = ?, description = ?, unit_price = ?, batch_number = ?, expiry_date = ? WHERE id = ?',
                    (product_data['name'], product_data['description'], product_data['unit_price'], 
                     product_data['batch_number'], product_data['expiry_date'], product_id)
                )
                
                self.db.conn.commit()
                QMessageBox.information(self, "Success", "Product updated successfully.")
                
                # Reload products
                self.loadProducts()
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to update product: {str(e)}")
        finally:
            self.db.close()
    
    def deleteProduct(self, product_id):
        """Delete a product"""
        try:
            self.db.connect()
            
            # Check if product has entries
            self.db.cursor.execute('SELECT COUNT(*) FROM entries WHERE product_id = ?', (product_id,))
            count = self.db.cursor.fetchone()[0]
            
            if count > 0:
                QMessageBox.warning(
                    self, "Cannot Delete",
                    f"This product has {count} entries. Delete all entries first."
                )
                return
            
            # Confirm deletion
            reply = QMessageBox.question(
                self, "Confirm Deletion",
                "Are you sure you want to delete this product?\nThis action cannot be undone.",
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Delete product
                self.db.cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
                self.db.conn.commit()
                
                QMessageBox.information(self, "Success", "Product deleted successfully.")
                
                # Reload products
                self.loadProducts()
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to delete product: {str(e)}")
        finally:
            self.db.close()
    
    def checkExpiredProducts(self):
        """Check for expired or expiring products"""
        try:
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            upcoming_date = QDate.currentDate().addDays(30).toString("yyyy-MM-dd")
            
            expired_products = self.db.get_expired_products(current_date)
            
            self.db.connect()
            self.db.cursor.execute(
                'SELECT id, name, batch_number, expiry_date FROM products WHERE expiry_date > ? AND expiry_date <= ? ORDER BY expiry_date',
                (current_date, upcoming_date)
            )
            expiring_products = self.db.cursor.fetchall()
            
            message = ""
            
            if expired_products:
                message += "EXPIRED PRODUCTS:\n"
                for product in expired_products:
                    message += f"• {product[1]} (Batch: {product[2]}) - Expired: {product[3]}\n"
                message += "\n"
            
            if expiring_products:
                message += "PRODUCTS EXPIRING IN 30 DAYS:\n"
                for product in expiring_products:
                    message += f"• {product[1]} (Batch: {product[2]}) - Expires: {product[3]}\n"
            
            if not message:
                message = "No expired or expiring products found."
            
            QMessageBox.information(self, "Product Expiry Check", message)
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to check expired products: {str(e)}")
        finally:
            self.db.close()
    
    def showCustomerContextMenu(self, position):
        """Show context menu for customer table"""
        # Get the selected row
        selected_rows = self.customers_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Get customer ID from the first column
        row = selected_rows[0].row()
        customer_id = int(self.customers_table.item(row, 0).text())
        
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
        product_id = int(self.products_table.item(row, 0).text())
        
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
        """Import data from CSV"""
        dialog = ImportDialog(self, self.db.db_path)
        if dialog.exec_() == QDialog.Accepted:
            # Reload data
            if data_type == "Customers":
                self.loadCustomers()
            else:
                self.loadProducts()

    def exportData(self, data_type):
        """Export data to CSV"""
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
        
        try:
            self.db.connect()
            
            # Get data based on type
            if data_type == "Customers":
                self.db.cursor.execute('SELECT id, name, contact, address FROM customers ORDER BY name')
                data = self.db.cursor.fetchall()
                headers = ["ID", "Name", "Contact", "Address"]
                
            else:  # Products
                self.db.cursor.execute('SELECT id, name, description, unit_price, batch_number, expiry_date FROM products ORDER BY name, expiry_date DESC')
                data = self.db.cursor.fetchall()
                headers = ["ID", "Name", "Description", "Unit Price", "Batch Number", "Expiry Date"]
            
            # Write to CSV
            with open(file_name, 'w', newline='', encoding='utf-8') as csv_file:
                writer = csv.writer(csv_file)
                
                # Write header
                writer.writerow(headers)
                
                # Write data rows
                for row in data:
                    writer.writerow(row)
            
            QMessageBox.information(
                self, "Export Complete",
                f"{data_type} exported successfully to:\n{file_name}"
            )
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
        finally:
            self.db.close()