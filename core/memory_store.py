"""
Redis-based shared memory store for the multi-agent system.
Provides centralized storage for agent communications and audit trails.
"""
import json
import logging
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
import redis.asyncio as redis
from models.schemas import MemoryEntry, ProcessingSession, AgentDecision, ActionResult

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Centralized memory store using Redis for agent communication and audit trails.
    """
    
    def __init__(self, redis_url: str = "redis://localhost:6379/0"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.is_connected = False
        
    async def connect(self):
        """Establish Redis connection."""
        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            await self.redis_client.ping()
            self.is_connected = True
            logger.info("Connected to Redis memory store")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            self.is_connected = False
            raise
    
    async def disconnect(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()
            self.is_connected = False
            logger.info("Disconnected from Redis memory store")
    
    async def store_entry(self, entry: MemoryEntry) -> bool:
        """Store a memory entry."""
        try:
            key = f"memory:{entry.key}"
            value = {
                "value": entry.value,
                "entry_type": entry.entry_type,
                "agent_source": entry.agent_source,
                "timestamp": entry.timestamp.isoformat()
            }
            
            if entry.ttl_seconds:
                await self.redis_client.setex(key, entry.ttl_seconds, json.dumps(value))
            else:
                await self.redis_client.set(key, json.dumps(value))
            
            logger.debug(f"Stored memory entry: {entry.key}")
            return True
        except Exception as e:
            logger.error(f"Failed to store memory entry {entry.key}: {e}")
            return False
    
    async def get_entry(self, key: str) -> Optional[MemoryEntry]:
        """Retrieve a memory entry."""
        try:
            full_key = f"memory:{key}"
            data = await self.redis_client.get(full_key)
            if not data:
                return None
            
            parsed_data = json.loads(data)
            return MemoryEntry(
                key=key,
                value=parsed_data["value"],
                entry_type=parsed_data["entry_type"],
                agent_source=parsed_data["agent_source"],
                timestamp=datetime.fromisoformat(parsed_data["timestamp"])
            )
        except Exception as e:
            logger.error(f"Failed to get memory entry {key}: {e}")
            return None
    
    async def store_session(self, session: ProcessingSession) -> bool:
        """Store a complete processing session."""
        try:
            key = f"session:{session.session_id}"
            value = session.model_dump_json()
            await self.redis_client.setex(key, 86400, value)  # 24 hour TTL
            
            # Also store in session index
            await self.redis_client.zadd(
                "session_index", 
                {session.session_id: session.created_at.timestamp()}
            )
            
            logger.info(f"Stored processing session: {session.session_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store session {session.session_id}: {e}")
            return False
    
    async def get_session(self, session_id: str) -> Optional[ProcessingSession]:
        """Retrieve a processing session."""
        try:
            key = f"session:{session_id}"
            data = await self.redis_client.get(key)
            if not data:
                return None
            
            return ProcessingSession.model_validate_json(data)
        except Exception as e:
            logger.error(f"Failed to get session {session_id}: {e}")
            return None
    
    async def add_agent_decision(self, session_id: str, decision: AgentDecision) -> bool:
        """Add an agent decision to a session."""
        try:
            session = await self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            session.agent_decisions.append(decision)
            return await self.store_session(session)
        except Exception as e:
            logger.error(f"Failed to add agent decision to session {session_id}: {e}")
            return False
    
    async def add_action_result(self, session_id: str, action_result: ActionResult) -> bool:
        """Add an action result to a session."""
        try:
            session = await self.get_session(session_id)
            if not session:
                logger.error(f"Session {session_id} not found")
                return False
            
            session.actions_triggered.append(action_result)
            return await self.store_session(session)
        except Exception as e:
            logger.error(f"Failed to add action result to session {session_id}: {e}")
            return False
    
    async def get_recent_sessions(self, limit: int = 50) -> List[ProcessingSession]:
        """Get recent processing sessions."""
        try:
            # Get recent session IDs from sorted set
            session_ids = await self.redis_client.zrevrange("session_index", 0, limit-1)
            
            sessions = []
            for session_id in session_ids:
                session = await self.get_session(session_id)
                if session:
                    sessions.append(session)
            
            return sessions
        except Exception as e:
            logger.error(f"Failed to get recent sessions: {e}")
            return []
    
    async def store_agent_state(self, agent_name: str, state: Dict[str, Any]) -> bool:
        """Store agent state information."""
        try:
            key = f"agent_state:{agent_name}"
            value = {
                "state": state,
                "last_updated": datetime.utcnow().isoformat()
            }
            await self.redis_client.setex(key, 3600, json.dumps(value))  # 1 hour TTL
            return True
        except Exception as e:
            logger.error(f"Failed to store agent state for {agent_name}: {e}")
            return False
    
    async def get_agent_state(self, agent_name: str) -> Optional[Dict[str, Any]]:
        """Get agent state information."""
        try:
            key = f"agent_state:{agent_name}"
            data = await self.redis_client.get(key)
            if not data:
                return None
            
            parsed_data = json.loads(data)
            return parsed_data["state"]
        except Exception as e:
            logger.error(f"Failed to get agent state for {agent_name}: {e}")
            return None
    
    async def increment_counter(self, counter_name: str, increment: int = 1) -> int:
        """Increment a counter and return new value."""
        try:
            key = f"counter:{counter_name}"
            return await self.redis_client.incrby(key, increment)
        except Exception as e:
            logger.error(f"Failed to increment counter {counter_name}: {e}")
            return 0
    
    async def get_counter(self, counter_name: str) -> int:
        """Get counter value."""
        try:
            key = f"counter:{counter_name}"
            value = await self.redis_client.get(key)
            return int(value) if value else 0
        except Exception as e:
            logger.error(f"Failed to get counter {counter_name}: {e}")
            return 0
    
    async def cleanup_expired_entries(self):
        """Clean up expired entries (maintenance task)."""
        try:
            # This is handled automatically by Redis TTL, but we can add custom cleanup logic here
            logger.info("Memory store cleanup completed")
        except Exception as e:
            logger.error(f"Failed to cleanup expired entries: {e}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """Get system statistics from memory store."""
        try:
            stats = {
                "total_sessions": await self.redis_client.zcard("session_index"),
                "memory_usage": await self.redis_client.memory_usage("session_index") if hasattr(self.redis_client, 'memory_usage') else 0,
                "connected": self.is_connected,
                "redis_info": await self.redis_client.info() if self.is_connected else {}
            }
            
            # Get counter stats
            counter_keys = await self.redis_client.keys("counter:*")
            counters = {}
            for key in counter_keys:
                counter_name = key.replace("counter:", "")
                counters[counter_name] = await self.get_counter(counter_name)
            stats["counters"] = counters
            
            return stats
        except Exception as e:
            logger.error(f"Failed to get system stats: {e}")
            return {"error": str(e)}


# Global memory store instance
memory_store = MemoryStore()


async def get_memory_store() -> MemoryStore:
    """Get the global memory store instance."""
    if not memory_store.is_connected:
        await memory_store.connect()
    return memory_store
