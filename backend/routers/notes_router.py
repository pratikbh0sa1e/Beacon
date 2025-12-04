from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from backend.database import SessionLocal, UserNote, User, Document
from backend.routers.auth_router import get_current_user

router = APIRouter(prefix="/api/notes", tags=["notes"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Pydantic Models
class NoteCreate(BaseModel):
    document_id: Optional[int] = None
    title: Optional[str] = None
    content: str
    tags: Optional[List[str]] = None
    color: Optional[str] = None


class NoteUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    tags: Optional[List[str]] = None
    is_pinned: Optional[bool] = None
    color: Optional[str] = None


class NoteResponse(BaseModel):
    id: int
    user_id: int
    document_id: Optional[int]
    title: Optional[str]
    content: str
    tags: Optional[List[str]]
    is_pinned: bool
    color: Optional[str]
    created_at: datetime
    updated_at: datetime
    document_title: Optional[str] = None

    class Config:
        from_attributes = True


# ✅ Create a new note
@router.post("/", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
def create_note(
    note_data: NoteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new personal note"""
    
    # Validate document exists if document_id provided
    if note_data.document_id:
        document = db.query(Document).filter(Document.id == note_data.document_id).first()
        if not document:
            raise HTTPException(status_code=404, detail="Document not found")
    
    # Create note
    new_note = UserNote(
        user_id=current_user.id,
        document_id=note_data.document_id,
        title=note_data.title,
        content=note_data.content,
        tags=note_data.tags,
        color=note_data.color
    )
    
    db.add(new_note)
    db.commit()
    db.refresh(new_note)
    
    # Add document title if linked
    response = NoteResponse.from_orm(new_note)
    if new_note.document_id:
        document = db.query(Document).filter(Document.id == new_note.document_id).first()
        response.document_title = document.title if document else None
    
    return response


# ✅ Get all notes for current user
@router.get("/", response_model=List[NoteResponse])
def get_my_notes(
    document_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all notes for the current user, optionally filtered by document"""
    
    query = db.query(UserNote).filter(UserNote.user_id == current_user.id)
    
    # Filter by document if provided
    if document_id:
        query = query.filter(UserNote.document_id == document_id)
    
    # Search in title and content
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (UserNote.title.ilike(search_pattern)) |
            (UserNote.content.ilike(search_pattern))
        )
    
    # Order by pinned first, then by updated date
    notes = query.order_by(UserNote.is_pinned.desc(), UserNote.updated_at.desc()).all()
    
    # Add document titles
    result = []
    for note in notes:
        note_response = NoteResponse.from_orm(note)
        if note.document_id:
            document = db.query(Document).filter(Document.id == note.document_id).first()
            note_response.document_title = document.title if document else None
        result.append(note_response)
    
    return result


# ✅ Get a specific note
@router.get("/{note_id}", response_model=NoteResponse)
def get_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific note by ID"""
    
    note = db.query(UserNote).filter(
        UserNote.id == note_id,
        UserNote.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    response = NoteResponse.from_orm(note)
    if note.document_id:
        document = db.query(Document).filter(Document.id == note.document_id).first()
        response.document_title = document.title if document else None
    
    return response


# ✅ Update a note
@router.put("/{note_id}", response_model=NoteResponse)
def update_note(
    note_id: int,
    note_data: NoteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing note"""
    
    note = db.query(UserNote).filter(
        UserNote.id == note_id,
        UserNote.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    # Update fields
    if note_data.title is not None:
        note.title = note_data.title
    if note_data.content is not None:
        note.content = note_data.content
    if note_data.tags is not None:
        note.tags = note_data.tags
    if note_data.is_pinned is not None:
        note.is_pinned = note_data.is_pinned
    if note_data.color is not None:
        note.color = note_data.color
    
    note.updated_at = datetime.utcnow()
    
    db.commit()
    db.refresh(note)
    
    response = NoteResponse.from_orm(note)
    if note.document_id:
        document = db.query(Document).filter(Document.id == note.document_id).first()
        response.document_title = document.title if document else None
    
    return response


# ✅ Delete a note
@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_note(
    note_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a note"""
    
    note = db.query(UserNote).filter(
        UserNote.id == note_id,
        UserNote.user_id == current_user.id
    ).first()
    
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    
    db.delete(note)
    db.commit()
    
    return None


# ✅ Get notes statistics
@router.get("/stats/summary")
def get_notes_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get statistics about user's notes"""
    
    total_notes = db.query(UserNote).filter(UserNote.user_id == current_user.id).count()
    
    document_notes = db.query(UserNote).filter(
        UserNote.user_id == current_user.id,
        UserNote.document_id.isnot(None)
    ).count()
    
    standalone_notes = total_notes - document_notes
    
    pinned_notes = db.query(UserNote).filter(
        UserNote.user_id == current_user.id,
        UserNote.is_pinned == True
    ).count()
    
    return {
        "total_notes": total_notes,
        "document_notes": document_notes,
        "standalone_notes": standalone_notes,
        "pinned_notes": pinned_notes
    }
