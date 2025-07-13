from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget, QTreeWidgetItem,
    QTextBrowser, QSplitter, QLabel, QPushButton, QDialog,
    QLineEdit, QMessageBox
)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QPixmap
import os
import sys

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.database.mongo_adapter import MongoAdapter

class HelpBrowser(QWidget):
    def __init__(self, mongo_adapter=None):
        super().__init__()
        try:
            self.mongo_adapter = mongo_adapter or MongoAdapter()
            self.setWindowTitle("Medical Rep Transaction Software - Help")
            self.setMinimumSize(900, 600)
            self.initUI()
        except Exception as e:
            print(f"Error initializing Help Browser: {e}")
            self.createErrorUI(str(e))
    
    def createErrorUI(self, error_message):
        """Create a minimal error UI when initialization fails"""
        layout = QVBoxLayout()
        
        error_label = QLabel(f"Help system temporarily unavailable\n\nError: {error_message}")
        error_label.setAlignment(Qt.AlignCenter)
        error_label.setStyleSheet("color: #e74c3c; font-weight: bold; padding: 20px;")
        
        retry_btn = QPushButton("Retry Initialization")
        retry_btn.clicked.connect(self.retryInitialization)
        
        layout.addWidget(error_label)
        layout.addWidget(retry_btn)
        layout.addStretch()
        
        self.setLayout(layout)
    
    def retryInitialization(self):
        """Retry initializing the help browser"""
        try:
            # Clear current layout
            if self.layout():
                QWidget().setLayout(self.layout())
            
            # Retry initialization
            self.__init__(self.mongo_adapter)
            
        except Exception as e:
            print(f"Retry failed: {e}")
            QMessageBox.critical(self, "Initialization Failed", 
                               f"Failed to initialize Help Browser: {str(e)}")
        
    def initUI(self):
        """Initialize the UI components"""
        main_layout = QVBoxLayout()
        
        # Header
        header_layout = QHBoxLayout()
        
        header_label = QLabel("Medical Rep Transaction Software - Help & Documentation")
        header_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #4B0082;")
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("Search help topics...")
        search_box.textChanged.connect(self.searchHelp)
        search_box.setStyleSheet("""
            QLineEdit {
                padding: 8px;
                border: 2px solid #4B0082;
                border-radius: 5px;
                font-size: 14px;
            }
        """)
        
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
        self.topics_tree.setStyleSheet("""
            QTreeWidget {
                border: 1px solid #4B0082;
                border-radius: 5px;
            }
            QTreeWidget::item:selected {
                background-color: #4B0082;
                color: white;
            }
        """)
        
        # Help content
        self.help_content = QTextBrowser()
        self.help_content.setOpenExternalLinks(True)
        self.help_content.setStyleSheet("""
            QTextBrowser {
                border: 1px solid #4B0082;
                border-radius: 5px;
                padding: 10px;
            }
        """)
        
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
        
        # MongoDB Features
        mongodb_features = QTreeWidgetItem(self.topics_tree, ["MongoDB Features"])
        QTreeWidgetItem(mongodb_features, ["MongoDB Connection"])
        QTreeWidgetItem(mongodb_features, ["Data Migration"])
        QTreeWidgetItem(mongodb_features, ["Cloud Database"])
        QTreeWidgetItem(mongodb_features, ["Performance Benefits"])
        
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
        QTreeWidgetItem(advanced_features, ["Enhanced Analytics"])
        QTreeWidgetItem(advanced_features, ["Data Import/Export"])
        
        # Data Management
        data_management = QTreeWidgetItem(self.topics_tree, ["Data Management"])
        QTreeWidgetItem(data_management, ["MongoDB Backup"])
        QTreeWidgetItem(data_management, ["Cloud Synchronization"])
        QTreeWidgetItem(data_management, ["Database Maintenance"])
        QTreeWidgetItem(data_management, ["Data Security"])
        
        # Troubleshooting
        troubleshooting = QTreeWidgetItem(self.topics_tree, ["Troubleshooting"])
        QTreeWidgetItem(troubleshooting, ["Common Issues"])
        QTreeWidgetItem(troubleshooting, ["MongoDB Connection Issues"])
        QTreeWidgetItem(troubleshooting, ["Error Messages"])
        QTreeWidgetItem(troubleshooting, ["Data Recovery"])
        
        # Expand the first level
        self.topics_tree.expandItem(getting_started)
        self.topics_tree.expandItem(mongodb_features)

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
        elif category == "MongoDB Features":
            self.help_content.setHtml(self.getMongoDBFeaturesOverview())
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
        # MongoDB-specific topics
        if category == "MongoDB Features" and topic == "MongoDB Connection":
            self.help_content.setHtml(self.getMongoDBConnectionHelp())
        elif category == "MongoDB Features" and topic == "Data Migration":
            self.help_content.setHtml(self.getDataMigrationHelp())
        elif category == "MongoDB Features" and topic == "Cloud Database":
            self.help_content.setHtml(self.getCloudDatabaseHelp())
        elif category == "MongoDB Features" and topic == "Performance Benefits":
            self.help_content.setHtml(self.getPerformanceBenefitsHelp())
        elif category == "Basic Features" and topic == "Adding New Entries":
            self.help_content.setHtml(self.getNewEntriesHelp())
        elif category == "Basic Features" and topic == "Managing the Ledger":
            self.help_content.setHtml(self.getLedgerHelp())
        elif category == "Advanced Features" and topic == "Enhanced Analytics":
            self.help_content.setHtml(self.getEnhancedAnalyticsHelp())
        elif category == "Data Management" and topic == "MongoDB Backup":
            self.help_content.setHtml(self.getMongoDBBackupHelp())
        elif category == "Troubleshooting" and topic == "MongoDB Connection Issues":
            self.help_content.setHtml(self.getMongoDBTroubleshootingHelp())
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
        <h1>Welcome to Medical Rep Transaction Software ()</h1>
        <p>This help system will guide you through using the Medical Rep Transaction Software with MongoDB database integration.</p>
        
        <h2>About the Software</h2>
        <p>Medical Rep Transaction Software is designed to help medical representatives track their sales, manage customer relationships, and generate reports and invoices. This  provides enhanced performance, scalability, and cloud integration capabilities.</p>
        
        <h2>MongoDB Benefits</h2>
        <ul>
            <li>🚀 <strong>Enhanced Performance</strong> - Faster data processing and retrieval</li>
            <li>☁️ <strong>Cloud Integration</strong> - Seamless cloud database connectivity</li>
            <li>📊 <strong>Advanced Analytics</strong> - Powerful aggregation and reporting capabilities</li>
            <li>🔒 <strong>Data Security</strong> - Enterprise-grade security features</li>
            <li>📈 <strong>Scalability</strong> - Grows with your business needs</li>
        </ul>
        
        <h2>Getting Help</h2>
        <p>To get help on a specific topic, browse the topics in the tree on the left side of this window, or use the search box at the top to find specific information.</p>
        
        <h2>Key Features</h2>
        <ul>
            <li>Recording sales transactions with MongoDB backend</li>
            <li>Advanced customer relationship management</li>
            <li>Comprehensive product data management</li>
            <li>Enhanced reports and interactive graphs</li>
            <li>Professional invoice generation</li>
            <li>Cloud-based backup and synchronization</li>
            <li>Real-time analytics dashboard</li>
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
    
    def getMongoDBFeaturesOverview(self):
        """Get the MongoDB Features overview content"""
        return """
        <h1>MongoDB Features</h1>
        
        <p>This section covers the powerful MongoDB features integrated into the Medical Rep Transaction Software.</p>
        
        <h2>Topics in this Section</h2>
        <ul>
            <li><strong>MongoDB Connection</strong> - Setting up and testing your MongoDB connection</li>
            <li><strong>Data Migration</strong> - Migrating existing data to MongoDB</li>
            <li><strong>Cloud Database</strong> - Using MongoDB Atlas for cloud database solutions</li>
            <li><strong>Performance Benefits</strong> - Advantages of using MongoDB for data management</li>
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
            <li><strong>Enhanced Analytics</strong> - Advanced reporting and data analysis tools</li>
            <li><strong>Data Import/Export</strong> - Importing and exporting data to and from other systems</li>
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
            <li><strong>MongoDB Backup</strong> - How to back up your MongoDB data</li>
            <li><strong>Cloud Synchronization</strong> - Keeping your data synchronized across multiple devices</li>
            <li><strong>Database Maintenance</strong> - Maintaining database performance and integrity</li>
            <li><strong>Data Security</strong> - Ensuring the security of your data in MongoDB</li>
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
            <li><strong>MongoDB Connection Issues</strong> - Troubleshooting MongoDB connection problems</li>
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
    
    def getMongoDBConnectionHelp(self):
        """Get MongoDB connection help content"""
        return """
        <h1>MongoDB Connection</h1>
        
        <p>The Medical Rep Transaction Software uses MongoDB as its database backend, providing enhanced performance and scalability.</p>
        
        <h2>Connection Setup</h2>
        
        <h3>Local MongoDB Installation</h3>
        <ol>
            <li>Download and install MongoDB Community Edition from the official MongoDB website.</li>
            <li>Start the MongoDB service on your computer.</li>
            <li>The software will automatically connect to the local MongoDB instance on the default port (27017).</li>
        </ol>
        
        <h3>Cloud MongoDB (MongoDB Atlas)</h3>
        <ol>
            <li>Create a free account at <a href="https://www.mongodb.com/cloud/atlas">MongoDB Atlas</a>.</li>
            <li>Create a new cluster and database.</li>
            <li>Get your connection string from the MongoDB Atlas dashboard.</li>
            <li>In the software settings, enter your MongoDB connection string.</li>
            <li>Test the connection to ensure it's working properly.</li>
        </ol>
        
        <h2>Connection Configuration</h2>
        <p>You can configure the MongoDB connection in the application settings:</p>
        <ul>
            <li><strong>Connection String</strong>: The MongoDB connection URI</li>
            <li><strong>Database Name</strong>: The name of your database (default: medtran_db)</li>
            <li><strong>Connection Timeout</strong>: Maximum time to wait for connection</li>
            <li><strong>Auto-Retry</strong>: Automatically retry failed connections</li>
        </ul>
        
        <h2>Connection Status</h2>
        <p>The application shows the connection status in the status bar:</p>
        <ul>
            <li>🟢 <strong>Connected</strong>: Successfully connected to MongoDB</li>
            <li>🟡 <strong>Connecting</strong>: Attempting to establish connection</li>
            <li>🔴 <strong>Disconnected</strong>: No connection to MongoDB</li>
        </ul>
        
        <h2>Benefits of MongoDB Integration</h2>
        <ul>
            <li><strong>Flexible Schema</strong>: Easily adapt to changing business requirements</li>
            <li><strong>Horizontal Scaling</strong>: Scale across multiple servers as needed</li>
            <li><strong>Rich Queries</strong>: Advanced querying and aggregation capabilities</li>
            <li><strong>High Availability</strong>: Built-in replication and failover</li>
            <li><strong>Cloud Ready</strong>: Native cloud integration and deployment</li>
        </ul>
        
        <h2>Troubleshooting Connection Issues</h2>
        <p>If you're experiencing connection problems:</p>
        <ol>
            <li>Check that MongoDB service is running</li>
            <li>Verify your connection string is correct</li>
            <li>Ensure your firewall allows MongoDB connections</li>
            <li>Check your network connectivity</li>
            <li>Review the application logs for detailed error messages</li>
        </ol>
        """
    
    def getDataMigrationHelp(self):
        """Get data migration help content"""
        return """
        <h1>Data Migration to MongoDB</h1>
        
        <p>If you're upgrading from a previous version with SQLite, the software provides tools to migrate your existing data to MongoDB.</p>
        
        <h2>Automatic Migration</h2>
        <p>When you first run the  with existing SQLite data:</p>
        <ol>
            <li>The software will detect your existing SQLite database</li>
            <li>A migration wizard will appear automatically</li>
            <li>Follow the on-screen instructions to migrate your data</li>
            <li>Your original SQLite data will be preserved as a backup</li>
        </ol>
        
        <h2>Manual Migration</h2>
        <p>You can also perform manual migration:</p>
        <ol>
            <li>Go to <strong>Settings</strong> → <strong>Data Migration</strong></li>
            <li>Select your SQLite database file</li>
            <li>Choose the MongoDB connection settings</li>
            <li>Click <strong>Start Migration</strong></li>
            <li>Wait for the migration to complete</li>
        </ol>
        
        <h2>Migration Process</h2>
        <p>The migration process includes:</p>
        <ul>
            <li><strong>Data Validation</strong>: Ensures data integrity before migration</li>
            <li><strong>Schema Mapping</strong>: Converts SQLite schema to MongoDB collections</li>
            <li><strong>Data Transfer</strong>: Moves all records with progress tracking</li>
            <li><strong>Verification</strong>: Confirms all data was migrated successfully</li>
            <li><strong>Backup Creation</strong>: Creates backups of both old and new data</li>
        </ul>
        
        <h2>What Gets Migrated</h2>
        <ul>
            <li>All customer records</li>
            <li>Complete product catalog</li>
            <li>Transaction history</li>
            <li>Entry records</li>
            <li>User settings and preferences</li>
        </ul>
        
        <h2>Post-Migration</h2>
        <p>After successful migration:</p>
        <ul>
            <li>Verify your data appears correctly in the application</li>
            <li>Test all major functions (adding entries, generating reports)</li>
            <li>Create a backup of your new MongoDB database</li>
            <li>Update any external integrations to use the new database</li>
        </ul>
        
        <h2>Rollback Options</h2>
        <p>If you need to rollback:</p>
        <ul>
            <li>Your original SQLite database is preserved</li>
            <li>You can switch back to SQLite mode in settings</li>
            <li>Contact support if you need assistance with rollback</li>
        </ul>
        """
    
    def getEnhancedAnalyticsHelp(self):
        """Get enhanced analytics help content"""
        return """
        <h1>Enhanced Analytics ()</h1>
        
        <p>The  provides powerful analytics capabilities through the Enhanced Reports tab, offering deep insights into your business data.</p>
        
        <h2>Available Analytics</h2>
        
        <h3>Customer Analytics</h3>
        <ul>
            <li><strong>Top Customers by Revenue</strong>: Identify your most valuable customers</li>
            <li><strong>Customer Segmentation</strong>: Categorize customers by value and activity</li>
            <li><strong>Customer Lifetime Value</strong>: Track long-term customer relationships</li>
            <li><strong>Purchase Patterns</strong>: Analyze buying behavior and trends</li>
        </ul>
        
        <h3>Product Performance</h3>
        <ul>
            <li><strong>Best-Selling Products</strong>: Track top performers by sales volume</li>
            <li><strong>Revenue by Product</strong>: Analyze profitability across your catalog</li>
            <li><strong>Batch Analysis</strong>: Monitor performance by product batches</li>
            <li><strong>Seasonal Trends</strong>: Identify seasonal demand patterns</li>
        </ul>
        
        <h3>Sales Trends</h3>
        <ul>
            <li><strong>Time-Series Analysis</strong>: Track sales over daily, weekly, monthly periods</li>
            <li><strong>Growth Rate Calculations</strong>: Measure business growth metrics</li>
            <li><strong>Forecasting</strong>: Predict future sales based on historical data</li>
            <li><strong>Comparative Analysis</strong>: Compare performance across time periods</li>
        </ul>
        
        <h3>Financial Analysis</h3>
        <ul>
            <li><strong>Credit vs Debit Analysis</strong>: Track money flow in your business</li>
            <li><strong>Outstanding Balances</strong>: Monitor customer payment status</li>
            <li><strong>Profit Margins</strong>: Calculate profitability by product/customer</li>
            <li><strong>Cash Flow Analysis</strong>: Track financial health over time</li>
        </ul>
        
        <h3>Inventory Management</h3>
        <ul>
            <li><strong>Expiry Tracking</strong>: Monitor products approaching expiry dates</li>
            <li><strong>Stock Movement</strong>: Track inventory turnover rates</li>
            <li><strong>Reorder Alerts</strong>: Get notified when stock is low</li>
            <li><strong>Waste Analysis</strong>: Identify expired or slow-moving inventory</li>
        </ul>
        
        <h2>Using the Analytics Dashboard</h2>
        <ol>
            <li>Navigate to the <strong>Enhanced Reports</strong> tab</li>
            <li>Select the type of analysis you want to perform</li>
            <li>Set your date range and filters</li>
            <li>Click <strong>Generate Report</strong> to create the analysis</li>
            <li>Use the interactive charts and tables to explore your data</li>
        </ol>
        
        <h2>Export and Sharing</h2>
        <p>Analytics reports can be:</p>
        <ul>
            <li><strong>Exported to CSV</strong>: For further analysis in Excel or other tools</li>
            <li><strong>Saved as PDF</strong>: For sharing with stakeholders</li>
            <li><strong>Printed</strong>: For physical documentation</li>
            <li><strong>Scheduled</strong>: Set up automatic report generation</li>
        </ul>
        
        <h2>MongoDB Advantages for Analytics</h2>
        <ul>
            <li><strong>Aggregation Pipeline</strong>: Complex data processing in the database</li>
            <li><strong>Real-time Calculations</strong>: Fast computation of metrics and KPIs</li>
            <li><strong>Flexible Queries</strong>: Ad-hoc analysis without predefined schemas</li>
            <li><strong>Large Dataset Handling</strong>: Process millions of records efficiently</li>
        </ul>
        
        <h2>Best Practices</h2>
        <ul>
            <li>Regular review of key metrics to identify trends</li>
            <li>Use filters to focus on specific time periods or segments</li>
            <li>Export important analyses for historical comparison</li>
            <li>Set up alerts for critical business metrics</li>
            <li>Share insights with your team for collaborative decision-making</li>
        </ul>
        """
    
    def getMongoDBBackupHelp(self):
        """Get MongoDB backup help content"""
        return """
        <h1>MongoDB Backup and Recovery</h1>
        
        <p>Protecting your data with regular backups is crucial. The  provides comprehensive backup and recovery options.</p>
        
        <h2>Backup Types</h2>
        
        <h3>Application-Level Backup</h3>
        <p>The software provides built-in backup functionality:</p>
        <ol>
            <li>Go to <strong>Settings</strong> → <strong>Backup & Restore</strong></li>
            <li>Click <strong>Create Backup</strong></li>
            <li>Choose backup location and format</li>
            <li>The backup will include all collections and data</li>
        </ol>
        
        <h3>MongoDB Native Backup</h3>
        <p>For advanced users, MongoDB provides native backup tools:</p>
        <ul>
            <li><strong>mongodump</strong>: Create binary backups of your database</li>
            <li><strong>mongoexport</strong>: Export data in JSON or CSV format</li>
            <li><strong>Atlas Backup</strong>: Automated cloud backups for Atlas users</li>
        </ul>
        
        <h2>Scheduled Backups</h2>
        <p>Set up automatic backups:</p>
        <ol>
            <li>Go to <strong>Settings</strong> → <strong>Backup Schedule</strong></li>
            <li>Enable automatic backups</li>
            <li>Set frequency (daily, weekly, monthly)</li>
            <li>Choose backup retention period</li>
            <li>Configure notification preferences</li>
        </ol>
        
        <h2>Cloud Backup Integration</h2>
        <p>Integrate with cloud storage services:</p>
        <ul>
            <li><strong>MongoDB Atlas</strong>: Automatic cloud backups</li>
            <li><strong>Google Drive</strong>: Sync backups to Google Drive</li>
            <li><strong>Dropbox</strong>: Store backups in Dropbox</li>
            <li><strong>OneDrive</strong>: Microsoft cloud storage integration</li>
        </ul>
        
        <h2>Backup Verification</h2>
        <p>Ensure backup integrity:</p>
        <ul>
            <li>Regular test restores to verify backup validity</li>
            <li>Checksum verification for data integrity</li>
            <li>Monitor backup logs for errors or warnings</li>
            <li>Validate backup completeness against source data</li>
        </ul>
        
        <h2>Restore Process</h2>
        <ol>
            <li>Go to <strong>Settings</strong> → <strong>Restore</strong></li>
            <li>Select the backup file to restore from</li>
            <li>Choose restore options (full or partial)</li>
            <li>Confirm the restore operation</li>
            <li>Wait for the restore process to complete</li>
        </ol>
        
        <h2>Disaster Recovery</h2>
        <p>Prepare for disaster scenarios:</p>
        <ul>
            <li>Maintain multiple backup copies in different locations</li>
            <li>Document recovery procedures and contact information</li>
            <li>Test disaster recovery scenarios regularly</li>
            <li>Keep backup media secure and accessible</li>
            <li>Plan for both local and cloud recovery options</li>
        </ul>
        
        <h2>Best Practices</h2>
        <ul>
            <li><strong>3-2-1 Rule</strong>: 3 copies, 2 different media, 1 offsite</li>
            <li><strong>Regular Testing</strong>: Test restore procedures monthly</li>
            <li><strong>Documentation</strong>: Keep detailed backup and recovery procedures</li>
            <li><strong>Monitoring</strong>: Set up alerts for backup failures</li>
            <li><strong>Security</strong>: Encrypt backups and secure access</li>
        </ul>
        
        <h2>Recovery Time Objectives</h2>
        <p>Plan for different recovery scenarios:</p>
        <ul>
            <li><strong>Point-in-time Recovery</strong>: Restore to specific timestamp</li>
            <li><strong>Full Recovery</strong>: Complete database restoration</li>
            <li><strong>Partial Recovery</strong>: Restore specific collections or data</li>
            <li><strong>Cross-platform Recovery</strong>: Restore across different environments</li>
        </ul>
        """
    
    def getMongoDBTroubleshootingHelp(self):
        """Get MongoDB troubleshooting help content"""
        return """
        <h1>MongoDB Connection Troubleshooting</h1>
        
        <p>This guide helps you resolve common MongoDB connection and performance issues.</p>
        
        <h2>Common Connection Issues</h2>
        
        <h3>Connection Refused</h3>
        <p><strong>Symptoms:</strong> "Connection refused" or "Unable to connect to MongoDB"</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Verify MongoDB service is running: <code>systemctl status mongod</code> (Linux) or check Services (Windows)</li>
            <li>Check if MongoDB is listening on the correct port (default: 27017)</li>
            <li>Verify firewall settings allow connections to MongoDB port</li>
            <li>Ensure MongoDB configuration file allows connections from your IP</li>
        </ul>
        
        <h3>Authentication Failed</h3>
        <p><strong>Symptoms:</strong> "Authentication failed" or "Invalid credentials"</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Verify username and password are correct</li>
            <li>Check authentication database is specified correctly</li>
            <li>Ensure user has proper permissions for the database</li>
            <li>For Atlas: verify connection string includes correct credentials</li>
        </ul>
        
        <h3>Network Timeout</h3>
        <p><strong>Symptoms:</strong> "Connection timeout" or "Network unreachable"</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Check internet connectivity for cloud databases</li>
            <li>Verify DNS resolution for MongoDB hostname</li>
            <li>Test connection with MongoDB shell or compass</li>
            <li>Increase connection timeout in application settings</li>
        </ul>
        
        <h2>Performance Issues</h2>
        
        <h3>Slow Query Performance</h3>
        <p><strong>Symptoms:</strong> Reports and charts take long time to load</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Check database indexes are properly configured</li>
            <li>Monitor MongoDB performance with built-in profiler</li>
            <li>Optimize aggregation pipelines in analytics queries</li>
            <li>Consider upgrading MongoDB server resources</li>
        </ul>
        
        <h3>Memory Usage Issues</h3>
        <p><strong>Symptoms:</strong> High memory usage or out-of-memory errors</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Adjust MongoDB cache size settings</li>
            <li>Implement data archiving for old records</li>
            <li>Use projection to limit returned fields</li>
            <li>Consider database sharding for large datasets</li>
        </ul>
        
        <h2>Data Issues</h2>
        
        <h3>Missing or Corrupted Data</h3>
        <p><strong>Symptoms:</strong> Data appears incomplete or incorrect</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Run database consistency checks</li>
            <li>Restore from a known good backup</li>
            <li>Check application logs for error messages</li>
            <li>Verify data migration completed successfully</li>
        </ul>
        
        <h3>Schema Validation Errors</h3>
        <p><strong>Symptoms:</strong> Cannot save new records or updates fail</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Check MongoDB schema validation rules</li>
            <li>Verify data types match expected formats</li>
            <li>Review application validation logic</li>
            <li>Check for required field violations</li>
        </ul>
        
        <h2>Cloud-Specific Issues (Atlas)</h2>
        
        <h3>IP Whitelist Problems</h3>
        <p><strong>Symptoms:</strong> Connection works from some locations but not others</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Add your current IP address to Atlas whitelist</li>
            <li>Use 0.0.0.0/0 for testing (not recommended for production)</li>
            <li>Check if your IP address has changed</li>
            <li>Consider using VPN if IP changes frequently</li>
        </ul>
        
        <h3>Atlas Cluster Paused</h3>
        <p><strong>Symptoms:</strong> Cannot connect to Atlas cluster</p>
        <p><strong>Solutions:</strong></p>
        <ul>
            <li>Check Atlas dashboard for cluster status</li>
            <li>Resume paused clusters manually</li>
            <li>Verify billing information is up to date</li>
            <li>Check for service maintenance notifications</li>
        </ul>
        
        <h2>Diagnostic Tools</h2>
        
        <h3>Built-in Diagnostics</h3>
        <p>The application provides diagnostic tools:</p>
        <ul>
            <li><strong>Connection Test</strong>: Test MongoDB connection from settings</li>
            <li><strong>Performance Monitor</strong>: View query performance metrics</li>
            <li><strong>Data Validation</strong>: Check data integrity and consistency</li>
            <li><strong>Error Logs</strong>: Review detailed error messages and stack traces</li>
        </ul>
        
        <h3>External Tools</h3>
        <ul>
            <li><strong>MongoDB Compass</strong>: Visual database explorer and query tool</li>
            <li><strong>MongoDB Shell</strong>: Command-line interface for database operations</li>
            <li><strong>MongoDB Profiler</strong>: Analyze query performance and optimization</li>
            <li><strong>Atlas Monitoring</strong>: Cloud-based monitoring for Atlas clusters</li>
        </ul>
        
        <h2>Getting Help</h2>
        <p>If you continue to experience issues:</p>
        <ul>
            <li>Check the application error logs for detailed messages</li>
            <li>Consult MongoDB documentation for specific error codes</li>
            <li>Contact support with detailed error information</li>
            <li>Include connection strings (without passwords) and error logs</li>
            <li>Provide information about your MongoDB setup and environment</li>
        </ul>
        """