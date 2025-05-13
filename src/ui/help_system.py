from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextBrowser, QSplitter, QLabel, QPushButton, QDialog,
    QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
import os
import sys

class HelpBrowser(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Medical Rep Transaction Software - Help")
        self.setMinimumSize(900, 600)
        self.initUI()
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Medical Rep Transaction Software - Help & Documentation")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold;")
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search help topics...")
        search_box.textChanged.connect(self.searchHelp)
        
        header_layout.addWidget(header_label)
        header_layout.addWidget(search_box)
        
        main_layout.addLayout(header_layout)
        
        # Content splitter
        splitter = QSplitter(Qt.Horizontal)
        
        # Topics tree
        self.topics_tree = QTreeWidget()
        self.topics_tree.setHeaderLabel("Help Topics")
        self.topics_tree.setMinimumWidth(200)
        self.topics_tree.itemClicked.connect(self.topicSelected)
        
        # Help content
        self.help_content = QTextBrowser()
        self.help_content.setOpenExternalLinks(True)
        
        splitter.addWidget(self.topics_tree)
        splitter.addWidget(self.help_content)
        
        # Set initial splitter sizes (25% tree, 75% content)
        splitter.setSizes([225, 675])
        
        main_layout.addWidget(splitter)
        
        self.setLayout(main_layout)
        
        # Load help topics
        self.loadHelpTopics()
        
        # Show initial help
        self.showInitialHelp()
    
    def loadHelpTopics(self):
        """Load help topics into the tree"""
        # Getting Started
        getting_started = QTreeWidgetItem(self.topics_tree, ["Getting Started"])
        QTreeWidgetItem(getting_started, ["Introduction"])
        QTreeWidgetItem(getting_started, ["System Requirements"])
        QTreeWidgetItem(getting_started, ["Installation"])
        QTreeWidgetItem(getting_started, ["First Time Setup"])
        
        # Basic Features
        basic_features = QTreeWidgetItem(self.topics_tree, ["Basic Features"])
        QTreeWidgetItem(basic_features, ["Adding New Entries"])
        QTreeWidgetItem(basic_features, ["Managing the Ledger"])
        QTreeWidgetItem(basic_features, ["Using Graphs"])
        QTreeWidgetItem(basic_features, ["Generating Reports"])
        
        # Advanced Features
        advanced_features = QTreeWidgetItem(self.topics_tree, ["Advanced Features"])
        QTreeWidgetItem(advanced_features, ["Customer Management"])
        QTreeWidgetItem(advanced_features, ["Product Management"])
        QTreeWidgetItem(advanced_features, ["Invoice Generation"])
        QTreeWidgetItem(advanced_features, ["Data Import/Export"])
        QTreeWidgetItem(advanced_features, ["Audit Trail"])
        
        # Data Management
        data_management = QTreeWidgetItem(self.topics_tree, ["Data Management"])
        QTreeWidgetItem(data_management, ["Backup and Restore"])
        QTreeWidgetItem(data_management, ["Cloud Synchronization"])
        QTreeWidgetItem(data_management, ["Database Maintenance"])
        
        # Troubleshooting
        troubleshooting = QTreeWidgetItem(self.topics_tree, ["Troubleshooting"])
        QTreeWidgetItem(troubleshooting, ["Common Issues"])
        QTreeWidgetItem(troubleshooting, ["Error Messages"])
        QTreeWidgetItem(troubleshooting, ["Data Recovery"])
        
        # Expand the first level
        self.topics_tree.expandItem(getting_started)
    
    def topicSelected(self, item, column):
        """Show help content for the selected topic"""
        # Get the full path to the topic
        path = []
        current = item
        while current:
            path.insert(0, current.text(0))
            current = current.parent()
        
        # Load the appropriate help content
        if len(path) == 1:
            # Category selected, show overview
            category = path[0]
            self.showCategoryOverview(category)
        else:
            # Specific topic selected
            category = path[0]
            topic = path[-1]
            self.showTopicHelp(category, topic)
    
    def showCategoryOverview(self, category):
        """Show an overview of the category"""
        if category == "Getting Started":
            self.help_content.setHtml(self.getGettingStartedOverview())
        elif category == "Basic Features":
            self.help_content.setHtml(self.getBasicFeaturesOverview())
        elif category == "Advanced Features":
            self.help_content.setHtml(self.getAdvancedFeaturesOverview())
        elif category == "Data Management":
            self.help_content.setHtml(self.getDataManagementOverview())
        elif category == "Troubleshooting":
            self.help_content.setHtml(self.getTroubleshootingOverview())
    
    def showTopicHelp(self, category, topic):
        """Show help for a specific topic"""
        # Implement topic-specific help content
        if category == "Basic Features" and topic == "Adding New Entries":
            self.help_content.setHtml(self.getNewEntriesHelp())
        elif category == "Basic Features" and topic == "Managing the Ledger":
            self.help_content.setHtml(self.getLedgerHelp())
        elif category == "Advanced Features" and topic == "Invoice Generation":
            self.help_content.setHtml(self.getInvoiceGenerationHelp())
        elif category == "Data Management" and topic == "Backup and Restore":
            self.help_content.setHtml(self.getBackupRestoreHelp())
        else:
            # For topics not yet implemented, show a placeholder
            self.help_content.setHtml(f"""
            <h2>{topic}</h2>
            <p>This help topic is under development. Please check back later.</p>
            """)
    
    def searchHelp(self, text):
        """Search help topics"""
        if not text:
            # If search is cleared, restore full tree
            for i in range(self.topics_tree.topLevelItemCount()):
                top_item = self.topics_tree.topLevelItem(i)
                self.setItemVisibility(top_item, True)
            return
        
        # Search topics
        text = text.lower()
        for i in range(self.topics_tree.topLevelItemCount()):
            top_item = self.topics_tree.topLevelItem(i)
            
            # Check if category matches
            category_matches = text in top_item.text(0).lower()
            
            # Check if any topic in the category matches
            topic_matches = False
            for j in range(top_item.childCount()):
                child_item = top_item.child(j)
                
                if text in child_item.text(0).lower():
                    topic_matches = True
                    self.setItemVisibility(child_item, True)
                else:
                    self.setItemVisibility(child_item, False)
            
            # Show category if either the category itself matches or any of its topics
            self.setItemVisibility(top_item, category_matches or topic_matches)
            
            # Expand category if it has matching topics
            if topic_matches:
                self.topics_tree.expandItem(top_item)
    
    def setItemVisibility(self, item, visible):
        """Set the visibility of a tree item"""
        item.setHidden(not visible)
    
    def showInitialHelp(self):
        """Show initial help content"""
        self.help_content.setHtml(self.getWelcomeHelp())
    
    # Help content methods
    def getWelcomeHelp(self):
        """Get the welcome help content"""
        return """
        <h1>Welcome to Medical Rep Transaction Software</h1>
        <p>This help system will guide you through using the Medical Rep Transaction Software efficiently.</p>
        
        <h2>About the Software</h2>
        <p>Medical Rep Transaction Software is designed to help medical representatives track their sales, manage customer relationships, and generate reports and invoices. The software provides a comprehensive solution for managing the day-to-day business operations of medical representatives.</p>
        
        <h2>Getting Help</h2>
        <p>To get help on a specific topic, browse the topics in the tree on the left side of this window, or use the search box at the top to find specific information.</p>
        
        <h2>Key Features</h2>
        <ul>
            <li>Recording sales transactions</li>
            <li>Tracking customer information</li>
            <li>Managing product data</li>
            <li>Generating reports and graphs</li>
            <li>Creating professional invoices</li>
            <li>Backing up and securing your data</li>
        </ul>
        
        <p>Select a topic from the tree on the left to get more detailed information.</p>
        """
    
    def getGettingStartedOverview(self):
        """Get the Getting Started overview content"""
        return """
        <h1>Getting Started</h1>
        
        <p>This section will help you get up and running with the Medical Rep Transaction Software.</p>
        
        <h2>Topics in this Section</h2>
        <ul>
            <li><strong>Introduction</strong> - Overview of the software and its features</li>
            <li><strong>System Requirements</strong> - Hardware and software requirements</li>
            <li><strong>Installation</strong> - Step-by-step installation guide</li>
            <li><strong>First Time Setup</strong> - Initial configuration of the software</li>
        </ul>
        
        <p>Select a specific topic from the tree on the left to view detailed information.</p>
        """
    
    def getBasicFeaturesOverview(self):
        """Get the Basic Features overview content"""
        return """
        <h1>Basic Features</h1>
        
        <p>This section covers the core features that you'll use regularly in the Medical Rep Transaction Software.</p>
        
        <h2>Topics in this Section</h2>
        <ul>
            <li><strong>Adding New Entries</strong> - How to record sales and transactions</li>
            <li><strong>Managing the Ledger</strong> - Viewing, filtering, and managing transaction records</li>
            <li><strong>Using Graphs</strong> - Visualizing your sales data with charts and graphs</li>
            <li><strong>Generating Reports</strong> - Creating and exporting reports</li>
        </ul>
        
        <p>Select a specific topic from the tree on the left to view detailed information.</p>
        """
    
    def getAdvancedFeaturesOverview(self):
        """Get the Advanced Features overview content"""
        return """
        <h1>Advanced Features</h1>
        
        <p>This section covers the more advanced features of the Medical Rep Transaction Software that can help streamline your business operations.</p>
        
        <h2>Topics in this Section</h2>
        <ul>
            <li><strong>Customer Management</strong> - Managing customer information and relationships</li>
            <li><strong>Product Management</strong> - Managing product data and pricing</li>
            <li><strong>Invoice Generation</strong> - Creating professional invoices from your transaction data</li>
            <li><strong>Data Import/Export</strong> - Importing and exporting data to and from other systems</li>
            <li><strong>Audit Trail</strong> - Tracking changes and activities in the system</li>
        </ul>
        
        <p>Select a specific topic from the tree on the left to view detailed information.</p>
        """
    
    def getDataManagementOverview(self):
        """Get the Data Management overview content"""
        return """
        <h1>Data Management</h1>
        
        <p>This section covers important aspects of managing your data to ensure security and reliability.</p>
        
        <h2>Topics in this Section</h2>
        <ul>
            <li><strong>Backup and Restore<li><strong>Backup and Restore</strong> - How to back up and restore your data</li>
            <li><strong>Cloud Synchronization</strong> - Keeping your data synchronized across multiple devices</li>
            <li><strong>Database Maintenance</strong> - Maintaining database performance and integrity</li>
        </ul>
        
        <p>Select a specific topic from the tree on the left to view detailed information.</p>
        """
    
    def getTroubleshootingOverview(self):
        """Get the Troubleshooting overview content"""
        return """
        <h1>Troubleshooting</h1>
        
        <p>This section provides solutions to common issues that you might encounter while using the software.</p>
        
        <h2>Topics in this Section</h2>
        <ul>
            <li><strong>Common Issues</strong> - Solutions to frequently encountered problems</li>
            <li><strong>Error Messages</strong> - Explanations of error messages and how to resolve them</li>
            <li><strong>Data Recovery</strong> - How to recover data in case of corruption or loss</li>
        </ul>
        
        <p>Select a specific topic from the tree on the left to view detailed information.</p>
        """
    
    def getNewEntriesHelp(self):
        """Get help content for Adding New Entries"""
        return """
        <h1>Adding New Entries</h1>
        
        <p>The New Entry tab allows you to record sales transactions and other financial entries in the system.</p>
        
        <h2>Steps to Add a New Entry</h2>
        <ol>
            <li>Go to the <strong>New Entry</strong> tab in the main application window.</li>
            <li>Select the <strong>Date</strong> of the transaction using the date picker.</li>
            <li>Choose a <strong>Customer</strong> from the dropdown list.</li>
            <li>Select a <strong>Product</strong> from the dropdown list.</li>
            <li>Enter the <strong>Quantity</strong> of products sold or purchased.</li>
            <li>The <strong>Unit Price</strong> will be automatically filled based on the selected product, but you can adjust it if needed.</li>
            <li>The <strong>Total Amount</strong> will be calculated automatically (Quantity × Unit Price).</li>
            <li>Check the <strong>Credit Entry</strong> box if this is a credit transaction, or leave it unchecked for a debit transaction.
                <ul>
                    <li><strong>Credit</strong>: Money coming in (e.g., a sale)</li>
                    <li><strong>Debit</strong>: Money going out (e.g., a purchase or expense)</li>
                </ul>
            </li>
            <li>Add optional <strong>Notes</strong> about the transaction if needed.</li>
            <li>Click the <strong>Save Entry</strong> button to record the transaction.</li>
        </ol>
        
        <h2>Tips</h2>
        <ul>
            <li>You can clear the form by clicking the <strong>Clear Form</strong> button.</li>
            <li>The date defaults to the current date, but you can change it for backdated entries.</li>
            <li>If a customer or product is not in the list, you need to add them first in the <strong>Manage Data</strong> tab.</li>
            <li>You cannot save an entry without selecting a customer and product.</li>
        </ul>
        
        <h2>How Entries Affect Your Balances</h2>
        <p>Each entry affects your running balance in the following way:</p>
        <ul>
            <li><strong>Credit entries</strong> increase your balance.</li>
            <li><strong>Debit entries</strong> decrease your balance.</li>
        </ul>
        <p>The transaction is automatically recorded in both the Entries and Transactions tables, with the balance calculated and updated.</p>
        """
    
    def getLedgerHelp(self):
        """Get help content for Managing the Ledger"""
        return """
        <h1>Managing the Ledger</h1>
        
        <p>The Ledger tab allows you to view, search, filter, and manage all transactions recorded in the system.</p>
        
        <h2>Ledger Features</h2>
        
        <h3>Filtering and Searching</h3>
        <p>You can filter the ledger entries using various criteria:</p>
        <ul>
            <li><strong>Date Range</strong>: Filter entries within a specific date range.</li>
            <li><strong>Customer</strong>: Show entries for a specific customer only.</li>
            <li><strong>Search Notes</strong>: Search for specific text in the notes field.</li>
            <li><strong>Entry Type</strong>: Show all entries, credit entries only, or debit entries only.</li>
        </ul>
        <p>After setting your filter criteria, click <strong>Apply Filters</strong> to update the ledger view. To clear all filters and show all entries, click <strong>Clear Filters</strong>.</p>
        
        <h3>Ledger Table</h3>
        <p>The ledger table displays detailed information about each entry:</p>
        <ul>
            <li><strong>ID</strong>: The unique identifier for the entry.</li>
            <li><strong>Date</strong>: The date of the transaction.</li>
            <li><strong>Customer</strong>: The customer involved in the transaction.</li>
            <li><strong>Product</strong>: The product involved in the transaction.</li>
            <li><strong>Quantity</strong>: The quantity of the product.</li>
            <li><strong>Unit Price</strong>: The unit price of the product.</li>
            <li><strong>Total</strong>: The total amount (Quantity × Unit Price).</li>
            <li><strong>Type</strong>: Whether the entry is a Credit or Debit.</li>
            <li><strong>Notes</strong>: Any additional notes about the transaction.</li>
        </ul>
        
        <h3>Entry Management</h3>
        <p>Right-click on any entry in the ledger to access a context menu with these options:</p>
        <ul>
            <li><strong>View Details</strong>: See complete details about the selected entry.</li>
            <li><strong>Edit Entry</strong>: Modify the selected entry.</li>
            <li><strong>Delete Entry</strong>: Remove the selected entry from the ledger.</li>
            <li><strong>View Customer History</strong>: View all transactions for the customer associated with this entry.</li>
        </ul>
        
        <h3>Summary Information</h3>
        <p>At the bottom of the ledger, you'll see summary information:</p>
        <ul>
            <li><strong>Total Entries</strong>: The number of entries currently displayed.</li>
            <li><strong>Total Credit</strong>: The sum of all credit entries displayed.</li>
            <li><strong>Total Debit</strong>: The sum of all debit entries displayed.</li>
            <li><strong>Current Balance</strong>: The current overall balance.</li>
        </ul>
        
        <h3>Export and Reporting</h3>
        <p>You can export the current ledger view or generate reports:</p>
        <ul>
            <li><strong>Export to CSV</strong>: Export the current ledger view to a CSV file.</li>
            <li><strong>Generate Report</strong>: Create a formatted report of the current ledger view.</li>
        </ul>
        
        <h2>Tips</h2>
        <ul>
            <li>Double-click on an entry to view its details.</li>
            <li>Use the date range filters to focus on specific time periods.</li>
            <li>The Type column is color-coded: green for Credit and red for Debit.</li>
            <li>Before deleting an entry, make sure you understand how it will affect your balance.</li>
        </ul>
        """
    
    def getInvoiceGenerationHelp(self):
        """Get help content for Invoice Generation"""
        return """
        <h1>Invoice Generation</h1>
        
        <p>The Invoice Generator allows you to create professional invoices based on your transaction data or by manually adding items.</p>
        
        <h2>Creating a New Invoice</h2>
        
        <h3>Invoice Information</h3>
        <ol>
            <li>Navigate to the <strong>Invoice Generator</strong> in the application.</li>
            <li>The <strong>Invoice Number</strong> is generated automatically, but you can modify it if needed.</li>
            <li>Set the <strong>Invoice Date</strong> (defaults to today).</li>
            <li>Set the <strong>Due Date</strong> (defaults to 30 days from today).</li>
            <li>Select the <strong>Customer</strong> from the dropdown list.</li>
            <li>Enter your <strong>Company Name</strong> and <strong>Address</strong> information.</li>
            <li>Optionally, you can add a company logo by clicking the <strong>Select Logo</strong> button.</li>
        </ol>
        
        <h3>Adding Invoice Items</h3>
        <p>You can add items to the invoice in two ways:</p>
        
        <h4>Manually Adding Items</h4>
        <ol>
            <li>Click the <strong>Add Item</strong> button.</li>
            <li>Enter the <strong>Product</strong> name.</li>
            <li>Add a <strong>Description</strong> for the item.</li>
            <li>Specify the <strong>Quantity</strong>.</li>
            <li>Set the <strong>Unit Price</strong>.</li>
            <li>Click <strong>Add</strong> to add the item to the invoice.</li>
        </ol>
        
        <h4>Adding from Transactions</h4>
        <ol>
            <li>Click the <strong>Add from Transactions</strong> button.</li>
            <li>Set the date range to search for transactions.</li>
            <li>Click <strong>Search</strong> to find transactions for the selected customer.</li>
            <li>Check the boxes next to the transactions you want to include.</li>
            <li>Click <strong>Add Selected Items</strong> to add them to the invoice.</li>
        </ol>
        
        <h3>Managing Invoice Items</h3>
        <ul>
            <li>To remove an item, click the <strong>Remove</strong> button next to the item.</li>
            <li>To clear all items, click the <strong>Clear All Items</strong> button.</li>
            <li>The <strong>Subtotal</strong>, <strong>Tax Amount</strong>, and <strong>Total</strong> are calculated automatically.</li>
            <li>You can set the <strong>Tax Rate</strong> percentage as needed.</li>
        </ul>
        
        <h3>Notes and Terms</h3>
        <p>You can add custom notes or terms and conditions to the invoice using the <strong>Notes & Terms</strong> section.</p>
        
        <h3>Invoice Actions</h3>
        <p>Once your invoice is complete, you have several options:</p>
        <ul>
            <li><strong>Preview Invoice</strong>: See how the invoice will look before saving or printing.</li>
            <li><strong>Save as PDF</strong>: Save the invoice as a PDF file.</li>
            <li><strong>Print</strong>: Send the invoice directly to a printer.</li>
        </ul>
        
        <h2>Tips</h2>
        <ul>
            <li>Always double-check the customer information and items before saving or printing.</li>
            <li>Using the <strong>Add from Transactions</strong> feature ensures accuracy and saves time.</li>
            <li>You can customize the notes section to include payment instructions or thank you messages.</li>
            <li>Save invoices as PDFs for easy sharing via email.</li>
            <li>Make sure your company information is correct as it appears on all invoices.</li>
        </ul>
        """
    
    def getBackupRestoreHelp(self):
        """Get help content for Backup and Restore"""
        return """
        <h1>Backup and Restore</h1>
        
        <p>Backing up your data regularly is essential to prevent data loss. The Medical Rep Transaction Software provides tools to easily backup and restore your database.</p>
        
        <h2>Manual Backup</h2>
        
        <h3>Creating a Manual Backup</h3>
        <ol>
            <li>Go to the <strong>Settings</strong> tab in the main application window.</li>
            <li>Locate the <strong>Backup & Restore</strong> section.</li>
            <li>Check that the <strong>Backup Location</strong> is set to your preferred directory.</li>
            <li>Click the <strong>Create Manual Backup</strong> button.</li>
            <li>The system will create a timestamped backup file of your database.</li>
            <li>A confirmation message will show the location of the backup file.</li>
        </ol>
        
        <h3>Recent Backups</h3>
        <p>The <strong>Recent Backups</strong> list shows all backup files in your backup directory, sorted by date (newest first). Each entry shows the filename and creation date.</p>
        
        <h2>Restoring from Backup</h2>
        
        <h3>Restoring a Database</h3>
        <ol>
            <li>Go to the <strong>Settings</strong> tab in the main application window.</li>
            <li>Locate the <strong>Backup & Restore</strong> section.</li>
            <li>Click the <strong>Restore from Backup</strong> button.</li>
            <li>A dialog will appear showing all available backup files.</li>
            <li>Select the backup file you want to restore from.</li>
            <li>Click <strong>OK</strong> to proceed with the restoration.</li>
            <li>The system will automatically create a backup of your current database before restoring.</li>
        </ol>
        
        <div style="background-color: #ffe0e0; padding: 10px; border: 1px solid #ff0000; margin: 10px 0;">
            <strong>Warning:</strong> Restoring from a backup will overwrite your current database. 
            Make sure you understand the implications before proceeding.
        </div>
        
        <h2>Scheduled Backups</h2>
        
        <h3>Setting Up Scheduled Backups</h3>
        <ol>
            <li>Go to the <strong>Settings</strong> tab in the main application window.</li>
            <li>Locate the <strong>Backup & Restore</strong> section.</li>
            <li>Click the <strong>Schedule Backups</strong> button.</li>
            <li>In the dialog that appears:
                <ul>
                    <li>Check the <strong>Enable scheduled backups</strong> box.</li>
                    <li>Select the <strong>Backup frequency</strong> (Daily, Weekly, or Monthly).</li>
                    <li>Set the <strong>Backup time</strong> (when the backup should run).</li>
                    <li>Specify how many backup files to keep with <strong>Keep last N backups</strong>.</li>
                </ul>
            </li>
            <li>Click <strong>OK</strong> to save the schedule.</li>
        </ol>
        
        <h2>Cloud Synchronization</h2>
        
        <h3>Setting Up Cloud Sync</h3>
        <ol>
            <li>Go to the <strong>Settings</strong> tab in the main application window.</li>
            <li>Locate the <strong>Cloud Sync Information</strong> section.</li>
            <li>Click the <strong>Setup Cloud Sync</strong> button.</li>
            <li>Follow the instructions to set up synchronization with your cloud storage provider (OneDrive, Dropbox, or Google Drive).</li>
        </ol>
        
        <h2>Best Practices for Backups</h2>
        <ul>
            <li>Create manual backups before making significant changes to your data.</li>
            <li>Enable scheduled backups to automate the backup process.</li>
            <li>Keep backup files in multiple locations, including cloud storage.</li>
            <li>Regularly test the restoration process to ensure your backups are valid.</li>
            <li>Keep track of what changes were made since your last backup.</li>
        </ul>
        """