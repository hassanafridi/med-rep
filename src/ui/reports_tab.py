from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, QLabel, 
    QPushButton, QDateEdit, QGroupBox, QFormLayout,
    QTableWidget, QTableWidgetItem, QHeaderView, QFileDialog,
    QMessageBox, QCheckBox, QSpinBox
)
from PyQt5.QtCore import QDate, Qt
from PyQt5.QtPrintSupport import QPrinter, QPrintDialog, QPrintPreviewDialog
import sys
import os
import datetime

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
        """Load products into combo box"""
        try:
            self.db.connect()
            
            # Get all products
            self.db.cursor.execute('SELECT id, name FROM products ORDER BY name')
            products = self.db.cursor.fetchall()
            
            # Add to combo box
            for product_id, name in products:
                self.product_combo.addItem(name, product_id)
                
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
                product_id = self.product_combo.currentData()
                show_quantity = self.show_quantity.isChecked()
                self.generateSalesByProduct(from_date, to_date, detail_level, product_id, show_quantity)
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
        """Generate sales by period report"""
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
                    self.report_table.setItem(row, 1, QTableWidgetItem(f"${credit:.2f}"))
                    self.report_table.setItem(row, 2, QTableWidgetItem(f"${debit:.2f}"))
                    
                    net_item = QTableWidgetItem(f"${net:.2f}")
                    net_item.setForeground(Qt.green if net >= 0 else Qt.red)
                    self.report_table.setItem(row, 3, net_item)
                    
                    total_credit += credit
                    total_debit += debit
                    total_net += net
                
                # Add total row
                total_row = self.report_table.rowCount()
                self.report_table.insertRow(total_row)
                self.report_table.setItem(total_row, 0, QTableWidgetItem("TOTAL"))
                self.report_table.setItem(total_row, 1, QTableWidgetItem(f"${total_credit:.2f}"))
                self.report_table.setItem(total_row, 2, QTableWidgetItem(f"${total_debit:.2f}"))
                
                net_item = QTableWidgetItem(f"${total_net:.2f}")
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
                self.report_table.setColumnCount(8)
                self.report_table.setHorizontalHeaderLabels([
                    "ID", "Date", "Customer", "Product", 
                    "Quantity", "Unit Price", "Total", "Type"
                ])
                
                # Fill table
                data = self.db.cursor.fetchall()
                self.report_table.setRowCount(len(data))
                
                total_credit = 0
                total_debit = 0
                
                for row, (id, date, customer, product, quantity, unit_price, total, is_credit, _) in enumerate(data):
                    self.report_table.setItem(row, 0, QTableWidgetItem(str(id)))
                    self.report_table.setItem(row, 1, QTableWidgetItem(date))
                    self.report_table.setItem(row, 2, QTableWidgetItem(customer))
                    self.report_table.setItem(row, 3, QTableWidgetItem(product))
                    self.report_table.setItem(row, 4, QTableWidgetItem(str(quantity)))
                    self.report_table.setItem(row, 5, QTableWidgetItem(f"${unit_price:.2f}"))
                    self.report_table.setItem(row, 6, QTableWidgetItem(f"${total:.2f}"))
                    
                    type_item = QTableWidgetItem("Credit" if is_credit else "Debit")
                    type_item.setForeground(Qt.green if is_credit else Qt.red)
                    self.report_table.setItem(row, 7, type_item)
                    
                    if is_credit:
                        total_credit += total
                    else:
                        total_debit += total
                
                # Add total row
                total_row = self.report_table.rowCount()
                self.report_table.insertRow(total_row)
                self.report_table.setItem(total_row, 0, QTableWidgetItem("TOTAL"))
                self.report_table.setItem(total_row, 6, QTableWidgetItem(f"Credit: ${total_credit:.2f} / Debit: ${total_debit:.2f}"))
                self.report_table.setItem(total_row, 7, QTableWidgetItem(f"Net: ${total_credit - total_debit:.2f}"))
                
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
        """Generate sales by customer report"""
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
                    self.report_table.setItem(row, 2, QTableWidgetItem(f"${credit:.2f}"))
                    self.report_table.setItem(row, 3, QTableWidgetItem(f"${debit:.2f}"))
                    
                    net_item = QTableWidgetItem(f"${net:.2f}")
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
                self.report_table.setItem(total_row, 2, QTableWidgetItem(f"${total_credit:.2f}"))
                self.report_table.setItem(total_row, 3, QTableWidgetItem(f"${total_debit:.2f}"))
                
                net_item = QTableWidgetItem(f"${total_net:.2f}")
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
                        
            elif detail_level == "Detailed" and not show_totals:
                # Get detailed data by customer and transaction
                query = f"""
                    SELECT 
                        e.id,
                        strftime('%Y-%m-%d', e.date) as date,
                        c.name as customer,
                        p.name as product,
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
                self.report_table.setColumnCount(8)
                self.report_table.setHorizontalHeaderLabels([
                    "ID", "Date", "Customer", "Product", 
                    "Quantity", "Unit Price", "Total", "Type"
                ])
                
                # Fill table
                data = self.db.cursor.fetchall()
                self.report_table.setRowCount(len(data))
                
                current_customer = None
                customer_total = 0
                
                for row, (id, date, customer, product, quantity, unit_price, total, is_credit) in enumerate(data):
                    # If customer changes, add a subtotal row
                    if current_customer is not None and current_customer != customer:
                        subtotal_row = row + row_offset
                        self.report_table.insertRow(subtotal_row)
                        self.report_table.setItem(subtotal_row, 2, QTableWidgetItem(f"{current_customer} Total:"))
                        self.report_table.setItem(subtotal_row, 6, QTableWidgetItem(f"${customer_total:.2f}"))
                        
                        # Format subtotal row
                        for col in range(self.report_table.columnCount()):
                            item = self.report_table.item(subtotal_row, col)
                            if item:
                                font = item.font()
                                font.setBold(True)
                                item.setFont(font)
                        
                        customer_total = 0
                        row_offset += 1
                    
                    current_customer = customer
                    
                    # Add transaction row
                    actual_row = row + row_offset
                    
                    self.report_table.setItem(actual_row, 0, QTableWidgetItem(str(id)))
                    self.report_table.setItem(actual_row, 1, QTableWidgetItem(date))
                    self.report_table.setItem(actual_row, 2, QTableWidgetItem(customer))
                    self.report_table.setItem(actual_row, 3, QTableWidgetItem(product))
                    self.report_table.setItem(actual_row, 4, QTableWidgetItem(str(quantity)))
                    self.report_table.setItem(actual_row, 5, QTableWidgetItem(f"${unit_price:.2f}"))
                    self.report_table.setItem(actual_row, 6, QTableWidgetItem(f"${total:.2f}"))
                    
                    type_item = QTableWidgetItem("Credit" if is_credit else "Debit")
                    type_item.setForeground(Qt.green if is_credit else Qt.red)
                    self.report_table.setItem(actual_row, 7, type_item)
                    
                    # Update customer total
                    customer_total += total if is_credit else -total
                
                # Add final customer subtotal
                if current_customer is not None:
                    subtotal_row = self.report_table.rowCount()
                    self.report_table.insertRow(subtotal_row)
                    self.report_table.setItem(subtotal_row, 2, QTableWidgetItem(f"{current_customer} Total:"))
                    self.report_table.setItem(subtotal_row, 6, QTableWidgetItem(f"${customer_total:.2f}"))
                    
                    # Format subtotal row
                    for col in range(self.report_table.columnCount()):
                        item = self.report_table.item(subtotal_row, col)
                        if item:
                            font = item.font()
                            font.setBold(True)
                            item.setFont(font)
                
        except Exception as e:
            raise Exception(f"Error generating sales by customer report: {str(e)}")
        finally:
            self.db.close()
            
    def generateSalesByProduct(self, from_date, to_date, detail_level, product_id, show_quantity):
        """Generate sales by product report"""
        # Similar implementation to sales by customer, but grouped by product
        pass  # Actual implementation would be similar to generateSalesByCustomer
    
    def generateProfitAndLoss(self, from_date, to_date, detail_level, grouping, include_chart):
        """Generate profit and loss report"""
        # Implementation of profit and loss report with optional chart
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
        # Implementation for exporting the current report to CSV
        pass
    
    def exportToPdf(self):
        """Export report to PDF file"""
        # Implementation for exporting the current report to PDF
        pass
    
    def printReport(self):
        """Print the current report"""
        # Implementation for printing the current report
        pass
    
    def printPreview(self):
        """Show print preview for the current report"""
        # Implementation for showing print preview
        pass