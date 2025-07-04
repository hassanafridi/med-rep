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
from database.db import Database

class ReportsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Report selection
        report_group = QGroupBox("Report Settings")
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
        report_layout.addRow("Report Type:", self.report_type)
        
        # Date range
        date_layout = QHBoxLayout()
        
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-1))
        self.from_date.setCalendarPopup(True)
        
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.to_date)
        
        report_layout.addRow("Date Range:", date_layout)
        
        # Detail level
        self.detail_level = QComboBox()
        self.detail_level.addItems(["Summary", "Detailed"])
        report_layout.addRow("Detail Level:", self.detail_level)
        
        # Additional options (will be dynamically updated)
        self.options_layout = QFormLayout()
        report_layout.addRow(self.options_layout)
        
        # Generate button
        self.generate_btn = QPushButton("Generate Report")
        self.generate_btn.clicked.connect(self.generateReport)
        report_layout.addRow("", self.generate_btn)
        
        report_group.setLayout(report_layout)
        main_layout.addWidget(report_group)
        
        # Report results
        results_group = QGroupBox("Report Results")
        results_layout = QVBoxLayout()
        
        self.report_table = QTableWidget()
        self.report_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        results_layout.addWidget(self.report_table)
        
        # Action buttons
        actions_layout = QHBoxLayout()
        
        self.export_csv_btn = QPushButton("Export to CSV")
        self.export_csv_btn.clicked.connect(self.exportToCsv)
        
        self.export_pdf_btn = QPushButton("Export to PDF")
        self.export_pdf_btn.clicked.connect(self.exportToPdf)
        
        self.print_btn = QPushButton("Print")
        self.print_btn.clicked.connect(self.printReport)
        
        self.print_preview_btn = QPushButton("Print Preview")
        self.print_preview_btn.clicked.connect(self.printPreview)
        
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
        """Load customers into combo box"""
        try:
            self.db.connect()
            
            # Get all customers
            self.db.cursor.execute('SELECT id, name FROM customers ORDER BY name')
            customers = self.db.cursor.fetchall()
            
            # Add to combo box
            for customer_id, name in customers:
                self.customer_combo.addItem(name, customer_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customers: {str(e)}")
        finally:
            self.db.close()
            
    def loadProducts(self):
        """Load distinct product names into combo box"""
        try:
            self.db.connect()
            
            # Get distinct product names
            self.db.cursor.execute('SELECT DISTINCT name FROM products ORDER BY name')
            products = self.db.cursor.fetchall()
            
            # Add to combo box
            for (name,) in products:
                self.product_combo.addItem(name, name)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load products: {str(e)}")
        finally:
            self.db.close()
            
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
        """Generate sales by period report with batch information"""
        try:
            self.db.connect()
            
            if detail_level == "Summary":
                # Get summary data
                query = """
                    SELECT 
                        strftime('%Y-%m-%d', e.date) as date,
                        SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as credit,
                        SUM(CASE WHEN e.is_credit = 0 THEN e.quantity * e.unit_price ELSE 0 END) as debit,
                        SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE -e.quantity * e.unit_price END) as net
                    FROM entries e
                    WHERE e.date BETWEEN ? AND ?
                    GROUP BY date
                    ORDER BY date
                """
                
                self.db.cursor.execute(query, (from_date, to_date))
                
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                self.report_table.setColumnCount(4)
                self.report_table.setHorizontalHeaderLabels(["Date", "Credit", "Debit", "Net"])
                
                # Fill table
                data = self.db.cursor.fetchall()
                self.report_table.setRowCount(len(data))
                
                total_credit = 0
                total_debit = 0
                total_net = 0
                
                for row, (date, credit, debit, net) in enumerate(data):
                    self.report_table.setItem(row, 0, QTableWidgetItem(date))
                    self.report_table.setItem(row, 1, QTableWidgetItem(f"Rs. {credit:.2f}"))
                    self.report_table.setItem(row, 2, QTableWidgetItem(f"Rs. {debit:.2f}"))
                    
                    net_item = QTableWidgetItem(f"Rs. {net:.2f}")
                    net_item.setForeground(Qt.green if net >= 0 else Qt.red)
                    self.report_table.setItem(row, 3, net_item)
                    
                    total_credit += credit
                    total_debit += debit
                    total_net += net
                
                # Add total row
                total_row = self.report_table.rowCount()
                self.report_table.insertRow(total_row)
                self.report_table.setItem(total_row, 0, QTableWidgetItem("TOTAL"))
                self.report_table.setItem(total_row, 1, QTableWidgetItem(f"Rs. {total_credit:.2f}"))
                self.report_table.setItem(total_row, 2, QTableWidgetItem(f"Rs. {total_debit:.2f}"))
                
                net_item = QTableWidgetItem(f"Rs. {total_net:.2f}")
                net_item.setForeground(Qt.green if total_net >= 0 else Qt.red)
                self.report_table.setItem(total_row, 3, net_item)
                
                # Format total row
                for col in range(self.report_table.columnCount()):
                    item = self.report_table.item(total_row, col)
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
                
            else:  # Detailed report
                query = """
                    SELECT 
                        e.id,
                        strftime('%Y-%m-%d', e.date) as date,
                        c.name as customer,
                        p.name as product,
                        p.batch_number,
                        p.expiry_date,
                        e.quantity,
                        e.unit_price,
                        (e.quantity * e.unit_price) as total,
                        e.is_credit,
                        e.notes
                    FROM entries e
                    JOIN customers c ON e.customer_id = c.id
                    JOIN products p ON e.product_id = p.id
                    WHERE e.date BETWEEN ? AND ?
                    ORDER BY e.date, e.id
                """
                
                self.db.cursor.execute(query, (from_date, to_date))
                
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                self.report_table.setColumnCount(10)
                self.report_table.setHorizontalHeaderLabels([
                    "ID", "Date", "Customer", "Product", "Batch", "Expiry", 
                    "Quantity", "Unit Price", "Total", "Type"
                ])
                
                # Fill table
                data = self.db.cursor.fetchall()
                self.report_table.setRowCount(len(data))
                
                total_credit = 0
                total_debit = 0
                current_date = QDate.currentDate()
                
                for row, (id, date, customer, product, batch_number, expiry_date, quantity, unit_price, total, is_credit, _) in enumerate(data):
                    self.report_table.setItem(row, 0, QTableWidgetItem(str(id)))
                    self.report_table.setItem(row, 1, QTableWidgetItem(date))
                    self.report_table.setItem(row, 2, QTableWidgetItem(customer))
                    self.report_table.setItem(row, 3, QTableWidgetItem(product))
                    self.report_table.setItem(row, 4, QTableWidgetItem(batch_number or ""))
                    
                    # Color-code expiry date
                    expiry_item = QTableWidgetItem(expiry_date or "")
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
                    self.report_table.setItem(row, 7, QTableWidgetItem(f"Rs. {unit_price:.2f}"))
                    self.report_table.setItem(row, 8, QTableWidgetItem(f"Rs. {total:.2f}"))
                    
                    type_item = QTableWidgetItem("Credit" if is_credit else "Debit")
                    type_item.setForeground(Qt.green if is_credit else Qt.red)
                    self.report_table.setItem(row, 9, type_item)
                    
                    if is_credit:
                        total_credit += total
                    else:
                        total_debit += total
                
                # Add total row
                total_row = self.report_table.rowCount()
                self.report_table.insertRow(total_row)
                self.report_table.setItem(total_row, 0, QTableWidgetItem("TOTAL"))
                self.report_table.setItem(total_row, 8, QTableWidgetItem(f"Credit: Rs. {total_credit:.2f} / Debit: Rs. {total_debit:.2f}"))
                self.report_table.setItem(total_row, 9, QTableWidgetItem(f"Net: Rs. {total_credit - total_debit:.2f}"))
                
                # Format total row
                for col in range(self.report_table.columnCount()):
                    item = self.report_table.item(total_row, col)
                    if item:
                        font = item.font()
                        font.setBold(True)
                        item.setFont(font)
            
        except Exception as e:
            raise Exception(f"Error generating sales by period report: {str(e)}")
        finally:
            self.db.close()
            
    def generateSalesByCustomer(self, from_date, to_date, detail_level, customer_id, show_totals):
        """Generate sales by customer report with batch information"""
        try:
            self.db.connect()
            
            # Build the customer filter
            customer_filter = ""
            params = [from_date, to_date]
            
            if customer_id is not None:
                customer_filter = "AND e.customer_id = ?"
                params.append(customer_id)
            
            if detail_level == "Summary" or show_totals:
                # Get summary data by customer
                query = f"""
                    SELECT 
                        c.id,
                        c.name,
                        SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as credit,
                        SUM(CASE WHEN e.is_credit = 0 THEN e.quantity * e.unit_price ELSE 0 END) as debit,
                        SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE -e.quantity * e.unit_price END) as net,
                        COUNT(e.id) as transaction_count
                    FROM entries e
                    JOIN customers c ON e.customer_id = c.id
                    WHERE e.date BETWEEN ? AND ? {customer_filter}
                    GROUP BY c.id, c.name
                    ORDER BY net DESC
                """
                
                self.db.cursor.execute(query, params)
                
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                self.report_table.setColumnCount(6)
                self.report_table.setHorizontalHeaderLabels([
                    "ID", "Customer", "Credit", "Debit", "Net", "Transaction Count"
                ])
                
                # Fill table
                data = self.db.cursor.fetchall()
                self.report_table.setRowCount(len(data))
                
                total_credit = 0
                total_debit = 0
                total_net = 0
                total_transactions = 0
                
                for row, (id, name, credit, debit, net, count) in enumerate(data):
                    self.report_table.setItem(row, 0, QTableWidgetItem(str(id)))
                    self.report_table.setItem(row, 1, QTableWidgetItem(name))
                    self.report_table.setItem(row, 2, QTableWidgetItem(f"Rs. {credit:.2f}"))
                    self.report_table.setItem(row, 3, QTableWidgetItem(f"Rs. {debit:.2f}"))
                    
                    net_item = QTableWidgetItem(f"Rs. {net:.2f}")
                    net_item.setForeground(Qt.green if net >= 0 else Qt.red)
                    self.report_table.setItem(row, 4, net_item)
                    
                    self.report_table.setItem(row, 5, QTableWidgetItem(str(count)))
                    
                    total_credit += credit
                    total_debit += debit
                    total_net += net
                    total_transactions += count
                
                # Add total row
                total_row = self.report_table.rowCount()
                self.report_table.insertRow(total_row)
                self.report_table.setItem(total_row, 1, QTableWidgetItem("TOTAL"))
                self.report_table.setItem(total_row, 2, QTableWidgetItem(f"Rs. {total_credit:.2f}"))
                self.report_table.setItem(total_row, 3, QTableWidgetItem(f"Rs. {total_debit:.2f}"))
                
                net_item = QTableWidgetItem(f"Rs. {total_net:.2f}")
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
                query = f"""
                    SELECT 
                        e.id,
                        strftime('%Y-%m-%d', e.date) as date,
                        c.name as customer,
                        p.name as product,
                        p.batch_number,
                        p.expiry_date,
                        e.quantity,
                        e.unit_price,
                        (e.quantity * e.unit_price) as total,
                        e.is_credit
                    FROM entries e
                    JOIN customers c ON e.customer_id = c.id
                    JOIN products p ON e.product_id = p.id
                    WHERE e.date BETWEEN ? AND ? {customer_filter}
                    ORDER BY c.name, e.date
                """
                
                self.db.cursor.execute(query, params)
                
                # Set up table
                self.report_table.clear()
                self.report_table.setRowCount(0)
                self.report_table.setColumnCount(10)
                self.report_table.setHorizontalHeaderLabels([
                    "ID", "Date", "Customer", "Product", "Batch", "Expiry",
                    "Quantity", "Unit Price", "Total", "Type"
                ])
                
                # Fill table
                data = self.db.cursor.fetchall()
                self.report_table.setRowCount(len(data))
                
                for row, (id, date, customer, product, batch_number, expiry_date, quantity, unit_price, total, is_credit) in enumerate(data):
                    self.report_table.setItem(row, 0, QTableWidgetItem(str(id)))
                    self.report_table.setItem(row, 1, QTableWidgetItem(date))
                    self.report_table.setItem(row, 2, QTableWidgetItem(customer))
                    self.report_table.setItem(row, 3, QTableWidgetItem(product))
                    self.report_table.setItem(row, 4, QTableWidgetItem(batch_number or ""))
                    self.report_table.setItem(row, 5, QTableWidgetItem(expiry_date or ""))
                    self.report_table.setItem(row, 6, QTableWidgetItem(str(quantity)))
                    self.report_table.setItem(row, 7, QTableWidgetItem(f"Rs. {unit_price:.2f}"))
                    self.report_table.setItem(row, 8, QTableWidgetItem(f"Rs. {total:.2f}"))
                    
                    type_item = QTableWidgetItem("Credit" if is_credit else "Debit")
                    type_item.setForeground(Qt.green if is_credit else Qt.red)
                    self.report_table.setItem(row, 9, type_item)
                
        except Exception as e:
            raise Exception(f"Error generating sales by customer report: {str(e)}")
        finally:
            self.db.close()
            
    def generateSalesByProduct(self, from_date, to_date, detail_level, product_name, show_quantity, group_by_name):
        """Generate sales by product report with batch analysis"""
        try:
            self.db.connect()
            
            # Build the product filter
            product_filter = ""
            params = [from_date, to_date]
            
            if product_name is not None:
                product_filter = "AND p.name = ?"
                params.append(product_name)
            
            if group_by_name:
                # Group by product name (combines all batches)
                if detail_level == "Summary":
                    query = f"""
                        SELECT 
                            p.name,
                            SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as total_sales,
                            SUM(CASE WHEN e.is_credit = 1 THEN e.quantity ELSE 0 END) as total_quantity,
                            COUNT(DISTINCT p.batch_number) as batch_count,
                            MIN(p.expiry_date) as earliest_expiry,
                            MAX(p.expiry_date) as latest_expiry
                        FROM entries e
                        JOIN products p ON e.product_id = p.id
                        WHERE e.date BETWEEN ? AND ? {product_filter}
                        GROUP BY p.name
                        ORDER BY total_sales DESC
                    """
                    
                    self.db.cursor.execute(query, params)
                    
                    # Set up table
                    self.report_table.clear()
                    self.report_table.setRowCount(0)
                    columns = ["Product", "Total Sales", "Batches", "Earliest Expiry", "Latest Expiry"]
                    if show_quantity:
                        columns.insert(2, "Total Quantity")
                    
                    self.report_table.setColumnCount(len(columns))
                    self.report_table.setHorizontalHeaderLabels(columns)
                    
                    # Fill table
                    data = self.db.cursor.fetchall()
                    self.report_table.setRowCount(len(data))
                    
                    for row, (name, total_sales, total_quantity, batch_count, earliest_expiry, latest_expiry) in enumerate(data):
                        col = 0
                        self.report_table.setItem(row, col, QTableWidgetItem(name))
                        col += 1
                        self.report_table.setItem(row, col, QTableWidgetItem(f"Rs. {total_sales:.2f}"))
                        col += 1
                        
                        if show_quantity:
                            self.report_table.setItem(row, col, QTableWidgetItem(str(total_quantity)))
                            col += 1
                        
                        self.report_table.setItem(row, col, QTableWidgetItem(str(batch_count)))
                        col += 1
                        self.report_table.setItem(row, col, QTableWidgetItem(earliest_expiry or "N/A"))
                        col += 1
                        self.report_table.setItem(row, col, QTableWidgetItem(latest_expiry or "N/A"))
                        
            else:
                # Show individual batches
                if detail_level == "Summary":
                    query = f"""
                        SELECT 
                            p.name,
                            p.batch_number,
                            p.expiry_date,
                            SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as total_sales,
                            SUM(CASE WHEN e.is_credit = 1 THEN e.quantity ELSE 0 END) as total_quantity
                        FROM entries e
                        JOIN products p ON e.product_id = p.id
                        WHERE e.date BETWEEN ? AND ? {product_filter}
                        GROUP BY p.id, p.name, p.batch_number, p.expiry_date
                        ORDER BY total_sales DESC
                    """
                    
                    self.db.cursor.execute(query, params)
                    
                    # Set up table
                    self.report_table.clear()
                    self.report_table.setRowCount(0)
                    columns = ["Product", "Batch", "Expiry Date", "Total Sales"]
                    if show_quantity:
                        columns.append("Total Quantity")
                    
                    self.report_table.setColumnCount(len(columns))
                    self.report_table.setHorizontalHeaderLabels(columns)
                    
                    # Fill table
                    data = self.db.cursor.fetchall()
                    self.report_table.setRowCount(len(data))
                    current_date = QDate.currentDate()
                    
                    for row, (name, batch_number, expiry_date, total_sales, total_quantity) in enumerate(data):
                        self.report_table.setItem(row, 0, QTableWidgetItem(name))
                        self.report_table.setItem(row, 1, QTableWidgetItem(batch_number or ""))
                        
                        # Color-code expiry date
                        expiry_item = QTableWidgetItem(expiry_date or "")
                        try:
                            expiry_qdate = QDate.fromString(expiry_date, "yyyy-MM-dd")
                            if expiry_qdate.isValid():
                                if expiry_qdate < current_date:
                                    expiry_item.setForeground(QColor("#cc0000"))  # Red for expired
                                elif expiry_qdate < current_date.addDays(30):
                                    expiry_item.setForeground(QColor("#856404"))  # Orange for expiring soon
                        except:
                            pass
                        self.report_table.setItem(row, 2, expiry_item)
                        
                        self.report_table.setItem(row, 3, QTableWidgetItem(f"Rs. {total_sales:.2f}"))
                        
                        if show_quantity:
                            self.report_table.setItem(row, 4, QTableWidgetItem(str(total_quantity)))
                    
        except Exception as e:
            raise Exception(f"Error generating sales by product report: {str(e)}")
        finally:
            self.db.close()
    
    def generateBatchAnalysis(self, from_date, to_date, detail_level, include_batch_info, show_expired_only):
        """Generate product batch analysis report"""
        try:
            self.db.connect()
            
            # Build expiry filter
            expiry_filter = ""
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            
            if show_expired_only:
                expiry_filter = f"AND p.expiry_date < '{current_date}'"
            
            query = f"""
                SELECT 
                    p.name,
                    p.batch_number,
                    p.expiry_date,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as total_sales,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity ELSE 0 END) as total_quantity,
                    COUNT(e.id) as transaction_count,
                    CASE 
                        WHEN p.expiry_date < '{current_date}' THEN 'EXPIRED'
                        WHEN p.expiry_date <= date('{current_date}', '+30 days') THEN 'EXPIRING SOON'
                        ELSE 'VALID'
                    END as status
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.date BETWEEN ? AND ? {expiry_filter}
                GROUP BY p.id, p.name, p.batch_number, p.expiry_date
                ORDER BY p.expiry_date, total_sales DESC
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            
            # Set up table
            self.report_table.clear()
            self.report_table.setRowCount(0)
            self.report_table.setColumnCount(7)
            self.report_table.setHorizontalHeaderLabels([
                "Product", "Batch Number", "Expiry Date", "Total Sales", 
                "Total Quantity", "Transactions", "Status"
            ])
            
            # Fill table
            data = self.db.cursor.fetchall()
            self.report_table.setRowCount(len(data))
            
            total_sales = 0
            total_quantity = 0
            
            for row, (name, batch_number, expiry_date, sales, quantity, trans_count, status) in enumerate(data):
                self.report_table.setItem(row, 0, QTableWidgetItem(name))
                self.report_table.setItem(row, 1, QTableWidgetItem(batch_number or ""))
                self.report_table.setItem(row, 2, QTableWidgetItem(expiry_date or ""))
                self.report_table.setItem(row, 3, QTableWidgetItem(f"Rs. {sales:.2f}"))
                self.report_table.setItem(row, 4, QTableWidgetItem(str(quantity)))
                self.report_table.setItem(row, 5, QTableWidgetItem(str(trans_count)))
                
                # Color-code status
                status_item = QTableWidgetItem(status)
                if status == "EXPIRED":
                    status_item.setForeground(QColor("#cc0000"))
                elif status == "EXPIRING SOON":
                    status_item.setForeground(QColor("#856404"))
                else:
                    status_item.setForeground(QColor("#155724"))
                self.report_table.setItem(row, 6, status_item)
                
                total_sales += sales
                total_quantity += quantity
            
            # Add summary row
            summary_row = self.report_table.rowCount()
            self.report_table.insertRow(summary_row)
            self.report_table.setItem(summary_row, 0, QTableWidgetItem("TOTAL"))
            self.report_table.setItem(summary_row, 3, QTableWidgetItem(f"Rs. {total_sales:.2f}"))
            self.report_table.setItem(summary_row, 4, QTableWidgetItem(str(total_quantity)))
            
            # Bold the summary row
            for col in range(self.report_table.columnCount()):
                item = self.report_table.item(summary_row, col)
                if item:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
            
        except Exception as e:
            raise Exception(f"Error generating batch analysis report: {str(e)}")
        finally:
            self.db.close()
    
    def generateExpiryReport(self, from_date, to_date, detail_level, threshold_days, include_expired):
        """Generate expiry date analysis report"""
        try:
            self.db.connect()
            
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            threshold_date = QDate.currentDate().addDays(threshold_days).toString("yyyy-MM-dd")
            
            # Build expiry filter
            if include_expired:
                expiry_filter = f"AND p.expiry_date <= '{threshold_date}'"
            else:
                expiry_filter = f"AND p.expiry_date > '{current_date}' AND p.expiry_date <= '{threshold_date}'"
            
            query = f"""
                SELECT 
                    p.name,
                    p.batch_number,
                    p.expiry_date,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as total_sales,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity ELSE 0 END) as total_quantity,
                    julianday(p.expiry_date) - julianday('{current_date}') as days_to_expiry,
                    CASE 
                        WHEN p.expiry_date < '{current_date}' THEN 'EXPIRED'
                        WHEN p.expiry_date <= date('{current_date}', '+30 days') THEN 'EXPIRING SOON'
                        ELSE 'VALID'
                    END as status
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.date BETWEEN ? AND ? {expiry_filter}
                GROUP BY p.id, p.name, p.batch_number, p.expiry_date
                ORDER BY p.expiry_date
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            
            # Set up table
            self.report_table.clear()
            self.report_table.setRowCount(0)
            self.report_table.setColumnCount(7)
            self.report_table.setHorizontalHeaderLabels([
                "Product", "Batch Number", "Expiry Date", "Days to Expiry",
                "Total Sales", "Total Quantity", "Status"
            ])
            
            # Fill table
            data = self.db.cursor.fetchall()
            self.report_table.setRowCount(len(data))
            
            total_sales = 0
            total_quantity = 0
            expired_count = 0
            expiring_count = 0
            
            for row, (name, batch_number, expiry_date, sales, quantity, days_to_expiry, status) in enumerate(data):
                self.report_table.setItem(row, 0, QTableWidgetItem(name))
                self.report_table.setItem(row, 1, QTableWidgetItem(batch_number or ""))
                self.report_table.setItem(row, 2, QTableWidgetItem(expiry_date or ""))
                
                # Days to expiry
                days_item = QTableWidgetItem(f"{int(days_to_expiry)}" if days_to_expiry is not None else "N/A")
                if days_to_expiry is not None and days_to_expiry < 0:
                    days_item.setForeground(QColor("#cc0000"))
                elif days_to_expiry is not None and days_to_expiry <= 30:
                    days_item.setForeground(QColor("#856404"))
                self.report_table.setItem(row, 3, days_item)
                
                self.report_table.setItem(row, 4, QTableWidgetItem(f"Rs. {sales:.2f}"))
                self.report_table.setItem(row, 5, QTableWidgetItem(str(quantity)))
                
                # Status with color coding
                status_item = QTableWidgetItem(status)
                if status == "EXPIRED":
                    status_item.setForeground(QColor("#cc0000"))
                    expired_count += 1
                elif status == "EXPIRING SOON":
                    status_item.setForeground(QColor("#856404"))
                    expiring_count += 1
                else:
                    status_item.setForeground(QColor("#155724"))
                self.report_table.setItem(row, 6, status_item)
                
                total_sales += sales
                total_quantity += quantity
            
            # Add summary information
            summary_row = self.report_table.rowCount()
            self.report_table.insertRow(summary_row)
            self.report_table.setItem(summary_row, 0, QTableWidgetItem("SUMMARY"))
            self.report_table.setItem(summary_row, 1, QTableWidgetItem(f"Expired: {expired_count}, Expiring: {expiring_count}"))
            self.report_table.setItem(summary_row, 4, QTableWidgetItem(f"Rs. {total_sales:.2f}"))
            self.report_table.setItem(summary_row, 5, QTableWidgetItem(str(total_quantity)))
            
            # Bold the summary row
            for col in range(self.report_table.columnCount()):
                item = self.report_table.item(summary_row, col)
                if item:
                    font = item.font()
                    font.setBold(True)
                    item.setFont(font)
            
        except Exception as e:
            raise Exception(f"Error generating expiry report: {str(e)}")
        finally:
            self.db.close()
    
    def generateProfitAndLoss(self, from_date, to_date, detail_level, grouping, include_chart):
        """Generate profit and loss report"""
        # Implementation for profit and loss report with optional chart
        pass  # Full implementation would include grouping by day/week/month
    
    def generateInventoryValuation(self, from_date, to_date, detail_level):
        """Generate inventory valuation report"""
        # Implementation for inventory valuation based on transactions
        pass
    
    def generateCustomerBalance(self, from_date, to_date, detail_level):
        """Generate customer balance report"""
        # Implementation for customer balance/account statements
        pass
    
    def generateOutstandingPayments(self, from_date, to_date, detail_level, min_days):
        """Generate outstanding payments report"""
        # Implementation for tracking outstanding/overdue payments
        pass
    
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
        """Export report to PDF file"""
        # Implementation for exporting the current report to PDF
        QMessageBox.information(self, "PDF Export", "PDF export functionality will be implemented in a future update.")
    
    def printReport(self):
        """Print the current report"""
        # Implementation for printing the current report
        QMessageBox.information(self, "Print", "Print functionality will be implemented in a future update.")
    
    def printPreview(self):
        """Show print preview for the current report"""
        # Implementation for showing print preview
        QMessageBox.information(self, "Print Preview", "Print preview functionality will be implemented in a future update.")