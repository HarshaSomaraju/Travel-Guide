"""
Event types and emitter for real-time streaming
"""
from enum import Enum
from typing import Any, Optional
from dataclasses import dataclass, field, asdict
from datetime import datetime
import json
import asyncio
from queue import Queue


class EventType(str, Enum):
    """Event types for streaming to frontend"""
    THINKING = "thinking"        # LLM is processing
    QUESTION = "question"        # LLM asks clarification
    SEARCHING = "searching"      # Web search in progress
    PROGRESS = "progress"        # Step completion update
    PLAN = "plan"               # Final or partial plan
    ERROR = "error"             # Error occurred
    COMPLETE = "complete"       # Flow finished


@dataclass
class StreamEvent:
    """A streaming event to send to the frontend"""
    type: EventType
    content: str
    metadata: dict = field(default_factory=dict)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    
    def to_sse(self) -> str:
        """Convert to raw SSE format string (for manual SSE handling)"""
        data = self.to_dict()
        return f"event: {self.type.value}\ndata: {json.dumps(data)}\n\n"
    
    def to_sse_starlette(self) -> dict:
        """Convert to sse-starlette format (dict with 'event' and 'data' keys)"""
        return {
            "event": self.type.value,
            "data": json.dumps(self.to_dict())  # sse-starlette needs JSON string
        }
    
    def to_dict(self) -> dict:
        """Convert to dictionary"""
        return {
            "type": self.type.value,
            "content": self.content,
            "metadata": self.metadata,
            "timestamp": self.timestamp
        }


class EventEmitter:
    """
    Event emitter for streaming updates to the frontend.
    Uses an asyncio queue for async consumption.
    """
    
    def __init__(self):
        self._queue: asyncio.Queue = None
        self._sync_queue: Queue = Queue()
        self._closed = False
    
    def init_async_queue(self):
        """Initialize the async queue (must be called in async context)"""
        self._queue = asyncio.Queue()
    
    def emit(self, event_type: EventType, content: str, metadata: dict = None):
        """
        Emit an event (can be called from sync code).
        Events are stored in sync queue and transferred to async queue.
        """
        if self._closed:
            return
            
        event = StreamEvent(
            type=event_type,
            content=content,
            metadata=metadata or {}
        )
        self._sync_queue.put(event)
    
    def thinking(self, content: str):
        """Emit a thinking event"""
        self.emit(EventType.THINKING, content)
    
    def question(self, content: str, questions: list = None):
        """Emit a question event"""
        self.emit(EventType.QUESTION, content, {"questions": questions or []})
    
    def searching(self, content: str, query: str = None):
        """Emit a searching event"""
        self.emit(EventType.SEARCHING, content, {"query": query})
    
    def progress(self, content: str, step: str = None):
        """Emit a progress event"""
        self.emit(EventType.PROGRESS, content, {"step": step})
    
    def plan(self, content: str, is_final: bool = False):
        """Emit a plan event"""
        self.emit(EventType.PLAN, content, {"is_final": is_final})
    
    def error(self, content: str, error_type: str = None):
        """Emit an error event"""
        self.emit(EventType.ERROR, content, {"error_type": error_type})
    
    def complete(self, content: str = "Flow completed"):
        """Emit completion event"""
        self.emit(EventType.COMPLETE, content)
        self._closed = True
    
    async def get_events(self):
        """
        Async generator that yields events.
        Transfers events from sync queue to async stream.
        """
        if self._queue is None:
            self.init_async_queue()
        
        while not self._closed or not self._sync_queue.empty():
            # Transfer from sync to async queue
            while not self._sync_queue.empty():
                try:
                    event = self._sync_queue.get_nowait()
                    yield event
                except:
                    break
            
            # Small delay to avoid busy waiting
            await asyncio.sleep(0.1)
        
        # Drain any remaining events
        while not self._sync_queue.empty():
            try:
                event = self._sync_queue.get_nowait()
                yield event
            except:
                break
