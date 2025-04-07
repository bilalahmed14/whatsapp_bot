import time
from PySide6.QtCore import QThread, Signal
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
                top_k=20,
                top_p=0.85,
                repeat_penalty=1.1,
                streaming=True
            ):
                if time.time() - start_time > 15:  # 15 second timeout
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