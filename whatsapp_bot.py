import sys
import time
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout,
                            QGroupBox, QMessageBox, QSplitter)
from PySide6.QtCore import QThread, Signal, QObject, QUrl
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from gpt4all import GPT4All
import subprocess
from bot_controller import WhatsAppBotController

class WhatsAppBot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Chat Bot")
        self.setGeometry(100, 100, 1200, 800)  # Increased window size
        
        # Initialize bot controller
        self.bot_controller = WhatsAppBotController()
        self.bot_controller.status_signal.connect(self.log_status)
        self.bot_controller.error_signal.connect(self.show_error)
        
        # Create main splitter
        main_splitter = QSplitter()
        self.setCentralWidget(main_splitter)
        
        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # Phone number input group
        phone_group = QGroupBox("Target Settings")
        phone_layout = QVBoxLayout()
        phone_group.setLayout(phone_layout)
        
        self.phone_label = QLabel("Target Phone Number (with country code):")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+1234567890")
        phone_layout.addWidget(self.phone_label)
        phone_layout.addWidget(self.phone_input)
        left_layout.addWidget(phone_group)
        
        # Model settings group
        model_group = QGroupBox("AI Model Settings")
        model_layout = QVBoxLayout()
        model_group.setLayout(model_layout)
        
        self.model_label = QLabel("Model initialized: No")
        model_layout.addWidget(self.model_label)
        
        self.init_model_btn = QPushButton("Initialize AI Model")
        self.init_model_btn.clicked.connect(self.init_llm)
        model_layout.addWidget(self.init_model_btn)
        left_layout.addWidget(model_group)
        
        # Status display
        status_group = QGroupBox("Status Log")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        status_layout.addWidget(self.status_display)
        left_layout.addWidget(status_group)
        
        # Control buttons
        buttons_group = QGroupBox("Controls")
        buttons_layout = QVBoxLayout()
        buttons_group.setLayout(buttons_layout)
        
        self.start_button = QPushButton("Start Bot")
        self.stop_button = QPushButton("Stop Bot")
        self.open_whatsapp_btn = QPushButton("Open WhatsApp Web")
        
        self.start_button.clicked.connect(self.start_bot)
        self.stop_button.clicked.connect(self.stop_bot)
        self.open_whatsapp_btn.clicked.connect(self.open_whatsapp)
        
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.open_whatsapp_btn)
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        left_layout.addWidget(buttons_group)
        
        # Right side - Web View
        self.web_view = QWebEngineView()
        
        # Set up web profile
        profile = QWebEngineProfile.defaultProfile()
        profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Add widgets to splitter
        main_splitter.addWidget(left_widget)
        main_splitter.addWidget(self.web_view)
        
        # Set splitter sizes
        main_splitter.setSizes([400, 800])  # Left panel: 400px, Right panel: 800px
        
        # Log initial message
        self.log_status("WhatsApp Bot initialized.")
        self.log_status("Click 'Open WhatsApp Web' to start.")
        
    def log_status(self, message):
        self.status_display.append(message)
        
    def show_error(self, message, title):
        QMessageBox.warning(self, title, message)
        
    def open_whatsapp(self):
        self.web_view.setUrl(QUrl("https://web.whatsapp.com"))
        self.open_whatsapp_btn.setEnabled(False)
        
    def init_llm(self):
        self.init_model_btn.setEnabled(False)
        success = self.bot_controller.init_llm()
        self.model_label.setText(f"Model initialized: {'Yes' if success else 'Error'}")
        self.init_model_btn.setEnabled(True)
        
    def start_bot(self):
        if self.bot_controller.start_monitoring(self.phone_input.text()):
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        
    def stop_bot(self):
        self.bot_controller.stop_monitoring()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def closeEvent(self, event):
        self.bot_controller.cleanup()
        event.accept()

class MessageMonitor(QThread):
    """Thread to monitor for new messages and generate responses"""
    status_signal = Signal(str)
    
    def __init__(self, phone_number, model, driver):
        super().__init__()
        self.phone_number = phone_number
        self.model = model
        self.driver = driver
        self.is_running = False
        self.last_processed_message = ""
        
    def run(self):
        self.is_running = True
        self.status_signal.emit(f"Starting to monitor messages from {self.phone_number}")
        
        while self.is_running:
            try:
                # Wait for messages to appear
                time.sleep(2)
                self.status_signal.emit("Checking for new messages...")
                
                # This is where you would implement the message checking logic
                # For now, we'll just simulate monitoring
                time.sleep(3)
                
            except Exception as e:
                self.status_signal.emit(f"Error while monitoring: {str(e)}")
                time.sleep(5)
        
    def generate_response(self, message):
        """Generate a response using the AI model"""
        if not message:
            return "I couldn't understand your message."
            
        try:
            self.status_signal.emit("Generating response...")
            prompt = f"User: {message}\nAssistant:"
            response = self.model.generate(prompt, max_tokens=100)
            
            if not response:
                return "I'm having trouble generating a response. Please try again."
                
            return response.strip()
            
        except Exception as e:
            self.status_signal.emit(f"Error generating response: {str(e)}")
            return "Sorry, I couldn't process your request at the moment."
        
    def stop(self):
        self.is_running = False

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppBot()
    window.show()
    sys.exit(app.exec()) 