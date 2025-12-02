"""Data models for the bot."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Set


@dataclass
class Message:
    """Represents a chat message."""
    user: str
    text: str
    chat_id: int
    user_id: Optional[int] = None
    timestamp: Optional[datetime] = None

    def __post_init__(self):
        """Set timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.now()

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "user": self.user,
            "text": self.text,
            "chat_id": self.chat_id,
            "user_id": self.user_id,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Message":
        """Create from dictionary."""
        timestamp = None
        if data.get("timestamp"):
            timestamp = datetime.fromisoformat(data["timestamp"])
        return cls(
            user=data.get("user", ""),
            text=data.get("text", ""),
            chat_id=data.get("chat_id", 0),
            user_id=data.get("user_id"),
            timestamp=timestamp,
        )


@dataclass
class UserProfile:
    """Represents a user's profile based on chat history."""
    name: str
    messages: List[str]
    interests: Set[str]
    topics: List[str]

    def __post_init__(self):
        """Ensure interests is a set."""
        if not isinstance(self.interests, set):
            self.interests = set(self.interests)

    def to_dict(self) -> dict:
        """Convert to dictionary for storage."""
        return {
            "name": self.name,
            "messages": self.messages,
            "interests": list(self.interests),
            "topics": self.topics,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "UserProfile":
        """Create from dictionary."""
        return cls(
            name=data.get("name", ""),
            messages=data.get("messages", []),
            interests=set(data.get("interests", [])),
            topics=data.get("topics", []),
        )

