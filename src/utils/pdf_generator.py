"""
Improved PDF Generation Utilities using ReportLab
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT, TA_JUSTIFY
from reportlab.pdfgen import canvas
import os
from datetime import datetime
from io import BytesIO
import base64

class ImprovedPDFGenerator:
    """PDF generator that exactly matches the HTML template design"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Setup custom paragraph styles to match the template"""
        # Purple color matching the template
        self.purple_color = colors.HexColor('#847DE6')
        self.light_purple = colors.HexColor('#F4F0FF')
        
        # Header styles
        self.styles.add(ParagraphStyle(
            name='InvoiceTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.black,
            alignment=TA_CENTER,
            spaceAfter=0,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyLogo',
            parent=self.styles['Normal'],
            fontSize=20,
            textColor=self.purple_color,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        ))
        
        self.styles.add(ParagraphStyle(
            name='CompanyContact',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_RIGHT,
            spaceAfter=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='DetailText',
            parent=self.styles['Normal'],
            fontSize=10,
            alignment=TA_LEFT,
            spaceAfter=0
        ))
        
        self.styles.add(ParagraphStyle(
            name='TermsText',
            parent=self.styles['Normal'],
            fontSize=9,
            alignment=TA_JUSTIFY,
            spaceAfter=0,
            leading=11
        ))
    
    def generate_invoice_pdf(self, invoice_data, output_path):
        """Generate PDF that exactly matches the HTML template"""
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=10*mm,
                leftMargin=10*mm,
                topMargin=10*mm,
                bottomMargin=10*mm
            )
            
            story = []
            
            # Main container with border
            container_table = Table([['CONTENT_PLACEHOLDER']], colWidths=[190*mm])
            container_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 2, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0)
            ]))
            
            # Build the inner content
            inner_content = []
            
            # 1. Header
            header = Paragraph("Bill/Cash Memo", self.styles['InvoiceTitle'])
            inner_content.append(header)
            inner_content.append(Spacer(1, 10))
            
            # 2. Company header
            company_data = [[
                Paragraph("Tru-Pharma", self.styles['CompanyLogo']),
                Paragraph(f"{invoice_data.get('company_contact', '')}<br/>{invoice_data.get('company_address', '').replace(chr(10), '<br/>')}", 
                         self.styles['CompanyContact'])
            ]]
            
            company_table = Table(company_data, colWidths=[95*mm, 95*mm])
            company_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 15),
                ('RIGHTPADDING', (0, 0), (-1, -1), 15),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10)
            ]))
            
            inner_content.append(company_table)
            
            # 3. Section headers
            header_cells = [
                Paragraph("<b>Bill To</b>", ParagraphStyle('SectionHeaderStyle', 
                    fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT)),
                Paragraph("<b>Transportation Details</b>", ParagraphStyle('SectionHeaderStyle', 
                    fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT)),
                Paragraph("<b>Invoice Details</b>", ParagraphStyle('SectionHeaderStyle', 
                    fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT))
            ]
            
            header_table = Table([header_cells], colWidths=[63.33*mm, 63.33*mm, 63.33*mm])
            header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.purple_color),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))
            
            inner_content.append(header_table)
            
            # 4. Details section
            customer_info = invoice_data.get('customer_info', {})
            transport_info = invoice_data.get('transport_info', {})
            invoice_details = invoice_data.get('invoice_details', {})
            
            customer_text = f"<b>{customer_info.get('name', '')}</b><br/>{customer_info.get('address', '').replace(chr(10), '<br/>')}"
            transport_text = (f"<b>Transport Name:</b> {transport_info.get('transport_name', '')}<br/>"
                            f"<b>Delivery Date:</b> {transport_info.get('delivery_date', '')}<br/>"
                            f"<b>Delivery location:</b> {transport_info.get('delivery_location', '')}")
            invoice_text = (f"<b>Invoice No.:</b> {invoice_details.get('invoice_number', '')}<br/>"
                          f"<b>Date:</b> {invoice_details.get('invoice_date', '')}")
            
            details_cells = [
                Paragraph(customer_text, ParagraphStyle('DetailStyle', fontSize=10, alignment=TA_LEFT)),
                Paragraph(transport_text, ParagraphStyle('DetailStyle', fontSize=10, alignment=TA_LEFT)),
                Paragraph(invoice_text, ParagraphStyle('DetailStyle', fontSize=10, alignment=TA_LEFT))
            ]
            
            details_table = Table([details_cells], colWidths=[63.33*mm, 63.33*mm, 63.33*mm])
            details_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'TOP')
            ]))
            
            inner_content.append(details_table)
            
            # 5. Items table
            items_data = [['#', 'Item name', 'MRP', 'Quantity', 'Rate', 'Discount', 'Amount']]
            
            total_amount = 0
            for i, item in enumerate(invoice_data.get('items', []), 1):
                amount = item.get('amount', 0)
                total_amount += amount
                
                # Include batch number in item name
                item_name = item.get('product_name', '')
                batch_info = item.get('batch_number', '')
                
                if batch_info and batch_info != 'N/A':
                    item_name += f" (Batch: {batch_info})"
                
                # Calculate discount (if any)
                discount_percent = item.get('discount', 0)
                # Use 'amount' if 'total' doesn't exist, with fallback calculation
                item_total = item.get('total', item.get('amount', item.get('quantity', 0) * item.get('unit_price', 0)))
                discount_amount = item_total * (discount_percent / 100)
                final_amount = item_total - discount_amount
                
                # Enhanced MRP and rate handling with proper validation
                mrp_value = item.get('mrp', 0)
                unit_price_value = item.get('unit_price', 0)
                
                print(f"PDF Generator - Item {i}: {item_name}")
                print(f"  Raw MRP: {mrp_value} (type: {type(mrp_value)}), Raw Unit Price: {unit_price_value} (type: {type(unit_price_value)})")
                print(f"  Item Total: {item_total}, Final Amount: {final_amount}")
                
                # Convert to float for calculations but validate first
                try:
                    mrp_float = float(mrp_value) if mrp_value is not None else 0.0
                    unit_price_float = float(unit_price_value) if unit_price_value is not None else 0.0
                except (ValueError, TypeError):
                    print(f"  Warning: Could not convert MRP/unit_price to float, using defaults")
                    mrp_float = 0.0
                    unit_price_float = 0.0
                
                # Enhanced MRP validation and fallback logic
                if mrp_float <= 0:
                    if unit_price_float > 0:
                        # Calculate MRP as 120% of unit price only when MRP is missing/zero
                        mrp_float = unit_price_float * 1.2
                        print(f"  MRP was missing/zero, calculated fallback: {mrp_float:.2f}")
                    else:
                        # Both are zero/invalid, use a minimum value
                        mrp_float = 1.0
                        print(f"  Both MRP and unit price invalid, using minimum MRP: {mrp_float:.2f}")
                else:
                    print(f"  Using provided MRP: {mrp_float:.2f}")
                
                # Ensure unit_price has a minimum value if zero
                if unit_price_float <= 0:
                    unit_price_float = mrp_float * 0.8  # Unit price as 80% of MRP
                    print(f"  Unit price was zero, calculated as 80% of MRP: {unit_price_float:.2f}")
                
                # Format for display with consistent decimal places
                mrp_display = f"{mrp_float:.0f}"  # Show MRP without decimals for clean display
                rate_display = f"{unit_price_float:.0f}"  # Show rate without decimals for clean display
                
                print(f"  Final - MRP Display: {mrp_display}, Rate Display: {rate_display}")
                
                items_data.append([
                    str(i),
                    item_name,
                    mrp_display,  # Market retail price - validated and formatted
                    str(item.get('quantity', 0)),
                    rate_display,  # Wholesale/billing rate - validated and formatted
                    f"{item.get('discount', 0)}%",
                    f"{final_amount:.0f}"  # Amount without decimals for clean display
                ])
            
            # Add total row with float precision
            items_data.append(['', '', '', '', '', 'Total', f"{total_amount:.2f}"])
            
            # Adjusted column widths without the "No." column
            items_table = Table(items_data, colWidths=[8*mm, 85*mm, 18*mm, 18*mm, 18*mm, 18*mm, 25*mm])
            items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), self.purple_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                
                # Data rows
                ('ALIGN', (0, 1), (-1, -2), 'CENTER'),
                ('ALIGN', (1, 1), (1, -2), 'LEFT'),  # Item name left aligned
                ('FONTSIZE', (0, 1), (-1, -1), 9),  # Smaller font for better fit
                ('VALIGN', (0, 1), (-1, -1), 'MIDDLE'),
                
                # Total row
                ('ALIGN', (-2, -1), (-1, -1), 'RIGHT'),
                ('FONTNAME', (-2, -1), (-1, -1), 'Helvetica-Bold'),
                
                # Grid and padding
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))
            
            inner_content.append(items_table)
            inner_content.append(Spacer(1, 0))
            
            # 6. Amounts section and Amount in words (side by side)
            # Get received and balance amounts from invoice data
            received_amount = invoice_data.get('received_amount', 0.0)
            balance_amount = invoice_data.get('balance_amount', total_amount)
            
            amounts_data = [
                [Paragraph('<b>Amounts</b>', ParagraphStyle('AmountHeader', fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER))],
                ['Sub Total', f"{total_amount:.0f}"],
                ['Total', f"{total_amount:.0f}"],
                ['Received', f"{received_amount:.2f}"],
                ['Balance', f"{balance_amount:.0f}"]
            ]
            
            amounts_table = Table(amounts_data, colWidths=[40*mm, 30*mm])
            amounts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.purple_color),
                ('SPAN', (0, 0), (-1, 0)),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')  # Make balance row bold
            ]))
            
            # Amount in words - use balance amount for words conversion
            amount_for_words = balance_amount if balance_amount > 0 else total_amount
            amount_words = self._amount_to_words(amount_for_words)
            
            words_header = Paragraph('<b>Invoice Amount In Words</b>', 
                ParagraphStyle('WordsHeader', fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER))
            words_content = Paragraph(amount_words, 
                ParagraphStyle('WordsContent', fontSize=11, fontName='Helvetica-Bold', alignment=TA_CENTER))
            
            words_data = [[words_header], [words_content]]
            words_table = Table(words_data, colWidths=[120*mm])
            words_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.purple_color),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#F8F8F8')),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8)
            ]))
            
            # Combine amounts and words
            amounts_words_data = [[words_table, amounts_table]]
            amounts_words_table = Table(amounts_words_data, colWidths=[120*mm, 70*mm])
            amounts_words_table.setStyle(TableStyle([
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0)
            ]))
            
            inner_content.append(amounts_words_table)
            
            # 7. Terms and signature section
            company_name = invoice_data.get('company_name', 'Tru_pharma')
            
            terms_header = Paragraph('<b>Terms and Conditions</b>', 
                ParagraphStyle('TermsHeader', fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT))
            
            terms_text = (f"Form 2-A, as specified under Rules 19 and 30, pertains to the warranty provided under Section 23(1)(1) of the Drug Act 1976. "
                         f"This document, issued by {company_name}, serves as an assurance of the quality and effectiveness of products. "
                         f"The warranty ensures that the drugs manufactured by {company_name} comply with the prescribed standards and meet the necessary regulatory requirements. "
                         f"By utilizing Form 2-A, {company_name} demonstrates its commitment to delivering safe and reliable pharmaceuticals to consumers. "
                         f"This form acts as a legal document, emphasizing {company_name}'s responsibility and accountability in maintaining the highest standards in drug manufacturing and distribution.")
            
            terms_content = Paragraph(terms_text, self.styles['TermsText'])
            
            signature_content = Paragraph(f"""For: {company_name}
            <br/><br/><br/><br/>
            ____________________<br/>
            <b>Authorized Signatory</b>""", 
                ParagraphStyle('SignatureStyle', fontSize=10, alignment=TA_CENTER))
            
            # Terms header spans both columns
            terms_header_table = Table([[terms_header]], colWidths=[190*mm])
            terms_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.purple_color),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 5),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 5)
            ]))
            
            # Terms content and signature
            terms_content_table = Table([[terms_content, signature_content]], colWidths=[126.67*mm, 63.33*mm])
            terms_content_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 12),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 9),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 11),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('ALIGN', (1, 0), (1, 0), 'CENTER')
            ]))
            
            inner_content.append(terms_header_table)
            inner_content.append(terms_content_table)
            
            # Create the final story
            story.extend(inner_content)
            
            # Build PDF
            doc.build(story)
            return True
            
        except Exception as e:
            print(f"Error generating PDF: {e}")
            import traceback
            traceback.print_exc()
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


# Backward compatibility - alias for the original class name
class PDFGenerator(ImprovedPDFGenerator):
    """Backward compatibility alias for PDFGenerator"""
    
    def __init__(self):
        super().__init__()
    
    def generate_invoice_pdf(self, invoice_data, output_path):
        """Generate PDF using the improved generator"""
        return super().generate_invoice_pdf(invoice_data, output_path)
    
    def amount_to_words(self, amount):
        """Convert amount to words - backward compatibility method"""
        return self._amount_to_words(amount)