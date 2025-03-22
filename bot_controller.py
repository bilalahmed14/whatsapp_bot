import time
import os
from PySide6.QtCore import QThread, Signal, QObject
from gpt4all import GPT4All

class WhatsAppBotController(QObject):
    """Controller class to handle all bot-related operations"""
    status_signal = Signal(str)
    error_signal = Signal(str, str)  # message, title
    
    def __init__(self):
        super().__init__()
        self.model = None
        self.bot_worker = None
        self.is_whatsapp_ready = False
            
    def init_llm(self):
        """Initialize the language model"""
        self.status_signal.emit("Initializing local LLM...")
        
        try:
            model_name = "all-MiniLM-L6-v2-f16.gguf"
            self.status_signal.emit(f"Using model: {model_name}")
            
            if os.path.exists(model_name):
                self.status_signal.emit("Model file found locally.")
            else:
                self.status_signal.emit("Model file not found locally. Will download automatically.")
                self.status_signal.emit("This may take several minutes...")
            
            self.model = GPT4All(model_name)
            self.status_signal.emit("LLM initialized successfully!")
            
            # Test the model
            test_response = self.model.generate("Hello", max_tokens=20)
            self.status_signal.emit("Model test successful.")
            return True
            
        except Exception as e:
            self.status_signal.emit(f"Error initializing LLM: {str(e)}")
            self.status_signal.emit("If download fails, please download a model manually:")
            self.status_signal.emit("1. Go to https://gpt4all.io/models")
            self.status_signal.emit("2. Download a smaller model like 'all-MiniLM-L6-v2-f16.gguf'")
            self.status_signal.emit("3. Place the file in the same directory as this script")
            self.model = None
            return False
            
    def start_monitoring(self, phone_number):
        """Start monitoring messages"""
        if not phone_number:
            self.error_signal.emit("Please enter a phone number!", "Missing Information")
            return False
            
        if self.model is None:
            self.error_signal.emit("Please initialize the AI model before starting the bot.", 
                                 "AI Model Not Ready")
            return False
            
        self.status_signal.emit("Starting message monitoring...")
        self.status_signal.emit(f"Target number: {phone_number}")
        self.status_signal.emit("Please navigate to your conversation with this contact in WhatsApp Web.")
        
        self.bot_worker = MessageMonitor(phone_number, self.model)
        self.bot_worker.status_signal.connect(lambda msg: self.status_signal.emit(msg))
        self.bot_worker.start()
        return True
        
    def stop_monitoring(self):
        """Stop monitoring messages"""
        if self.bot_worker:
            self.bot_worker.stop()
            self.bot_worker = None
            self.status_signal.emit("Bot stopped")
            
    def cleanup(self):
        """Clean up resources"""
        self.stop_monitoring()

class MessageMonitor(QThread):
    """Thread to monitor for new messages and generate responses"""
    status_signal = Signal(str)
    
    def __init__(self, phone_number, model):
        super().__init__()
        self.phone_number = phone_number
        self.model = model
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