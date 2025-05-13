from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
    QLabel, QDateEdit, QGroupBox, QFormLayout,
    QPushButton, QCheckBox, QTabWidget, QSplitter,
    QTableWidget, QTableWidgetItem, QHeaderView
)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtWebEngineWidgets import QWebEngineView
import json
import os
import sys
import pandas as pd
import numpy as np

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
            "Monthly Performance",
            "Sales Heatmap"
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
        
        # Web view for interactive chart
        self.web_view = QWebEngineView()
        splitter.addWidget(self.web_view)
        
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
        
        # Set initial chart content
        self.web_view.setHtml(
            """
            <html>
            <head>
                <title>Chart</title>
                <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
                <script src="https://cdn.jsdelivr.net/npm/moment"></script>
                <script src="https://cdn.jsdelivr.net/npm/chartjs-adapter-moment"></script>
                <style>
                    body { margin: 0; padding: 20px; font-family: Arial, sans-serif; }
                    #chart-container { width: 100%; height: 100%; }
                </style>
            </head>
            <body>
                <div id="chart-container">
                    <canvas id="myChart"></canvas>
                </div>
                
                <script>
                    // Initial empty chart
                    const ctx = document.getElementById('myChart').getContext('2d');
                    const myChart = new Chart(ctx, {
                        type: 'bar',
                        data: {
                            labels: [],
                            datasets: []
                        },
                        options: {
                            responsive: true,
                            maintainAspectRatio: false,
                            plugins: {
                                title: {
                                    display: true,
                                    text: 'Select options and click Generate Chart'
                                }
                            }
                        }
                    });
                    
                    // Function to update chart with new data
                    function updateChart(chartConfig) {
                        myChart.destroy();
                        new Chart(ctx, chartConfig);
                    }
                </script>
            </body>
            </html>
            """
        )
    
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
            
            # Show cumulative option
            self.show_cumulative = QCheckBox("Show Cumulative")
            self.options_layout.addRow("", self.show_cumulative)
            
        elif chart_type == "Product Comparison":
            # Add product limit option
            self.product_limit = QComboBox()
            self.product_limit.addItems(["Top 5", "Top 10", "All Products"])
            self.options_layout.addRow("Products to Show:", self.product_limit)
            
            # Add chart style option
            self.chart_style = QComboBox()
            self.chart_style.addItems(["Bar Chart", "Pie Chart", "Radar Chart"])
            self.options_layout.addRow("Chart Style:", self.chart_style)
            
        elif chart_type == "Customer Analysis":
            # Add customer limit option
            self.customer_limit = QComboBox()
            self.customer_limit.addItems(["Top 5", "Top 10", "All Customers"])
            self.options_layout.addRow("Customers to Show:", self.customer_limit)
            
            # Add data metric option
            self.data_metric = QComboBox()
            self.data_metric.addItems(["Total Sales", "Transaction Count", "Average Transaction"])
            self.options_layout.addRow("Measure:", self.data_metric)
            
        elif chart_type == "Credit vs Debit":
            # Add time breakdown option
            self.time_breakdown = QComboBox()
            self.time_breakdown.addItems(["Daily", "Weekly", "Monthly", "Quarterly"])
            self.options_layout.addRow("Time Breakdown:", self.time_breakdown)
            
            # Add chart type option
            self.comparison_type = QComboBox()
            self.comparison_type.addItems(["Side by Side", "Stacked", "Line"])
            self.options_layout.addRow("Comparison Type:", self.comparison_type)
            
        elif chart_type == "Monthly Performance":
            # Add year selection
            self.year_selection = QComboBox()
            current_year = QDate.currentDate().year()
            for year in range(current_year - 5, current_year + 1):
                self.year_selection.addItem(str(year))
            self.year_selection.setCurrentText(str(current_year))
            self.options_layout.addRow("Year:", self.year_selection)
            
            # Add include target line option
            self.show_target = QCheckBox("Show Target Line")
            self.options_layout.addRow("", self.show_target)
            
        elif chart_type == "Sales Heatmap":
            # Add year selection
            self.heatmap_year = QComboBox()
            current_year = QDate.currentDate().year()
            for year in range(current_year - 5, current_year + 1):
                self.heatmap_year.addItem(str(year))
            self.heatmap_year.setCurrentText(str(current_year))
            self.options_layout.addRow("Year:", self.heatmap_year)
            
            # Add heatmap metric option
            self.heatmap_metric = QComboBox()
            self.heatmap_metric.addItems(["Total Sales", "Transaction Count", "Credit Only", "Debit Only"])
            self.options_layout.addRow("Metric:", self.heatmap_metric)
    
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
                show_cumulative = self.show_cumulative.isChecked()
                
                self.generateSalesTrendChart(from_date, to_date, grouping, include_credit, include_debit, show_cumulative)
                
            elif chart_type == "Product Comparison":
                product_limit = self.product_limit.currentText()
                chart_style = self.chart_style.currentText()
                
                self.generateProductComparisonChart(from_date, to_date, product_limit, chart_style)
                
            elif chart_type == "Customer Analysis":
                customer_limit = self.customer_limit.currentText()
                data_metric = self.data_metric.currentText()
                
                self.generateCustomerAnalysisChart(from_date, to_date, customer_limit, data_metric)
                
            elif chart_type == "Credit vs Debit":
                time_breakdown = self.time_breakdown.currentText()
                comparison_type = self.comparison_type.currentText()
                
                self.generateCreditDebitComparisonChart(from_date, to_date, time_breakdown, comparison_type)
                
            elif chart_type == "Monthly Performance":
                year = self.year_selection.currentText()
                show_target = self.show_target.isChecked()
                
                self.generateMonthlyPerformanceChart(year, show_target)
                
            elif chart_type == "Sales Heatmap":
                year = self.heatmap_year.currentText()
                metric = self.heatmap_metric.currentText()
                
                self.generateSalesHeatmapChart(year, metric)
                
        except Exception as e:
            print(f"Chart generation error: {e}")
    
    def generateSalesTrendChart(self, from_date, to_date, grouping, include_credit, include_debit, show_cumulative):
        """Generate sales trend chart"""
        try:
            self.db.connect()
            
            # Determine SQL date grouping
            if grouping == "Daily":
                date_format = "%Y-%m-%d"
                date_sql = "date(e.date)"
            elif grouping == "Weekly":
                date_format = "%Y-%W"
                date_sql = "strftime('%Y-%W', e.date)"
            else:  # Monthly
                date_format = "%Y-%m"
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
                # Show empty chart
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Prepare data for chart
            periods = []
            credit_data = []
            debit_data = []
            
            for period, credit, debit in data:
                periods.append(period)
                credit_data.append(credit)
                debit_data.append(debit)
            
            # Build datasets
            datasets = []
            
            if include_credit:
                if show_cumulative:
                    # Calculate cumulative sum
                    cumulative_credit = np.cumsum(credit_data).tolist()
                    datasets.append({
                        'label': 'Cumulative Credit',
                        'data': cumulative_credit,
                        'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                        'borderColor': 'rgba(75, 192, 192, 1)',
                        'borderWidth': 2,
                        'type': 'line',
                        'fill': False,
                        'tension': 0.1
                    })
                else:
                    datasets.append({
                        'label': 'Credit',
                        'data': credit_data,
                        'backgroundColor': 'rgba(75, 192, 192, 0.5)',
                        'borderColor': 'rgba(75, 192, 192, 1)',
                        'borderWidth': 1
                    })
            
            if include_debit:
                if show_cumulative:
                    # Calculate cumulative sum
                    cumulative_debit = np.cumsum(debit_data).tolist()
                    datasets.append({
                        'label': 'Cumulative Debit',
                        'data': cumulative_debit,
                        'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'borderWidth': 2,
                        'type': 'line',
                        'fill': False,
                        'tension': 0.1
                    })
                else:
                    datasets.append({
                        'label': 'Debit',
                        'data': debit_data,
                        'backgroundColor': 'rgba(255, 99, 132, 0.5)',
                        'borderColor': 'rgba(255, 99, 132, 1)',
                        'borderWidth': 1
                    })
            
            # Build chart config
            chart_config = {
                'type': 'bar',
                'data': {
                    'labels': periods,
                    'datasets': datasets
                },
                'options': {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Amount ($)'
                            }
                        },
                        'x': {
                            'title': {
                                'display': True,
                                'text': 'Period'
                            }
                        }
                    },
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': f'Sales Trend ({grouping} Breakdown)'
                        },
                        'tooltip': {
                            'mode': 'index',
                            'intersect': False
                        }
                    }
                }
            }
            
            # Update chart in web view
            self.updateChart(chart_config)
            
            # Update data table
            self.updateDataTable(
                ["Period", "Credit", "Debit", "Net"],
                [(period, f"${credit:.2f}", f"${debit:.2f}", f"${credit - debit:.2f}") for period, credit, debit in data]
            )
            
        except Exception as e:
            print(f"Error generating sales trend chart: {e}")
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
                WHERE e.date BETWEEN ? AND ?
                GROUP BY p.name
                ORDER BY total DESC
                {limit_clause}
            """
            
            self.db.cursor.execute(query, (from_date, to_date))
            data = self.db.cursor.fetchall()
            
            if not data:
                # Show empty chart
                self.showEmptyChart("No data available for the selected period")
                return
            
            # Prepare data for chart
            products = []
            totals = []
            
            for product, total in data:
                products.append(product)
                totals.append(total)
            
            # Determine chart type
            if chart_style == "Pie Chart":
                chart_type = 'pie'
                
                # Generate colors
                colors = self.generateColors(len(products))
                
                datasets = [{
                    'data': totals,
                    'backgroundColor': colors,
                    'borderColor': '#ffffff',
                    'borderWidth': 1
                }]
                
                options = {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Product Sales Comparison'
                        },
                        'legend': {
                            'position': 'right'
                        },
                        'tooltip': {
                            'callbacks': {
                                'label': 'function(context) { return context.label + ": $" + context.raw.toFixed(2); }'
                            }
                        }
                    }
                }
                
            elif chart_style == "Radar Chart":
                chart_type = 'radar'
                
                datasets = [{
                    'label': 'Sales',
                    'data': totals,
                    'backgroundColor': 'rgba(54, 162, 235, 0.2)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }]
                
                options = {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Product Sales Comparison'
                        },
                        'tooltip': {
                            'callbacks': {
                                'label': 'function(context) { return context.label + ": $" + context.raw.toFixed(2); }'
                            }
                        }
                    },
                    'scales': {
                        'r': {
                            'beginAtZero': True
                        }
                    }
                }
                
            else:  # Bar Chart
                chart_type = 'bar'
                
                datasets = [{
                    'label': 'Sales',
                    'data': totals,
                    'backgroundColor': 'rgba(54, 162, 235, 0.5)',
                    'borderColor': 'rgba(54, 162, 235, 1)',
                    'borderWidth': 1
                }]
                
                options = {
                    'responsive': True,
                    'maintainAspectRatio': False,
                    'plugins': {
                        'title': {
                            'display': True,
                            'text': 'Product Sales Comparison'
                        }
                    },
                    'scales': {
                        'y': {
                            'beginAtZero': True,
                            'title': {
                                'display': True,
                                'text': 'Amount ($)'
                            }
                        },
                        'x': {
                            'title': {
                                'display': True,
                                'text': 'Product'
                            }
                        }
                    }
                }
            
            # Build chart config
            chart_config = {
                'type': chart_type,
                'data': {
                    'labels': products,
                    'datasets': datasets
                },
                'options': options
            }
            
            # Update chart in web view
            self.updateChart(chart_config)
            
            # Update data table
            self.updateDataTable(
                ["Product", "Sales Amount", "Percentage"],
                [(product, f"${total:.2f}", f"{(total / sum(totals) * 100):.1f}%") for product, total in data]
            )
            
        except Exception as e:
            print(f"Error generating product comparison chart: {e}")
        finally:
            self.db.close()
    
    def generateColors(self, count):
        """Generate a list of colors for charts"""
        base_colors = [
            'rgba(255, 99, 132, 0.7)',
            'rgba(54, 162, 235, 0.7)',
            'rgba(255, 206, 86, 0.7)',
            'rgba(75, 192, 192, 0.7)',
            'rgba(153, 102, 255, 0.7)',
            'rgba(255, 159, 64, 0.7)',
            'rgba(199, 199, 199, 0.7)',
            'rgba(83, 102, 255, 0.7)',
            'rgba(40, 180, 99, 0.7)',
            'rgba(250, 128, 114, 0.7)'
        ]
        
        # If we need more colors than in our base list, generate them
        if count <= len(base_colors):
            return base_colors[:count]
        else:
            colors = base_colors.copy()
            
            # Generate additional colors using HSL (easier to ensure good contrast)
            for i in range(count - len(base_colors)):
                hue = (i * 137) % 360  # Golden angle approximation for even distribution
                saturation = 70
                lightness = 60
                
                # Convert HSL to RGB
                h = hue / 360
                s = saturation / 100
                l = lightness / 100
                
                if s == 0:
                    r = g = b = l
                else:
                    def hue_to_rgb(p, q, t):
                        if t < 0: t += 1
                        if t > 1: t -= 1
                        if t < 1/6: return p + (q - p) * 6 * t
                        if t < 1/2: return q
                        if t < 2/3: return p + (q - p) * (2/3 - t) * 6
                        return p
                    
                    q = l * (1 + s) if l < 0.5 else l + s - l * s
                    p = 2 * l - q
                    r = hue_to_rgb(p, q, h + 1/3)
                    g = hue_to_rgb(p, q, h)
                    b = hue_to_rgb(p, q, h - 1/3)
                
                r = round(r * 255)
                g = round(g * 255)
                b = round(b * 255)
                
                colors.append(f'rgba({r}, {g}, {b}, 0.7)')
            
            return colors
    
    def updateChart(self, chart_config):
        """Update the chart in the web view with new config"""
        # Convert chart config to JSON
        chart_json = json.dumps(chart_config)
        
        # Update chart using JavaScript
        js_code = f"updateChart({chart_json});"
        self.web_view.page().runJavaScript(js_code)
    
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
        chart_config = {
            'type': 'bar',
            'data': {
                'labels': [],
                'datasets': []
            },
            'options': {
                'responsive': True,
                'maintainAspectRatio': False,
                'plugins': {
                    'title': {
                        'display': True,
                        'text': message
                    }
                }
            }
        }
        
        self.updateChart(chart_config)
        self.data_table.clear()
        self.data_table.setRowCount(0)
        self.data_table.setColumnCount(0)