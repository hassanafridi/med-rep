from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QPushButton, QGroupBox, QFormLayout, QRadioButton,
    QButtonGroup, QDateEdit, QMessageBox
)
from PyQt5.QtCore import QDate
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Make sure we can import from parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from database.db import Database

class MatplotlibCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        self.fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = self.fig.add_subplot(111)
        super(MatplotlibCanvas, self).__init__(self.fig)

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
            "Product Performance"
        ])
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
        
        # Generate chart button
        self.generate_btn = QPushButton("Generate Chart")
        self.generate_btn.clicked.connect(self.generateChart)
        options_layout.addRow("", self.generate_btn)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # Chart canvas
        self.chart_canvas = MatplotlibCanvas(self, width=8, height=6, dpi=100)
        main_layout.addWidget(self.chart_canvas)
        
        self.setLayout(main_layout)
        
        # Generate initial chart
        self.generateChart()
    
    def generateChart(self):
        """Generate the selected chart type"""
        try:
            chart_type = self.chart_type.currentText()
            from_date = self.from_date_edit.date().toString("yyyy-MM-dd")
            to_date = self.to_date_edit.date().toString("yyyy-MM-dd")
            
            # Determine data type filter
            if self.radio_credit.isChecked():
                data_type_filter = "AND e.is_credit = 1"
            elif self.radio_debit.isChecked():
                data_type_filter = "AND e.is_credit = 0"
            else:
                data_type_filter = ""
            
            # Clear the current chart
            self.chart_canvas.axes.clear()
            
            # Generate the appropriate chart based on selection
            if chart_type == "Daily Transactions":
                self.generateDailyChart(from_date, to_date, data_type_filter)
            elif chart_type == "Weekly Transactions":
                self.generateWeeklyChart(from_date, to_date, data_type_filter)
            elif chart_type == "Monthly Transactions":
                self.generateMonthlyChart(from_date, to_date, data_type_filter)
            elif chart_type == "Customer Distribution":
                self.generateCustomerChart(from_date, to_date, data_type_filter)
            elif chart_type == "Product Performance":
                self.generateProductChart(from_date, to_date, data_type_filter)
            
            # Refresh the canvas
            self.chart_canvas.fig.tight_layout()
            self.chart_canvas.draw()
            
        except Exception as e:
            QMessageBox.critical(self, "Chart Error", f"Failed to generate chart: {str(e)}")
    
    def generateDailyChart(self, from_date, to_date, data_type_filter):
        """Generate daily transaction chart"""
        try:
            self.db.connect()
            
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
                self.chart_canvas.axes.text(
                    0.5, 0.5, "No data available for the selected period",
                    horizontalalignment='center', verticalalignment='center'
                )
                return
            
            # Parse data for plotting
            dates = []
            credits = []
            debits = []
            
            for date_str, credit, debit in data:
                dates.append(datetime.strptime(date_str, '%Y-%m-%d'))
                credits.append(credit)
                debits.append(debit)
            
            # Create the chart
            ax = self.chart_canvas.axes
            
            if self.radio_all.isChecked():
                ax.bar(dates, credits, label='Credit', color='green', alpha=0.7)
                ax.bar(dates, debits, label='Debit', color='red', alpha=0.7)
                ax.legend()
            elif self.radio_credit.isChecked():
                ax.bar(dates, credits, color='green', alpha=0.7)
            else:
                ax.bar(dates, debits, color='red', alpha=0.7)
            
            # Format the chart
            ax.set_title('Daily Transactions')
            ax.set_xlabel('Date')
            ax.set_ylabel('Amount ($)')
            
            # Format date axis
            self.chart_canvas.fig.autofmt_xdate()
            
        except Exception as e:
            raise e
        finally:
            self.db.close()
    
    def generateWeeklyChart(self, from_date, to_date, data_type_filter):
        """Generate weekly transaction chart"""
        try:
            self.db.connect()
            
            # SQLite doesn't have built-in week functions, so we'll group by week manually
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            
            # Get all transactions in date range
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
                self.chart_canvas.axes.text(
                    0.5, 0.5, "No data available for the selected period",
                    horizontalalignment='center', verticalalignment='center'
                )
                return
            
            # Group by week
            weekly_data = {}
            
            for date_str, credit, debit in data:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                # Get week number
                week_key = date_obj.strftime('%Y-%U')  # Year-Week format
                
                if week_key not in weekly_data:
                    weekly_data[week_key] = {'credit': 0, 'debit': 0, 'date': date_obj}
                
                weekly_data[week_key]['credit'] += credit
                weekly_data[week_key]['debit'] += debit
            
            # Sort weeks
            sorted_weeks = sorted(weekly_data.keys())
            
            # Extract data for plotting
            weeks = []
            credits = []
            debits = []
            
            for week in sorted_weeks:
                weeks.append(weekly_data[week]['date'])
                credits.append(weekly_data[week]['credit'])
                debits.append(weekly_data[week]['debit'])
            
            # Create the chart
            ax = self.chart_canvas.axes
            
            if self.radio_all.isChecked():
                ax.bar(weeks, credits, label='Credit', color='green', alpha=0.7)
                ax.bar(weeks, debits, label='Debit', color='red', alpha=0.7)
                ax.legend()
            elif self.radio_credit.isChecked():
                ax.bar(weeks, credits, color='green', alpha=0.7)
            else:
                ax.bar(weeks, debits, color='red', alpha=0.7)
            
            # Format the chart
            ax.set_title('Weekly Transactions')
            ax.set_xlabel('Week')
            ax.set_ylabel('Amount ($)')
            
            # Format date axis
            self.chart_canvas.fig.autofmt_xdate()
            
        except Exception as e:
            raise e
        finally:
            self.db.close()
    
    def generateMonthlyChart(self, from_date, to_date, data_type_filter):
        """Generate monthly transaction chart"""
        try:
            self.db.connect()
            
            # SQLite doesn't have built-in month functions, so we'll group by month manually
            from_date_obj = datetime.strptime(from_date, '%Y-%m-%d')
            to_date_obj = datetime.strptime(to_date, '%Y-%m-%d')
            
            # Get all transactions in date range
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
                self.chart_canvas.axes.text(
                    0.5, 0.5, "No data available for the selected period",
                    horizontalalignment='center', verticalalignment='center'
                )
                return
            
            # Group by month
            monthly_data = {}
            
            for date_str, credit, debit in data:
                date_obj = datetime.strptime(date_str, '%Y-%m-%d')
                # Get month number
                month_key = date_obj.strftime('%Y-%m')  # Year-Month format
                
                if month_key not in monthly_data:
                    monthly_data[month_key] = {'credit': 0, 'debit': 0, 'date': date_obj}
                
                monthly_data[month_key]['credit'] += credit
                monthly_data[month_key]['debit'] += debit
            
            # Sort months
            sorted_months = sorted(monthly_data.keys())
            
            # Extract data for plotting
            months = []
            credits = []
            debits = []
            
            for month in sorted_months:
                months.append(monthly_data[month]['date'])
                credits.append(monthly_data[month]['credit'])
                debits.append(monthly_data[month]['debit'])
            
            # Create the chart
            ax = self.chart_canvas.axes
            
            if self.radio_all.isChecked():
                ax.bar(months, credits, label='Credit', color='green', alpha=0.7)
                ax.bar(months, debits, label='Debit', color='red', alpha=0.7)
                ax.legend()
            elif self.radio_credit.isChecked():
                ax.bar(months, credits, color='green', alpha=0.7)
            else:
                ax.bar(months, debits, color='red', alpha=0.7)
            
            # Format the chart
            ax.set_title('Monthly Transactions')
            ax.set_xlabel('Month')
            ax.set_ylabel('Amount ($)')
            
            # Format date axis to show month names
            ax.xaxis.set_major_formatter(plt.matplotlib.dates.DateFormatter('%b %Y'))
            self.chart_canvas.fig.autofmt_xdate()
            
        except Exception as e:
            raise e
        finally:
            self.db.close()
    
    def generateCustomerChart(self, from_date, to_date, data_type_filter):
        """Generate customer distribution pie chart"""
        try:
            self.db.connect()
            
            # Prepare the data type condition for the SQL query
            if data_type_filter:
                data_type_cond = data_type_filter.replace("AND", "WHERE")
            else:
                data_type_cond = ""
            
            query = f"""
                SELECT 
                    c.name,
                    SUM(e.quantity * e.unit_price) as total
                FROM entries e
                JOIN customers c ON e.customer_id = c.id
                WHERE e.date BETWEEN ? AND ?
                {data_type_filter}
                GROUP BY c.name
                ORDER BY total DESC
                LIMIT 10
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.chart_canvas.axes.text(
                    0.5, 0.5, "No data available for the selected period",
                    horizontalalignment='center', verticalalignment='center'
                )
                return
            
            # Parse data for plotting
            customers = []
            amounts = []
            
            for customer, amount in data:
                customers.append(customer)
                amounts.append(amount)
            
            # Create the pie chart
            ax = self.chart_canvas.axes
            ax.pie(amounts, labels=customers, autopct='%1.1f%%', startangle=90)
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle
            
            # Format the chart
            title_suffix = ""
            if self.radio_credit.isChecked():
                title_suffix = " (Credits Only)"
            elif self.radio_debit.isChecked():
                title_suffix = " (Debits Only)"
                
            ax.set_title(f'Top 10 Customers by Transaction Volume{title_suffix}')
            
        except Exception as e:
            raise e
        finally:
            self.db.close()
    
    def generateProductChart(self, from_date, to_date, data_type_filter):
        """Generate product performance chart"""
        try:
            self.db.connect()
            
            query = f"""
                SELECT 
                    p.name,
                    SUM(e.quantity * e.unit_price) as total
                FROM entries e
                JOIN products p ON e.product_id = p.id
                WHERE e.date BETWEEN ? AND ?
                {data_type_filter}
                GROUP BY p.name
                ORDER BY total DESC
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                self.chart_canvas.axes.text(
                    0.5, 0.5, "No data available for the selected period",
                    horizontalalignment='center', verticalalignment='center'
                )
                return
            
            # Parse data for plotting
            products = []
            amounts = []
            
            for product, amount in data:
                products.append(product)
                amounts.append(amount)
            
            # Create the horizontal bar chart
            ax = self.chart_canvas.axes
            y_pos = np.arange(len(products))
            
            # Determine bar color based on selection
            bar_color = 'blue'
            if self.radio_credit.isChecked():
                bar_color = 'green'
            elif self.radio_debit.isChecked():
                bar_color = 'red'
                
            ax.barh(y_pos, amounts, align='center', color=bar_color, alpha=0.7)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(products)
            ax.invert_yaxis()  # Labels read top-to-bottom
            
            # Format the chart
            title_suffix = ""
            if self.radio_credit.isChecked():
                title_suffix = " (Credits Only)"
            elif self.radio_debit.isChecked():
                title_suffix = " (Debits Only)"
                
            ax.set_title(f'Product Performance{title_suffix}')
            ax.set_xlabel('Total Amount ($)')
            
        except Exception as e:
            raise e
        finally:
            self.db.close()