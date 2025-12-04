"""Document-specific collaboration chat with real-time messaging"""
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session
from sqlalchemy import and_, desc
from datetime import datetime, timedelta
from typing import Optional, List, AsyncGenerator
import asyncio
import json
import re
import os
from dotenv import load_dotenv

from backend.database import (
    User, Document, DocumentChatMessage, DocumentChatParticipant,
    Notification, get_db
)
from backend.routers.auth_router import get_current_user, decode_token

load_dotenv()

router = APIRouter(prefix="/documents/{document_id}/chat", tags=["document-chat"])

# Global SSE connections manager
active_connections = {}  # {document_id: {user_id: queue}}

# Initialize RAG agent (lazy loading)
rag_agent = None

def get_rag_agent():
    global rag_agent
    if rag_agent is None:
        from Agent.rag_agent.react_agent import PolicyRAGAgent
        google_api_key = os.getenv("GOOGLE_API_KEY")
        if not google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in environment")
        rag_agent = PolicyRAGAgent(google_api_key=google_api_key, temperature=0.1)
    return rag_agent


class SendMessageRequest(BaseModel):
    content: str
    parent_message_id: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    document_id: int
    user_id: Optional[int]
    user_name: Optional[str]
    content: str
    message_type: str
    parent_message_id: Optional[int]
    citations: Optional[list]
    mentioned_user_ids: Optional[List[int]]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ParticipantResponse(BaseModel):
    user_id: int
    user_name: str
    user_email: str
    is_active: bool
    last_seen: datetime


def check_document_access(document_id: int, user: User, db: Session) -> Document:
    """Verify user has access to document"""
    document = db.query(Document).filter(Document.id == document_id).first()
    
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")
    
    user_role = user.role
    user_institution_id = user.institution_id
    
    if user_role in ["developer", "ministry_admin"]:
        return document
    
    if document.approval_status not in ["approved", "restricted_approved"]:
        if document.uploader_id != user.id and user_role not in ["university_admin", "document_officer"]:
            raise HTTPException(status_code=403, detail="Document not approved for viewing")
    
    if document.visibility_level == "public":
        return document
    elif document.visibility_level == "institution_only":
        if document.institution_id != user_institution_id:
            raise HTTPException(status_code=403, detail="Document restricted to institution members")
    elif document.visibility_level in ["restricted", "confidential"]:
        if user_role not in ["developer", "ministry_admin", "university_admin", "document_officer"]:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
    
    return document


def parse_mentions(content: str, db: Session) -> List[int]:
    """Parse @mentions from message content"""
    mention_pattern = r'@(\w+(?:\.\w+)*@[\w.-]+|\w+)'
    matches = re.findall(mention_pattern, content)
    
    if not matches:
        return []
    
    user_ids = []
    for match in matches:
        if '@' in match:
            user = db.query(User).filter(User.email == match).first()
        else:
            user = db.query(User).filter(User.name.ilike(match)).first()
        
        if user and user.id not in user_ids:
            user_ids.append(user.id)
    
    return user_ids


async def broadcast_message(document_id: int, message_data: dict):
    """Broadcast message to all connected users"""
    if document_id in active_connections:
        for user_id, queue in active_connections[document_id].items():
            try:
                await queue.put(message_data)
            except:
                pass


@router.post("/messages", response_model=MessageResponse)
async def send_message(
    document_id: int,
    request: SendMessageRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Send a message to document chat"""
    document = check_document_access(document_id, current_user, db)
    
    if not request.content or not request.content.strip():
        raise HTTPException(status_code=400, detail="Message content cannot be empty")
    
    # Check for @beacon invocation
    beacon_pattern = r'@beacon\s+(.+)'
    beacon_match = re.search(beacon_pattern, request.content, re.IGNORECASE)
    
    if beacon_match:
        query = beacon_match.group(1).strip()
        
        # Save user message
        user_message = DocumentChatMessage(
            document_id=document_id,
            user_id=current_user.id,
            content=request.content,
            parent_message_id=request.parent_message_id,
            message_type="user"
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # Broadcast user message
        await broadcast_message(document_id, {
            "type": "message",
            "data": {
                "id": user_message.id,
                "document_id": document_id,
                "user_id": current_user.id,
                "user_name": current_user.name,
                "content": request.content,
                "message_type": "user",
                "parent_message_id": request.parent_message_id,
                "created_at": user_message.created_at.isoformat()
            }
        })
        
        # Broadcast thinking status
        await broadcast_message(document_id, {
            "type": "beacon_thinking",
            "data": {"message": "Beacon is analyzing the document..."}
        })
        
        # Invoke RAG agent
        try:
            from Agent.tools.document_specific_search import search_within_document
            
            search_results = search_within_document(
                document_id=document_id,
                query=query,
                user_role=current_user.role,
                user_institution_id=current_user.institution_id,
                top_k=5
            )
            
            agent = get_rag_agent()
            result = agent.query(
                f"Based on the following information from document '{document.filename}':\n\n{search_results}\n\nQuestion: {query}",
                thread_id=f"doc_{document_id}",
                user_role=current_user.role,
                user_institution_id=current_user.institution_id
            )
            
            beacon_message = DocumentChatMessage(
                document_id=document_id,
                user_id=None,
                content=result["answer"],
                parent_message_id=user_message.id,
                message_type="beacon",
                citations=result.get("citations", [])
            )
            db.add(beacon_message)
            db.commit()
            db.refresh(beacon_message)
            
            await broadcast_message(document_id, {
                "type": "message",
                "data": {
                    "id": beacon_message.id,
                    "document_id": document_id,
                    "user_id": None,
                    "user_name": "Beacon AI",
                    "content": result["answer"],
                    "message_type": "beacon",
                    "parent_message_id": user_message.id,
                    "citations": result.get("citations", []),
                    "created_at": beacon_message.created_at.isoformat()
                }
            })
            
            return MessageResponse(
                id=beacon_message.id,
                document_id=document_id,
                user_id=None,
                user_name="Beacon AI",
                content=result["answer"],
                message_type="beacon",
                parent_message_id=user_message.id,
                citations=result.get("citations", []),
                mentioned_user_ids=None,
                created_at=beacon_message.created_at
            )
            
        except Exception as e:
            await broadcast_message(document_id, {
                "type": "beacon_error",
                "data": {"message": f"Beacon encountered an error: {str(e)}"}
            })
            raise HTTPException(status_code=500, detail=f"Beacon error: {str(e)}")
    
    # Regular message
    mentioned_user_ids = parse_mentions(request.content, db)
    
    message = DocumentChatMessage(
        document_id=document_id,
        user_id=current_user.id,
        content=request.content,
        parent_message_id=request.parent_message_id,
        message_type="user",
        mentioned_user_ids=mentioned_user_ids if mentioned_user_ids else None
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Create notifications for mentions
    if mentioned_user_ids:
        for mentioned_user_id in mentioned_user_ids:
            mentioned_user = db.query(User).filter(User.id == mentioned_user_id).first()
            if mentioned_user:
                try:
                    check_document_access(document_id, mentioned_user, db)
                    
                    notification = Notification(
                        user_id=mentioned_user_id,
                        title=f"{current_user.name} mentioned you in {document.filename}",
                        message=request.content[:200],
                        type="document_chat_mention",
                        priority="medium",
                        action_url=f"/documents/{document_id}?message={message.id}",
                        action_label="View Message",
                        action_metadata={"document_id": document_id, "message_id": message.id}
                    )
                    db.add(notification)
                except:
                    pass
        
        db.commit()
    
    await broadcast_message(document_id, {
        "type": "message",
        "data": {
            "id": message.id,
            "document_id": document_id,
            "user_id": current_user.id,
            "user_name": current_user.name,
            "content": request.content,
            "message_type": "user",
            "parent_message_id": request.parent_message_id,
            "mentioned_user_ids": mentioned_user_ids,
            "created_at": message.created_at.isoformat()
        }
    })
    
    return MessageResponse(
        id=message.id,
        document_id=document_id,
        user_id=current_user.id,
        user_name=current_user.name,
        content=request.content,
        message_type="user",
        parent_message_id=request.parent_message_id,
        citations=None,
        mentioned_user_ids=mentioned_user_ids,
        created_at=message.created_at
    )


@router.get("/messages", response_model=List[MessageResponse])
async def get_messages(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    before_id: Optional[int] = None
):
    """Get chat messages for a document"""
    check_document_access(document_id, current_user, db)
    
    query = db.query(DocumentChatMessage).filter(
        DocumentChatMessage.document_id == document_id
    )
    
    if before_id:
        query = query.filter(DocumentChatMessage.id < before_id)
    
    messages = query.order_by(desc(DocumentChatMessage.created_at)).offset(offset).limit(limit).all()
    messages.reverse()
    
    response = []
    for msg in messages:
        user_name = None
        if msg.user_id:
            user = db.query(User).filter(User.id == msg.user_id).first()
            user_name = user.name if user else "Unknown User"
        elif msg.message_type == "beacon":
            user_name = "Beacon AI"
        else:
            user_name = "System"
        
        response.append(MessageResponse(
            id=msg.id,
            document_id=msg.document_id,
            user_id=msg.user_id,
            user_name=user_name,
            content=msg.content,
            message_type=msg.message_type,
            parent_message_id=msg.parent_message_id,
            citations=msg.citations,
            mentioned_user_ids=msg.mentioned_user_ids,
            created_at=msg.created_at
        ))
    
    return response


@router.get("/stream")
async def stream_messages(
    document_id: int,
    token: str = Query(..., description="JWT token"),
    db: Session = Depends(get_db)
):
    """SSE endpoint for real-time updates"""
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        current_user = db.query(User).filter(User.id == user_id).first()
        if not current_user:
            raise HTTPException(status_code=404, detail="User not found")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Authentication failed: {str(e)}")
    
    check_document_access(document_id, current_user, db)
    
    message_queue = asyncio.Queue()
    
    if document_id not in active_connections:
        active_connections[document_id] = {}
    active_connections[document_id][current_user.id] = message_queue
    
    participant = db.query(DocumentChatParticipant).filter(
        and_(
            DocumentChatParticipant.document_id == document_id,
            DocumentChatParticipant.user_id == current_user.id
        )
    ).first()
    
    if participant:
        participant.is_active = True
        participant.last_seen = datetime.utcnow()
    else:
        participant = DocumentChatParticipant(
            document_id=document_id,
            user_id=current_user.id,
            is_active=True
        )
        db.add(participant)
    
    db.commit()
    
    await broadcast_message(document_id, {
        "type": "participant_joined",
        "data": {
            "user_id": current_user.id,
            "user_name": current_user.name
        }
    })
    
    async def event_generator():
        try:
            yield f"data: {json.dumps({'type': 'connected', 'data': {'user_id': current_user.id}})}\n\n"
            
            while True:
                message = await message_queue.get()
                yield f"data: {json.dumps(message)}\n\n"
                
        except asyncio.CancelledError:
            pass
        finally:
            if document_id in active_connections and current_user.id in active_connections[document_id]:
                del active_connections[document_id][current_user.id]
                if not active_connections[document_id]:
                    del active_connections[document_id]
            
            db_session = next(get_db())
            try:
                participant = db_session.query(DocumentChatParticipant).filter(
                    and_(
                        DocumentChatParticipant.document_id == document_id,
                        DocumentChatParticipant.user_id == current_user.id
                    )
                ).first()
                
                if participant:
                    participant.is_active = False
                    participant.last_seen = datetime.utcnow()
                    db_session.commit()
                
                await broadcast_message(document_id, {
                    "type": "participant_left",
                    "data": {
                        "user_id": current_user.id,
                        "user_name": current_user.name
                    }
                })
            finally:
                db_session.close()
    
    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.get("/participants", response_model=List[ParticipantResponse])
async def get_participants(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of active participants"""
    check_document_access(document_id, current_user, db)
    
    cutoff_time = datetime.utcnow() - timedelta(minutes=10)
    
    participants = db.query(DocumentChatParticipant).filter(
        and_(
            DocumentChatParticipant.document_id == document_id,
            DocumentChatParticipant.last_seen >= cutoff_time
        )
    ).all()
    
    response = []
    for p in participants:
        user = db.query(User).filter(User.id == p.user_id).first()
        if user:
            response.append(ParticipantResponse(
                user_id=user.id,
                user_name=user.name,
                user_email=user.email,
                is_active=p.is_active,
                last_seen=p.last_seen
            ))
    
    return response


@router.get("/search-users")
async def search_users_for_mention(
    document_id: int,
    query: str = Query(..., min_length=1),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search users for @mention autocomplete"""
    document = check_document_access(document_id, current_user, db)
    
    from sqlalchemy import or_
    users = db.query(User).filter(
        or_(
            User.name.ilike(f"%{query}%"),
            User.email.ilike(f"%{query}%")
        )
    ).limit(10).all()
    
    accessible_users = []
    for user in users:
        try:
            check_document_access(document_id, user, db)
            accessible_users.append({
                "id": user.id,
                "name": user.name,
                "email": user.email
            })
        except:
            pass
    
    return accessible_users
