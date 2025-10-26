"""
Test script for enhanced PDF generation with dynamic features:
- Dynamic header contact info
- Optional logo support
- Optional signatory field
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.pdf_generator import ImprovedPDFGenerator

print("=" * 80)
print("Testing Enhanced PDF Generation Features")
print("=" * 80)

# Test 1: With company name and signatory
print("\n1. Testing with Company Name and Signatory...")
invoice_data_1 = {
    'header_contact_name': 'Mr. Ahmed Khan',
    'header_contact_phone': '03001234567',
    'header_email': 'ahmed@testpharma.com',
    'use_company_name': True,
    'logo_data': None,
    'company_contact': 'Mr. Behzad Aslam 03339911914',
    'company_address': 'trupharmaceuticalfsd@gmail.com',
    'company_name': 'Tru_Pharma',
    'customer_info': {
        'name': 'City Medical Store',
        'address': 'Mall Road, Faisalabad'
    },
    'transport_info': {
        'transport_name': 'Express Delivery',
        'delivery_date': '26-10-25',
        'delivery_location': 'Faisalabad'
    },
    'invoice_details': {
        'invoice_number': '2001',
        'invoice_date': '26-10-25'
    },
    'items': [
        {
            'product_name': 'Panadol Tablets',
            'quantity': 10,
            'unit_price': 150,
            'discount': 10,
        },
        {
            'product_name': 'Aspirin 100mg',
            'quantity': 5,
            'unit_price': 200,
            'discount': 5,
        }
    ],
    'received_amount': 500.00,
    'balance_amount': 1850,
    'authorized_signatory': 'Mr. Ali Raza'
}

generator = ImprovedPDFGenerator()
output_path_1 = 'test_invoice_with_signatory.pdf'
success = generator.generate_invoice_pdf(invoice_data_1, output_path_1)
print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
if success:
    print(f"   Generated: {output_path_1}")

# Test 2: Without signatory (should show blank line)
print("\n2. Testing without Signatory (blank line with underline)...")
invoice_data_2 = {
    'header_contact_name': 'Mr. Behzad Aslam',
    'header_contact_phone': '03339911914',
    'header_email': 'trupharmaceuticalfsd@gmail.com',
    'use_company_name': True,
    'logo_data': None,
    'company_contact': 'Mr. Behzad Aslam 03339911914',
    'company_address': 'trupharmaceuticalfsd@gmail.com',
    'company_name': 'Tru_Pharma',
    'customer_info': {
        'name': 'Health Plus Pharmacy',
        'address': 'Satellite Town'
    },
    'transport_info': {
        'transport_name': 'Standard Delivery',
        'delivery_date': '26-10-25',
        'delivery_location': 'Lahore'
    },
    'invoice_details': {
        'invoice_number': '2002',
        'invoice_date': '26-10-25'
    },
    'items': [
        {
            'product_name': 'Vitamin D3',
            'quantity': 3,
            'unit_price': 500,
            'discount': 15,
        }
    ],
    'received_amount': 0.00,
    'balance_amount': 1275,
    'authorized_signatory': ''  # Empty signatory
}

output_path_2 = 'test_invoice_no_signatory.pdf'
success = generator.generate_invoice_pdf(invoice_data_2, output_path_2)
print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
if success:
    print(f"   Generated: {output_path_2}")

# Test 3: With different header contact info
print("\n3. Testing with different header contact info...")
invoice_data_3 = {
    'header_contact_name': 'Dr. Fatima Shah',
    'header_contact_phone': '03219876543',
    'header_email': 'contact@newpharma.pk',
    'use_company_name': True,
    'logo_data': None,
    'company_contact': 'Mr. Behzad Aslam 03339911914',
    'company_address': 'trupharmaceuticalfsd@gmail.com',
    'company_name': 'Tru_Pharma',
    'customer_info': {
        'name': 'Medicare Center',
        'address': 'Jinnah Colony'
    },
    'transport_info': {
        'transport_name': 'TCS Express',
        'delivery_date': '26-10-25',
        'delivery_location': 'Islamabad'
    },
    'invoice_details': {
        'invoice_number': '2003',
        'invoice_date': '26-10-25'
    },
    'items': [
        {
            'product_name': 'Antibiotic Syrup',
            'quantity': 2,
            'unit_price': 850,
            'discount': 20,
        },
        {
            'product_name': 'Cough Syrup',
            'quantity': 4,
            'unit_price': 300,
            'discount': 10,
        }
    ],
    'received_amount': 1000.00,
    'balance_amount': 1440,
    'authorized_signatory': 'Dr. Fatima Shah'
}

output_path_3 = 'test_invoice_custom_header.pdf'
success = generator.generate_invoice_pdf(invoice_data_3, output_path_3)
print(f"   Result: {'SUCCESS' if success else 'FAILED'}")
if success:
    print(f"   Generated: {output_path_3}")

print("\n" + "=" * 80)
print("Summary:")
print("- All PDFs should have different header contact information")
print("- test_invoice_with_signatory.pdf: Should show 'Mr. Ali Raza' as signatory")
print("- test_invoice_no_signatory.pdf: Should show blank line with underline")
print("- test_invoice_custom_header.pdf: Should show Dr. Fatima Shah contact info")
print("=" * 80)
print("\nNote: Logo upload feature can only be tested through the GUI")
print("      (Invoice Generator UI has logo upload button)")
print("=" * 80)
