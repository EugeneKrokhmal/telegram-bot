"""Text messages and responses for commands."""


# Start command message
START_MESSAGE = (
    "Yo! I'm the AI buddy of this chat 🍻\n\n"
    "- I sometimes jump into the conversation\n"
    "- You can ask me stuff with /ask\n"
    "- Search chat with /search\n\n"
    "I'm a bot, not a real person – don't trust me with your bank account 😉"
)

# Help command message
HELP_MESSAGE = (
    "Commands:\n"
    "/ask <question> – ask me anything, I'll try to answer.\n"
    "/search <text> – search recent messages by text.\n"
    "/summary or /daily – get a summary of the last 24 hours.\n"
    "/help – this message.\n\n"
    "You can also just talk in the chat – I may reply randomly 🤖"
)

# Command usage messages
ASK_USAGE = "Use: /ask <question>"
SEARCH_USAGE = "Use: /search <text>"
SEARCH_NO_RESULTS = "Nothing found in recent messages 🤷‍♂️"
SEARCH_RESULTS_HEADER = "Found these in recent messages:"

# AI service prompts
DECISION_SYSTEM_PROMPT = "You are a conversational AI assistant. Decide if joining this conversation would be natural and valuable. Respond with only YES or NO."
ANALYZER_SYSTEM_PROMPT = "You are a conversation analyzer. Respond with valid JSON only."
SEARCH_QUERY_SYSTEM_PROMPT = "You are a search query generator. Respond with a search query or 'NO'."
ASK_SYSTEM_PROMPT = (
    "You are an AI member of a friendly Telegram group chat. "
    "Answer concisely, in a casual tone. If you don't know "
    "something for sure, say you're not certain rather than inventing details."
)

# Error messages
RATE_LIMIT_MESSAGE = "Sorry, I've hit my API quota limit. Please check your OpenAI billing or try again later. 💳"
AI_ERROR_MESSAGE = "I tried to think of something smart to say, but my brain glitched 🤖"

# Summary command
SUMMARY_USAGE = "Use: /summary or /daily"
SUMMARY_NO_MESSAGES = "No messages found from the last 24 hours 🤷‍♂️"
SUMMARY_SYSTEM_PROMPT = (
    "You are summarizing a Telegram group chat conversation from the last 24 hours. "
    "Create a concise, engaging summary that highlights: "
    "- Who said what (key participants and their main points) "
    "- Main topics discussed "
    "- Important events or decisions "
    "- General vibe/atmosphere of the conversation "
    "Keep it casual and readable, like a friend summarizing what happened in the group."
)

