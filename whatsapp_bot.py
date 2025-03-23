import sys
import time
import os
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QLineEdit, QPushButton, QTextEdit, QHBoxLayout,
                            QGroupBox, QMessageBox, QSplitter)
from PySide6.QtCore import QThread, Signal, QObject, QUrl, QTimer
from PySide6.QtGui import QFont
from PySide6.QtWebEngineWidgets import QWebEngineView
from PySide6.QtWebEngineCore import QWebEngineProfile, QWebEngineSettings, QWebEnginePage
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from gpt4all import GPT4All
import subprocess
from bot_controller import WhatsAppBotController
import json

class WhatsAppBot(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp Chat Bot")
        self.setGeometry(100, 100, 1200, 800)
        
        # Set up persistent storage directory
        self.profile_dir = os.path.join(os.path.expanduser("~"), ".whatsapp_bot_profile")
        if not os.path.exists(self.profile_dir):
            os.makedirs(self.profile_dir)
            
        # Initialize bot controller
        self.bot_controller = WhatsAppBotController()
        self.bot_controller.status_signal.connect(self.log_status)
        self.bot_controller.error_signal.connect(self.show_error)
        
        # Initialize message monitoring state
        self.is_monitoring = False
        self.last_processed_message = ""
        
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
        
        # Main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # Create splitter for left and right panels
        splitter = QSplitter()
        main_layout.addWidget(splitter)
        
        # Left side - Controls
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        splitter.addWidget(left_widget)
        
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
        
        # Right side - Web View Container
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)  # Remove all margins
        right_layout.setSpacing(0)  # Remove spacing between elements
        splitter.addWidget(right_widget)
        
        # URL Bar
        url_container = QWidget()
        url_layout = QHBoxLayout(url_container)
        url_layout.setContentsMargins(2, 2, 2, 2)  # Minimal margins
        url_layout.setSpacing(2)  # Minimal spacing
        
        self.url_bar = QLineEdit()
        self.url_bar.setMaximumHeight(30)  # Set maximum height
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
        url_layout.addWidget(self.url_bar)
        
        self.go_button = QPushButton("Go")
        self.go_button.setMaximumWidth(40)  # Make button narrower
        self.go_button.setMaximumHeight(30)  # Match URL bar height
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
        url_layout.addWidget(self.go_button)
        
        right_layout.addWidget(url_container)
        
        # Web View with custom profile
        self.web_view = QWebEngineView()
        self.web_view.setPage(QWebEnginePage(self.web_profile, self.web_view))
        self.web_view.setMinimumSize(800, 600)
        self.web_view.loadFinished.connect(self.on_page_loaded)
        right_layout.addWidget(self.web_view)
        
        # Connect URL changed signal
        self.web_view.urlChanged.connect(self.update_url_bar)
        
        # Set initial splitter sizes (30% left, 70% right)
        splitter.setSizes([360, 840])
        
        # Initialize LLM
        self.model = None
        
        # Log initial message
        self.log_status("WhatsApp Bot initialized.")
        self.log_status("Click 'Open WhatsApp Web' to start.")
        self.log_status(f"Browser data stored in: {self.profile_dir}")
        
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
        self.status_display.append(message)
        
    def show_error(self, message, title):
        QMessageBox.warning(self, title, message)
        
    def open_whatsapp(self):
        """Open WhatsApp Web and let user manually navigate to the chat"""
        self.web_view.setUrl(QUrl("https://web.whatsapp.com"))
        self.open_whatsapp_btn.setEnabled(False)
        self.log_status("Please manually open the chat with your target contact after scanning QR code")
        
    def on_page_loaded(self, success):
        if not success:
            self.log_status("Failed to load page")
            return
            
        if self.is_monitoring:
            self.inject_message_monitor()
            
    def inject_message_monitor(self):
        # JavaScript to extract last 5 text messages from current chat - with simpler syntax
        js_code = """
        (function() {
            try {
                console.log('Starting message analysis');
                
                // Check if WhatsApp is loaded
                if (!document.querySelector('#app')) {
                    console.log('WhatsApp not fully loaded');
                    return JSON.stringify({
                        status: 'waiting',
                        error: 'WhatsApp not fully loaded',
                        messages: []
                    });
                }
                
                // Look for messages using different approaches
                const messages = [];
                
                // Try direct approach to get message text elements
                // Find actual chat conversation elements
                const msgTextElements = document.querySelectorAll('div.focusable-list-item div.copyable-text span.selectable-text');
                console.log('Found ' + msgTextElements.length + ' message text elements');
                
                if (msgTextElements.length > 0) {
                    let count = 0;
                    for (let i = msgTextElements.length - 1; i >= 0 && count < 5; i--) {
                        const textEl = msgTextElements[i];
                        const text = textEl.innerText.trim();
                        
                        if (text && text.length > 0) {
                            // Determine if outgoing by walking up to container
                            let container = textEl;
                            for (let j = 0; j < 10 && container; j++) {
                                if (container.className && typeof container.className === 'string') {
                                    container = container.parentElement;
                                } else {
                                    break;
                                }
                            }
                            
                            // Check if message is outgoing
                            const isOutgoing = container && 
                                          container.parentElement && 
                                          container.parentElement.className && 
                                          typeof container.parentElement.className === 'string' && 
                                          container.parentElement.className.indexOf('message-out') >= 0;
                            
                            messages.unshift({
                                text: text,
                                isOutgoing: isOutgoing,
                                timestamp: new Date().getTime()
                            });
                            count++;
                            console.log('Added message: ' + (isOutgoing ? 'OUT: ' : 'IN:  ') + text.substring(0, 30));
                        }
                    }
                }
                
                // If we couldn't find messages with the above approach, try a different one
                if (messages.length === 0) {
                    // Try to find WhatsApp Web message list
                    const messageList = document.querySelector('#main div.message-list');
                    if (messageList) {
                        const bubbles = messageList.querySelectorAll('div.message-in, div.message-out');
                        console.log('Found ' + bubbles.length + ' message bubbles');
                        
                        let count = 0;
                        for (let i = bubbles.length - 1; i >= 0 && count < 5; i--) {
                            const bubble = bubbles[i];
                            const isOutgoing = bubble.classList.contains('message-out');
                            
                            // Skip if it's a system message or media
                            if (bubble.querySelector('img') || bubble.querySelector('audio')) {
                                continue;
                            }
                            
                            // Find the actual text content
                            const textEl = bubble.querySelector('span.selectable-text');
                            if (textEl) {
                                const text = textEl.innerText.trim();
                                if (text) {
                                    messages.unshift({
                                        text: text,
                                        isOutgoing: isOutgoing,
                                        timestamp: new Date().getTime()
                                    });
                                    count++;
                                }
                            }
                        }
                    }
                }
                
                // If we still couldn't find messages, try a more generic approach
                if (messages.length === 0) {
                    // Look for any span with selectable-text class
                    const textSpans = document.querySelectorAll('span.selectable-text');
                    console.log('Found ' + textSpans.length + ' text spans');
                    
                    if (textSpans.length > 0) {
                        let count = 0;
                        for (let i = textSpans.length - 1; i >= 0 && count < 5; i--) {
                            const span = textSpans[i];
                            // Skip timestamps by checking if the text is a valid message
                            // Timestamps usually follow a pattern like "4:21 AM"
                            const text = span.innerText.trim();
                            
                            // Skip timestamps and very short messages
                            if (!text || text.length < 2 || /^[0-9]{1,2}:[0-9]{2}\s*(AM|PM)$/.test(text)) {
                                continue;
                            }
                            
                            // Determine if outgoing
                            let container = span.parentElement;
                            let isOutgoing = false;
                            
                            while (container) {
                                if (container.className && 
                                    typeof container.className === 'string' && 
                                    container.className.indexOf('message-out') >= 0) {
                                    isOutgoing = true;
                                    break;
                                }
                                container = container.parentElement;
                                if (!container) break;
                            }
                            
                            messages.unshift({
                                text: text,
                                isOutgoing: isOutgoing,
                                timestamp: new Date().getTime()
                            });
                            count++;
                            console.log('Added fallback message: ' + (isOutgoing ? 'OUT: ' : 'IN:  ') + text.substring(0, 30));
                        }
                    }
                }
                
                console.log('Extracted ' + messages.length + ' messages');
                for (let i = 0; i < messages.length; i++) {
                    console.log((i+1) + '. ' + 
                               (messages[i].isOutgoing ? 'OUT: ' : 'IN:  ') + 
                               messages[i].text.substring(0, 30));
                }
                
                return JSON.stringify({
                    status: messages.length > 0 ? 'success' : 'waiting',
                    error: messages.length === 0 ? 'No messages found' : '',
                    messages: messages
                });
            } catch (error) {
                console.error('Error in message monitor:', error);
                return JSON.stringify({
                    status: 'error',
                    error: error.toString(),
                    messages: []
                });
            }
        })();
        """
        
        # Create a callback to handle the JavaScript result
        def callback(result):
            try:
                if not result:
                    self.log_status("No result from message monitor")
                    return
                    
                data = json.loads(result)
                status = data.get('status', '')
                
                if status == 'waiting':
                    error = data.get('error', 'Unknown reason')
                    self.log_status(f"Waiting for messages: {error}")
                elif status == 'error':
                    error = data.get('error', 'Unknown error')
                    self.log_status(f"Error monitoring messages: {error}")
                elif status == 'success':
                    messages = data.get('messages', [])
                    if messages:
                        self.log_status(f"Found {len(messages)} messages")
                        self.process_messages(result)
                    else:
                        self.log_status("No messages found to process")
                else:
                    self.log_status("Unknown status from message monitor")
                    
            except Exception as e:
                self.log_status(f"Error in message monitor callback: {str(e)}")
        
        # Run JavaScript with the correct signature
        self.web_view.page().runJavaScript(js_code, 0, callback)
        
    def process_messages(self, result):
        try:
            data = json.loads(result)
            
            # Check the status
            if data.get('status') == 'waiting':
                self.log_status("Waiting for chat to load...")
                return
            elif data.get('status') == 'error':
                self.log_status(f"Error in message monitoring: {data.get('error', 'Unknown error')}")
                return
                
            messages = data.get('messages', [])
            if not messages:
                self.log_status("No messages found")
                return
                
            # Log all detected messages
            self.log_status("Detected messages:")
            for idx, msg in enumerate(messages):
                is_out = msg['isOutgoing']
                text = msg['text'][:50] + "..." if len(msg['text']) > 50 else msg['text']
                self.log_status(f"  {idx+1}. {'[OUT]' if is_out else '[IN] '} {text}")
                
            # Get the last message
            last_message = messages[-1]
            
            # Debug last processed message
            self.log_status(f"Last processed message: '{self.last_processed_message[:30]}...'")
            self.log_status(f"New message: '{last_message['text'][:30]}...'")
            
            # Check if this is a new incoming message we should respond to
            is_new_message = last_message['text'] != self.last_processed_message
            is_incoming = not last_message['isOutgoing']
            
            if is_incoming and is_new_message:
                self.log_status(f"Processing new message: '{last_message['text'][:30]}...'")
                self.last_processed_message = last_message['text']
                
                # Create conversation context from last 5 messages
                conversation = "\n".join([
                    f"{'Assistant' if msg['isOutgoing'] else 'User'}: {msg['text']}"
                    for msg in messages
                ])
                
                # Generate response using bot controller
                self.generate_and_send_response(conversation)
            else:
                if not is_incoming:
                    self.log_status("Last message is outgoing - not responding")
                elif not is_new_message:
                    self.log_status("Message already processed - not responding")
                
        except json.JSONDecodeError as e:
            self.log_status(f"Invalid JSON from message monitor: {str(e)}")
        except Exception as e:
            self.log_status(f"Error processing messages: {str(e)}")
            
    def generate_and_send_response(self, conversation):
        if not self.bot_controller.model:
            self.log_status("Model not initialized")
            return
            
        try:
            # Generate response using the bot controller
            response = ""
            for token in self.bot_controller.model.generate(
                prompt=f"""<|im_start|>system
You are a helpful WhatsApp chat assistant. Provide natural and relevant responses.
Keep your responses concise and friendly. Respond in the same language as the user.

<|im_start|>user
Based on this conversation, provide a response:
{conversation}

<|im_start|>assistant
""",
                max_tokens=150,
                temp=0.7,
                top_k=40,
                top_p=0.9,
                repeat_penalty=1.1,
                streaming=True
            ):
                response += token
                
            if response:
                self.log_status(f"Generated response: {response}")
                # Inject JavaScript to send the message
                js_code = """
                (function() {
                    try {
                        // Find input field (try multiple selectors)
                        var input = document.querySelector('div[contenteditable="true"]');
                        if (!input) {
                            input = document.querySelector('div[role="textbox"]');
                        }
                        if (!input) {
                            console.error('Input field not found');
                            return false;
                        }
                        
                        // Focus and set text
                        input.focus();
                        input.innerHTML = "";
                        document.execCommand('insertText', false, %s);
                        
                        // Dispatch input event
                        var event = new Event('input', { bubbles: true });
                        input.dispatchEvent(event);
                        
                        // Find send button (try multiple selectors)
                        var sendButton = document.querySelector('button[data-testid="send"]');
                        if (!sendButton) {
                            sendButton = document.querySelector('span[data-icon="send"]');
                        }
                        if (!sendButton) {
                            sendButton = document.querySelector('button[data-icon="send"]');
                        }
                        
                        if (sendButton) {
                            sendButton.click();
                            console.log('Message sent successfully');
                            return true;
                        } else {
                            console.error('Send button not found');
                            return false;
                        }
                    } catch (error) {
                        console.error('Error sending message:', error);
                        return false;
                    }
                })();
                """ % json.dumps(response)
                
                # Run JavaScript with the correct signature
                def send_callback(success):
                    if success is False:
                        self.log_status("Failed to send message - please make sure chat is open")
                    elif success is True:
                        self.log_status("Message sent successfully")
                
                self.web_view.page().runJavaScript(js_code, 0, send_callback)
                
        except Exception as e:
            self.log_status(f"Error generating response: {str(e)}")
            
    def start_bot(self):
        if not self.bot_controller.model:
            self.show_error("Please initialize the AI model first", "Model Required")
            return
            
        phone_number = self.phone_input.text().strip()
        if not phone_number:
            self.show_error("Please enter a phone number", "Missing Information")
            return
            
        if self.bot_controller.start_monitoring(phone_number):
            self.is_monitoring = True
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.log_status("Bot started - monitoring messages")
            # Start message monitoring
            self.monitor_messages()
        
    def monitor_messages(self):
        if self.is_monitoring:
            try:
                self.inject_message_monitor()
                # Check messages every 7 seconds to reduce resource usage
                QTimer.singleShot(7000, self.monitor_messages)
            except Exception as e:
                self.log_status(f"Error in message monitoring: {str(e)}")
                # Don't stop the bot immediately, just log and continue
                QTimer.singleShot(10000, self.monitor_messages)
            
    def stop_bot(self):
        self.is_monitoring = False
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.log_status("Bot stopped")
        self.bot_controller.stop_monitoring()
        
    def init_llm(self):
        self.init_model_btn.setEnabled(False)
        success = self.bot_controller.init_llm()
        self.model_label.setText(f"Model initialized: {'Yes' if success else 'Error'}")
        self.init_model_btn.setEnabled(True)
        
    def closeEvent(self, event):
        self.bot_controller.cleanup()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = WhatsAppBot()
    window.show()
    sys.exit(app.exec()) 