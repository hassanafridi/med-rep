import os
import datetime
import xlsxwriter
from PyQt5.QtWidgets import QFileDialog, QMessageBox

class ExcelExporter:
    """Excel export utility with formatting and multiple worksheets"""
    
    def __init__(self, parent=None):
        self.parent = parent
    
    def export_ledger(self, entries, summary_data, title="Transaction Ledger"):
        """
        Export ledger data to Excel with formatting
        
        Args:
            entries: List of entry tuples
            summary_data: Dictionary with summary information
            title: Report title
        """
        # Get save file location
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(
            self.parent, "Export to Excel", 
            f"Ledger_{datetime.datetime.now().strftime('%Y%m%d')}.xlsx",
            "Excel Files (*.xlsx);;All Files (*)", options=options
        )
        
        if not file_name:
            return False
        
        # Add .xlsx extension if not present
        if not file_name.endswith('.xlsx'):
            file_name += '.xlsx'
        
        try:
            # Create workbook
            workbook = xlsxwriter.Workbook(file_name)
            
            # Add worksheet
            worksheet = workbook.add_worksheet("Transactions")
            
            # Define formats
            header_format = workbook.add_format({
                'bold': True,
                'bg_color': '#4e73df',
                'color': 'white',
                'align': 'center',
                'valign': 'vcenter',
                'border': 1
            })
            
            title_format = workbook.add_format({
                'bold': True,
                'font_size': 16,
                'align': 'center',
                'valign': 'vcenter'
            })
            
            date_format = workbook.add_format({
                'num_format': 'yyyy-mm-dd',
                'align': 'center'
            })
            
            currency_format = workbook.add_format({
                'num_format': '$#,##0.00',
                'align': 'right'
            })
            
            total_format = workbook.add_format({
                'bold': True,
                'num_format': '$#,##0.00',
                'align': 'right',
                'top': 1,
                'bottom': 1
            })
            
            credit_format = workbook.add_format({
                'color': 'green',
                'align': 'center',
                'bold': True
            })
            
            debit_format = workbook.add_format({
                'color': 'red',
                'align': 'center',
                'bold': True
            })
            
            # Set column widths
            worksheet.set_column('A:A', 8)  # ID
            worksheet.set_column('B:B', 12)  # Date
            worksheet.set_column('C:C', 25)  # Customer
            worksheet.set_column('D:D', 25)  # Product
            worksheet.set_column('E:E', 10)  # Quantity
            worksheet.set_column('F:F', 12)  # Unit Price
            worksheet.set_column('G:G', 12)  # Total
            worksheet.set_column('H:H', 10)  # Type
            worksheet.set_column('I:I', 30)  # Notes
            
            # Add title
            worksheet.merge_range('A1:I1', title, title_format)
            worksheet.merge_range('A2:I2', f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", workbook.add_format({'align': 'center'}))
            
            # Write header row
            headers = ["ID", "Date", "Customer", "Product", "Quantity", "Unit Price", "Total", "Type", "Notes"]
            for col, header in enumerate(headers):
                worksheet.write(3, col, header, header_format)
            
            # Write data rows
            row = 4
            for entry in entries:
                worksheet.write(row, 0, entry[0])  # ID
                worksheet.write(row, 1, entry[1], date_format)  # Date
                worksheet.write(row, 2, entry[2])  # Customer
                worksheet.write(row, 3, entry[3])  # Product
                worksheet.write(row, 4, entry[4])  # Quantity
                worksheet.write(row, 5, entry[5], currency_format)  # Unit Price
                worksheet.write(row, 6, entry[6], currency_format)  # Total
                
                # Type (Credit/Debit)
                is_credit = entry[7]
                if is_credit:
                    worksheet.write(row, 7, "Credit", credit_format)
                else:
                    worksheet.write(row, 7, "Debit", debit_format)
                
                worksheet.write(row, 8, entry[8])  # Notes
                
                row += 1
            
            # Add summary section
            summary_row = row + 2
            worksheet.merge_range(f'A{summary_row}:F{summary_row}', "Summary", header_format)
            summary_row += 1
            
            worksheet.write(summary_row, 0, "Total Entries:")
            worksheet.write(summary_row, 1, summary_data.get('total_entries', 0))
            summary_row += 1
            
            worksheet.write(summary_row, 0, "Total Credit:")
            worksheet.write(summary_row, 1, summary_data.get('total_credit', 0), total_format)
            summary_row += 1
            
            worksheet.write(summary_row, 0, "Total Debit:")
            worksheet.write(summary_row, 1, summary_data.get('total_debit', 0), total_format)
            summary_row += 1
            
            worksheet.write(summary_row, 0, "Current Balance:")
            worksheet.write(summary_row, 1, summary_data.get('current_balance', 0), total_format)
            
            # Add chart sheet
            self.add_chart_sheet(workbook, entries)
            
            # Add summary sheet
            self.add_summary_sheet(workbook, summary_data)
            
            # Close workbook
            workbook.close()
            
            return True
            
        except Exception as e:
            QMessageBox.critical(self.parent, "Export Error", f"Failed to export to Excel: {str(e)}")
            return False
    
    def add_chart_sheet(self, workbook, entries):
        """Add a sheet with charts visualizing the data"""
        chart_sheet = workbook.add_worksheet("Charts")
        
        # Prepare data for charts
        months = {}
        customers = {}
        
        for entry in entries:
            date = entry[1]
            customer = entry[2]
            total = entry[6]
            is_credit = entry[7]
            
            # Extract month
            try:
                month = datetime.datetime.strptime(date, "%Y-%m-%d").strftime("%Y-%m")
            except:
                month = date[:7]  # Fall back to first 7 chars (YYYY-MM)
            
            # Update months data
            if month not in months:
                months[month] = {'credit': 0, 'debit': 0}
            
            if is_credit:
                months[month]['credit'] += total
            else:
                months[month]['debit'] += total
            
            # Update customers data
            if is_credit:  # Only count credits for customer distribution
                if customer not in customers:
                    customers[customer] = 0
                customers[customer] += total
        
        # Sort months chronologically
        sorted_months = sorted(months.keys())
        
        # Sort customers by total
        sorted_customers = sorted(customers.items(), key=lambda x: x[1], reverse=True)[:5]  # Top 5
        
        # Write months data
        chart_sheet.write(0, 0, "Month", workbook.add_format({'bold': True}))
        chart_sheet.write(0, 1, "Credit", workbook.add_format({'bold': True}))
        chart_sheet.write(0, 2, "Debit", workbook.add_format({'bold': True}))
        
        for i, month in enumerate(sorted_months):
            chart_sheet.write(i+1, 0, month)
            chart_sheet.write(i+1, 1, months[month]['credit'])
            chart_sheet.write(i+1, 2, months[month]['debit'])
        
        # Create monthly chart
        monthly_chart = workbook.add_chart({'type': 'column'})
        
        # Add data series
        monthly_chart.add_series({
            'name': 'Credit',
            'categories': ['Charts', 1, 0, len(sorted_months), 0],
            'values': ['Charts', 1, 1, len(sorted_months), 1],
            'fill': {'color': '#4e73df'}
        })
        
        monthly_chart.add_series({
            'name': 'Debit',
            'categories': ['Charts', 1, 0, len(sorted_months), 0],
            'values': ['Charts', 1, 2, len(sorted_months), 2],
            'fill': {'color': '#e74a3b'}
        })
        
        # Set chart title and labels
        monthly_chart.set_title({'name': 'Monthly Transactions'})
        monthly_chart.set_x_axis({'name': 'Month'})
        monthly_chart.set_y_axis({'name': 'Amount ($)'})
        
        # Insert chart
        chart_sheet.insert_chart('E1', monthly_chart, {'x_scale': 1.5, 'y_scale': 1.5})
        
        # Write customer data
        chart_sheet.write(0, 4, "Customer", workbook.add_format({'bold': True}))
        chart_sheet.write(0, 5, "Sales", workbook.add_format({'bold': True}))
        
        for i, (customer, total) in enumerate(sorted_customers):
            chart_sheet.write(i+1, 4, customer)
            chart_sheet.write(i+1, 5, total)
        
        # Create customer pie chart
        pie_chart = workbook.add_chart({'type': 'pie'})
        
        # Add data series
        pie_chart.add_series({
            'name': 'Customer Sales',
            'categories': ['Charts', 1, 4, len(sorted_customers), 4],
            'values': ['Charts', 1, 5, len(sorted_customers), 5],
        })
        
        # Set chart title
        pie_chart.set_title({'name': 'Sales by Customer'})
        
        # Insert chart
        chart_sheet.insert_chart('E18', pie_chart, {'x_scale': 1.5, 'y_scale': 1.5})
    
    def add_summary_sheet(self, workbook, summary_data):
        """Add a summary sheet with key metrics"""
        summary_sheet = workbook.add_worksheet("Summary")
        
        # Define formats
        title_format = workbook.add_format({
            'bold': True,
            'font_size': 16,
            'align': 'center',
            'valign': 'vcenter'
        })
        
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4e73df',
            'color': 'white',
            'align': 'center',
            'valign': 'vcenter',
            'border': 1
        })
        
        metric_format = workbook.add_format({
            'bold': True,
            'align': 'right',
            'border': 1
        })
        
        value_format = workbook.add_format({
            'num_format': '$#,##0.00',
            'align': 'right',
            'border': 1
        })
        
        count_format = workbook.add_format({
            'align': 'right',
            'border': 1
        })
        
        # Add title
        summary_sheet.merge_range('A1:B1', "Financial Summary", title_format)
        summary_sheet.merge_range('A2:B2', f"Generated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}", workbook.add_format({'align': 'center'}))
        
        # Set column widths
        summary_sheet.set_column('A:A', 25)
        summary_sheet.set_column('B:B', 15)
        
        # Add metrics
        row = 4
        summary_sheet.write(row, 0, "Metric", header_format)
        summary_sheet.write(row, 1, "Value", header_format)
        row += 1
        
        summary_sheet.write(row, 0, "Total Entries", metric_format)
        summary_sheet.write(row, 1, summary_data.get('total_entries', 0), count_format)
        row += 1
        
        summary_sheet.write(row, 0, "Total Credit", metric_format)
        summary_sheet.write(row, 1, summary_data.get('total_credit', 0), value_format)
        row += 1
        
        summary_sheet.write(row, 0, "Total Debit", metric_format)
        summary_sheet.write(row, 1, summary_data.get('total_debit', 0), value_format)
        row += 1
        
        summary_sheet.write(row, 0, "Net Balance", metric_format)
        summary_sheet.write(row, 1, summary_data.get('current_balance', 0), value_format)
        row += 1
        
        # Add more metrics if available
        if 'average_transaction' in summary_data:
            summary_sheet.write(row, 0, "Average Transaction", metric_format)
            summary_sheet.write(row, 1, summary_data.get('average_transaction', 0), value_format)
            row += 1
        
        if 'highest_transaction' in summary_data:
            summary_sheet.write(row, 0, "Highest Transaction", metric_format)
            summary_sheet.write(row, 1, summary_data.get('highest_transaction', 0), value_format)
            row += 1