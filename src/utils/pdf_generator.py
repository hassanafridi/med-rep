"""
Improved PDF Generation Utilities using ReportLab
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.pdfgen import canvas
import os
from datetime import datetime
from io import BytesIO
import base64

class ImprovedPDFGenerator:
    """Improved PDF generator that matches the HTML template design"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles to match the template"""
        # Purple color matching the template
        purple_color = colors.HexColor('#847DE6')
        
        # Header styles
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=12,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Normal'],
            fontSize=11,
            textColor=colors.white,
            backColor=purple_color,
            alignment=TA_LEFT,
            spaceBefore=0,
            spaceAfter=0,
            leftIndent=8,
            rightIndent=8,
            topPadding=4,
            bottomPadding=4,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyContact',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            spaceAfter=6
        ))
        
        self.styles.add(ParagraphStyle(
            name='DetailText',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=3
        ))
    
    def generate_invoice_pdf(self, invoice_data, output_path):
        """Generate PDF that matches the HTML template exactly"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=15*mm,
                leftMargin=15*mm,
                topMargin=15*mm,
                bottomMargin=15*mm
            )
            
            story = []
            purple_color = colors.HexColor('#847DE6')
            
            # Main title
            title = Paragraph("Bill/Cash Memo", self.styles['InvoiceTitle'])
            story.append(title)
            story.append(Spacer(1, 12))
            
            # Company header section
            company_data = []
            
            # Logo and company contact
            logo_cell = ""
            if invoice_data.get('company_logo'):
                logo_cell = f"<img src='{invoice_data['company_logo']}' width='60' height='30'/>"
            
            company_contact = invoice_data.get('company_contact', 'Company Contact')
            company_address = invoice_data.get('company_address', 'Company Address').replace('\n', '<br/>')
            
            company_data.append([
                logo_cell,
                f"{company_contact}<br/>{company_address}"
            ])
            
            company_table = Table(company_data, colWidths=[80*mm, 100*mm])
            company_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
            ]))
            
            story.append(company_table)
            story.append(Spacer(1, 6))
            
            # Section headers
            header_data = [["Bill To", "Transportation Details", "Invoice Details"]]
            
            header_table = Table(header_data, colWidths=[60*mm, 60*mm, 60*mm])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), purple_color),
                ('TEXTCOLOR', (0, 0), (-1, -1), colors.white),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))
            
            story.append(header_table)
            
            # Details section
            customer_info = invoice_data.get('customer_info', {})
            transport_info = invoice_data.get('transport_info', {})
            invoice_details = invoice_data.get('invoice_details', {})
            
            details_data = [[
                f"<b>{customer_info.get('name', '')}</b><br/>{customer_info.get('address', '').replace(chr(10), '<br/>')}",
                f"<b>Transport Name:</b> {transport_info.get('transport_name', '')}<br/>"
                f"<b>Delivery Date:</b> {transport_info.get('delivery_date', '')}<br/>"
                f"<b>Delivery location:</b> {transport_info.get('delivery_location', '')}",
                f"<b>Invoice No.:</b> {invoice_details.get('invoice_number', '')}<br/>"
                f"<b>Date:</b> {invoice_details.get('invoice_date', '')}"
            ]]
            
            details_table = Table(details_data, colWidths=[60*mm, 60*mm, 60*mm])
            details_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('BACKGROUND', (0, 0), (-1, -1), colors.white)
            ]))
            
            story.append(details_table)
            story.append(Spacer(1, 12))
            
            # Items table
            items_data = [['#', 'Item name', 'No.', 'MRP', 'Quantity', 'Rate', 'Discount', 'Amount']]
            
            total_amount = 0
            for i, item in enumerate(invoice_data.get('items', []), 1):
                amount = item.get('amount', 0)
                total_amount += amount
                
                item_name = item.get('product_name', '')
                batch_info = item.get('batch_number', 'N/A')
                if batch_info != 'N/A':
                    item_name += f"\n(Batch: {batch_info})"
                
                items_data.append([
                    str(i),
                    item_name,
                    item.get('product_id', 'N/A'),
                    f"{item.get('unit_price', 0):.0f}",
                    str(item.get('quantity', 0)),
                    f"{item.get('unit_price', 0):.0f}",
                    f"{item.get('discount', 0)}%",
                    f"{amount:.0f}"
                ])
            
            # Add total row
            items_data.append(['', '', '', '', '', '', 'Total', f"{total_amount:.0f}"])
            
            items_table = Table(items_data, colWidths=[8*mm, 45*mm, 20*mm, 20*mm, 20*mm, 20*mm, 20*mm, 25*mm])
            items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), purple_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 11),
                
                # Data rows
                ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
                ('ALIGN', (1, 1), (1, -2), 'LEFT'),  # Item name left aligned
                ('ALIGN', (-1, 1), (-1, -1), 'RIGHT'),  # Amount right aligned
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                
                # Total row
                ('BACKGROUND', (-2, -1), (-1, -1), purple_color),
                ('TEXTCOLOR', (-2, -1), (-1, -1), colors.white),
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
                ('ALIGN', (-2, -1), (-2, -1), 'RIGHT'),
                
                # Grid
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
            ]))
            
            story.append(items_table)
            story.append(Spacer(1, 12))
            
            # Amounts section (right-aligned)
            amounts_data = [
                ['Amounts'],
                ['Sub Total', f"{total_amount:.0f}"],
                ['Total', f"{total_amount:.0f}"],
                ['Received', '0.00'],
                ['Balance', f"{total_amount:.0f}"]
            ]
            
            # Create a table that spans full width but content is right-aligned
            amounts_table = Table(amounts_data, colWidths=[40*mm, 30*mm])
            amounts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), purple_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('SPAN', (0, 0), (-1, 0)),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 0), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('BACKGROUND', (-2, -1), (-1, -1), colors.HexColor('#F0F0F0')),
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold')
            ]))
            
            # Create a wrapper table to right-align the amounts section
            wrapper_data = [['', amounts_table]]
            wrapper_table = Table(wrapper_data, colWidths=[110*mm, 70*mm])
            wrapper_table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            story.append(wrapper_table)
            story.append(Spacer(1, 12))
            
            # Amount in words
            amount_words = self._amount_to_words(total_amount)
            amount_para = Paragraph(
                f"<para align='center' backColor='#847DE6' textColor='white' fontSize='11' fontName='Helvetica-Bold'>"
                f"Invoice Amount In Words<br/><br/>{amount_words}</para>",
                self.styles['Normal']
            )
            story.append(amount_para)
            story.append(Spacer(1, 12))
            
            # Terms and signature section
            terms_text = invoice_data.get('terms', '')
            company_name = invoice_data.get('company_name', 'Tru_pharma')
            
            terms_content = f"""
            <para fontSize='11' fontName='Helvetica-Bold' backColor='#847DE6' textColor='white' leftIndent='8' rightIndent='8' topPadding='4' bottomPadding='4'>Terms and Conditions</para>
            <br/>
            <para fontSize='9' alignment='justify'>{terms_text}<br/><br/>
            Form 2-A, as specified under Rules 19 and 30, pertains to the warranty provided under Section 23(1)(1) of the Drug Act 1976. 
            This document, issued by {company_name}, serves as an assurance of the quality and effectiveness of products. 
            The warranty ensures that the drugs manufactured by {company_name} comply with the prescribed standards and meet the necessary regulatory requirements. 
            By utilizing Form 2-A, {company_name} demonstrates its commitment to delivering safe and reliable pharmaceuticals to consumers. 
            This form acts as a legal document, emphasizing {company_name}'s responsibility and accountability in maintaining the highest standards in drug manufacturing and distribution.</para>
            """
            
            signature_content = f"""
            <para fontSize='10' alignment='center'>For: {company_name}<br/><br/><br/><br/>
            ____________________<br/>
            <b>Authorized Signatory</b></para>
            """
            
            terms_data = [[terms_content, signature_content]]
            terms_table = Table(terms_data, colWidths=[120*mm, 60*mm])
            terms_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
            ]))
            
            story.append(terms_table)
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
    
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