# WhatsApp Chat Bot

A Python-based WhatsApp chat bot that integrates a browser window for WhatsApp Web alongside a control panel UI. It allows you to log in to WhatsApp and respond to messages using a local language model.

## Features

- Integrated browser window for WhatsApp Web
- Control panel with bot controls and status monitoring
- Local language model (GPT4All) for generating responses
- Split interface design for easy monitoring

## Prerequisites

- Python 3.8 or higher
- Internet connection

## Installation

1. Clone this repository
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. The bot will automatically download the required AI model on first run
   - This may take several minutes depending on your internet connection
   - If the download fails, you can manually download it from [GPT4All's website](https://gpt4all.io/models)
   - Look for "all-MiniLM-L6-v2-f16.gguf" (small and efficient)
   - Place the downloaded model file in the same directory as the script

## Usage

1. Run the bot:
   ```bash
   python whatsapp_bot.py
   ```
2. The interface will show:
   - Left panel: Controls and status log
   - Right panel: Embedded WhatsApp Web browser

3. In the left panel:
   - Enter the target phone number (with country code, e.g., "+1234567890")
   - Click "Initialize AI Model" to prepare the language model
   - Once initialized, click "Start Bot" to begin monitoring messages

4. In the browser panel:
   - Scan the WhatsApp QR code with your phone to log in
   - Navigate to your conversation with the target number
   - The bot will monitor for new messages and generate responses

## Notes

- You can resize the split between control panel and browser as needed
- Use the "Refresh Browser" button if WhatsApp Web fails to load properly
- The local language model is lightweight but may take a moment to generate responses
- All WhatsApp interactions happen in the embedded browser that you can directly control

## Troubleshooting

### Common Issues

- **Browser doesn't load**: Click the "Refresh Browser" button
- **QR code doesn't scan**: Make sure your phone camera is working properly
- **Model initialization fails**: Try downloading the model manually as described in the installation section
- **Bot doesn't respond**: Check the status log in the left panel for error messages

## Security Considerations

- Never share your WhatsApp QR code
- Your WhatsApp Web session is contained within the application
- No messages or personal data are stored permanently 