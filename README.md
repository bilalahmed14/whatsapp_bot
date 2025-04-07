# WhatsApp Chat Bot

A Python-based WhatsApp chat bot that uses GPT4All for automated responses.

## Features

- Automated responses using local GPT4All model
- User-friendly GUI built with PySide6
- Persistent browser session
- Customizable system prompts
- Real-time message monitoring
- Progress tracking for response generation

## Requirements

- Python 3.8+
- PySide6
- GPT4All
- Selenium
- WebDriver Manager

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/whatsapp-bot.git
cd whatsapp-bot
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the application:
```bash
python main.py
```

2. Click "Initialize AI Model" to download and set up the GPT4All model (first run only)
3. Click "Open WhatsApp Web" and scan the QR code with your phone
4. Enter the target phone number (with country code)
5. Customize the system prompt if desired
6. Click "Start Bot" to begin monitoring and responding to messages

## Project Structure

```
whstapp/
├── src/
│   ├── gui/
│   │   ├── components/
│   │   │   └── web_view.py    # Custom WebView component
│   │   └── main_window.py     # Main window UI
│   ├── core/
│   │   ├── bot_controller.py  # Bot logic
│   │   ├── message_worker.py  # Message processing
│   │   └── js_injector.py     # JavaScript injection
│   └── utils/
│       └── constants.py       # Configuration
├── requirements.txt
└── main.py                    # Entry point
```

## Configuration

You can modify the following settings in `src/utils/constants.py`:

- Model parameters (temperature, tokens, etc.)
- Monitoring interval
- Default system prompt
- Message timeout

## License

MIT License 