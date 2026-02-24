"""
MemoryStore: Unified memory storage using telemetry DB.

Replaces file-based project_profile.json with SQLite-backed storage.
"""

import sqlite3
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
import uuid

logger = logging.getLogger(__name__)


class MemoryStore:
    """
    Unified memory storage backed by telemetry DB.
    
    Features:
    - Persistent context storage (active_context, memory_bank)
    - Historical snapshots for pattern analysis
    - Query interface for self-healing logic
    """
    
    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path.home() / ".swarm" / "telemetry.db"
        else:
            self.db_path = db_path
        
        self._ensure_schema()
    
    def _get_connection(self):
        return sqlite3.connect(str(self.db_path))
    
    def _ensure_schema(self):
        """Create memory_snapshots table if not exists."""
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        with self._get_connection() as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS memory_snapshots (
                    snapshot_id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    context_type TEXT NOT NULL,
                    data TEXT NOT NULL
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_session 
                ON memory_snapshots(session_id, context_type)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_memory_timestamp 
                ON memory_snapshots(timestamp DESC)
            """)
            conn.commit()
    
    def save_context(self, session_id: str, context_type: str, data: Dict[str, Any]) -> str:
        """
        Save a context snapshot.
        
        Args:
            session_id: Current session ID
            context_type: 'active_context' or 'memory_bank'
            data: The context data to save
            
        Returns:
            The snapshot_id
        """
        snapshot_id = str(uuid.uuid4())
        
        with self._get_connection() as conn:
            conn.execute(
                """INSERT INTO memory_snapshots 
                   (snapshot_id, session_id, context_type, data)
                   VALUES (?, ?, ?, ?)""",
                (snapshot_id, session_id, context_type, json.dumps(data))
            )
            conn.commit()
        
        logger.debug(f"Saved {context_type} snapshot: {snapshot_id}")
        return snapshot_id
    
    def load_latest_context(self, context_type: str) -> Optional[Dict[str, Any]]:
        """Load the most recent context of a given type."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT data FROM memory_snapshots 
                   WHERE context_type = ?
                   ORDER BY timestamp DESC LIMIT 1""",
                (context_type,)
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
            return None
    
    def load_session_context(self, session_id: str, context_type: str) -> Optional[Dict[str, Any]]:
        """Load context for a specific session."""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT data FROM memory_snapshots 
                   WHERE session_id = ? AND context_type = ?
                   ORDER BY timestamp DESC LIMIT 1""",
                (session_id, context_type)
            )
            row = cursor.fetchone()
            
            if row:
                return json.loads(row[0])
            return None
    
    def query_recent_events(self, hours: int = 24, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query recent memory snapshots for pattern analysis.
        Used by self-healing logic to detect trends.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                """SELECT snapshot_id, session_id, timestamp, context_type, data
                   FROM memory_snapshots
                   WHERE timestamp > datetime('now', ?)
                   ORDER BY timestamp DESC
                   LIMIT ?""",
                (f'-{hours} hours', limit)
            )
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "snapshot_id": row[0],
                    "session_id": row[1],
                    "timestamp": row[2],
                    "context_type": row[3],
                    "data": json.loads(row[4])
                })
            return results
    
    def get_failure_patterns(self, window_hours: int = 24) -> List[Dict[str, Any]]:
        """
        Analyze recent snapshots for failure patterns.
        Returns files/tasks with repeated failures.
        """
        events = self.query_recent_events(hours=window_hours)
        
        failure_counts = {}
        for event in events:
            data = event.get("data", {})
            # Look for error markers in context
            if data.get("error") or data.get("status") == "FAILED":
                key = data.get("task_id") or data.get("file") or "unknown"
                failure_counts[key] = failure_counts.get(key, 0) + 1
        
        # Return items with 2+ failures
        patterns = [
            {"target": k, "failure_count": v}
            for k, v in failure_counts.items()
            if v >= 2
        ]
        return sorted(patterns, key=lambda x: x["failure_count"], reverse=True)


# Global instance
memory_store = MemoryStore()
