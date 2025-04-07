"""Main entry point for the WhatsApp Bot application"""
import sys
from PySide6.QtWidgets import QApplication
from src.gui.main_window import WhatsAppBotWindow

def main():
    """Main application entry point"""
    app = QApplication(sys.argv)
    window = WhatsAppBotWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == '__main__':
    main() 