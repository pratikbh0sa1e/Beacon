"""
Progress Manager for tracking document processing operations
"""
import logging
from typing import Dict, Any, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class ProgressState:
    """Progress state for an operation"""
    session_id: str
    operation_type: str  # 'scraping' | 'analysis'
    current: int
    total: int
    status: str  # 'idle' | 'in_progress' | 'complete' | 'error'
    message: str = ""
    current_item: str = ""
    started_at: str = ""
    updated_at: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ProgressManager:
    """Manages progress tracking for scraping and analysis operations"""
    
    def __init__(self):
        self.active_sessions: Dict[str, ProgressState] = {}
        self.callbacks: Dict[str, Callable] = {}
    
    def start_operation(
        self,
        session_id: str,
        operation_type: str,
        total: int,
        message: str = ""
    ) -> ProgressState:
        """Initialize progress tracking for an operation"""
        now = datetime.utcnow().isoformat()
        
        state = ProgressState(
            session_id=session_id,
            operation_type=operation_type,
            current=0,
            total=total,
            status='in_progress',
            message=message,
            started_at=now,
            updated_at=now
        )
        
        self.active_sessions[session_id] = state
        self._emit_progress(session_id)
        
        logger.info(f"Started {operation_type} operation: {session_id} (total: {total})")
        return state
    
    def update_progress(
        self,
        session_id: str,
        current: int,
        message: str = "",
        current_item: str = ""
    ):
        """Update progress for an operation"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session not found: {session_id}")
            return
        
        state = self.active_sessions[session_id]
        state.current = current
        state.message = message
        state.current_item = current_item
        state.updated_at = datetime.utcnow().isoformat()
        
        self._emit_progress(session_id)
    
    def increment_progress(
        self,
        session_id: str,
        message: str = "",
        current_item: str = ""
    ):
        """Increment progress by 1"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session not found: {session_id}")
            return
        
        state = self.active_sessions[session_id]
        state.current += 1
        state.message = message
        state.current_item = current_item
        state.updated_at = datetime.utcnow().isoformat()
        
        self._emit_progress(session_id)
    
    def complete_operation(
        self,
        session_id: str,
        message: str = "Operation complete"
    ):
        """Mark operation as complete"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session not found: {session_id}")
            return
        
        state = self.active_sessions[session_id]
        state.status = 'complete'
        state.message = message
        state.updated_at = datetime.utcnow().isoformat()
        
        self._emit_progress(session_id)
        
        logger.info(f"Completed operation: {session_id}")
    
    def error_operation(
        self,
        session_id: str,
        error_message: str
    ):
        """Mark operation as error"""
        if session_id not in self.active_sessions:
            logger.warning(f"Session not found: {session_id}")
            return
        
        state = self.active_sessions[session_id]
        state.status = 'error'
        state.message = error_message
        state.updated_at = datetime.utcnow().isoformat()
        
        self._emit_progress(session_id)
        
        logger.error(f"Operation error: {session_id} - {error_message}")
    
    def get_progress(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get current progress state"""
        state = self.active_sessions.get(session_id)
        return state.to_dict() if state else None
    
    def register_callback(self, session_id: str, callback: Callable):
        """Register a callback for progress updates"""
        self.callbacks[session_id] = callback
    
    def _emit_progress(self, session_id: str):
        """Emit progress update via callback"""
        if session_id in self.callbacks:
            state = self.active_sessions[session_id]
            try:
                self.callbacks[session_id](state.to_dict())
            except Exception as e:
                logger.error(f"Callback error for {session_id}: {str(e)}")
    
    def cleanup_session(self, session_id: str):
        """Remove session from tracking"""
        if session_id in self.active_sessions:
            del self.active_sessions[session_id]
        if session_id in self.callbacks:
            del self.callbacks[session_id]


# Global progress manager instance
_progress_manager = None


def get_progress_manager() -> ProgressManager:
    """Get or create global progress manager"""
    global _progress_manager
    if _progress_manager is None:
        _progress_manager = ProgressManager()
    return _progress_manager
