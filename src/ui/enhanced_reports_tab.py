# src/ui/enhanced_reports_tab.py

"""
Enhanced reports tab that leverages MongoDB's advanced querying capabilities - MongoDB Only
"""

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox,
    QComboBox, QDateEdit, QPushButton, QTableWidget, QTableWidgetItem,
    QHeaderView, QTextEdit, QLabel, QProgressBar, QMessageBox,
    QSplitter, QFrame, QGridLayout
)
from PyQt5.QtCore import Qt, QDate, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QColor, QPalette
from PyQt5.QtChart import QChart, QChartView, QBarSeries, QBarSet, QLineSeries, QPieSeries
from PyQt5.QtChart import QCategoryAxis, QValueAxis, QLegend
import sys
import os
from datetime import datetime, timedelta
import json

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter

class ReportGenerationThread(QThread):
    """Thread for generating complex reports without freezing the UI"""
    report_ready = pyqtSignal(dict)
    progress_updated = pyqtSignal(int)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, query_func, *args, **kwargs):
        super().__init__()
        self.query_func = query_func
        self.args = args
        self.kwargs = kwargs
    
    def run(self):
        try:
            self.progress_updated.emit(25)
            result = self.query_func(*self.args, **self.kwargs)
            self.progress_updated.emit(75)
            self.report_ready.emit(result)
            self.progress_updated.emit(100)
        except Exception as e:
            self.error_occurred.emit(str(e))

class EnhancedReportsTab(QWidget):
    def __init__(self, mongo_adapter=None):
        super().__init__()
        try:
            self.mongo_adapter = mongo_adapter or MongoAdapter()
            self.current_thread = None
            self.current_product_data = []
            self.initUI()
        except Exception as e:
            print(f"Error initializing Enhanced Reports tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Enhanced Reports tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the enhanced reports tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.mongo_adapter)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Enhanced Reports tab: {str(e)}")
    
    def initUI(self):
        """Initialize the enhanced reports UI"""
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        title_label = QLabel("Enhanced Analytics & Reports")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        # Progress bar for long-running queries
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        header_layout.addWidget(self.progress_bar)
        
        main_layout.addLayout(header_layout)
        
        # Create tabs for different report categories
        self.tab_widget = QTabWidget()
        
        # Customer Analytics Tab
        self.customer_tab = self.create_customer_analytics_tab()
        self.tab_widget.addTab(self.customer_tab, "Customer Analytics")
        
        # Product Performance Tab
        self.product_tab = self.create_product_performance_tab()
        self.tab_widget.addTab(self.product_tab, "Product Performance")
        
        # Sales Trends Tab
        self.trends_tab = self.create_sales_trends_tab()
        self.tab_widget.addTab(self.trends_tab, "Sales Trends")
        
        # Financial Analysis Tab
        self.financial_tab = self.create_financial_analysis_tab()
        self.tab_widget.addTab(self.financial_tab, "Financial Analysis")
        
        # Inventory Management Tab
        self.inventory_tab = self.create_inventory_management_tab()
        self.tab_widget.addTab(self.inventory_tab, "Inventory Management")
        
        main_layout.addWidget(self.tab_widget)
        self.setLayout(main_layout)
    
    def create_customer_analytics_tab(self) -> QWidget:
        """Create customer analytics tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_group = QGroupBox("Customer Analysis Options")
        controls_layout = QHBoxLayout()
        
        # Top customers count
        controls_layout.addWidget(QLabel("Top Customers:"))
        self.customer_count_combo = QComboBox()
        self.customer_count_combo.addItems(["10", "25", "50", "100"])
        controls_layout.addWidget(self.customer_count_combo)
        
        # Generate button
        generate_customer_btn = QPushButton("Generate Customer Report")
        generate_customer_btn.clicked.connect(self.generate_customer_analytics)
        generate_customer_btn.setStyleSheet("""
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
        controls_layout.addWidget(generate_customer_btn)
        
        # Segmentation button
        segment_btn = QPushButton("Customer Segmentation")
        segment_btn.clicked.connect(self.generate_customer_segmentation)
        controls_layout.addWidget(segment_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Results area with splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Table for customer data
        self.customer_table = QTableWidget()
        self.customer_table.setAlternatingRowColors(True)
        splitter.addWidget(self.customer_table)
        
        # Chart area
        self.customer_chart_view = QChartView()
        splitter.addWidget(self.customer_chart_view)
        
        # Set initial splitter sizes
        splitter.setSizes([400, 400])
        layout.addWidget(splitter)
        
        widget.setLayout(layout)
        return widget
    
    def create_product_performance_tab(self) -> QWidget:
        """Create product performance tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_group = QGroupBox("Product Performance Analysis")
        controls_layout = QHBoxLayout()
        
        generate_product_btn = QPushButton("Analyze Product Performance")
        generate_product_btn.clicked.connect(self.generate_product_analysis)
        generate_product_btn.setStyleSheet("""
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
        controls_layout.addWidget(generate_product_btn)
        
        export_btn = QPushButton("Export to CSV")
        export_btn.clicked.connect(self.export_product_analysis)
        controls_layout.addWidget(export_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Results area
        splitter = QSplitter(Qt.Vertical)
        
        # Table for product data
        self.product_table = QTableWidget()
        self.product_table.setAlternatingRowColors(True)
        splitter.addWidget(self.product_table)
        
        # Chart area
        self.product_chart_view = QChartView()
        splitter.addWidget(self.product_chart_view)
        
        splitter.setSizes([300, 300])
        layout.addWidget(splitter)
        
        widget.setLayout(layout)
        return widget
    
    def create_sales_trends_tab(self) -> QWidget:
        """Create sales trends tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_group = QGroupBox("Sales Trend Analysis")
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Time Period:"))
        self.trend_period_combo = QComboBox()
        self.trend_period_combo.addItems(["3 months", "6 months", "12 months", "24 months"])
        controls_layout.addWidget(self.trend_period_combo)
        
        generate_trend_btn = QPushButton("Generate Trend Report")
        generate_trend_btn.clicked.connect(self.generate_sales_trends)
        generate_trend_btn.setStyleSheet("""
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
        controls_layout.addWidget(generate_trend_btn)
        
        forecast_btn = QPushButton("Sales Forecasting")
        forecast_btn.clicked.connect(self.generate_sales_forecast)
        controls_layout.addWidget(forecast_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Results area
        self.trends_chart_view = QChartView()
        layout.addWidget(self.trends_chart_view)
        
        # Summary table
        self.trends_table = QTableWidget()
        self.trends_table.setMaximumHeight(200)
        self.trends_table.setAlternatingRowColors(True)
        layout.addWidget(self.trends_table)
        
        widget.setLayout(layout)
        return widget
    
    def create_financial_analysis_tab(self) -> QWidget:
        """Create financial analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_group = QGroupBox("Financial Analysis")
        controls_layout = QHBoxLayout()
        
        credit_debit_btn = QPushButton("Credit/Debit Analysis")
        credit_debit_btn.clicked.connect(self.generate_credit_debit_analysis)
        credit_debit_btn.setStyleSheet("""
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
        controls_layout.addWidget(credit_debit_btn)
        
        outstanding_btn = QPushButton("Outstanding Balances")
        outstanding_btn.clicked.connect(self.generate_outstanding_report)
        controls_layout.addWidget(outstanding_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Results in grid layout
        results_frame = QFrame()
        results_layout = QGridLayout()
        
        # Summary cards
        self.create_summary_cards(results_layout)
        
        # Detailed table
        self.financial_table = QTableWidget()
        self.financial_table.setAlternatingRowColors(True)
        results_layout.addWidget(self.financial_table, 1, 0, 1, 4)
        
        # Chart
        self.financial_chart_view = QChartView()
        results_layout.addWidget(self.financial_chart_view, 2, 0, 1, 4)
        
        results_frame.setLayout(results_layout)
        layout.addWidget(results_frame)
        
        widget.setLayout(layout)
        return widget
    
    def create_inventory_management_tab(self) -> QWidget:
        """Create inventory management tab"""
        widget = QWidget()
        layout = QVBoxLayout()
        
        # Controls
        controls_group = QGroupBox("Inventory Analysis")
        controls_layout = QHBoxLayout()
        
        controls_layout.addWidget(QLabel("Alert Days:"))
        self.expiry_days_combo = QComboBox()
        self.expiry_days_combo.addItems(["7", "15", "30", "60", "90"])
        self.expiry_days_combo.setCurrentText("30")
        controls_layout.addWidget(self.expiry_days_combo)
        
        expiry_btn = QPushButton("Check Expiring Products")
        expiry_btn.clicked.connect(self.generate_expiry_report)
        expiry_btn.setStyleSheet("""
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
        controls_layout.addWidget(expiry_btn)
        
        stock_movement_btn = QPushButton("Stock Movement Analysis")
        stock_movement_btn.clicked.connect(self.generate_stock_movement)
        controls_layout.addWidget(stock_movement_btn)
        
        controls_layout.addStretch()
        controls_group.setLayout(controls_layout)
        layout.addWidget(controls_group)
        
        # Results area
        self.inventory_table = QTableWidget()
        self.inventory_table.setAlternatingRowColors(True)
        layout.addWidget(self.inventory_table)
        
        widget.setLayout(layout)
        return widget

    def create_summary_cards(self, layout):
        """Create summary cards for financial overview"""
        # Total Revenue Card
        self.revenue_card = self.create_summary_card("Total Revenue", "PKR0", QColor(76, 175, 80))
        layout.addWidget(self.revenue_card, 0, 0)
        
        # Outstanding Balance Card
        self.outstanding_card = self.create_summary_card("Outstanding", "PKR0", QColor(255, 152, 0))
        layout.addWidget(self.outstanding_card, 0, 1)
        
        # Credit Balance Card
        self.credit_card = self.create_summary_card("Credit Balance", "PKR0", QColor(33, 150, 243))
        layout.addWidget(self.credit_card, 0, 2)
        
        # Active Customers Card
        self.customers_card = self.create_summary_card("Active Customers", "0", QColor(156, 39, 176))
        layout.addWidget(self.customers_card, 0, 3)
    
    def create_summary_card(self, title: str, value: str, color: QColor) -> QFrame:
        """Create a summary card widget"""
        card = QFrame()
        card.setFrameStyle(QFrame.Box)
        card.setFixedHeight(100)
        card.setStyleSheet(f"""
            QFrame {{
                border: 2px solid {color.name()};
                border-radius: 10px;
                background-color: rgba({color.red()}, {color.green()}, {color.blue()}, 0.1);
            }}
        """)
        
        layout = QVBoxLayout()
        
        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 10))
        title_label.setAlignment(Qt.AlignCenter)
        
        value_label = QLabel(value)
        value_label.setFont(QFont("Arial", 16, QFont.Bold))
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"color: {color.name()};")
        
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        card.setLayout(layout)
        
        # Store reference to value label for updates
        card.value_label = value_label
        
        return card

    # MongoDB-based Report Generation Methods
    
    def generate_customer_analytics(self):
        """Generate customer analytics report using MongoDB"""
        try:
            # Validate prerequisites
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
            
            self.show_progress()
            limit = int(self.customer_count_combo.currentText())
            
            self.current_thread = ReportGenerationThread(
                self.get_top_customers_by_revenue, limit
            )
            self.current_thread.report_ready.connect(self.display_customer_analytics)
            self.current_thread.progress_updated.connect(self.update_progress)
            self.current_thread.error_occurred.connect(self.handle_error)
            self.current_thread.start()
            
        except Exception as e:
            self.hide_progress()
            QMessageBox.critical(self, "Error", f"Failed to generate customer analytics: {str(e)}")

    def get_top_customers_by_revenue(self, limit=10):
        """Get top customers by revenue using MongoDB aggregation"""
        try:
            # Check if mongo_adapter is available
            if not self.mongo_adapter:
                print("MongoDB adapter not available")
                return []
            
            # Get entries and customers from MongoDB
            entries = self.mongo_adapter.get_entries()
            customers = self.mongo_adapter.get_customers()
            
            # Validate data
            if not entries or not customers:
                print(f"Insufficient data: {len(entries) if entries else 0} entries, {len(customers) if customers else 0} customers")
                return []
            
            # Create customer lookup
            customer_lookup = {}
            for customer in customers:
                customer_lookup[str(customer.get('id', ''))] = customer
            
            # Calculate revenue per customer
            customer_revenue = {}
            for entry in entries:
                if entry.get('is_credit'):
                    customer_id = str(entry.get('customer_id', ''))
                    revenue = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    
                    if customer_id in customer_revenue:
                        customer_revenue[customer_id]['total_revenue'] += revenue
                        customer_revenue[customer_id]['entry_count'] += 1
                    else:
                        customer_info = customer_lookup.get(customer_id, {})
                        customer_revenue[customer_id] = {
                            'name': customer_info.get('name', 'Unknown'),
                            'contact': customer_info.get('contact', ''),
                            'total_revenue': revenue,
                            'entry_count': 1
                        }
            
            # Sort and limit
            sorted_customers = sorted(
                customer_revenue.values(), 
                key=lambda x: x['total_revenue'], 
                reverse=True
            )[:limit]
            
            return sorted_customers
            
        except Exception as e:
            print(f"Error getting top customers: {e}")
            return []

    def display_customer_analytics(self, customers):
        """Display customer analytics results"""
        self.hide_progress()
        
        # Setup table
        headers = ["Customer Name", "Contact", "Total Revenue", "Entry Count"]
        self.customer_table.setColumnCount(len(headers))
        self.customer_table.setHorizontalHeaderLabels(headers)
        self.customer_table.setRowCount(len(customers))
        
        # Populate table
        for row, customer in enumerate(customers):
            self.customer_table.setItem(row, 0, QTableWidgetItem(customer.get("name", "")))
            self.customer_table.setItem(row, 1, QTableWidgetItem(customer.get("contact", "")))
            self.customer_table.setItem(row, 2, QTableWidgetItem(f"PKR{customer.get('total_revenue', 0):,.2f}"))
            self.customer_table.setItem(row, 3, QTableWidgetItem(str(customer.get("entry_count", 0))))
        
        self.customer_table.horizontalHeader().setStretchLastSection(True)
        self.customer_table.resizeColumnsToContents()
        
        # Create chart
        self.create_customer_revenue_chart(customers)
    
    def create_customer_revenue_chart(self, customers):
        """Create customer revenue chart"""
        chart = QChart()
        chart.setTitle("Top Customers by Revenue")
        
        # Bar series
        series = QBarSeries()
        bar_set = QBarSet("Revenue")
        
        categories = []
        for customer in customers[:10]:  # Top 10 for readability
            bar_set.append(customer.get("total_revenue", 0))
            categories.append(customer.get("name", "")[:15])  # Truncate long names
        
        series.append(bar_set)
        chart.addSeries(series)
        
        # Axes
        axis_x = QCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        self.customer_chart_view.setChart(chart)
    
    def generate_customer_segmentation(self):
        """Generate customer segmentation report using MongoDB"""
        self.show_progress()
        
        self.current_thread = ReportGenerationThread(
            self.get_customer_segmentation
        )
        self.current_thread.report_ready.connect(self.display_customer_segmentation)
        self.current_thread.progress_updated.connect(self.update_progress)
        self.current_thread.error_occurred.connect(self.handle_error)
        self.current_thread.start()
    
    def get_customer_segmentation(self):
        """Get customer segmentation using MongoDB data"""
        try:
            # Check if mongo_adapter is available
            if not self.mongo_adapter:
                print("MongoDB adapter not available for customer segmentation")
                return {}
            
            # Get data from MongoDB
            entries = self.mongo_adapter.get_entries()
            customers = self.mongo_adapter.get_customers()
            
            # Validate data
            if not entries or not customers:
                print("Insufficient data for customer segmentation")
                return {}
            
            # Create customer lookup
            customer_lookup = {}
            for customer in customers:
                customer_lookup[str(customer.get('id', ''))] = customer
            
            # Calculate customer metrics
            customer_metrics = {}
            for entry in entries:
                if entry.get('is_credit'):
                    customer_id = str(entry.get('customer_id', ''))
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    entry_date = entry.get('date', '')
                    
                    if customer_id not in customer_metrics:
                        customer_info = customer_lookup.get(customer_id, {})
                        customer_metrics[customer_id] = {
                            'name': customer_info.get('name', 'Unknown'),
                            'total_spent': 0,
                            'order_count': 0,
                            'last_order_date': entry_date,
                            'first_order_date': entry_date
                        }
                    
                    customer_metrics[customer_id]['total_spent'] += amount
                    customer_metrics[customer_id]['order_count'] += 1
                    
                    # Update dates
                    if entry_date > customer_metrics[customer_id]['last_order_date']:
                        customer_metrics[customer_id]['last_order_date'] = entry_date
                    if entry_date < customer_metrics[customer_id]['first_order_date']:
                        customer_metrics[customer_id]['first_order_date'] = entry_date
            
            # Calculate derived metrics and segment
            today = datetime.now().date()
            segmentation = {
                'High Value': {'count': 0, 'customers': []},
                'Medium Value': {'count': 0, 'customers': []},
                'Low Value': {'count': 0, 'customers': []},
                'Inactive': {'count': 0, 'customers': []}
            }
            
            for customer_id, metrics in customer_metrics.items():
                # Calculate additional metrics
                metrics['avg_order_value'] = metrics['total_spent'] / metrics['order_count']
                
                try:
                    last_order = datetime.strptime(metrics['last_order_date'], '%Y-%m-%d').date()
                    metrics['days_since_last_order'] = (today - last_order).days
                except:
                    metrics['days_since_last_order'] = 999
                
                # Segment customers
                if metrics['days_since_last_order'] > 180:
                    segment = 'Inactive'
                elif metrics['total_spent'] > 10000:
                    segment = 'High Value'
                elif metrics['total_spent'] > 5000:
                    segment = 'Medium Value'
                else:
                    segment = 'Low Value'
                
                segmentation[segment]['count'] += 1
                segmentation[segment]['customers'].append(metrics)
            
            return segmentation
            
        except Exception as e:
            print(f"Error getting customer segmentation: {e}")
            return {}

    def display_customer_segmentation(self, segmentation):
        """Display customer segmentation results"""
        self.hide_progress()
        
        # Create pie chart for segmentation
        chart = QChart()
        chart.setTitle("Customer Segmentation")
        
        series = QPieSeries()
        
        for segment_name, segment_data in segmentation.items():
            series.append(segment_name, segment_data["count"])
        
        # Enable slice labels
        for slice in series.slices():
            slice.setLabelVisible(True)
            slice.setLabel(f"{slice.label()}: {slice.value()}")
        
        chart.addSeries(series)
        chart.legend().setAlignment(Qt.AlignRight)
        
        self.customer_chart_view.setChart(chart)
        
        # Update table with segmentation details
        all_customers = []
        for segment_name, segment_data in segmentation.items():
            for customer in segment_data["customers"]:
                customer["segment"] = segment_name
                all_customers.append(customer)
        
        headers = ["Customer", "Segment", "Total Spent", "Orders", "Avg Order", "Days Since Last Order"]
        self.customer_table.setColumnCount(len(headers))
        self.customer_table.setHorizontalHeaderLabels(headers)
        self.customer_table.setRowCount(len(all_customers))
        
        for row, customer in enumerate(all_customers):
            self.customer_table.setItem(row, 0, QTableWidgetItem(customer.get("name", "")))
            self.customer_table.setItem(row, 1, QTableWidgetItem(customer.get("segment", "")))
            self.customer_table.setItem(row, 2, QTableWidgetItem(f"PKR{customer.get('total_spent', 0):,.2f}"))
            self.customer_table.setItem(row, 3, QTableWidgetItem(str(customer.get("order_count", 0))))
            self.customer_table.setItem(row, 4, QTableWidgetItem(f"PKR{customer.get('avg_order_value', 0):,.2f}"))
            self.customer_table.setItem(row, 5, QTableWidgetItem(f"{customer.get('days_since_last_order', 0):.0f}"))
        
        self.customer_table.resizeColumnsToContents()

    def generate_product_analysis(self):
        """Generate product performance analysis using MongoDB"""
        try:
            # Validate prerequisites
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
            
            self.show_progress()
            
            self.current_thread = ReportGenerationThread(
                self.get_product_performance_analysis
            )
            self.current_thread.report_ready.connect(self.display_product_analysis)
            self.current_thread.progress_updated.connect(self.update_progress)
            self.current_thread.error_occurred.connect(self.handle_error)
            self.current_thread.start()
            
        except Exception as e:
            self.hide_progress()
            QMessageBox.critical(self, "Error", f"Failed to generate product analysis: {str(e)}")

    def get_product_performance_analysis(self):
        """Get product performance analysis using MongoDB"""
        try:
            # Check if mongo_adapter is available
            if not self.mongo_adapter:
                print("MongoDB adapter not available for product analysis")
                return []
            
            # Get data from MongoDB
            entries = self.mongo_adapter.get_entries()
            products = self.mongo_adapter.get_products()
            
            # Validate data
            if not entries or not products:
                print("Insufficient data for product analysis")
                return []
            
            # Create product lookup
            product_lookup = {}
            for product in products:
                product_lookup[str(product.get('id', ''))] = product
            
            # Calculate product metrics
            product_metrics = {}
            for entry in entries:
                if entry.get('is_credit'):
                    product_id = str(entry.get('product_id', ''))
                    quantity = float(entry.get('quantity', 0))
                    unit_price = float(entry.get('unit_price', 0))
                    revenue = quantity * unit_price
                    customer_id = str(entry.get('customer_id', ''))
                    
                    if product_id not in product_metrics:
                        product_info = product_lookup.get(product_id, {})
                        product_metrics[product_id] = {
                            'name': product_info.get('name', 'Unknown'),
                            'description': product_info.get('description', ''),
                            'batch_number': product_info.get('batch_number', ''),
                            'unit_price': product_info.get('unit_price', 0),
                            'total_quantity_sold': 0,
                            'total_revenue': 0,
                            'unique_customers': set(),
                            'order_count': 0
                        }
                    
                    product_metrics[product_id]['total_quantity_sold'] += quantity
                    product_metrics[product_id]['total_revenue'] += revenue
                    product_metrics[product_id]['unique_customers'].add(customer_id)
                    product_metrics[product_id]['order_count'] += 1
            
            # Calculate derived metrics
            result = []
            for product_id, metrics in product_metrics.items():
                unique_customers = len(metrics['unique_customers'])
                metrics['unique_customers'] = unique_customers
                metrics['avg_order_size'] = metrics['total_quantity_sold'] / metrics['order_count'] if metrics['order_count'] > 0 else 0
                metrics['revenue_per_customer'] = metrics['total_revenue'] / unique_customers if unique_customers > 0 else 0
                
                result.append(metrics)
            
            # Sort by revenue
            result.sort(key=lambda x: x['total_revenue'], reverse=True)
            
            return result
            
        except Exception as e:
            print(f"Error getting product performance: {e}")
            return []

    def display_product_analysis(self, products):
        """Display product analysis results"""
        self.hide_progress()
        
        # Setup table
        headers = ["Product", "Batch", "Qty Sold", "Revenue", "Customers", "Avg Order", "Revenue/Customer"]
        self.product_table.setColumnCount(len(headers))
        self.product_table.setHorizontalHeaderLabels(headers)
        self.product_table.setRowCount(len(products))
        
        # Populate table
        for row, product in enumerate(products):
            self.product_table.setItem(row, 0, QTableWidgetItem(product.get("name", "")))
            self.product_table.setItem(row, 1, QTableWidgetItem(product.get("batch_number", "")))
            self.product_table.setItem(row, 2, QTableWidgetItem(str(product.get("total_quantity_sold", 0))))
            self.product_table.setItem(row, 3, QTableWidgetItem(f"PKR{product.get('total_revenue', 0):,.2f}"))
            self.product_table.setItem(row, 4, QTableWidgetItem(str(product.get("unique_customers", 0))))
            self.product_table.setItem(row, 5, QTableWidgetItem(f"{product.get('avg_order_size', 0):.1f}"))
            self.product_table.setItem(row, 6, QTableWidgetItem(f"PKR{product.get('revenue_per_customer', 0):,.2f}"))
        
        self.product_table.resizeColumnsToContents()
        
        # Create chart
        self.create_product_revenue_chart(products)
        
        # Store data for export
        self.current_product_data = products
    
    def create_product_revenue_chart(self, products):
        """Create product revenue chart"""
        chart = QChart()
        chart.setTitle("Product Revenue Performance")
        
        series = QBarSeries()
        revenue_set = QBarSet("Revenue")
        quantity_set = QBarSet("Quantity Sold")
        
        categories = []
        max_products = 15  # Limit for readability
        
        for product in products[:max_products]:
            revenue_set.append(product.get("total_revenue", 0))
            quantity_set.append(product.get("total_quantity_sold", 0) * 100)  # Scale for visibility
            categories.append(product.get("name", "")[:12])
        
        series.append(revenue_set)
        series.append(quantity_set)
        chart.addSeries(series)
        
        # Axes
        axis_x = QCategoryAxis()
        axis_x.append(categories)
        chart.addAxis(axis_x, Qt.AlignBottom)
        series.attachAxis(axis_x)
        
        axis_y = QValueAxis()
        chart.addAxis(axis_y, Qt.AlignLeft)
        series.attachAxis(axis_y)
        
        self.product_chart_view.setChart(chart)

    def generate_sales_trends(self):
        """Generate sales trends analysis using MongoDB"""
        self.show_progress()
        
        period_text = self.trend_period_combo.currentText()
        months = int(period_text.split()[0])
        
        self.current_thread = ReportGenerationThread(
            self.get_monthly_sales_trend, months
        )
        self.current_thread.report_ready.connect(self.display_sales_trends)
        self.current_thread.progress_updated.connect(self.update_progress)
        self.current_thread.error_occurred.connect(self.handle_error)
        self.current_thread.start()
    
    def get_monthly_sales_trend(self, months=6):
        """Get monthly sales trend using MongoDB"""
        try:
            # Check if mongo_adapter is available
            if not self.mongo_adapter:
                print("MongoDB adapter not available for sales trends")
                return []
            
            # Get entries from MongoDB
            entries = self.mongo_adapter.get_entries()
            
            # Validate data
            if not entries:
                print("No entries available for sales trends")
                return []
            
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            # Group by month
            monthly_data = {}
            for entry in entries:
                if entry.get('is_credit'):
                    entry_date_str = entry.get('date', '')
                    try:
                        entry_date = datetime.strptime(entry_date_str, '%Y-%m-%d')
                        if start_date <= entry_date <= end_date:
                            month_key = entry_date.strftime('%Y-%m')
                            quantity = float(entry.get('quantity', 0))
                            unit_price = float(entry.get('unit_price', 0))
                            revenue = quantity * unit_price
                            customer_id = str(entry.get('customer_id', ''))
                            
                            if month_key not in monthly_data:
                                monthly_data[month_key] = {
                                    'month': month_key,
                                    'total_revenue': 0,
                                    'total_quantity': 0,
                                    'customers': set(),
                                    'order_count': 0
                                }
                            
                            monthly_data[month_key]['total_revenue'] += revenue
                            monthly_data[month_key]['total_quantity'] += quantity
                            monthly_data[month_key]['customers'].add(customer_id)
                            monthly_data[month_key]['order_count'] += 1
                    except:
                        continue
            
            # Convert to list and calculate derived metrics
            result = []
            for month_key, data in sorted(monthly_data.items()):
                data['customer_count'] = len(data['customers'])
                data['avg_order_value'] = data['total_revenue'] / data['order_count'] if data['order_count'] > 0 else 0
                del data['customers']  # Remove set for JSON serialization
                result.append(data)
            
            return result
            
        except Exception as e:
            print(f"Error getting sales trends: {e}")
            return []

    def display_sales_trends(self, trends):
        """Display sales trends results"""
        self.hide_progress()
        
        # Create line chart
        chart = QChart()
        chart.setTitle("Monthly Sales Trends")
        
        revenue_series = QLineSeries()
        revenue_series.setName("Revenue")
        
        quantity_series = QLineSeries()
        quantity_series.setName("Quantity")
        
        for i, trend in enumerate(trends):
            revenue_series.append(i, trend.get("total_revenue", 0))
            quantity_series.append(i, trend.get("total_quantity", 0) * 10)  # Scale for visibility
        
        chart.addSeries(revenue_series)
        chart.addSeries(quantity_series)
        
        self.trends_chart_view.setChart(chart)
        
        # Update summary table
        headers = ["Month", "Revenue", "Quantity", "Customers", "Avg Order Value"]
        self.trends_table.setColumnCount(len(headers))
        self.trends_table.setHorizontalHeaderLabels(headers)
        self.trends_table.setRowCount(len(trends))
        
        for row, trend in enumerate(trends):
            self.trends_table.setItem(row, 0, QTableWidgetItem(trend.get("month", "")))
            self.trends_table.setItem(row, 1, QTableWidgetItem(f"PKR{trend.get('total_revenue', 0):,.2f}"))
            self.trends_table.setItem(row, 2, QTableWidgetItem(str(trend.get("total_quantity", 0))))
            self.trends_table.setItem(row, 3, QTableWidgetItem(str(trend.get("customer_count", 0))))
            self.trends_table.setItem(row, 4, QTableWidgetItem(f"PKR{trend.get('avg_order_value', 0):,.2f}"))
        
        self.trends_table.resizeColumnsToContents()
    
    def generate_credit_debit_analysis(self):
        """Generate credit/debit analysis using MongoDB"""
        try:
            # Validate prerequisites
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
            
            self.show_progress()
            
            self.current_thread = ReportGenerationThread(
                self.get_credit_debit_analysis
            )
            self.current_thread.report_ready.connect(self.display_credit_debit_analysis)
            self.current_thread.progress_updated.connect(self.update_progress)
            self.current_thread.error_occurred.connect(self.handle_error)
            self.current_thread.start()
            
        except Exception as e:
            self.hide_progress()
            QMessageBox.critical(self, "Error", f"Failed to generate credit/debit analysis: {str(e)}")

    def get_credit_debit_analysis(self):
        """Get credit/debit analysis using MongoDB"""
        try:
            # Check if mongo_adapter is available
            if not self.mongo_adapter:
                print("MongoDB adapter not available for credit/debit analysis")
                return {'customer_balances': [], 'summary': []}
            
            # Get data from MongoDB
            entries = self.mongo_adapter.get_entries()
            customers = self.mongo_adapter.get_customers()
            
            # Validate data
            if not entries or not customers:
                print("Insufficient data for credit/debit analysis")
                return {'customer_balances': [], 'summary': []}
            
            # Create customer lookup
            customer_lookup = {}
            for customer in customers:
                customer_lookup[str(customer.get('id', ''))] = customer
        
            # Calculate customer balances
            customer_balances = {}
            summary = {'total_credit': 0, 'total_debit': 0}
            
            for entry in entries:
                customer_id = str(entry.get('customer_id', ''))
                quantity = float(entry.get('quantity', 0))
                unit_price = float(entry.get('unit_price', 0))
                amount = quantity * unit_price
                is_credit = entry.get('is_credit', False)
                
                if customer_id not in customer_balances:
                    customer_info = customer_lookup.get(customer_id, {})
                    customer_balances[customer_id] = {
                        'customer_name': customer_info.get('name', 'Unknown'),
                        'credit_total': 0,
                        'debit_total': 0,
                        'raw_balance': 0,
                        'balance': 0
                    }
                
                if is_credit:
                    customer_balances[customer_id]['credit_total'] += amount
                    customer_balances[customer_id]['raw_balance'] += amount
                    summary['total_credit'] += amount
                else:
                    customer_balances[customer_id]['debit_total'] += amount
                    customer_balances[customer_id]['raw_balance'] -= amount
                    summary['total_debit'] += amount
        
            # Add status for each customer and handle negative balances
            for customer_id, balance_data in customer_balances.items():
                raw_balance = balance_data['raw_balance']
                display_balance = max(0, raw_balance)  # Show 0 if negative
                balance_data['balance'] = display_balance
                
                if raw_balance > 1000:
                    balance_data['status'] = 'High Credit'
                elif raw_balance > 0:
                    balance_data['status'] = 'Credit Balance'
                elif raw_balance < 0:
                    balance_data['status'] = 'No Balance'
                else:
                    balance_data['status'] = 'Balanced'
            
            # Convert to list format
            customer_balances_list = list(customer_balances.values())
            customer_balances_list.sort(key=lambda x: x['raw_balance'], reverse=True)
            
            # Create summary in expected format
            summary_list = [
                {'_id': True, 'total_amount': summary['total_credit']},
                {'_id': False, 'total_amount': summary['total_debit']}
            ]
            
            return {
                'customer_balances': customer_balances_list,
                'summary': summary_list
            }
            
        except Exception as e:
            print(f"Error getting credit/debit analysis: {e}")
            return {'customer_balances': [], 'summary': []}

    def display_credit_debit_analysis(self, analysis):
        """Display credit/debit analysis results"""
        self.hide_progress()
        
        customer_balances = analysis.get("customer_balances", [])
        summary = analysis.get("summary", [])
        
        # Update summary cards
        total_credit = sum(s["total_amount"] for s in summary if s["_id"] == True)
        total_debit = sum(s["total_amount"] for s in summary if s["_id"] == False)
        net_outstanding = max(0, total_credit - total_debit)  # Show 0 if negative
        active_customers = len(customer_balances)
        
        self.revenue_card.value_label.setText(f"PKR{total_credit:,.2f}")
        self.outstanding_card.value_label.setText(f"PKR{net_outstanding:,.2f}")
        self.credit_card.value_label.setText(f"PKR{total_debit:,.2f}")
        self.customers_card.value_label.setText(str(active_customers))
        
        # Setup table
        headers = ["Customer", "Credit Total", "Debit Total", "Balance", "Status"]
        self.financial_table.setColumnCount(len(headers))
        self.financial_table.setHorizontalHeaderLabels(headers)
        self.financial_table.setRowCount(len(customer_balances))
        
        # Populate table
        for row, balance in enumerate(customer_balances):
            self.financial_table.setItem(row, 0, QTableWidgetItem(balance.get("customer_name", "")))
            self.financial_table.setItem(row, 1, QTableWidgetItem(f"PKR{balance.get('credit_total', 0):,.2f}"))
            self.financial_table.setItem(row, 2, QTableWidgetItem(f"PKR{balance.get('debit_total', 0):,.2f}"))
            
            display_balance = balance.get("balance", 0)  # This is already max(0, raw_balance)
            raw_balance = balance.get("raw_balance", display_balance)
            balance_item = QTableWidgetItem(f"PKR{display_balance:,.2f}")
            
            if raw_balance > 0:
                balance_item.setBackground(QColor(200, 255, 200))  # Light green for positive
            else:
                balance_item.setBackground(QColor(245, 245, 245))  # Light gray for zero display
                
            self.financial_table.setItem(row, 3, balance_item)
            self.financial_table.setItem(row, 4, QTableWidgetItem(balance.get("status", "")))
    
        self.financial_table.resizeColumnsToContents()
        
        # Create balance distribution chart
        self.create_balance_distribution_chart(customer_balances)

    def create_balance_distribution_chart(self, balances):
        """Create balance distribution chart"""
        chart = QChart()
        chart.setTitle("Customer Balance Distribution")
        
        series = QPieSeries()
        
        positive_count = sum(1 for b in balances if b.get("raw_balance", 0) > 0)
        no_balance_count = sum(1 for b in balances if b.get("raw_balance", 0) <= 0)
        
        if positive_count > 0:
            series.append("Credit Balance", positive_count)
        if no_balance_count > 0:
            series.append("No Balance", no_balance_count)
        
        chart.addSeries(series)
        self.financial_chart_view.setChart(chart)
    
    def generate_expiry_report(self):
        """Generate expiring products report using MongoDB"""
        self.show_progress()
        
        days = int(self.expiry_days_combo.currentText())
        
        self.current_thread = ReportGenerationThread(
            self.get_expiring_products, days
        )
        self.current_thread.report_ready.connect(self.display_expiry_report)
        self.current_thread.progress_updated.connect(self.update_progress)
        self.current_thread.error_occurred.connect(self.handle_error)
        self.current_thread.start()
    
    def get_expiring_products(self, days=30):
        """Get expiring products using MongoDB"""
        try:
            # Check if mongo_adapter is available
            if not self.mongo_adapter:
                print("MongoDB adapter not available for expiry analysis")
                return []
            
            # Get products and entries from MongoDB
            products = self.mongo_adapter.get_products()
            entries = self.mongo_adapter.get_entries()
            
            # Validate data
            if not products:
                print("No products available for expiry analysis")
                return []
            
            # Calculate stock movement for each product
            product_movement = {}
            for entry in entries:
                product_id = str(entry.get('product_id', ''))
                quantity = float(entry.get('quantity', 0))
                
                if product_id not in product_movement:
                    product_movement[product_id] = 0
                
                if entry.get('is_credit'):
                    product_movement[product_id] += quantity
                else:
                    product_movement[product_id] -= quantity
            
            # Check expiry dates
            today = datetime.now().date()
            warning_date = today + timedelta(days=days)
            
            expiring_products = []
            for product in products:
                expiry_str = product.get('expiry_date', '')
                if expiry_str and expiry_str != 'No expiry':
                    try:
                        expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                        
                        if expiry_date <= warning_date:
                            days_to_expiry = (expiry_date - today).days
                            product_id = str(product.get('id', ''))
                            
                            expiring_products.append({
                                'name': product.get('name', ''),
                                'batch_number': product.get('batch_number', ''),
                                'expiry_date': expiry_str,
                                'days_to_expiry': days_to_expiry,
                                'unit_price': float(product.get('unit_price', 0)),
                                'stock_movement': product_movement.get(product_id, 0)
                            })
                    except:
                        continue
            
            # Sort by days to expiry
            expiring_products.sort(key=lambda x: x['days_to_expiry'])
            
            return expiring_products
            
        except Exception as e:
            print(f"Error getting expiring products: {e}")
            return []

    def display_expiry_report(self, products):
        """Display expiring products report"""
        self.hide_progress()
        
        # Setup table
        headers = ["Product", "Batch Number", "Expiry Date", "Days to Expiry", "Unit Price", "Stock Movement"]
        self.inventory_table.setColumnCount(len(headers))
        self.inventory_table.setHorizontalHeaderLabels(headers)
        self.inventory_table.setRowCount(len(products))
        
        # Populate table
        for row, product in enumerate(products):
            days_to_expiry = product.get("days_to_expiry", 0)
            
            self.inventory_table.setItem(row, 0, QTableWidgetItem(product.get("name", "")))
            self.inventory_table.setItem(row, 1, QTableWidgetItem(product.get("batch_number", "")))
            self.inventory_table.setItem(row, 2, QTableWidgetItem(product.get("expiry_date", "")))
            
            days_item = QTableWidgetItem(f"{days_to_expiry:.0f}")
            if days_to_expiry <= 7:
                days_item.setBackground(QColor(255, 200, 200))  # Red for urgent
            elif days_to_expiry <= 30:
                days_item.setBackground(QColor(255, 255, 200))  # Yellow for warning
            
            self.inventory_table.setItem(row, 3, days_item)
            self.inventory_table.setItem(row, 4, QTableWidgetItem(f"PKR{product.get('unit_price', 0):,.2f}"))
            self.inventory_table.setItem(row, 5, QTableWidgetItem(str(product.get("stock_movement", 0))))
        
        self.inventory_table.resizeColumnsToContents()
    
    def export_product_analysis(self):
        """Export product analysis to CSV (simplified without Excel dependency)"""
        try:
            if not hasattr(self, 'current_product_data') or not self.current_product_data:
                QMessageBox.warning(self, "No Data", "Please generate product analysis first.")
                return
            
            from PyQt5.QtWidgets import QFileDialog
            import csv
            
            filename, _ = QFileDialog.getSaveFileName(
                self, "Export Product Analysis", "product_analysis.csv",
                "CSV Files (*.csv)"
            )
            
            if filename:
                with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                    fieldnames = [
                        'Product', 'Description', 'Batch', 'Unit Price', 'Qty Sold',
                        'Revenue', 'Customers', 'Avg Order Size', 'Revenue/Customer'
                    ]
                    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                    
                    writer.writeheader()
                    for product in self.current_product_data:
                        writer.writerow({
                            'Product': product.get('name', ''),
                            'Description': product.get('description', ''),
                            'Batch': product.get('batch_number', ''),
                            'Unit Price': product.get('unit_price', 0),
                            'Qty Sold': product.get('total_quantity_sold', 0),
                            'Revenue': product.get('total_revenue', 0),
                            'Customers': product.get('unique_customers', 0),
                            'Avg Order Size': product.get('avg_order_size', 0),
                            'Revenue/Customer': product.get('revenue_per_customer', 0)
                        })
                
                QMessageBox.information(self, "Success", f"Data exported to {filename}")
                
        except Exception as e:
            QMessageBox.critical(self, "Export Error", f"Failed to export data: {str(e)}")

    # Utility Methods
    
    def show_progress(self):
        """Show progress bar"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
    
    def hide_progress(self):
        """Hide progress bar"""
        self.progress_bar.setVisible(False)
    
    def update_progress(self, value):
        """Update progress bar"""
        self.progress_bar.setValue(value)
    
    def handle_error(self, error_message):
        """Handle error from background thread"""
        self.hide_progress()
        
        # Show user-friendly error message
        if "MongoDB adapter not available" in error_message:
            QMessageBox.warning(self, "Database Connection", 
                              "Database connection is not available. Please check your MongoDB connection and try again.")
        elif "Insufficient data" in error_message:
            QMessageBox.information(self, "No Data", 
                                   "There is insufficient data to generate this report. Please ensure you have customers, products, and entries in your database.")
        else:
            QMessageBox.critical(self, "Report Generation Error", 
                               f"Failed to generate report:\n\n{error_message}")
    
    def generate_sales_forecast(self):
        """Generate sales forecasting report"""
        QMessageBox.information(
            self, "Coming Soon", 
            "Sales forecasting feature will be available in the next update. "
            "This will use machine learning algorithms to predict future sales trends based on MongoDB data."
        )
    
    def generate_outstanding_report(self):
        """Generate outstanding balances report"""
        self.generate_credit_debit_analysis()  # Reuse the credit/debit analysis
    
    def generate_stock_movement(self):
        """Generate stock movement analysis"""
        QMessageBox.information(
            self, "Coming Soon",
            "Stock movement analysis will show detailed inventory flow patterns and turnover rates using MongoDB aggregation."
        )