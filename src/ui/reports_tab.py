from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
    QPushButton, QDateEdit, QGroupBox, QFormLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QCheckBox, QSpinBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
from PyQt5.QtGui import QColor
import sys
import os
import datetime
import csv

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter
from src.utils.pdf_generator import PDFGenerator

class ReportsTab(QWidget):
    def __init__(self, mongo_adapter=None):
        super().__init__()
        try:
            self.mongo_adapter = mongo_adapter or MongoAdapter()
            self.initUI()
        except Exception as e:
            print(f"Error initializing Reports tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Reports tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the reports tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.mongo_adapter)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Reports tab: {str(e)}")
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Reports & Analytics - ")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; color: #4B0082; margin-bottom: 10px;")
        main_layout.addWidget(title_label)
        
        # Report selection
        report_group = QGroupBox("Report Settings")
        report_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        report_layout = QFormLayout()
        
        # Report type
        self.report_type = QComboBox()
        self.report_type.addItems([
            "Sales by Period",
            "Sales by Customer",
            "Sales by Product",
            "Product Batch Analysis",
            "Expiry Date Report",
            "Profit and Loss",
            "Inventory Valuation",
            "Customer Balance",
            "Outstanding Payments"
        ])
        self.report_type.currentIndexChanged.connect(self.updateReportOptions)
        self.report_type.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        report_layout.addRow("Report Type:", self.report_type)
        
        # Date range
        date_layout = QHBoxLayout()
        
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        self.from_date.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        self.to_date.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.to_date)
        
        report_layout.addRow("Date Range:", date_layout)
        
        # Detail level
        self.detail_level = QComboBox()
        self.detail_level.addItems(["Summary", "Detailed"])
        self.detail_level.setStyleSheet("border: 1px solid #4B0082; padding: 5px;")
        report_layout.addRow("Detail Level:", self.detail_level)
        
        # Additional options (will be dynamically updated)
        self.options_layout = QFormLayout()
        report_layout.addRow(self.options_layout)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.generateReport)
        self.generate_btn.setStyleSheet("""
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
        report_layout.addRow("", self.generate_btn)
        
        report_group.setLayout(report_layout)
        main_layout.addWidget(report_group)
        
        # Report results
        results_group = QGroupBox("Report Results")
        results_group.setStyleSheet("QGroupBox { font-weight: bold; color: #4B0082; }")
        results_layout = QVBoxLayout()
        
        self.report_table = QTableWidget()
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.report_table.setStyleSheet("border: 1px solid #4B0082;")
        results_layout.addWidget(self.report_table)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.exportToCsv)
        self.export_csv_btn.setStyleSheet("""
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
        
        self.export_pdf_btn = QPushButton("Export to PDF")
        self.export_pdf_btn.clicked.connect(self.exportToPdf)
        self.export_pdf_btn.setStyleSheet("""
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
        
        self.print_btn = QPushButton("Print")
        self.print_btn.clicked.connect(self.printReport)
        self.print_btn.setStyleSheet("""
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
        
        self.print_preview_btn = QPushButton("Print Preview")
        self.print_preview_btn.clicked.connect(self.printPreview)
        self.print_preview_btn.setStyleSheet("""
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
        
        actions_layout.addWidget(self.export_csv_btn)
        actions_layout.addWidget(self.export_pdf_btn)
        actions_layout.addWidget(self.print_btn)
        actions_layout.addWidget(self.print_preview_btn)
        
        results_layout.addLayout(actions_layout)
        
        results_group.setLayout(results_layout)
        main_layout.addWidget(results_group)
        
        self.setLayout(main_layout)
        
        # Initialize report options
        self.updateReportOptions()
        
    def updateReportOptions(self):
        """Update additional options based on selected report type"""
        # Clear existing options
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        report_type = self.report_type.currentText()
        
        if report_type == "Sales by Customer":
            # Add customer selection
            self.customer_combo = QComboBox()
            self.customer_combo.addItem("All Customers", None)
            self.loadCustomers()
            self.options_layout.addRow("Customer:", self.customer_combo)
            
            # Show totals only option
            self.show_totals = QCheckBox("Show totals only")
            self.options_layout.addRow("", self.show_totals)
            
        elif report_type == "Sales by Product":
            # Add product selection
            self.product_combo = QComboBox()
            self.product_combo.addItem("All Products", None)
            self.loadProducts()
            self.options_layout.addRow("Product:", self.product_combo)
            
            # Show quantity option
            self.show_quantity = QCheckBox("Show quantities")
            self.show_quantity.setChecked(True)
            self.options_layout.addRow("", self.show_quantity)
            
            # Group by product name option
            self.group_by_name = QCheckBox("Group by product name")
            self.group_by_name.setChecked(True)
            self.options_layout.addRow("", self.group_by_name)
            
        elif report_type == "Product Batch Analysis":
            # Batch-specific options
            self.include_batch_info = QCheckBox("Include batch details")
            self.include_batch_info.setChecked(True)
            self.options_layout.addRow("", self.include_batch_info)
            
            # Show expired batches option
            self.show_expired_only = QCheckBox("Show expired batches only")
            self.options_layout.addRow("", self.show_expired_only)
            
        elif report_type == "Expiry Date Report":
            # Expiry threshold
            self.expiry_threshold = QSpinBox()
            self.expiry_threshold.setMinimum(0)
            self.expiry_threshold.setMaximum(365)
            self.expiry_threshold.setValue(30)
            self.options_layout.addRow("Days until expiry:", self.expiry_threshold)
            
            # Include expired products
            self.include_expired = QCheckBox("Include expired products")
            self.include_expired.setChecked(True)
            self.options_layout.addRow("", self.include_expired)
            
        elif report_type == "Profit and Loss":
            # Add grouping options
            self.grouping = QComboBox()
            self.grouping.addItems(["Daily", "Weekly", "Monthly"])
            self.options_layout.addRow("Group By:", self.grouping)
            
            # Include chart option
            self.include_chart = QCheckBox("Include chart")
            self.include_chart.setChecked(True)
            self.options_layout.addRow("", self.include_chart)
            
        elif report_type == "Outstanding Payments":
            # Add minimum days outstanding
            self.min_days = QSpinBox()
            self.min_days.setMinimum(0)
            self.min_days.setMaximum(365)
            self.min_days.setValue(30)
            self.options_layout.addRow("Minimum Days Outstanding:", self.min_days)
            
    def loadCustomers(self):
        """Load customers into combo box using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get all customers from MongoDB
            customers = self.mongo_adapter.get_customers()
            
            # Add to combo box
            for customer in customers:
                name = customer.get('name', '')
                customer_id = customer.get('id', '')
                if name:
                    self.customer_combo.addItem(name, customer_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customers: {str(e)}")
            
    def loadProducts(self):
        """Load distinct product names into combo box using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get all products from MongoDB
            products = self.mongo_adapter.get_products()
            
            # Get distinct product names
            product_names = set()
            for product in products:
                name = product.get('name', '')
                if name:
                    product_names.add(name)
            
            # Add to combo box
            for name in sorted(product_names):
                self.product_combo.addItem(name, name)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load products: {str(e)}")
            
    def generateReport(self):
        """Generate the selected report"""
        report_type = self.report_type.currentText()
        from_date = self.from_date.date().toString("yyyy-MM-dd")
        to_date = self.to_date.date().toString("yyyy-MM-dd")
        detail_level = self.detail_level.currentText()
        
        try:
            if report_type == "Sales by Period":
                self.generateSalesByPeriod(from_date, to_date, detail_level)
            elif report_type == "Sales by Customer":
                customer_id = self.customer_combo.currentData()
                show_totals = self.show_totals.isChecked()
                self.generateSalesByCustomer(from_date, to_date, detail_level, customer_id, show_totals)
            elif report_type == "Sales by Product":
                product_name = self.product_combo.currentData()
                show_quantity = self.show_quantity.isChecked()
                group_by_name = self.group_by_name.isChecked()
                self.generateSalesByProduct(from_date, to_date, detail_level, product_name, show_quantity, group_by_name)
            elif report_type == "Product Batch Analysis":
                include_batch_info = self.include_batch_info.isChecked()
                show_expired_only = self.show_expired_only.isChecked()
                self.generateBatchAnalysis(from_date, to_date, detail_level, include_batch_info, show_expired_only)
            elif report_type == "Expiry Date Report":
                threshold_days = self.expiry_threshold.value()
                include_expired = self.include_expired.isChecked()
                self.generateExpiryReport(from_date, to_date, detail_level, threshold_days, include_expired)
            elif report_type == "Profit and Loss":
                grouping = self.grouping.currentText()
                include_chart = self.include_chart.isChecked()
                self.generateProfitAndLoss(from_date, to_date, detail_level, grouping, include_chart)
            elif report_type == "Inventory Valuation":
                self.generateInventoryValuation(from_date, to_date, detail_level)
            elif report_type == "Customer Balance":
                self.generateCustomerBalance(from_date, to_date, detail_level)
            elif report_type == "Outstanding Payments":
                min_days = self.min_days.value()
                self.generateOutstandingPayments(from_date, to_date, detail_level, min_days)
                
        except Exception as e:
            QMessageBox.critical(self, "Report Error", f"Failed to generate report: {str(e)}")
            
    def generateSalesByPeriod(self, from_date, to_date, detail_level):
        """Generate sales by period report with batch information using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get data from MongoDB
            entries = self.mongo_adapter.get_entries()
            customers = self.mongo_adapter.get_customers()
            products = self.mongo_adapter.get_products()
            
            # Create lookup dictionaries
            customer_lookup = {str(customer.get('id')): customer for customer in customers}
            product_lookup = {str(product.get('id')): product for product in products}
            
            # Filter entries by date range
            filtered_entries = []
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date:
                    filtered_entries.append(entry)
            
            if detail_level == "Summary":
                # Group by date for summary
                daily_summary = {}
                
                for entry in filtered_entries:
                    date = entry.get('date', '')
                    quantity = float(entry.get('quantity', 0))
                    unit_price = float(entry.get('unit_price', 0))
                    total = quantity * unit_price
                    is_credit = entry.get('is_credit', False)
                    
                    if date not in daily_summary:
                        daily_summary[date] = {'credit': 0, 'debit': 0, 'net': 0}
                    
                    if is_credit:
                        daily_summary[date]['credit'] += total
                    else:
                        daily_summary[date]['debit'] += total
                    # Net = Debit - Credit
                    daily_summary[date]['net'] = daily_summary[date]['debit'] - daily_summary[date]['credit']
                
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                self.report_table.setColumnCount(4)
                self.report_table.setHorizontalHeaderLabels(["Date", "Debit", "Credit", "Net"])
                
                # Sort dates and fill table
                sorted_dates = sorted(daily_summary.keys())
                self.report_table.setRowCount(len(sorted_dates))
                
                total_credit = 0
                total_debit = 0
                total_net = 0
                
                for row, date in enumerate(sorted_dates):
                    summary = daily_summary[date]
                    
                    self.report_table.setItem(row, 0, QTableWidgetItem(date))
                    # Debit (Green)
                    debit_item = QTableWidgetItem(f"PKR{summary['debit']:.2f}")
                    debit_item.setForeground(Qt.green)
                    self.report_table.setItem(row, 1, debit_item)
                    # Credit (Red)
                    credit_item = QTableWidgetItem(f"PKR{summary['credit']:.2f}")
                    credit_item.setForeground(Qt.red)
                    self.report_table.setItem(row, 2, credit_item)
                    # Net (Green if positive, Red if negative)
                    net_item = QTableWidgetItem(f"PKR{summary['net']:.2f}")
                    net_item.setForeground(Qt.green if summary['net'] >= 0 else Qt.red)
                    self.report_table.setItem(row, 3, net_item)
                    
                    total_credit += summary['credit']
                    total_debit += summary['debit']
                    total_net += summary['net']
                
                # Add total row
                total_row = self.report_table.rowCount()
                self.report_table.insertRow(total_row)
                self.report_table.setItem(total_row, 0, QTableWidgetItem("TOTAL"))
                debit_item = QTableWidgetItem(f"PKR{total_debit:.2f}")
                debit_item.setForeground(Qt.green)
                self.report_table.setItem(total_row, 1, debit_item)
                credit_item = QTableWidgetItem(f"PKR{total_credit:.2f}")
                credit_item.setForeground(Qt.red)
                self.report_table.setItem(total_row, 2, credit_item)
                net_item = QTableWidgetItem(f"PKR{total_net:.2f}")
                net_item.setForeground(Qt.green if total_net >= 0 else Qt.red)
                self.report_table.setItem(total_row, 3, net_item)
                
                # Format total row
                for col in range(self.report_table.columnCount()):
                    item = self.report_table.item(total_row, col)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
            else:  # Detailed report
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                self.report_table.setColumnCount(10)
                self.report_table.setHorizontalHeaderLabels([
                    "ID", "Date", "Customer", "Product", "Batch", "Expiry", 
                    "Quantity", "Unit Price", "Total", "Type"
                ])
                
                # Fill table
                self.report_table.setRowCount(len(filtered_entries))
                
                total_credit = 0
                total_debit = 0
                current_date = QDate.currentDate()
                
                for row, entry in enumerate(filtered_entries):
                    entry_id = str(entry.get('id', ''))
                    date = entry.get('date', '')
                    customer_id = str(entry.get('customer_id', ''))
                    product_id = str(entry.get('product_id', ''))
                    quantity = float(entry.get('quantity', 0))
                    unit_price = float(entry.get('unit_price', 0))
                    total = quantity * unit_price
                    is_credit = entry.get('is_credit', False)
                    
                    # Get customer and product info
                    customer_info = customer_lookup.get(customer_id, {})
                    product_info = product_lookup.get(product_id, {})
                    
                    customer_name = customer_info.get('name', 'Unknown Customer')
                    product_name = product_info.get('name', 'Unknown Product')
                    batch_number = product_info.get('batch_number', '')
                    expiry_date = product_info.get('expiry_date', '')
                    
                    self.report_table.setItem(row, 0, QTableWidgetItem(entry_id))
                    self.report_table.setItem(row, 1, QTableWidgetItem(date))
                    self.report_table.setItem(row, 2, QTableWidgetItem(customer_name))
                    self.report_table.setItem(row, 3, QTableWidgetItem(product_name))
                    self.report_table.setItem(row, 4, QTableWidgetItem(batch_number))
                    
                    # Color-code expiry date
                    expiry_item = QTableWidgetItem(expiry_date)
                    try:
                        expiry_qdate = QDate.fromString(expiry_date, "yyyy-MM-dd")
                        if expiry_qdate.isValid():
                            if expiry_qdate < current_date:
                                expiry_item.setForeground(QColor("#cc0000"))  # Red for expired
                            elif expiry_qdate < current_date.addDays(30):
                                expiry_item.setForeground(QColor("#856404"))  # Orange for expiring soon
                    except:
                        pass
                    self.report_table.setItem(row, 5, expiry_item)
                    
                    self.report_table.setItem(row, 6, QTableWidgetItem(str(quantity)))
                    self.report_table.setItem(row, 7, QTableWidgetItem(f"PKR{unit_price:.2f}"))
                    self.report_table.setItem(row, 8, QTableWidgetItem(f"PKR{total:.2f}"))
                    
                    # Type
                    type_item = QTableWidgetItem("Debit" if not is_credit else "Credit")
                    type_item.setForeground(Qt.green if not is_credit else Qt.red)
                    self.report_table.setItem(row, 9, type_item)
                    
                    if is_credit:
                        total_credit += total
                    else:
                        total_debit += total
                
                # Add total row
                total_row = self.report_table.rowCount()
                self.report_table.insertRow(total_row)
                self.report_table.setItem(total_row, 0, QTableWidgetItem("TOTAL"))
                self.report_table.setItem(total_row, 8, QTableWidgetItem(f"Debit: PKR{total_debit:.2f} / Credit: PKR{total_credit:.2f}"))
                net_val = total_debit - total_credit
                net_item = QTableWidgetItem(f"Net: PKR{net_val:.2f}")
                net_item.setForeground(Qt.green if net_val >= 0 else Qt.red)
                self.report_table.setItem(total_row, 9, net_item)
                
                # Format total row
                for col in range(self.report_table.columnCount()):
                    item = self.report_table.item(total_row, col)
                    if item:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
        except Exception as e:
            raise Exception(f"Error generating sales by period report: {str(e)}")

    def generateSalesByCustomer(self, from_date, to_date, detail_level, customer_id, show_totals):
        """Generate sales by customer report with batch information using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get data from MongoDB
            entries = self.mongo_adapter.get_entries()
            customers = self.mongo_adapter.get_customers()
            products = self.mongo_adapter.get_products()
            
            # Create lookup dictionaries
            customer_lookup = {str(customer.get('id')): customer for customer in customers}
            product_lookup = {str(product.get('id')): product for product in products}
            
            # Filter entries by date range and customer
            filtered_entries = []
            for entry in entries:
                entry_date = entry.get('date', '')
                entry_customer_id = str(entry.get('customer_id', ''))
                
                # Check date range
                if not (from_date <= entry_date <= to_date):
                    continue
                
                # Check customer filter
                if customer_id is not None and entry_customer_id != str(customer_id):
                    continue
                
                filtered_entries.append(entry)
            
            if detail_level == "Summary" or show_totals:
                # Group by customer
                customer_summary = {}
                
                for entry in filtered_entries:
                    customer_id = str(entry.get('customer_id', ''))
                    quantity = float(entry.get('quantity', 0))
                    unit_price = float(entry.get('unit_price', 0))
                    total = quantity * unit_price
                    is_credit = entry.get('is_credit', False)
                    
                    if customer_id not in customer_summary:
                        customer_info = customer_lookup.get(customer_id, {})
                        customer_summary[customer_id] = {
                            'name': customer_info.get('name', 'Unknown Customer'),
                            'credit': 0,
                            'debit': 0,
                            'net': 0,
                            'transaction_count': 0
                        }
                    
                    if is_credit:
                        customer_summary[customer_id]['credit'] += total
                    else:
                        customer_summary[customer_id]['debit'] += total
                    # Net = Debit - Credit
                    customer_summary[customer_id]['net'] = customer_summary[customer_id]['debit'] - customer_summary[customer_id]['credit']
                    customer_summary[customer_id]['transaction_count'] += 1
                
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                self.report_table.setColumnCount(6)
                self.report_table.setHorizontalHeaderLabels([
                    "ID", "Customer", "Debit", "Credit", "Net", "Transaction Count"
                ])
                
                # Sort by net amount and fill table
                sorted_customers = sorted(customer_summary.items(), key=lambda x: x[1]['net'], reverse=True)
                self.report_table.setRowCount(len(sorted_customers))
                
                total_credit = 0
                total_debit = 0
                total_net = 0
                total_transactions = 0
                
                for row, (customer_id, summary) in enumerate(sorted_customers):
                    self.report_table.setItem(row, 0, QTableWidgetItem(customer_id))
                    self.report_table.setItem(row, 1, QTableWidgetItem(summary['name']))
                    # Debit (Green)
                    debit_item = QTableWidgetItem(f"PKR{summary['debit']:.2f}")
                    debit_item.setForeground(Qt.green)
                    self.report_table.setItem(row, 2, debit_item)
                    # Credit (Red)
                    credit_item = QTableWidgetItem(f"PKR{summary['credit']:.2f}")
                    credit_item.setForeground(Qt.red)
                    self.report_table.setItem(row, 3, credit_item)
                    # Net (Green if positive, Red if negative)
                    net_item = QTableWidgetItem(f"PKR{summary['net']:.2f}")
                    net_item.setForeground(Qt.green if summary['net'] >= 0 else Qt.red)
                    self.report_table.setItem(row, 4, net_item)
                    self.report_table.setItem(row, 5, QTableWidgetItem(str(summary['transaction_count'])))
                    
                    total_credit += summary['credit']
                    total_debit += summary['debit']
                    total_net += summary['net']
                    total_transactions += summary['transaction_count']
                
                # Add total row
                total_row = self.report_table.rowCount()
                self.report_table.insertRow(total_row)
                self.report_table.setItem(total_row, 1, QTableWidgetItem("TOTAL"))
                debit_item = QTableWidgetItem(f"PKR{total_debit:.2f}")
                debit_item.setForeground(Qt.green)
                self.report_table.setItem(total_row, 2, debit_item)
                credit_item = QTableWidgetItem(f"PKR{total_credit:.2f}")
                credit_item.setForeground(Qt.red)
                self.report_table.setItem(total_row, 3, credit_item)
                net_item = QTableWidgetItem(f"PKR{total_net:.2f}")
                net_item.setForeground(Qt.green if total_net >= 0 else Qt.red)
                self.report_table.setItem(total_row, 4, net_item)
                self.report_table.setItem(total_row, 5, QTableWidgetItem(str(total_transactions)))
                
                # Format total row
                for col in range(self.report_table.columnCount()):
                    item = self.report_table.item(total_row, col)
                    if item:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
            else:  # Detailed report
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                self.report_table.setColumnCount(10)
                self.report_table.setHorizontalHeaderLabels([
                    "ID", "Date", "Customer", "Product", "Batch", "Expiry",
                    "Quantity", "Unit Price", "Total", "Type"
                ])
                
                # Sort by customer name, then date
                sorted_entries = sorted(filtered_entries, key=lambda x: (
                    customer_lookup.get(str(x.get('customer_id', '')), {}).get('name', ''),
                    x.get('date', '')
                ))
                
                # Fill table
                self.report_table.setRowCount(len(sorted_entries))
                current_date = QDate.currentDate()
                
                for row, entry in enumerate(sorted_entries):
                    entry_id = str(entry.get('id', ''))
                    date = entry.get('date', '')
                    customer_id = str(entry.get('customer_id', ''))
                    product_id = str(entry.get('product_id', ''))
                    quantity = float(entry.get('quantity', 0))
                    unit_price = float(entry.get('unit_price', 0))
                    total = quantity * unit_price
                    is_credit = entry.get('is_credit', False)
                    
                    # Get customer and product info
                    customer_info = customer_lookup.get(customer_id, {})
                    product_info = product_lookup.get(product_id, {})
                    
                    customer_name = customer_info.get('name', 'Unknown Customer')
                    product_name = product_info.get('name', 'Unknown Product')
                    batch_number = product_info.get('batch_number', '')
                    expiry_date = product_info.get('expiry_date', '')
                    
                    self.report_table.setItem(row, 0, QTableWidgetItem(entry_id))
                    self.report_table.setItem(row, 1, QTableWidgetItem(date))
                    self.report_table.setItem(row, 2, QTableWidgetItem(customer_name))
                    self.report_table.setItem(row, 3, QTableWidgetItem(product_name))
                    self.report_table.setItem(row, 4, QTableWidgetItem(batch_number))
                    
                    # Color-code expiry date
                    expiry_item = QTableWidgetItem(expiry_date)
                    try:
                        expiry_qdate = QDate.fromString(expiry_date, "yyyy-MM-dd")
                        if expiry_qdate.isValid():
                            if expiry_qdate < current_date:
                                expiry_item.setForeground(QColor("#cc0000"))  # Red for expired
                            elif expiry_qdate < current_date.addDays(30):
                                expiry_item.setForeground(QColor("#856404"))  # Orange for expiring soon
                    except:
                        pass
                    self.report_table.setItem(row, 5, expiry_item)
                    
                    self.report_table.setItem(row, 6, QTableWidgetItem(str(quantity)))
                    self.report_table.setItem(row, 7, QTableWidgetItem(f"PKR{unit_price:.2f}"))
                    self.report_table.setItem(row, 8, QTableWidgetItem(f"PKR{total:.2f}"))
                    
                    # Type
                    type_item = QTableWidgetItem("Debit" if not is_credit else "Credit")
                    type_item.setForeground(Qt.green if not is_credit else Qt.red)
                    self.report_table.setItem(row, 9, type_item)
                
        except Exception as e:
            raise Exception(f"Error generating sales by customer report: {str(e)}")
    
    def generateSalesByProduct(self, from_date, to_date, detail_level, product_name, show_quantity, group_by_name):
        """Generate sales by product report with batch analysis using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get data from MongoDB
            entries = self.mongo_adapter.get_entries()
            products = self.mongo_adapter.get_products()
            
            # Create product lookup
            product_lookup = {str(product.get('id')): product for product in products}
            
            # Filter entries by date range and product
            filtered_entries = []
            for entry in entries:
                entry_date = entry.get('date', '')
                if not (from_date <= entry_date <= to_date):
                    continue
                
                # Check product filter
                if product_name is not None:
                    product_id = str(entry.get('product_id', ''))
                    product_info = product_lookup.get(product_id, {})
                    if product_info.get('name', '') != product_name:
                        continue
                
                filtered_entries.append(entry)
            
            if group_by_name:
                # Group by product name (combines all batches)
                product_summary = {}
                
                for entry in filtered_entries:
                    if not entry.get('is_credit', False):  # Only sales (credit entries)
                        continue
                        
                    product_id = str(entry.get('product_id', ''))
                    product_info = product_lookup.get(product_id, {})
                    product_name_key = product_info.get('name', 'Unknown Product')
                    
                    quantity = float(entry.get('quantity', 0))
                    unit_price = float(entry.get('unit_price', 0))
                    total = quantity * unit_price
                    
                    if product_name_key not in product_summary:
                        # Get all batches for this product
                        product_batches = set()
                        earliest_expiry = None
                        latest_expiry = None
                        
                        for p in products:
                            if p.get('name') == product_name_key:
                                batch = p.get('batch_number', '')
                                if batch:
                                    product_batches.add(batch)
                                
                                expiry = p.get('expiry_date', '')
                                if expiry:
                                    if earliest_expiry is None or expiry < earliest_expiry:
                                        earliest_expiry = expiry
                                    if latest_expiry is None or expiry > latest_expiry:
                                        latest_expiry = expiry
                        
                        product_summary[product_name_key] = {
                            'total_sales': 0,
                            'total_quantity': 0,
                            'batch_count': len(product_batches),
                            'earliest_expiry': earliest_expiry or 'N/A',
                            'latest_expiry': latest_expiry or 'N/A'
                        }
                    
                    product_summary[product_name_key]['total_sales'] += total
                    product_summary[product_name_key]['total_quantity'] += quantity
                
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                columns = ["Product", "Total Sales", "Batches", "Earliest Expiry", "Latest Expiry"]
                if show_quantity:
                    columns.insert(2, "Total Quantity")
                
                self.report_table.setColumnCount(len(columns))
                self.report_table.setHorizontalHeaderLabels(columns)
                
                # Sort by total sales and fill table
                sorted_products = sorted(product_summary.items(), key=lambda x: x[1]['total_sales'], reverse=True)
                self.report_table.setRowCount(len(sorted_products))
                
                for row, (product_name_key, summary) in enumerate(sorted_products):
                    col = 0
                    self.report_table.setItem(row, col, QTableWidgetItem(product_name_key))
                    col += 1
                    self.report_table.setItem(row, col, QTableWidgetItem(f"PKR{summary['total_sales']:.2f}"))
                    col += 1
                    
                    if show_quantity:
                        self.report_table.setItem(row, col, QTableWidgetItem(str(int(summary['total_quantity']))))
                        col += 1
                    
                    self.report_table.setItem(row, col, QTableWidgetItem(str(summary['batch_count'])))
                    col += 1
                    self.report_table.setItem(row, col, QTableWidgetItem(summary['earliest_expiry']))
                    col += 1
                    self.report_table.setItem(row, col, QTableWidgetItem(summary['latest_expiry']))
                        
            else:
                # Show individual batches
                batch_summary = {}
                
                for entry in filtered_entries:
                    if not entry.get('is_credit', False):  # Only sales (credit entries)
                        continue
                        
                    product_id = str(entry.get('product_id', ''))
                    product_info = product_lookup.get(product_id, {})
                    
                    product_name_key = product_info.get('name', 'Unknown Product')
                    batch_number = product_info.get('batch_number', '')
                    expiry_date = product_info.get('expiry_date', '')
                    
                    batch_key = f"{product_name_key}|{batch_number}|{expiry_date}"
                    
                    quantity = float(entry.get('quantity', 0))
                    unit_price = float(entry.get('unit_price', 0))
                    total = quantity * unit_price
                    
                    if batch_key not in batch_summary:
                        batch_summary[batch_key] = {
                            'product_name': product_name_key,
                            'batch_number': batch_number,
                            'expiry_date': expiry_date,
                            'total_sales': 0,
                            'total_quantity': 0
                        }
                    
                    batch_summary[batch_key]['total_sales'] += total
                    batch_summary[batch_key]['total_quantity'] += quantity
                
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                columns = ["Product", "Batch", "Expiry Date", "Total Sales"]
                if show_quantity:
                    columns.append("Total Quantity")
                
                self.report_table.setColumnCount(len(columns))
                self.report_table.setHorizontalHeaderLabels(columns)
                
                # Sort by total sales and fill table
                sorted_batches = sorted(batch_summary.values(), key=lambda x: x['total_sales'], reverse=True)
                self.report_table.setRowCount(len(sorted_batches))
                current_date = QDate.currentDate()
                
                for row, batch_data in enumerate(sorted_batches):
                    self.report_table.setItem(row, 0, QTableWidgetItem(batch_data['product_name']))
                    self.report_table.setItem(row, 1, QTableWidgetItem(batch_data['batch_number']))
                    
                    # Color-code expiry date
                    expiry_item = QTableWidgetItem(batch_data['expiry_date'])
                    try:
                        expiry_qdate = QDate.fromString(batch_data['expiry_date'], "yyyy-MM-dd")
                        if expiry_qdate.isValid():
                            if expiry_qdate < current_date:
                                expiry_item.setForeground(QColor("#cc0000"))  # Red for expired
                            elif expiry_qdate < current_date.addDays(30):
                                expiry_item.setForeground(QColor("#856404"))  # Orange for expiring soon
                    except:
                        pass
                    self.report_table.setItem(row, 2, expiry_item)
                    
                    self.report_table.setItem(row, 3, QTableWidgetItem(f"PKR{batch_data['total_sales']:.2f}"))
                    
                    if show_quantity:
                        self.report_table.setItem(row, 4, QTableWidgetItem(str(int(batch_data['total_quantity']))))
                    
        except Exception as e:
            raise Exception(f"Error generating sales by product report: {str(e)}")
    
    def generateBatchAnalysis(self, from_date, to_date, detail_level, include_batch_info, show_expired_only):
        """Generate product batch analysis report using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get data from MongoDB
            entries = self.mongo_adapter.get_entries()
            products = self.mongo_adapter.get_products()
            
            # Create product lookup
            product_lookup = {str(product.get('id')): product for product in products}
            
            # Filter entries by date range
            filtered_entries = []
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date:
                    filtered_entries.append(entry)
            
            # Group by product batch
            batch_analysis = {}
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            
            for entry in filtered_entries:
                if not entry.get('is_credit', False):  # Only sales (credit entries)
                    continue
                    
                product_id = str(entry.get('product_id', ''))
                product_info = product_lookup.get(product_id, {})
                
                product_name = product_info.get('name', 'Unknown Product')
                batch_number = product_info.get('batch_number', '')
                expiry_date = product_info.get('expiry_date', '')
                
                # Check expiry filter
                if show_expired_only and expiry_date >= current_date:
                    continue
                
                batch_key = f"{product_name}|{batch_number}|{expiry_date}"
                
                quantity = float(entry.get('quantity', 0))
                unit_price = float(entry.get('unit_price', 0))
                total = quantity * unit_price
                
                if batch_key not in batch_analysis:
                    # Determine status
                    status = 'VALID'
                    if expiry_date:
                        if expiry_date < current_date:
                            status = 'EXPIRED'
                        elif expiry_date <= QDate.currentDate().addDays(30).toString("yyyy-MM-dd"):
                            status = 'EXPIRING SOON'
                    
                    batch_analysis[batch_key] = {
                        'product_name': product_name,
                        'batch_number': batch_number,
                        'expiry_date': expiry_date,
                        'total_sales': 0,
                        'total_quantity': 0,
                        'transaction_count': 0,
                        'status': status
                    }
                
                batch_analysis[batch_key]['total_sales'] += total
                batch_analysis[batch_key]['total_quantity'] += quantity
                batch_analysis[batch_key]['transaction_count'] += 1
            
            # Set up table
            self.report_table.clear()
            self.report_table.setRowCount(0)
            self.report_table.setColumnCount(7)
            self.report_table.setHorizontalHeaderLabels([
                "Product", "Batch Number", "Expiry Date", "Total Sales", 
                "Total Quantity", "Transactions", "Status"
            ])
            
            # Sort by expiry date and total sales
            sorted_batches = sorted(batch_analysis.values(), 
                                  key=lambda x: (x['expiry_date'], -x['total_sales']))
            self.report_table.setRowCount(len(sorted_batches))
            
            total_sales = 0
            total_quantity = 0
            
            for row, batch_data in enumerate(sorted_batches):
                self.report_table.setItem(row, 0, QTableWidgetItem(batch_data['product_name']))
                self.report_table.setItem(row, 1, QTableWidgetItem(batch_data['batch_number']))
                self.report_table.setItem(row, 2, QTableWidgetItem(batch_data['expiry_date']))
                self.report_table.setItem(row, 3, QTableWidgetItem(f"PKR{batch_data['total_sales']:.2f}"))
                self.report_table.setItem(row, 4, QTableWidgetItem(str(int(batch_data['total_quantity']))))
                self.report_table.setItem(row, 5, QTableWidgetItem(str(batch_data['transaction_count'])))
                
                # Color-code status
                status_item = QTableWidgetItem(batch_data['status'])
                if batch_data['status'] == "EXPIRED":
                    status_item.setForeground(QColor("#cc0000"))
                elif batch_data['status'] == "EXPIRING SOON":
                    status_item.setForeground(QColor("#856404"))
                else:
                    status_item.setForeground(QColor("#155724"))
                self.report_table.setItem(row, 6, status_item)
                
                total_sales += batch_data['total_sales']
                total_quantity += batch_data['total_quantity']
            
            # Add summary row
            if sorted_batches:
                summary_row = self.report_table.rowCount()
                self.report_table.insertRow(summary_row)
                self.report_table.setItem(summary_row, 0, QTableWidgetItem("TOTAL"))
                self.report_table.setItem(summary_row, 3, QTableWidgetItem(f"PKR{total_sales:.2f}"))
                self.report_table.setItem(summary_row, 4, QTableWidgetItem(str(int(total_quantity))))
                
                # Bold the summary row
                for col in range(self.report_table.columnCount()):
                    item = self.report_table.item(summary_row, col)
                    if item:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
            
        except Exception as e:
            raise Exception(f"Error generating batch analysis report: {str(e)}")
    
    def generateExpiryReport(self, from_date, to_date, detail_level, threshold_days, include_expired):
        """Generate expiry date analysis report using MongoDB"""
        try:
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
                
            # Get data from MongoDB
            entries = self.mongo_adapter.get_entries()
            products = self.mongo_adapter.get_products()
            
            # Create product lookup
            product_lookup = {str(product.get('id')): product for product in products}
            
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            threshold_date = QDate.currentDate().addDays(threshold_days).toString("yyyy-MM-dd")
            
            # Filter entries by date range
            filtered_entries = []
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date:
                    filtered_entries.append(entry)
            
            # Group by product batch and filter by expiry
            expiry_analysis = {}
            
            for entry in filtered_entries:
                if not entry.get('is_credit', False):  # Only sales (credit entries)
                    continue
                    
                product_id = str(entry.get('product_id', ''))
                product_info = product_lookup.get(product_id, {})
                
                product_name = product_info.get('name', 'Unknown Product')
                batch_number = product_info.get('batch_number', '')
                expiry_date = product_info.get('expiry_date', '')
                
                # Apply expiry filters
                if expiry_date:
                    if include_expired:
                        # Include products that are expired or expiring within threshold
                        if expiry_date > threshold_date:
                            continue
                    else:
                        # Only products expiring within threshold (not yet expired)
                        if expiry_date <= current_date or expiry_date > threshold_date:
                            continue
                else:
                    continue  # Skip products without expiry date
                
                batch_key = f"{product_name}|{batch_number}|{expiry_date}"
                
                quantity = float(entry.get('quantity', 0))
                unit_price = float(entry.get('unit_price', 0))
                total = quantity * unit_price
                
                if batch_key not in expiry_analysis:
                    # Calculate days to expiry
                    try:
                        expiry_qdate = QDate.fromString(expiry_date, "yyyy-MM-dd")
                        current_qdate = QDate.fromString(current_date, "yyyy-MM-dd")
                        days_to_expiry = current_qdate.daysTo(expiry_qdate)
                    except:
                        days_to_expiry = 0
                    
                    # Determine status
                    if days_to_expiry < 0:
                        status = 'EXPIRED'
                    elif days_to_expiry <= 30:
                        status = 'EXPIRING SOON'
                    else:
                        status = 'VALID'
                    
                    expiry_analysis[batch_key] = {
                        'product_name': product_name,
                        'batch_number': batch_number,
                        'expiry_date': expiry_date,
                        'days_to_expiry': days_to_expiry,
                        'total_sales': 0,
                        'total_quantity': 0,
                        'status': status
                    }
                
                expiry_analysis[batch_key]['total_sales'] += total
                expiry_analysis[batch_key]['total_quantity'] += quantity
            
            # Set up table
            self.report_table.clear()
            self.report_table.setRowCount(0)
            self.report_table.setColumnCount(7)
            self.report_table.setHorizontalHeaderLabels([
                "Product", "Batch Number", "Expiry Date", "Days to Expiry",
                "Total Sales", "Total Quantity", "Status"
            ])
            
            # Sort by expiry date
            sorted_products = sorted(expiry_analysis.values(), key=lambda x: x['expiry_date'])
            self.report_table.setRowCount(len(sorted_products))
            
            total_sales = 0
            total_quantity = 0
            expired_count = 0
            expiring_count = 0
            
            for row, product_data in enumerate(sorted_products):
                self.report_table.setItem(row, 0, QTableWidgetItem(product_data['product_name']))
                self.report_table.setItem(row, 1, QTableWidgetItem(product_data['batch_number']))
                self.report_table.setItem(row, 2, QTableWidgetItem(product_data['expiry_date']))
                
                # Days to expiry with color coding
                days_item = QTableWidgetItem(str(product_data['days_to_expiry']))
                if product_data['days_to_expiry'] < 0:
                    days_item.setForeground(QColor("#cc0000"))
                elif product_data['days_to_expiry'] <= 30:
                    days_item.setForeground(QColor("#856404"))
                self.report_table.setItem(row, 3, days_item)
                
                self.report_table.setItem(row, 4, QTableWidgetItem(f"PKR{product_data['total_sales']:.2f}"))
                self.report_table.setItem(row, 5, QTableWidgetItem(str(int(product_data['total_quantity']))))
                
                # Status with color coding
                status_item = QTableWidgetItem(product_data['status'])
                if product_data['status'] == "EXPIRED":
                    status_item.setForeground(QColor("#cc0000"))
                    expired_count += 1
                elif product_data['status'] == "EXPIRING SOON":
                    status_item.setForeground(QColor("#856404"))
                    expiring_count += 1
                else:
                    status_item.setForeground(QColor("#155724"))
                self.report_table.setItem(row, 6, status_item)
                
                total_sales += product_data['total_sales']
                total_quantity += product_data['total_quantity']
            
            # Add summary information
            if sorted_products:
                summary_row = self.report_table.rowCount()
                self.report_table.insertRow(summary_row)
                self.report_table.setItem(summary_row, 0, QTableWidgetItem("SUMMARY"))
                self.report_table.setItem(summary_row, 1, QTableWidgetItem(f"Expired: {expired_count}, Expiring: {expiring_count}"))
                self.report_table.setItem(summary_row, 4, QTableWidgetItem(f"PKR{total_sales:.2f}"))
                self.report_table.setItem(summary_row, 5, QTableWidgetItem(str(int(total_quantity))))
                
                # Bold the summary row
                for col in range(self.report_table.columnCount()):
                    item = self.report_table.item(summary_row, col)
                    if item:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
            
        except Exception as e:
            raise Exception(f"Error generating expiry report: {str(e)}")
    
    def generateProfitAndLoss(self, from_date, to_date, detail_level, grouping, include_chart):
        """Generate profit and loss report using MongoDB"""
        try:
            QMessageBox.information(self, "Coming Soon", 
                                  "Profit and Loss report will be implemented in a future update with advanced analytics.")
        except Exception as e:
            raise Exception(f"Error generating profit and loss report: {str(e)}")
    
    def generateInventoryValuation(self, from_date, to_date, detail_level):
        """Generate inventory valuation report using MongoDB"""
        try:
            QMessageBox.information(self, "Coming Soon", 
                                  "Inventory Valuation report will be implemented in a future update.")
        except Exception as e:
            raise Exception(f"Error generating inventory valuation report: {str(e)}")
    
    def generateCustomerBalance(self, from_date, to_date, detail_level):
        """Generate customer balance report using MongoDB"""
        try:
            QMessageBox.information(self, "Coming Soon", 
                                  "Customer Balance report will be implemented in a future update.")
        except Exception as e:
            raise Exception(f"Error generating customer balance report: {str(e)}")
    
    def generateOutstandingPayments(self, from_date, to_date, detail_level, min_days):
        """Generate outstanding payments report using MongoDB"""
        try:
            QMessageBox.information(self, "Coming Soon", 
                                  "Outstanding Payments report will be implemented in a future update.")
        except Exception as e:
            raise Exception(f"Error generating outstanding payments report: {str(e)}")
    
    def exportToCsv(self):
        """Export report to CSV file"""
        try:
            # Get save file location
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Export to CSV", "", "CSV Files (*.csv);;All Files (*)", options=options
            )
            
            if not file_name:
                return
            
            # Add .csv extension if not present
            if not file_name.endswith('.csv'):
                file_name += '.csv'
            
            # Open the file for writing
            with open(file_name, 'w', newline='', encoding='utf-8') as file:
                writer = csv.writer(file)
                
                # Write report metadata
                writer.writerow([f"Report Type: {self.report_type.currentText()}"])
                writer.writerow([f"Date Range: {self.from_date.date().toString('yyyy-MM-dd')} to {self.to_date.date().toString('yyyy-MM-dd')}"])
                writer.writerow([f"Generated on: {QDate.currentDate().toString('yyyy-MM-dd')}"])
                writer.writerow([f"Generated using: "])
                writer.writerow([])  # Empty row
                
                # Write header row
                headers = []
                for col in range(self.report_table.columnCount()):
                    headers.append(self.report_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data rows
                for row in range(self.report_table.rowCount()):
                    row_data = []
                    for col in range(self.report_table.columnCount()):
                        item = self.report_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export Successful", 
                                f"Report exported successfully to:\n{file_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export report: {str(e)}")
    
    def exportToPdf(self):
        """Export report to PDF file using reportlab"""
        try:
            if self.report_table.rowCount() == 0:
                QMessageBox.warning(self, "No Data", "No data to export to PDF!")
                return
            
            # Get save file location
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Export to PDF", f"report_{QDate.currentDate().toString('yyyy-MM-dd')}.pdf",
                "PDF Files (*.pdf);;All Files (*)", options=options
            )
            
            if not file_name:
                return
            
            # Add .pdf extension if not present
            if not file_name.endswith('.pdf'):
                file_name += '.pdf'
            
            # Prepare report data
            report_data = self._prepareReportData()
            
            # Generate PDF using reportlab
            pdf_generator = PDFGenerator()
            success = pdf_generator.generate_report_pdf(report_data, file_name)
            
            if success:
                QMessageBox.information(self, "Export Successful", 
                                      f"Report exported to PDF:\n{file_name}")
            else:
                QMessageBox.critical(self, "Export Error", 
                                   "Failed to generate PDF report.")
            
        except ImportError:
            QMessageBox.critical(
                self, "Missing Library",
                "ReportLab library is required for PDF generation.\n"
                "Please install it using: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export to PDF: {str(e)}")
    
    def _prepareReportData(self):
        """Prepare report data for PDF generation"""
        # Get table headers
        headers = []
        for col in range(self.report_table.columnCount()):
            header_item = self.report_table.horizontalHeaderItem(col)
            headers.append(header_item.text() if header_item else f"Column {col+1}")
        
        # Get table data
        table_data = [headers]
        for row in range(self.report_table.rowCount()):
            row_data = []
            for col in range(self.report_table.columnCount()):
                item = self.report_table.item(row, col)
                row_data.append(item.text() if item else "")
            table_data.append(row_data)
        
        return {
            'report_type': self.report_type.currentText(),
            'from_date': self.from_date.date().toString("yyyy-MM-dd"),
            'to_date': self.to_date.date().toString("yyyy-MM-dd"),
            'detail_level': self.detail_level.currentText(),
            'table_data': table_data
        }

    def printReport(self):
        """Print the current report using reportlab PDF"""
        try:
            if self.report_table.rowCount() == 0:
                QMessageBox.warning(self, "No Data", "No data to print!")
                return
            
            # Create temporary PDF
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_pdf = os.path.join(temp_dir, f"temp_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            
            # Prepare report data
            report_data = self._prepareReportData()
            
            # Generate PDF
            pdf_generator = PDFGenerator()
            success = pdf_generator.generate_report_pdf(report_data, temp_pdf)
            
            if success:
                # Open PDF for printing
                import subprocess
                if sys.platform == "win32":
                    os.startfile(temp_pdf)
                elif sys.platform == "darwin":
                    subprocess.call(["open", temp_pdf])
                else:
                    subprocess.call(["xdg-open", temp_pdf])
                
                QMessageBox.information(self, "Print Ready", 
                                      f"PDF generated and opened for printing:\n{temp_pdf}")
            else:
                QMessageBox.critical(self, "Print Error", 
                                   "Failed to generate PDF for printing.")
            
        except ImportError:
            QMessageBox.critical(
                self, "Missing Library",
                "ReportLab library is required for PDF generation.\n"
                "Please install it using: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Print Error", f"Failed to print report: {str(e)}")
    
    def printPreview(self):
        """Show print preview by opening the temporary PDF"""
        try:
            if self.report_table.rowCount() == 0:
                QMessageBox.warning(self, "No Data", "No data to preview!")
                return
            
            # Create temporary PDF
            import tempfile
            temp_dir = tempfile.gettempdir()
            temp_pdf = os.path.join(temp_dir, f"preview_report_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf")
            
            # Prepare report data
            report_data = self._prepareReportData()
            
            # Generate PDF
            pdf_generator = PDFGenerator()
            success = pdf_generator.generate_report_pdf(report_data, temp_pdf)
            
            if success:
                # Open PDF for preview
                import subprocess
                if sys.platform == "win32":
                    os.startfile(temp_pdf)
                elif sys.platform == "darwin":
                    subprocess.call(["open", temp_pdf])
                else:
                    subprocess.call(["xdg-open", temp_pdf])
                
                QMessageBox.information(self, "Preview Ready", 
                                      f"PDF preview opened:\n{temp_pdf}")
            else:
                QMessageBox.critical(self, "Preview Error", 
                                   "Failed to generate PDF preview.")
            
        except ImportError:
            QMessageBox.critical(
                self, "Missing Library",
                "ReportLab library is required for PDF generation.\n"
                "Please install it using: pip install reportlab"
            )
        except Exception as e:
            QMessageBox.critical(self, "Print Preview Error", f"Failed to show print preview: {str(e)}")
