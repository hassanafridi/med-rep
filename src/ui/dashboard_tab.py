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
from database.mongo_adapter import MongoAdapter

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
        self.db = MongoAdapter()
        self.current_user = current_user
        self.initUI()
        
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
        expiry_chart_view = QChartView(expiry_chart)
        expiry_chart_view.setRenderHint(QPainter.Antialiasing)
        expiry_chart_view.setMinimumHeight(300)
        
        expiry_card = ChartCard("Expiry Timeline", expiry_chart_view)
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
                    amount_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    amount_label.setStyleSheet("color: red; font-weight: bold;")
                
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
            
            # Get expired products with sales data
            expired_products = self.db.execute('''
                SELECT DISTINCT p.name, p.batch_number, p.expiry_date,
                       SUM(e.quantity * e.unit_price) as total_sales
                FROM products p
                LEFT JOIN entries e ON p.id = e.product_id AND e.is_credit = 1
                WHERE p.expiry_date < ?
                GROUP BY p.id, p.name, p.batch_number, p.expiry_date
                HAVING total_sales > 0
                ORDER BY p.expiry_date
            ''', (current_date,))
            
            # Get expiring products with sales data
            expiring_products = self.db.execute('''
                SELECT DISTINCT p.name, p.batch_number, p.expiry_date,
                       SUM(e.quantity * e.unit_price) as total_sales
                FROM products p
                LEFT JOIN entries e ON p.id = e.product_id AND e.is_credit = 1
                WHERE p.expiry_date >= ? AND p.expiry_date <= ?
                GROUP BY p.id, p.name, p.batch_number, p.expiry_date
                HAVING total_sales > 0
                ORDER BY p.expiry_date
            ''', (current_date, upcoming_date))
            
            # Handle MongoDB adapter results - ensure we have lists
            if not isinstance(expired_products, list):
                expired_products = []
            if not isinstance(expiring_products, list):
                expiring_products = []
            
            # Format alerts
            expired_alerts = []
            for result in expired_products:
                if len(result) >= 4:
                    name, batch, expiry, sales = result[:4]
                    expired_alerts.append(f"{name} (Batch: {batch}) - Expired: {expiry}")
            
            expiring_alerts = []
            for result in expiring_products:
                if len(result) >= 4:
                    name, batch, expiry, sales = result[:4]
                    days_until = QDate.currentDate().daysTo(QDate.fromString(expiry, "yyyy-MM-dd"))
                    expiring_alerts.append(f"{name} (Batch: {batch}) - Expires in {days_until} days")
            
            return {
                'expired': expired_alerts,
                'expiring': expiring_alerts
            }
            
        except Exception as e:
            print(f"Error getting product alerts: {e}")
            return {'expired': [], 'expiring': []}
    
    def getBatchMetrics(self):
        """Get batch-related metrics"""
        try:
            # Get active batches (products with sales)
            result = self.db.execute('''
                SELECT COUNT(DISTINCT p.id) as active_batches,
                       COUNT(DISTINCT p.name) as unique_products
                FROM products p
                JOIN entries e ON p.id = e.product_id
                WHERE e.is_credit = 1
            ''')
            
            active_batches = 0
            unique_products = 0
            if result and len(result) > 0 and len(result[0]) >= 2:
                active_batches = result[0][0] or 0
                unique_products = result[0][1] or 0
            
            # Get total products in inventory
            total_products_result = self.db.execute('SELECT COUNT(*) FROM products')
            total_products = 0
            if total_products_result and len(total_products_result) > 0:
                total_products = total_products_result[0][0] or 0
            
            return {
                'active_batches': active_batches,
                'unique_products': unique_products,
                'total_products': total_products
            }
            
        except Exception as e:
            print(f"Error getting batch metrics: {e}")
            return {
                'active_batches': 0,
                'unique_products': 0,
                'total_products': 0
            }
        
    def loadKPIMetrics(self):
        """Load KPI metrics from database"""
        try:
            # Get current month and last month dates
            today = QDate.currentDate()
            current_month_start = QDate(today.year(), today.month(), 1).toString("yyyy-MM-dd")
            
            last_month = today.addMonths(-1)
            last_month_start = QDate(last_month.year(), last_month.month(), 1).toString("yyyy-MM-dd")
            last_month_end = QDate(today.year(), today.month(), 1).addDays(-1).toString("yyyy-MM-dd")
            
            # Get total sales (credits) for current month
            result = self.db.execute('''
                SELECT SUM(quantity * unit_price) 
                FROM entries 
                WHERE is_credit = 1 AND date >= ?
            ''', (current_month_start,))
            current_sales = 0
            if result and len(result) > 0 and result[0] and result[0][0] is not None:
                current_sales = result[0][0]
            
            # Get total sales for last month
            result = self.db.execute('''
                SELECT SUM(quantity * unit_price) 
                FROM entries 
                WHERE is_credit = 1 AND date >= ? AND date <= ?
            ''', (last_month_start, last_month_end))
            last_month_sales = 0
            if result and len(result) > 0 and result[0] and result[0][0] is not None:
                last_month_sales = result[0][0]
            
            # Calculate sales change percentage
            sales_change = 0
            if last_month_sales > 0:
                sales_change = ((current_sales - last_month_sales) / last_month_sales) * 100
            
            # Get transaction count for current month
            result = self.db.execute('''
                SELECT COUNT(*) 
                FROM entries 
                WHERE date >= ?
            ''', (current_month_start,))
            current_count = 0
            if result and len(result) > 0 and result[0] and result[0][0] is not None:
                current_count = result[0][0]
            
            # Get transaction count for last month
            result = self.db.execute('''
                SELECT COUNT(*) 
                FROM entries 
                WHERE date >= ? AND date <= ?
            ''', (last_month_start, last_month_end))
            last_month_count = 0
            if result and len(result) > 0 and result[0] and result[0][0] is not None:
                last_month_count = result[0][0]
            
            # Calculate transaction change percentage
            transaction_change = 0
            if last_month_count > 0:
                transaction_change = ((current_count - last_month_count) / last_month_count) * 100
            
            # Calculate average sale for current month
            average_sale = 0
            if current_count > 0:
                average_sale = current_sales / current_count
            
            # Calculate average sale for last month
            last_month_average = 0
            if last_month_count > 0:
                last_month_average = last_month_sales / last_month_count
            
            # Calculate average change percentage
            average_change = 0
            if last_month_average > 0:
                average_change = ((average_sale - last_month_average) / last_month_average) * 100
            
            # Get current balance
            result = self.db.execute('SELECT MAX(balance) FROM transactions')
            current_balance = 0
            if result and len(result) > 0 and result[0] and result[0][0] is not None:
                current_balance = result[0][0]
            
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
        """Create monthly sales chart"""
        chart = QChart()
        chart.setTitle("Monthly Sales")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        try:
            # Get data for the last 6 months
            today = QDate.currentDate()
            
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
                
                # Get credits for this month
                result = self.db.execute('''
                    SELECT SUM(quantity * unit_price) 
                    FROM entries 
                    WHERE is_credit = 1 AND date >= ? AND date <= ?
                ''', (month_start, month_end))
                month_credits = 0
                if result and len(result) > 0 and result[0] and result[0][0] is not None:
                    month_credits = result[0][0]
                credits.append(month_credits)
                
                # Get debits for this month
                result = self.db.execute('''
                    SELECT SUM(quantity * unit_price) 
                    FROM entries 
                    WHERE is_credit = 0 AND date >= ? AND date <= ?
                ''', (month_start, month_end))
                month_debits = 0
                if result and len(result) > 0 and result[0] and result[0][0] is not None:
                    month_debits = result[0][0]
                debits.append(month_debits)
            
            # Only create chart if we have data
            if any(credits) or any(debits):
                # Create bar sets
                credit_set = QBarSet("Credits")
                credit_set.setColor(QColor("#4e73df"))
                credit_set.append(credits)
                
                debit_set = QBarSet("Debits")
                debit_set.setColor(QColor("#e74a3b"))
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
                axisY.setTitleText("Amount (Rs. )")
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
            chart.setTitle("Monthly Sales - Error Loading Data")
        
        return chart
    
    def createProductChart(self):
        """Create product distribution pie chart (grouped by product name)"""
        chart = QChart()
        chart.setTitle("Product Distribution")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        try:
            # Get product sales data grouped by product name (combines all batches)
            products = self.db.execute('''
                SELECT p.name, SUM(e.quantity * e.unit_price) as total,
                       COUNT(DISTINCT p.batch_number) as batch_count
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.is_credit = 1
                GROUP BY p.name
                ORDER BY total DESC
                LIMIT 5
            ''')
            
            if products and len(products) > 0:
                series = QPieSeries()
                
                # Get total sales for percentage calculation
                result = self.db.execute('''
                    SELECT SUM(e.quantity * e.unit_price) as total
                    FROM entries e
                    WHERE e.is_credit = 1
                ''')
                total_sales = 0
                if result and len(result) > 0 and result[0] and result[0][0] is not None:
                    total_sales = result[0][0]
                
                if total_sales > 0:
                    for product, total, batch_count in products:
                        series.append(product, total)
                    
                    # Add "Other" slice for remaining products if needed
                    top_sales = sum(total for _, total, _ in products)
                    
                    if total_sales > top_sales:
                        series.append("Other", total_sales - top_sales)
                    
                    # Customize slices
                    for i in range(series.count()):
                        slice = series.slices()[i]
                        slice.setLabelVisible(False)  # Hide default labels
                        percentage = (slice.value() / total_sales) * 100
                        
                        # Add batch count info for main products (not "Other")
                        if i < len(products):
                            batch_count = products[i][2]
                            batch_info = f" ({batch_count} batch{'es' if batch_count > 1 else ''})"
                            slice.setLabel(f"{slice.label()}{batch_info}: {percentage:.1f}%")
                        else:
                            slice.setLabel(f"{slice.label()}: {percentage:.1f}%")
                    
                    chart.addSeries(series)
                    
                    # Set legend
                    chart.legend().setVisible(True)
                    chart.legend().setAlignment(Qt.AlignRight)
                else:
                    chart.setTitle("Product Distribution - No Sales Data")
            else:
                chart.setTitle("Product Distribution - No Data Available")
            
        except Exception as e:
            print(f"Error creating product chart: {e}")
            chart.setTitle("Product Distribution - Error Loading Data")
        
        return chart
    
    def createExpiryChart(self):
        """Create expiry timeline chart showing products by expiry status"""
        chart = QChart()
        chart.setTitle("Product Expiry Status")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        try:
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            upcoming_date = QDate.currentDate().addDays(30).toString("yyyy-MM-dd")
            
            # Get products with sales, categorized by expiry status
            expiry_data = self.db.execute('''
                SELECT 
                    CASE 
                        WHEN p.expiry_date < ? THEN 'Expired'
                        WHEN p.expiry_date <= ? THEN 'Expiring Soon'
                        ELSE 'Valid'
                    END as status,
                    COUNT(DISTINCT p.id) as product_count,
                    SUM(e.quantity * e.unit_price) as total_sales
                FROM products p
                JOIN entries e ON p.id = e.product_id
                WHERE e.is_credit = 1
                GROUP BY status
            ''', (current_date, upcoming_date))
            
            if expiry_data and len(expiry_data) > 0:
                # Create pie chart for expiry status
                series = QPieSeries()
                
                colors = {
                    'Expired': QColor("#e74c3c"),      # Red
                    'Expiring Soon': QColor("#f39c12"), # Orange
                    'Valid': QColor("#27ae60")         # Green
                }
                
                total_products = sum(count for _, count, _ in expiry_data)
                
                for status, count, sales in expiry_data:
                    slice = series.append(status, count)
                    slice.setColor(colors.get(status, QColor("#95a5a6")))
                    percentage = (count / total_products) * 100 if total_products > 0 else 0
                    slice.setLabel(f"{status}: {count} products ({percentage:.1f}%)")
                    slice.setLabelVisible(True)
                
                chart.addSeries(series)
                
                # Set legend
                chart.legend().setVisible(True)
                chart.legend().setAlignment(Qt.AlignBottom)
            else:
                chart.setTitle("Product Expiry Status - No Data Available")
            
        except Exception as e:
            print(f"Error creating expiry chart: {e}")
            chart.setTitle("Product Expiry Status - Error Loading Data")
        
        return chart
    
    def getRecentTransactions(self):
        """Get recent transactions with batch and expiry information"""
        try:
            # Get recent transactions with batch and expiry data
            result = self.db.execute('''
                SELECT e.date, c.name, p.name, e.is_credit, 
                       (e.quantity * e.unit_price) as total,
                       e.quantity, p.batch_number, p.expiry_date
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                JOIN products p ON e.product_id = p.id
                ORDER BY e.id DESC
                LIMIT 5
            ''')
            
            return result if result else []
            
        except Exception as e:
            print(f"Error getting recent transactions: {e}")
            return []