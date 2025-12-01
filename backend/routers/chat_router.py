"""Chat/Q&A router for RAG agent"""
from fastapi import APIRouter, HTTPException, Depends

from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import Optional, AsyncGenerator
import os
import json
import asyncio
from dotenv import load_dotenv

from Agent.rag_agent.react_agent import PolicyRAGAgent
from backend.database import User
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
    thread_id: Optional[str] = "default"


class ChatResponse(BaseModel):
    answer: str
    citations: list
    confidence: float
    status: str


async def generate_stream(question: str, thread_id: str) -> AsyncGenerator[str, None]:
    """
    Generate SSE stream for chat response
    
    Yields SSE formatted events with:
    - content chunks (token-by-token)
    - citations (when available)
    - final metadata (confidence, status)
    """
    try:
        rag_agent = get_agent()
        
        # Stream the response
        async for chunk in rag_agent.query_stream(question, thread_id):
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
async def chat_query_stream(request: ChatRequest):
    """
    Ask a question to the RAG agent with streaming response (SSE)
    
    Args:
        question: The question to ask
        thread_id: Optional thread ID for conversation memory
    
    Returns:
        Server-Sent Events stream with:
        - content: Token chunks as they're generated
        - citation: Citations as they're discovered
        - metadata: Final confidence and status
        - done: Stream completion signal
    """
    return StreamingResponse(
        generate_stream(request.question, request.thread_id),
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
    current_user: User = Depends(get_current_user)
):
    """
    Ask a question to the RAG agent (non-streaming, backward compatible)
    
    Args:
        question: The question to ask
        thread_id: Optional thread ID for conversation memory
    
    Returns:
        Answer with citations and confidence score
    
    Requires authentication - all authenticated users can query
    """
    try:
        rag_agent = get_agent()
        result = rag_agent.query(request.question, request.thread_id)
        
        return ChatResponse(**result)
        
    except Exception as e:
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
