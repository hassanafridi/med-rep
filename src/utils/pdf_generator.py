"""
Professional PDF Generation Utilities using ReportLab
"""

from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import os
from datetime import datetime
from io import BytesIO
import base64

class PDFGenerator:
    """Professional PDF generator for invoices and reports"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles"""
        # Company header style
        self.styles.add(ParagraphStyle(
            name='CompanyHeader',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#8A2BE2'),
            alignment=TA_CENTER,
            spaceAfter=12
        ))
        
        # Invoice title style
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.white,
            backColor=colors.HexColor('#8A2BE2'),
            alignment=TA_CENTER,
            spaceAfter=12,
            borderPadding=8
        ))
        
        # Section header style
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.white,
            backColor=colors.HexColor('#8A2BE2'),
            alignment=TA_CENTER,
            spaceAfter=6,
            borderPadding=4
        ))
        
        # Address style
        self.styles.add(ParagraphStyle(
            name='Address',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=6
        ))
        
        # Amount words style
        self.styles.add(ParagraphStyle(
            name='AmountWords',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.white,
            backColor=colors.HexColor('#8A2BE2'),
            alignment=TA_CENTER,
            borderPadding=8
        ))
    
    def generate_invoice_pdf(self, invoice_data, output_path):
        """Generate professional pharmaceutical invoice PDF"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            story = []
            
            # Company logo and header
            if invoice_data.get('company_logo'):
                try:
                    # Handle both file paths and base64 data
                    if invoice_data['company_logo'].startswith('data:'):
                        # Base64 encoded image
                        image_data = invoice_data['company_logo'].split(',')[1]
                        img_bytes = base64.b64decode(image_data)
                        img = Image(BytesIO(img_bytes))
                    else:
                        # File path
                        img = Image(invoice_data['company_logo'])
                    
                    img.drawHeight = 30*mm
                    img.drawWidth = 60*mm
                    story.append(img)
                except:
                    pass
            
            # Company name
            company_name = Paragraph(invoice_data.get('company_name', 'Company Name'), self.styles['CompanyHeader'])
            story.append(company_name)
            
            # Invoice title
            invoice_title = Paragraph("Bill/Cash Memo", self.styles['InvoiceTitle'])
            story.append(invoice_title)
            story.append(Spacer(1, 12))
            
            # Create header table with customer, transport, and invoice details
            header_data = [
                [
                    self._format_section("Bill To", invoice_data.get('customer_info', {})),
                    self._format_section("Transportation Details", invoice_data.get('transport_info', {})),
                    self._format_section("Invoice Details", invoice_data.get('invoice_details', {}))
                ]
            ]
            
            header_table = Table(header_data, colWidths=[60*mm, 60*mm, 60*mm])
            header_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#8A2BE2')),
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#F5F5F5'))
            ]))
            
            story.append(header_table)
            story.append(Spacer(1, 12))
            
            # Items table
            items_data = [['#', 'Item Name', 'No.', 'MRP', 'Quantity', 'Rate', 'Discount', 'Amount']]
            
            total_amount = 0
            for i, item in enumerate(invoice_data.get('items', []), 1):
                amount = item.get('amount', 0)
                total_amount += amount
                
                items_data.append([
                    str(i),
                    f"{item.get('product_name', '')}\n(Batch: {item.get('batch_number', 'N/A')})",
                    item.get('product_id', 'N/A'),
                    f"{item.get('unit_price', 0):.0f}",
                    str(item.get('quantity', 0)),
                    f"{item.get('unit_price', 0):.0f}",
                    f"{item.get('discount', 0)}%",
                    f"{amount:.0f}"
                ])
            
            # Add total row
            items_data.append(['', '', '', '', '', '', 'Total', f"{total_amount:.0f}"])
            
            items_table = Table(items_data, colWidths=[15*mm, 45*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 25*mm])
            items_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8A2BE2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('ALIGN', (1, 1), (1, -2), 'LEFT'),  # Product name left aligned
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),  # Amount right aligned
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#666666')),
                ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#8A2BE2')),
                ('TEXTCOLOR', (-2, -1), (-1, -1), colors.white),
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold')
            ]))
            
            story.append(items_table)
            story.append(Spacer(1, 12))
            
            # Amounts section
            amounts_data = [
                ['Sub Total', f"{total_amount:.0f}"],
                ['Total', f"{total_amount:.0f}"],
                ['Received', '0.00'],
                ['Balance', f"{total_amount:.0f}"]
            ]
            
            amounts_table = Table(amounts_data, colWidths=[40*mm, 30*mm])
            amounts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8A2BE2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
                ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#F0F0F0')),
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold')
            ]))
            
            story.append(amounts_table)
            story.append(Spacer(1, 12))
            
            # Amount in words
            amount_words = self._amount_to_words(total_amount)
            amount_para = Paragraph(f"Invoice Amount In Words<br/><b>{amount_words}</b>", self.styles['AmountWords'])
            story.append(amount_para)
            story.append(Spacer(1, 12))
            
            # Terms and signature section
            terms_data = [
                [
                    self._format_terms(invoice_data.get('terms', '')),
                    self._format_signature(invoice_data.get('company_name', ''))
                ]
            ]
            
            terms_table = Table(terms_data, colWidths=[120*mm, 50*mm])
            terms_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 9),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#8A2BE2'))
            ]))
            
            story.append(terms_table)
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
    
    def _format_section(self, title, data):
        """Format a section for the header table"""
        content = f"<b style='color: white; background-color: #8A2BE2; padding: 2px;'>{title}</b><br/>"
        
        if title == "Bill To":
            content += f"<b>{data.get('name', '')}</b><br/>"
            content += data.get('address', '').replace('\n', '<br/>')
        elif title == "Transportation Details":
            content += f"<b>Transport Name:</b> {data.get('transport_name', '')}<br/>"
            content += f"<b>Delivery Date:</b> {data.get('delivery_date', '')}<br/>"
            content += f"<b>Delivery Location:</b> {data.get('delivery_location', '')}"
        elif title == "Invoice Details":
            content += f"<b>Invoice No.:</b> {data.get('invoice_number', '')}<br/>"
            content += f"<b>Date:</b> {data.get('invoice_date', '')}"
        
        return content
    
    def _format_terms(self, terms_text):
        """Format terms and conditions section"""
        content = "<b style='color: white; background-color: #8A2BE2; padding: 2px;'>Terms and Conditions</b><br/><br/>"
        content += terms_text.replace('\n', '<br/>')
        return content
    
    def _format_signature(self, company_name):
        """Format signature section"""
        content = f"For: {company_name}<br/><br/><br/><br/>"
        content += "_" * 20 + "<br/>"
        content += "<b>Authorized Signatory</b>"
        return content
    
    def _amount_to_words(self, amount):
        """Convert amount to words"""
        ones = ["", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine"]
        teens = ["ten", "eleven", "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
        tens = ["", "", "twenty", "thirty", "forty", "fifty", "sixty", "seventy", "eighty", "ninety"]
        
        try:
            amount = int(amount)
            if amount == 0:
                return "zero rupees"
            
            result = ""
            if amount >= 1000:
                thousands = amount // 1000
                if thousands > 0:
                    result += f"{ones[thousands]} thousand "
                    amount %= 1000
            
            if amount >= 100:
                hundreds = amount // 100
                if hundreds > 0:
                    result += f"{ones[hundreds]} hundred "
                    amount %= 100
            
            if amount >= 20:
                ten_digit = amount // 10
                ones_digit = amount % 10
                result += f"{tens[ten_digit]} "
                if ones_digit > 0:
                    result += f"{ones[ones_digit]} "
            elif amount >= 10:
                result += f"{teens[amount - 10]} "
            elif amount > 0:
                result += f"{ones[amount]} "
            
            return f"{result.strip()} rupees"
        except:
            return "amount not specified"
    
    def generate_report_pdf(self, report_data, output_path):
        """Generate professional report PDF"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=20*mm,
                leftMargin=20*mm,
                topMargin=20*mm,
                bottomMargin=20*mm
            )
            
            story = []
            
            # Report header
            title = Paragraph("Medical Rep Transaction System", self.styles['CompanyHeader'])
            story.append(title)
            
            subtitle = Paragraph(f"{report_data.get('report_type', 'Report')}", self.styles['InvoiceTitle'])
            story.append(subtitle)
            story.append(Spacer(1, 12))
            
            # Report metadata
            metadata_data = [
                ['Report Type:', report_data.get('report_type', '')],
                ['Date Range:', f"{report_data.get('from_date', '')} to {report_data.get('to_date', '')}"],
                ['Detail Level:', report_data.get('detail_level', '')],
                ['Generated:', f"{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"]
            ]
            
            metadata_table = Table(metadata_data, colWidths=[40*mm, 120*mm])
            metadata_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (0, -1), colors.HexColor('#F5F5F5')),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC'))
            ]))
            
            story.append(metadata_table)
            story.append(Spacer(1, 20))
            
            # Report table
            table_data = report_data.get('table_data', [])
            if table_data:
                # Calculate column widths based on content
                num_cols = len(table_data[0]) if table_data else 1
                col_width = (A4[0] - 40*mm) / num_cols
                col_widths = [col_width] * num_cols
                
                report_table = Table(table_data, colWidths=col_widths)
                report_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8A2BE2')),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 8),
                    ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#CCCCCC')),
                    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F8F8')])
                ]))
                
                story.append(report_table)
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating report PDF: {e}")
            return False
