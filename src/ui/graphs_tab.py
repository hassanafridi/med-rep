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
from database.db import Database

class GraphsTab(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.initUI()
        
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
        """Generate daily transaction chart"""
        try:
            self.db.connect()
            
            # Determine data type condition
            if self.radio_credit.isChecked():
                data_type_filter = "AND e.is_credit = 1"
            elif self.radio_debit.isChecked():
                data_type_filter = "AND e.is_credit = 0"
            else:
                data_type_filter = ""
            
            query = f"""
                SELECT 
                    e.date,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as credit,
                    SUM(CASE WHEN e.is_credit = 0 THEN e.quantity * e.unit_price ELSE 0 END) as debit
                FROM entries e
                WHERE e.date BETWEEN ? AND ?
                {data_type_filter}
                GROUP BY e.date
                ORDER BY e.date
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle("Daily Transactions")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Prepare data
            dates = []
            credit_amounts = []
            debit_amounts = []
            
            for date_str, credit, debit in data:
                dates.append(date_str)
                credit_amounts.append(credit)
                debit_amounts.append(debit)
            
            # Add bar sets based on radio button selection
            if self.radio_all.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#4CAF50"))
                credit_set.append(credit_amounts)
                
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#F44336"))
                debit_set.append(debit_amounts)
                
                series.append(credit_set)
                series.append(debit_set)
            elif self.radio_credit.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#4CAF50"))
                credit_set.append(credit_amounts)
                series.append(credit_set)
            else:
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#F44336"))
                debit_set.append(debit_amounts)
                series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(dates)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (Rs. )")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateWeeklyChart(self, from_date, to_date):
        """Generate weekly transaction chart"""
        try:
            self.db.connect()
            
            # Get daily data first, then group by week
            query = """
                SELECT 
                    e.date,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as credit,
                    SUM(CASE WHEN e.is_credit = 0 THEN e.quantity * e.unit_price ELSE 0 END) as debit
                FROM entries e
                WHERE e.date BETWEEN ? AND ?
                GROUP BY e.date
                ORDER BY e.date
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            daily_data = self.db.cursor.fetchall()
            
            if not daily_data:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Group by week
            weekly_data = {}
            
            for date_str, credit, debit in daily_data:
                try:
                    date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                    # Get week number (year-week format)
                    week_key = date_obj.strftime('%Y-W%U')
                    
                    if week_key not in weekly_data:
                        weekly_data[week_key] = {'credit': 0, 'debit': 0}
                    
                    weekly_data[week_key]['credit'] += credit
                    weekly_data[week_key]['debit'] += debit
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
                credit_set.setColor(QColor("#4CAF50"))
                credit_set.append(credit_amounts)
                
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#F44336"))
                debit_set.append(debit_amounts)
                
                series.append(credit_set)
                series.append(debit_set)
            elif self.radio_credit.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#4CAF50"))
                credit_set.append(credit_amounts)
                series.append(credit_set)
            else:
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#F44336"))
                debit_set.append(debit_amounts)
                series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(weeks)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (Rs. )")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateMonthlyChart(self, from_date, to_date):
        """Generate monthly transaction chart"""
        try:
            self.db.connect()
            
            # Get data grouped by month
            query = """
                SELECT 
                    strftime('%Y-%m', e.date) as month,
                    SUM(CASE WHEN e.is_credit = 1 THEN e.quantity * e.unit_price ELSE 0 END) as credit,
                    SUM(CASE WHEN e.is_credit = 0 THEN e.quantity * e.unit_price ELSE 0 END) as debit
                FROM entries e
                WHERE e.date BETWEEN ? AND ?
                GROUP BY month
                ORDER BY month
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle("Monthly Transactions")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Prepare data
            months = []
            credit_amounts = []
            debit_amounts = []
            
            for month, credit, debit in data:
                months.append(month)
                credit_amounts.append(credit)
                debit_amounts.append(debit)
            
            # Add bar sets based on radio button selection
            if self.radio_all.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#4CAF50"))
                credit_set.append(credit_amounts)
                
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#F44336"))
                debit_set.append(debit_amounts)
                
                series.append(credit_set)
                series.append(debit_set)
            elif self.radio_credit.isChecked():
                credit_set = QBarSet("Credit")
                credit_set.setColor(QColor("#4CAF50"))
                credit_set.append(credit_amounts)
                series.append(credit_set)
            else:
                debit_set = QBarSet("Debit")
                debit_set.setColor(QColor("#F44336"))
                debit_set.append(debit_amounts)
                series.append(debit_set)
            
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(months)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Amount (Rs. )")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateCustomerChart(self, from_date, to_date):
        """Generate customer distribution pie chart"""
        try:
            self.db.connect()
            
            # Get customer data
            query = """
                SELECT 
                    c.name,
                    SUM(e.quantity * e.unit_price) as total
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                WHERE e.date BETWEEN ? AND ? AND e.is_credit = 1
                GROUP BY c.name
                ORDER BY total DESC
                LIMIT 10
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No customer data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle("Customer Distribution (Top 10)")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create pie series
            series = QPieSeries()
            
            total_amount = sum(amount for _, amount in data)
            
            for customer, amount in data:
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
        finally:
            self.db.close()
    
    def generateProductChart(self, from_date, to_date):
        """Generate product performance chart (grouped by product name)"""
        try:
            self.db.connect()
            
            # Get product data grouped by product name (combines all batches)
            query = """
                SELECT 
                    p.name,
                    SUM(e.quantity * e.unit_price) as total,
                    COUNT(DISTINCT p.batch_number) as batch_count
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.date BETWEEN ? AND ? AND e.is_credit = 1
                GROUP BY p.name
                ORDER BY total DESC
                LIMIT 10
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No product data available for the selected period")
                return
            
            # Create chart
            chart = QChart()
            chart.setTitle("Product Performance (Top 10 by Sales)")
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Prepare data
            products = []
            amounts = []
            
            for product, amount, batch_count in data:
                # Add batch count info to product name
                product_label = f"{product}\n({batch_count} batch{'es' if batch_count > 1 else ''})"
                products.append(product_label)
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
            
        except Exception as e:
            self.showEmptyChart(f"Error generating chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateBatchAnalysisChart(self, from_date, to_date):
        """Generate batch analysis chart"""
        try:
            self.db.connect()
            
            # Check if we should show expired batches only
            expired_filter = ""
            current_date = QDate.currentDate().toString("yyyy-MM-dd")
            
            if hasattr(self, 'show_expired_only') and self.show_expired_only.isChecked():
                expired_filter = f"AND p.expiry_date < '{current_date}'"
            
            # Check grouping option
            group_by_product = hasattr(self, 'group_by_product') and self.group_by_product.isChecked()
            
            if group_by_product:
                # Group by product name, showing total sales across all batches
                query = f"""
                    SELECT 
                        p.name as label,
                        SUM(e.quantity * e.unit_price) as total,
                        COUNT(DISTINCT p.batch_number) as batch_count,
                        COUNT(DISTINCT CASE WHEN p.expiry_date < '{current_date}' THEN p.batch_number END) as expired_batches
                    FROM entries e
                    JOIN products p ON e.product_id = p.id
                    WHERE e.date BETWEEN ? AND ? AND e.is_credit = 1 {expired_filter}
                    GROUP BY p.name
                    ORDER BY total DESC
                    LIMIT 10
                """
            else:
                # Show individual batches
                query = f"""
                    SELECT 
                        p.name || ' (' || p.batch_number || ')' as label,
                        SUM(e.quantity * e.unit_price) as total,
                        1 as batch_count,
                        CASE WHEN p.expiry_date < '{current_date}' THEN 1 ELSE 0 END as expired_batches
                    FROM entries e
                    JOIN products p ON e.product_id = p.id
                    WHERE e.date BETWEEN ? AND ? AND e.is_credit = 1 {expired_filter}
                    GROUP BY p.id, p.name, p.batch_number
                    ORDER BY total DESC
                    LIMIT 15
                """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.showEmptyChart("No batch data available for the selected criteria")
                return
            
            # Create chart
            chart = QChart()
            title = "Product Batch Analysis"
            if hasattr(self, 'show_expired_only') and self.show_expired_only.isChecked():
                title += " (Expired Batches Only)"
            chart.setTitle(title)
            chart.setAnimationOptions(QChart.SeriesAnimations)
            
            # Create bar series
            series = QBarSeries()
            
            # Prepare data
            labels = []
            amounts = []
            
            for label, amount, batch_count, expired_batches in data:
                labels.append(label)
                amounts.append(amount)
            
            # Create bar set with color coding
            bar_set = QBarSet("Sales")
            
            # Color based on expiry status if showing individual batches
            if not group_by_product:
                # Individual batches - color expired ones red
                for i, (label, amount, batch_count, expired_batches) in enumerate(data):
                    if expired_batches > 0:
                        bar_set.setColor(QColor("#F44336"))  # Red for expired
                    else:
                        bar_set.setColor(QColor("#4CAF50"))  # Green for valid
            else:
                bar_set.setColor(QColor("#2196F3"))  # Blue for grouped view
            
            bar_set.append(amounts)
            
            series.append(bar_set)
            chart.addSeries(series)
            
            # Create axes
            axisX = QBarCategoryAxis()
            axisX.append(labels)
            chart.addAxis(axisX, Qt.AlignBottom)
            series.attachAxis(axisX)
            
            axisY = QValueAxis()
            axisY.setTitleText("Sales Amount (Rs. )")
            chart.addAxis(axisY, Qt.AlignLeft)
            series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating batch analysis chart: {str(e)}")
        finally:
            self.db.close()
    
    def generateExpiryAnalysisChart(self, from_date, to_date):
        """Generate expiry date analysis chart"""
        try:
            self.db.connect()
            
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
            
            # Get products with sales in the date range and their expiry status
            query = """
                SELECT 
                    p.name,
                    p.batch_number,
                    p.expiry_date,
                    SUM(e.quantity * e.unit_price) as total_sales,
                    CASE 
                        WHEN p.expiry_date < ? THEN 'Expired'
                        WHEN p.expiry_date <= ? THEN 'Expiring Soon'
                        ELSE 'Valid'
                    END as expiry_status
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.date BETWEEN ? AND ? AND e.is_credit = 1
                GROUP BY p.id, p.name, p.batch_number, p.expiry_date
                ORDER BY p.expiry_date
            """
            
            self.db.cursor.execute(query, (current_date_str, threshold_date, from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
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
                
                for name, batch, expiry_date, sales, status in data:
                    status_totals[status] += sales
                
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
                        slice.setLabel(f"{status}: Rs. {amount:.0f} ({percentage:.1f}%)")
                        slice.setLabelVisible(True)
                
                chart.addSeries(series)
                
            else:
                # Create a bar chart showing individual products/batches
                chart = QChart()
                chart.setTitle(f"Product Sales by Expiry Date\n(Showing products expiring within {threshold_text})")
                chart.setAnimationOptions(QChart.SeriesAnimations)
                
                # Filter to show only expiring/expired products
                filtered_data = [item for item in data if item[4] in ['Expired', 'Expiring Soon']]
                
                if not filtered_data:
                    self.showEmptyChart(f"No products expiring within {threshold_text}")
                    return
                
                # Limit to top 10 by sales
                filtered_data = filtered_data[:10]
                
                # Create bar series
                series = QBarSeries()
                
                # Prepare data
                labels = []
                amounts = []
                
                for name, batch, expiry_date, sales, status in filtered_data:
                    label = f"{name}\n({batch})\nExp: {expiry_date}"
                    labels.append(label)
                    amounts.append(sales)
                
                # Create bar sets by status
                expired_amounts = []
                expiring_amounts = []
                
                for name, batch, expiry_date, sales, status in filtered_data:
                    if status == 'Expired':
                        expired_amounts.append(sales)
                        expiring_amounts.append(0)
                    else:
                        expired_amounts.append(0)
                        expiring_amounts.append(sales)
                
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
                axisY.setTitleText("Sales Amount (Rs. )")
                chart.addAxis(axisY, Qt.AlignLeft)
                series.attachAxis(axisY)
            
            # Set chart to view
            self.chart_view.setChart(chart)
            
        except Exception as e:
            self.showEmptyChart(f"Error generating expiry analysis chart: {str(e)}")
        finally:
            self.db.close()
    
    def showEmptyChart(self, message):
        """Show an empty chart with message"""
        chart = QChart()
        chart.setTitle(message)
        self.chart_view.setChart(chart)