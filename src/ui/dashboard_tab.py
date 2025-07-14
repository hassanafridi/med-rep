from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QSizePolicy, QGridLayout,
    QScrollArea, QMessageBox
)
from PyQt5.QtCore import Qt, QDate, QSize, pyqtSignal
from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis, QPieSeries

import sys
import os

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter

class KPICard(QFrame):
    """Card widget to display a KPI metric"""
    def __init__(self, title, value, subtitle=None, color="#4e73df"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet(f"""
            QFrame {{
                border-left: 4px solid {color};
                background-color: white;
                border-radius: 4px;
                padding: 15px;
                margin: 5px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #5a5c69; font-size: 10px; font-weight: bold; text-transform: uppercase;")
        
        # Value with proper formatting
        value_label = QLabel(self.format_value(value))
        value_label.setStyleSheet(f"color: {color}; font-size: 18px; font-weight: bold;")
        value_label.setWordWrap(True)
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Optional subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #858796; font-size: 10px;")
            subtitle_label.setWordWrap(True)
            layout.addWidget(subtitle_label)
        
        layout.setContentsMargins(10, 10, 10, 10)
        self.setLayout(layout)
        
        # Set minimum size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(100)
        self.setMaximumHeight(120)
    
    def format_value(self, value):
        """Format numeric values for better display"""
        if isinstance(value, str):
            return value
        
        try:
            num_value = float(value)
            if num_value >= 1000000:
                return f"{num_value/1000000:.1f}M"
            elif num_value >= 1000:
                return f"{num_value/1000:.1f}K"
            elif num_value == int(num_value):
                return str(int(num_value))
            else:
                return f"{num_value:.2f}"
        except (ValueError, TypeError):
            return str(value)

class ChartCard(QFrame):
    """Card widget to display a chart"""
    def __init__(self, title, chart_view):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border-radius: 4px;
            }
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #5a5c69; font-size: 14px; font-weight: bold;")
        title_label.setAlignment(Qt.AlignLeft)
        
        layout.addWidget(title_label)
        layout.addWidget(chart_view)
        
        layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(layout)

class AlertCard(QFrame):
    """Card widget to display alerts and warnings"""
    def __init__(self, title, alerts, alert_type="warning"):
        super().__init__()
        self.setFrameShape(QFrame.StyledPanel)
        self.setFrameShadow(QFrame.Raised)
        
        # Color scheme based on alert type
        colors = {
            "warning": {"border": "#f39c12", "bg": "#fef9e7", "text": "#8b6914"},
            "danger": {"border": "#e74c3c", "bg": "#fdf2f2", "text": "#c53030"},
            "info": {"border": "#3498db", "bg": "#ebf8ff", "text": "#2b77a6"}
        }
        
        color_scheme = colors.get(alert_type, colors["warning"])
        
        self.setStyleSheet(f"""
            QFrame {{
                border-left: 4px solid {color_scheme['border']};
                background-color: {color_scheme['bg']};
                border-radius: 4px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"color: {color_scheme['text']}; font-size: 14px; font-weight: bold;")
        layout.addWidget(title_label)
        
        # Alert items
        for alert in alerts[:5]:  # Limit to 5 alerts
            alert_label = QLabel(f"• {alert}")
            alert_label.setStyleSheet(f"color: {color_scheme['text']}; font-size: 12px; margin-left: 10px;")
            alert_label.setWordWrap(True)
            layout.addWidget(alert_label)
        
        # Show count if more alerts exist
        if len(alerts) > 5:
            more_label = QLabel(f"... and {len(alerts) - 5} more")
            more_label.setStyleSheet(f"color: {color_scheme['text']}; font-size: 11px; font-style: italic; margin-left: 10px;")
            layout.addWidget(more_label)
        
        layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(layout)
        
        # Set minimum size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(120)

class DashboardTab(QWidget):
    # Signal to communicate with main window
    switch_to_ledger = pyqtSignal()
    
    def __init__(self, current_user=None):
        super().__init__()
        try:
            self.db = MongoAdapter()
            self.current_user = current_user
            self.initUI()
            self.loadData()
        except Exception as e:
            print(f"Error initializing Dashboard tab: {e}")
            import traceback
            traceback.print_exc()
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Dashboard temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Loading Dashboard")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the dashboard"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.current_user)
            
        except Exception as e:
            print(f"Dashboard retry failed: {e}")
            QMessageBox.critical(self, "Dashboard Error", 
                               f"Failed to load Dashboard: {str(e)}")

    def initUI(self):
        """Initialize the UI components"""
        # Main layout
        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        
        # Welcome section
        welcome_layout = QHBoxLayout()
        
        welcome_text = "Welcome to Your Dashboard"
        if self.current_user and 'username' in self.current_user:
            welcome_text = f"Welcome, {self.current_user['username']}!"
        
        welcome_label = QLabel(welcome_text)
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #5a5c69; margin-bottom: 10px;")
        
        date_label = QLabel(f"Today: {QDate.currentDate().toString('dddd, MMMM d, yyyy')}")
        date_label.setStyleSheet("font-size: 14px; color: #858796;")
        date_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        
        welcome_layout.addWidget(welcome_label)
        welcome_layout.addWidget(date_label)
        
        main_layout.addLayout(welcome_layout)
        
        # Create a scroll area for the dashboard content
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.NoFrame)
        scroll_area.setStyleSheet("QScrollArea { background-color: #f8f9fc; }")
        
        # Create widget to hold dashboard content
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        dashboard_layout.setSpacing(20)
        
        # Get alerts first
        alerts = self.getProductAlerts()
        
        # Critical Alerts section (for expired products) - Direct alert display
        if alerts['expired']:
            critical_layout = QVBoxLayout()
            
            # Expired products alert with enhanced styling - no header
            expired_card = AlertCard("🚨 IMMEDIATE ACTION REQUIRED - These products have EXPIRED", 
                                   alerts['expired'], "danger")
            critical_layout.addWidget(expired_card)
            
            dashboard_layout.addLayout(critical_layout)
        
        # Warning Alerts section (for expiring products)
        if alerts['expiring']:
            warning_layout = QVBoxLayout()
            
            expiring_card = AlertCard("⚠️ Products Expiring in the Next 30 Days", 
                                    alerts['expiring'], "warning")
            warning_layout.addWidget(expiring_card)
            
            dashboard_layout.addLayout(warning_layout)
        
        # KPI Cards section (removed header, just the cards)
        kpi_section = QVBoxLayout()
        
        # Create two rows of KPI cards for better layout
        kpi_row1 = QHBoxLayout()
        kpi_row2 = QHBoxLayout()
        
        # Load KPI metrics
        metrics = self.loadKPIMetrics()
        
        # Create KPI cards with improved formatting
        total_sales_card = KPICard("Total Sales", f"Rs. {metrics['total_sales']:,.0f}", 
                               f"{metrics['sales_change']:+.1f}% from last month", "#4e73df")
        
        total_transactions_card = KPICard("Total Transactions", f"{metrics['transaction_count']:,}",
                                     f"{metrics['transaction_change']:+.1f}% from last month", "#1cc88a")
        
        average_sale_card = KPICard("Average Sale", f"Rs. {metrics['average_sale']:,.0f}",
                                f"{metrics['average_change']:+.1f}% from last month", "#36b9cc")
        
        # Format balance with proper sign indication
        balance_color = "#1cc88a" if metrics['current_balance'] >= 0 else "#e74c3c"
        balance_text = f"Rs. {abs(metrics['current_balance']):,.0f}"
        if metrics['current_balance'] < 0:
            balance_text = f"-{balance_text}"
        
        balance_card = KPICard("Current Balance", balance_text, "Net position", balance_color)
        
        # Add batch tracking metrics
        batch_metrics = self.getBatchMetrics()
        batch_diversity_card = KPICard("Active Batches", f"{batch_metrics['active_batches']:,}",
                                   f"{batch_metrics['unique_products']} unique products", "#e83e8c")
        
        # Arrange KPI cards in two rows
        kpi_row1.addWidget(total_sales_card)
        kpi_row1.addWidget(total_transactions_card)
        kpi_row1.addWidget(average_sale_card)
        
        kpi_row2.addWidget(balance_card)
        kpi_row2.addWidget(batch_diversity_card)
        kpi_row2.addStretch(1)  # Add stretch to balance the second row
        
        kpi_section.addLayout(kpi_row1)
        kpi_section.addLayout(kpi_row2)
        
        dashboard_layout.addLayout(kpi_section)
        
        # Charts section with improved spacing
        charts_section = QVBoxLayout()
        charts_title = QLabel("Analytics Dashboard")
        charts_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #5a5c69; margin-bottom: 10px;")
        charts_section.addWidget(charts_title)
        
        charts_layout = QGridLayout()
        charts_layout.setSpacing(15)
        
        # Monthly earnings chart
        sales_chart = self.createSalesChart()
        sales_chart_view = QChartView(sales_chart)
        sales_chart_view.setRenderHint(QPainter.Antialiasing)
        sales_chart_view.setMinimumHeight(300)
        
        sales_card = ChartCard("Monthly Sales", sales_chart_view)
        charts_layout.addWidget(sales_card, 0, 0)
        
        # Product distribution chart (by product name, not individual batches)
        product_chart = self.createProductChart()
        product_chart_view = QChartView(product_chart)
        product_chart_view.setRenderHint(QPainter.Antialiasing)
        product_chart_view.setMinimumHeight(300)
        
        product_card = ChartCard("Product Distribution", product_chart_view)
        charts_layout.addWidget(product_card, 0, 1)
        
        # Batch expiry timeline chart
        expiry_chart = self.createExpiryChart()
        
        expiry_card = ChartCard("Product Expiry Status", expiry_chart)
        charts_layout.addWidget(expiry_card, 1, 0, 1, 2)  # Span across both columns
        
        charts_section.addLayout(charts_layout)
        dashboard_layout.addLayout(charts_section)
        
        # Recent transactions section with improved styling
        recent_transactions = self.getRecentTransactions()
        
        if recent_transactions:
            transactions_section = QVBoxLayout()
            
            transactions_title = QLabel("Recent Transactions")
            transactions_title.setStyleSheet("font-size: 18px; font-weight: bold; color: #5a5c69; margin-bottom: 10px;")
            transactions_section.addWidget(transactions_title)
            
            for transaction in recent_transactions:
                transaction_frame = QFrame()
                transaction_frame.setFrameShape(QFrame.StyledPanel)
                transaction_frame.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border-radius: 4px;
                        padding: 10px;
                        margin: 2px;
                        border: 1px solid #e3e6f0;
                    }
                    QFrame:hover {
                        border: 1px solid #4e73df;
                    }
                """)
                
                transaction_layout = QHBoxLayout(transaction_frame)
                
                date_label = QLabel(transaction[0])
                date_label.setMinimumWidth(80)
                customer_label = QLabel(transaction[1])
                customer_label.setStyleSheet("font-weight: bold;")
                customer_label.setMinimumWidth(120)
                
                # Enhanced product info with batch
                product_info = transaction[2]
                if len(transaction) > 6 and transaction[6]:  # batch_number exists
                    product_info += f" (Batch: {transaction[6]})"
                product_label = QLabel(product_info)
                product_label.setMinimumWidth(200)
                
                # Format amount with proper styling
                amount = transaction[4]
                amount_text = f"Rs. {amount:,.2f}"
                amount_label = QLabel(amount_text)
                if transaction[3]:  # is_credit
                    amount_label.setStyleSheet("color: #e74a3b; font-weight: bold;")
                else:
                    amount_label.setStyleSheet("color: #1cc88a; font-weight: bold;")
                amount_label.setMinimumWidth(100)
                amount_label.setAlignment(Qt.AlignRight)
                
                # Add expiry warning if applicable - make more prominent
                expiry_warning = ""
                if len(transaction) > 7 and transaction[7]:  # expiry_date exists
                    try:
                        expiry_date = QDate.fromString(transaction[7], "yyyy-MM-dd")
                        if expiry_date.isValid():
                            if expiry_date < QDate.currentDate():
                                expiry_warning = "🚨 EXPIRED"
                            elif expiry_date < QDate.currentDate().addDays(30):
                                expiry_warning = "⚠️ EXPIRING"
                    except:
                        pass
                
                transaction_layout.addWidget(date_label)
                transaction_layout.addWidget(customer_label)
                transaction_layout.addWidget(product_label)
                if expiry_warning:
                    warning_label = QLabel(expiry_warning)
                    if "EXPIRED" in expiry_warning:
                        warning_label.setStyleSheet("""
                            color: #e74c3c; 
                            font-weight: bold; 
                            font-size: 11px; 
                            background-color: #fdf2f2; 
                            padding: 4px 8px; 
                            border-radius: 4px;
                            border: 1px solid #e74c3c;
                        """)
                    else:
                        warning_label.setStyleSheet("""
                            color: #f39c12; 
                            font-weight: bold; 
                            font-size: 11px; 
                            background-color: #fef9e7; 
                            padding: 4px 8px; 
                            border-radius: 4px;
                            border: 1px solid #f39c12;
                        """)
                    transaction_layout.addWidget(warning_label)
                transaction_layout.addStretch(1)
                transaction_layout.addWidget(amount_label)
                
                transactions_section.addWidget(transaction_frame)
            
            # Add the "View All Transactions" button with functionality
            view_all_btn = QPushButton("View All Transactions")
            view_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4e73df;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 4px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #2e59d9;
                }
            """)
            # Connect the button to switch to ledger tab
            view_all_btn.clicked.connect(self.viewAllTransactions)
            transactions_section.addWidget(view_all_btn)
            
            dashboard_layout.addLayout(transactions_section)
        
        # Set dashboard widget as the scrollable content
        scroll_area.setWidget(dashboard_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
    
    def loadData(self):
        """Load dashboard data"""
        # This method can be called to refresh dashboard data
        pass
    
    def viewAllTransactions(self):
        """Switch to the Ledger tab to view all transactions"""
        try:
            # Try to find the main window and switch to ledger tab
            main_window = self.window()
            if hasattr(main_window, 'tabs'):
                # Find the Ledger tab index
                for i in range(main_window.tabs.count()):
                    if main_window.tabs.tabText(i) == "Ledger":
                        main_window.tabs.setCurrentIndex(i)
                        return
                
                # If Ledger tab not found, show message
                QMessageBox.information(self, "Navigate to Ledger", 
                                      "Please click on the 'Ledger' tab to view all transactions.")
            else:
                # Fallback message
                QMessageBox.information(self, "View Transactions", 
                                      "To view all transactions, please navigate to the Ledger tab.")
        except Exception as e:
            QMessageBox.information(self, "Navigate to Ledger", 
                                  "Please click on the 'Ledger' tab to view all transactions.")
    
    def getProductAlerts(self):
        """Get alerts for expired and expiring products with enhanced details"""
        try:
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            upcoming_date = QDate.currentDate().addDays(30).toString("yyyy-MM-dd")
            
            print(f"DEBUG: Checking alerts for current date: {current_date}")
            print(f"DEBUG: Upcoming date threshold: {upcoming_date}")
            
            # Get all products directly from MongoDB
            products = self.db.get_products()
            entries = self.db.get_entries()
            
            print(f"DEBUG: Found {len(products)} products, {len(entries)} entries")
            
            # Create a map of product IDs that have sales with quantities
            products_with_sales = {}
            for entry in entries:
                if entry.get('is_credit'):  # Only count actual sales (credits)
                    product_id = str(entry.get('product_id', ''))
                    quantity = float(entry.get('quantity', 0))
                    products_with_sales[product_id] = products_with_sales.get(product_id, 0) + quantity
            
            print(f"DEBUG: Products with sales: {len(products_with_sales)}")
            
            expired_alerts = []
            expiring_alerts = []
            
            for product in products:
                product_id = str(product.get('id', ''))
                product_name = product.get('name', 'Unknown')
                expiry_date = product.get('expiry_date', '')
                batch = product.get('batch_number', 'Unknown')
                
                print(f"DEBUG: Checking product '{product_name}' (ID: {product_id})")
                print(f"       Expiry date: '{expiry_date}' | Batch: '{batch}'")
                print(f"       Has sales: {product_id in products_with_sales}")
                
                # Check ALL products with expiry dates, not just those with sales
                # This is important because expired products should be flagged regardless
                if expiry_date:
                    print(f"       Comparing dates: '{expiry_date}' vs '{current_date}'")
                    
                    # Check if product is expired
                    if expiry_date < current_date:
                        days_expired = QDate.fromString(expiry_date, "yyyy-MM-dd").daysTo(QDate.currentDate())
                        sold_qty = products_with_sales.get(product_id, 0)
                        
                        alert_message = f"{product_name} (Batch: {batch}) - Expired {days_expired} days ago"
                        if sold_qty > 0:
                            alert_message += f" | Sold: {sold_qty:.0f} units"
                        else:
                            alert_message += " | No sales recorded"
                        
                        expired_alerts.append(alert_message)
                        print(f"       >>> EXPIRED PRODUCT FOUND: {alert_message}")
                    
                    # Check if product is expiring soon
                    elif current_date <= expiry_date <= upcoming_date:
                        days_until = QDate.currentDate().daysTo(QDate.fromString(expiry_date, "yyyy-MM-dd"))
                        sold_qty = products_with_sales.get(product_id, 0)
                        
                        alert_message = f"{product_name} (Batch: {batch}) - Expires in {days_until} days"
                        if sold_qty > 0:
                            alert_message += f" | Sold: {sold_qty:.0f} units"
                        else:
                            alert_message += " | No sales recorded"
                        
                        expiring_alerts.append(alert_message)
                        print(f"       >>> EXPIRING PRODUCT FOUND: {alert_message}")
                    else:
                        print(f"       Product is active (expires after {upcoming_date})")
                else:
                    print(f"       No expiry date set")
            
            print(f"DEBUG: Final results - Expired: {len(expired_alerts)}, Expiring: {len(expiring_alerts)}")
            
            return {
                'expired': expired_alerts,
                'expiring': expiring_alerts
            }
            
        except Exception as e:
            print(f"Error getting product alerts: {e}")
            import traceback
            traceback.print_exc()
            return {'expired': [], 'expiring': []}

    def getBatchMetrics(self):
        """Get batch-related metrics with improved calculation"""
        try:
            products = self.db.get_products()
            entries = self.db.get_entries()
            
            # Get products with sales and their quantities
            products_with_sales = {}
            total_sold_quantity = 0
            
            for entry in entries:
                if entry.get('is_credit'):
                    product_id = str(entry.get('product_id', ''))
                    quantity = float(entry.get('quantity', 0))
                    products_with_sales[product_id] = products_with_sales.get(product_id, 0) + quantity
                    total_sold_quantity += quantity
            
            # Count unique product names and active batches with sales
            unique_products = set()
            active_batches = 0
            
            for product in products:
                product_id = str(product.get('id', ''))
                if product_id in products_with_sales:
                    active_batches += 1
                    unique_products.add(product.get('name', ''))
            
            return {
                'active_batches': active_batches,
                'unique_products': len(unique_products),
                'total_products': len(products),
                'total_sold_quantity': total_sold_quantity
            }
            
        except Exception as e:
            print(f"Error getting batch metrics: {e}")
            import traceback
            traceback.print_exc()
            return {
                'active_batches': 0,
                'unique_products': 0,
                'total_products': 0,
                'total_sold_quantity': 0
            }
        
    def loadKPIMetrics(self):
        """Load KPI metrics from MongoDB database"""
        try:
            # Get current month and last month dates
            today = QDate.currentDate()
            current_month_start = QDate(today.year(), today.month(), 1).toString("yyyy-MM-dd")
            
            last_month = today.addMonths(-1)
            last_month_start = QDate(last_month.year(), last_month.month(), 1).toString("yyyy-MM-dd")
            last_month_end = QDate(today.year(), today.month(), 1).addDays(-1).toString("yyyy-MM-dd")
            
            # Get all entries and transactions from MongoDB
            entries = self.db.get_entries()
            transactions = self.db.get_transactions()
            
            print(f"DEBUG: KPI Metrics - Total entries from DB: {len(entries)}")
            print(f"DEBUG: KPI Metrics - Total transactions from DB: {len(transactions)}")
            
            # Calculate current month metrics
            current_credits = 0
            current_debits = 0
            current_count = 0
            last_month_credits = 0
            last_month_debits = 0
            last_month_count = 0
            
            # Calculate cumulative balance (all time)
            total_credits = 0
            total_debits = 0
            total_count = len(entries)  # Total transaction count
            
            for entry in entries:
                entry_date = entry.get('date', '')
                amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                
                # Cumulative totals for balance calculation
                if entry.get('is_credit'):
                    total_credits += amount
                else:
                    total_debits += amount
                
                if entry_date >= current_month_start:
                    current_count += 1
                    if entry.get('is_credit'):
                        current_credits += amount
                    else:
                        current_debits += amount
                elif last_month_start <= entry_date <= last_month_end:
                    last_month_count += 1
                    if entry.get('is_credit'):
                        last_month_credits += amount
                    else:
                        last_month_debits += amount
            
            # Total sales = credits + debits (both are revenue)
            current_sales = current_credits + current_debits
            last_month_sales = last_month_credits + last_month_debits
            
            # Current balance = credits - debits (net position)
            # Set to 0 if negative (don't show negative balances)
            calculated_balance = total_credits - total_debits
            current_balance = max(0, calculated_balance)
            
            # Calculate percentage changes
            sales_change = 0
            if last_month_sales > 0:
                sales_change = ((current_sales - last_month_sales) / last_month_sales) * 100
            
            transaction_change = 0
            if last_month_count > 0:
                transaction_change = ((current_count - last_month_count) / last_month_count) * 100
            
            # Calculate average sale
            average_sale = current_sales / current_count if current_count > 0 else 0
            last_month_average = last_month_sales / last_month_count if last_month_count > 0 else 0
            
            average_change = 0
            if last_month_average > 0:
                average_change = ((average_sale - last_month_average) / last_month_average) * 100
            
            print(f"DEBUG: KPI Results - Total transactions: {total_count}, Current month: {current_count}")
            print(f"DEBUG: KPI Results - Total sales: {current_sales}, Balance: {current_balance}")
            
            return {
                'total_sales': current_sales,
                'sales_change': round(sales_change, 1),
                'transaction_count': total_count,  # Use total count, not just current month
                'transaction_change': round(transaction_change, 1),
                'average_sale': average_sale,
                'average_change': round(average_change, 1),
                'current_balance': current_balance
            }
            
        except Exception as e:
            print(f"Error loading KPI metrics: {e}")
            import traceback
            traceback.print_exc()
            return {
                'total_sales': 0,
                'sales_change': 0,
                'transaction_count': 0,
                'transaction_change': 0,
                'average_sale': 0,
                'average_change': 0,
                'current_balance': 0
            }
    
    def createSalesChart(self):
        """Create monthly sales chart from MongoDB data"""
        chart = QChart()
        chart.setTitle("Monthly Sales")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        try:
            # Get data for the last 6 months from MongoDB
            today = QDate.currentDate()
            entries = self.db.get_entries()
            
            # Prepare data structure
            months = []
            credits = []
            debits = []
            
            # Get data for each month
            for i in range(5, -1, -1):
                month_date = today.addMonths(-i)
                month_name = month_date.toString("MMM")
                months.append(month_name)
                
                month_start = QDate(month_date.year(), month_date.month(), 1).toString("yyyy-MM-dd")
                month_end = QDate(month_date.year(), month_date.month(), 
                               month_date.daysInMonth()).toString("yyyy-MM-dd")
                
                month_credits = 0
                month_debits = 0
                
                for entry in entries:
                    entry_date = entry.get('date', '')
                    if month_start <= entry_date <= month_end:
                        try:
                            amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                            if entry.get('is_credit'):
                                month_credits += amount
                            else:
                                month_debits += amount
                        except (ValueError, TypeError):
                            continue
                
                credits.append(month_credits)
                debits.append(month_debits)
            
            # Only create chart if we have data
            if any(credits) or any(debits):
                # Create bar sets
                credit_set = QBarSet("Credits")
                credit_set.setColor(QColor("#e74a3b"))
                credit_set.append(credits)
                
                debit_set = QBarSet("Debits")
                debit_set.setColor(QColor("#4CAF50"))
                debit_set.append(debits)
                
                # Create bar series
                series = QBarSeries()
                series.append(credit_set)
                series.append(debit_set)
                
                chart.addSeries(series)
                
                # Create axes
                axisX = QBarCategoryAxis()
                axisX.append(months)
                chart.addAxis(axisX, Qt.AlignBottom)
                series.attachAxis(axisX)
                
                axisY = QValueAxis()
                axisY.setTitleText("Amount (Rs.)")
                axisY.setLabelsAngle(0)
                chart.addAxis(axisY, Qt.AlignLeft)
                series.attachAxis(axisY)
                
                # Set legend
                chart.legend().setVisible(True)
                chart.legend().setAlignment(Qt.AlignBottom)
            else:
                # Create empty chart with message
                chart.setTitle("Monthly Sales - No Data Available")
                
        except Exception as e:
            print(f"Error creating sales chart: {e}")
            import traceback
            traceback.print_exc()
            chart.setTitle("Monthly Sales - Error Loading Data")
        
        return chart
    
    def createProductChart(self):
        """Create product distribution pie chart from MongoDB data"""
        chart = QChart()
        chart.setTitle("Product Distribution")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        try:
            products = self.db.get_products()
            entries = self.db.get_entries()
            
            # Create product lookup with string IDs
            product_lookup = {}
            for p in products:
                product_lookup[str(p.get('id', ''))] = p.get('name', 'Unknown')
            
            # Calculate sales by product name
            product_sales = {}
            product_batches = {}
            
            for entry in entries:
                if entry.get('is_credit'):
                    product_id = str(entry.get('product_id', ''))
                    product_name = product_lookup.get(product_id, 'Unknown')
                    
                    try:
                        amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                        product_sales[product_name] = product_sales.get(product_name, 0) + amount
                    except (ValueError, TypeError):
                        continue
                    
                    # Count batches
                    if product_name not in product_batches:
                        product_batches[product_name] = set()
                    
                    # Find the product to get batch info
                    for product in products:
                        if str(product.get('id', '')) == product_id:
                            batch_number = product.get('batch_number', 'Unknown')
                            product_batches[product_name].add(batch_number)
                            break
            
            if product_sales:
                series = QPieSeries()
                
                # Get top 5 products
                sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)[:5]
                total_sales = sum(product_sales.values())
                top_sales = sum(amount for _, amount in sorted_products)
                
                for product_name, amount in sorted_products:
                    batch_count = len(product_batches.get(product_name, set()))
                    batch_text = f"({batch_count} batch{'es' if batch_count > 1 else ''})"
                    series.append(f"{product_name} {batch_text}", amount)
                
                # Add "Other" slice if needed
                if total_sales > top_sales:
                    series.append("Other", total_sales - top_sales)
                
                # Customize slices
                for i in range(series.count()):
                    slice = series.slices()[i]
                    percentage = (slice.value() / total_sales) * 100
                    slice.setLabel(f"{slice.label()}: {percentage:.1f}%")
                
                chart.addSeries(series)
                chart.legend().setVisible(True)
                chart.legend().setAlignment(Qt.AlignRight)
            else:
                chart.setTitle("Product Distribution - No Sales Data")
            
        except Exception as e:
            print(f"Error creating product chart: {e}")
            import traceback
            traceback.print_exc()
            chart.setTitle("Product Distribution - Error Loading Data")
        
        return chart

    def createExpiryChart(self):
        """Create a pie chart showing product expiry status from MongoDB"""
        try:
            # Get products from MongoDB and check expiry status
            products = self.db.get_products()
            
            # Count products by expiry status
            active_count = 0
            expiring_count = 0
            expired_count = 0
            
            today = QDate.currentDate()
            warning_date = today.addDays(30)
            
            for product in products:
                expiry_str = product.get('expiry_date', '')
                if expiry_str:
                    try:
                        expiry_date = QDate.fromString(expiry_str, "yyyy-MM-dd")
                        if expiry_date.isValid():
                            if expiry_date < today:
                                expired_count += 1
                            elif expiry_date <= warning_date:
                                expiring_count += 1
                            else:
                                active_count += 1
                        else:
                            active_count += 1  # Treat invalid dates as active
                    except Exception:
                        active_count += 1  # Treat unparseable dates as active
                else:
                    active_count += 1  # Treat missing dates as active
            
            # Create the chart
            chart = QChart()
            chart.setTitle("Product Expiry Status")
            chart.setTitleFont(QFont("Arial", 12, QFont.Bold))
            
            series = QPieSeries()
            
            # Only add slices for categories that have data
            total_products = active_count + expiring_count + expired_count
            
            if total_products > 0:
                if active_count > 0:
                    slice_active = series.append(f"Active ({active_count})", active_count)
                    slice_active.setColor(QColor(46, 204, 113))  # Green
                
                if expiring_count > 0:
                    slice_expiring = series.append(f"Expiring Soon ({expiring_count})", expiring_count)
                    slice_expiring.setColor(QColor(241, 196, 15))  # Yellow
                
                if expired_count > 0:
                    slice_expired = series.append(f"Expired ({expired_count})", expired_count)
                    slice_expired.setColor(QColor(231, 76, 60))  # Red
            else:
                # If no products have expiry data, show a message
                series.append("No Products", 1)
                slice_no_data = series.slices()[0]
                slice_no_data.setColor(QColor(149, 165, 166))  # Gray
            
            chart.addSeries(series)
            chart.legend().setAlignment(Qt.AlignRight)
            
            # Create chart view
            chart_view = QChartView(chart)
            chart_view.setRenderHint(QPainter.Antialiasing)
            chart_view.setMinimumHeight(200)
            
            return chart_view
            
        except Exception as e:
            print(f"Error creating expiry chart: {e}")
            import traceback
            traceback.print_exc()
            
            # Return a simple label with error message instead of crashing
            error_label = QLabel(f"Chart temporarily unavailable\n(Error: {str(e)})")
            error_label.setAlignment(Qt.AlignCenter)
            error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
            error_label.setMinimumHeight(200)
            return error_label
    
    def getRecentTransactions(self):
        """Get recent transactions with batch and expiry information from MongoDB"""
        try:
            # Get entries using the same method as ledger for consistency
            recent_entries = self.db.get_entries_with_balance(limit=5)
            
            print(f"DEBUG: Recent transactions - Retrieved {len(recent_entries)} enriched entries")
            
            if not recent_entries:
                print("DEBUG: No recent transactions found, trying direct method")
                # Fallback to direct method if enriched method fails
                entries = self.db.get_entries()
                customers = self.db.get_customers()
                products = self.db.get_products()
                
                # Create lookup dictionaries
                customer_lookup = {str(c.get('id', '')): c for c in customers}
                product_lookup = {str(p.get('id', '')): p for p in products}
                
                # Sort by date and get top 5
                sorted_entries = sorted(entries, key=lambda x: x.get('date', ''), reverse=True)[:5]
                
                result = []
                for entry in sorted_entries:
                    customer_id = str(entry.get('customer_id', ''))
                    product_id = str(entry.get('product_id', ''))
                    
                    customer_info = customer_lookup.get(customer_id, {})
                    product_info = product_lookup.get(product_id, {})
                    
                    try:
                        total = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                        quantity = float(entry.get('quantity', 0))
                    except (ValueError, TypeError):
                        total = 0
                        quantity = 0
                    
                    # Format: [date, customer, product, is_credit, total, quantity, batch_number, expiry_date]
                    result.append([
                        entry.get('date', ''),
                        customer_info.get('name', 'Unknown Customer'),
                        product_info.get('name', 'Unknown Product'),
                        entry.get('is_credit', False),
                        total,
                        quantity,
                        product_info.get('batch_number', ''),
                        product_info.get('expiry_date', '')
                    ])
                
                print(f"DEBUG: Fallback method returned {len(result)} transactions")
                return result
            
            # Convert enriched entries to expected format
            result = []
            for entry in recent_entries:
                # Find product info for batch and expiry
                product_id = str(entry.get('product_id', ''))
                products = self.db.get_products()
                product_info = {}
                for p in products:
                    if str(p.get('id', '')) == product_id:
                        product_info = p
                        break
                
                # Format: [date, customer, product, is_credit, total, quantity, batch_number, expiry_date]
                result.append([
                    entry.get('date', ''),
                    entry.get('customer_name', 'Unknown Customer'),
                    entry.get('product_name', 'Unknown Product'),
                    entry.get('is_credit', False),
                    entry.get('amount', 0),
                    entry.get('quantity', 0),
                    product_info.get('batch_number', ''),
                    product_info.get('expiry_date', '')
                ])
            
            print(f"DEBUG: Final recent transactions result: {len(result)} transactions")
            if result:
                print(f"DEBUG: First transaction date: {result[0][0]}")
                print(f"DEBUG: First transaction customer: {result[0][1]}")
                print(f"DEBUG: First transaction product: {result[0][2]}")
                print(f"DEBUG: First transaction amount: {result[0][4]}")
            
            return result
            
        except Exception as e:
            print(f"Error getting recent transactions: {e}")
            import traceback
            traceback.print_exc()
            return []