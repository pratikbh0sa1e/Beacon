"""
Notification Hierarchy Helper
Implements Option 2 notification routing:
- Students → University Admin (primary), Developer (copy)
- Document Officers → University Admin (primary), Developer (copy)
- University Admin → MoE Admin ONLY if document is escalated
- MoE Admin → Developer only
"""

from sqlalchemy.orm import Session
from backend.database import Notification, User
from datetime import datetime
from typing import Optional, Dict, Any


def send_hierarchical_notification(
    db: Session,
    sender: User,
    notification_type: str,
    title: str,
    message: str,
    action_url: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None,
    priority: str = "medium",
    document_escalated: bool = False
):
    """
    Send notifications following the hierarchy rules
    
    Args:
        db: Database session
        sender: User who triggered the notification
        notification_type: Type of notification (document_upload, approval_request, etc.)
        title: Notification title
        message: Notification message
        action_url: Optional URL for action button
        metadata: Optional metadata dict
        priority: Notification priority (low, medium, high)
        document_escalated: Whether document requires MoE approval
    """
    notifications_created = []
    
    # Rule 1: Students → University Admin (primary), Developer (copy)
    if sender.role == "student":
        # Send to University Admin from same institution
        if sender.institution_id:
            uni_admins = db.query(User).filter(
                User.role == "university_admin",
                User.institution_id == sender.institution_id
            ).all()
            
            for admin in uni_admins:
                notif = Notification(
                    user_id=admin.id,
                    type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    action_url=action_url,
                    action_metadata=metadata or {}
                )
                db.add(notif)
                notifications_created.append(notif)
        
        # Copy to Developer
        developers = db.query(User).filter(User.role == "developer").all()
        for dev in developers:
            notif = Notification(
                user_id=dev.id,
                type=notification_type,
                title=f"[Copy] {title}",
                message=message,
                priority="low",
                action_url=action_url,
                action_metadata=metadata or {}
            )
            db.add(notif)
            notifications_created.append(notif)
    
    # Rule 2: Document Officers → University Admin (primary), Developer (copy)
    elif sender.role == "document_officer":
        # Send to University Admin from same institution
        if sender.institution_id:
            uni_admins = db.query(User).filter(
                User.role == "university_admin",
                User.institution_id == sender.institution_id
            ).all()
            
            for admin in uni_admins:
                notif = Notification(
                    user_id=admin.id,
                    type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    action_url=action_url,
                    action_metadata=metadata or {}
                )
                db.add(notif)
                notifications_created.append(notif)
        
        # Copy to Developer
        developers = db.query(User).filter(User.role == "developer").all()
        for dev in developers:
            notif = Notification(
                user_id=dev.id,
                type=notification_type,
                title=f"[Copy] {title}",
                message=message,
                priority="low",
                action_url=action_url,
                action_metadata=metadata or {}
            )
            db.add(notif)
            notifications_created.append(notif)
    
    # Rule 3: University Admin → Ministry Admin ONLY if document is escalated
    elif sender.role == "university_admin":
        if document_escalated:
            # Send to Ministry Admin
            ministry_admins = db.query(User).filter(User.role == "ministry_admin").all()
            for ministry_admin in ministry_admins:
                notif = Notification(
                    user_id=ministry_admin.id,
                    type=notification_type,
                    title=title,
                    message=message,
                    priority=priority,
                    action_url=action_url,
                    action_metadata=metadata or {}
                )
                db.add(notif)
                notifications_created.append(notif)
        
        # Always copy to Developer
        developers = db.query(User).filter(User.role == "developer").all()
        for dev in developers:
            notif = Notification(
                user_id=dev.id,
                type=notification_type,
                title=f"[Copy] {title}",
                message=message,
                priority="low",
                action_url=action_url,
                action_metadata=metadata or {}
            )
            db.add(notif)
            notifications_created.append(notif)
    
    # Rule 4: Ministry Admin → Developer only
    elif sender.role == "ministry_admin":
        developers = db.query(User).filter(User.role == "developer").all()
        for dev in developers:
            notif = Notification(
                user_id=dev.id,
                type=notification_type,
                title=title,
                message=message,
                priority=priority,
                action_url=action_url,
                action_metadata=metadata or {}
            )
            db.add(notif)
            notifications_created.append(notif)
    
    # Rule 5: Developer → No escalations required (but can send to anyone if needed)
    elif sender.role == "developer":
        # Developers can send notifications but don't follow hierarchy
        # This is handled separately in specific endpoints
        pass
    
    db.commit()
    return notifications_created


def notify_document_upload(
    db: Session,
    uploader: User,
    document_id: int,
    document_title: str
):
    """Notify about new document upload"""
    return send_hierarchical_notification(
        db=db,
        sender=uploader,
        notification_type="document_upload",
        title="New Document Uploaded",
        message=f"{uploader.name} uploaded a new document: {document_title}",
        action_url=f"/documents/{document_id}",
        metadata={"document_id": document_id, "uploader_id": uploader.id},
        priority="medium"
    )


def notify_approval_request(
    db: Session,
    requester: User,
    document_id: int,
    document_title: str
):
    """Notify about approval request (escalated to MoE)"""
    return send_hierarchical_notification(
        db=db,
        sender=requester,
        notification_type="approval_request",
        title="Document Approval Requested",
        message=f"{requester.name} submitted '{document_title}' for approval",
        action_url=f"/approvals/{document_id}",
        metadata={"document_id": document_id, "requester_id": requester.id},
        priority="high",
        document_escalated=True
    )


def notify_document_approved(
    db: Session,
    approver: User,
    uploader_id: int,
    document_id: int,
    document_title: str
):
    """Notify uploader that document was approved"""
    notif = Notification(
        user_id=uploader_id,
        type="document_approved",
        title="Document Approved",
        message=f"Your document '{document_title}' has been approved by {approver.name}",
        priority="high",
        action_url=f"/documents/{document_id}",
        action_metadata={"document_id": document_id, "approved_by": approver.id}
    )
    db.add(notif)
    db.commit()
    return notif


def notify_document_rejected(
    db: Session,
    rejector: User,
    uploader_id: int,
    document_id: int,
    document_title: str,
    reason: str
):
    """Notify uploader that document was rejected"""
    notif = Notification(
        user_id=uploader_id,
        type="document_rejected",
        title="Document Rejected",
        message=f"Your document '{document_title}' was rejected by {rejector.name}. Reason: {reason}",
        priority="high",
        action_url=f"/documents/{document_id}",
        action_metadata={"document_id": document_id, "rejected_by": rejector.id, "reason": reason}
    )
    db.add(notif)
    db.commit()
    return notif


def notify_changes_requested(
    db: Session,
    requester: User,
    uploader_id: int,
    document_id: int,
    document_title: str,
    changes: str
):
    """Notify uploader that changes were requested"""
    notif = Notification(
        user_id=uploader_id,
        type="changes_requested",
        title="Changes Requested",
        message=f"Changes requested for '{document_title}' by {requester.name}: {changes}",
        priority="high",
        action_url=f"/documents/{document_id}",
        action_metadata={"document_id": document_id, "requested_by": requester.id}
    )
    db.add(notif)
    db.commit()
    return notif

