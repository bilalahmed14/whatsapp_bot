import time
import os
import json
from PySide6.QtCore import QThread, Signal, QObject, QTimer
from gpt4all import GPT4All

class MessageWorker(QThread):
    """Worker thread for handling message processing and LLM operations"""
    response_ready = Signal(str)  # Emits when response is generated
    status_update = Signal(str)   # Emits status updates
    progress_update = Signal(int) # Emits progress updates (0-100)
    
    def __init__(self, model):
        super().__init__()
        self.model = model
        self.conversation = None
        self.is_processing = False
        self.token_count = 0
        self.max_tokens = 50  # Reduced from 100 for faster responses
        self.system_prompt = None
        
    def set_conversation(self, conversation, system_prompt):
        """Set conversation to process"""
        if self.is_processing:
            return
        self.conversation = conversation
        self.system_prompt = system_prompt
        self.token_count = 0
        if not self.isRunning():
            self.start()
            
    def run(self):
        """Process conversation and generate response"""
        if not self.conversation or not self.model or self.is_processing:
            return
            
        try:
            self.is_processing = True
            self.status_update.emit("Generating response...")
            self.progress_update.emit(0)
            
            full_response = ""
            start_time = time.time()
            
            # Use provided system prompt
            prompt = f"""<|im_start|>system
{self.system_prompt}
<|im_start|>user
{self.conversation.split('\n')[-1]}
<|im_start|>assistant
"""
            
            for token in self.model.generate(
                prompt=prompt,
                max_tokens=self.max_tokens,
                temp=0.7,
                top_k=20,        # Reduced from 40
                top_p=0.85,      # Reduced from 0.9
                repeat_penalty=1.1,
                streaming=True
            ):
                if time.time() - start_time > 15:  # Reduced timeout from 30s to 15s
                    self.status_update.emit("Response generation timed out")
                    break
                    
                full_response += token
                self.token_count += 1
                # Update progress based on token count
                progress = min(100, int((self.token_count / self.max_tokens) * 100))
                self.progress_update.emit(progress)
                
            if full_response:
                # Extract only the assistant's response
                response = full_response.strip()
                if "<|im_start|>" in response:
                    response = response.split("<|im_start|>assistant")[-1].strip()
                if "<|im_end|>" in response:
                    response = response.split("<|im_end|>")[0].strip()
                    
                self.response_ready.emit(response)
                self.progress_update.emit(100)
                
        except Exception as e:
            self.status_update.emit(f"Error generating response: {str(e)}")
        finally:
            self.is_processing = False
            self.conversation = None
            self.token_count = 0

class WhatsAppBotController(QObject):
    """Controller class to handle all bot-related operations"""
    status_signal = Signal(str)
    error_signal = Signal(str, str)  # message, title
    progress_signal = Signal(int)    # For showing generation progress
    
    DEFAULT_SYSTEM_PROMPT = """You are a WhatsApp assistant. Keep responses very concise (1-2 sentences).
Respond naturally and be helpful while maintaining a friendly tone. Match the language style of the user."""
    
    def __init__(self, web_view=None):
        super().__init__()
        self.model = None
        self.web_view = web_view
        self.is_monitoring = False
        self.last_processed_message = ""
        self.message_worker = None
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self._execute_message_monitor)
        self.monitor_timer.setInterval(15000)  # 15 seconds interval
        self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
            
    def init_llm(self):
        """Initialize the language model"""
        if self.model:  # Reuse existing model if available
            return True
            
        self.status_signal.emit("Initializing local LLM...")
        
        try:
            model_name = "mistral-7b-instruct-v0.1.Q4_0.gguf"
            self.status_signal.emit(f"Using model: {model_name}")
            
            if os.path.exists(model_name):
                self.status_signal.emit("Model file found locally.")
            else:
                self.status_signal.emit("Model file not found locally. Will download automatically.")
                self.status_signal.emit("This may take several minutes...")
            
            # Initialize model with CPU backend
            self.model = GPT4All(model_name, device='cpu')
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
            self.inject_message_monitor()
        except Exception as e:
            self.status_signal.emit(f"Error in message monitoring: {str(e)}")

    def inject_message_monitor(self):
        """Inject JavaScript to monitor messages"""
        if not self.web_view:
            self.status_signal.emit("Web view not available")
            return
            
        # JavaScript to extract last 5 text messages from current chat
        js_code = """
        (function() {
            try {
                // Check if WhatsApp is loaded
                if (!document.querySelector('#app')) {
                    return JSON.stringify({
                        status: 'waiting',
                        error: 'WhatsApp not fully loaded',
                        messages: []
                    });
                }
                
                // Look for messages using different approaches
                const messages = [];
                
                // Try the most reliable approach first - selecting message text elements
                const msgTextElements = document.querySelectorAll('div.focusable-list-item div.copyable-text span.selectable-text');
                
                if (msgTextElements.length > 0) {
                    let count = 0;
                    for (let i = msgTextElements.length - 1; i >= 0 && count < 5; i--) {
                        const textEl = msgTextElements[i];
                        const text = textEl.innerText.trim();
                        
                        // Skip timestamps and very short messages
                        if (!text || text.length < 2 || /^[0-9]{1,2}:[0-9]{2}[ ](AM|PM)$/.test(text)) {
                            continue;
                        }
                        
                        // Determine if outgoing message by checking parent containers
                        let container = textEl;
                        let isOutgoing = false;
                        
                        // Walk up parent chain to find message container
                        for (let j = 0; j < 10 && container; j++) {
                            if (container.parentElement) {
                                container = container.parentElement;
                                
                                // Check if it's an outgoing message container
                                if (container.className && 
                                    typeof container.className === 'string' && 
                                    container.className.indexOf('message-out') >= 0) {
                                    isOutgoing = true;
                                    break;
                                }
                            } else {
                                break;
                            }
                        }
                        
                        messages.unshift({
                            text: text,
                            isOutgoing: isOutgoing,
                            timestamp: new Date().getTime()
                        });
                        count++;
                    }
                }
                
                // If we couldn't find messages, try with message bubbles
                if (messages.length === 0) {
                    const bubbles = document.querySelectorAll('div.message-in, div.message-out');
                    
                    if (bubbles.length > 0) {
                        let count = 0;
                        for (let i = bubbles.length - 1; i >= 0 && count < 5; i--) {
                            const bubble = bubbles[i];
                            const isOutgoing = bubble.classList.contains('message-out');
                            
                            // Skip media messages
                            if (bubble.querySelector('img') || bubble.querySelector('audio')) {
                                continue;
                            }
                            
                            // Find the text content
                            const textEl = bubble.querySelector('span.selectable-text');
                            if (textEl) {
                                const text = textEl.innerText.trim();
                                
                                // Skip timestamps and very short messages
                                if (!text || text.length < 2 || /^[0-9]{1,2}:[0-9]{2}[ ](AM|PM)$/.test(text)) {
                                    continue;
                                }
                                
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
                
                // Last resort approach
                if (messages.length === 0) {
                    const textSpans = document.querySelectorAll('span.selectable-text');
                    
                    if (textSpans.length > 0) {
                        let count = 0;
                        for (let i = textSpans.length - 1; i >= 0 && count < 5; i--) {
                            const span = textSpans[i];
                            const text = span.innerText.trim();
                            
                            // Skip timestamps and very short messages
                            if (!text || text.length < 2 || /^[0-9]{1,2}:[0-9]{2}[ ](AM|PM)$/.test(text)) {
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
                        }
                    }
                }
                
                return JSON.stringify({
                    status: messages.length > 0 ? 'success' : 'waiting',
                    error: messages.length === 0 ? 'No messages found' : '',
                    messages: messages
                });
            } catch (error) {
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
                    self.status_signal.emit("No result from message monitor")
                    return
                    
                data = json.loads(result)
                status = data.get('status', '')
                
                if status == 'waiting':
                    error = data.get('error', 'Unknown reason')
                    self.status_signal.emit(f"Waiting for messages: {error}")
                elif status == 'error':
                    error = data.get('error', 'Unknown error')
                    self.status_signal.emit(f"Error monitoring messages: {error}")
                elif status == 'success':
                    messages = data.get('messages', [])
                    if messages:
                        self.status_signal.emit(f"Found {len(messages)} messages")
                        self.process_messages(result)
                    else:
                        self.status_signal.emit("No messages found to process")
                else:
                    self.status_signal.emit("Unknown status from message monitor")
                    
            except Exception as e:
                self.status_signal.emit(f"Error in message monitor callback: {str(e)}")
        
        # Run JavaScript with the correct signature
        self.web_view.page().runJavaScript(js_code, 0, callback)
        
    def _send_message(self, response):
        """Send message in a non-blocking way"""
        if not response or not self.web_view:
            return
            
        # Clean up response by removing "assistant: " prefix if present
        if response.lower().startswith("assistant:"):
            response = response[len("assistant:"):].strip()
            
        self.status_signal.emit(f"Sending response: {response[:30]}...")
        # Inject JavaScript to send the message with improved selectors and input handling
        js_code = """
        (function() {
            function sleep(ms) {
                return new Promise(resolve => setTimeout(resolve, ms));
            }
            
            async function sendMessage() {
                try {
                    console.log('Starting message send process...');
                    
                    // Wait for WhatsApp to be fully loaded
                    if (!document.querySelector('#app')) {
                        console.error('WhatsApp not loaded');
                        return {success: false, error: 'WhatsApp not loaded'};
                    }
                    
                    // Find input field (try multiple selectors)
                    const inputSelectors = [
                        'div[contenteditable="true"][data-testid="conversation-compose-box-input"]',
                        'div[contenteditable="true"][title="Type a message"]',
                        'div[contenteditable="true"][data-tab="10"]',
                        'footer div[contenteditable="true"]',
                        'div.copyable-text[contenteditable="true"]'
                    ];
                    
                    let input = null;
                    for (const selector of inputSelectors) {
                        const elements = document.querySelectorAll(selector);
                        for (const element of elements) {
                            // Check if the element is within the message compose area
                            let isInComposeArea = false;
                            let parent = element.parentElement;
                            while (parent) {
                                if (parent.getAttribute('data-testid') === 'conversation-compose-box' ||
                                    parent.getAttribute('data-testid') === 'conversation-footer' ||
                                    (parent.className && parent.className.includes('conversation-compose'))) {
                                    isInComposeArea = true;
                                    break;
                                }
                                parent = parent.parentElement;
                            }
                            
                            if (isInComposeArea) {
                                input = element;
                                console.log('Found message input with selector:', selector);
                                break;
                            }
                        }
                        if (input) break;
                    }
                    
                    if (!input) {
                        // Try finding by footer area as last resort
                        const footer = document.querySelector('footer');
                        if (footer) {
                            const footerInput = footer.querySelector('div[contenteditable="true"]');
                            if (footerInput) {
                                input = footerInput;
                                console.log('Found message input in footer');
                            }
                        }
                    }
                    
                    if (!input) {
                        console.error('Message input field not found');
                        return {success: false, error: 'Message input field not found'};
                    }
                    
                    // Focus the input field
                    input.focus();
                    await sleep(100);
                    
                    // Clear existing content
                    input.textContent = '';
                    input.innerHTML = '';
                    await sleep(100);
                    
                    // Try multiple methods to insert text
                    const text = %s;
                    let textInserted = false;
                    
                    // Method 1: execCommand
                    try {
                        document.execCommand('insertText', false, text);
                        textInserted = input.textContent === text;
                        console.log('Method 1 (execCommand) success:', textInserted);
                    } catch (e) {
                        console.log('Method 1 failed:', e);
                    }
                    
                    // Method 2: clipboard
                    if (!textInserted) {
                        try {
                            const originalClipboard = await navigator.clipboard.readText().catch(() => '');
                            await navigator.clipboard.writeText(text);
                            await sleep(100);
                            document.execCommand('paste');
                            await sleep(100);
                            await navigator.clipboard.writeText(originalClipboard);
                            textInserted = input.textContent === text;
                            console.log('Method 2 (clipboard) success:', textInserted);
                        } catch (e) {
                            console.log('Method 2 failed:', e);
                        }
                    }
                    
                    // Method 3: direct assignment
                    if (!textInserted) {
                        try {
                            input.textContent = text;
                            textInserted = input.textContent === text;
                            console.log('Method 3 (direct) success:', textInserted);
                        } catch (e) {
                            console.log('Method 3 failed:', e);
                        }
                    }
                    
                    if (!textInserted) {
                        console.error('Failed to insert text');
                        return {success: false, error: 'Could not insert text'};
                    }
                    
                    // Trigger input events
                    input.dispatchEvent(new Event('input', {bubbles: true}));
                    input.dispatchEvent(new Event('change', {bubbles: true}));
                    await sleep(100);
                    
                    // Find send button (try multiple selectors)
                    const buttonSelectors = [
                        'button[data-testid="send"]',
                        'button[data-icon="send"]',
                        'button[aria-label="Send"]',
                        'span[data-icon="send"]',
                        'span[data-testid="send"]',
                        'button.tvf2evcx.oq44ahr5.lb5m6g5c.svlsagor.p2rjqpw5.epia9gcq',
                        '[role="button"][aria-label="Send"]'
                    ];
                    
                    let sendButton = null;
                    for (const selector of buttonSelectors) {
                        sendButton = document.querySelector(selector);
                        if (sendButton) {
                            console.log('Found button with selector:', selector);
                            break;
                        }
                    }
                    
                    // If still not found, try to find any clickable element near the input
                    if (!sendButton) {
                        console.log('Looking for send button near input...');
                        let parent = input.parentElement;
                        let maxTries = 5;
                        
                        while (parent && maxTries > 0) {
                            const buttons = parent.querySelectorAll('button, span[role="button"], div[role="button"]');
                            for (const btn of buttons) {
                                if (btn.innerHTML.includes('send') || 
                                    btn.getAttribute('aria-label')?.toLowerCase().includes('send') ||
                                    btn.className.includes('send')) {
                                    sendButton = btn;
                                    console.log('Found send button by proximity');
                                    break;
                                }
                            }
                            if (sendButton) break;
                            parent = parent.parentElement;
                            maxTries--;
                        }
                    }
                    
                    if (sendButton) {
                        console.log('Clicking send button...');
                        sendButton.click();
                        await sleep(100);
                        return {success: true, message: 'Message sent successfully'};
                    }
                    
                    // Last resort: try Enter key
                    console.log('Trying Enter key...');
                    const enterEvent = new KeyboardEvent('keydown', {
                        key: 'Enter',
                        code: 'Enter',
                        keyCode: 13,
                        which: 13,
                        bubbles: true,
                        cancelable: true
                    });
                    input.dispatchEvent(enterEvent);
                    await sleep(100);
                    
                    // Check if text was sent (input should be empty)
                    if (input.textContent.trim() === '') {
                        return {success: true, message: 'Message sent via Enter key'};
                    }
                    
                    return {success: false, error: 'Could not send message'};
                    
                } catch (error) {
                    console.error('Error in sendMessage:', error);
                    return {success: false, error: error.toString()};
                }
            }
            
            return sendMessage();
        })();
        """ % json.dumps(response)
        
        # Run JavaScript with the correct signature
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
                elif result is False:
                    self.status_signal.emit("Failed to send message - please make sure chat is open")
                elif result is True:
                    self.status_signal.emit("Message sent successfully")
                else:
                    self.status_signal.emit(f"Unknown result from send attempt: {result}")
                    
            except Exception as e:
                self.status_signal.emit(f"Error in send callback: {str(e)}")
        
        self.web_view.page().runJavaScript(js_code, 0, send_callback)

    def set_system_prompt(self, prompt):
        """Set custom system prompt"""
        if not prompt or not prompt.strip():
            self.system_prompt = self.DEFAULT_SYSTEM_PROMPT
        else:
            self.system_prompt = prompt.strip()
        self.status_signal.emit("System prompt updated")
        
    def get_system_prompt(self):
        """Get current system prompt"""
        return self.system_prompt 