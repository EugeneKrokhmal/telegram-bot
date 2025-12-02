"""Command and message handlers for the bot."""
import logging
import random
from datetime import datetime
from telegram import Update, MessageEntity
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from config import logger, ENABLE_STICKERS, STICKER_CHANCE, STICKER_SET_NAME
from services import AIService, StorageService
from models import Message
from messages import (
    START_MESSAGE,
    HELP_MESSAGE,
    ASK_USAGE,
    SEARCH_USAGE,
    SEARCH_NO_RESULTS,
    SEARCH_RESULTS_HEADER,
    ASK_SYSTEM_PROMPT,
    SUMMARY_USAGE,
    SUMMARY_NO_MESSAGES,
    SUMMARY_SYSTEM_PROMPT,
)
from prompts import (
    get_base_system_prompt,
    get_mention_prompt,
    get_conversation_type_prompts,
    get_user_prompt_base,
    get_user_prompt_with_context,
    get_user_prompt_with_search,
    get_user_prompt_final,
)

logger = logging.getLogger(__name__)


class BotHandlers:
    """Handlers for bot commands and messages."""

    def __init__(self, ai_service: AIService, storage_service: StorageService):
        """Initialize handlers with services."""
        self.ai_service = ai_service
        self.storage = storage_service
        self.sticker_set_name = STICKER_SET_NAME

    def is_bot_mentioned(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ) -> bool:
        """Check if the bot is mentioned/tagged in the message."""
        if not update.message or not update.message.entities:
            return False

        bot = context.bot
        bot_username = bot.username.lower() if bot.username else None

        # Check entities for mentions
        for entity in update.message.entities:
            if entity.type == MessageEntity.MENTION:
                mentioned = update.message.text[
                    entity.offset : entity.offset + entity.length
                ].lower()
                if bot_username and f"@{bot_username}" in mentioned:
                    return True
            elif entity.type == MessageEntity.TEXT_MENTION:
                if entity.user and entity.user.id == bot.id:
                    return True

        # Fallback: check if bot username appears in text
        if bot_username and f"@{bot_username}" in update.message.text.lower():
            return True

        return False

    async def start_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /start command."""
        if not update.message:
            return
        await update.message.reply_text(START_MESSAGE)

    async def help_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /help command."""
        if not update.message:
            return
        await update.message.reply_text(HELP_MESSAGE)

    async def ask_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /ask command."""
        if not update.message:
            return
        if not context.args:
            await update.message.reply_text(ASK_USAGE)
            return

        question = " ".join(context.args).strip()
        reply = await self.ai_service.call_llm(
            ASK_SYSTEM_PROMPT, question, max_tokens=400
        )
        await update.message.reply_text(reply)

    async def search_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /search command."""
        if not update.message:
            return
        if not context.args:
            await update.message.reply_text(SEARCH_USAGE)
            return

        query = " ".join(context.args).strip()
        chat_id = update.effective_chat.id
        matches = self.storage.search_messages(query, chat_id)

        if not matches:
            await update.message.reply_text(SEARCH_NO_RESULTS)
            return

        lines = [SEARCH_RESULTS_HEADER]
        for m in matches:
            lines.append(f"- {m.user}: {m.text[:120]}")

        await update.message.reply_text("\n".join(lines))

    async def summary_command(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle /summary or /daily command - summarize last 24 hours."""
        if not update.message:
            return

        chat_id = update.effective_chat.id
        logger.info(f"Summary command called for chat {chat_id}")
        
        # Get messages from last day (or most recent if none in last 24h)
        messages = self.storage.get_messages_from_last_day(chat_id)
        logger.info(f"Messages to summarize: {len(messages)}")

        if not messages:
            # Check total messages across all chats to see if bot is working
            total_all_chats = len(self.storage.recent_messages)
            if total_all_chats == 0:
                await update.message.reply_text(
                    "No messages found yet. The bot needs to receive messages first!\n\n"
                    "💡 **Tip:** Send some messages in this chat, and I'll store them. "
                    "Then use /summary to get a summary.\n\n"
                    "Note: Messages are stored in memory, so if the bot restarts, "
                    "previous messages won't be available."
                )
            else:
                await update.message.reply_text(
                    f"No messages found in this chat yet.\n\n"
                    f"The bot has {total_all_chats} messages stored from other chats, "
                    f"but none from this chat ({chat_id}).\n\n"
                    "Send some messages here and I'll start tracking them! 💬"
                )
            return

        # Build conversation history for summary
        conversation_text = []
        for m in messages:
            time_str = ""
            if m.timestamp:
                time_ago = datetime.now() - m.timestamp
                hours_ago = int(time_ago.total_seconds() / 3600)
                if hours_ago < 1:
                    time_str = " (just now)"
                elif hours_ago < 24:
                    time_str = f" ({hours_ago}h ago)"
            conversation_text.append(f"{m.user}: {m.text}{time_str}")

        full_conversation = "\n".join(conversation_text)
        
        # Detect language from the most recent messages
        recent_texts = [m.text for m in messages[-5:]]  # Last 5 messages
        combined_recent_text = " ".join(recent_texts)
        detected_lang = self.ai_service.detect_language(combined_recent_text)
        language_name = self.ai_service.get_language_name(detected_lang)
        
        logger.info(f"Generating summary for {len(messages)} messages in {language_name} ({detected_lang})")
        logger.info(f"First 500 chars: {full_conversation[:500]}...")
        
        # Generate summary using AI
        time_range = "last 24 hours" if any(m.timestamp and (datetime.now() - m.timestamp).total_seconds() < 86400 for m in messages) else "recent messages"
        
        # Build system prompt with language instruction
        system_prompt_with_lang = (
            f"{SUMMARY_SYSTEM_PROMPT}\n\n"
            f"CRITICAL: The conversation is in {language_name} ({detected_lang}). "
            f"You MUST respond in {language_name} ({detected_lang}). "
            f"Match the language of the conversation exactly."
        )
        
        summary_prompt = (
            f"Here's the conversation from the {time_range}:\n\n{full_conversation}\n\n"
            "Create a summary of what happened, who said what, and what the main topics were."
        )

        summary = await self.ai_service.call_llm(
            system_prompt_with_lang,
            summary_prompt,
            max_tokens=500
        )

        await update.message.reply_text(
            f"📅 Summary ({time_range} - {len(messages)} messages):\n\n{summary}"
        )

    async def generate_summary_for_chat(
        self, context: ContextTypes.DEFAULT_TYPE, chat_id: int
    ) -> None:
        """
        Generate and send summary for a specific chat (used by scheduled jobs).
        
        Args:
            context: Bot context
            chat_id: Chat ID to summarize
        """
        logger.info(f"Generating automatic daily summary for chat {chat_id}")
        
        # Get messages from last day
        messages = self.storage.get_messages_from_last_day(chat_id)
        logger.info(f"Messages to summarize: {len(messages)}")

        if not messages:
            logger.info(f"No messages found for chat {chat_id}, skipping summary")
            return

        # Build conversation history for summary
        conversation_text = []
        for m in messages:
            time_str = ""
            if m.timestamp:
                time_ago = datetime.now() - m.timestamp
                hours_ago = int(time_ago.total_seconds() / 3600)
                if hours_ago < 1:
                    time_str = " (just now)"
                elif hours_ago < 24:
                    time_str = f" ({hours_ago}h ago)"
            conversation_text.append(f"{m.user}: {m.text}{time_str}")

        full_conversation = "\n".join(conversation_text)
        
        # Detect language from the most recent messages
        recent_texts = [m.text for m in messages[-5:]]  # Last 5 messages
        combined_recent_text = " ".join(recent_texts)
        detected_lang = self.ai_service.detect_language(combined_recent_text)
        language_name = self.ai_service.get_language_name(detected_lang)
        
        logger.info(f"Generating summary for {len(messages)} messages in {language_name} ({detected_lang})")
        
        # Generate summary using AI
        time_range = "last 24 hours" if any(m.timestamp and (datetime.now() - m.timestamp).total_seconds() < 86400 for m in messages) else "recent messages"
        
        # Build system prompt with language instruction
        system_prompt_with_lang = (
            f"{SUMMARY_SYSTEM_PROMPT}\n\n"
            f"CRITICAL: The conversation is in {language_name} ({detected_lang}). "
            f"You MUST respond in {language_name} ({detected_lang}). "
            f"Match the language of the conversation exactly."
        )
        
        summary_prompt = (
            f"Here's the conversation from the {time_range}:\n\n{full_conversation}\n\n"
            "Create a summary of what happened, who said what, and what the main topics were."
        )

        summary = await self.ai_service.call_llm(
            system_prompt_with_lang,
            summary_prompt,
            max_tokens=500
        )

        # Send summary to the chat
        try:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"📅 Daily Summary ({time_range} - {len(messages)} messages):\n\n{summary}"
            )
            logger.info(f"Successfully sent daily summary to chat {chat_id}")
        except Exception as e:
            logger.error(f"Failed to send summary to chat {chat_id}: {e}")

    async def daily_summary_job(self, context: ContextTypes.DEFAULT_TYPE) -> None:
        """
        Scheduled job to send daily summaries to all active chats.
        """
        logger.info("Running scheduled daily summary job")
        
        # Get all chat IDs that have messages
        chat_ids = self.storage.get_all_chat_ids()
        logger.info(f"Found {len(chat_ids)} chats with messages")
        
        # Generate and send summary for each chat
        for chat_id in chat_ids:
            try:
                await self.generate_summary_for_chat(context, chat_id)
            except Exception as e:
                logger.error(f"Error generating summary for chat {chat_id}: {e}")
        
        logger.info("Daily summary job completed")

    async def message_handler(
        self, update: Update, context: ContextTypes.DEFAULT_TYPE
    ):
        """Handle regular text messages."""
        if update.message is None or update.message.text is None:
            return

        text = update.message.text.strip()
        user = update.effective_user.first_name or "Unknown"
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id

        # Detect language of the message
        detected_lang = self.ai_service.detect_language(text)
        language_name = self.ai_service.get_language_name(detected_lang)
        logger.info(f"Detected language: {language_name} ({detected_lang}) for message: {text[:50]}")

        # Store message
        self.storage.store_message(user, text, chat_id, user_id)

        # Don't respond to commands
        if text.startswith("/"):
            return

        # Get recent context
        recent_messages = self.storage.get_recent_messages(chat_id, limit=15)
        history_snippets = "\n".join(
            f"{m.user}: {m.text}" for m in recent_messages
        )

        # Analyze conversation context
        conversation_analysis = await self.ai_service.analyze_conversation(
            text, history_snippets
        )

        # Check if bot was mentioned
        was_mentioned = self.is_bot_mentioned(update, context)
        
        # Decide if we should reply - now more context-aware and conversational
        should_reply = await self.ai_service.should_reply(
            text, history_snippets, was_mentioned
        )

        if not should_reply:
            return

        # Check if web search would be helpful
        search_query = await self.ai_service.should_search_web(text, history_snippets)
        search_results = []
        if search_query:
            logger.info(f"Searching web for: {search_query}")
            search_results = await self.ai_service.search_web(search_query)

        # Build system prompt using prompts module
        system_parts = get_base_system_prompt(
            conversation_analysis.get('tone', 'rude, sarcastic, funny'),
            language_name,
            detected_lang
        )
        
        system_parts.append(get_mention_prompt(was_mentioned))
        system_parts.extend(get_conversation_type_prompts(conversation_analysis))
        
        system_prompt = " ".join(system_parts)

        # Get personalized context
        user_context = self.storage.get_user_context(user_id, chat_id)

        # Build user prompt using prompts module
        user_prompt = get_user_prompt_base(history_snippets, user, text)
        user_prompt = get_user_prompt_with_context(user_prompt, user_context, user)
        user_prompt = get_user_prompt_with_search(user_prompt, search_results)
        user_prompt = get_user_prompt_final(user_prompt)

        reply = await self.ai_service.call_llm(
            system_prompt, user_prompt, max_tokens=150
        )
        
        # Send text reply
        await update.message.reply_text(reply)
        
        # Sometimes send a sticker (15% chance)
        if ENABLE_STICKERS and random.random() < STICKER_CHANCE:
            await self._send_contextual_sticker(update, context, text, history_snippets)
    
    async def _send_contextual_sticker(self, update: Update, context: ContextTypes.DEFAULT_TYPE, text: str, history: str):
        """
        Send a contextual sticker from the configured sticker set.
        
        Args:
            update: Telegram update
            context: Bot context
            text: Current message text
            history: Recent conversation history
        """
        try:
            # Try to get stickers from the set
            bot = context.bot
            
            # Get sticker set
            try:
                sticker_set = await bot.get_sticker_set(self.sticker_set_name)
                if not sticker_set.stickers:
                    logger.warning(f"Sticker set {self.sticker_set_name} is empty or not found")
                    return
                
                # Pick a random sticker from the set
                sticker = random.choice(sticker_set.stickers)
                await update.message.reply_sticker(sticker.file_id)
                logger.info(f"Sent sticker from {self.sticker_set_name}")
            except Exception as e:
                logger.warning(f"Could not get sticker set {self.sticker_set_name}: {e}")
                # Try alternative: search for sticker set or use a fallback
                # For now, just log the error
                return
                
        except Exception as e:
            logger.warning(f"Error sending sticker: {e}")

