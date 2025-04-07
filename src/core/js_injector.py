"""JavaScript injection code for WhatsApp Web interaction"""
import json
from src.utils.constants import INPUT_SELECTORS, SEND_BUTTON_SELECTORS

def get_message_monitor_script():
    """Returns the JavaScript code for monitoring messages"""
    return """
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

def get_message_sender_script(message):
    """Returns the JavaScript code for sending messages"""
    return f"""
    (function() {{
        function sleep(ms) {{
            return new Promise(resolve => setTimeout(resolve, ms));
        }}
        
        async function sendMessage() {{
            try {{
                console.log('Starting message send process...');
                
                // Wait for WhatsApp to be fully loaded
                if (!document.querySelector('#app')) {{
                    console.error('WhatsApp not loaded');
                    return {{success: false, error: 'WhatsApp not loaded'}};
                }}
                
                // Find input field (try multiple selectors)
                const inputSelectors = {json.dumps(INPUT_SELECTORS)};
                let input = null;
                
                for (const selector of inputSelectors) {{
                    const elements = document.querySelectorAll(selector);
                    for (const element of elements) {{
                        // Check if the element is within the message compose area
                        let isInComposeArea = false;
                        let parent = element.parentElement;
                        while (parent) {{
                            if (parent.getAttribute('data-testid') === 'conversation-compose-box' ||
                                parent.getAttribute('data-testid') === 'conversation-footer' ||
                                (parent.className && parent.className.includes('conversation-compose'))) {{
                                isInComposeArea = true;
                                break;
                            }}
                            parent = parent.parentElement;
                        }}
                        
                        if (isInComposeArea) {{
                            input = element;
                            console.log('Found message input with selector:', selector);
                            break;
                        }}
                    }}
                    if (input) break;
                }}
                
                if (!input) {{
                    // Try finding by footer area as last resort
                    const footer = document.querySelector('footer');
                    if (footer) {{
                        const footerInput = footer.querySelector('div[contenteditable="true"]');
                        if (footerInput) {{
                            input = footerInput;
                            console.log('Found message input in footer');
                        }}
                    }}
                }}
                
                if (!input) {{
                    console.error('Message input field not found');
                    return {{success: false, error: 'Message input field not found'}};
                }}
                
                // Focus the input field
                input.focus();
                await sleep(100);
                
                // Clear existing content
                input.textContent = '';
                input.innerHTML = '';
                await sleep(100);
                
                // Try multiple methods to insert text
                const text = {json.dumps(message)};
                let textInserted = false;
                
                // Method 1: execCommand
                try {{
                    document.execCommand('insertText', false, text);
                    textInserted = input.textContent === text;
                    console.log('Method 1 (execCommand) success:', textInserted);
                }} catch (e) {{
                    console.log('Method 1 failed:', e);
                }}
                
                // Method 2: clipboard
                if (!textInserted) {{
                    try {{
                        const originalClipboard = await navigator.clipboard.readText().catch(() => '');
                        await navigator.clipboard.writeText(text);
                        await sleep(100);
                        document.execCommand('paste');
                        await sleep(100);
                        await navigator.clipboard.writeText(originalClipboard);
                        textInserted = input.textContent === text;
                        console.log('Method 2 (clipboard) success:', textInserted);
                    }} catch (e) {{
                        console.log('Method 2 failed:', e);
                    }}
                }}
                
                // Method 3: direct assignment
                if (!textInserted) {{
                    try {{
                        input.textContent = text;
                        textInserted = input.textContent === text;
                        console.log('Method 3 (direct) success:', textInserted);
                    }} catch (e) {{
                        console.log('Method 3 failed:', e);
                    }}
                }}
                
                if (!textInserted) {{
                    console.error('Failed to insert text');
                    return {{success: false, error: 'Could not insert text'}};
                }}
                
                // Trigger input events
                input.dispatchEvent(new Event('input', {{bubbles: true}}));
                input.dispatchEvent(new Event('change', {{bubbles: true}}));
                await sleep(100);
                
                // Find send button (try multiple selectors)
                const buttonSelectors = {json.dumps(SEND_BUTTON_SELECTORS)};
                let sendButton = null;
                
                for (const selector of buttonSelectors) {{
                    sendButton = document.querySelector(selector);
                    if (sendButton) {{
                        console.log('Found button with selector:', selector);
                        break;
                    }}
                }}
                
                // If still not found, try to find any clickable element near the input
                if (!sendButton) {{
                    console.log('Looking for send button near input...');
                    let parent = input.parentElement;
                    let maxTries = 5;
                    
                    while (parent && maxTries > 0) {{
                        const buttons = parent.querySelectorAll('button, span[role="button"], div[role="button"]');
                        for (const btn of buttons) {{
                            if (btn.innerHTML.includes('send') || 
                                btn.getAttribute('aria-label')?.toLowerCase().includes('send') ||
                                btn.className.includes('send')) {{
                                sendButton = btn;
                                console.log('Found send button by proximity');
                                break;
                            }}
                        }}
                        if (sendButton) break;
                        parent = parent.parentElement;
                        maxTries--;
                    }}
                }}
                
                if (sendButton) {{
                    console.log('Clicking send button...');
                    sendButton.click();
                    await sleep(100);
                    return {{success: true, message: 'Message sent successfully'}};
                }}
                
                // Last resort: try Enter key
                console.log('Trying Enter key...');
                const enterEvent = new KeyboardEvent('keydown', {{
                    key: 'Enter',
                    code: 'Enter',
                    keyCode: 13,
                    which: 13,
                    bubbles: true,
                    cancelable: true
                }});
                input.dispatchEvent(enterEvent);
                await sleep(100);
                
                // Check if text was sent (input should be empty)
                if (input.textContent.trim() === '') {{
                    return {{success: true, message: 'Message sent via Enter key'}};
                }}
                
                return {{success: false, error: 'Could not send message'}};
                
            }} catch (error) {{
                console.error('Error in sendMessage:', error);
                return {{success: false, error: error.toString()}};
            }}
        }}
        
        return sendMessage();
    }})();
    """ 