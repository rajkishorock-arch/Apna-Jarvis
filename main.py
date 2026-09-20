import sys
from PySide6.QtWidgets import QApplication
from gui.dashboard import DashboardWindow

def main():
    # Initialize the PySide6 application event loop
    app = QApplication(sys.argv)
    
    # Create and show the primary dashboard window
    window = DashboardWindow()
    window.show()
    
    # Execute the application loop and exit cleanly
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
