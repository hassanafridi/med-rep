"""
Auto Invoice PDF Generator for MedRep
Automatically generates Tru-Pharma style invoice when new entry is saved
"""

import os
from datetime import datetime
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from num2words import num2words


class AutoInvoiceGenerator:
    """
    Automatically generates Tru-Pharma style invoices when entries are saved
    """
    
    def __init__(self, invoice_folder="invoices"):
        self.invoice_folder = invoice_folder
        self.company_info = {
            'name': 'Tru-Pharma',
            'email': 'trupharmaceuticalfsd@gmail.com',
            'logo_path': None
        }
        
        # Create invoice folder if it doesn't exist
        if not os.path.exists(self.invoice_folder):
            os.makedirs(self.invoice_folder)
    
    def generate_invoice_from_entry(self, entry_data, db_connection=None):
        """
        Generate invoice from new entry data
        
        Args:
            entry_data: Dictionary containing the entry information
            db_connection: Database connection to fetch additional data
            
        Returns:
            str: Path to the generated PDF file
        """
        # Generate invoice data from entry
        invoice_data = self._prepare_invoice_data(entry_data, db_connection)
        
        # Generate filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        customer_name = invoice_data['customer_name'].replace(' ', '_')[:20]
        filename = f"INV_{invoice_data['invoice_number']}_{customer_name}_{timestamp}.pdf"
        filepath = os.path.join(self.invoice_folder, filename)
        
        # Generate PDF
        self._create_pdf(invoice_data, filepath)
        
        return filepath
    
    def _prepare_invoice_data(self, entry_data, db_connection):
        """
        Convert entry data to invoice format
        """
        # Generate invoice number (you can customize this logic)
        invoice_number = self._generate_invoice_number(db_connection)
        
        # Extract customer address if available
        customer_address = ""
        if db_connection and entry_data.get('customer_id'):
            try:
                cursor = db_connection.cursor()
                cursor.execute("SELECT address FROM customers WHERE id = ?", 
                             (entry_data['customer_id'],))
                result = cursor.fetchone()
                if result:
                    customer_address = result[0] or ""
            except:
                pass
        
        # Handle multiple items or single item
        items = []
        if 'items' in entry_data and isinstance(entry_data['items'], list):
            # Multiple products
            for item in entry_data['items']:
                items.append({
                    'name': item.get('product_name', 'Medical Supplies'),
                    'quantity': item.get('quantity', 1),
                    'rate': item.get('unit_price', 0),
                    'discount': item.get('discount', 0),
                    'amount': item.get('amount', 0)
                })
        else:
            # Single product (backward compatibility)
            quantity = entry_data.get('quantity', 1)
            unit_price = entry_data.get('unit_price', 0)
            discount = entry_data.get('discount', 0)
            
            amount = quantity * unit_price
            if discount > 0:
                amount = amount * (1 - discount / 100)
            
            items.append({
                'name': entry_data.get('product_name', 'Medical Supplies'),
                'quantity': quantity,
                'rate': unit_price,
                'discount': discount,
                'amount': amount
            })
        
        # Calculate totals
        subtotal = sum(item['amount'] for item in items)
        total = subtotal
        
        # Prepare invoice data
        invoice_data = {
            'customer_name': entry_data.get('customer_name', 'Cash Customer'),
            'customer_address': customer_address,
            'transport_name': entry_data.get('transport_name', 'N/A'),
            'delivery_date': entry_data.get('delivery_date', entry_data.get('date', datetime.now().strftime('%d-%m-%y'))),
            'delivery_location': entry_data.get('delivery_location', customer_address),
            'invoice_number': invoice_number,
            'invoice_date': datetime.now().strftime('%d-%m-%y'),
            'items': items,
            'subtotal': subtotal,
            'total': total,
            'received': 0.00,
            'balance': total,
            'terms': None  # Will use default
        }
        
        return invoice_data
    
    def _generate_invoice_number(self, db_connection):
        """
        Generate unique invoice number
        """
        # Try to get last invoice number from database
        last_number = 0
        if db_connection:
            try:
                cursor = db_connection.cursor()
                cursor.execute("""
                    SELECT MAX(CAST(SUBSTR(notes, INSTR(notes, 'INV-') + 4, 
                           INSTR(SUBSTR(notes, INSTR(notes, 'INV-') + 4), ' ') - 1) AS INTEGER))
                    FROM entries 
                    WHERE notes LIKE '%INV-%'
                """)
                result = cursor.fetchone()
                if result and result[0]:
                    last_number = result[0]
            except:
                pass
        
        return str(last_number + 1).zfill(4)
    
    def _create_pdf(self, invoice_data, output_path):
        """
        Create the PDF invoice
        """
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20,
            leftMargin=20,
            topMargin=30,
            bottomMargin=30
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        header_style = ParagraphStyle(
            'HeaderStyle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#4B0082'),
            fontName='Helvetica-Bold',
            alignment=TA_LEFT
        )
        
        normal_style = ParagraphStyle(
            'NormalStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.black,
            fontName='Helvetica'
        )
        
        # Company header
        header_data = [[
            Paragraph(f"<font size='20' color='#4B0082'><b>{self.company_info['name']}</b></font>", header_style),
            Paragraph(self.company_info['email'], normal_style)
        ]]
        
        header_table = Table(header_data, colWidths=[3*inch, 4*inch])
        header_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ]))
        
        elements.append(header_table)
        elements.append(Spacer(1, 20))
        
        # Bill To section
        bill_to_data = [
            [Paragraph("<b>Bill To</b>", header_style), 
             Paragraph("<b>Transportation Details</b>", header_style), 
             Paragraph("<b>Invoice Details</b>", header_style)]
        ]
        
        customer_info = f"<b>{invoice_data['customer_name']}</b>"
        if invoice_data.get('customer_address'):
            customer_info += f"<br/>{invoice_data['customer_address']}"
        
        transport_info = f"Transport Name: <b>{invoice_data.get('transport_name', 'N/A')}</b><br/>"
        transport_info += f"Delivery Date: <b>{invoice_data.get('delivery_date', 'N/A')}</b><br/>"
        transport_info += f"Delivery location: <b>{invoice_data.get('delivery_location', 'N/A')}</b>"
        
        invoice_info = f"Invoice No. <b>{invoice_data['invoice_number']}</b><br/>"
        invoice_info += f"Date: <b>{invoice_data['invoice_date']}</b>"
        
        bill_to_data.append([
            Paragraph(customer_info, normal_style),
            Paragraph(transport_info, normal_style),
            Paragraph(invoice_info, normal_style)
        ])
        
        bill_to_table = Table(bill_to_data, colWidths=[2.3*inch, 2.5*inch, 2.2*inch])
        bill_to_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#E6E6FA')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#4B0082')),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D3D3D3')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white]),
        ]))
        
        elements.append(bill_to_table)
        elements.append(Spacer(1, 20))
        
        # Items table
        items_data = [
            ['#', 'Item name', 'Quantity', 'Rate', 'Discount', 'Amount']
        ]
        
        for idx, item in enumerate(invoice_data['items'], 1):
            items_data.append([
                str(idx),
                item['name'],
                str(item['quantity']),
                f"{item['rate']:.1f}",
                f"{item['discount']}%",
                f"{item['amount']:.1f}"
            ])
        
        items_data.append(['', '', '', '', 'Total', f"{invoice_data['subtotal']:.1f}"])
        
        items_table = Table(
            items_data,
            colWidths=[0.5*inch, 3*inch, 1*inch, 1*inch, 1*inch, 1.5*inch]
        )
        
        items_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9999FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),
            ('ALIGN', (2, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -2), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#F5F5F5')]),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 11),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#E6E6FA')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D3D3D3')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ]))
        
        elements.append(items_table)
        elements.append(Spacer(1, 20))
        
        # Amounts summary
        amounts_data = [
            [Paragraph('<b>Amounts</b>', header_style), '']
        ]
        
        amounts_details = [
            ('Sub Total', f"{invoice_data['subtotal']:.1f}"),
            ('Total', f"{invoice_data['total']:.1f}"),
            ('Received', f"{invoice_data.get('received', 0.00):.2f}"),
            ('Balance', f"{invoice_data['balance']:.1f}")
        ]
        
        for label, value in amounts_details:
            amounts_data.append([label, value])
        
        amounts_table = Table(amounts_data, colWidths=[1.5*inch, 1.5*inch])
        amounts_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9999FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (1, 0)),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D3D3D3')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        container_data = [[Spacer(1, 1), amounts_table]]
        container_table = Table(container_data, colWidths=[4*inch, 3*inch])
        
        elements.append(container_table)
        elements.append(Spacer(1, 20))
        
        # Invoice amount in words
        amount_words = self._amount_to_words(invoice_data['total'])
        words_data = [
            [Paragraph('<b>Invoice Amount in Words</b>', header_style)],
            [Paragraph(amount_words, normal_style)]
        ]
        
        words_table = Table(words_data, colWidths=[7*inch])
        words_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9999FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#D3D3D3')),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(words_table)
        elements.append(Spacer(1, 20))
        
        # Terms and Conditions
        terms_text = self._get_default_terms()
        terms_data = [
            [Paragraph('<b>Terms and Conditions</b>', header_style), '']
        ]
        
        terms_data.append([Paragraph(terms_text, normal_style), ''])
        
        signature_data = [
            ['', Paragraph('<b>For : Tru_Pharma</b>', header_style)],
            ['', ''],
            ['', ''],
            ['', Paragraph('<b>Authorized Signatory</b>', normal_style)]
        ]
        
        terms_table = Table(terms_data + signature_data, colWidths=[4.5*inch, 2.5*inch])
        terms_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#9999FF')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('SPAN', (0, 0), (1, 0)),
            ('ALIGN', (0, 0), (-1, 0), 'LEFT'),
            ('ALIGN', (1, -4), (1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, 1), 0.5, colors.HexColor('#D3D3D3')),
            ('LINEBELOW', (1, -2), (1, -2), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('VALIGN', (0, 1), (0, 1), 'TOP'),
        ]))
        
        elements.append(terms_table)
        
        # Build PDF
        doc.build(elements)
    
    def _amount_to_words(self, amount):
        """Convert amount to words"""
        try:
            whole = int(amount)
            decimal = int((amount - whole) * 100)
            
            words = num2words(whole, lang='en_IN').replace(',', '').title()
            if decimal > 0:
                words += f" and {num2words(decimal, lang='en_IN').title()} Paisa"
            
            return words + " Only"
        except:
            return "Amount in words"
    
    def _get_default_terms(self):
        """Get default terms and conditions"""
        return """Form 2-A, as specified under Rules 19 and 30, pertains to the warranty provided under Section 23(1)(1) of the Drug Act 1976. This document, issued by Tru_pharma, serves as an assurance of the quality and effectiveness of their products. The warranty ensures that the drugs manufactured by Tru_pharma comply with the prescribed standards and meet the necessary regulatory requirements. By utilizing Form 2-A, Tru_pharma demonstrates its commitment to delivering safe and reliable pharmaceuticals to consumers. This form acts as a legal document, emphasizing Tru_pharma's responsibility and accountability in maintaining the highest standards in drug manufacturing and distribution."""