"""
Chat API routes
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from sse_starlette.sse import EventSourceResponse
import asyncio

from app.schemas.chat import ChatRequest, ChatResponse, SessionInfo, SessionDetail
from app.core.sessions import session_manager
from app.core.events import EventType
from app.services.travel_flow import run_travel_flow_async

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def send_message(request: ChatRequest, background_tasks: BackgroundTasks):
    """
    Send a message to start or continue a conversation.
    Returns session ID and stream URL for SSE events.
    """
    # Get or create session
    session = session_manager.get_or_create_session(request.session_id)
    
    # Add user message to history
    session.add_message("user", request.message)
    
    # Determine if this is a new conversation or continuing
    is_resuming = session.status == "waiting_input"
    
    session.status = "processing"
    
    # Start or resume flow processing in background
    background_tasks.add_task(run_travel_flow_async, session, request.message)
    
    return ChatResponse(
        session_id=session.id,
        status=session.status,
        stream_url=f"/api/chat/{session.id}/stream"
    )


@router.get("/{session_id}/stream")
async def stream_events(session_id: str):
    """
    SSE endpoint for streaming events from the flow.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    async def event_generator():
        """Generate SSE events from the session's event emitter"""
        emitter = session.emitter
        
        async for event in emitter.get_events():
            yield event.to_sse_starlette()
            
            # If complete, stop streaming
            if event.type == EventType.COMPLETE:
                break
    
    return EventSourceResponse(event_generator())


@router.get("/{session_id}", response_model=SessionDetail)
async def get_session(session_id: str):
    """
    Get session details including messages and plan.
    """
    session = session_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    return SessionDetail(
        id=session.id,
        created_at=session.created_at.isoformat(),
        updated_at=session.updated_at.isoformat(),
        status=session.status,
        message_count=len(session.messages),
        has_plan=bool(session.shared.get("final_travel_guide")),
        messages=session.messages,
        trip_info=session.shared.get("trip_info", {}),
        final_plan=session.shared.get("final_travel_guide")
    )


@router.delete("/{session_id}")
async def delete_session(session_id: str):
    """Delete a session"""
    if session_manager.delete_session(session_id):
        return {"status": "deleted"}
    raise HTTPException(status_code=404, detail="Session not found")


@router.get("", response_model=list[SessionInfo])
async def list_sessions():
    """List all sessions"""
    return session_manager.list_sessions()
