# AI Telegram Helper Bot

A friendly AI-powered Telegram bot that helps with reminders, answers questions, and adds some fun to group chats.

## Features

- 🤖 **Smart Replies**: Replies to questions or randomly joins conversations
- 🍻 **Social Suggestions**: Suggests going out when it detects relevant keywords
- ⏰ **Reminders**: Set reminders with `/remind 10m grab preworkout`
- 🔍 **Message Search**: Search recent chat history with `/search keyword`
- 💬 **AI Q&A**: Ask questions with `/ask why is sky blue`
- 😄 **Jokes & Banter**: Context-aware playful responses

## Setup

1. **Create a virtual environment** (if not already done):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   
   Create a `.env` file in the project root:
   ```
   TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
   OPENAI_API_KEY=sk-your_openai_api_key_here
   ```
   
   - Get your Telegram bot token from [@BotFather](https://t.me/botfather)
   - Get your OpenAI API key from [OpenAI Platform](https://platform.openai.com/api-keys)

## Running the Bot

1. **Activate the virtual environment**:
   ```bash
   source venv/bin/activate
   ```

2. **Run the bot**:
   ```bash
   python bot.py
   ```

## Commands

- `/start` - Welcome message and bot introduction
- `/help` - Show available commands
- `/ask <question>` - Ask the AI a question
- `/remind <time> <text>` - Set a reminder (e.g., `/remind 10m go to gym`)
- `/search <text>` - Search recent messages in the chat

## Notes

- The bot uses in-memory storage (up to 300 recent messages per process)
- Reminders are stored in memory and will be lost if the bot restarts
- For production use, consider adding database persistence

