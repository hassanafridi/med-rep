"""
Test script to generate a sample PDF matching the layout from the image
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.pdf_generator import ImprovedPDFGenerator

# Sample invoice data matching the image
invoice_data = {
    'company_contact': 'Mr. Behzad Aslam 03339911914',
    'company_address': 'trupharmaceuticalfsd@gmail.com',
    'company_name': 'Tru_Pharma',
    'customer_info': {
        'name': 'Fatima poli clinic',
        'address': ''
    },
    'transport_info': {
        'transport_name': 'Jawad Asfam',
        'delivery_date': '14-10-25',
        'delivery_location': 'Jaranwala'
    },
    'invoice_details': {
        'invoice_number': '1499',
        'invoice_date': '14-10-25'
    },
    'items': [
        {
            'product_name': 'G+ cream',
            'quantity': 4,
            'unit_price': 1020,
            'discount': 25,
            'amount': 3060
        }
    ],
    'received_amount': 0.00,
    'balance_amount': 3060,
    'authorized_signatory': 'Mr. Jawad Aslam Yahya'
}

# Generate PDF
generator = ImprovedPDFGenerator()
output_path = 'test_invoice_layout.pdf'

print(f"Generating test invoice PDF to match image layout...")
success = generator.generate_invoice_pdf(invoice_data, output_path)

if success:
    print(f"PDF generated successfully: {output_path}")
    print("\nPlease compare this PDF with the image to verify the layout matches.")
else:
    print("Failed to generate PDF")
