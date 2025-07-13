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
                border-radius: 0px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #5a5c69; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        
        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color: {color}; font-size: 20px; font-weight: bold;")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        
        # Optional subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet("color: #858796; font-size: 11px;")
            layout.addWidget(subtitle_label)
        
        layout.setContentsMargins(15, 15, 15, 15)
        self.setLayout(layout)
        
        # Set minimum size policy
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(100)

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
        main_layout.setSpacing(20)
        
        # Welcome section
        welcome_layout = QHBoxLayout()
        
        welcome_text = "Welcome to Your Dashboard"
        if self.current_user and 'username' in self.current_user:
            welcome_text = f"Welcome, {self.current_user['username']}!"
        
        welcome_label = QLabel(welcome_text)
        welcome_label.setStyleSheet("font-size: 24px; font-weight: bold; color: #5a5c69;")
        
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
        
        # Create widget to hold dashboard content
        dashboard_widget = QWidget()
        dashboard_layout = QVBoxLayout(dashboard_widget)
        dashboard_layout.setSpacing(20)
        
        # Alerts section (for expired/expiring products)
        alerts = self.getProductAlerts()
        if alerts['expired'] or alerts['expiring']:
            alerts_layout = QHBoxLayout()
            
            if alerts['expired']:
                expired_card = AlertCard("Expired Products", alerts['expired'], "danger")
                alerts_layout.addWidget(expired_card)
            
            if alerts['expiring']:
                expiring_card = AlertCard("Products Expiring Soon", alerts['expiring'], "warning")
                alerts_layout.addWidget(expiring_card)
            
            # Add spacer if only one alert type
            if not alerts['expired'] or not alerts['expiring']:
                alerts_layout.addStretch(1)
            
            dashboard_layout.addLayout(alerts_layout)
        
        # KPI Cards section
        kpi_layout = QHBoxLayout()
        
        # Load KPI metrics
        metrics = self.loadKPIMetrics()
        
        # Create KPI cards
        total_sales_card = KPICard("Total Sales", f"Rs. {metrics['total_sales']:.2f}", 
                               f"{metrics['sales_change']}% from last month", "#4e73df")
        
        total_transactions_card = KPICard("Total Transactions", str(metrics['transaction_count']),
                                     f"{metrics['transaction_change']}% from last month", "#1cc88a")
        
        average_sale_card = KPICard("Average Sale", f"Rs. {metrics['average_sale']:.2f}",
                                f"{metrics['average_change']}% from last month", "#36b9cc")
        
        balance_card = KPICard("Current Balance", f"Rs. {metrics['current_balance']:.2f}",
                          "Updated just now", "#f6c23e")
        
        # Add batch tracking metrics
        batch_metrics = self.getBatchMetrics()
        batch_diversity_card = KPICard("Active Batches", str(batch_metrics['active_batches']),
                                   f"{batch_metrics['total_products']} total products", "#e83e8c")
        
        kpi_layout.addWidget(total_sales_card)
        kpi_layout.addWidget(total_transactions_card)
        kpi_layout.addWidget(average_sale_card)
        kpi_layout.addWidget(balance_card)
        kpi_layout.addWidget(batch_diversity_card)
        
        dashboard_layout.addLayout(kpi_layout)
        
        # Charts section
        charts_layout = QGridLayout()
        
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
        
        expiry_card = ChartCard("Expiry Timeline", expiry_chart)
        charts_layout.addWidget(expiry_card, 1, 0, 1, 2)  # Span across both columns
        
        dashboard_layout.addLayout(charts_layout)
        
        # Recent transactions section
        recent_transactions = self.getRecentTransactions()
        
        if recent_transactions:
            transactions_layout = QVBoxLayout()
            
            transactions_title = QLabel("Recent Transactions")
            transactions_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #5a5c69;")
            transactions_layout.addWidget(transactions_title)
            
            for transaction in recent_transactions:
                transaction_frame = QFrame()
                transaction_frame.setFrameShape(QFrame.StyledPanel)
                transaction_frame.setStyleSheet("""
                    QFrame {
                        background-color: white;
                        border-radius: 4px;
                        padding: 10px;
                    }
                """)
                
                transaction_layout = QHBoxLayout(transaction_frame)
                
                date_label = QLabel(transaction[0])
                customer_label = QLabel(transaction[1])
                customer_label.setStyleSheet("font-weight: bold;")
                
                # Enhanced product info with batch
                product_info = transaction[2]
                if len(transaction) > 6 and transaction[6]:  # batch_number exists
                    product_info += f" (Batch: {transaction[6]})"
                product_label = QLabel(product_info)
                
                amount_label = QLabel(f"Rs. {transaction[4]:.2f}")
                if transaction[3]:  # is_credit
                    amount_label.setStyleSheet("color: red; font-weight: bold;")
                else:
                    amount_label.setStyleSheet("color: green; font-weight: bold;")
                
                # Add expiry warning if applicable
                expiry_warning = ""
                if len(transaction) > 7 and transaction[7]:  # expiry_date exists
                    try:
                        expiry_date = QDate.fromString(transaction[7], "yyyy-MM-dd")
                        if expiry_date.isValid():
                            if expiry_date < QDate.currentDate():
                                expiry_warning = "⚠️ EXPIRED"
                            elif expiry_date < QDate.currentDate().addDays(30):
                                expiry_warning = "⚠️ EXPIRING"
                    except:
                        pass
                
                transaction_layout.addWidget(date_label)
                transaction_layout.addWidget(customer_label)
                transaction_layout.addWidget(product_label)
                if expiry_warning:
                    warning_label = QLabel(expiry_warning)
                    warning_label.setStyleSheet("color: #e74c3c; font-weight: bold; font-size: 10px;")
                    transaction_layout.addWidget(warning_label)
                transaction_layout.addStretch(1)
                transaction_layout.addWidget(amount_label)
                
                transactions_layout.addWidget(transaction_frame)
            
            # Add the "View All Transactions" button with functionality
            view_all_btn = QPushButton("View All Transactions")
            view_all_btn.setStyleSheet("""
                QPushButton {
                    background-color: #4e73df;
                    color: white;
                    border: none;
                    padding: 8px 16px;
                    border-radius: 4px;
                }
                QPushButton:hover {
                    background-color: #2e59d9;
                }
            """)
            # Connect the button to switch to ledger tab
            view_all_btn.clicked.connect(self.viewAllTransactions)
            transactions_layout.addWidget(view_all_btn)
            
            dashboard_layout.addLayout(transactions_layout)
        
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
        """Get alerts for expired and expiring products"""
        try:
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            upcoming_date = QDate.currentDate().addDays(30).toString("yyyy-MM-dd")
            
            # Get all products directly from MongoDB
            products = self.db.get_products()
            entries = self.db.get_entries()
            
            # Create a set of product IDs that have sales
            products_with_sales = set()
            for entry in entries:
                if entry.get('is_credit'):
                    products_with_sales.add(str(entry.get('product_id', '')))
            
            expired_alerts = []
            expiring_alerts = []
            
            for product in products:
                # Only check products that have sales
                product_id = str(product.get('id', ''))
                if product_id in products_with_sales:
                    expiry_date = product.get('expiry_date', '')
                    if expiry_date:
                        name = product.get('name', 'Unknown')
                        batch = product.get('batch_number', 'Unknown')
                        
                        if expiry_date < current_date:
                            expired_alerts.append(f"{name} (Batch: {batch}) - Expired: {expiry_date}")
                        elif current_date <= expiry_date <= upcoming_date:
                            days_until = QDate.currentDate().daysTo(QDate.fromString(expiry_date, "yyyy-MM-dd"))
                            expiring_alerts.append(f"{name} (Batch: {batch}) - Expires in {days_until} days")
            
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
        """Get batch-related metrics"""
        try:
            products = self.db.get_products()
            entries = self.db.get_entries()
            
            # Get products with sales
            products_with_sales = set()
            for entry in entries:
                if entry.get('is_credit'):
                    products_with_sales.add(str(entry.get('product_id', '')))
            
            # Count unique product names with sales
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
                'total_products': len(products)
            }
            
        except Exception as e:
            print(f"Error getting batch metrics: {e}")
            import traceback
            traceback.print_exc()
            return {
                'active_batches': 0,
                'unique_products': 0,
                'total_products': 0
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
            current_balance = total_credits - total_debits
            
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
            
            return {
                'total_sales': current_sales,
                'sales_change': round(sales_change, 1),
                'transaction_count': current_count,
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
            entries = self.db.get_entries()
            customers = self.db.get_customers()
            products = self.db.get_products()
            
            # Create lookup dictionaries with string IDs
            customer_lookup = {}
            for c in customers:
                customer_lookup[str(c.get('id', ''))] = c.get('name', 'Unknown')
            
            product_lookup = {}
            for p in products:
                product_lookup[str(p.get('id', ''))] = {
                    'name': p.get('name', 'Unknown'),
                    'batch_number': p.get('batch_number', ''),
                    'expiry_date': p.get('expiry_date', '')
                }
            
            # Sort entries by date (most recent first) and get top 5
            sorted_entries = sorted(entries, key=lambda x: x.get('date', ''), reverse=True)[:5]
            
            result = []
            for entry in sorted_entries:
                customer_id = str(entry.get('customer_id', ''))
                product_id = str(entry.get('product_id', ''))
                
                customer_name = customer_lookup.get(customer_id, 'Unknown Customer')
                product_info = product_lookup.get(product_id, {})
                product_name = product_info.get('name', 'Unknown Product')
                batch_number = product_info.get('batch_number', '')
                expiry_date = product_info.get('expiry_date', '')
                
                try:
                    total = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    quantity = float(entry.get('quantity', 0))
                except (ValueError, TypeError):
                    total = 0
                    quantity = 0
                
                # Format: [date, customer, product, is_credit, total, quantity, batch_number, expiry_date]
                result.append([
                    entry.get('date', ''),
                    customer_name,
                    product_name,
                    entry.get('is_credit', False),
                    total,
                    quantity,
                    batch_number,
                    expiry_date
                ])
            
            return result
            
        except Exception as e:
            print(f"Error getting recent transactions: {e}")
            import traceback
            traceback.print_exc()
            return []