
import sqlite3
import json
import logging
from pathlib import Path
from typing import List, Dict, Any
from mcp_core.telemetry.events import TelemetryEvent

logger = logging.getLogger(__name__)

class LocalTelemetryBuffer:
    """
    Local SQLite buffer for telemetry events.
    Stored in ~/.swarm/telemetry.db
    """
    
    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_db()
        
    def _init_db(self):
        """Initialize database schema."""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    CREATE TABLE IF NOT EXISTS events (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT,
                        type TEXT,
                        session_id TEXT,
                        install_id TEXT,
                        data JSON
                    )
                """)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to init telemetry DB: {e}")

    def add_event(self, event: TelemetryEvent):
        """Flatten and store event."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO events (id, timestamp, type, session_id, install_id, data) VALUES (?, ?, ?, ?, ?, ?)",
                    (
                        event.event_id,
                        event.timestamp.isoformat(),
                        event.type.value,
                        event.session_id,
                        event.install_id,
                        event.model_dump_json()
                    )
                )
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to record telemetry event: {e}")
            
    def get_stats(self) -> Dict[str, int]:
        """Get basic stats for health check."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
                return {"total_events": count}
        except Exception:
            return {"total_events": -1}
