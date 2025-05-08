from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLineEdit, QLabel, QDateEdit, QComboBox, QMenu, 
    QAction, QMessageBox, QHeaderView, QGroupBox, QFormLayout
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
import sys
import os

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
        """Show dialog to edit the selected entry"""
        # For now, just show a placeholder message
        # In a complete implementation, this would open a dialog similar to the New Entry form
        QMessageBox.information(self, "Coming Soon", "Edit functionality will be implemented in a future update.")
    
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