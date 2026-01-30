"""
In-memory session manager for conversation state
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
import uuid
from app.core.events import EventEmitter


@dataclass
class Session:
    """A chat session storing conversation state"""
    id: str
    created_at: datetime
    updated_at: datetime
    
    # Conversation history
    messages: list = field(default_factory=list)
    
    # PocketFlow shared store
    shared: dict = field(default_factory=dict)
    
    # Current status
    status: str = "idle"  # idle, processing, waiting_input, complete
    
    # Event emitter for this session
    emitter: EventEmitter = field(default_factory=EventEmitter)
    
    def add_message(self, role: str, content: str):
        """Add a message to conversation history"""
        self.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        })
        self.updated_at = datetime.now()
    
    def init_shared_store(self):
        """Initialize the PocketFlow shared store"""
        self.shared = {
            # Conversation tracking for dynamic question flow
            "conversation_history": [],
            
            # Trip info - populated dynamically by LLM
            "trip_info": {},
            
            # Clarification tracking
            "clarification_round": 0,
            "max_clarification_rounds": 5,
            
            # Research results
            "destination_info": {},
            "accommodations": [],
            "transportation": {},
            "activities": [],
            "restaurants": [],
            
            # Planning outputs
            "daily_plans": [],
            "narrative_story": "",
            "final_travel_guide": "",
            "plan_revision_count": 0,
            
            # Event emitter for streaming
            "emitter": self.emitter,
        }
    
    def to_dict(self) -> dict:
        """Convert session to dictionary (for API response)"""
        return {
            "id": self.id,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "status": self.status,
            "message_count": len(self.messages),
            "has_plan": bool(self.shared.get("final_travel_guide")),
        }


class SessionManager:
    """In-memory session manager"""
    
    def __init__(self):
        self._sessions: Dict[str, Session] = {}
    
    def create_session(self) -> Session:
        """Create a new session"""
        session_id = str(uuid.uuid4())
        now = datetime.now()
        
        session = Session(
            id=session_id,
            created_at=now,
            updated_at=now
        )
        session.init_shared_store()
        
        self._sessions[session_id] = session
        return session
    
    def get_session(self, session_id: str) -> Optional[Session]:
        """Get a session by ID"""
        return self._sessions.get(session_id)
    
    def get_or_create_session(self, session_id: Optional[str] = None) -> Session:
        """Get existing session or create new one"""
        if session_id and session_id in self._sessions:
            return self._sessions[session_id]
        return self.create_session()
    
    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
    
    def list_sessions(self) -> list:
        """List all sessions"""
        return [s.to_dict() for s in self._sessions.values()]


# Global session manager instance
session_manager = SessionManager()
