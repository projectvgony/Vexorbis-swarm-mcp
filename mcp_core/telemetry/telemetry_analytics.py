
import sqlite3
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

class TelemetryAnalyticsService:
    """
    Service to query telemetry.db for insights.
    Used by:
    - GitRoleDispatcher (to optimize role order)
    - Orchestrator (to warn about flaky tools)
    - Dashboard (to visualize performance)
    """

    def __init__(self, db_path: Optional[Path] = None):
        if db_path is None:
            self.db_path = Path.home() / ".swarm" / "telemetry.db"
        else:
            self.db_path = db_path

    def _get_connection(self):
        return sqlite3.connect(str(self.db_path))

    def get_tool_success_rate(self, tool_name: str, window_days: int = 7) -> float:
        """Calculate success rate for a tool over the last N days."""
        if not self.db_path.exists():
            return 1.0  # Default to optimistic if no data

        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN json_extract(data, '$.success') = 1 THEN 1 ELSE 0 END) as successes
            FROM events
            WHERE type = 'tool_use'
              AND json_extract(data, '$.tool_name') = ?
              AND timestamp > date('now', ?)
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (tool_name, f'-{window_days} days'))
                row = cursor.fetchone()
                
                if row and row[0] and row[0] > 0:
                    return row[1] / row[0]
                return 1.0 # Default success
        except Exception as e:
            logger.warning(f"Failed to query tool stats: {e}")
            return 1.0

    def get_role_success_rate(self, role: str) -> float:
        """
        Calculate success rate for a Git Role.
        Relies on provenance events where role=<role> and action='task_completed' vs 'task_failed'
        """
        if not self.db_path.exists():
            return 1.0

        query = """
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN json_extract(data, '$.success') = 1 THEN 1 ELSE 0 END) as successes
            FROM events
            WHERE type = 'provenance'
              AND json_extract(data, '$.properties.role') = ?
        """
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (role,))
                row = cursor.fetchone()
                
                if row and row[0] and row[0] > 0:
                    return row[1] / row[0]
                return 1.0
        except Exception as e:
            logger.warning(f"Failed to query role stats: {e}")
            return 1.0
            
    def get_problematic_tools(self, threshold: float = 0.8, window_days: int = 3) -> List[Dict[str, Any]]:
        """Identify tools with success rate below threshold."""
        if not self.db_path.exists():
            return []

        query = """
            SELECT 
                json_extract(data, '$.tool_name') as name,
                COUNT(*) as total,
                SUM(CASE WHEN json_extract(data, '$.success') = 1 THEN 1 ELSE 0 END) as successes
            FROM events
            WHERE type = 'tool_use'
              AND timestamp > date('now', ?)
            GROUP BY name
            HAVING total > 5
        """
        
        problems = []
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (f'-{window_days} days',))
                rows = cursor.fetchall()
                
                for row in rows:
                    name, total, successes = row
                    rate = successes / total
                    if rate < threshold:
                        problems.append({
                            "tool": name,
                            "success_rate": rate,
                            "total_uses": total
                        })
        except Exception as e:
            logger.warning(f"Failed to query problematic tools: {e}")
            
        return problems

    def get_avg_duration(self, tool_name: str) -> float:
        """Get average duration in ms for a tool."""
        if not self.db_path.exists():
            return 0.0
            
        query = """
            SELECT AVG(json_extract(data, '$.duration_ms'))
            FROM events
            WHERE type = 'tool_use'
              AND json_extract(data, '$.tool_name') = ?
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (tool_name,))
                row = cursor.fetchone()
                return row[0] if row and row[0] else 0.0
        except Exception:
            return 0.0
    
    def get_performance_index(self, role: str, success_weight: float = 0.7, speed_weight: float = 0.3, max_duration_ms: float = 10000.0) -> float:
        """
        Calculate a multi-dimensional performance index for a role.
        PI = (SuccessRate * SuccessWeight) + (SpeedScore * SpeedWeight)
        SpeedScore = 1 - (AvgDuration / MaxDuration)
        
        Returns: 0.0 to 1.0 (higher is better)
        """
        success_rate = self.get_role_success_rate(role)
        avg_duration = self.get_avg_duration(f"git_role_{role}")  # Assuming roles are tracked with this prefix
        
        # Calculate speed score (normalized inverse of duration)
        speed_score = 1.0 - min(avg_duration / max_duration_ms, 1.0) if avg_duration > 0 else 1.0
        
        # Weighted combination
        pi = (success_rate * success_weight) + (speed_score * speed_weight)
        return pi
    
    def get_tool_status(self, tool_name: str, critical_threshold: float = 0.3, warning_threshold: float = 0.7, window_days: int = 1) -> str:
        """
        Determine circuit breaker status for a tool.
        Returns: "READY", "WARNING", or "TRIPPED"
        """
        if not self.db_path.exists():
            return "READY"
        
        # Get recent performance (last 24 hours for quick detection)
        success_rate = self.get_tool_success_rate(tool_name, window_days=window_days)
        
        if success_rate < critical_threshold:
            return "TRIPPED"
        elif success_rate < warning_threshold:
            return "WARNING"
        return "READY"
    
    def prune_old_events(self, retention_days: int = 30) -> int:
        """
        Delete telemetry events older than retention_days.
        Returns: Number of rows deleted.
        """
        if not self.db_path.exists():
            return 0
        
        query = "DELETE FROM events WHERE timestamp < date('now', ?)"
        
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query, (f'-{retention_days} days',))
                deleted = cursor.rowcount
                conn.commit()
                logger.info(f"Pruned {deleted} old telemetry events")
                return deleted
        except Exception as e:
            logger.error(f"Failed to prune old events: {e}")
            return 0
    
    def optimize_database(self):
        """
        Run VACUUM and enable WAL mode for better performance.
        """
        if not self.db_path.exists():
            return
        
        try:
            with self._get_connection() as conn:
                conn.execute("PRAGMA journal_mode=WAL")
                conn.execute("VACUUM")
                conn.commit()
                logger.info("Optimized telemetry database")
        except Exception as e:
            logger.error(f"Failed to optimize database: {e}")
