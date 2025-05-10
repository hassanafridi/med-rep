from PyQt5.QtWidgets import (
    QWidget, 
    QVBoxLayout, 
    QHBoxLayout, 
    QTableWidget, 
    QTableWidgetItem,
    QPushButton, 
    QLineEdit, 
    QLabel, 
    QDateEdit, 
    QComboBox, 
    QMenu, 
    QAction, 
    QMessageBox, 
    QHeaderView, 
    QGroupBox, 
    QFormLayout, 
    QFileDialog,
    QDialog, 
    QDialogButtonBox, 
    QCheckBox, 
    QSpinBox,
    QDoubleSpinBox,
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import sys
import os
import csv

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Database

class LedgerTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Create search/filter section
        filter_group = QGroupBox("Search & Filter")
        filter_layout = QFormLayout()
        
        # Date range filters
        date_range_layout = QHBoxLayout()
        
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setDate(QDate.currentDate().addDays(-30))  # Default to last 30 days
        self.from_date_edit.setCalendarPopup(True)
        
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setCalendarPopup(True)
        
        date_range_layout.addWidget(QLabel("From:"))
        date_range_layout.addWidget(self.from_date_edit)
        date_range_layout.addWidget(QLabel("To:"))
        date_range_layout.addWidget(self.to_date_edit)
        
        filter_layout.addRow("Date Range:", date_range_layout)
        
        # Customer filter
        self.customer_filter = QComboBox()
        self.customer_filter.addItem("All Customers", None)
        filter_layout.addRow("Customer:", self.customer_filter)
        
        # Search by note text
        self.search_text = QLineEdit()
        self.search_text.setPlaceholderText("Search by notes...")
        filter_layout.addRow("Search Notes:", self.search_text)
        
        # Entry type filter
        self.entry_type_filter = QComboBox()
        self.entry_type_filter.addItems(["All Entries", "Credit Only", "Debit Only"])
        filter_layout.addRow("Entry Type:", self.entry_type_filter)
        
        # Apply filter button
        button_layout = QHBoxLayout()
        
        self.apply_filter_btn = QPushButton("Apply Filters")
        self.apply_filter_btn.clicked.connect(self.loadEntries)
        
        self.clear_filter_btn = QPushButton("Clear Filters")
        self.clear_filter_btn.clicked.connect(self.clearFilters)
        
        button_layout.addWidget(self.apply_filter_btn)
        button_layout.addWidget(self.clear_filter_btn)
        
        filter_layout.addRow("", button_layout)
        filter_group.setLayout(filter_layout)
        main_layout.addWidget(filter_group)
        
        # Create table for entries
        self.entries_table = QTableWidget()
        self.entries_table.setColumnCount(9)
        self.entries_table.setHorizontalHeaderLabels([
            "ID", "Date", "Customer", "Product", "Quantity", 
            "Unit Price", "Total", "Type", "Notes"
        ])
        # Add Generate Report button (if not already defined)
        self.report_btn = QPushButton("Generate Report")
        self.report_btn.clicked.connect(self.generateReport)

        # Add it to your layout (you might need to adjust this to match your existing layout)
        button_layout.addWidget(self.report_btn)  # or add it to summary_layout if that's where it belongs
        
        # Set column widths
        self.entries_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.entries_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)  # ID column
        
        # Enable context menu
        self.entries_table.setContextMenuPolicy(Qt.CustomContextMenu)
        self.entries_table.customContextMenuRequested.connect(self.showContextMenu)
        
        main_layout.addWidget(self.entries_table)
        
        # Summary section
        summary_layout = QHBoxLayout()
        self.total_entries_label = QLabel("Total Entries: 0")
        self.total_credit_label = QLabel("Total Credit: $0.00")
        self.total_debit_label = QLabel("Total Debit: $0.00")
        self.balance_label = QLabel("Current Balance: $0.00")
        
        summary_layout.addWidget(self.total_entries_label)
        summary_layout.addWidget(self.total_credit_label)
        summary_layout.addWidget(self.total_debit_label)
        summary_layout.addWidget(self.balance_label)
        
        main_layout.addLayout(summary_layout)
        
        # Set main layout
        self.setLayout(main_layout)
        
        # Load data
        self.loadCustomers()
        self.loadEntries()
        
        # Add Export button
        self.export_btn = QPushButton("Export to CSV")
        self.export_btn.clicked.connect(self.exportToCSV)
        summary_layout.addWidget(self.export_btn)
    
    def loadCustomers(self):
        """Load customers for filter dropdown"""
        try:
            self.db.connect()
            
            # Get all customers
            self.db.cursor.execute('SELECT id, name FROM customers ORDER BY name')
            customers = self.db.cursor.fetchall()
            
            # Add customers to filter dropdown
            for customer_id, name in customers:
                self.customer_filter.addItem(name, customer_id)
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customers: {str(e)}")
        finally:
            self.db.close()
    
    def loadEntries(self):
        """Load entries based on current filters"""
        try:
            self.db.connect()
            
            # Build query based on filters
            query = '''
                SELECT 
                    e.id, e.date, c.name as customer, p.name as product,
                    e.quantity, e.unit_price, (e.quantity * e.unit_price) as total,
                    e.is_credit, e.notes
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                JOIN products p ON e.product_id = p.id
                WHERE 1=1
            '''
            
            params = []
            
            # Date range filter
            from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
            to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
            query += " AND e.date BETWEEN ? AND ?"
            params.extend([from_date, to_date])
            
            # Customer filter
            selected_customer_id = self.customer_filter.currentData()
            if selected_customer_id is not None:
                query += " AND e.customer_id = ?"
                params.append(selected_customer_id)
            
            # Note text search
            search_text = self.search_text.text().strip()
            if search_text:
                query += " AND e.notes LIKE ?"
                params.append(f"%{search_text}%")
            
            # Entry type filter
            entry_type = self.entry_type_filter.currentText()
            if entry_type == "Credit Only":
                query += " AND e.is_credit = 1"
            elif entry_type == "Debit Only":
                query += " AND e.is_credit = 0"
            
            # Sort by date, newest first
            query += " ORDER BY e.date DESC, e.id DESC"
            
            # Execute query
            self.db.cursor.execute(query, params)
            entries = self.db.cursor.fetchall()
            
            # Clear and set row count
            self.entries_table.setRowCount(0)
            self.entries_table.setRowCount(len(entries))
            
            # Fill table with data
            total_credit = 0
            total_debit = 0
            
            for row, entry in enumerate(entries):
                entry_id, date, customer, product, quantity, unit_price, total, is_credit, notes = entry
                
                # Add data to row
                self.entries_table.setItem(row, 0, QTableWidgetItem(str(entry_id)))
                self.entries_table.setItem(row, 1, QTableWidgetItem(date))
                self.entries_table.setItem(row, 2, QTableWidgetItem(customer))
                self.entries_table.setItem(row, 3, QTableWidgetItem(product))
                self.entries_table.setItem(row, 4, QTableWidgetItem(str(quantity)))
                self.entries_table.setItem(row, 5, QTableWidgetItem(f"${unit_price:.2f}"))
                self.entries_table.setItem(row, 6, QTableWidgetItem(f"${total:.2f}"))
                
                # Entry type (Credit/Debit)
                type_item = QTableWidgetItem("Credit" if is_credit else "Debit")
                type_item.setForeground(QColor("green" if is_credit else "red"))
                self.entries_table.setItem(row, 7, type_item)
                
                self.entries_table.setItem(row, 8, QTableWidgetItem(notes or ""))
                
                # Update totals
                if is_credit:
                    total_credit += total
                else:
                    total_debit += total
            
            # Update summary labels
            self.total_entries_label.setText(f"Total Entries: {len(entries)}")
            self.total_credit_label.setText(f"Total Credit: ${total_credit:.2f}")
            self.total_debit_label.setText(f"Total Debit: ${total_debit:.2f}")
            
            # Get current balance
            self.db.cursor.execute("SELECT MAX(balance) FROM transactions")
            result = self.db.cursor.fetchone()
            current_balance = result[0] if result[0] is not None else 0
            
            self.balance_label.setText(f"Current Balance: ${current_balance:.2f}")
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load entries: {str(e)}")
        finally:
            self.db.close()
    
    def clearFilters(self):
        """Reset all filters to default values"""
        self.from_date_edit.setDate(QDate.currentDate().addDays(-30))
        self.to_date_edit.setDate(QDate.currentDate())
        self.customer_filter.setCurrentIndex(0)  # "All Customers"
        self.search_text.clear()
        self.entry_type_filter.setCurrentIndex(0)  # "All Entries"
        self.loadEntries()
    
    def showContextMenu(self, position):
        """Show context menu for table items"""
        # Get the selected row
        selected_rows = self.entries_table.selectionModel().selectedRows()
        if not selected_rows:
            return
        
        # Get entry ID from the first column
        row = selected_rows[0].row()
        entry_id = int(self.entries_table.item(row, 0).text())
        
        # Create context menu
        context_menu = QMenu(self)
        
        view_action = QAction("View Details", self)
        view_action.triggered.connect(lambda: self.viewEntryDetails(entry_id))
        
        edit_action = QAction("Edit Entry", self)
        edit_action.triggered.connect(lambda: self.editEntry(entry_id))
        
        delete_action = QAction("Delete Entry", self)
        delete_action.triggered.connect(lambda: self.deleteEntry(entry_id))
        
                # Get customer ID for the selected entry
        try:
            self.db.connect()
            self.db.cursor.execute("SELECT customer_id FROM entries WHERE id = ?", (entry_id,))
            result = self.db.cursor.fetchone()
            if result:
                customer_id = result[0]
                
                # Add customer history action
                customer_action = QAction("View Customer History", self)
                customer_action.triggered.connect(lambda: self.viewCustomerHistory(customer_id))
                context_menu.addAction(customer_action)
                
        except Exception as e:
            print(f"Error getting customer ID: {e}")
        finally:
            self.db.close()
        
        context_menu.addAction(view_action)
        context_menu.addAction(edit_action)
        context_menu.addAction(delete_action)
        
        # Show context menu at cursor position
        context_menu.exec_(self.entries_table.viewport().mapToGlobal(position))
    
    def viewEntryDetails(self, entry_id):
        """Show details for the selected entry"""
        try:
            self.db.connect()
            
            # Get entry details
            query = '''
                SELECT 
                    e.id, e.date, c.name as customer, p.name as product,
                    e.quantity, e.unit_price, (e.quantity * e.unit_price) as total,
                    e.is_credit, e.notes, t.balance
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                JOIN products p ON e.product_id = p.id
                JOIN transactions t ON e.id = t.entry_id
                WHERE e.id = ?
            '''
            
            self.db.cursor.execute(query, (entry_id,))
            entry = self.db.cursor.fetchone()
            
            if entry:
                entry_id, date, customer, product, quantity, unit_price, total, is_credit, notes, balance = entry
                
                details = f"""
                Entry ID: {entry_id}
                Date: {date}
                Customer: {customer}
                Product: {product}
                Quantity: {quantity}
                Unit Price: ${unit_price:.2f}
                Total Amount: ${total:.2f}
                Entry Type: {"Credit" if is_credit else "Debit"}
                Balance After Transaction: ${balance:.2f}
                Notes: {notes or "N/A"}
                """
                
                QMessageBox.information(self, "Entry Details", details)
            else:
                QMessageBox.warning(self, "Entry Not Found", f"Entry with ID {entry_id} not found.")
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load entry details: {str(e)}")
        finally:
            self.db.close()
    
    def editEntry(self, entry_id):
        """Edit the selected entry"""
        try:
            self.db.connect()
            
            # Get entry details
            query = '''
                SELECT 
                    e.id, e.date, e.customer_id, c.name as customer_name, 
                    e.product_id, p.name as product_name,
                    e.quantity, e.unit_price, e.is_credit, e.notes
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                JOIN products p ON e.product_id = p.id
                WHERE e.id = ?
            '''
            
            self.db.cursor.execute(query, (entry_id,))
            entry = self.db.cursor.fetchone()
            
            if not entry:
                QMessageBox.warning(self, "Entry Not Found", f"Entry with ID {entry_id} not found.")
                return
            
            # Create edit dialog
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Edit Entry #{entry_id}")
            dialog.setMinimumWidth(400)
            
            layout = QFormLayout()
            
            # Date field
            date_edit = QDateEdit()
            date_edit.setDate(QDate.fromString(entry[1], "yyyy-MM-dd"))
            date_edit.setCalendarPopup(True)
            layout.addRow("Date:", date_edit)
            
            # Customer (read-only)
            customer_label = QLineEdit(entry[3])
            customer_label.setReadOnly(True)
            layout.addRow("Customer:", customer_label)
            
            # Product (read-only)
            product_label = QLineEdit(entry[5])
            product_label.setReadOnly(True)
            layout.addRow("Product:", product_label)
            
            # Quantity
            quantity_spin = QSpinBox()
            quantity_spin.setMinimum(1)
            quantity_spin.setMaximum(1000)
            quantity_spin.setValue(entry[6])
            layout.addRow("Quantity:", quantity_spin)
            
            # Unit price
            unit_price_spin = QDoubleSpinBox()
            unit_price_spin.setMinimum(0.01)
            unit_price_spin.setMaximum(99999.99)
            unit_price_spin.setValue(entry[7])
            unit_price_spin.setPrefix("$")
            layout.addRow("Unit Price:", unit_price_spin)
            
            # Total (calculated, read-only)
            total_field = QLineEdit()
            total_field.setReadOnly(True)
            total_field.setText(f"${entry[6] * entry[7]:.2f}")
            layout.addRow("Total:", total_field)
            
            # Update total when quantity or price changes
            def update_total():
                total = quantity_spin.value() * unit_price_spin.value()
                total_field.setText(f"${total:.2f}")
            
            quantity_spin.valueChanged.connect(update_total)
            unit_price_spin.valueChanged.connect(update_total)
            
            # Entry type (credit/debit)
            is_credit = QCheckBox("Credit Entry")
            is_credit.setChecked(entry[8])
            layout.addRow("Entry Type:", is_credit)
            
            # Notes
            notes_edit = QLineEdit(entry[9] or "")
            layout.addRow("Notes:", notes_edit)
            
            # Buttons
            button_box = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
            button_box.accepted.connect(dialog.accept)
            button_box.rejected.connect(dialog.reject)
            layout.addRow(button_box)
            
            dialog.setLayout(layout)
            
            # Execute dialog
            if dialog.exec_() == QDialog.Accepted:
                # Update entry in database
                date = date_edit.date().toString("yyyy-MM-dd")
                quantity = quantity_spin.value()
                unit_price = unit_price_spin.value()
                is_credit_value = is_credit.isChecked()
                notes = notes_edit.text()
                
                # Start transaction
                self.db.conn.execute("BEGIN")
                
                try:
                    # Update entry
                    self.db.cursor.execute(
                        "UPDATE entries SET date=?, quantity=?, unit_price=?, is_credit=?, notes=? WHERE id=?",
                        (date, quantity, unit_price, is_credit_value, notes, entry_id)
                    )
                    
                    # Calculate new total amount
                    total_amount = quantity * unit_price
                    
                    # Get current balance before this transaction
                    self.db.cursor.execute(
                        "SELECT id, amount FROM transactions WHERE entry_id=?",
                        (entry_id,)
                    )
                    trans_result = self.db.cursor.fetchone()
                    
                    if trans_result:
                        trans_id, old_amount = trans_result
                        
                        # Calculate amount difference
                        amount_diff = total_amount - old_amount
                        
                        # Update transactions table
                        self.db.cursor.execute(
                            "UPDATE transactions SET amount=? WHERE id=?",
                            (total_amount, trans_id)
                        )
                        
                        # Update all following transactions' balances
                        if amount_diff != 0:
                            # If entry type changed, double the impact
                            if is_credit_value != entry[8]:
                                amount_diff *= 2
                            
                            # Adjust sign based on entry type
                            balance_adj = amount_diff if is_credit_value else -amount_diff
                            
                            self.db.cursor.execute(
                                "UPDATE transactions SET balance = balance + ? WHERE id > ?",
                                (balance_adj, trans_id)
                            )
                    
                    self.db.conn.commit()
                    QMessageBox.information(self, "Success", f"Entry #{entry_id} updated successfully.")
                    
                    # Refresh entries
                    self.loadEntries()
                    
                except Exception as e:
                    self.db.conn.rollback()
                    QMessageBox.critical(self, "Update Error", f"Failed to update entry: {str(e)}")
                
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load entry details: {str(e)}")
        finally:
            self.db.close()
        
    def viewCustomerHistory(self, customer_id):
        """Show transaction history for a specific customer"""
        try:
            self.db.connect()
            
            # Get customer name
            self.db.cursor.execute("SELECT name FROM customers WHERE id = ?", (customer_id,))
            customer = self.db.cursor.fetchone()
            
            if not customer:
                QMessageBox.warning(self, "Customer Not Found", f"Customer with ID {customer_id} not found.")
                return
            
            customer_name = customer[0]
            
            # Get all entries for this customer
            query = """
                SELECT 
                    e.id, e.date, p.name as product,
                    e.quantity, e.unit_price, (e.quantity * e.unit_price) as total,
                    e.is_credit, e.notes
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.customer_id = ?
                ORDER BY e.date DESC, e.id DESC
            """
            
            self.db.cursor.execute(query, (customer_id,))
            entries = self.db.cursor.fetchall()
            
            if not entries:
                QMessageBox.information(self, "No Transactions", 
                                        f"No transactions found for customer: {customer_name}")
                return
            
            # Calculate totals
            total_credit = sum(e[5] for e in entries if e[6])  # sum of total where is_credit is True
            total_debit = sum(e[5] for e in entries if not e[6])  # sum of total where is_credit is False
            balance = total_credit - total_debit
            
            # Create a dialog to show history
            dialog = QDialog(self)
            dialog.setWindowTitle(f"Transaction History - {customer_name}")
            dialog.setMinimumSize(700, 500)
            
            layout = QVBoxLayout()
            
            # Summary info
            summary = QLabel(f"Customer: {customer_name}\n"
                            f"Total Credit: ${total_credit:.2f}\n"
                            f"Total Debit: ${total_debit:.2f}\n"
                            f"Balance: ${balance:.2f}")
            layout.addWidget(summary)
            
            # Transactions table
            table = QTableWidget()
            table.setColumnCount(7)
            table.setHorizontalHeaderLabels([
                "Date", "Product", "Quantity", "Unit Price", 
                "Total", "Type", "Notes"
            ])
            
            table.setRowCount(len(entries))
            
            for row, entry in enumerate(entries):
                _, date, product, quantity, unit_price, total, is_credit, notes = entry
                
                table.setItem(row, 0, QTableWidgetItem(date))
                table.setItem(row, 1, QTableWidgetItem(product))
                table.setItem(row, 2, QTableWidgetItem(str(quantity)))
                table.setItem(row, 3, QTableWidgetItem(f"${unit_price:.2f}"))
                table.setItem(row, 4, QTableWidgetItem(f"${total:.2f}"))
                
                type_item = QTableWidgetItem("Credit" if is_credit else "Debit")
                type_item.setForeground(QColor("green" if is_credit else "red"))
                table.setItem(row, 5, type_item)
                
                table.setItem(row, 6, QTableWidgetItem(notes or ""))
            
            table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
            layout.addWidget(table)
            
            # Close button
            close_btn = QPushButton("Close")
            close_btn.clicked.connect(dialog.accept)
            layout.addWidget(close_btn)
            
            dialog.setLayout(layout)
            dialog.exec_()
            
        except Exception as e:
            QMessageBox.critical(self, "Database Error", f"Failed to load customer history: {str(e)}")
        finally:
            self.db.close()
    
    def exportToCSV(self):
        """Export current ledger view to CSV file"""
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
            with open(file_name, 'w', newline='') as file:
                import csv
                writer = csv.writer(file)
                
                # Write header row
                headers = []
                for col in range(self.entries_table.columnCount()):
                    headers.append(self.entries_table.horizontalHeaderItem(col).text())
                writer.writerow(headers)
                
                # Write data rows
                for row in range(self.entries_table.rowCount()):
                    row_data = []
                    for col in range(self.entries_table.columnCount()):
                        item = self.entries_table.item(row, col)
                        row_data.append(item.text() if item else "")
                    writer.writerow(row_data)
            
            QMessageBox.information(self, "Export Successful", 
                                f"Data exported successfully to:\n{file_name}")
            
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")
    
    def generateReport(self):
        """Generate a CSV report of the current filtered entries"""
        try:
            options = QFileDialog.Options()
            file_name, _ = QFileDialog.getSaveFileName(
                self, "Save Report", "", "PDF Files (*.pdf);;Text Files (*.txt);;All Files (*)", 
                options=options
            )
            
            if not file_name:
                return
            
            # Add appropriate extension if not present
            if file_name.endswith('.pdf'):
                self.generatePDFReport(file_name)
            elif file_name.endswith('.txt'):
                self.generateTextReport(file_name)
            else:
                # Default to text report if no extension
                self.generateTextReport(file_name + '.txt')
            
            # Get all visible rows from the table
            rows = []
            headers = []
            
            # Get headers
            for col in range(self.entries_table.columnCount()):
                headers.append(self.entries_table.horizontalHeaderItem(col).text())
            
            rows.append(','.join(f'"{h}"' for h in headers))
            
            # Get data
            for row in range(self.entries_table.rowCount()):
                row_data = []
                for col in range(self.entries_table.columnCount()):
                    item = self.entries_table.item(row, col)
                    if item:
                        # Quote values to handle commas
                        row_data.append(f'"{item.text()}"')
                    else:
                        row_data.append('""')
                
                rows.append(','.join(row_data))
            
            # Write to file
            with open(file_name, 'w', encoding='utf-8') as f:
                f.write('\n'.join(rows))
            
            # QMessageBox.information(
            #     self, "Report Generated", 
            #     f"Report has been saved to:\n{file_name}"
            # )
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to generate report: {str(e)}")
            
    def generateTextReport(self, file_name):
        """Generate a simple text report"""
        try:
            with open(file_name, 'w') as f:
                # Write header
                f.write("Medical Rep Transaction Report\n")
                f.write("=" * 80 + "\n\n")
                
                # Write date range
                from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
                to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
                f.write(f"Date Range: {from_date} to {to_date}\n\n")
                
                # Write summary information
                f.write(f"Total Entries: {self.entries_table.rowCount()}\n")
                f.write(f"Total Credit: {self.total_credit_label.text().split('$')[1]}\n")
                f.write(f"Total Debit: {self.total_debit_label.text().split('$')[1]}\n")
                f.write(f"Current Balance: {self.balance_label.text().split('$')[1]}\n\n")
                
                # Write table header
                headers = []
                for col in range(self.entries_table.columnCount()):
                    headers.append(self.entries_table.horizontalHeaderItem(col).text())
                
                # Calculate column widths
                col_widths = [max(len(header), 15) for header in headers]
                
                # Write header row
                header_row = "  ".join(h.ljust(w) for h, w in zip(headers, col_widths))
                f.write(header_row + "\n")
                f.write("-" * len(header_row) + "\n")
                
                # Write data rows
                for row in range(self.entries_table.rowCount()):
                    row_data = []
                    for col in range(self.entries_table.columnCount()):
                        item = self.entries_table.item(row, col)
                        text = item.text() if item else ""
                        row_data.append(text.ljust(col_widths[col]))
                    f.write("  ".join(row_data) + "\n")
            
            QMessageBox.information(self, "Report Generated", 
                                f"Report saved successfully to:\n{file_name}")
                                
        except Exception as e:
            raise Exception(f"Error writing text report: {str(e)}")

    def generatePDFReport(self, file_name):
        """Generate a PDF report (requires reportlab)"""
        try:
            # Check if reportlab is installed
            try:
                from reportlab.lib.pagesizes import letter
                from reportlab.lib import colors
                from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
                from reportlab.lib.styles import getSampleStyleSheet
            except ImportError:
                QMessageBox.warning(self, "Missing Library", 
                                "ReportLab library is required for PDF reports.\n"
                                "Generating text report instead.")
                return self.generateTextReport(file_name.replace('.pdf', '.txt'))
            
            # Create PDF document
            doc = SimpleDocTemplate(file_name, pagesize=letter)
            elements = []
            
            # Add title
            styles = getSampleStyleSheet()
            elements.append(Paragraph("Medical Rep Transaction Report", styles['Title']))
            elements.append(Spacer(1, 12))
            
            # Add date range
            from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
            to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
            elements.append(Paragraph(f"Date Range: {from_date} to {to_date}", styles['Normal']))
            elements.append(Spacer(1, 12))
            
            # Add summary information
            elements.append(Paragraph(f"Total Entries: {self.entries_table.rowCount()}", styles['Normal']))
            elements.append(Paragraph(f"Total Credit: {self.total_credit_label.text()}", styles['Normal']))
            elements.append(Paragraph(f"Total Debit: {self.total_debit_label.text()}", styles['Normal']))
            elements.append(Paragraph(f"Current Balance: {self.balance_label.text()}", styles['Normal']))
            elements.append(Spacer(1, 24))
            
            # Create table data
            data = []
            
            # Add header row
            headers = []
            for col in range(min(7, self.entries_table.columnCount())):  # Limit to first 7 columns to fit page
                headers.append(self.entries_table.horizontalHeaderItem(col).text())
            data.append(headers)
            
            # Add data rows
            for row in range(self.entries_table.rowCount()):
                row_data = []
                for col in range(min(7, self.entries_table.columnCount())):
                    item = self.entries_table.item(row, col)
                    row_data.append(item.text() if item else "")
                data.append(row_data)
            
            # Create table
            table = Table(data)
            
            # Add table style
            style = TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
            ])
            
            # Alternate row colors for readability
            for row in range(1, len(data)):
                if row % 2 == 0:
                    style.add('BACKGROUND', (0, row), (-1, row), colors.lightgrey)
            
            table.setStyle(style)
            elements.append(table)
            
            # Build PDF
            doc.build(elements)
            
            QMessageBox.information(self, "Report Generated", 
                                f"PDF report saved successfully to:\n{file_name}")
                                
        except Exception as e:
            raise Exception(f"Error generating PDF report: {str(e)}")

    def deleteEntry(self, entry_id):
        """Delete the selected entry"""
        reply = QMessageBox.question(
            self, "Confirm Deletion",
            f"Are you sure you want to delete entry #{entry_id}?\nThis action cannot be undone.",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            try:
                self.db.connect()
                
                # Start transaction
                self.db.conn.execute("BEGIN")
                
                # First, delete from transactions table
                self.db.cursor.execute("DELETE FROM transactions WHERE entry_id = ?", (entry_id,))
                
                # Then, delete from entries table
                self.db.cursor.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
                
                # Commit changes
                self.db.conn.commit()
                
                QMessageBox.information(self, "Success", f"Entry #{entry_id} deleted successfully.")
                
                # Reload entries
                self.loadEntries()
                
            except Exception as e:
                self.db.conn.rollback()
                QMessageBox.critical(self, "Database Error", f"Failed to delete entry: {str(e)}")
            finally:
                self.db.close()