"""
Chat History Router - Manage chat sessions and messages
"""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_, func
from typing import List, Optional
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

from backend.database import get_db, ChatSession, ChatMessage, User
from backend.routers.auth_router import get_current_user

router = APIRouter()


# ============================================================================
# Request/Response Models
# ============================================================================

class CreateSessionRequest(BaseModel):
    """Request model for creating a new chat session"""
    title: Optional[str] = Field(None, max_length=200, description="Optional session title")


class SessionResponse(BaseModel):
    """Response model for chat session"""
    session_id: int
    title: str
    thread_id: str
    created_at: datetime
    updated_at: datetime
    message_count: Optional[int] = 0
    last_message: Optional[str] = None
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """Response model for chat message"""
    id: int
    role: str
    content: str
    citations: List[dict] = []
    confidence: Optional[int] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class UpdateTitleRequest(BaseModel):
    """Request model for updating session title"""
    title: str = Field(..., min_length=1, max_length=200, description="New session title")


class SessionListResponse(BaseModel):
    """Response model for session list"""
    sessions: List[SessionResponse]
    total: int
    limit: int
    offset: int


class MessagesResponse(BaseModel):
    """Response model for messages list"""
    session_id: int
    messages: List[MessageResponse]


# ============================================================================
# Endpoints
# ============================================================================

@router.post("/sessions", response_model=SessionResponse, tags=["chat-history"])
async def create_session(
    request: CreateSessionRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new chat session
    
    - **title**: Optional session title (defaults to "New Chat")
    - Returns session details including unique thread_id for agent memory
    """
    # Generate unique thread_id for LangGraph
    thread_id = str(uuid.uuid4())
    
    # Create session
    session = ChatSession(
        user_id=current_user.id,
        title=request.title or "New Chat",
        thread_id=thread_id
    )
    
    db.add(session)
    db.commit()
    db.refresh(session)
    
    return SessionResponse(
        session_id=session.id,
        title=session.title,
        thread_id=session.thread_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=0,
        last_message=None
    )


@router.get("/sessions", response_model=SessionListResponse, tags=["chat-history"])
async def list_sessions(
    limit: int = Query(20, ge=1, le=100, description="Number of sessions to return"),
    offset: int = Query(0, ge=0, description="Number of sessions to skip"),
    search: Optional[str] = Query(None, description="Search query for title or content"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all chat sessions for the current user
    
    - **limit**: Number of sessions to return (1-100, default 20)
    - **offset**: Number of sessions to skip (for pagination)
    - **search**: Optional search query to filter sessions
    - Returns paginated list of sessions with message counts and previews
    """
    # Base query - only user's sessions
    query = db.query(ChatSession).filter(ChatSession.user_id == current_user.id)
    
    # Apply search filter if provided
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            or_(
                ChatSession.title.ilike(search_term),
                ChatSession.id.in_(
                    db.query(ChatMessage.session_id).filter(
                        ChatMessage.content.ilike(search_term)
                    )
                )
            )
        )
    
    # Get total count
    total = query.count()
    
    # Get paginated sessions ordered by most recent
    sessions = query.order_by(ChatSession.updated_at.desc()).offset(offset).limit(limit).all()
    
    # Build response with message counts and previews
    session_responses = []
    for session in sessions:
        # Get message count
        message_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.session_id == session.id
        ).scalar()
        
        # Get last message preview
        last_message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.desc()).first()
        
        last_message_text = None
        if last_message:
            # Get first 50 characters
            last_message_text = last_message.content[:50]
            if len(last_message.content) > 50:
                last_message_text += "..."
        
        session_responses.append(SessionResponse(
            session_id=session.id,
            title=session.title,
            thread_id=session.thread_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
            last_message=last_message_text
        ))
    
    return SessionListResponse(
        sessions=session_responses,
        total=total,
        limit=limit,
        offset=offset
    )


@router.get("/sessions/{session_id}/messages", response_model=MessagesResponse, tags=["chat-history"])
async def get_session_messages(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all messages for a specific chat session
    
    - **session_id**: ID of the chat session
    - Returns all messages ordered by creation time (oldest first)
    - Returns 403 if session doesn't belong to current user
    """
    # Get session and verify ownership
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or you don't have access to it"
        )
    
    # Get all messages ordered by creation time
    messages = db.query(ChatMessage).filter(
        ChatMessage.session_id == session_id
    ).order_by(ChatMessage.created_at.asc()).all()
    
    # Convert to response model
    message_responses = [
        MessageResponse(
            id=msg.id,
            role=msg.role,
            content=msg.content,
            citations=msg.citations or [],
            confidence=msg.confidence,
            created_at=msg.created_at
        )
        for msg in messages
    ]
    
    return MessagesResponse(
        session_id=session_id,
        messages=message_responses
    )


@router.put("/sessions/{session_id}", response_model=SessionResponse, tags=["chat-history"])
async def update_session_title(
    session_id: int,
    request: UpdateTitleRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update the title of a chat session
    
    - **session_id**: ID of the chat session
    - **title**: New title (1-200 characters)
    - Returns updated session details
    - Returns 403 if session doesn't belong to current user
    """
    # Get session and verify ownership
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or you don't have access to it"
        )
    
    # Update title
    session.title = request.title
    session.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(session)
    
    # Get message count for response
    message_count = db.query(func.count(ChatMessage.id)).filter(
        ChatMessage.session_id == session.id
    ).scalar()
    
    return SessionResponse(
        session_id=session.id,
        title=session.title,
        thread_id=session.thread_id,
        created_at=session.created_at,
        updated_at=session.updated_at,
        message_count=message_count
    )


@router.delete("/sessions/{session_id}", tags=["chat-history"])
async def delete_session(
    session_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a chat session and all its messages
    
    - **session_id**: ID of the chat session to delete
    - Cascade deletes all messages in the session
    - Returns 403 if session doesn't belong to current user
    """
    # Get session and verify ownership
    session = db.query(ChatSession).filter(
        ChatSession.id == session_id,
        ChatSession.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(
            status_code=404,
            detail="Session not found or you don't have access to it"
        )
    
    # Delete session (cascade deletes messages)
    db.delete(session)
    db.commit()
    
    return {
        "message": "Session deleted successfully",
        "session_id": session_id
    }


@router.get("/sessions/search", response_model=SessionListResponse, tags=["chat-history"])
async def search_sessions(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100, description="Number of results to return"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search chat sessions by title or message content
    
    - **q**: Search query (required)
    - **limit**: Number of results to return (1-100, default 20)
    - Searches in session titles and message content
    - Returns matching sessions ordered by relevance (most recent first)
    """
    search_term = f"%{q}%"
    
    # Search in titles and message content
    query = db.query(ChatSession).filter(
        ChatSession.user_id == current_user.id,
        or_(
            ChatSession.title.ilike(search_term),
            ChatSession.id.in_(
                db.query(ChatMessage.session_id).filter(
                    ChatMessage.content.ilike(search_term)
                )
            )
        )
    )
    
    # Get total count
    total = query.count()
    
    # Get sessions ordered by most recent
    sessions = query.order_by(ChatSession.updated_at.desc()).limit(limit).all()
    
    # Build response with message counts and previews
    session_responses = []
    for session in sessions:
        # Get message count
        message_count = db.query(func.count(ChatMessage.id)).filter(
            ChatMessage.session_id == session.id
        ).scalar()
        
        # Get last message preview
        last_message = db.query(ChatMessage).filter(
            ChatMessage.session_id == session.id
        ).order_by(ChatMessage.created_at.desc()).first()
        
        last_message_text = None
        if last_message:
            last_message_text = last_message.content[:50]
            if len(last_message.content) > 50:
                last_message_text += "..."
        
        session_responses.append(SessionResponse(
            session_id=session.id,
            title=session.title,
            thread_id=session.thread_id,
            created_at=session.created_at,
            updated_at=session.updated_at,
            message_count=message_count,
            last_message=last_message_text
        ))
    
    return SessionListResponse(
        sessions=session_responses,
        total=total,
        limit=limit,
        offset=0
    )
