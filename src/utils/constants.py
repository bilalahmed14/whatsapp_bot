"""Constants and configuration for the WhatsApp Bot application"""

# LLM Configuration
MODEL_NAME = "mistral-7b-instruct-v0.1.Q4_0.gguf"
MAX_TOKENS = 50
TEMPERATURE = 0.7
TOP_K = 20
TOP_P = 0.85
REPEAT_PENALTY = 1.1

# Message Monitor Configuration
MONITOR_INTERVAL = 15000  # 15 seconds in milliseconds
MESSAGE_TIMEOUT = 15  # 15 seconds timeout for message generation

# Default System Prompt
DEFAULT_SYSTEM_PROMPT = """You are a WhatsApp assistant. Keep responses very concise (1-2 sentences).
Respond naturally and be helpful while maintaining a friendly tone. Match the language style of the user."""

# JavaScript Selectors
INPUT_SELECTORS = [
    'div[contenteditable="true"][data-testid="conversation-compose-box-input"]',
    'div[contenteditable="true"][title="Type a message"]',
    'div[contenteditable="true"][data-tab="10"]',
    'footer div[contenteditable="true"]',
    'div.copyable-text[contenteditable="true"]'
]

SEND_BUTTON_SELECTORS = [
    'button[data-testid="send"]',
    'button[data-icon="send"]',
    'button[aria-label="Send"]',
    'span[data-icon="send"]',
    'span[data-testid="send"]',
    'button.tvf2evcx.oq44ahr5.lb5m6g5c.svlsagor.p2rjqpw5.epia9gcq',
    '[role="button"][aria-label="Send"]'
] 