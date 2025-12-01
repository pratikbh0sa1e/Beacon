from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.database import get_db, Bookmark, Document, User
from backend.routers.auth_router import get_current_user

router = APIRouter(tags=["bookmarks"])

@router.post("/toggle/{document_id}")
async def toggle_bookmark(
    document_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Toggle bookmark status for a document"""
    # Check if document exists
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")

    # Check if already bookmarked
    existing = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.document_id == document_id
    ).first()

    if existing:
        db.delete(existing)
        db.commit()
        return {"status": "removed", "message": "Bookmark removed"}
    else:
        new_bookmark = Bookmark(user_id=current_user.id, document_id=document_id)
        db.add(new_bookmark)
        db.commit()
        return {"status": "added", "message": "Bookmark added"}

@router.get("/list")
async def list_bookmarks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all bookmarked document IDs for current user"""
    bookmarks = db.query(Bookmark).filter(Bookmark.user_id == current_user.id).all()
    # Return list of document IDs
    return [b.document_id for b in bookmarks]