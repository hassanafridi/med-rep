from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QDateEdit, QGroupBox, QFormLayout,
    QPushButton, QCheckBox, QTabWidget, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView, QMessageBox
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtChart import (
    QChart, QChartView, QBarSeries, QBarSet, 
    QValueAxis, QBarCategoryAxis, QPieSeries,
    QLineSeries, QScatterSeries, QAreaSeries
)
from PyQt5.QtGui import QPainter, QColor
import sys
import os
from datetime import datetime, timedelta

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter

class AdvancedChartsTab(QWidget):
    def __init__(self):
        super().__init__()
        try:
            self.db = MongoAdapter()
            self.chart_data = None
            self.initUI()
        except Exception as e:
            print(f"Error initializing Advanced Charts tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Advanced Charts tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the advanced charts tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__()
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Advanced Charts tab: {str(e)}")
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Create top controls
        controls_layout = QHBoxLayout()
        
        # Chart selection
        chart_group = QGroupBox("Chart Type")
        chart_layout = QVBoxLayout()
        
        self.chart_type = QComboBox()
        self.chart_type.addItems([
            "Sales Trend",
            "Product Comparison", 
            "Customer Analysis",
            "Credit vs Debit",
            "Monthly Performance",
            "Product Expiry Analysis"
        ])
        self.chart_type.currentIndexChanged.connect(self.updateChartOptions)
        
        chart_layout.addWidget(self.chart_type)
        chart_group.setLayout(chart_layout)
        controls_layout.addWidget(chart_group)
        
        # Time period
        time_group = QGroupBox("Time Period")
        time_layout = QFormLayout()
        
        # Date range
        self.from_date = QDateEdit()
        self.from_date.setDate(QDate.currentDate().addMonths(-6))
        self.from_date.setCalendarPopup(True)
        
        self.to_date = QDateEdit()
        self.to_date.setDate(QDate.currentDate())
        self.to_date.setCalendarPopup(True)
        
        date_layout = QHBoxLayout()
        date_layout.addWidget(QLabel("From:"))
        date_layout.addWidget(self.from_date)
        date_layout.addWidget(QLabel("To:"))
        date_layout.addWidget(self.to_date)
        
        time_layout.addRow(date_layout)
        
        # Preset periods
        periods_layout = QHBoxLayout()
        
        self.this_month_btn = QPushButton("This Month")
        self.this_month_btn.clicked.connect(self.setThisMonth)
        
        self.last_month_btn = QPushButton("Last Month")
        self.last_month_btn.clicked.connect(self.setLastMonth)
        
        self.this_quarter_btn = QPushButton("This Quarter")
        self.this_quarter_btn.clicked.connect(self.setThisQuarter)
        
        self.this_year_btn = QPushButton("This Year")
        self.this_year_btn.clicked.connect(self.setThisYear)
        
        periods_layout.addWidget(self.this_month_btn)
        periods_layout.addWidget(self.last_month_btn)
        periods_layout.addWidget(self.this_quarter_btn)
        periods_layout.addWidget(self.this_year_btn)
        
        time_layout.addRow(periods_layout)
        
        time_group.setLayout(time_layout)
        controls_layout.addWidget(time_group)
        
        # Chart Options (will be dynamically updated)
        self.options_group = QGroupBox("Chart Options")
        self.options_layout = QFormLayout()
        self.options_group.setLayout(self.options_layout)
        controls_layout.addWidget(self.options_group)
        
        main_layout.addLayout(controls_layout)
        
        # Generate button
        generate_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Chart")
        self.generate_btn.clicked.connect(self.generateChart)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        generate_layout.addWidget(self.generate_btn)
        
        main_layout.addLayout(generate_layout)
        
        # Create splitter for chart and data
        splitter = QSplitter(Qt.Vertical)
        
        # Chart view
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        splitter.addWidget(self.chart_view)
        
        # Data table
        self.data_table = QTableWidget()
        self.data_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        splitter.addWidget(self.data_table)
        
        # Set initial splitter sizes (70% chart, 30% data)
        splitter.setSizes([700, 300])
        
        main_layout.addWidget(splitter, stretch=1)
        
        self.setLayout(main_layout)
        
        # Initialize chart options
        self.updateChartOptions()
        
        # Set initial empty chart
        self.showEmptyChart("Select options and click Generate Chart")
    
    def updateChartOptions(self):
        """Update chart options based on selected chart type"""
        # Clear existing options
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        chart_type = self.chart_type.currentText()
        
        if chart_type == "Sales Trend":
            # Add grouping options
            self.group_by = QComboBox()
            self.group_by.addItems(["Daily", "Weekly", "Monthly"])
            self.options_layout.addRow("Group By:", self.group_by)
            
            # Include data type filter
            self.include_credit = QCheckBox("Include Credit")
            self.include_credit.setChecked(True)
            self.options_layout.addRow("", self.include_credit)
            
            self.include_debit = QCheckBox("Include Debit")
            self.include_debit.setChecked(True)
            self.options_layout.addRow("", self.include_debit)
            
        elif chart_type == "Product Comparison":
            # Add product limit option
            self.product_limit = QComboBox()
            self.product_limit.addItems(["Top 5", "Top 10", "All Products"])
            self.options_layout.addRow("Products to Show:", self.product_limit)
            
            # Add chart style option
            self.chart_style = QComboBox()
            self.chart_style.addItems(["Bar Chart", "Pie Chart"])
            self.options_layout.addRow("Chart Style:", self.chart_style)
            
        elif chart_type == "Customer Analysis":
            # Add customer limit option
            self.customer_limit = QComboBox()
            self.customer_limit.addItems(["Top 5", "Top 10", "All Customers"])
            self.options_layout.addRow("Customers to Show:", self.customer_limit)
            
        elif chart_type == "Credit vs Debit":
            # Add time breakdown option
            self.time_breakdown = QComboBox()
            self.time_breakdown.addItems(["Daily", "Weekly", "Monthly"])
            self.options_layout.addRow("Time Breakdown:", self.time_breakdown)
            
        elif chart_type == "Monthly Performance":
            # Add year selection
            self.year_selection = QComboBox()
            current_year = QDate.currentDate().year()
            for year in range(current_year - 5, current_year + 1):
                self.year_selection.addItem(str(year))
            self.year_selection.setCurrentText(str(current_year))
            self.options_layout.addRow("Year:", self.year_selection)
    
    def setThisMonth(self):
        """Set date range to current month"""
        today = QDate.currentDate()
        start_of_month = QDate(today.year(), today.month(), 1)
        
        self.from_date.setDate(start_of_month)
        self.to_date.setDate(today)
    
    def setLastMonth(self):
        """Set date range to last month"""
        today = QDate.currentDate()
        
        if today.month() == 1:  # January
            start_of_last_month = QDate(today.year() - 1, 12, 1)
            end_of_last_month = QDate(today.year() - 1, 12, 31)
        else:
            start_of_last_month = QDate(today.year(), today.month() - 1, 1)
            end_of_last_month = QDate(today.year(), today.month(), 1).addDays(-1)
        
        self.from_date.setDate(start_of_last_month)
        self.to_date.setDate(end_of_last_month)
    
    def setThisQuarter(self):
        """Set date range to current quarter"""
        today = QDate.currentDate()
        month = today.month()
        
        # Calculate quarter start month (1, 4, 7, or 10)
        quarter_start_month = ((month - 1) // 3) * 3 + 1
        
        start_of_quarter = QDate(today.year(), quarter_start_month, 1)
        
        self.from_date.setDate(start_of_quarter)
        self.to_date.setDate(today)
    
    def setThisYear(self):
        """Set date range to current year"""
        today = QDate.currentDate()
        start_of_year = QDate(today.year(), 1, 1)
        
        self.from_date.setDate(start_of_year)
        self.to_date.setDate(today)
    
    def generateChart(self):
        """Generate the selected chart type"""
        try:
            chart_type = self.chart_type.currentText()
            from_date = self.from_date.date().toString("yyyy-MM-dd")
            to_date = self.to_date.date().toString("yyyy-MM-dd")
            
            # Generate appropriate chart based on selection
            if chart_type == "Sales Trend":
                grouping = self.group_by.currentText()
                include_credit = self.include_credit.isChecked()
                include_debit = self.include_debit.isChecked()
                
                self.generateSalesTrendChart(from_date, to_date, grouping, include_credit, include_debit)
                
            elif chart_type == "Product Comparison":
                product_limit = self.product_limit.currentText()
                chart_style = self.chart_style.currentText()
                
                self.generateProductComparisonChart(from_date, to_date, product_limit, chart_style)
                
            elif chart_type == "Customer Analysis":
                customer_limit = self.customer_limit.currentText()
                
                self.generateCustomerAnalysisChart(from_date, to_date, customer_limit)
                
            elif chart_type == "Credit vs Debit":
                time_breakdown = self.time_breakdown.currentText()
                
                self.generateCreditDebitComparisonChart(from_date, to_date, time_breakdown)
                
            elif chart_type == "Monthly Performance":
                year = self.year_selection.currentText()
                
                self.generateMonthlyPerformanceChart(year)
                
            elif chart_type == "Product Expiry Analysis":
                self.generateProductExpiryChart()
                
        except Exception as e:
            QMessageBox.critical(self, "Chart Error", f"Failed to generate chart: {str(e)}")
    
    def generateSalesTrendChart(self, from_date, to_date, grouping, include_credit, include_debit):
        """Generate sales trend chart using MongoDB data"""
        try:
            # Get entries from MongoDB
            entries = self.db.get_entries()
            
            # Filter by date range
            filtered_entries = []
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date:
                    filtered_entries.append(entry)
            
            if not filtered_entries:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Group data by time period
            grouped_data = {}
            
            for entry in filtered_entries:
                entry_date = entry.get('date', '')
                is_credit = entry.get('is_credit', False)
                amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                
                # Determine period key based on grouping
                if grouping == "Daily":
                    period_key = entry_date
                elif grouping == "Weekly":
                    # Simple week grouping by year-week
                    try:
                        date_obj = datetime.strptime(entry_date, '%Y-%m-%d')
                        year_week = f"{date_obj.year}-W{date_obj.isocalendar()[1]:02d}"
                        period_key = year_week
                    except:
                        period_key = entry_date
                else:  # Monthly
                    period_key = entry_date[:7]  # YYYY-MM
                
                if period_key not in grouped_data:
                    grouped_data[period_key] = {'credit': 0, 'debit': 0}
                
                if is_credit:
                    grouped_data[period_key]['credit'] += amount
                else:
                    grouped_data[period_key]['debit'] += amount
            
            # Sort periods
            sorted_periods = sorted(grouped_data.keys())
            
            # Create chart
            chart = QChart()
            chart.setTitle(f"Sales Trend ({grouping} Breakdown)")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create series
            series = QBarSeries()
            
            # Prepare data
            credit_data = []
            debit_data = []
            
            for period in sorted_periods:
                credit_data.append(grouped_data[period]['credit'])
                debit_data.append(grouped_data[period]['debit'])
            
            # Add bar sets based on options
            if include_credit:
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#4CAF50"))
                credit_set.append(credit_data)
                series.append(credit_set)
            
            if include_debit:
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#F44336"))
                debit_set.append(debit_data)
                series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(sorted_periods)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (Rs.)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Period", "Credit", "Debit", "Net"]
            table_data = []
            for period in sorted_periods:
                credit = grouped_data[period]['credit']
                debit = grouped_data[period]['debit']
                table_data.append([
                    period,
                    f"Rs. {credit:.2f}",
                    f"Rs. {debit:.2f}",
                    f"Rs. {credit - debit:.2f}"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating sales trend chart: {str(e)}")
            print(f"Sales trend chart error: {e}")
            import traceback
            traceback.print_exc()
    
    def generateProductComparisonChart(self, from_date, to_date, product_limit, chart_style):
        """Generate product comparison chart using MongoDB data"""
        try:
            # Get data from MongoDB
            entries = self.db.get_entries()
            products = self.db.get_products()
            
            # Create product lookup
            product_lookup = {}
            for product in products:
                product_lookup[str(product.get('id', ''))] = product.get('name', 'Unknown')
            
            # Calculate product sales
            product_sales = {}
            
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date and entry.get('is_credit'):
                    product_id = str(entry.get('product_id', ''))
                    product_name = product_lookup.get(product_id, 'Unknown Product')
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    
                    product_sales[product_name] = product_sales.get(product_name, 0) + amount
            
            if not product_sales:
                self.showEmptyChart("No product sales data available for the selected period")
                return
            
            # Apply product limit
            sorted_products = sorted(product_sales.items(), key=lambda x: x[1], reverse=True)
            
            if product_limit == "Top 5":
                sorted_products = sorted_products[:5]
            elif product_limit == "Top 10":
                sorted_products = sorted_products[:10]
            
            # Create chart
            chart = QChart()
            chart.setTitle("Product Sales Comparison")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            if chart_style == "Pie Chart":
                # Create pie series
                series = QPieSeries()
                
                total_amount = sum(amount for _, amount in sorted_products)
                
                for product, amount in sorted_products:
                    slice_obj = series.append(product, amount)
                    percentage = (amount / total_amount) * 100
                    slice_obj.setLabel(f"{product}: {percentage:.1f}%")
                    slice_obj.setLabelVisible(True)
                
                chart.addSeries(series)
                
            else:  # Bar Chart
                # Create bar series
                series = QBarSeries()
                
                # Prepare data
                products_list = [product for product, _ in sorted_products]
                amounts = [amount for _, amount in sorted_products]
                
                # Create bar set
                bar_set = QBarSet("Sales")
                bar_set.setColor(QColor("#2196F3"))
                bar_set.append(amounts)
                
                series.append(bar_set)
                chart.addSeries(series)
                
                # Create axes
                axisX = QBarCategoryAxis()
                axisX.append(products_list)
                chart.addAxis(axisX, Qt.AlignBottom)
                series.attachAxis(axisX)
                
                axisY = QValueAxis()
                axisY.setTitleText("Sales Amount (Rs.)")
                chart.addAxis(axisY, Qt.AlignLeft)
                series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            total_sales = sum(amount for _, amount in sorted_products)
            headers = ["Product", "Sales Amount", "Percentage"]
            table_data = []
            for product, amount in sorted_products:
                percentage = (amount / total_sales * 100) if total_sales > 0 else 0
                table_data.append([
                    product,
                    f"Rs. {amount:.2f}",
                    f"{percentage:.1f}%"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating product comparison chart: {str(e)}")
            print(f"Product comparison chart error: {e}")
            import traceback
            traceback.print_exc()
    
    def generateCustomerAnalysisChart(self, from_date, to_date, customer_limit):
        """Generate customer analysis chart using MongoDB data"""
        try:
            # Get data from MongoDB
            entries = self.db.get_entries()
            customers = self.db.get_customers()
            
            # Create customer lookup
            customer_lookup = {}
            for customer in customers:
                customer_lookup[str(customer.get('id', ''))] = customer.get('name', 'Unknown')
            
            # Calculate customer data
            customer_data = {}
            
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date and entry.get('is_credit'):
                    customer_id = str(entry.get('customer_id', ''))
                    customer_name = customer_lookup.get(customer_id, 'Unknown Customer')
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    
                    if customer_name not in customer_data:
                        customer_data[customer_name] = {'total': 0, 'count': 0}
                    
                    customer_data[customer_name]['total'] += amount
                    customer_data[customer_name]['count'] += 1
            
            if not customer_data:
                self.showEmptyChart("No customer data available for the selected period")
                return
            
            # Apply customer limit and sort
            sorted_customers = sorted(customer_data.items(), key=lambda x: x[1]['total'], reverse=True)
            
            if customer_limit == "Top 5":
                sorted_customers = sorted_customers[:5]
            elif customer_limit == "Top 10":
                sorted_customers = sorted_customers[:10]
            
            # Create chart
            chart = QChart()
            chart.setTitle("Customer Analysis")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Prepare data
            customers_list = [customer for customer, _ in sorted_customers]
            amounts = [data['total'] for _, data in sorted_customers]
            
            # Create bar set
            bar_set = QBarSet("Sales")
            bar_set.setColor(QColor("#FF9800"))
            bar_set.append(amounts)
            
            series.append(bar_set)
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(customers_list)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Sales Amount (Rs.)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Customer", "Sales Amount", "Transaction Count", "Average per Transaction"]
            table_data = []
            for customer, data in sorted_customers:
                avg_per_transaction = data['total'] / data['count'] if data['count'] > 0 else 0
                table_data.append([
                    customer,
                    f"Rs. {data['total']:.2f}",
                    str(data['count']),
                    f"Rs. {avg_per_transaction:.2f}"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating customer analysis chart: {str(e)}")
            print(f"Customer analysis chart error: {e}")
            import traceback
            traceback.print_exc()

    def generateCreditDebitComparisonChart(self, from_date, to_date, time_breakdown):
        """Generate credit vs debit comparison chart using MongoDB data"""
        try:
            # Get entries from MongoDB
            entries = self.db.get_entries()
            
            # Filter and group data
            grouped_data = {}
            
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date:
                    is_credit = entry.get('is_credit', False)
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    
                    # Determine period key
                    if time_breakdown == "Daily":
                        period_key = entry_date
                    elif time_breakdown == "Weekly":
                        try:
                            date_obj = datetime.strptime(entry_date, '%Y-%m-%d')
                            year_week = f"{date_obj.year}-W{date_obj.isocalendar()[1]:02d}"
                            period_key = year_week
                        except:
                            period_key = entry_date
                    else:  # Monthly
                        period_key = entry_date[:7]  # YYYY-MM
                    
                    if period_key not in grouped_data:
                        grouped_data[period_key] = {'credit': 0, 'debit': 0}
                    
                    if is_credit:
                        grouped_data[period_key]['credit'] += amount
                    else:
                        grouped_data[period_key]['debit'] += amount
            
            if not grouped_data:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Sort periods
            sorted_periods = sorted(grouped_data.keys())
            
            # Create chart
            chart = QChart()
            chart.setTitle(f"Credit vs Debit ({time_breakdown})")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create series
            series = QBarSeries()
            
            # Prepare data
            credit_data = []
            debit_data = []
            
            for period in sorted_periods:
                credit_data.append(grouped_data[period]['credit'])
                debit_data.append(grouped_data[period]['debit'])
            
            # Create bar sets
            credit_set = QBarSet("Credit")
            credit_set.setColor(QColor("#4CAF50"))
            credit_set.append(credit_data)
            
            debit_set = QBarSet("Debit")
            debit_set.setColor(QColor("#F44336"))
            debit_set.append(debit_data)
            
            series.append(credit_set)
            series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(sorted_periods)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (Rs.)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Period", "Credit", "Debit", "Net"]
            table_data = []
            for period in sorted_periods:
                credit = grouped_data[period]['credit']
                debit = grouped_data[period]['debit']
                table_data.append([
                    period,
                    f"Rs. {credit:.2f}",
                    f"Rs. {debit:.2f}",
                    f"Rs. {credit - debit:.2f}"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating credit vs debit chart: {str(e)}")
            print(f"Credit vs debit chart error: {e}")
            import traceback
            traceback.print_exc()
    
    def generateMonthlyPerformanceChart(self, year):
        """Generate monthly performance chart using MongoDB data"""
        try:
            # Get entries from MongoDB
            entries = self.db.get_entries()
            
            # Initialize data for all 12 months
            monthly_data = {}
            month_names = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
            
            for i in range(1, 13):
                month_key = f"{year}-{i:02d}"
                monthly_data[month_key] = {'credit': 0, 'debit': 0}
            
            # Process entries
            for entry in entries:
                entry_date = entry.get('date', '')
                if entry_date.startswith(year):
                    month_key = entry_date[:7]  # YYYY-MM
                    if month_key in monthly_data:
                        is_credit = entry.get('is_credit', False)
                        amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                        
                        if is_credit:
                            monthly_data[month_key]['credit'] += amount
                        else:
                            monthly_data[month_key]['debit'] += amount
            
            # Create chart
            chart = QChart()
            chart.setTitle(f"Monthly Performance - {year}")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create series
            series = QBarSeries()
            
            # Prepare data
            credit_data = []
            debit_data = []
            
            for i in range(1, 13):
                month_key = f"{year}-{i:02d}"
                credit_data.append(monthly_data[month_key]['credit'])
                debit_data.append(monthly_data[month_key]['debit'])
            
            # Create bar sets
            credit_set = QBarSet("Credit")
            credit_set.setColor(QColor("#4CAF50"))
            credit_set.append(credit_data)
            
            debit_set = QBarSet("Debit")
            debit_set.setColor(QColor("#F44336"))
            debit_set.append(debit_data)
            
            series.append(credit_set)
            series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(month_names)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (Rs.)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Month", "Credit", "Debit", "Net"]
            table_data = []
            for i, month_name in enumerate(month_names):
                month_key = f"{year}-{i+1:02d}"
                credit = monthly_data[month_key]['credit']
                debit = monthly_data[month_key]['debit']
                table_data.append([
                    month_name,
                    f"Rs. {credit:.2f}",
                    f"Rs. {debit:.2f}",
                    f"Rs. {credit - debit:.2f}"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating monthly performance chart: {str(e)}")
            print(f"Monthly performance chart error: {e}")
            import traceback
            traceback.print_exc()

    def generateProductExpiryChart(self):
        """Generate product expiry analysis chart using MongoDB data"""
        try:
            # Get products from MongoDB
            products = self.db.get_products()
            entries = self.db.get_entries()
            
            # Get products with sales
            products_with_sales = set()
            for entry in entries:
                if entry.get('is_credit'):
                    products_with_sales.add(str(entry.get('product_id', '')))
            
            # Analyze expiry status
            today = datetime.now().date()
            warning_date = today + timedelta(days=30)
            
            expiry_data = {'Active': 0, 'Expiring Soon': 0, 'Expired': 0, 'No Expiry Date': 0}
            
            for product in products:
                product_id = str(product.get('id', ''))
                if product_id in products_with_sales:
                    expiry_str = product.get('expiry_date', '')
                    
                    if not expiry_str or expiry_str == 'No expiry':
                        expiry_data['No Expiry Date'] += 1
                    else:
                        try:
                            expiry_date = datetime.strptime(expiry_str, '%Y-%m-%d').date()
                            
                            if expiry_date < today:
                                expiry_data['Expired'] += 1
                            elif expiry_date <= warning_date:
                                expiry_data['Expiring Soon'] += 1
                            else:
                                expiry_data['Active'] += 1
                        except:
                            expiry_data['No Expiry Date'] += 1
            
            if sum(expiry_data.values()) == 0:
                self.showEmptyChart("No product expiry data available")
                return
            
            # Create pie chart
            chart = QChart()
            chart.setTitle("Product Expiry Analysis")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            series = QPieSeries()
            
            colors = {
                'Active': QColor("#4CAF50"),
                'Expiring Soon': QColor("#FF9800"),
                'Expired': QColor("#F44336"),
                'No Expiry Date': QColor("#9E9E9E")
            }
            
            total_products = sum(expiry_data.values())
            
            for status, count in expiry_data.items():
                if count > 0:
                    percentage = (count / total_products) * 100
                    slice_obj = series.append(f"{status} ({count})", count)
                    slice_obj.setLabel(f"{status}: {percentage:.1f}%")
                    slice_obj.setLabelVisible(True)
                    slice_obj.setColor(colors[status])
            
            chart.addSeries(series)
            chart.legend().setAlignment(Qt.AlignRight)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Status", "Count", "Percentage"]
            table_data = []
            for status, count in expiry_data.items():
                if count > 0:
                    percentage = (count / total_products) * 100
                    table_data.append([
                        status,
                        str(count),
                        f"{percentage:.1f}%"
                    ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating product expiry chart: {str(e)}")
            print(f"Product expiry chart error: {e}")
            import traceback
            traceback.print_exc()

    def updateDataTable(self, headers, data):
        """Update the data table with chart data"""
        self.data_table.clear()
        self.data_table.setRowCount(0)
        self.data_table.setColumnCount(len(headers))
        self.data_table.setHorizontalHeaderLabels(headers)
        
        for row, row_data in enumerate(data):
            self.data_table.insertRow(row)
            for col, col_data in enumerate(row_data):
                self.data_table.setItem(row, col, QTableWidgetItem(str(col_data)))
    
    def showEmptyChart(self, message):
        """Show an empty chart with message"""
        chart = QChart()
        chart.setTitle(message)
        self.chart_view.setChart(chart)
        
        # Clear data table
        self.data_table.clear()
        self.data_table.setRowCount(0)
        self.data_table.setColumnCount(0)