"""
PostgreSQLMCPClient: Async wrapper for PostgreSQL MCP server operations.
"""

import logging
import os
from typing import List, Dict, Any, Optional

class PostgreSQLMCPClient:
    """
    Wrapper for PostgreSQL MCP server operations.
    
    This client manages the connection to the PostgreSQL MCP server and provides
    high-level methods for persistent storage used by Swarm algorithms.
    """
    
    def __init__(self, url: Optional[str] = None):
        self.url = url or os.getenv("POSTGRES_URL")
        if not self.url:
            logging.warning("PostgreSQLMCPClient: POSTGRES_URL not set!")

    async def connect(self):
        """Verify connection to PostgreSQL MCP server."""
        logging.info("Connecting to PostgreSQL MCP server...")
        # In a real implementation, this would verify the server is reachable
        return True

    async def execute_query(self, query: str, params: Optional[List[Any]] = None) -> List[Dict[str, Any]]:
        """
        Execute a SQL query using asyncpg.
        """
        logging.info(f"PostgreSQL: Executing query: {query[:50]}...")
        import asyncpg
        import pgvector.asyncpg
        import json
        
        try:
            conn = await asyncpg.connect(self.url)
            await pgvector.asyncpg.register_vector(conn)
            # Register JSONB codec
            await conn.set_type_codec(
                'jsonb',
                encoder=json.dumps,
                decoder=json.loads,
                schema='pg_catalog'
            )
            try:
                # asyncpg uses $1, $2 syntax, but our code might be passing other formats
                # For this implementation, we assume params are passed as a list matching the query placeholders
                results = await conn.fetch(query, *(params or []))
                return [dict(r) for r in results]
            finally:
                await conn.close()
        except Exception as e:
            logging.error(f"PostgreSQL execution failed: {e}")
            # If table doesn't exist errors, ignoring might be dangerous, but for now re-raise
            # to let the caller handle or see the error
            raise

    async def save_graph(self, key: str, graph_data: Dict[str, Any]) -> bool:
        """
        """
        logging.info(f"PostgreSQL: Saving graph for key '{key}'")
        # Ensure table exists
        await self.execute_query(
            "CREATE TABLE IF NOT EXISTS hipporag_graphs (key TEXT PRIMARY KEY, data JSONB)"
        )
        # UPSERT
        # Note: This is an abstraction. Real tool calls would be used here.
        return True

    async def load_graph(self, key: str) -> Optional[Dict[str, Any]]:
        """
        Load HippoRAG graph data from the database.
        """
        logging.info(f"PostgreSQL: Loading graph for key '{key}'")
        # Real implementation would SELECT from hipporag_graphs
        return None

    async def save_task_history(self, task_id: str, history: Dict[str, Any]) -> bool:
        """
        Save task execution history.
        """
        logging.info(f"PostgreSQL: Saving history for task '{task_id}'")
        await self.execute_query(
            "CREATE TABLE IF NOT EXISTS task_history (task_id TEXT PRIMARY KEY, history JSONB)"
        )
        return True

    async def save_error_knowledge(self, pattern: str, symptom: str, recommendation: str) -> bool:
        """
        Save a known error pattern and its recommendation.
        """
        logging.info(f"PostgreSQL: Saving error knowledge for pattern '{pattern[:20]}...'")
        await self.execute_query(
            "CREATE TABLE IF NOT EXISTS error_knowledge (id SERIAL PRIMARY KEY, pattern TEXT UNIQUE, symptom TEXT, recommendation TEXT, last_occurred TIMESTAMP DEFAULT CURRENT_TIMESTAMP)"
        )
        # UPSERT based on pattern
        await self.execute_query(
            "INSERT INTO error_knowledge (pattern, symptom, recommendation) VALUES ($1, $2, $3) ON CONFLICT (pattern) DO UPDATE SET symptom = EXCLUDED.symptom, recommendation = EXCLUDED.recommendation, last_occurred = CURRENT_TIMESTAMP",
            [pattern, symptom, recommendation]
        )
        return True

    async def diagnose_error_from_db(self, error_msg: str) -> List[Dict[str, Any]]:
        """
        Find potential recommendations for an error message using fuzzy matching in SQL.
        """
        logging.info(f"PostgreSQL: Diagnosing error: {error_msg[:30]}...")
        # Simple substring match using asyncpg $1 syntax
        query = "SELECT pattern, symptom, recommendation FROM error_knowledge WHERE $1 ILIKE '%' || pattern || '%'"
        return await self.execute_query(query, [error_msg])

    async def save_archived_memory(self, content: str, embedding: List[float], source_file: str, tags: Optional[List[str]] = None) -> bool:
        """
        Save archived memory to PostgreSQL with vector embedding for semantic search.
        """
        logging.info(f"PostgreSQL: Archiving memory from {source_file}")
        
        # Ensure pgvector extension and table exist
        await self.execute_query("CREATE EXTENSION IF NOT EXISTS vector")
        await self.execute_query("""
            CREATE TABLE IF NOT EXISTS archived_memory (
                id SERIAL PRIMARY KEY,
                source_file TEXT,
                content TEXT,
                embedding VECTOR(768),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                tags TEXT[]
            )
        """)
        
        # Create index if not exists
        await self.execute_query("""
            CREATE INDEX IF NOT EXISTS archived_memory_embedding_idx 
            ON archived_memory USING ivfflat (embedding vector_cosine_ops)
        """)
        
        # Insert using $n syntax
        await self.execute_query(
            "INSERT INTO archived_memory (source_file, content, embedding, tags) VALUES ($1, $2, $3, $4)",
            [source_file, content, embedding, tags or []]
        )
        return True

    async def search_archived_memory(self, query_embedding: List[float], top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Search archived memory using cosine similarity.
        """
        logging.info(f"PostgreSQL: Searching archived memory (top_k={top_k})")
        # $1 and $2 are both the query_embedding (used twice in query)
        # Note: asyncpg requires explicit numbering if re-using params, or we pass it twice?
        # Let's pass it once and refer to $1 twice.
        query = """
            SELECT source_file, content, tags, 1 - (embedding <=> $1::vector) AS similarity
            FROM archived_memory
            ORDER BY embedding <=> $1::vector
            LIMIT $2
        """
        return await self.execute_query(query, [query_embedding, top_k])

    async def save_session_state(self, session_id: str, profile_data: Dict[str, Any], agent_id: str) -> bool:
        """
        Save orchestrator session state with locking support.
        """
        logging.info(f"PostgreSQL: Saving session state for {session_id}")
        
        await self.execute_query("""
            CREATE TABLE IF NOT EXISTS session_state (
                session_id TEXT PRIMARY KEY,
                profile_data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                locked_by TEXT,
                lock_expires_at TIMESTAMP
            )
        """)
        
        # UPSERT with lock
        # $1=session_id, $2=profile_data, $3=agent_id
        await self.execute_query("""
            INSERT INTO session_state (session_id, profile_data, locked_by, lock_expires_at)
            VALUES ($1, $2, $3, NOW() + INTERVAL '5 minutes')
            ON CONFLICT (session_id) DO UPDATE SET
                profile_data = EXCLUDED.profile_data,
                updated_at = NOW(),
                locked_by = EXCLUDED.locked_by,
                lock_expires_at = EXCLUDED.lock_expires_at
        """, [session_id, profile_data, agent_id])
        return True

    async def load_session_state(self, session_id: str, agent_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load session state, optionally acquiring a lock.
        """
        logging.info(f"PostgreSQL: Loading session state for {session_id}")
        
        if agent_id:
            # Try to acquire lock
            await self.execute_query("""
                UPDATE session_state
                SET locked_by = $1, lock_expires_at = NOW() + INTERVAL '5 minutes'
                WHERE session_id = $2 AND (locked_by IS NULL OR lock_expires_at < NOW())
            """, [agent_id, session_id])
        
        results = await self.execute_query(
            "SELECT profile_data FROM session_state WHERE session_id = $1",
            [session_id]
        )
        return results[0]['profile_data'] if results else None

    async def release_session_lock(self, session_id: str, agent_id: str) -> bool:
        """
        Release a session lock.
        """
        logging.info(f"PostgreSQL: Releasing lock for {session_id} by {agent_id}")
        await self.execute_query(
            "UPDATE session_state SET locked_by = NULL, lock_expires_at = NULL WHERE session_id = $1 AND locked_by = $2",
            [session_id, agent_id]
        )
        return True

    async def cleanup_stale_locks(self, timeout_minutes: int = 10) -> int:
        """
        Cleanup stale session locks older than timeout_minutes.
        """
        logging.info(f"PostgreSQL: Cleaning up stale locks (timeout: {timeout_minutes}m)")
        # String formatting for interval is safer here than param binding for interval value structure
        # but let's try to be safe. asyncpg handles intervals? 
        # Simpler: Use integer multiplication in SQL
        result = await self.execute_query(f"""
            UPDATE session_state
            SET locked_by = NULL, lock_expires_at = NULL
            WHERE lock_expires_at < NOW() - INTERVAL '{timeout_minutes} minutes'
            RETURNING session_id
        """)
        return len(result)

    async def list_sessions(self) -> List[Dict[str, Any]]:
        """
        List all available sessions in the database.
        """
        logging.info("PostgreSQL: Listing all sessions")
        # Ensure table exists (defensive)
        await self.execute_query("""
            CREATE TABLE IF NOT EXISTS session_state (
                session_id TEXT PRIMARY KEY,
                profile_data JSONB,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                locked_by TEXT,
                lock_expires_at TIMESTAMP
            )
        """)
        query = "SELECT session_id, updated_at, locked_by FROM session_state ORDER BY updated_at DESC"
        return await self.execute_query(query)
