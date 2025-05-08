import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel, QTabWidget

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Medical Rep Transaction Software")
        self.setGeometry(100, 100, 800, 600)
        
        # Create tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Create tab placeholders
        self.create_new_entry_tab()
        self.create_ledger_tab()
        self.create_graphs_tab()
        self.create_settings_tab()
    
    def create_new_entry_tab(self):
        tab = QLabel("New Entry Tab - Coming Soon")
        self.tabs.addTab(tab, "New Entry")
    
    def create_ledger_tab(self):
        tab = QLabel("Ledger Tab - Coming Soon")
        self.tabs.addTab(tab, "Ledger")
    
    def create_graphs_tab(self):
        tab = QLabel("Graphs Tab - Coming Soon")
        self.tabs.addTab(tab, "Graphs")
    
    def create_settings_tab(self):
        tab = QLabel("Settings Tab - Coming Soon")
        self.tabs.addTab(tab, "Settings")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())