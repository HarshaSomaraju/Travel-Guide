"""
Pydantic schemas for chat API
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


class ChatMessage(BaseModel):
    """A chat message"""
    role: str = Field(..., description="Role: 'user' or 'assistant'")
    content: str = Field(..., description="Message content")
    timestamp: Optional[str] = None


class ChatRequest(BaseModel):
    """Request to send a chat message"""
    session_id: Optional[str] = Field(None, description="Existing session ID or null for new")
    message: str = Field(..., description="User's message")


class ChatResponse(BaseModel):
    """Response after sending a chat message"""
    session_id: str = Field(..., description="Session ID")
    status: str = Field(..., description="Status: processing, waiting_input, complete")
    stream_url: str = Field(..., description="SSE stream URL for events")


class SessionInfo(BaseModel):
    """Session information"""
    id: str
    created_at: str
    updated_at: str
    status: str
    message_count: int
    has_plan: bool


class SessionDetail(SessionInfo):
    """Detailed session info with messages"""
    messages: List[ChatMessage] = []
    trip_info: dict = {}
    final_plan: Optional[str] = None
