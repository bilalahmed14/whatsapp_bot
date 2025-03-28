import sys
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout,
                            QGroupBox, QMessageBox, QSplitter)
from PySide6.QtCore import QUrl
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
from bot_controller import WhatsAppBotController

class WhatsAppBot(QMainWindow):
    """Main application window for WhatsApp Chat Bot"""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Chat Bot")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up persistent storage directory
        self.profile_dir = os.path.join(os.path.expanduser("~"), ".whatsapp_bot_profile")
        if not os.path.exists(self.profile_dir):
            os.makedirs(self.profile_dir)
            
        # Initialize UI components
        self.init_web_view()
        self.init_bot_controller()
        self.init_ui()
        
        # Log initial message
        self.log_status("WhatsApp Bot initialized.")
        self.log_status("Click 'Open WhatsApp Web' to start.")
        self.log_status(f"Browser data stored in: {self.profile_dir}")
    
    def init_web_view(self):
        """Initialize the web view with a persistent profile"""
        # Set up custom web profile
        self.web_profile = QWebEngineProfile("WhatsAppBot", self)
        self.web_profile.setPersistentStoragePath(self.profile_dir)
        self.web_profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        self.web_profile.setHttpUserAgent("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
        
        # Enable required settings
        settings = self.web_profile.settings()
        settings.setAttribute(QWebEngineSettings.LocalStorageEnabled, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.JavascriptEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanAccessClipboard, True)
        
        # Create web view with custom profile
        self.web_view = QWebEngineView()
        self.web_view.setPage(QWebEnginePage(self.web_profile, self.web_view))
        self.web_view.setMinimumSize(800, 600)
        self.web_view.loadFinished.connect(self.on_page_loaded)
        self.web_view.urlChanged.connect(self.update_url_bar)
        
    def init_bot_controller(self):
        """Initialize the bot controller"""
        self.bot_controller = WhatsAppBotController(self.web_view)
        self.bot_controller.status_signal.connect(self.log_status)
        self.bot_controller.error_signal.connect(self.show_error)
        
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
        
        # URL Bar
        self.setup_url_bar(right_layout)
        
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
        
    def setup_url_bar(self, parent_layout):
        """Set up the URL bar"""
        # Add system prompt input first
        prompt_container = QWidget()
        prompt_layout = QVBoxLayout(prompt_container)
        prompt_layout.setContentsMargins(2, 2, 2, 2)
        prompt_layout.setSpacing(2)
        
        prompt_label = QLabel("System Prompt:")
        self.prompt_input = QTextEdit()
        self.prompt_input.setPlaceholderText("Customize the bot's behavior")
        self.prompt_input.setMaximumHeight(80)  # Limit height
        self.prompt_input.setReadOnly(False)  # Ensure it's editable by default
        
        # Set the default prompt text if available
        if hasattr(self, 'bot_controller') and self.bot_controller:
            default_prompt = self.bot_controller.get_system_prompt()
            if default_prompt:
                self.prompt_input.setText(default_prompt)
        
        prompt_layout.addWidget(prompt_label)
        prompt_layout.addWidget(self.prompt_input)
        parent_layout.addWidget(prompt_container)
        
        # Add some styling to make it clear it's editable
        self.prompt_input.setStyleSheet("""
            QTextEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
                background: white;
            }
            QTextEdit:focus {
                border: 1px solid #0078D4;
            }
        """)
        
        # Original URL bar code
        url_container = QWidget()
        url_layout = QHBoxLayout(url_container)
        url_layout.setContentsMargins(2, 2, 2, 2)
        url_layout.setSpacing(2)
        
        self.url_bar = QLineEdit()
        self.url_bar.setMaximumHeight(30)
        self.url_bar.setStyleSheet("""
            QLineEdit {
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 2px 5px;
                background: white;
            }
            QLineEdit:focus {
                border: 1px solid #0078D4;
            }
        """)
        self.url_bar.returnPressed.connect(self.navigate_to_url)
        
        self.go_button = QPushButton("Go")
        self.go_button.setMaximumWidth(40)
        self.go_button.setMaximumHeight(30)
        self.go_button.setStyleSheet("""
            QPushButton {
                background-color: #0078D4;
                color: white;
                border: none;
                border-radius: 3px;
                padding: 2px 10px;
            }
            QPushButton:hover {
                background-color: #106EBE;
            }
            QPushButton:pressed {
                background-color: #005A9E;
            }
        """)
        self.go_button.clicked.connect(self.navigate_to_url)
        
        url_layout.addWidget(self.url_bar)
        url_layout.addWidget(self.go_button)
        parent_layout.addWidget(url_container)
        
    def navigate_to_url(self):
        """Navigate to the URL entered in the URL bar"""
        url = self.url_bar.text()
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        self.web_view.setUrl(QUrl(url))
        
    def update_url_bar(self, url):
        """Update the URL bar when the web view URL changes"""
        self.url_bar.setText(url.toString())
        
    def log_status(self, message):
        """Log a status message to the status display"""
        self.status_display.append(message)
        
    def show_error(self, message, title):
        """Show an error message box"""
        QMessageBox.warning(self, title, message)
        
    def open_whatsapp(self):
        """Open WhatsApp Web and let user manually navigate to the chat"""
        self.web_view.setUrl(QUrl("https://web.whatsapp.com"))
        self.open_whatsapp_btn.setEnabled(False)
        self.log_status("Please manually open the chat with your target contact after scanning QR code")
        
    def on_page_loaded(self, success):
        """Handle page load events"""
        if not success:
            self.log_status("Failed to load page")
            return
            
        if self.bot_controller.is_monitoring:
            self.bot_controller.inject_message_monitor()
            
    def start_bot(self):
        """Start the bot monitoring"""
        if not self.bot_controller.model:
            self.show_error("Please initialize the AI model first", "Model Required")
            return
            
        phone_number = self.phone_input.text().strip()
        if not phone_number:
            self.show_error("Please enter a phone number", "Missing Information")
            return
            
        # Update system prompt before starting
        system_prompt = self.prompt_input.toPlainText().strip()
        self.bot_controller.set_system_prompt(system_prompt)
        self.prompt_input.setReadOnly(True)  # Lock prompt editing while bot is running
            
        if self.bot_controller.start_monitoring(phone_number):
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.log_status("Bot started - monitoring messages")
    
    def stop_bot(self):
        """Stop the bot monitoring"""
        self.bot_controller.stop_monitoring()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.prompt_input.setReadOnly(False)  # Allow prompt editing when stopped
        self.log_status("Bot stopped")
        
    def init_llm(self):
        """Initialize the language model"""
        self.init_model_btn.setEnabled(False)
        success = self.bot_controller.init_llm()
        self.model_label.setText(f"Model initialized: {'Yes' if success else 'Error'}")
        self.init_model_btn.setEnabled(True)
        
    def closeEvent(self, event):
        """Handle window close event"""
        self.bot_controller.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppBot()
    window.show()
    sys.exit(app.exec()) 