"""Chat/Q&A router for RAG agent"""
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import os
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


@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Ask a question to the RAG agent
    
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
