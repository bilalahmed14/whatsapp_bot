"""WhatsApp Bot Controller for managing bot operations"""
import os
import json
from PySide6.QtCore import QObject, Signal, QTimer
from gpt4all import GPT4All

from src.core.message_worker import MessageWorker
from src.core.js_injector import get_message_monitor_script, get_message_sender_script
from src.utils.constants import (
    MODEL_NAME, MONITOR_INTERVAL, DEFAULT_SYSTEM_PROMPT
)

class WhatsAppBotController(QObject):
    """Controller class to handle all bot-related operations"""
    status_signal = Signal(str)
    error_signal = Signal(str, str)  # message, title
    progress_signal = Signal(int)    # For showing generation progress
    
    def __init__(self, web_view=None):
        super().__init__()
        self.model = None
        self.web_view = web_view
        self.is_monitoring = False
        self.last_processed_message = ""
        self.message_worker = None
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._execute_message_monitor)
        self.monitor_timer.setInterval(MONITOR_INTERVAL)
        self.system_prompt = DEFAULT_SYSTEM_PROMPT
            
    def init_llm(self):
        """Initialize the language model"""
        if self.model:  # Reuse existing model if available
            return True
            
        self.status_signal.emit("Initializing local LLM...")
        
        try:
            self.status_signal.emit(f"Using model: {MODEL_NAME}")
            
            if os.path.exists(MODEL_NAME):
                self.status_signal.emit("Model file found locally.")
            else:
                self.status_signal.emit("Model file not found locally. Will download automatically.")
                self.status_signal.emit("This may take several minutes...")
            
            # Initialize model with CPU backend
            self.model = GPT4All(MODEL_NAME, device='cpu')
            # Initialize message worker
            self.message_worker = MessageWorker(self.model)
            self.message_worker.response_ready.connect(self._send_message)
            self.message_worker.status_update.connect(self.status_signal.emit)
            self.message_worker.progress_update.connect(self.progress_signal.emit)
            
            self.status_signal.emit(f"LLM initialized successfully!")
            return True
            
        except Exception as e:
            self.status_signal.emit(f"Error initializing LLM: {str(e)}")
            self.model = None
            return False
            
    def set_web_view(self, web_view):
        """Set the web view for message monitoring"""
        self.web_view = web_view
            
    def start_monitoring(self, phone_number):
        """Start monitoring messages"""
        if not phone_number:
            self.error_signal.emit("Please enter a phone number!", "Missing Information")
            return False
            
        if self.model is None:
            self.error_signal.emit("Please initialize the AI model before starting the bot.", 
                                "AI Model Not Ready")
            return False
        
        if self.web_view is None:
            self.error_signal.emit("Web view not initialized.", "Web View Not Ready")
            return False
            
        self.status_signal.emit("Starting message monitoring...")
        self.status_signal.emit(f"Target number: {phone_number}")
        self.status_signal.emit("Please make sure your conversation is open in WhatsApp Web.")
        
        self.is_monitoring = True
        self._execute_message_monitor()  # Initial check
        self.monitor_timer.start()  # Start periodic checking
        return True
        
    def stop_monitoring(self):
        """Stop monitoring messages"""
        self.is_monitoring = False
        self.monitor_timer.stop()
        if self.message_worker and self.message_worker.isRunning():
            self.message_worker.wait()  # Wait for current processing to finish
        self.status_signal.emit("Bot stopped")
            
    def cleanup(self):
        """Clean up resources"""
        self.stop_monitoring()
        if self.message_worker:
            self.message_worker.quit()
            self.message_worker.wait()
        
    def process_messages(self, result):
        """Process messages from the message monitor"""
        try:
            data = json.loads(result)
            
            if data.get('status') != 'success' or not data.get('messages'):
                return
                
            messages = data['messages']
            last_message = messages[-1]
            
            # Only process if it's a new incoming message
            if (not last_message['isOutgoing'] and 
                last_message['text'] != self.last_processed_message):
                
                self.status_signal.emit(f"New message: '{last_message['text'][:30]}...'")
                self.last_processed_message = last_message['text']
                
                # Only use the last message for faster response
                conversation = f"User: {last_message['text']}"
                
                # Process in worker thread if not already processing
                if self.message_worker and not self.message_worker.is_processing:
                    self.progress_signal.emit(0)  # Reset progress
                    self.message_worker.set_conversation(conversation, self.system_prompt)
                
        except Exception as e:
            self.status_signal.emit(f"Error processing messages: {str(e)}")
            
    def _execute_message_monitor(self):
        """Execute the message monitoring logic"""
        if not self.is_monitoring or not self.web_view:
            return
            
        try:
            self.web_view.page().runJavaScript(
                get_message_monitor_script(),
                0,
                lambda result: self.process_messages(result) if result else None
            )
        except Exception as e:
            self.status_signal.emit(f"Error in message monitoring: {str(e)}")
            
    def _send_message(self, response):
        """Send message in a non-blocking way"""
        if not response or not self.web_view:
            return
            
        # Clean up response by removing "assistant: " prefix if present
        if response.lower().startswith("assistant:"):
            response = response[len("assistant:"):].strip()
            
        self.status_signal.emit(f"Sending response: {response[:30]}...")
        
        def send_callback(result):
            try:
                if not result:
                    self.status_signal.emit("No result from message send attempt")
                    return
                    
                if isinstance(result, dict):
                    if result.get('success'):
                        self.status_signal.emit(f"Message sent successfully: {result.get('message', '')}")
                    else:
                        self.status_signal.emit(f"Failed to send message: {result.get('error', 'unknown error')}")
                else:
                    self.status_signal.emit(f"Unknown result from send attempt: {result}")
                    
            except Exception as e:
                self.status_signal.emit(f"Error in send callback: {str(e)}")
        
        self.web_view.page().runJavaScript(
            get_message_sender_script(response),
            0,
            send_callback
        )
        
    def set_system_prompt(self, prompt):
        """Set custom system prompt"""
        if not prompt or not prompt.strip():
            self.system_prompt = DEFAULT_SYSTEM_PROMPT
        else:
            self.system_prompt = prompt.strip()
        self.status_signal.emit("System prompt updated")
        
    def get_system_prompt(self):
        """Get current system prompt"""
        return self.system_prompt 