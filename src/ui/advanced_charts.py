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
from database.db import Database

class AdvancedChartsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.chart_data = None
        self.initUI()
        
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
            "Monthly Performance"
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
                
        except Exception as e:
            QMessageBox.critical(self, "Chart Error", f"Failed to generate chart: {str(e)}")
    
    def generateSalesTrendChart(self, from_date, to_date, grouping, include_credit, include_debit):
        """Generate sales trend chart"""
        try:
            self.db.connect()
            
            # Determine SQL date grouping
            if grouping == "Daily":
                date_sql = "date(e.date)"
                date_format = "date"
            elif grouping == "Weekly":
                date_sql = "strftime('%Y-W%W', e.date)"
                date_format = "week"
            else:  # Monthly
                date_sql = "strftime('%Y-%m', e.date)"
                date_format = "month"
            
            # Build query
            query = f"""
                SELECT 
                    {date_sql} as period,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as credit,
                    SUM(CASE WHEN e.is_credit = 0 THEN e.quantity * e.unit_price ELSE 0 END) as debit
                FROM entries e
                WHERE e.date BETWEEN ? AND ?
                GROUP BY period
                ORDER BY period
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle(f"Sales Trend ({grouping} Breakdown)")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create series
            series = QBarSeries()
            
            # Prepare data
            periods = []
            credit_data = []
            debit_data = []
            
            for period, credit, debit in data:
                periods.append(period)
                credit_data.append(credit)
                debit_data.append(debit)
            
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
            axisX.append(periods)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (Rs. )")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Period", "Credit", "Debit", "Net"]
            table_data = []
            for period, credit, debit in data:
                table_data.append([
                    period,
                    f"Rs. {credit:.2f}",
                    f"Rs. {debit:.2f}",
                    f"Rs. {credit - debit:.2f}"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating sales trend chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateProductComparisonChart(self, from_date, to_date, product_limit, chart_style):
        """Generate product comparison chart"""
        try:
            self.db.connect()
            
            # Determine product limit
            if product_limit == "Top 5":
                limit_clause = "LIMIT 5"
            elif product_limit == "Top 10":
                limit_clause = "LIMIT 10"
            else:
                limit_clause = ""
            
            # Query data
            query = f"""
                SELECT 
                    p.name,
                    SUM(e.quantity * e.unit_price) as total
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.date BETWEEN ? AND ? AND e.is_credit = 1
                GROUP BY p.name
                ORDER BY total DESC
                {limit_clause}
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle("Product Sales Comparison")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            if chart_style == "Pie Chart":
                # Create pie series
                series = QPieSeries()
                
                total_amount = sum(total for _, total in data)
                
                for product, total in data:
                    slice = series.append(product, total)
                    percentage = (total / total_amount) * 100
                    slice.setLabel(f"{product}: {percentage:.1f}%")
                    slice.setLabelVisible(True)
                
                chart.addSeries(series)
                
            else:  # Bar Chart
                # Create bar series
                series = QBarSeries()
                
                # Prepare data
                products = []
                amounts = []
                
                for product, amount in data:
                    products.append(product)
                    amounts.append(amount)
                
                # Create bar set
                bar_set = QBarSet("Sales")
                bar_set.setColor(QColor("#2196F3"))
                bar_set.append(amounts)
                
                series.append(bar_set)
                chart.addSeries(series)
                
                # Create axes
                axisX = QBarCategoryAxis()
                axisX.append(products)
                chart.addAxis(axisX, Qt.AlignBottom)
                series.attachAxis(axisX)
                
                axisY = QValueAxis()
                axisY.setTitleText("Sales Amount (Rs. )")
                chart.addAxis(axisY, Qt.AlignLeft)
                series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            total_sales = sum(total for _, total in data)
            headers = ["Product", "Sales Amount", "Percentage"]
            table_data = []
            for product, total in data:
                percentage = (total / total_sales * 100) if total_sales > 0 else 0
                table_data.append([
                    product,
                    f"Rs. {total:.2f}",
                    f"{percentage:.1f}%"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating product comparison chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateCustomerAnalysisChart(self, from_date, to_date, customer_limit):
        """Generate customer analysis chart"""
        try:
            self.db.connect()
            
            # Determine customer limit
            if customer_limit == "Top 5":
                limit_clause = "LIMIT 5"
            elif customer_limit == "Top 10":
                limit_clause = "LIMIT 10"
            else:
                limit_clause = ""
            
            # Query data
            query = f"""
                SELECT 
                    c.name,
                    SUM(e.quantity * e.unit_price) as total,
                    COUNT(e.id) as transaction_count
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                WHERE e.date BETWEEN ? AND ? AND e.is_credit = 1
                GROUP BY c.name
                ORDER BY total DESC
                {limit_clause}
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No customer data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle("Customer Analysis")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Prepare data
            customers = []
            amounts = []
            
            for customer, amount, _ in data:
                customers.append(customer)
                amounts.append(amount)
            
            # Create bar set
            bar_set = QBarSet("Sales")
            bar_set.setColor(QColor("#FF9800"))
            bar_set.append(amounts)
            
            series.append(bar_set)
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(customers)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Sales Amount (Rs. )")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Customer", "Sales Amount", "Transaction Count", "Average per Transaction"]
            table_data = []
            for customer, total, count in data:
                avg_per_transaction = total / count if count > 0 else 0
                table_data.append([
                    customer,
                    f"Rs. {total:.2f}",
                    str(count),
                    f"Rs. {avg_per_transaction:.2f}"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating customer analysis chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateCreditDebitComparisonChart(self, from_date, to_date, time_breakdown):
        """Generate credit vs debit comparison chart"""
        try:
            self.db.connect()
            
            # Determine SQL date grouping
            if time_breakdown == "Daily":
                date_sql = "date(e.date)"
            elif time_breakdown == "Weekly":
                date_sql = "strftime('%Y-W%W', e.date)"
            else:  # Monthly
                date_sql = "strftime('%Y-%m', e.date)"
            
            # Build query
            query = f"""
                SELECT 
                    {date_sql} as period,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as credit,
                    SUM(CASE WHEN e.is_credit = 0 THEN e.quantity * e.unit_price ELSE 0 END) as debit
                FROM entries e
                WHERE e.date BETWEEN ? AND ?
                GROUP BY period
                ORDER BY period
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle(f"Credit vs Debit ({time_breakdown})")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create series
            series = QBarSeries()
            
            # Prepare data
            periods = []
            credit_data = []
            debit_data = []
            
            for period, credit, debit in data:
                periods.append(period)
                credit_data.append(credit)
                debit_data.append(debit)
            
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
            axisX.append(periods)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (Rs. )")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Period", "Credit", "Debit", "Net"]
            table_data = []
            for period, credit, debit in data:
                table_data.append([
                    period,
                    f"Rs. {credit:.2f}",
                    f"Rs. {debit:.2f}",
                    f"Rs. {credit - debit:.2f}"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating credit vs debit chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateMonthlyPerformanceChart(self, year):
        """Generate monthly performance chart for a specific year"""
        try:
            self.db.connect()
            
            # Query data for the specified year
            query = """
                SELECT 
                    strftime('%m', e.date) as month,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as credit,
                    SUM(CASE WHEN e.is_credit = 0 THEN e.quantity * e.unit_price ELSE 0 END) as debit
                FROM entries e
                WHERE strftime('%Y', e.date) = ?
                GROUP BY month
                ORDER BY month
            """
            
            self.db.cursor.execute(query, (year,))
            data = self.db.cursor.fetchall()
            
            # Create chart
            chart = QChart()
            chart.setTitle(f"Monthly Performance - {year}")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create series
            series = QBarSeries()
            
            # Month names
            month_names = [
                "Jan", "Feb", "Mar", "Apr", "May", "Jun",
                "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"
            ]
            
            # Initialize data for all 12 months
            credit_data = [0] * 12
            debit_data = [0] * 12
            
            # Fill in data from database
            for month_num, credit, debit in data:
                month_index = int(month_num) - 1  # Convert to 0-based index
                credit_data[month_index] = credit
                debit_data[month_index] = debit
            
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
            axisY.setTitleText("Amount (Rs. )")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
            # Update data table
            headers = ["Month", "Credit", "Debit", "Net"]
            table_data = []
            for i, month_name in enumerate(month_names):
                credit = credit_data[i]
                debit = debit_data[i]
                table_data.append([
                    month_name,
                    f"Rs. {credit:.2f}",
                    f"Rs. {debit:.2f}",
                    f"Rs. {credit - debit:.2f}"
                ])
            
            self.updateDataTable(headers, table_data)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating monthly performance chart: {str(e)}")
        finally:
            self.db.close()
    
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