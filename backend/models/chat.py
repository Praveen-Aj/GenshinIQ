"""Data models for chat messages, requests, and grounded responses."""

from typing import List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """A single message in the chat history."""
    role: str = Field(..., description="user or model")
    content: str = Field(..., description="The markdown text content of the message")


class ChatRequest(BaseModel):
    """Payload to request assistant generation."""
    messages: List[ChatMessage] = Field(..., description="History of chat messages")
    uid: Optional[str] = Field(None, description="Active Genshin Impact UID")


class Citation(BaseModel):
    """Source citation context for grounded facts/guidelines."""
    source_name: str = Field(..., description="E.g., KeqingMains, HoYoverse")
    source_url: str = Field(..., description="Source URL link")
    snippet: str = Field(..., description="Matching text context snippet")
    character: Optional[str] = None
    topic: Optional[str] = None
    game_version: Optional[str] = None


class ChatResponse(BaseModel):
    """Response payload containing generated message, classification intent, and citations."""
    content: str = Field(..., description="Grounded response text")
    intent: str = Field(..., description="general or account")
    citations: List[Citation] = Field(default_factory=list, description="Retrieve source references")
