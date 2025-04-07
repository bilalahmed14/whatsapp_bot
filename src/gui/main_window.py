"""Main window for the WhatsApp Bot application"""
import os
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QLabel, QLineEdit, 
    QPushButton, QTextEdit, QHBoxLayout, QGroupBox, 
    QMessageBox, QSplitter
)
from PySide6.QtCore import Qt

from src.gui.components.web_view import WhatsAppWebView
from src.core.bot_controller import WhatsAppBotController

class WhatsAppBotWindow(QMainWindow):
    """Main application window for WhatsApp Chat Bot"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Chat Bot")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up persistent storage directory
        self.profile_dir = os.path.join(os.path.expanduser("~"), ".whatsapp_bot_profile")
        
        # Initialize components
        self.init_web_view()
        self.init_bot_controller()
        self.init_ui()
        
        # Log initial message
        self.log_status("WhatsApp Bot initialized.")
        self.log_status("Click 'Open WhatsApp Web' to start.")
        self.log_status(f"Browser data stored in: {self.profile_dir}")
    
    def init_web_view(self):
        """Initialize the web view component"""
        self.web_view = WhatsAppWebView(self.profile_dir)
        self.web_view.setMinimumSize(800, 600)
        self.web_view.loadFinished.connect(self.on_page_loaded)
        self.web_view.urlChanged.connect(self.update_url_bar)
        
    def init_bot_controller(self):
        """Initialize the bot controller"""
        self.bot_controller = WhatsAppBotController(self.web_view)
        self.bot_controller.status_signal.connect(self.log_status)
        self.bot_controller.error_signal.connect(self.show_error)
        self.bot_controller.progress_signal.connect(self.update_progress)
        
    def init_ui(self):
        """Initialize the user interface"""
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Create splitter for left and right panels
        splitter = QSplitter()
        main_layout.addWidget(splitter)
        
        # Set up left panel (controls)
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)
        
        # Phone number input group
        self.setup_phone_input_group(left_layout)
        
        # Model settings group
        self.setup_model_settings_group(left_layout)
        
        # Status display
        self.setup_status_display(left_layout)
        
        # Control buttons
        self.setup_control_buttons(left_layout)
        
        # Right side - Web View Container
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        splitter.addWidget(right_widget)
        
        # System prompt input
        self.setup_prompt_input(right_layout)
        
        # Add web view to right panel
        right_layout.addWidget(self.web_view)
        
        # Set initial splitter sizes (30% left, 70% right)
        splitter.setSizes([360, 840])
        
    def setup_phone_input_group(self, parent_layout):
        """Set up the phone number input group"""
        phone_group = QGroupBox("Target Settings")
        phone_layout = QVBoxLayout()
        phone_group.setLayout(phone_layout)
        
        self.phone_label = QLabel("Target Phone Number (with country code):")
        self.phone_input = QLineEdit()
        self.phone_input.setPlaceholderText("+1234567890")
        
        phone_layout.addWidget(self.phone_label)
        phone_layout.addWidget(self.phone_input)
        parent_layout.addWidget(phone_group)
        
    def setup_model_settings_group(self, parent_layout):
        """Set up the model settings group"""
        model_group = QGroupBox("AI Model Settings")
        model_layout = QVBoxLayout()
        model_group.setLayout(model_layout)
        
        self.model_label = QLabel("Model initialized: No")
        self.init_model_btn = QPushButton("Initialize AI Model")
        self.init_model_btn.clicked.connect(self.init_llm)
        
        model_layout.addWidget(self.model_label)
        model_layout.addWidget(self.init_model_btn)
        parent_layout.addWidget(model_group)
        
    def setup_status_display(self, parent_layout):
        """Set up the status display"""
        status_group = QGroupBox("Status Log")
        status_layout = QVBoxLayout()
        status_group.setLayout(status_layout)
        
        self.status_display = QTextEdit()
        self.status_display.setReadOnly(True)
        
        status_layout.addWidget(self.status_display)
        parent_layout.addWidget(status_group)
        
    def setup_control_buttons(self, parent_layout):
        """Set up the control buttons"""
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
        parent_layout.addWidget(buttons_group)
        
    def setup_prompt_input(self, parent_layout):
        """Set up the system prompt input"""
        prompt_container = QWidget()
        prompt_layout = QVBoxLayout(prompt_container)
        prompt_layout.setContentsMargins(2, 2, 2, 2)
        prompt_layout.setSpacing(2)
        
        prompt_label = QLabel("System Prompt:")
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Customize the bot's behavior")
        self.prompt_input.setMaximumHeight(80)
        
        # Set the default prompt text
        default_prompt = self.bot_controller.get_system_prompt()
        if default_prompt:
            self.prompt_input.setText(default_prompt)
        
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(self.prompt_input)
        parent_layout.addWidget(prompt_container)
        
    def log_status(self, message):
        """Add a status message to the log"""
        self.status_display.append(message)
        
    def show_error(self, message, title="Error"):
        """Show an error message box"""
        QMessageBox.critical(self, title, message)
        
    def update_progress(self, value):
        """Update progress in the status display"""
        self.log_status(f"Progress: {value}%")
        
    def on_page_loaded(self, success):
        """Handle page load completion"""
        if success:
            self.log_status("Page loaded successfully")
        else:
            self.log_status("Page failed to load")
            
    def update_url_bar(self, url):
        """Update status when URL changes"""
        self.log_status(f"Navigated to: {url.toString()}")
        
    def init_llm(self):
        """Initialize the language model"""
        if self.bot_controller.init_llm():
            self.model_label.setText("Model initialized: Yes")
            self.init_model_btn.setEnabled(False)
        
    def start_bot(self):
        """Start the bot"""
        phone_number = self.phone_input.text().strip()
        system_prompt = self.prompt_input.toPlainText().strip()
        
        if system_prompt:
            self.bot_controller.set_system_prompt(system_prompt)
            
        if self.bot_controller.start_monitoring(phone_number):
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
        
    def stop_bot(self):
        """Stop the bot"""
        self.bot_controller.stop_monitoring()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        
    def open_whatsapp(self):
        """Open WhatsApp Web"""
        self.web_view.load_whatsapp()
        
    def closeEvent(self, event):
        """Handle application closure"""
        self.bot_controller.cleanup()
        event.accept() 