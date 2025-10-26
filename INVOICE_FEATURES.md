# Enhanced Invoice Generation Features

## Overview
The invoice generation system has been significantly enhanced with dynamic customization options. All these features are accessible through the **Invoice Generation Details Modal** when generating PDFs.

## New Features

### 1. Dynamic Header Contact Information
**Location:** Header Information section in PDF Info Dialog

The header contact details (previously hardcoded as "Mr. Behzad Aslam 03339911914") are now fully customizable:

- **Header Contact Name**: Name displayed in the top-right of the invoice
  - Example: "Mr. Behzad Aslam", "Dr. Ahmed Khan"
  - Default: "Mr. Behzad Aslam"

- **Header Contact Phone**: Phone number displayed in the top-right
  - Example: "03339911914", "03001234567"
  - Default: "03339911914"

- **Header Email**: Email address displayed below the contact info
  - Example: "trupharmaceuticalfsd@gmail.com"
  - Default: "trupharmaceuticalfsd@gmail.com"

**How it appears in PDF:**
```
                                    Mr. Behzad Aslam  03339911914
                                    trupharmaceuticalfsd@gmail.com
```

### 2. Company Logo Support
**Location:** Company Logo / Name section in PDF Info Dialog

You can now choose between displaying the company name or a custom logo:

#### Option A: Use Company Name (Default)
- Check the "Use Company Name (Tru-Pharma)" checkbox
- The PDF will display "Tru-Pharma" text as before

#### Option B: Use Custom Logo
- Uncheck the "Use Company Name" checkbox
- Select from previously uploaded logos in the dropdown, OR
- Click "Upload New Logo" to add a new logo

**Logo Upload Process:**
1. Click "Upload New Logo" button
2. Select an image file (PNG, JPG, JPEG, BMP, or GIF)
3. Enter a name for the logo (for future reference)
4. Logo is saved to MongoDB and can be reused
5. Preview appears in the dialog

**Logo Storage:**
- All logos are stored in MongoDB collection: `company_logos`
- Logos are stored as Base64-encoded strings
- Can be reused across multiple invoices
- Managed by `CompanyLogoManager` class

**Database Schema:**
```javascript
{
  _id: ObjectId,
  logo_name: String,        // User-friendly name
  logo_path: String,        // Original file path (reference)
  logo_data: String,        // Base64 encoded image
  created_at: DateTime,
  updated_at: DateTime
}
```

### 3. Optional Authorized Signatory
**Location:** Authorized Signatory (Optional) section in PDF Info Dialog

The signatory field is now optional with two behaviors:

#### With Signatory Name:
- Enter a name like "Mr. Jawad Aslam Yahya"
- PDF displays:
  ```
  For : Tru_Pharma


  Mr. Jawad Aslam Yahya
  Authorized Signatory
  ```

#### Without Signatory (Empty Field):
- Leave the field blank
- PDF displays a blank line with underline for manual signature:
  ```
  For : Tru_Pharma


  ____________________
  Authorized Signatory
  ```

**Use Cases:**
- Pre-signed invoices: Enter signatory name
- For manual signatures: Leave blank
- Different signatories: Enter different names per invoice

## Technical Implementation

### Files Modified/Created

#### New Files:
1. **src/database/company_logo_manager.py**
   - Database operations for logos
   - CRUD operations for company logos
   - Base64 encoding/decoding

#### Modified Files:
1. **src/ui/invoice_generator.py**
   - Enhanced `PDFInfoDialog` with new fields
   - Logo upload and selection functionality
   - Preview capabilities

2. **src/utils/pdf_generator.py**
   - Dynamic header contact rendering
   - Logo vs company name logic
   - Optional signatory handling

### API Changes

#### PDFInfoDialog Constructor:
```python
PDFInfoDialog(parent=None, existing_data=None, mongo_adapter=None)
```
- Added `mongo_adapter` parameter for logo management

#### Invoice Data Structure:
```python
invoice_data = {
    # NEW FIELDS
    'header_contact_name': str,      # Dynamic header contact
    'header_contact_phone': str,     # Dynamic header phone
    'header_email': str,             # Dynamic header email
    'use_company_name': bool,        # True = text, False = logo
    'logo_data': str | None,         # Base64 logo or None
    'authorized_signatory': str,     # Can be empty string

    # EXISTING FIELDS
    'company_contact': str,
    'company_address': str,
    'company_name': str,
    'customer_info': dict,
    'transport_info': dict,
    'invoice_details': dict,
    'items': list,
    'received_amount': float,
    'balance_amount': float
}
```

## Usage Examples

### Example 1: Dynamic Header with Signatory
```python
from src.utils.pdf_generator import ImprovedPDFGenerator

invoice_data = {
    'header_contact_name': 'Dr. Ahmed Khan',
    'header_contact_phone': '03001234567',
    'header_email': 'ahmed@pharma.com',
    'use_company_name': True,
    'logo_data': None,
    'authorized_signatory': 'Dr. Ahmed Khan',
    # ... other fields
}

generator = ImprovedPDFGenerator()
generator.generate_invoice_pdf(invoice_data, 'invoice.pdf')
```

### Example 2: Logo with No Signatory
```python
invoice_data = {
    'header_contact_name': 'Support Team',
    'header_contact_phone': '0800-PHARMA',
    'header_email': 'support@pharma.com',
    'use_company_name': False,
    'logo_data': '<base64_encoded_logo>',
    'authorized_signatory': '',  # Empty for manual signature
    # ... other fields
}
```

## Testing

Run the test suite:
```bash
python test_enhanced_pdf.py
```

This generates three test PDFs:
1. `test_invoice_with_signatory.pdf` - With signatory name
2. `test_invoice_no_signatory.pdf` - Blank signature line
3. `test_invoice_custom_header.pdf` - Custom header contact

## User Guide

### How to Generate an Invoice with Custom Options:

#### Method 1: From Invoice Generator Tab

1. **Open Invoice Generator Tab** in the application

2. **Add Items** to the invoice as usual

3. **Click "Save as PDF"** button

4. **In the Invoice Generation Details Modal:**

   a. **Header Information Section:**
      - Enter contact person name
      - Enter phone number
      - Enter email address

   b. **Company Logo / Name Section:**
      - Check "Use Company Name" for text logo, OR
      - Uncheck and select/upload a logo

   c. **Authorized Signatory Section:**
      - Enter signatory name for pre-signed invoices
      - Leave blank for manual signature space

   d. **Fill Other Sections** as needed:
      - Company Information
      - Transport & Delivery Information
      - Terms & Conditions

5. **Click "Generate PDF"**

#### Method 2: From New Entry Tab (Auto-Generate on Save)

1. **Open New Entry Tab** in the application

2. **Fill in Entry Details:**
   - Select customer
   - Add products
   - Set quantities and prices
   - Choose Credit/Debit

3. **Check "Auto-generate invoice on save"** checkbox

4. **Click "Save Entry & Generate Invoice"** button

5. **In the Invoice Generation Details Modal:**

   a. **Header Information Section:**
      - Enter contact person name
      - Enter phone number
      - Enter email address

   b. **Company Logo / Name Section:**
      - Check "Use Company Name" for text logo, OR
      - Uncheck and select/upload a logo

   c. **Authorized Signatory Section:**
      - Enter signatory name for pre-signed invoices
      - Leave blank for manual signature space

   d. **Fill Other Sections** as needed:
      - Company Information
      - Transport & Delivery Information
      - Terms & Conditions

5. **Click "Generate PDF"**

## Database Maintenance

### View Saved Logos:
```python
from src.database.company_logo_manager import CompanyLogoManager
from src.database.mongo_adapter import MongoAdapter

mongo = MongoAdapter()
logo_mgr = CompanyLogoManager(mongo)

# Get all logo names
logos = logo_mgr.get_logo_names()
print(logos)
```

### Delete a Logo:
```python
logo_mgr.delete_logo_by_name("Old Logo Name")
```

## Backward Compatibility

All changes are backward compatible:
- If new fields are not provided, defaults are used
- Existing invoice generation code continues to work
- Old invoice data format is still supported

## Future Enhancements

Potential future additions:
- Multiple signatory support
- Logo position customization
- Header layout templates
- QR code generation for invoices
- Digital signature integration
