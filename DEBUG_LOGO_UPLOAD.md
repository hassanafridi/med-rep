# Debug Guide: Logo Upload Button

## Current Status
Added comprehensive debug logging to identify why the upload button isn't working.

## How to Debug

### Step 1: Check Console Output
When you run the application, watch the console/terminal for these messages:

```
Toggle logo options - use_name: True, button enabled: False   # On dialog open
Toggle logo options - use_name: False, button enabled: True   # When unchecking
Upload logo method called                                      # When clicking button
Selected file: /path/to/image.png                             # After selecting file
Logo name: MyLogo, OK: True                                   # After entering name
Saving to database...                                          # When saving
Logo ID: 507f1f77bcf86cd799439011                            # After save success
```

### Step 2: Test the Upload Feature

1. **Open the application**
   ```bash
   python main.py  # or your entry point
   ```

2. **Open Invoice Generation Dialog**
   - Go to Invoice Generator tab → Click "Save as PDF"
   - OR Go to New Entry tab → Check "Auto-generate invoice" → Click "Save Entry & Generate Invoice"

3. **Enable Logo Upload**
   - Find the checkbox: **"Use Company Name (Tru-Pharma)"**
   - **UNCHECK IT** (this is critical!)
   - Console should show: `Toggle logo options - use_name: False, button enabled: True`

4. **Click Upload Button**
   - Click **"Upload New Logo"** button
   - Console should show: `Upload logo method called`
   - File picker should open

5. **Select Image**
   - Choose a PNG, JPG, or other image file
   - Console should show: `Selected file: <your_file_path>`

6. **Enter Logo Name**
   - Dialog will ask for logo name
   - Enter a name (or use default)
   - Click OK
   - Console should show: `Logo name: <name>, OK: True`

7. **Verify Save**
   - Console should show: `Saving to database...`
   - Console should show: `Logo ID: <some_id>`
   - Success message box should appear

### Step 3: Common Issues

#### Issue 1: Nothing happens when clicking button
**Check:**
- Is "Use Company Name" checkbox UNCHECKED?
- Console shows: `Toggle logo options - use_name: False, button enabled: True`
- Button is purple (enabled) not grayed out (disabled)

**Solution:**
Uncheck the "Use Company Name (Tru-Pharma)" checkbox first!

#### Issue 2: Console shows "Upload logo method called" but no file picker
**Possible causes:**
- QFileDialog not working in your environment
- Parent window issue

**Debug:**
Add this test before the file picker:
```python
print(f"Dialog parent: {self.parent()}")
print(f"Dialog visible: {self.isVisible()}")
```

#### Issue 3: "Logo manager not initialized"
**Cause:**
PDFInfoDialog was not passed a mongo_adapter

**Check the constructor call:**
```python
# Should be:
dialog = PDFInfoDialog(self, existing_data, self.mongo_adapter)

# NOT:
dialog = PDFInfoDialog(self, existing_data)  # Missing mongo_adapter!
```

**Fix in calling code:**
```python
# invoice_generator.py (around line 1829, 1862, 1936)
pdf_dialog = PDFInfoDialog(self, existing_data, self.mongo_adapter)

# new_entry_tab.py (around line 790)
invoice_dialog = PDFInfoDialog(self, existing_data, self.db)
```

#### Issue 4: File picker opens but crashes
**Check console for error traceback**

The error handler will now print full stack trace:
```python
Traceback (most recent call last):
  ...
  (error details here)
```

### Step 4: Verify Database Connection

Test if MongoDB is accessible:

```python
# Quick test script
from src.database.mongo_adapter import MongoAdapter
from src.database.company_logo_manager import CompanyLogoManager

mongo = MongoAdapter()
logo_mgr = CompanyLogoManager(mongo)

# Test save
test_data = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
logo_id = logo_mgr.save_logo("TestLogo", "/test/path.png", test_data)

print(f"Test logo saved with ID: {logo_id}")

# Test retrieve
logos = logo_mgr.get_logo_names()
print(f"All logos: {logos}")
```

## Debug Output Examples

### Successful Upload Flow:
```
Toggle logo options - use_name: False, button enabled: True
Upload logo method called
Selected file: D:\Images\company_logo.png
Logo name: CompanyLogo, OK: True
Saving to database...
Logo ID: 507f1f77bcf86cd799439011
```

### Cancelled Upload:
```
Upload logo method called
Selected file:                    # Empty because cancelled
```

### Failed Save:
```
Upload logo method called
Selected file: D:\Images\logo.png
Logo name: MyLogo, OK: True
Saving to database...
Logo ID: None                     # Failed!
(Error message box appears)
```

### Button Disabled (checkbox is checked):
```
Toggle logo options - use_name: True, button enabled: False
# Clicking button does nothing - it's disabled!
```

## Quick Fixes

### If button appears grayed out:
```python
# Check this in the code:
self.use_company_name_radio.isChecked()  # Should be False

# Manually uncheck in UI:
# Find and uncheck "Use Company Name (Tru-Pharma)"
```

### If mongo_adapter is None:
```python
# In PDFInfoDialog __init__:
print(f"Mongo adapter: {mongo_adapter}")
print(f"Logo manager: {self.logo_manager}")

# Should show:
# Mongo adapter: <MongoAdapter object>
# Logo manager: <CompanyLogoManager object>

# If shows None, fix the constructor call!
```

### Force enable button for testing:
```python
# Temporarily in toggle_logo_options:
def toggle_logo_options(self, use_name):
    self.logo_dropdown.setEnabled(True)  # Always enabled for testing
    self.upload_logo_btn.setEnabled(True)  # Always enabled for testing
    # ... rest of code
```

## Files with Debug Logging

### src/ui/invoice_generator.py
- Line 492: `toggle_logo_options` debug
- Line 496: `upload_logo` start
- Line 505: File selection result
- Line 524: Logo name input result
- Line 529: Database save start
- Line 531: Database save result
- Line 554: Error handling with full traceback

## Next Steps

1. Run the application
2. Open invoice dialog
3. Uncheck "Use Company Name"
4. Click "Upload New Logo"
5. **Watch console output**
6. Report what you see in console

## Expected Console Output

If everything works, you should see exactly this sequence:
```
1. Toggle logo options - use_name: True, button enabled: False    # On dialog open
2. Toggle logo options - use_name: False, button enabled: True    # After unchecking
3. Upload logo method called                                       # After clicking button
4. Selected file: <your_file_path>                                # After selecting image
5. Logo name: <your_logo_name>, OK: True                          # After entering name
6. Saving to database...                                           # During save
7. Logo ID: <some_mongodb_id>                                     # After successful save
```

Then you'll see a success message box!

## Report Format

If it's still not working, please provide:

1. **Console output** - Copy all the debug messages
2. **What you clicked** - Step by step what you did
3. **What happened** - File picker opened? Dialog appeared? Nothing?
4. **Error messages** - Any error boxes or console errors

This will help pinpoint exactly where it's failing!
