"""
Session management service
"""

import uuid
import asyncio
import time
from typing import Dict, Optional, Any
import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages chat sessions"""
    
    def __init__(self):
        self.sessions: Dict[str, Dict[str, Any]] = {}
        self.max_sessions = 100
        self.session_timeout = 3600  # 1 hour
        self._cleanup_task = None
    
    async def start_cleanup_task(self):
        """Start background cleanup task (called from startup event)"""
        if self._cleanup_task is None or self._cleanup_task.done():
            self._cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())
    
    async def _cleanup_expired_sessions(self):
        """Background task to cleanup expired sessions"""
        while True:
            try:
                await asyncio.sleep(300)  # Check every 5 minutes
                await self._remove_expired_sessions()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Session cleanup error: {e}")
    
    async def _remove_expired_sessions(self):
        """Remove expired sessions"""
        current_time = time.time()
        expired_sessions = []
        
        for session_id, session_data in self.sessions.items():
            last_activity = session_data.get("last_activity", 0)
            if current_time - last_activity > self.session_timeout:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            await self.end_session(session_id)
            logger.info(f"🗑️ Cleaned up expired session: {session_id}")
    
    async def create_session(self, config_override: Optional[Dict[str, Any]] = None) -> str:
        """Create a new session"""
        # Check session limit
        if len(self.sessions) >= self.max_sessions:
            # Try to clean up expired sessions first
            await self._remove_expired_sessions()
            
            if len(self.sessions) >= self.max_sessions:
                raise Exception("Maximum number of sessions reached")
        
        session_id = str(uuid.uuid4())
        current_time = time.time()
        
        session_data = {
            "session_id": session_id,
            "created_at": current_time,
            "last_activity": current_time,
            "status": "created",
            "config_override": config_override or {},
            "message_count": 0,
            "conversation_history": []
        }
        
        self.sessions[session_id] = session_data
        logger.info(f"📋 Created session {session_id}")
        
        return session_id
    
    async def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session information"""
        if session_id not in self.sessions:
            return None
        
        # Update last activity
        self.sessions[session_id]["last_activity"] = time.time()
        return self.sessions[session_id].copy()
    
    async def update_session_activity(self, session_id: str):
        """Update session last activity timestamp"""
        if session_id in self.sessions:
            self.sessions[session_id]["last_activity"] = time.time()
    
    async def add_message_to_history(self, session_id: str, message_type: str, content: Dict[str, Any]):
        """Add a message to session conversation history"""
        if session_id not in self.sessions:
            return False
        
        message = {
            "timestamp": time.time(),
            "type": message_type,
            "content": content
        }
        
        self.sessions[session_id]["conversation_history"].append(message)
        self.sessions[session_id]["message_count"] += 1
        await self.update_session_activity(session_id)
        
        # Limit conversation history to last 50 messages
        if len(self.sessions[session_id]["conversation_history"]) > 50:
            self.sessions[session_id]["conversation_history"] = \
                self.sessions[session_id]["conversation_history"][-50:]
        
        return True
    
    async def get_conversation_history(self, session_id: str, limit: int = 20) -> list:
        """Get conversation history for a session"""
        if session_id not in self.sessions:
            return []
        
        history = self.sessions[session_id]["conversation_history"]
        return history[-limit:] if limit else history
    
    async def update_session_config(self, session_id: str, config_update: Dict[str, Any]) -> bool:
        """Update session configuration"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["config_override"].update(config_update)
        await self.update_session_activity(session_id)
        return True
    
    async def end_session(self, session_id: str) -> bool:
        """End a session"""
        if session_id not in self.sessions:
            return False
        
        self.sessions[session_id]["status"] = "ended"
        self.sessions[session_id]["ended_at"] = time.time()
        
        # Remove from active sessions after a delay to allow final cleanup
        await asyncio.sleep(1)
        del self.sessions[session_id]
        
        logger.info(f"🗑️ Ended session {session_id}")
        return True
    
    def get_active_session_count(self) -> int:
        """Get number of active sessions"""
        return len([s for s in self.sessions.values() if s.get("status") != "ended"])
    
    def get_session_stats(self) -> Dict[str, Any]:
        """Get session statistics"""
        total_sessions = len(self.sessions)
        active_sessions = self.get_active_session_count()
        
        if total_sessions > 0:
            avg_messages = sum(s.get("message_count", 0) for s in self.sessions.values()) / total_sessions
        else:
            avg_messages = 0
        
        return {
            "total_sessions": total_sessions,
            "active_sessions": active_sessions,
            "average_messages_per_session": round(avg_messages, 2),
            "max_sessions": self.max_sessions,
            "session_timeout": self.session_timeout
        }
    
    async def cleanup_all_sessions(self):
        """Cleanup all sessions on shutdown"""
        logger.info("🧹 Cleaning up all sessions...")
        
        # Cancel cleanup task
        if self._cleanup_task and not self._cleanup_task.done():
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        # End all sessions
        session_ids = list(self.sessions.keys())
        for session_id in session_ids:
            try:
                await self.end_session(session_id)
            except Exception as e:
                logger.error(f"Error ending session {session_id}: {e}")
        
        self.sessions.clear()
        logger.info(f"✅ Cleaned up {len(session_ids)} sessions")
