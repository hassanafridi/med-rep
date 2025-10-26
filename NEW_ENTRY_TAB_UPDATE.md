# New Entry Tab - Enhanced Invoice Generation

## What Changed?

The **New Entry Tab** now uses the same enhanced **Invoice Generation Details Modal** with all the new customization features!

## Before vs After

### Before:
When you clicked "Save Entry & Generate Invoice", you saw a simple dialog with only:
- Company Contact
- Company Address
- Transport Name
- Delivery Date
- Delivery Location

### After:
Now you see the **FULL Enhanced Invoice Generation Details Modal** with:

#### 1. Header Information (NEW!)
- Header Contact Name (customizable)
- Header Contact Phone (customizable)
- Header Email (customizable)

#### 2. Company Logo / Name (NEW!)
- Option to use company name OR upload/select a logo
- Logo preview
- Logo saved to database for reuse

#### 3. Authorized Signatory (NEW!)
- Optional signatory field
- Leave blank for manual signature line
- Pre-fill for pre-signed invoices

#### 4. Company Information
- Company Contact
- Company Address

#### 5. Transport & Delivery Information
- Transport Name
- Delivery Date (auto-filled with current date)
- Delivery Location (auto-filled from customer address)

#### 6. Terms & Conditions
- Customizable terms text

#### 7. Customer Information (Read-only)
- Shows customer details from the entry

## How to Use

### Step-by-Step Guide:

1. **Open New Entry Tab**

2. **Fill in Entry Information:**
   - Select Date
   - Select Customer
   - Add Products (can add multiple)
   - Enter Quantities & Prices
   - Choose Credit or Debit
   - Enter Received Amount (for credit entries)

3. **Enable Auto-Invoice:**
   - Check the "Auto-generate invoice on save" checkbox

4. **Click "Save Entry & Generate Invoice"**

5. **Fill in Enhanced Invoice Details:**

   **Header Section:**
   - Enter your contact name (e.g., "Mr. Ahmed Khan")
   - Enter phone number (e.g., "03001234567")
   - Enter email (e.g., "contact@yourcompany.com")

   **Logo/Name Section:**
   - Keep "Use Company Name" checked for text logo, OR
   - Uncheck it and:
     - Select previously uploaded logo from dropdown
     - OR click "Upload New Logo" to add new one

   **Signatory Section:**
   - Enter signatory name if you want pre-signed invoice
   - Leave blank if you want empty signature line

   **Other Sections:**
   - Verify/edit company contact and address
   - Verify/edit transport details (auto-filled)
   - Edit terms if needed

6. **Click "Generate PDF"**

7. **Entry Saved & Invoice Generated:**
   - Entry is saved to database
   - Invoice PDF is generated in the `invoices/` folder
   - Success message shown with invoice path

## Key Benefits

### 1. Consistency
- **Same dialog** for both New Entry Tab and Invoice Generator Tab
- All features available in both places

### 2. Flexibility
- **Different header info** for different invoices
- **Logo support** - upload once, reuse many times
- **Optional signatory** - perfect for both pre-signed and manual signing

### 3. Auto-Fill Intelligence
- Delivery location auto-filled from customer address
- Current date auto-filled for delivery date
- Customer info displayed for reference

### 4. Database Integration
- Logos stored in MongoDB
- Reuse logos across multiple invoices
- No need to re-upload every time

## Example Scenarios

### Scenario 1: Standard Invoice with Signatory
```
1. Add entry for "City Medical Store"
2. Add products: Panadol, Aspirin
3. Check "Auto-generate invoice"
4. Click Save
5. In dialog:
   - Header: "Mr. Behzad Aslam" / "03339911914"
   - Use company name: ✓
   - Signatory: "Mr. Jawad Aslam Yahya"
6. Generate PDF
Result: Invoice with company name and signatory printed
```

### Scenario 2: Invoice with Logo, No Signatory
```
1. Add entry for "Health Plus Pharmacy"
2. Add products
3. Check "Auto-generate invoice"
4. Click Save
5. In dialog:
   - Header: Custom contact info
   - Use company name: ✗
   - Select logo from dropdown (or upload new)
   - Signatory: (leave blank)
6. Generate PDF
Result: Invoice with logo and blank signature line
```

### Scenario 3: Custom Header for Branch Office
```
1. Add entry for customer
2. Add products
3. Check "Auto-generate invoice"
4. Click Save
5. In dialog:
   - Header: "Dr. Fatima Shah" / "03215556677"
   - Email: "branch@trupharma.com"
   - Use company name: ✓
   - Signatory: "Dr. Fatima Shah"
6. Generate PDF
Result: Invoice with branch office contact info
```

## Technical Details

### Files Modified:
- `src/ui/new_entry_tab.py`
  - Replaced old `InvoiceDetailsDialog` with enhanced `PDFInfoDialog`
  - Updated `generateAutoInvoiceWithDetails()` to pass new fields
  - Added imports for enhanced dialog

### Invoice Data Flow:
```
New Entry Tab
    ↓
Enhanced PDFInfoDialog (shows all options)
    ↓
User fills in details
    ↓
get_pdf_data() returns enhanced data
    ↓
generateAutoInvoiceWithDetails() receives data
    ↓
ImprovedPDFGenerator generates PDF
    ↓
PDF saved to invoices/ folder
```

### New Fields in Invoice Data:
```python
{
    'header_contact_name': str,
    'header_contact_phone': str,
    'header_email': str,
    'use_company_name': bool,
    'logo_data': str (base64) or None,
    'authorized_signatory': str (can be empty),
    # ... existing fields
}
```

## Backward Compatibility

✅ **Fully backward compatible:**
- Old entries still work
- If enhanced dialog not available, falls back to old dialog
- All new fields have sensible defaults
- Existing invoices remain unchanged

## Troubleshooting

### Issue: "PDFInfoDialog not available" warning
**Solution:** Enhanced dialog import failed. Check that `invoice_generator.py` is in the correct location.

### Issue: Logo not appearing in PDF
**Solution:**
1. Ensure you unchecked "Use Company Name"
2. Verify logo was uploaded/selected
3. Check logo preview shows correctly

### Issue: Signatory showing when I want blank
**Solution:** Make sure signatory field is completely empty (no spaces)

## Need Help?

See the main documentation: `INVOICE_FEATURES.md` for:
- Complete API reference
- Database schema
- Advanced usage examples
- Logo management guide
