from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QComboBox, QSizePolicy, QGridLayout,
    QScrollArea
)
from PyQt5.QtCore import Qt, QDate, QSize
from PyQt5.QtGui import QColor, QPainter, QFont
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QValueAxis, QBarCategoryAxis, QPieSeries

import sys
import os

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Database

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

class DashboardTab(QWidget):
    def __init__(self, current_user=None):
        super().__init__()
        self.db = Database()
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
        
        # KPI Cards section
        kpi_layout = QHBoxLayout()
        
        # Load KPI metrics
        metrics = self.loadKPIMetrics()
        
        # Create KPI cards
        total_sales_card = KPICard("Total Sales", f"${metrics['total_sales']:.2f}", 
                               f"{metrics['sales_change']}% from last month", "#4e73df")
        
        total_transactions_card = KPICard("Total Transactions", str(metrics['transaction_count']),
                                     f"{metrics['transaction_change']}% from last month", "#1cc88a")
        
        average_sale_card = KPICard("Average Sale", f"${metrics['average_sale']:.2f}",
                                f"{metrics['average_change']}% from last month", "#36b9cc")
        
        balance_card = KPICard("Current Balance", f"${metrics['current_balance']:.2f}",
                          "Updated just now", "#f6c23e")
        
        kpi_layout.addWidget(total_sales_card)
        kpi_layout.addWidget(total_transactions_card)
        kpi_layout.addWidget(average_sale_card)
        kpi_layout.addWidget(balance_card)
        
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
        
        # Product distribution chart
        product_chart = self.createProductChart()
        product_chart_view = QChartView(product_chart)
        product_chart_view.setRenderHint(QPainter.Antialiasing)
        product_chart_view.setMinimumHeight(300)
        
        product_card = ChartCard("Product Distribution", product_chart_view)
        charts_layout.addWidget(product_card, 0, 1)
        
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
                product_label = QLabel(transaction[2])
                
                amount_label = QLabel(f"${transaction[4]:.2f}")
                if transaction[3]:  # is_credit
                    amount_label.setStyleSheet("color: green; font-weight: bold;")
                else:
                    amount_label.setStyleSheet("color: red; font-weight: bold;")
                
                transaction_layout.addWidget(date_label)
                transaction_layout.addWidget(customer_label)
                transaction_layout.addWidget(product_label)
                transaction_layout.addStretch(1)
                transaction_layout.addWidget(amount_label)
                
                transactions_layout.addWidget(transaction_frame)
            
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
            transactions_layout.addWidget(view_all_btn)
            
            dashboard_layout.addLayout(transactions_layout)
        
        # Set dashboard widget as the scrollable content
        scroll_area.setWidget(dashboard_widget)
        main_layout.addWidget(scroll_area)
        
        self.setLayout(main_layout)
        
    def loadKPIMetrics(self):
        """Load KPI metrics from database"""
        try:
            self.db.connect()
            
            # Get current month and last month dates
            today = QDate.currentDate()
            current_month_start = QDate(today.year(), today.month(), 1).toString("yyyy-MM-dd")
            
            last_month = today.addMonths(-1)
            last_month_start = QDate(last_month.year(), last_month.month(), 1).toString("yyyy-MM-dd")
            last_month_end = QDate(today.year(), today.month(), 1).addDays(-1).toString("yyyy-MM-dd")
            
            # Get total sales (credits) for current month
            self.db.cursor.execute('''
                SELECT SUM(quantity * unit_price) 
                FROM entries 
                WHERE is_credit = 1 AND date >= ?
            ''', (current_month_start,))
            current_sales = self.db.cursor.fetchone()[0] or 0
            
            # Get total sales for last month
            self.db.cursor.execute('''
                SELECT SUM(quantity * unit_price) 
                FROM entries 
                WHERE is_credit = 1 AND date >= ? AND date <= ?
            ''', (last_month_start, last_month_end))
            last_month_sales = self.db.cursor.fetchone()[0] or 0
            
            # Calculate sales change percentage
            sales_change = 0
            if last_month_sales > 0:
                sales_change = ((current_sales - last_month_sales) / last_month_sales) * 100
            
            # Get transaction count for current month
            self.db.cursor.execute('''
                SELECT COUNT(*) 
                FROM entries 
                WHERE date >= ?
            ''', (current_month_start,))
            current_count = self.db.cursor.fetchone()[0] or 0
            
            # Get transaction count for last month
            self.db.cursor.execute('''
                SELECT COUNT(*) 
                FROM entries 
                WHERE date >= ? AND date <= ?
            ''', (last_month_start, last_month_end))
            last_month_count = self.db.cursor.fetchone()[0] or 0
            
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
            self.db.cursor.execute('SELECT MAX(balance) FROM transactions')
            current_balance = self.db.cursor.fetchone()[0] or 0
            
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
        finally:
            self.db.close()
    
    def createSalesChart(self):
        """Create monthly sales chart"""
        chart = QChart()
        chart.setTitle("Monthly Sales")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        try:
            self.db.connect()
            
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
                self.db.cursor.execute('''
                    SELECT SUM(quantity * unit_price) 
                    FROM entries 
                    WHERE is_credit = 1 AND date >= ? AND date <= ?
                ''', (month_start, month_end))
                month_credits = self.db.cursor.fetchone()[0] or 0
                credits.append(month_credits)
                
                # Get debits for this month
                self.db.cursor.execute('''
                    SELECT SUM(quantity * unit_price) 
                    FROM entries 
                    WHERE is_credit = 0 AND date >= ? AND date <= ?
                ''', (month_start, month_end))
                month_debits = self.db.cursor.fetchone()[0] or 0
                debits.append(month_debits)
            
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
            axisY.setTitleText("Amount ($)")
            axisY.setLabelsAngle(0)
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set legend
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignBottom)
            
        except Exception as e:
            print(f"Error creating sales chart: {e}")
        finally:
            self.db.close()
        
        return chart
    
    def createProductChart(self):
        """Create product distribution pie chart"""
        chart = QChart()
        chart.setTitle("Product Distribution")
        chart.setAnimationOptions(QChart.SeriesAnimations)
        
        try:
            self.db.connect()
            
            # Get product sales data
            self.db.cursor.execute('''
                SELECT p.name, SUM(e.quantity * e.unit_price) as total
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.is_credit = 1
                GROUP BY p.name
                ORDER BY total DESC
                LIMIT 5
            ''')
            products = self.db.cursor.fetchall()
            
            series = QPieSeries()
            
            if products:
                for product, total in products:
                    series.append(product, total)
                
                # Add "Other" slice for remaining products
                self.db.cursor.execute('''
                    SELECT SUM(e.quantity * e.unit_price) as total
                    FROM entries e
                    WHERE e.is_credit = 1
                ''')
                total_sales = self.db.cursor.fetchone()[0] or 0
                
                top_sales = sum(total for _, total in products)
                
                if total_sales > top_sales:
                    series.append("Other", total_sales - top_sales)
                
                # Customize slices
                for i in range(series.count()):
                    slice = series.slices()[i]
                    slice.setLabelVisible(True)
                    percentage = (slice.value() / total_sales) * 100
                    slice.setLabel(f"{slice.label()}: {percentage:.1f}%")
            
            chart.addSeries(series)
            
            # Set legend
            chart.legend().setVisible(True)
            chart.legend().setAlignment(Qt.AlignRight)
            
        except Exception as e:
            print(f"Error creating product chart: {e}")
        finally:
            self.db.close()
        
        return chart
    
    def getRecentTransactions(self):
        """Get recent transactions"""
        try:
            self.db.connect()
            
            # Get recent transactions
            self.db.cursor.execute('''
                SELECT e.date, c.name, p.name, e.is_credit, (e.quantity * e.unit_price) as total
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                JOIN products p ON e.product_id = p.id
                ORDER BY e.id DESC
                LIMIT 5
            ''')
            
            return self.db.cursor.fetchall()
            
        except Exception as e:
            print(f"Error getting recent transactions: {e}")
            return []
        finally:
            self.db.close()