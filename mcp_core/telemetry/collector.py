"""
Swarm Telemetry Collector

Provides decorators and utilities for tracking tool usage.
"""

import logging
import functools
import os
from pathlib import Path
from typing import Callable, Any
from datetime import datetime, timezone
import uuid
import hashlib

from mcp_core.telemetry.events import TelemetryEvent, EventType
from mcp_core.telemetry.buffer import LocalTelemetryBuffer
from mcp_core.swarm_schemas import AuthorSignature


logger = logging.getLogger(__name__)

# Dev build: Enable verbose telemetry
VERBOSE_TELEMETRY = os.getenv("SWARM_VERBOSE_TELEMETRY", "false").lower() == "true"


class TelemetryCollector:
    """
    Telemetry collector for tracking tool usage and events.
    """
    
    def __init__(self):
        """Initialize the telemetry collector with a buffer."""
        db_path = Path.home() / ".swarm" / "telemetry.db"
        self.buffer = LocalTelemetryBuffer(db_path=db_path)
        self.session_id = str(uuid.uuid4())
        self.install_id = self._get_install_id()

    
    def _get_install_id(self) -> str:
        """Get or create a hashed install ID."""
        install_file = Path.home() / ".swarm" / "install_id"
        if install_file.exists():
            return install_file.read_text().strip()
        
        # Create new install ID
        install_file.parent.mkdir(parents=True, exist_ok=True)
        install_id = hashlib.sha256(str(uuid.uuid4()).encode()).hexdigest()[:16]
        install_file.write_text(install_id)
        return install_id
    
    def track_tool(self, tool_name: str) -> Callable:
        """
        Decorator to track tool usage.
        
        Usage:
            @collector.track_tool("my_tool")
            def my_tool(arg1, arg2):
                return result
        """
        def decorator(func: Callable) -> Callable:
            @functools.wraps(func)
            def wrapper(*args, **kwargs) -> Any:
                start_time = datetime.now(timezone.utc)
                success = True
                error = None
                
                # Verbose telemetry: Log tool invocation
                if VERBOSE_TELEMETRY:
                    logger.debug(f"🔧 Tool {tool_name} invoked with args={args[:2] if args else []}, kwargs={list(kwargs.keys())}")
                
                try:
                    result = func(*args, **kwargs)
                    return result
                except Exception as e:
                    success = False
                    error = str(e)
                    raise
                finally:
                    # Record event
                    end_time = datetime.now(timezone.utc)
                    duration_ms = (end_time - start_time).total_seconds() * 1000
                    
                    # Verbose telemetry: Log timing
                    if VERBOSE_TELEMETRY:
                        logger.debug(f"🕒 Tool {tool_name} completed in {duration_ms:.2f}ms (success={success})")
                    
                    event = TelemetryEvent(
                        session_id=self.session_id,
                        install_id=self.install_id,
                        type=EventType.TOOL_USE,
                        tool_name=tool_name,
                        success=success,
                        duration_ms=duration_ms,
                        error_category=type(error).__name__ if error else None
                    )
                    
                    try:
                        self.buffer.add_event(event)
                    except Exception as e:
                        logger.warning(f"Failed to record telemetry: {e}")
            
            return wrapper
        return decorator

    def record_provenance(self, agent_id: str, role: str, action: str, contributing_model: str = None, artifact_ref: str = None) -> AuthorSignature:
        """
        Record a provenance event and return the signature for state containment.
        """
        # 1. Create Signature
        signature = AuthorSignature(
            agent_id=agent_id,
            role=role,
            contributing_model=contributing_model,
            action=action,
            artifact_ref=artifact_ref,
            signature=self.install_id  # using install_id as a proxy for now
        )

        # 2. Log to Telemetry DB
        # We store the full signature in 'properties'
        props = signature.model_dump(mode='json')
        if artifact_ref:
            props["artifact_ref"] = artifact_ref

        event = TelemetryEvent(
            session_id=self.session_id,
            install_id=self.install_id,
            type=EventType.PROVENANCE,
            tool_name="provenance_log",
            success=True,
            properties=props
        )

        try:
            self.buffer.add_event(event)
        except Exception as e:
            logger.warning(f"Failed to record provenance: {e}")

        return signature


# Global collector instance
collector = TelemetryCollector()
