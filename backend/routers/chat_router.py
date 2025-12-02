"""Chat/Q&A router for RAG agent"""
from fastapi import APIRouter, HTTPException, Depends

from fastapi.responses import StreamingResponse
from pydantic import BaseModel

from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional, AsyncGenerator
import os
import uuid
import json
import asyncio
from dotenv import load_dotenv

from Agent.rag_agent.react_agent import PolicyRAGAgent
from backend.database import User, ChatSession, ChatMessage, get_db
from backend.routers.auth_router import get_current_user

load_dotenv()

router = APIRouter(tags=["chat"])

# Initialize agent (lazy loading)
agent = None

def get_agent():
    global agent
    if agent is None:
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        agent = PolicyRAGAgent(google_api_key=google_api_key, temperature=0.1)
    return agent


class ChatRequest(BaseModel):
    question: str
    thread_id: Optional[str] = "default"  # Deprecated, use session_id instead
    session_id: Optional[int] = None  # NEW: Optional session ID


class ChatResponse(BaseModel):
    answer: str
    citations: list
    confidence: float
    status: str
    session_id: Optional[int] = None  # NEW: Return session ID
    message_id: Optional[int] = None  # NEW: Return message ID


def get_or_create_session(
    session_id: Optional[int],
    user_id: int,
    db: Session
) -> ChatSession:
    """
    Get existing session or create new one
    
    Args:
        session_id: Optional session ID
        user_id: Current user ID
        db: Database session
    
    Returns:
        ChatSession object
    """
    if session_id:
        # Get existing session and verify ownership
        session = db.query(ChatSession).filter(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        ).first()
        
        if not session:
            raise HTTPException(
                status_code=404,
                detail="Session not found or you don't have access to it"
            )
        
        return session
    else:
        # Create new session
        thread_id = str(uuid.uuid4())
        session = ChatSession(
            user_id=user_id,
            title="New Chat",
            thread_id=thread_id
        )
        db.add(session)
        db.commit()
        db.refresh(session)
        return session


async def generate_stream(question: str, thread_id: str, user_role: str = None, user_institution_id: int = None) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for chat response
    
    Yields SSE formatted events with:
    - content chunks (token-by-token)
    - citations (when available)
    - final metadata (confidence, status)
    """
    try:
        rag_agent = get_agent()
        
        # Stream the response with user context
        async for chunk in rag_agent.query_stream(question, thread_id, user_role, user_institution_id):
            event_type = chunk.get("type", "content")
            
            if event_type == "content":
                # Stream content tokens
                data = {
                    "type": "content",
                    "token": chunk.get("token", ""),
                    "timestamp": chunk.get("timestamp")
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            elif event_type == "citation":
                # Stream citations as they're discovered
                data = {
                    "type": "citation",
                    "citation": chunk.get("citation"),
                    "timestamp": chunk.get("timestamp")
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            elif event_type == "metadata":
                # Final metadata
                data = {
                    "type": "metadata",
                    "confidence": chunk.get("confidence", 0.0),
                    "status": chunk.get("status", "success"),
                    "timestamp": chunk.get("timestamp")
                }
                yield f"data: {json.dumps(data)}\n\n"
                
            elif event_type == "error":
                # Error occurred
                data = {
                    "type": "error",
                    "message": chunk.get("message", "Unknown error"),
                    "recoverable": chunk.get("recoverable", False)
                }
                yield f"data: {json.dumps(data)}\n\n"
                
        # Send done signal
        yield f"data: {json.dumps({'type': 'done'})}\n\n"
        
    except Exception as e:
        error_data = {
            "type": "error",
            "message": str(e),
            "recoverable": False
        }
        yield f"data: {json.dumps(error_data)}\n\n"


@router.post("/query/stream")
async def chat_query_stream(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Ask a question to the RAG agent with streaming response (SSE)
    
    Args:
        question: The question to ask
        thread_id: Optional thread ID for conversation memory
    
    Returns:
        Server-Sent Events stream with:
        - content: Token chunks as they're generated
        - citation: Citations as they're discovered (with approval status)
        - metadata: Final confidence and status
        - done: Stream completion signal
    
    Requires authentication - applies role-based access control
    """
    return StreamingResponse(
        generate_stream(
            request.question, 
            request.thread_id,
            current_user.role,
            current_user.institution_id
        ),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"  # Disable nginx buffering
        }
    )


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Ask a question to the RAG agent (non-streaming, backward compatible)
    
    Args:
        question: The question to ask
        session_id: Optional session ID (creates new if not provided)
        thread_id: Deprecated, use session_id instead
    
    Returns:
        Answer with citations, confidence score, session_id, and message_id
    
    Requires authentication - all authenticated users can query
    
    NEW: Now saves all messages to database for chat history
    """
    try:
        # Step 1: Get or create session
        session = get_or_create_session(request.session_id, current_user.id, db)
        
        # Step 2: Save user message to database
        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.question
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Step 3: Query the RAG agent using session's thread_id with user context
        rag_agent = get_agent()
        # Pass user context to agent for role-based filtering
        result = rag_agent.query(
            request.question, 
            session.thread_id,
            user_role=current_user.role,
            user_institution_id=current_user.institution_id
        )
        
        # Step 4: Save AI response to database
        ai_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=result["answer"],
            citations=result.get("citations", []),
            confidence=int(result.get("confidence", 0) * 100) if result.get("confidence", 0) <= 1 else int(result.get("confidence", 0))  # Handle both 0-1 and 0-100 formats
        )
        db.add(ai_message)
        
        # Step 5: Update session timestamp
        session.updated_at = datetime.utcnow()
        
        # Step 6: Auto-generate title from first user message
        if session.title == "New Chat":
            # Get first 50 characters of user message
            title = request.question[:50]
            if len(request.question) > 50:
                title += "..."
            session.title = title
        
        db.commit()
        db.refresh(ai_message)
        
        # Step 7: Return response with session and message IDs
        return ChatResponse(
            answer=result["answer"],
            citations=result.get("citations", []),
            confidence=result.get("confidence", 0.0),
            status=result.get("status", "success"),
            session_id=session.id,
            message_id=ai_message.id
        )
        
    except HTTPException:
        # Re-raise HTTP exceptions (like 404 for invalid session)
        raise
    except Exception as e:
        # Log error and return 500
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/health")
async def chat_health():
    """Check if chat service is healthy"""
    try:
        rag_agent = get_agent()
        return {
            "status": "healthy",
            "model": "gemini-2.0-flash-exp",
            "tools": len(rag_agent.tools)
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }
