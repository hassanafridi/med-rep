from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QPushButton, QGroupBox, QFormLayout,
    QRadioButton, QButtonGroup, QDateEdit, QMessageBox,
    QCheckBox
)
from PyQt5.QtCore import QDate
from PyQt5.QtChart import (
    QChart, QChartView, QBarSeries, QBarSet, 
    QValueAxis, QBarCategoryAxis, QPieSeries,
    QLineSeries, QDateTimeAxis, QScatterSeries
)
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtCore import Qt, QDateTime
import sys
import os
from datetime import datetime, timedelta

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter

class GraphsTab(QWidget):
    def __init__(self, mongo_adapter=None):
        super().__init__()
        try:
            self.mongo_adapter = mongo_adapter or MongoAdapter()
            self.initUI()
        except Exception as e:
            print(f"Error initializing Graphs tab: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Graphs tab temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the graphs tab"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.mongo_adapter)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Graphs tab: {str(e)}")
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Chart options section
        options_group = QGroupBox("Chart Options")
        options_layout = QFormLayout()
        
        # Chart type selection
        self.chart_type = QComboBox()
        self.chart_type.addItems([
            "Daily Transactions", 
            "Weekly Transactions", 
            "Monthly Transactions",
            "Customer Distribution",
            "Product Performance",
            "Product Batch Analysis",
            "Expiry Date Analysis"
        ])
        self.chart_type.currentIndexChanged.connect(self.updateChartOptions)
        options_layout.addRow("Chart Type:", self.chart_type)
        
        # Date range selection
        date_range_layout = QHBoxLayout()
        
        self.from_date_edit = QDateEdit()
        self.from_date_edit.setDate(QDate.currentDate().addMonths(-3))  # Default to last 3 months
        self.from_date_edit.setCalendarPopup(True)
        
        self.to_date_edit = QDateEdit()
        self.to_date_edit.setDate(QDate.currentDate())
        self.to_date_edit.setCalendarPopup(True)
        
        date_range_layout.addWidget(QLabel("From:"))
        date_range_layout.addWidget(self.from_date_edit)
        date_range_layout.addWidget(QLabel("To:"))
        date_range_layout.addWidget(self.to_date_edit)
        
        options_layout.addRow("Date Range:", date_range_layout)
        
        # Data type options
        data_type_layout = QHBoxLayout()
        
        self.data_type_group = QButtonGroup(self)
        
        self.radio_all = QRadioButton("All")
        self.radio_credit = QRadioButton("Credit Only")
        self.radio_debit = QRadioButton("Debit Only")
        
        self.data_type_group.addButton(self.radio_all, 1)
        self.data_type_group.addButton(self.radio_credit, 2)
        self.data_type_group.addButton(self.radio_debit, 3)
        
        self.radio_all.setChecked(True)
        
        data_type_layout.addWidget(self.radio_all)
        data_type_layout.addWidget(self.radio_credit)
        data_type_layout.addWidget(self.radio_debit)
        
        options_layout.addRow("Data Type:", data_type_layout)
        
        # Additional options container
        self.additional_options_layout = QFormLayout()
        options_layout.addRow(self.additional_options_layout)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Generate chart button
        generate_layout = QHBoxLayout()
        
        self.generate_btn = QPushButton("Generate Chart")
        self.generate_btn.clicked.connect(self.generateChart)
        self.generate_btn.setStyleSheet("""
            QPushButton {
                background-color: #4B0082;
                color: white;
                padding: 10px;
                font-weight: bold;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #6B0AC2;
            }
        """)
        generate_layout.addWidget(self.generate_btn)
        
        main_layout.addLayout(generate_layout)
        
        # Chart view
        self.chart_view = QChartView()
        self.chart_view.setRenderHint(QPainter.Antialiasing)
        main_layout.addWidget(self.chart_view)
        
        self.setLayout(main_layout)
        
        # Initialize with empty chart
        self.showEmptyChart("Select options and click Generate Chart")
        
        # Initialize additional options
        self.updateChartOptions()
        
    def updateChartOptions(self):
        """Update chart options based on selected chart type"""
        # Clear existing additional options
        while self.additional_options_layout.count():
            item = self.additional_options_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        chart_type = self.chart_type.currentText()
        
        if chart_type == "Product Batch Analysis":
            # Option to show expired products only
            self.show_expired_only = QCheckBox("Show expired batches only")
            self.additional_options_layout.addRow("Filter:", self.show_expired_only)
            
            # Option to group by product name
            self.group_by_product = QCheckBox("Group by product name")
            self.group_by_product.setChecked(True)
            self.additional_options_layout.addRow("Grouping:", self.group_by_product)
            
        elif chart_type == "Expiry Date Analysis":
            # Option to show expiry timeline
            self.expiry_timeline = QCheckBox("Show expiry timeline")
            self.expiry_timeline.setChecked(True)
            self.additional_options_layout.addRow("View:", self.expiry_timeline)
            
            # Option for expiry threshold
            self.expiry_threshold = QComboBox()
            self.expiry_threshold.addItems(["30 days", "60 days", "90 days", "6 months", "1 year"])
            self.additional_options_layout.addRow("Show products expiring within:", self.expiry_threshold)
        
    def generateChart(self):
        """Generate the selected chart type"""
        try:
            # Validate MongoDB connection
            if not self.mongo_adapter:
                QMessageBox.warning(self, "Database Error", "MongoDB connection not available")
                return
            
            chart_type = self.chart_type.currentText()
            from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
            to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
            
            # Generate appropriate chart based on selection
            if chart_type == "Daily Transactions":
                self.generateDailyChart(from_date, to_date)
            elif chart_type == "Weekly Transactions":
                self.generateWeeklyChart(from_date, to_date)
            elif chart_type == "Monthly Transactions":
                self.generateMonthlyChart(from_date, to_date)
            elif chart_type == "Customer Distribution":
                self.generateCustomerChart(from_date, to_date)
            elif chart_type == "Product Performance":
                self.generateProductChart(from_date, to_date)
            elif chart_type == "Product Batch Analysis":
                self.generateBatchAnalysisChart(from_date, to_date)
            elif chart_type == "Expiry Date Analysis":
                self.generateExpiryAnalysisChart(from_date, to_date)
                
        except Exception as e:
            QMessageBox.critical(self, "Chart Error", f"Failed to generate chart: {str(e)}")
    
    def generateDailyChart(self, from_date, to_date):
        """Generate daily transaction chart using MongoDB"""
        try:
            # Get entries from MongoDB
            entries = self.mongo_adapter.get_entries()
            
            if not entries:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Filter entries by date range
            filtered_entries = []
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date:
                    filtered_entries.append(entry)
            
            if not filtered_entries:
                self.showEmptyChart("No data available for the selected date range")
                return
            
            # Group by date
            daily_data = {}
            for entry in filtered_entries:
                date_str = entry.get('date', '')
                is_credit = entry.get('is_credit', False)
                amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                
                if date_str not in daily_data:
                    daily_data[date_str] = {'credit': 0, 'debit': 0}
                
                if is_credit:
                    daily_data[date_str]['credit'] += amount
                else:
                    daily_data[date_str]['debit'] += amount
            
            # Create chart
            chart = QChart()
            chart.setTitle("Daily Transactions")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Sort dates and prepare data
            sorted_dates = sorted(daily_data.keys())
            dates = []
            credit_amounts = []
            debit_amounts = []
            
            for date_str in sorted_dates:
                dates.append(date_str)
                credit_amounts.append(daily_data[date_str]['credit'])
                debit_amounts.append(daily_data[date_str]['debit'])
            
            # Add bar sets based on radio button selection
            if self.radio_all.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#F44336"))
                credit_set.append(credit_amounts)
                
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#4CAF50"))
                debit_set.append(debit_amounts)
                
                series.append(credit_set)
                series.append(debit_set)
            elif self.radio_credit.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#F44336"))
                credit_set.append(credit_amounts)
                series.append(credit_set)
            else:
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#4CAF50"))
                debit_set.append(debit_amounts)
                series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(dates)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (PKR)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")

    def generateWeeklyChart(self, from_date, to_date):
        """Generate weekly transaction chart using MongoDB"""
        try:
            # Get entries from MongoDB
            entries = self.mongo_adapter.get_entries()
            
            if not entries:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Filter and group by week
            weekly_data = {}
            
            for entry in entries:
                entry_date_str = entry.get('date', '')
                if from_date <= entry_date_str <= to_date:
                    try:
                        date_obj = datetime.strptime(entry_date_str, '%Y-%m-%d')
                        # Get week number (year-week format)
                        week_key = date_obj.strftime('%Y-W%U')
                        
                        if week_key not in weekly_data:
                            weekly_data[week_key] = {'credit': 0, 'debit': 0}
                        
                        amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                        if entry.get('is_credit'):
                            weekly_data[week_key]['credit'] += amount
                        else:
                            weekly_data[week_key]['debit'] += amount
                    except ValueError:
                        continue  # Skip invalid dates
            
            if not weekly_data:
                self.showEmptyChart("No valid data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle("Weekly Transactions")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Sort weeks and prepare data
            sorted_weeks = sorted(weekly_data.keys())
            weeks = []
            credit_amounts = []
            debit_amounts = []
            
            for week in sorted_weeks:
                weeks.append(week)
                credit_amounts.append(weekly_data[week]['credit'])
                debit_amounts.append(weekly_data[week]['debit'])
            
            # Add bar sets based on radio button selection
            if self.radio_all.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#F44336"))
                credit_set.append(credit_amounts)
                
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#4CAF50"))
                debit_set.append(debit_amounts)
                
                series.append(credit_set)
                series.append(debit_set)
            elif self.radio_credit.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#F44336"))
                credit_set.append(credit_amounts)
                series.append(credit_set)
            else:
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#4CAF50"))
                debit_set.append(debit_amounts)
                series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(weeks)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (PKR)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")

    def generateMonthlyChart(self, from_date, to_date):
        """Generate monthly transaction chart using MongoDB"""
        try:
            # Get entries from MongoDB
            entries = self.mongo_adapter.get_entries()
            
            if not entries:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Filter and group by month
            monthly_data = {}
            
            for entry in entries:
                entry_date_str = entry.get('date', '')
                if from_date <= entry_date_str <= to_date:
                    try:
                        date_obj = datetime.strptime(entry_date_str, '%Y-%m-%d')
                        month_key = date_obj.strftime('%Y-%m')
                        
                        if month_key not in monthly_data:
                            monthly_data[month_key] = {'credit': 0, 'debit': 0}
                        
                        amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                        if entry.get('is_credit'):
                            monthly_data[month_key]['credit'] += amount
                        else:
                            monthly_data[month_key]['debit'] += amount
                    except ValueError:
                        continue
            
            if not monthly_data:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle("Monthly Transactions")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Sort months and prepare data
            sorted_months = sorted(monthly_data.keys())
            months = []
            credit_amounts = []
            debit_amounts = []
            
            for month in sorted_months:
                months.append(month)
                credit_amounts.append(monthly_data[month]['credit'])
                debit_amounts.append(monthly_data[month]['debit'])
            
            # Add bar sets based on radio button selection
            if self.radio_all.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#F44336"))
                credit_set.append(credit_amounts)
                
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#4CAF50"))
                debit_set.append(debit_amounts)
                
                series.append(credit_set)
                series.append(debit_set)
            elif self.radio_credit.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#F44336"))
                credit_set.append(credit_amounts)
                series.append(credit_set)
            else:
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#4CAF50"))
                debit_set.append(debit_amounts)
                series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(months)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (PKR)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")

    def generateCustomerChart(self, from_date, to_date):
        """Generate customer distribution pie chart using MongoDB"""
        try:
            # Get entries and customers from MongoDB
            entries = self.mongo_adapter.get_entries()
            customers = self.mongo_adapter.get_customers()
            
            if not entries or not customers:
                self.showEmptyChart("No customer data available for the selected period")
                return
            
            # Create customer lookup
            customer_lookup = {str(customer.get('id')): customer.get('name', 'Unknown') 
                             for customer in customers}
            
            # Calculate customer totals
            customer_totals = {}
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date and entry.get('is_credit'):
                    customer_id = str(entry.get('customer_id', ''))
                    customer_name = customer_lookup.get(customer_id, 'Unknown')
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    
                    customer_totals[customer_name] = customer_totals.get(customer_name, 0) + amount
            
            if not customer_totals:
                self.showEmptyChart("No customer data available for the selected period")
                return
            
            # Sort and get top 10
            sorted_customers = sorted(customer_totals.items(), key=lambda x: x[1], reverse=True)[:10]
            
            # Create chart
            chart = QChart()
            chart.setTitle("Customer Distribution (Top 10)")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create pie series
            series = QPieSeries()
            
            total_amount = sum(amount for _, amount in sorted_customers)
            
            for customer, amount in sorted_customers:
                slice = series.append(customer, amount)
                # Calculate percentage
                percentage = (amount / total_amount) * 100
                slice.setLabel(f"{customer}: {percentage:.1f}%")
                slice.setLabelVisible(True)
            
            chart.addSeries(series)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")

    def generateProductChart(self, from_date, to_date):
        """Generate product performance chart using MongoDB"""
        try:
            # Get entries and products from MongoDB
            entries = self.mongo_adapter.get_entries()
            products = self.mongo_adapter.get_products()
            
            if not entries or not products:
                self.showEmptyChart("No product data available for the selected period")
                return
            
            # Create product lookup
            product_lookup = {str(product.get('id')): product for product in products}
            
            # Calculate product totals
            product_totals = {}
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date and entry.get('is_credit'):
                    product_id = str(entry.get('product_id', ''))
                    product_info = product_lookup.get(product_id, {})
                    product_name = product_info.get('name', 'Unknown')
                    batch_number = product_info.get('batch_number', '')
                    
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    
                    if product_name not in product_totals:
                        product_totals[product_name] = {
                            'total': 0,
                            'batches': set()
                        }
                    
                    product_totals[product_name]['total'] += amount
                    if batch_number:
                        product_totals[product_name]['batches'].add(batch_number)
            
            if not product_totals:
                self.showEmptyChart("No product data available for the selected period")
                return
            
            # Sort and get top 10
            sorted_products = sorted(product_totals.items(), key=lambda x: x[1]['total'], reverse=True)[:10]
            
            # Create chart
            chart = QChart()
            chart.setTitle("Product Performance (Top 10 by Sales)")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Prepare data
            products = []
            amounts = []
            
            for product_name, data in sorted_products:
                batch_count = len(data['batches'])
                product_label = f"{product_name}\n({batch_count} batch{'es' if batch_count > 1 else ''})"
                products.append(product_label)
                amounts.append(data['total'])
            
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
            axisY.setTitleText("Sales Amount (PKR)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")

    def generateBatchAnalysisChart(self, from_date, to_date):
        """Generate batch analysis chart using MongoDB"""
        try:
            # Get entries and products from MongoDB
            entries = self.mongo_adapter.get_entries()
            products = self.mongo_adapter.get_products()
            
            if not entries or not products:
                self.showEmptyChart("No batch data available for the selected criteria")
                return
            
            # Create product lookup
            product_lookup = {str(product.get('id')): product for product in products}
            
            # Check if we should show expired batches only
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            show_expired_only = hasattr(self, 'show_expired_only') and self.show_expired_only.isChecked()
            group_by_product = hasattr(self, 'group_by_product') and self.group_by_product.isChecked()
            
            # Calculate batch/product totals
            if group_by_product:
                # Group by product name
                product_totals = {}
                for entry in entries:
                    entry_date = entry.get('date', '')
                    if from_date <= entry_date <= to_date and entry.get('is_credit'):
                        product_id = str(entry.get('product_id', ''))
                        product_info = product_lookup.get(product_id, {})
                        product_name = product_info.get('name', 'Unknown')
                        expiry_date = product_info.get('expiry_date', '')
                        
                        # Filter expired if needed
                        if show_expired_only and expiry_date >= current_date:
                            continue
                        
                        amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                        
                        if product_name not in product_totals:
                            product_totals[product_name] = {
                                'total': 0,
                                'batch_count': set(),
                                'expired_batches': set()
                            }
                        
                        product_totals[product_name]['total'] += amount
                        batch_number = product_info.get('batch_number', '')
                        if batch_number:
                            product_totals[product_name]['batch_count'].add(batch_number)
                            if expiry_date < current_date:
                                product_totals[product_name]['expired_batches'].add(batch_number)
                
                data_list = [(name, data['total'], len(data['batch_count']), len(data['expired_batches'])) 
                           for name, data in product_totals.items()]
            else:
                # Show individual batches
                batch_totals = {}
                for entry in entries:
                    entry_date = entry.get('date', '')
                    if from_date <= entry_date <= to_date and entry.get('is_credit'):
                        product_id = str(entry.get('product_id', ''))
                        product_info = product_lookup.get(product_id, {})
                        product_name = product_info.get('name', 'Unknown')
                        batch_number = product_info.get('batch_number', '')
                        expiry_date = product_info.get('expiry_date', '')
                        
                        # Filter expired if needed
                        if show_expired_only and expiry_date >= current_date:
                            continue
                        
                        batch_key = f"{product_name} ({batch_number})"
                        amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                        
                        if batch_key not in batch_totals:
                            batch_totals[batch_key] = {
                                'total': 0,
                                'is_expired': expiry_date < current_date
                            }
                        
                        batch_totals[batch_key]['total'] += amount
                
                data_list = [(name, data['total'], 1, 1 if data['is_expired'] else 0) 
                           for name, data in batch_totals.items()]
            
            if not data_list:
                self.showEmptyChart("No batch data available for the selected criteria")
                return
            
            # Sort and limit
            data_list.sort(key=lambda x: x[1], reverse=True)
            data_list = data_list[:15]
            
            # Create chart
            chart = QChart()
            title = "Product Batch Analysis"
            if show_expired_only:
                title += " (Expired Batches Only)"
            chart.setTitle(title)
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Prepare data
            labels = []
            amounts = []
            
            for label, amount, batch_count, expired_batches in data_list:
                labels.append(label)
                amounts.append(amount)
            
            # Create bar set
            bar_set = QBarSet("Sales")
            bar_set.setColor(QColor("#2196F3"))
            bar_set.append(amounts)
            
            series.append(bar_set)
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(labels)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Sales Amount (PKR)")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating batch analysis chart: {str(e)}")

    def generateExpiryAnalysisChart(self, from_date, to_date):
        """Generate expiry date analysis chart using MongoDB"""
        try:
            # Get entries and products from MongoDB
            entries = self.mongo_adapter.get_entries()
            products = self.mongo_adapter.get_products()
            
            if not entries or not products:
                self.showEmptyChart("No product expiry data available for the selected period")
                return
            
            # Create product lookup
            product_lookup = {str(product.get('id')): product for product in products}
            
            # Get threshold from combobox
            threshold_text = "30 days"
            if hasattr(self, 'expiry_threshold'):
                threshold_text = self.expiry_threshold.currentText()
            
            # Convert threshold to days
            threshold_days = {
                "30 days": 30,
                "60 days": 60,
                "90 days": 90,
                "6 months": 180,
                "1 year": 365
            }.get(threshold_text, 30)
            
            current_date = QDate.currentDate()
            threshold_date = current_date.addDays(threshold_days).toString("yyyy-MM-dd")
            current_date_str = current_date.toString("yyyy-MM-dd")
            
            # Calculate product sales with expiry status
            product_sales = {}
            for entry in entries:
                entry_date = entry.get('date', '')
                if from_date <= entry_date <= to_date and entry.get('is_credit'):
                    product_id = str(entry.get('product_id', ''))
                    product_info = product_lookup.get(product_id, {})
                    product_name = product_info.get('name', 'Unknown')
                    batch_number = product_info.get('batch_number', '')
                    expiry_date = product_info.get('expiry_date', '')
                    
                    # Determine expiry status
                    if expiry_date < current_date_str:
                        status = 'Expired'
                    elif expiry_date <= threshold_date:
                        status = 'Expiring Soon'
                    else:
                        status = 'Valid'
                    
                    key = f"{product_name} ({batch_number})"
                    amount = float(entry.get('quantity', 0)) * float(entry.get('unit_price', 0))
                    
                    if key not in product_sales:
                        product_sales[key] = {
                            'amount': 0,
                            'status': status,
                            'expiry_date': expiry_date
                        }
                    
                    product_sales[key]['amount'] += amount
            
            if not product_sales:
                self.showEmptyChart("No product expiry data available for the selected period")
                return
            
            # Check if we should show timeline view
            show_timeline = hasattr(self, 'expiry_timeline') and self.expiry_timeline.isChecked()
            
            if show_timeline:
                # Create a pie chart showing distribution by expiry status
                chart = QChart()
                chart.setTitle(f"Product Expiry Status Distribution\n(Products expiring within {threshold_text})")
                chart.setAnimationOptions(QChart.SeriesAnimations)
                
                # Group data by expiry status
                status_totals = {'Expired': 0, 'Expiring Soon': 0, 'Valid': 0}
                
                for data in product_sales.values():
                    status_totals[data['status']] += data['amount']
                
                # Create pie series
                series = QPieSeries()
                
                colors = {
                    'Expired': QColor("#F44336"),      # Red
                    'Expiring Soon': QColor("#FF9800"), # Orange
                    'Valid': QColor("#4CAF50")         # Green
                }
                
                total_sales = sum(status_totals.values())
                
                for status, amount in status_totals.items():
                    if amount > 0:
                        slice = series.append(status, amount)
                        slice.setColor(colors[status])
                        percentage = (amount / total_sales) * 100 if total_sales > 0 else 0
                        slice.setLabel(f"{status}: PKR{amount:.0f} ({percentage:.1f}%)")
                        slice.setLabelVisible(True)
                
                chart.addSeries(series)
                
            else:
                # Create a bar chart showing individual products/batches
                chart = QChart()
                chart.setTitle(f"Product Sales by Expiry Date\n(Showing products expiring within {threshold_text})")
                chart.setAnimationOptions(QChart.SeriesAnimations)
                
                # Filter to show only expiring/expired products
                filtered_data = [(key, data) for key, data in product_sales.items() 
                               if data['status'] in ['Expired', 'Expiring Soon']]
                
                if not filtered_data:
                    self.showEmptyChart(f"No products expiring within {threshold_text}")
                    return
                
                # Sort by amount and limit to top 10
                filtered_data.sort(key=lambda x: x[1]['amount'], reverse=True)
                filtered_data = filtered_data[:10]
                
                # Create bar series
                series = QBarSeries()
                
                # Prepare data
                labels = []
                expired_amounts = []
                expiring_amounts = []
                
                for key, data in filtered_data:
                    label = f"{key}\nExp: {data['expiry_date']}"
                    labels.append(label)
                    
                    if data['status'] == 'Expired':
                        expired_amounts.append(data['amount'])
                        expiring_amounts.append(0)
                    else:
                        expired_amounts.append(0)
                        expiring_amounts.append(data['amount'])
                
                # Add bar sets
                if any(expired_amounts):
                    expired_set = QBarSet("Expired")
                    expired_set.setColor(QColor("#F44336"))
                    expired_set.append(expired_amounts)
                    series.append(expired_set)
                
                if any(expiring_amounts):
                    expiring_set = QBarSet("Expiring Soon")
                    expiring_set.setColor(QColor("#FF9800"))
                    expiring_set.append(expiring_amounts)
                    series.append(expiring_set)
                
                chart.addSeries(series)
                
                # Create axes
                axisX = QBarCategoryAxis()
                axisX.append(labels)
                chart.addAxis(axisX, Qt.AlignBottom)
                series.attachAxis(axisX)
                
                axisY = QValueAxis()
                axisY.setTitleText("Sales Amount (PKR)")
                chart.addAxis(axisY, Qt.AlignLeft)
                series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating expiry analysis chart: {str(e)}")
    
    def showEmptyChart(self, message):
        """Show an empty chart with message"""
        chart = QChart()
        chart.setTitle(message)
        self.chart_view.setChart(chart)