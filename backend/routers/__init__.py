# Routers package
from . import (
    auth_router,
    user_router,
    institution_router,
    institution_domain_router,
    document_router,
    bookmark_router,
    approval_router,
    chat_router,
    chat_history_router,
    audit_router,
    data_source_router,
    notification_router,
    voice_router,
    insights_router
)

__all__ = [
    "auth_router",
    "user_router",
    "institution_router",
    "institution_domain_router",
    "document_router",
    "bookmark_router",
    "approval_router",
    "chat_router",
    "chat_history_router",
    "audit_router",
    "data_source_router",
    "notification_router",
    "voice_router",
    "insights_router"
]
