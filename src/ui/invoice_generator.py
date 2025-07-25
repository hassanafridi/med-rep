from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QDateEdit, QGroupBox, QFormLayout,
    QPushButton, QDialog, QMessageBox, QFileDialog,
    QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QSpinBox, QDoubleSpinBox, QTextEdit, QCheckBox
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

class PDFInfoDialog(QDialog):
    """Dialog to collect additional information needed for PDF generation including company details"""
    
    def __init__(self, parent=None, existing_data=None):
        super().__init__(parent)
        self.setWindowTitle("PDF Invoice Information")
        self.setModal(True)
        self.setMinimumWidth(600)
        self.existing_data = existing_data or {}
        self.initUI()
    
    def initUI(self):
        """Initialize the dialog UI"""
        layout = QVBoxLayout()
        
        # Instructions
        instruction_label = QLabel("Please fill in the following information for the PDF invoice:")
        instruction_label.setStyleSheet("font-weight: bold; color: #4B0082; margin-bottom: 10px;")
        layout.addWidget(instruction_label)
        
        # Company Information Group
        company_group = QGroupBox("Company Information")
        company_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        company_layout = QFormLayout()
        
        # Company contact
        self.company_contact = QLineEdit()
        self.company_contact.setPlaceholderText("e.g., 0333-99-11-514")
        self.company_contact.setText(self.existing_data.get('company_contact', '0333-99-11-514'))
        self.company_contact.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        company_layout.addRow("Company Contact:", self.company_contact)
        
        # Company address
        self.company_address = QTextEdit()
        self.company_address.setMaximumHeight(80)
        self.company_address.setPlaceholderText("Enter your company address...")
        default_address = self.existing_data.get('company_address', 
            'info@trupharma.com')
        self.company_address.setText(default_address)
        self.company_address.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        company_layout.addRow("Company Address:", self.company_address)
        
        company_group.setLayout(company_layout)
        layout.addWidget(company_group)
        
        # Transport Information Group
        transport_group = QGroupBox("Transport & Delivery Information")
        transport_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        transport_layout = QFormLayout()
        
        self.transport_name = QLineEdit()
        self.transport_name.setPlaceholderText("e.g., Jawad Aslam, TCS, Standard Delivery")
        self.transport_name.setText(self.existing_data.get('transport_name', 'Standard Delivery'))
        self.transport_name.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        transport_layout.addRow("Transport Name:", self.transport_name)
        
        self.delivery_date = QDateEdit()
        self.delivery_date.setCalendarPopup(True)
        delivery_date_str = self.existing_data.get('delivery_date', '')
        if delivery_date_str:
            self.delivery_date.setDate(QDate.fromString(delivery_date_str, "dd-MM-yy"))
        else:
            self.delivery_date.setDate(QDate.currentDate())
        self.delivery_date.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        transport_layout.addRow("Delivery Date:", self.delivery_date)
        
        self.delivery_location = QLineEdit()
        self.delivery_location.setPlaceholderText("e.g., adda johal, Main Market Faisalabad")
        self.delivery_location.setText(self.existing_data.get('delivery_location', ''))
        self.delivery_location.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        transport_layout.addRow("Delivery Location:", self.delivery_location)
        
        transport_group.setLayout(transport_layout)
        layout.addWidget(transport_group)
        
        # Terms and Conditions Group
        terms_group = QGroupBox("Terms & Conditions")
        terms_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        terms_layout = QVBoxLayout()
        
        self.terms_text = QTextEdit()
        self.terms_text.setMaximumHeight(100)
        default_terms = self.existing_data.get('terms', 
            'Thank you for your business! Payment is due within 30 days.\n'
            'All products are subject to our standard terms and conditions.')
        self.terms_text.setText(default_terms)
        self.terms_text.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        terms_layout.addWidget(self.terms_text)
        
        terms_group.setLayout(terms_layout)
        layout.addWidget(terms_group)
        
        # Customer Information (read-only display)
        customer_group = QGroupBox("Customer Information (from invoice)")
        customer_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        customer_layout = QFormLayout()
        
        customer_name = self.existing_data.get('customer_name', 'N/A')
        customer_address = self.existing_data.get('customer_address', 'N/A')
        customer_contact = self.existing_data.get('customer_contact', 'N/A')
        
        customer_info_label = QLabel(f"Name: {customer_name}\nAddress: {customer_address}\nContact: {customer_contact}")
        customer_info_label.setStyleSheet("background-color: #f5f5f5; padding: 10px; border: 1px solid #ccc;")
        customer_layout.addRow("Customer:", customer_info_label)
        
        customer_group.setLayout(customer_layout)
        layout.addWidget(customer_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate PDF")
        self.generate_btn.clicked.connect(self.accept)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 10px 20px;
                font-weight: bold;
                font-size: 14px;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        
        self.cancel_btn = QPushButton("Cancel")
        self.cancel_btn.clicked.connect(self.reject)
        self.cancel_btn.setStyleSheet("""
            QPushButton {
                padding: 10px 20px;
                font-size: 14px;
                border-radius: 5px;
            }
        """)
        
        button_layout.addWidget(self.cancel_btn)
        button_layout.addWidget(self.generate_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def get_pdf_data(self):
        """Get the collected PDF data"""
        return {
            'company_contact': self.company_contact.text().strip() or '0333-99-11-514',
            'company_address': self.company_address.toPlainText().strip() or 'Main Market, Faisalabad\nPunjab, Pakistan',
            'transport_name': self.transport_name.text().strip() or 'Standard Delivery',
            'delivery_date': self.delivery_date.date().toString("dd-MM-yy"),
            'delivery_location': self.delivery_location.text().strip() or 'Customer Location',
            'terms': self.terms_text.toPlainText().strip()
        }

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
        
        self.subtotal_label = QLabel("Rs 0.00")
        self.subtotal_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Subtotal:", self.subtotal_label)
        
        self.tax_rate = QDoubleSpinBox()
        self.tax_rate.setRange(0, 100)
        self.tax_rate.setValue(0)
        self.tax_rate.setSuffix("%")
        self.tax_rate.valueChanged.connect(self.updateTotals)
        self.tax_rate.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        totals_layout.addRow("Tax Rate:", self.tax_rate)
        
        self.tax_amount_label = QLabel("Rs 0.00")
        self.tax_amount_label.setStyleSheet("font-weight: bold;")
        totals_layout.addRow("Tax Amount:", self.tax_amount_label)
        
        self.total_label = QLabel("Rs 0.00")
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
                        # Ensure MRP is properly typed and has fallback
                        raw_mrp = product.get('mrp', 0)
                        raw_unit_price = product.get('unit_price', 0)
                        
                        # Convert to float with proper validation
                        try:
                            unit_price = float(raw_unit_price) if raw_unit_price else 0.0
                            mrp = float(raw_mrp) if raw_mrp else 0.0
                            
                            # If MRP is 0 or missing, calculate as 120% of unit price
                            if mrp <= 0 and unit_price > 0:
                                mrp = unit_price * 1.2
                                print(f"Product {name}: MRP was {raw_mrp}, calculated as {mrp:.2f} from unit_price {unit_price}")
                            
                        except (ValueError, TypeError):
                            unit_price = 0.0
                            mrp = 0.0
                            print(f"Product {name}: Error converting prices, using defaults")
                        
                        # Enhanced display with MRP info
                        display_text = f"{name} (MRP: {mrp:.0f}, Rate: {unit_price:.0f}, Batch: {product.get('batch_number', 'N/A')})"
                        product_combo.addItem(display_text, product.get('id'))
                        
                        # Store complete product data including validated MRP
                        self.product_data[product.get('id')] = {
                            'id': product.get('id'),
                            'name': name,
                            'description': product.get('description', ''),
                            'unit_price': unit_price,
                            'mrp': mrp,  # Ensure this is always a valid float
                            'batch_number': product.get('batch_number', ''),
                            'expiry_date': product.get('expiry_date', '')
                        }
                        
                        print(f"Loaded product {name}: MRP={mrp} (type: {type(mrp)}), UnitPrice={unit_price} (type: {type(unit_price)})")
        except Exception as e:
            print(f"Error loading products: {e}")
            product_combo.addItem("Error loading products", None)
        
        layout.addRow("Product:", product_combo)
        
        # Description field (auto-filled based on product selection)
        description = QLineEdit()
        description.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        layout.addRow("Description:", description)
        
        # Unit price field (wholesale price, auto-filled based on product selection)
        unit_price = QDoubleSpinBox()
        unit_price.setMinimum(0.01)
        unit_price.setMaximum(99999.99)
        unit_price.setPrefix("Rs ")
        unit_price.setDecimals(2)
        unit_price.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        layout.addRow("Rate (UnitPrice):", unit_price)
        
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
                    mrp = product_info.get('mrp', 0)
                    product_description = f"{product_info.get('name', '')} - MRP: Rs{mrp:.0f} - Batch: {product_info.get('batch_number', 'N/A')}"
                description.setText(product_description)
                
                # Auto-fill wholesale price (unit_price)
                product_price = float(product_info.get('unit_price', 0))
                unit_price.setValue(product_price)
                
                print(f"Auto-filled product: {product_info.get('name')} - MRP: {product_info.get('mrp')}, Rate: {product_price}")
        
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
            
            # Get product info with validated MRP
            product_info = self.product_data.get(selected_product_id, {})
            product_name = product_info.get('name', 'Unknown Product')
            
            # Ensure MRP is properly retrieved and typed
            stored_mrp = product_info.get('mrp', 0)
            unit_price_value = unit_price.value()
            
            try:
                final_mrp = float(stored_mrp) if stored_mrp else unit_price_value * 1.2
            except (ValueError, TypeError):
                final_mrp = unit_price_value * 1.2
            
            print(f"Adding item - Product: {product_name}, Stored MRP: {stored_mrp}, Final MRP: {final_mrp}, Rate: {unit_price_value}")
            
            # Add item to table with proper MRP
            item = {
                'product': product_name,
                'description': description.text(),
                'quantity': quantity.value(),
                'unit_price': unit_price_value,  # Wholesale price for billing
                'mrp': final_mrp,  # Market retail price for display - ensure float
                'total': quantity.value() * unit_price_value,
                'product_id': selected_product_id,
                'batch_number': product_info.get('batch_number', ''),
                'expiry_date': product_info.get('expiry_date', '')
            }
            
            print(f"Final item data - MRP: {item['mrp']} (type: {type(item['mrp'])}), Rate: {item['unit_price']} (type: {type(item['unit_price'])})")
            
            self.addItemToTable(item)
            self.updateTotals()

    def addFromTransactions(self):
        """Add items from transactions in the database using MongoDB and get invoice number from notes"""
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
        transactions_table.setColumnCount(8)
        transactions_table.setHorizontalHeaderLabels([
            "ID", "Date", "Product", "Quantity", "Unit Price", "Total", "Invoice No", "Select"
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
        
        # Function to extract invoice number from notes
        def extract_invoice_number(notes):
            try:
                import re
                # Look for pattern like "Invoice: INV-20241201-123"
                pattern = r"Invoice:\s*(INV-\d{8}-\d{3})"
                match = re.search(pattern, notes)
                if match:
                    return match.group(1)
                return "No Invoice"
            except Exception as e:
                print(f"Error extracting invoice number: {e}")
                return "No Invoice"
        
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
                
                # Create product lookup with proper MRP handling
                product_lookup = {}
                for product in products:
                    product_id = str(product.get('id'))
                    raw_mrp = product.get('mrp', 0)
                    raw_unit_price = product.get('unit_price', 0)
                    
                    # Ensure proper type conversion with fallbacks
                    try:
                        unit_price = float(raw_unit_price) if raw_unit_price else 0.0
                        mrp = float(raw_mrp) if raw_mrp else 0.0
                        
                        # Calculate MRP if missing
                        if mrp <= 0 and unit_price > 0:
                            mrp = unit_price * 1.2
                    except (ValueError, TypeError):
                        unit_price = 0.0
                        mrp = 0.0
                    
                    product_lookup[product_id] = {
                        'name': product.get('name', 'Unknown'),
                        'mrp': mrp,
                        'unit_price': unit_price,
                        'batch_number': product.get('batch_number', ''),
                        'expiry_date': product.get('expiry_date', '')
                    }
                    
                    print(f"Transaction lookup - Product {product.get('name')}: MRP={mrp}, UnitPrice={unit_price}")
                
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
                        
                        # Extract invoice number from notes
                        invoice_number = extract_invoice_number(entry.get('notes', ''))
                        
                        filtered_transactions.append({
                            'id': entry.get('id', ''),
                            'date': entry_date,
                            'product_name': product_info.get('name', 'Unknown Product'),
                            'quantity': entry.get('quantity', 0),
                            'unit_price': entry.get('unit_price', 0),
                            'total': float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0)),
                            'invoice_number': invoice_number
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
                    transactions_table.setItem(row, 4, QTableWidgetItem(f"Rs {transaction['unit_price']:.2f}"))
                    transactions_table.setItem(row, 5, QTableWidgetItem(f"Rs {transaction['total']:.2f}"))
                    transactions_table.setItem(row, 6, QTableWidgetItem(transaction['invoice_number']))
                    
                    # Add checkbox for selection
                    check_box = QTableWidgetItem()
                    check_box.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                    check_box.setCheckState(Qt.Unchecked)
                    transactions_table.setItem(row, 7, check_box)
                
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
            selected_invoice_number = None
            for row in range(transactions_table.rowCount()):
                if transactions_table.item(row, 7) and transactions_table.item(row, 7).checkState() == Qt.Checked:
                    product_name = transactions_table.item(row, 2).text()
                    quantity = int(float(transactions_table.item(row, 3).text()))
                    unit_price = float(transactions_table.item(row, 4).text().replace('Rs ', ''))
                    invoice_number = transactions_table.item(row, 6).text()
                    
                    # Set invoice number from the first selected item
                    if selected_invoice_number is None and invoice_number != "No Invoice":
                        selected_invoice_number = invoice_number
                        self.invoice_number.setText(invoice_number)
                    
                    # Get product MRP from the enhanced lookup
                    product_mrp = unit_price  # Default fallback
                    product_id = None
                    batch_number = ""
                    
                    # Find the product in the lookup to get real MRP
                    try:
                        for pid, pinfo in product_lookup.items():
                            if pinfo['name'] == product_name:
                                product_id = pid
                                product_mrp = float(pinfo['mrp'])  # Already validated in lookup creation
                                batch_number = pinfo['batch_number']
                                print(f"Found product {product_name} in lookup: MRP={product_mrp}, UnitPrice={unit_price}")
                                break
                    except Exception as e:
                        print(f"Error fetching product MRP for {product_name}: {e}")
                        # Use fallback calculation
                        product_mrp = unit_price * 1.2
                    
                    item = {
                        'product': product_name,
                        'description': f"Transaction from {transactions_table.item(row, 1).text()}",
                        'quantity': quantity,
                        'unit_price': float(unit_price),  # Ensure float for billing price
                        'mrp': float(product_mrp),  # Ensure float for market retail price  
                        'total': quantity * unit_price,
                        'product_id': product_id,
                        'batch_number': batch_number
                    }
                    
                    print(f"Adding transaction item: {item['product']} - MRP: {item['mrp']} (type: {type(item['mrp'])}), Rate: {item['unit_price']} (type: {type(item['unit_price'])})")
                    selected_items.append(item)
            
            # Add selected items to invoice
            for item in selected_items:
                self.addItemToTable(item)
            
            self.updateTotals()

    def addItemToTable(self, item):
        """Add an item to the invoice table"""
        try:
            self.invoice_items.append(item)
            self.refreshItemsTable()
        except Exception as e:
            print(f"Error adding item to table: {e}")
    
    def refreshItemsTable(self):
        """Refresh the items table display"""
        try:
            self.items_table.setRowCount(len(self.invoice_items))
            
            for row, item in enumerate(self.invoice_items):
                # Product name
                self.items_table.setItem(row, 0, QTableWidgetItem(item.get('product', '')))
                
                # Description
                self.items_table.setItem(row, 1, QTableWidgetItem(item.get('description', '')))
                
                # Quantity
                self.items_table.setItem(row, 2, QTableWidgetItem(str(item.get('quantity', 0))))
                
                # Unit Price
                self.items_table.setItem(row, 3, QTableWidgetItem(f"Rs {item.get('unit_price', 0):.2f}"))
                
                # Total
                self.items_table.setItem(row, 4, QTableWidgetItem(f"Rs {item.get('total', 0):.2f}"))
                
                # Remove button
                remove_btn = QPushButton("Remove")
                remove_btn.clicked.connect(lambda checked, r=row: self.removeItem(r))
                remove_btn.setStyleSheet("background-color: #ff4444; color: white; padding: 4px;")
                self.items_table.setCellWidget(row, 5, remove_btn)
        except Exception as e:
            print(f"Error refreshing items table: {e}")
    
    def removeItem(self, row):
        """Remove an item from the invoice"""
        try:
            if 0 <= row < len(self.invoice_items):
                del self.invoice_items[row]
                self.refreshItemsTable()
                self.updateTotals()
        except Exception as e:
            print(f"Error removing item: {e}")
    
    def updateTotals(self):
        """Update the totals display"""
        try:
            if not self.invoice_items:
                self.subtotal_label.setText("Rs 0.00")
                self.tax_amount_label.setText("Rs 0.00")
                self.total_label.setText("Rs 0.00")
                return
            
            # Calculate subtotal
            subtotal = sum(item.get('total', 0) for item in self.invoice_items)
            
            # Calculate tax
            tax_rate = self.tax_rate.value() / 100
            tax_amount = subtotal * tax_rate
            
            # Calculate total
            total = subtotal + tax_amount
            
            # Update labels
            self.subtotal_label.setText(f"Rs {subtotal:.2f}")
            self.tax_amount_label.setText(f"Rs {tax_amount:.2f}")
            self.total_label.setText(f"Rs {total:.2f}")
            
        except Exception as e:
            print(f"Error updating totals: {e}")
    
    def clearItems(self):
        """Clear all items from the invoice"""
        try:
            reply = QMessageBox.question(
                self, "Clear Items",
                "Are you sure you want to clear all items?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.invoice_items.clear()
                self.refreshItemsTable()
                self.updateTotals()
        except Exception as e:
            print(f"Error clearing items: {e}")

    def generateInvoiceHtml(self, company_contact="0333-99-11-514", company_address="Main Market, Faisalabad\nPunjab, Pakistan"):
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
        
        # Convert amount to words from total
        amount_in_words = self.amount_to_words(total)
        
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
            
            # Use MRP for display, wholesale price for calculations
            mrp_price = item.get('mrp', item['unit_price'])  # Fallback to unit_price if MRP not available
            unit_price = item['unit_price']  # This is the actual rate used for billing
            
            # Calculate discount (if any)
            discount_percent = 0  # Can be made configurable
            discount_amount = item['total'] * (discount_percent / 100)
            final_amount = item['total'] - discount_amount
            
            items_html += f"""
                <tr>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{item_number}</td>
                    <td style="border: 1px solid #666; padding: 8px;">{item['product']}{batch_info}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{mrp_price:.0f}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{item['quantity']}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{unit_price:.0f}</td>
                    <td style="text-align: center; border: 1px solid #666; padding: 8px;">{discount_percent}%</td>
                    <td style="text-align: right; border: 1px solid #666; padding: 8px;">{final_amount:.0f}</td>
                </tr>
            """
            item_number += 1
        
        # Get transport/delivery info (can be made configurable)
        transport_name = "Standard Delivery"
        delivery_date = self.due_date.date().toString("dd-MM-yy")
        delivery_location = customer_address.split('\n')[0] if customer_address else "Customer Location"
        
        # Get current date for invoice
        current_date = QDate.currentDate().toString("dd-MM-yy")
        invoice_number = self.invoice_number.text()
        
        # Format company address for HTML
        company_address_html = company_address.replace('\n', '<br>')
        
        # Generate professional pharmaceutical invoice HTML
        html = f"""
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <title>Bill/Cash Memo</title>
    <style>
      body {{
        font-family: Arial, sans-serif;
        margin: 0;
        padding: 10px;
        font-size: 12px;
      }}
      .invoice-container {{
        border: 2px solid #000;
        padding: 0;
        max-width: 210mm;
        margin: 0 auto;
      }}
      .header {{
        background-color: white;
        color: black;
        padding: 10px;
        text-align: center;
        font-weight: bold;
        font-size: 16px;
      }}
      .company-header {{
        background-color: #ffffff;
        color: rgb(0, 0, 0);
        padding: 10px 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
      }}
      .company-logo {{
        font-size: 20px;
        font-weight: bold;
        display: flex;
        align-items: center;
        color: rgb(132 125 230);
      }}
      .company-contact {{
        text-align: right;
        font-size: 10px;
      }}

      .bill-headers {{
        display: flex;
        border: 1px solid #000;
        background-color: #f4f0ff;
      }}

      .bill-details {{
        display: flex;
        border: 1px solid #000;
        border-top: none;
        background-color: #f4f0ff;
      }}

      .bill-to,
      .transport-details,
      .invoice-details {{
        flex: 1;
        padding: 10px;
        border-right: 1px solid #000;
        background-color: #fff;
      }}

      .section-header {{
        background-color: rgb(132 125 230);
        color: white;
        padding: 4px 8px;
        font-weight: bold;
        font-size: 11px;
        width: 100%;
        border-right: 1px solid #000;
      }}

      .detail-row {{
        font-size: 11px;
        margin-top: 4px;
      }}

      .bold {{
        font-weight: bold;
      }}

      .items-table {{
        width: 100%;
        border-collapse: collapse;
        margin: 0;
      }}
      .items-table th {{
        background-color: rgb(132 125 230);
        color: white;
        padding: 6px;
        border: 1px solid #000;
        text-align: center;
        font-size: 11px;
        font-weight: bold;
      }}
      .items-table td {{
        padding: 6px;
        border: 1px solid #000;
        font-size: 11px;
        text-align: center;
      }}
      .items-table td:nth-child(2) {{
        text-align: left;
      }}
            .amounts-section {{
        width: 270px;
        margin-left: auto;
        border-left: 1px solid #000;
      }}
            .amounts-header {{
        background-color: rgb(132 125 230);
        color: white;
        padding: 6px;
        text-align: center;
        font-weight: bold;
        font-size: 11px;
      }}
      .amount-row {{
        display: flex;
        justify-content: space-between;
        padding: 4px 10px;
        border-bottom: 1px solid #000;
        font-size: 11px;
      }}
      .amounts-section {{
        width: 270px;
        margin-left: auto;
        border-left: 1px solid #000;
      }}
      .amounts-header {{
        background-color: rgb(132 125 230);
        color: white;
        padding: 6px;
        text-align: center;
        font-weight: bold;
        font-size: 11px;
      }}
      .amount-row {{
        display: flex;
        justify-content: space-between;
        padding: 4px 10px;
        border-bottom: 1px solid #000;
        font-size: 11px;
      }}
      .amount-words {{
        background-color: #f8f8f8;
        color: rgb(0, 0, 0);
        padding: 8px;
        text-align: center;
        font-weight: bold;
        font-size: 11px;
        width: 506px;
        border-right: #000 solid 1px;
      }}
      .amount-word-header {{
        background-color: rgb(132 125 230);
        color: white;
        width: 100%;
        border: #000 solid 1px;
        padding: 3px 13px 3px 3px;
        margin-top: -9px;
        margin-left: -9px;
      }}
      .terms-section {{
        display: flex;
        border-top: 1px solid #000;
      }}
      .term-section-header {{
        background-color: rgb(132 125 230);
        color: white;
        padding: 5px 10px 5px 13px;
        font-weight: bold;
        font-size: 11px;
        width: 100%;
        margin-top: -9px;
        margin-left: -12px;
      }}
      .terms {{
        flex: 2;
        padding: 9px 11px 11px 12px;
        font-size: 9px;
        border-right: 1px solid #000;
      }}
      .signature-section {{
        flex: 1;
        padding: 10px;
        text-align: center;
        font-size: 10px;
      }}
      .bold {{
        font-weight: bold;
      }}
      .right-align {{
        text-align: right;
      }}
      .detail-row {{
        margin-bottom: 3px;
        font-size: 10px;
      }}
    </style>
  </head>
  <body>
    <!-- Header -->
    <div class="header">Bill/Cash Memo</div>
    <div class="invoice-container">
      <!-- Company Header -->
      <div class="company-header">
        <div class="company-logo">Tru-Pharma</div>
        <div class="company-contact">
          {company_contact}<br />
          {company_address_html}
        </div>
      </div>

      <div class="bill-headers">
        <div class="section-header">Bill To</div>
        <div class="section-header">Transportation Details</div>
        <div class="section-header">Invoice Details</div>
      </div>

      <!-- Bill Details Section -->
      <div class="bill-details">
        <div class="bill-to">
          <div class="bold">{customer_name}</div>
          <div style="margin-top: 5px; font-size: 10px">{customer_address}</div>
        </div>

        <div class="transport-details">
          <div class="detail-row">
            <span class="bold">Transport Name:</span> {transport_name}
          </div>
          <div class="detail-row">
            <span class="bold">Delivery Date:</span> {delivery_date}
          </div>
          <div class="detail-row">
            <span class="bold">Delivery location:</span> {delivery_location}
          </div>
        </div>

        <div class="invoice-details">
          <div class="detail-row">
            <span class="bold">Invoice No.:</span> {invoice_number}
          </div>
          <div class="detail-row">
            <span class="bold">Date:</span> {current_date}
          </div>
        </div>
      </div>

      <!-- Items Section -->
      <table class="items-table">
        <thead>
          <tr>
            <th style="width: 5%">#</th>
            <th style="width: 35%">Item name</th>
            <th style="width: 12%">MRP</th>
            <th style="width: 12%">Quantity</th>
            <th style="width: 12%">Rate</th>
            <th style="width: 12%">Discount</th>
            <th style="width: 12%">Amount</th>
          </tr>
        </thead>
        <tbody>
          {items_html}
          <tr>
            <td colspan="6" style="text-align: right; font-weight: bold">
              Total
            </td>
            <td style="text-align: right; font-weight: bold">{subtotal:.0f}</td>
          </tr>
        </tbody>
      </table>

      <!-- Amounts Section -->
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

      <!-- Amount in Words -->
      <div class="amount-words">
        <div class="bold amount-word-header" style="margin-bottom: 3px">
          Invoice Amount In Words
        </div>
        <div>{amount_in_words}</div>
      </div>

      <!-- Terms and Signature -->
      <div class="terms-section">
        <div class="terms">
          <div class="term-section-header" style="margin-bottom: 8px">
            Terms and Conditions
          </div>
          <div style="text-align: justify; line-height: 1.3">
            Form 2-A, as specified under Rules 19 and 30, pertains to the
            warranty provided under Section 23(1)(1) of the Drug Act 1976. This
            document, issued by Tru_pharma, serves as an assurance of the
            quality and effectiveness of products. The warranty ensures that the
            drugs manufactured by Tru_pharma comply with the prescribed
            standards and meet the necessary regulatory requirements. By
            utilizing Form 2-A, Tru_pharma demonstrates its commitment to
            delivering safe and reliable pharmaceuticals to consumers. This form
            acts as a legal document, emphasizing Tru_pharma's
            responsibility and accountability in maintaining the highest
            standards in drug manufacturing and distribution.
          </div>
        </div>

        <div class="signature-section">
          <div style="margin-bottom: 15px">For : Tru_pharma</div>
          <div
            style="
              margin-top: 60px;
              border-top: 1px solid #000;
              padding-top: 8px;
            "
          >
            <div class="bold">Authorized Signatory</div>
          </div>
        </div>
      </div>
    </div>
  </body>
</html>
        """
        
        return html
    
    def amount_to_words(self, amount):
        """Convert amount to words"""
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

    def prepareInvoiceData(self, pdf_info=None):
        """Prepare invoice data for PDF generation with additional PDF info"""
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

        # For manual invoice generation, assume it's a credit entry with customizable received amount
        # This can be enhanced with additional UI controls if needed
        received_amount = 0.0  # Default for manual invoices
        balance_amount = total  # Full amount goes to balance for manual invoices
        
        # Prepare items data with MRP and consistent structure
        items_data = []
        for item in self.invoice_items:
            # Ensure both 'amount' and 'total' keys exist for compatibility
            item_amount = item.get('total', item.get('amount', 0))
            
            items_data.append({
                'product_name': item['product'],
                'batch_number': item.get('batch_number', 'N/A'),
                'product_id': item.get('product_id', 'N/A'),
                'quantity': item['quantity'],
                'unit_price': item['unit_price'],  # Wholesale/billing price
                'mrp': item.get('mrp', item['unit_price']),  # Market retail price for display
                'discount': 0,  # Can be made configurable
                'amount': item_amount,  # Primary amount field
                'total': item_amount   # Compatibility field
            })
        
        # Use PDF info if provided, otherwise use defaults
        if pdf_info:
            company_contact = pdf_info['company_contact']
            company_address = pdf_info['company_address']
            transport_name = pdf_info['transport_name']
            delivery_date = pdf_info['delivery_date']
            delivery_location = pdf_info['delivery_location']
            terms = pdf_info['terms']
        else:
            company_contact = '0333-99-11-514'
            company_address = 'info@trupharma.com'
            transport_name = 'Standard Delivery'
            delivery_date = self.due_date.date().toString("dd-MM-yy")
            delivery_location = customer_address.split('\n')[0] if customer_address else 'Customer Location'
            terms = self.notes.toPlainText()
        
        return {
            'company_name': 'Tru_pharma',  # Hardcoded
            'company_logo': None,  # No logo needed
            'company_contact': company_contact,  # From dialog
            'company_address': company_address,  # From dialog
            'customer_info': {
                'name': customer_name,
                'address': customer_address,
                'contact': customer_contact
            },
            'transport_info': {
                'transport_name': transport_name,
                'delivery_date': delivery_date,
                'delivery_location': delivery_location
            },
            'invoice_details': {
                'invoice_number': self.invoice_number.text(),
                'invoice_date': QDate.currentDate().toString("dd-MM-yy")
            },
            'items': items_data,
            'terms': terms,
            'total_amount': total,
            'received_amount': received_amount,  # Use calculated received amount
            'balance_amount': balance_amount     # Use calculated balance amount
        }

    def previewInvoice(self):
        """Preview the invoice"""
        if not self.invoice_items:
            QMessageBox.warning(self, "No Items", "Please add at least one item to the invoice.")
            return
        
        # Get customer info for the dialog
        customer_name = self.customer_combo.currentText()
        customer_info = self.customer_data.get(customer_name, {})
        
        # Prepare existing data for the dialog
        existing_data = {
            'customer_name': customer_name,
            'customer_address': customer_info.get('address', ''),
            'customer_contact': customer_info.get('contact', ''),
            'terms': self.notes.toPlainText(),
            'transport_name': 'Standard Delivery',
            'delivery_location': customer_info.get('address', '').split('\n')[0] if customer_info.get('address') else '',
            'company_contact': '0333-99-11-514',
            'company_address': 'info@trupharma.com'
        }
        
        # Show PDF info dialog
        pdf_dialog = PDFInfoDialog(self, existing_data)
        if pdf_dialog.exec_() == QDialog.Accepted:
            # Get PDF-specific information
            pdf_info = pdf_dialog.get_pdf_data()
            
            # Generate HTML with company details
            invoice_html = self.generateInvoiceHtml(pdf_info['company_contact'], pdf_info['company_address'])
            preview_dialog = InvoicePreviewDialog(invoice_html, self)
            preview_dialog.exec_()
    
    def saveAsPdf(self):
        """Save the invoice as a PDF file using reportlab with dialog for additional info"""
        if not self.invoice_items:
            QMessageBox.warning(self, "No Items", "Please add at least one item to the invoice.")
            return
        
        # Get customer info for the dialog
        customer_name = self.customer_combo.currentText()
        customer_info = self.customer_data.get(customer_name, {})
        
        # Prepare existing data for the dialog
        existing_data = {
            'customer_name': customer_name,
            'customer_address': customer_info.get('address', ''),
            'customer_contact': customer_info.get('contact', ''),
            'terms': self.notes.toPlainText(),
            'transport_name': 'Standard Delivery',
            'delivery_location': customer_info.get('address', '').split('\n')[0] if customer_info.get('address') else '',
            'company_contact': '0333-99-11-514',
            'company_address': 'info@trupharma.com'
        }
        
        # Show PDF info dialog
        pdf_dialog = PDFInfoDialog(self, existing_data)
        if pdf_dialog.exec_() != QDialog.Accepted:
            return
        
        # Get PDF-specific information
        pdf_info = pdf_dialog.get_pdf_data()
        
        # Get file save location
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self, "Save Invoice as PDF", f"{self.invoice_number.text()}.pdf",
            "PDF Files (*.pdf);;All Files (*)", options=options
        )
        
        if file_name:
            try:
                # Prepare invoice data for PDF generator with additional info
                invoice_data = self.prepareInvoiceData(pdf_info)
                
                # Generate PDF using the improved PDF generator
                from src.utils.pdf_generator import ImprovedPDFGenerator
                pdf_generator = ImprovedPDFGenerator()
                success = pdf_generator.generate_invoice_pdf(invoice_data, file_name)
                
                if success:
                    QMessageBox.information(
                        self, "PDF Saved",
                        f"Invoice saved as PDF:\n{file_name}\n\n"
                        f"Company: {pdf_info['company_contact']}\n"
                        f"Transport: {pdf_info['transport_name']}\n"
                        f"Delivery: {pdf_info['delivery_location']} ({pdf_info['delivery_date']})\n"
                        f"Total Amount: Rs {invoice_data['total_amount']:.2f}"
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
    
    def printInvoice(self):
        """Print the invoice using reportlab PDF with dialog for additional info"""
        if not self.invoice_items:
            QMessageBox.warning(self, "No Items", "Please add at least one item to the invoice.")
            return
        
        # Get customer info for the dialog
        customer_name = self.customer_combo.currentText()
        customer_info = self.customer_data.get(customer_name, {})
        
        # Prepare existing data for the dialog
        existing_data = {
            'customer_name': customer_name,
            'customer_address': customer_info.get('address', ''),
            'customer_contact': customer_info.get('contact', ''),
            'terms': self.notes.toPlainText(),
            'transport_name': 'Standard Delivery',
            'delivery_location': customer_info.get('address', '').split('\n')[0] if customer_info.get('address') else '',
            'company_contact': '0333-99-11-514',
            'company_address': 'info@trupharma.com'
        }
        
        # Show PDF info dialog
        pdf_dialog = PDFInfoDialog(self, existing_data)
        pdf_dialog.setWindowTitle("Print Invoice Information")
        if pdf_dialog.exec_() != QDialog.Accepted:
            return
        
        # Get PDF-specific information
        pdf_info = pdf_dialog.get_pdf_data()
        
        try:
            # Create temporary PDF file
            temp_dir = tempfile.gettempdir()
            temp_pdf = os.path.join(temp_dir, f"temp_invoice_{self.invoice_number.text()}.pdf")
            
            # Prepare invoice data with additional info
            invoice_data = self.prepareInvoiceData(pdf_info)
            
            # Generate PDF using the improved PDF generator
            from src.utils.pdf_generator import ImprovedPDFGenerator
            pdf_generator = ImprovedPDFGenerator()
            success = pdf_generator.generate_invoice_pdf(invoice_data, temp_pdf)
            
            if success:
                # Open the PDF file for printing
                import subprocess
                if sys.platform == "win32":
                    os.startfile(temp_pdf)
                elif sys.platform == "darwin":
                    subprocess.call(["open", temp_pdf])
                else:
                    subprocess.call(["xdg-open", temp_pdf])
                    
                QMessageBox.information(
                    self, "Print Ready",
                    f"PDF generated and opened for printing:\n{temp_pdf}\n\n"
                    f"Company: {pdf_info['company_contact']}\n"
                    f"Transport: {pdf_info['transport_name']}\n"
                    f"Delivery: {pdf_info['delivery_location']} ({pdf_info['delivery_date']})"
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