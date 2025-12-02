"""Services for AI and storage operations."""
import asyncio
import json
import logging
import random
from typing import List, Optional, Dict

from openai import OpenAI, RateLimitError
from duckduckgo_search import DDGS
from langdetect import detect, LangDetectException

from config import (
    OPENAI_API_KEY,
    MAX_RECENT_MESSAGES,
    MAX_USER_MESSAGES,
    DEFAULT_AI_MODEL,
    DEFAULT_TEMPERATURE,
    ENABLE_WEB_SEARCH,
    MAX_SEARCH_RESULTS,
    ENABLE_STICKERS,
    STICKER_CHANCE,
    STICKER_SET_NAME,
    logger,
)
from models import Message, UserProfile
from messages import (
    DECISION_SYSTEM_PROMPT,
    ANALYZER_SYSTEM_PROMPT,
    SEARCH_QUERY_SYSTEM_PROMPT,
    ASK_SYSTEM_PROMPT,
    RATE_LIMIT_MESSAGE,
    AI_ERROR_MESSAGE,
)

logger = logging.getLogger(__name__)


class AIService:
    """Service for AI/LLM operations."""

    def __init__(self, api_key: str, model: str = DEFAULT_AI_MODEL):
        """Initialize AI service with OpenAI client."""
        self.client = OpenAI(api_key=api_key)
        self.model = model

    def detect_language(self, text: str) -> str:
        """
        Detect the language of the given text.

        Args:
            text: Text to detect language for

        Returns:
            Language code (e.g., 'en', 'ru', 'es') or 'en' as default
        """
        if not text or len(text.strip()) < 3:
            return 'en'

        try:
            lang = detect(text)
            return lang
        except LangDetectException:
            return 'en'

    def get_language_name(self, lang_code: str) -> str:
        """
        Get human-readable language name from code.

        Args:
            lang_code: Language code (e.g., 'en', 'ru')

        Returns:
            Language name or code if unknown
        """
        language_names = {
            'en': 'English',
            'ru': 'Russian',
            'es': 'Spanish',
            'fr': 'French',
            'de': 'German',
            'it': 'Italian',
            'pt': 'Portuguese',
            'pl': 'Polish',
            'uk': 'Ukrainian',
            'ar': 'Arabic',
            'zh': 'Chinese',
            'ja': 'Japanese',
            'ko': 'Korean',
            'tr': 'Turkish',
            'nl': 'Dutch',
            'sv': 'Swedish',
            'no': 'Norwegian',
            'da': 'Danish',
            'fi': 'Finnish',
            'cs': 'Czech',
            'hu': 'Hungarian',
            'ro': 'Romanian',
            'bg': 'Bulgarian',
            'hr': 'Croatian',
            'sr': 'Serbian',
            'sk': 'Slovak',
            'sl': 'Slovenian',
            'el': 'Greek',
            'he': 'Hebrew',
            'th': 'Thai',
            'vi': 'Vietnamese',
            'id': 'Indonesian',
            'ms': 'Malay',
            'hi': 'Hindi',
        }
        return language_names.get(lang_code, lang_code)

    async def call_llm(
        self, system_prompt: str, user_prompt: str, max_tokens: int = 256
    ) -> str:
        """
        Call OpenAI Chat Completions API.

        Args:
            system_prompt: System message for the AI
            user_prompt: User message/prompt
            max_tokens: Maximum tokens in response

        Returns:
            AI response text
        """
        try:
            resp = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                max_tokens=max_tokens,
                temperature=DEFAULT_TEMPERATURE,
            )
            return resp.choices[0].message.content.strip()
        except RateLimitError as e:
            logger.warning("OpenAI rate limit/quota exceeded: %s", e)
            return RATE_LIMIT_MESSAGE
        except Exception as e:
            logger.exception("Error calling OpenAI: %s", e)
            return AI_ERROR_MESSAGE

    async def should_reply(
        self, text: str, recent_context: str = "", was_mentioned: bool = False
    ) -> bool:
        """
        Use AI to decide if bot should reply to a message based on context.
        More conversational - supports ongoing conversations naturally.

        Args:
            text: The message text
            recent_context: Recent conversation context
            was_mentioned: Whether bot was directly mentioned

        Returns:
            True if bot should reply, False otherwise
        """
        # Always reply if mentioned
        if was_mentioned:
            return True

        # If there's no context, use a higher base chance for engagement
        if not recent_context.strip():
            # 30% chance to engage in new conversations
            return random.random() < 0.30

        decision_prompt = (
            "You are analyzing a Telegram group chat to decide if an AI bot should naturally join the conversation.\n\n"
            f"Recent conversation:\n{recent_context}\n\n"
            f"Latest message: {text}\n\n"
            "Should the bot respond naturally? Consider:\n"
            "- Can the bot add value or continue the conversation naturally?\n"
            "- Is there an opportunity to be helpful, supportive, or engaging?\n"
            "- Would a response feel natural in this context?\n"
            "- Is the conversation ongoing and could use support?\n"
            "- Even if not a direct question, can the bot contribute meaningfully?\n"
            "- The bot should be conversational and supportive, not just answer questions.\n\n"
            "Be more lenient - if the conversation could benefit from engagement, say YES.\n"
            "Respond with ONLY 'YES' or 'NO' - nothing else."
        )

        try:
            decision = await self.call_llm(
                DECISION_SYSTEM_PROMPT,
                decision_prompt,
                max_tokens=10,
            )
            decision = decision.strip().upper()
            should_reply = decision.startswith("YES")

            # Add some randomness for natural conversation flow (even if AI says no, sometimes reply)
            if not should_reply and random.random() < 0.15:  # 15% chance to reply anyway
                logger.info("Randomly engaging in conversation for natural flow")
                return True

            return should_reply
        except Exception as e:
            logger.warning(f"Error in AI decision-making, using fallback: {e}")
            # Fallback: more lenient - questions, greetings, or 25% random
            return "?" in text or random.random() < 0.25

    async def analyze_conversation(
        self, text: str, recent_context: str
    ) -> Dict[str, any]:
        """
        Analyze conversation tone and context using AI.

        Args:
            text: Current message text
            recent_context: Recent conversation history

        Returns:
            Dictionary with analysis results
        """
        analysis_prompt = (
            f"Analyze this Telegram group chat message and context:\n\n"
            f"Recent conversation:\n{recent_context}\n\n"
            f"Current message: {text}\n\n"
            "Analyze and respond in this exact JSON format:\n"
            '{"is_social": true/false, "is_question": true/false, "needs_response": true/false, "tone": "casual/formal/excited/etc"}'
        )

        try:
            analysis = await self.call_llm(
                ANALYZER_SYSTEM_PROMPT,
                analysis_prompt,
                max_tokens=100,
            )
            # Extract JSON from response
            analysis = analysis.strip()
            if analysis.startswith("```"):
                analysis = analysis.split("```")[1]
                if analysis.startswith("json"):
                    analysis = analysis[4:]
            analysis = analysis.strip()
            if analysis.startswith("{"):
                return json.loads(analysis)
        except Exception as e:
            logger.warning(f"Error analyzing conversation tone: {e}")

        # Fallback
        return {
            "is_social": False,
            "is_question": "?" in text,
            "needs_response": "?" in text,
            "tone": "casual",
        }

    async def should_search_web(self, text: str, recent_context: str) -> Optional[str]:
        """
        Determine if web search would be helpful based on conversation context.

        Args:
            text: Current message text
            recent_context: Recent conversation history

        Returns:
            Search query string if search is recommended, None otherwise
        """
        if not ENABLE_WEB_SEARCH:
            return None

        search_prompt = (
            "Analyze this Telegram group chat conversation to determine if web search would be helpful.\n\n"
            f"Recent conversation:\n{recent_context}\n\n"
            f"Latest message: {text}\n\n"
            "Should the bot search the internet for information? Consider:\n"
            "- Is someone asking about current information, prices, locations, or facts?\n"
            "- Would real-time data or recent information be helpful?\n"
            "- Are they discussing topics that could benefit from web search (rentals, products, services, etc.)?\n"
            "- Would search results help provide better suggestions or solutions?\n\n"
            "If search would be helpful, respond with a search query (2-5 words).\n"
            "If not needed, respond with ONLY 'NO'.\n"
            "Example: 'house rental prices' or 'best restaurants near me' or 'NO'"
        )

        try:
            response = await self.call_llm(
                SEARCH_QUERY_SYSTEM_PROMPT,
                search_prompt,
                max_tokens=20,
            )
            response = response.strip().upper()
            if response == "NO" or len(response) < 3:
                return None
            # Extract search query (take first line or first few words)
            query = response.split('\n')[0].strip()
            if len(query) > 100:  # Too long, probably not a query
                return None
            return query
        except Exception as e:
            logger.warning(f"Error determining if search needed: {e}")
            return None

    async def search_web(self, query: str) -> List[Dict[str, str]]:
        """
        Search the web using DuckDuckGo.

        Args:
            query: Search query string

        Returns:
            List of search results with title, snippet, and url
        """
        if not query:
            return []

        try:
            # Use DuckDuckGo search (free, no API key needed)
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=MAX_SEARCH_RESULTS):
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", "")
                    })
                return results
        except Exception as e:
            logger.warning(f"Error searching web: {e}")
            return []



class StorageService:
    """Service for message and user profile storage."""

    def __init__(self, max_messages: int = MAX_RECENT_MESSAGES):
        """Initialize storage service."""
        self.recent_messages: List[Message] = []
        self.user_profiles: Dict[int, UserProfile] = {}
        self.max_messages = max_messages
        self.max_user_messages = MAX_USER_MESSAGES

    def store_message(
        self, user: str, text: str, chat_id: int, user_id: Optional[int] = None
    ) -> None:
        """
        Store a message and update user profile.

        Args:
            user: User name
            text: Message text
            chat_id: Chat ID
            user_id: User ID (optional)
        """
        if not text:
            return

        from datetime import datetime
        message = Message(
            user=user,
            text=text,
            chat_id=chat_id,
            user_id=user_id,
            timestamp=datetime.now()
        )
        self.recent_messages.append(message)
        logger.info(f"Stored message from {user} in chat {chat_id} (total messages: {len(self.recent_messages)})")

        # Maintain max messages limit
        if len(self.recent_messages) > self.max_messages:
            self.recent_messages = self.recent_messages[
                -self.max_messages :
            ]

        # Update user profile
        if user_id:
            self._update_user_profile(user_id, user, text)

    def _update_user_profile(
        self, user_id: int, name: str, text: str
    ) -> None:
        """Update user profile with new message."""
        if user_id not in self.user_profiles:
            self.user_profiles[user_id] = UserProfile(
                name=name, messages=[], interests=set(), topics=[]
            )

        profile = self.user_profiles[user_id]
        profile.messages.append(text)

        # Keep last N messages per user
        if len(profile.messages) > self.max_user_messages:
            profile.messages.pop(0)

    def get_recent_messages(self, chat_id: int, limit: int = 15) -> List[Message]:
        """
        Get recent messages for a chat.

        Args:
            chat_id: Chat ID
            limit: Maximum number of messages to return

        Returns:
            List of recent messages
        """
        messages = [
            m for m in self.recent_messages if m.chat_id == chat_id
        ]
        return messages[-limit:]

    def search_messages(
        self, query: str, chat_id: int, limit: int = 5
    ) -> List[Message]:
        """
        Search messages in a chat.

        Args:
            query: Search query
            chat_id: Chat ID
            limit: Maximum number of results

        Returns:
            List of matching messages
        """
        query_lower = query.lower()
        matches = [
            m
            for m in self.recent_messages
            if m.chat_id == chat_id and query_lower in m.text.lower()
        ]
        return matches[-limit:]

    def get_all_chat_ids(self) -> List[int]:
        """
        Get all unique chat IDs that have messages stored.
        
        Returns:
            List of unique chat IDs
        """
        chat_ids = set()
        for m in self.recent_messages:
            chat_ids.add(m.chat_id)
        return list(chat_ids)

    def get_messages_from_last_day(self, chat_id: int) -> List[Message]:
        """
        Get all messages from the last 24 hours.
        If no messages in last 24h, returns most recent messages (up to 50).

        Args:
            chat_id: Chat ID

        Returns:
            List of messages from last 24 hours, or recent messages if none found
        """
        from datetime import datetime, timedelta
        cutoff_time = datetime.now() - timedelta(days=1)

        # Get all messages for this chat
        chat_messages = [m for m in self.recent_messages if m.chat_id == chat_id]
        logger.info(f"Total messages in chat {chat_id}: {len(chat_messages)}")
        
        if not chat_messages:
            logger.warning(f"No messages found for chat {chat_id}")
            return []

        messages_with_timestamps = []
        messages_without_timestamps = []
        
        for m in chat_messages:
            if m.timestamp:
                if m.timestamp >= cutoff_time:
                    messages_with_timestamps.append(m)
            else:
                # Messages without timestamps (old format) - include them
                messages_without_timestamps.append(m)
        
        # If we have messages from last 24h, return those
        if messages_with_timestamps:
            logger.info(f"Found {len(messages_with_timestamps)} messages from last 24 hours")
            return messages_with_timestamps
        
        # If no messages in last 24h but we have messages without timestamps, return those
        if messages_without_timestamps:
            logger.info(f"No messages in last 24h, using {len(messages_without_timestamps)} messages without timestamps")
            return messages_without_timestamps[-50:]  # Last 50 messages
        
        # If we have messages but none match, return most recent ones anyway
        if chat_messages:
            logger.info(f"No messages in last 24h, returning most recent {min(50, len(chat_messages))} messages")
            return chat_messages[-50:]
        
        return []

    def get_user_context(self, user_id: int, chat_id: int) -> str:
        """
        Build personalized context for a user.

        Args:
            user_id: User ID
            chat_id: Chat ID

        Returns:
            Context string about the user
        """
        if user_id not in self.user_profiles:
            return ""

        profile = self.user_profiles[user_id]
        context_parts = []

        # Get user's recent messages from this chat
        user_messages = [
            m
            for m in self.recent_messages
            if m.user_id == user_id and m.chat_id == chat_id
        ][-10:]

        if user_messages:
            context_parts.append(f"User {profile.name} has been discussing:")
            for msg in user_messages[-5:]:
                context_parts.append(f"- {msg.text[:100]}")

        # Extract common topics from user's messages
        if len(profile.messages) > 5:
            all_text = " ".join(profile.messages[-20:]).lower()
            common_words = {}
            for word in all_text.split():
                if len(word) > 4:  # Skip short words
                    common_words[word] = common_words.get(word, 0) + 1

            # Get top 3 most mentioned topics
            if common_words:
                top_topics = sorted(
                    common_words.items(), key=lambda x: x[1], reverse=True
                )[:3]
                if top_topics:
                    topics = [
                        word for word, count in top_topics if count > 2
                    ]
                    if topics:
                        context_parts.append(
                            f"\n{profile.name} often talks about: {', '.join(topics)}"
                        )

        return "\n".join(context_parts) if context_parts else ""

