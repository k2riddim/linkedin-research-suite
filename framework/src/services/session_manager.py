"""
Centralized Session Manager for AI Browser Automation
Provides thread-safe session tracking, lifecycle management, and monitoring.
"""

import asyncio
import threading
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List, Set
from dataclasses import dataclass, field
from enum import Enum
import weakref
import uuid

from .ai_config import AIOperationType, get_ai_config

logger = logging.getLogger(__name__)


class SessionStatus(Enum):
    """Session status tracking."""
    CREATING = "creating"
    ACTIVE = "active"
    BUSY = "busy"
    IDLE = "idle"
    EXPIRED = "expired"
    ERROR = "error"
    CLEANUP = "cleanup"


@dataclass
class SessionMetadata:
    """Comprehensive session metadata for tracking and debugging."""
    session_id: str
    account_id: Optional[str] = None
    status: SessionStatus = SessionStatus.CREATING
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_activity: datetime = field(default_factory=datetime.utcnow)
    live_url: Optional[str] = None
    operation_type: AIOperationType = AIOperationType.BROWSER_AUTOMATION
    error_count: int = 0
    last_error: Optional[str] = None
    total_operations: int = 0
    browserbase_session_id: Optional[str] = None
    stagehand_server_url: str = "http://localhost:8081"
    tags: Set[str] = field(default_factory=set)
    
    def update_activity(self):
        """Update last activity timestamp."""
        self.last_activity = datetime.utcnow()
    
    def is_expired(self, max_idle_minutes: int = 30) -> bool:
        """Check if session has exceeded idle timeout."""
        idle_time = datetime.utcnow() - self.last_activity
        return idle_time > timedelta(minutes=max_idle_minutes)
    
    def increment_operation(self):
        """Increment operation counter and update activity."""
        self.total_operations += 1
        self.update_activity()
    
    def record_error(self, error_message: str):
        """Record an error occurrence."""
        self.error_count += 1
        self.last_error = error_message
        self.status = SessionStatus.ERROR
        self.update_activity()


class SessionManager:
    """Thread-safe centralized session manager for AI browser automation."""
    
    def __init__(self):
        self._sessions: Dict[str, SessionMetadata] = {}
        self._account_sessions: Dict[str, str] = {}  # account_id -> session_id mapping
        self._lock = threading.RLock()
        self._cleanup_task: Optional[asyncio.Task] = None
        self._ai_config = get_ai_config()
        self._stats = {
            'total_created': 0,
            'total_expired': 0,
            'total_errors': 0,
            'active_sessions': 0
        }
        
        # Start background cleanup
        self._start_cleanup_task()
        
        logger.info("SessionManager initialized with background cleanup")
    
    def _start_cleanup_task(self):
        """Start background cleanup task."""
        try:
            loop = asyncio.get_event_loop()
            if not loop.is_running():
                raise RuntimeError("No running event loop")
            self._cleanup_task = loop.create_task(self._background_cleanup())
        except RuntimeError:
            # No event loop running, cleanup will start when needed
            logger.info("No event loop running, cleanup task will start later")
    
    async def _background_cleanup(self):
        """Background task to clean up expired sessions."""
        while True:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                await self.cleanup_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in background cleanup: {e}")
    
    def create_session(self, account_id: Optional[str] = None, operation_type: AIOperationType = AIOperationType.BROWSER_AUTOMATION, **metadata) -> str:
        """Create a new session with thread-safe tracking."""
        with self._lock:
            session_id = str(uuid.uuid4())
            
            # Close existing session for account if any
            if account_id and account_id in self._account_sessions:
                old_session_id = self._account_sessions[account_id]
                logger.info(f"Closing existing session {old_session_id} for account {account_id}")
                self._mark_for_cleanup(old_session_id)
            
            # Create session metadata
            session_meta = SessionMetadata(
                session_id=session_id,
                account_id=account_id,
                operation_type=operation_type,
                **metadata
            )
            
            # Store session
            self._sessions[session_id] = session_meta
            if account_id:
                self._account_sessions[account_id] = session_id
            
            # Update statistics
            self._stats['total_created'] += 1
            self._stats['active_sessions'] = len([s for s in self._sessions.values() if s.status not in [SessionStatus.EXPIRED, SessionStatus.CLEANUP]])
            
            logger.info(f"Created session {session_id} for account {account_id}")
            return session_id
    
    def get_session(self, session_id: str) -> Optional[SessionMetadata]:
        """Get session metadata with thread safety."""
        with self._lock:
            return self._sessions.get(session_id)
    
    def get_session_by_account(self, account_id: str) -> Optional[SessionMetadata]:
        """Get active session for account."""
        with self._lock:
            session_id = self._account_sessions.get(account_id)
            if session_id:
                return self._sessions.get(session_id)
            return None
    
    def update_session(self, session_id: str, **updates) -> bool:
        """Update session metadata."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            for key, value in updates.items():
                if hasattr(session, key):
                    setattr(session, key, value)
            
            session.update_activity()
            logger.debug(f"Updated session {session_id}: {updates}")
            return True
    
    def set_session_status(self, session_id: str, status: SessionStatus) -> bool:
        """Set session status with validation."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            old_status = session.status
            session.status = status
            session.update_activity()
            
            logger.info(f"Session {session_id} status: {old_status.value} -> {status.value}")
            return True
    
    def increment_operation(self, session_id: str) -> bool:
        """Increment operation counter for session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            session.increment_operation()
            return True
    
    def record_error(self, session_id: str, error_message: str) -> bool:
        """Record error for session."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            session.record_error(error_message)
            self._stats['total_errors'] += 1
            
            logger.warning(f"Session {session_id} error: {error_message}")
            return True
    
    def _mark_for_cleanup(self, session_id: str):
        """Mark session for cleanup (internal method)."""
        session = self._sessions.get(session_id)
        if session:
            session.status = SessionStatus.CLEANUP
            # Remove from account mapping
            if session.account_id and session.account_id in self._account_sessions:
                if self._account_sessions[session.account_id] == session_id:
                    del self._account_sessions[session.account_id]
    
    def close_session(self, session_id: str) -> bool:
        """Mark session for closure."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return False
            
            self._mark_for_cleanup(session_id)
            logger.info(f"Marked session {session_id} for cleanup")
            return True
    
    def close_account_sessions(self, account_id: str) -> int:
        """Close all sessions for account."""
        with self._lock:
            closed_count = 0
            sessions_to_close = [
                session_id for session_id, session in self._sessions.items()
                if session.account_id == account_id and session.status not in [SessionStatus.EXPIRED, SessionStatus.CLEANUP]
            ]
            
            for session_id in sessions_to_close:
                if self.close_session(session_id):
                    closed_count += 1
            
            logger.info(f"Closed {closed_count} sessions for account {account_id}")
            return closed_count
    
    async def cleanup_expired_sessions(self, max_idle_minutes: int = 30) -> Dict[str, Any]:
        """Clean up expired sessions."""
        with self._lock:
            expired_sessions = []
            current_time = datetime.utcnow()
            
            for session_id, session in list(self._sessions.items()):
                # Check if session is expired
                if (session.is_expired(max_idle_minutes) or 
                    session.status in [SessionStatus.EXPIRED, SessionStatus.CLEANUP]):
                    expired_sessions.append(session_id)
            
            # Remove expired sessions
            cleanup_results = []
            for session_id in expired_sessions:
                session = self._sessions.pop(session_id, None)
                if session:
                    # Remove from account mapping
                    if session.account_id and session.account_id in self._account_sessions:
                        if self._account_sessions[session.account_id] == session_id:
                            del self._account_sessions[session.account_id]
                    
                    cleanup_results.append({
                        'session_id': session_id,
                        'account_id': session.account_id,
                        'live_url': session.live_url,
                        'browserbase_session_id': session.browserbase_session_id
                    })
            
            # Update statistics
            self._stats['total_expired'] += len(cleanup_results)
            self._stats['active_sessions'] = len([s for s in self._sessions.values() if s.status not in [SessionStatus.EXPIRED, SessionStatus.CLEANUP]])
            
            if cleanup_results:
                logger.info(f"Cleaned up {len(cleanup_results)} expired sessions")
            
            return {
                'cleaned_up': len(cleanup_results),
                'sessions': cleanup_results,
                'stats': self._stats.copy()
            }
    
    def get_active_sessions(self) -> List[SessionMetadata]:
        """Get all active sessions."""
        with self._lock:
            return [
                session for session in self._sessions.values()
                if session.status not in [SessionStatus.EXPIRED, SessionStatus.CLEANUP]
            ]
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics."""
        with self._lock:
            active_sessions = self.get_active_sessions()
            
            status_counts = {}
            for status in SessionStatus:
                status_counts[status.value] = len([s for s in active_sessions if s.status == status])
            
            return {
                'total_sessions': len(self._sessions),
                'active_sessions': len(active_sessions),
                'status_breakdown': status_counts,
                'lifetime_stats': self._stats.copy(),
                'oldest_session': min([s.created_at for s in active_sessions], default=None),
                'newest_session': max([s.created_at for s in active_sessions], default=None)
            }
    
    def validate_session(self, session_id: str) -> Dict[str, Any]:
        """Validate session status before AI operations."""
        with self._lock:
            session = self._sessions.get(session_id)
            if not session:
                return {
                    'valid': False,
                    'reason': 'Session not found',
                    'action': 'create_new_session'
                }
            
            if session.status == SessionStatus.ERROR:
                return {
                    'valid': False,
                    'reason': f'Session in error state: {session.last_error}',
                    'action': 'retry_or_recreate',
                    'error_count': session.error_count
                }
            
            if session.is_expired():
                return {
                    'valid': False,
                    'reason': 'Session expired due to inactivity',
                    'action': 'create_new_session'
                }
            
            if session.status in [SessionStatus.EXPIRED, SessionStatus.CLEANUP]:
                return {
                    'valid': False,
                    'reason': 'Session marked for cleanup',
                    'action': 'create_new_session'
                }
            
            return {
                'valid': True,
                'session': session,
                'status': session.status.value,
                'last_activity': session.last_activity,
                'operations_count': session.total_operations
            }
    
    def shutdown(self):
        """Shutdown session manager and cleanup resources."""
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
        
        with self._lock:
            session_count = len(self._sessions)
            self._sessions.clear()
            self._account_sessions.clear()
        
        logger.info(f"SessionManager shutdown - cleaned up {session_count} sessions")


# Global session manager instance
_session_manager: Optional[SessionManager] = None
_session_manager_lock = threading.Lock()


def get_session_manager() -> SessionManager:
    """Get the global session manager instance (thread-safe singleton)."""
    global _session_manager
    
    if _session_manager is None:
        with _session_manager_lock:
            if _session_manager is None:
                _session_manager = SessionManager()
    
    return _session_manager


def reset_session_manager():
    """Reset the global session manager (for testing)."""
    global _session_manager
    
    with _session_manager_lock:
        if _session_manager:
            _session_manager.shutdown()
        _session_manager = None