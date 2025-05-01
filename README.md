# GPTillo – Large Language Mode for Telegram

GPTillo is a conversational AI Telegram bot powered by Google Gemini API. It's designed to interact in group chats as a funny, casual, and energetic "friend" with various capabilities (those can be configured)
Difference between normal AI chatbots with GPTillo is that GPTillo can interact with many people in telegram groups as well.

## Features

- 🧠 **Conversational AI**: Uses Gemini (Gemini 2.5 Flash) for realistic group-chat behavior.
- 📷 **Image Understanding**: Upload a photo — GPTillo will describe what's in it.
- 🎨 **Image Generation**: Use `GENERATE_IMAGE` keyword to create vivid AI-generated images.
- 🔒 **Context Aware**: Responds only when needed (skips unrelated messages).


## 🚀 Getting Started

### Prerequisites

- Python 3.10+
- Telegram Bot Token (get from botfather)
- Google Gemini API Key

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Create ```tokens.py``` file and write api tokens there. For example:

```
BOT_TOKEN = "your-telegram-bot-token"
GEMINI_API = "your-gemini-api-key"

```

### After everything is configured, just run the pyton code; bot is ready to chat.