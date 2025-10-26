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

            # 1. Company header - Dynamic with logo or company name
            # Get header contact info (dynamic)
            header_contact_name = invoice_data.get('header_contact_name', 'Mr. Behzad Aslam')
            header_contact_phone = invoice_data.get('header_contact_phone', '03339911914')
            header_email = invoice_data.get('header_email', 'trupharmaceuticalfsd@gmail.com')
            use_company_name = invoice_data.get('use_company_name', True)
            logo_data = invoice_data.get('logo_data', None)

            # Left side - Logo or Company Name
            if use_company_name or not logo_data:
                # Use company name text
                left_content = Paragraph("<font size=24><b>Tru-Pharma</b></font>", self.styles['CompanyLogo'])
            else:
                # Use logo image
                try:
                    import base64
                    from io import BytesIO
                    logo_bytes = base64.b64decode(logo_data)
                    logo_image = Image(BytesIO(logo_bytes))
                    # Scale logo to fit
                    logo_image.drawHeight = 20*mm
                    logo_image.drawWidth = 40*mm
                    left_content = logo_image
                except Exception as e:
                    print(f"Error loading logo: {e}")
                    # Fallback to company name
                    left_content = Paragraph("<font size=24><b>Tru-Pharma</b></font>", self.styles['CompanyLogo'])

            # Right side - Dynamic contact info
            header_contact_text = f"<b>{header_contact_name}</b>  {header_contact_phone}<br/>{header_email}"
            right_content = Paragraph(header_contact_text, self.styles['CompanyContact'])

            company_data = [[left_content, right_content]]

            company_table = Table(company_data, colWidths=[95*mm, 95*mm])
            company_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
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
            
            # 5. Items table (matching image layout - no MRP column)
            items_data = [[
                Paragraph('<b>#</b>', ParagraphStyle('TableHeader', fontSize=10, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
                Paragraph('<b>Item name</b>', ParagraphStyle('TableHeader', fontSize=10, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
                Paragraph('<b>Quantity</b>', ParagraphStyle('TableHeader', fontSize=10, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
                Paragraph('<b>Rate</b>', ParagraphStyle('TableHeader', fontSize=10, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
                Paragraph('<b>Discount</b>', ParagraphStyle('TableHeader', fontSize=10, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)),
                Paragraph('<b>Amount</b>', ParagraphStyle('TableHeader', fontSize=10, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER))
            ]]

            total_amount = 0
            for i, item in enumerate(invoice_data.get('items', []), 1):
                # Get unit price and quantity
                unit_price_value = item.get('unit_price', 0)
                quantity = item.get('quantity', 0)

                # Convert to float for calculations
                try:
                    unit_price_float = float(unit_price_value) if unit_price_value is not None else 0.0
                    quantity_float = float(quantity) if quantity is not None else 0.0
                except (ValueError, TypeError):
                    unit_price_float = 0.0
                    quantity_float = 0.0

                # Calculate amount before discount
                item_total = quantity_float * unit_price_float

                # Calculate discount
                discount_percent = item.get('discount', 0)
                discount_amount = item_total * (discount_percent / 100)
                final_amount = item_total - discount_amount

                total_amount += final_amount

                # Item name (without batch for cleaner look matching image)
                item_name = item.get('product_name', '')

                items_data.append([
                    str(i),
                    item_name,
                    str(int(quantity_float)),
                    str(int(unit_price_float)),
                    f"{int(discount_percent)}%",
                    str(int(final_amount))
                ])

            # Add empty rows to fill space (like in the image)
            for _ in range(max(0, 2 - len(invoice_data.get('items', [])))):
                items_data.append(['', '', '', '', '', ''])

            # Add total row
            items_data.append([
                '',
                Paragraph('<b>Total</b>', ParagraphStyle('TotalLabel', fontSize=10, fontName='Helvetica-Bold', alignment=TA_LEFT)),
                '', '', '',
                str(int(total_amount))
            ])

            # Column widths matching image proportions
            items_table = Table(items_data, colWidths=[10*mm, 95*mm, 23*mm, 20*mm, 20*mm, 22*mm])
            items_table.setStyle(TableStyle([
                # Header row
                ('BACKGROUND', (0, 0), (-1, 0), self.purple_color),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

                # Data rows
                ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # # column centered
                ('ALIGN', (1, 1), (1, -2), 'LEFT'),     # Item name left aligned
                ('ALIGN', (2, 1), (-1, -2), 'CENTER'),  # Quantity, Rate, Discount, Amount centered
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),

                # Total row
                ('ALIGN', (1, -1), (1, -1), 'LEFT'),
                ('ALIGN', (-1, -1), (-1, -1), 'CENTER'),
                ('FONTNAME', (1, -1), (-1, -1), 'Helvetica-Bold'),

                # Grid and padding
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 6),
                ('RIGHTPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6)
            ]))
            
            inner_content.append(items_table)
            inner_content.append(Spacer(1, 0))
            
            # 6. Amounts section (matching image layout)
            # Get received and balance amounts from invoice data
            received_amount = invoice_data.get('received_amount', 0.0)
            balance_amount = invoice_data.get('balance_amount', total_amount)

            # Left side - Invoice Amount in Words
            amount_words = self._amount_to_words(int(total_amount))
            words_header = Paragraph('<b>Invoice Amount In Words</b>',
                ParagraphStyle('WordsHeader', fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT))

            words_data = [[words_header], ['']]
            words_table = Table(words_data, colWidths=[120*mm], rowHeights=[7*mm, 15*mm])
            words_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.purple_color),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('RIGHTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE')
            ]))

            # Right side - Amounts
            amounts_data = [
                [Paragraph('<b>Amounts</b>', ParagraphStyle('AmountHeader', fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_CENTER)), ''],
                ['Sub Total', str(int(total_amount))],
                ['Total', str(int(total_amount))],
                ['Received', f"{received_amount:.2f}"],
                ['Balance', str(int(balance_amount))]
            ]

            amounts_table = Table(amounts_data, colWidths=[35*mm, 35*mm])
            amounts_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), self.purple_color),
                ('SPAN', (0, 0), (-1, 0)),
                ('ALIGN', (0, 1), (0, -1), 'LEFT'),
                ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
                ('FONTSIZE', (0, 1), (-1, -1), 11),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold')
            ]))

            # Combine amounts and words (words on left, amounts on right)
            amounts_words_data = [[words_table, amounts_table]]
            amounts_words_table = Table(amounts_words_data, colWidths=[120*mm, 70*mm])
            amounts_words_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (0, 0), 'LEFT'),
                ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
                ('RIGHTPADDING', (0, 0), (-1, -1), 0),
                ('TOPPADDING', (0, 0), (-1, -1), 0),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 0)
            ]))

            inner_content.append(amounts_words_table)
            
            # 7. Terms and signature section (matching image layout)
            company_name = invoice_data.get('company_name', 'Tru_Pharma')

            terms_header = Paragraph('<b>Terms and Conditions</b>',
                ParagraphStyle('TermsHeader', fontSize=11, textColor=colors.white, fontName='Helvetica-Bold', alignment=TA_LEFT))

            terms_text = (f"Form 2-A, as specified under Rules 19 and 30, pertains to the warranty "
                         f"provided under Section 23(1)(1) of the Drug Act 1976. This document, "
                         f"issued by {company_name}, serves as an assurance of the quality and "
                         f"effectiveness of their products. The warranty ensures that the drugs "
                         f"manufactured by {company_name} comply with the prescribed standards and "
                         f"meet the necessary regulatory requirements. By utilizing Form 2-A, "
                         f"{company_name} demonstrates its commitment to delivering safe and reliable "
                         f"pharmaceuticals to consumers. This form acts as a legal document, "
                         f"emphasizing {company_name}'s responsibility and accountability in "
                         f"maintaining the highest standards in drug manufacturing and distribution.")

            terms_content = Paragraph(terms_text, self.styles['TermsText'])

            # Signature section matching image - optional signatory
            signature_name = invoice_data.get('authorized_signatory', '')

            if signature_name:
                # Signatory name provided
                signature_content = Paragraph(f"""<para alignment="center">For : {company_name}
                <br/><br/><br/><br/>
                <b>{signature_name}</b><br/>
                <b>Authorized Signatory</b></para>""",
                    ParagraphStyle('SignatureStyle', fontSize=10, alignment=TA_CENTER))
            else:
                # No signatory - show blank line with underline
                signature_content = Paragraph(f"""<para alignment="center">For : {company_name}
                <br/><br/><br/><br/>
                ____________________<br/>
                <b>Authorized Signatory</b></para>""",
                    ParagraphStyle('SignatureStyle', fontSize=10, alignment=TA_CENTER))

            # Terms header spans both columns
            terms_header_table = Table([[terms_header]], colWidths=[190*mm])
            terms_header_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), self.purple_color),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4)
            ]))

            # Terms content and signature
            terms_content_table = Table([[terms_content, signature_content]], colWidths=[126.67*mm, 63.33*mm])
            terms_content_table.setStyle(TableStyle([
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 10),
                ('RIGHTPADDING', (0, 0), (-1, -1), 10),
                ('TOPPADDING', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
                ('VALIGN', (0, 0), (0, 0), 'TOP'),
                ('VALIGN', (1, 0), (1, 0), 'MIDDLE'),
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