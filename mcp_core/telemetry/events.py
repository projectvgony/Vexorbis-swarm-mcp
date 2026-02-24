
from enum import Enum
from typing import Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field
import uuid

class EventType(str, Enum):
    TOOL_USE = "tool_use"
    TASK_ROUTING = "task_routing"
    ERROR = "error"
    PROVENANCE = "provenance"
    SYS_STARTUP = "startup"
    GAP_DETECTED = "gap_detected" # For Toolsmith

class TelemetryEvent(BaseModel):
    """
    Standardized telemetry event for Swarm.
    
    Privacy Principles:
    1. No PII (names, emails, raw code content).
    2. Hashed identifiers for correlation.
    3. Bucketed metrics for privacy preservation.
    """
    event_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_id: str # Ephemeral session ID
    install_id: str # Hashed install ID
    
    type: EventType
    tool_name: Optional[str] = None
    
    # Context
    codebase_size_bucket: str = "unknown" # e.g. "small", "medium", "large"
    language: Optional[str] = None
    
    # Instruction (Anonymized)
    instruction_hash: Optional[str] = None # One-way hash of prompt
    instruction_tokens: Optional[int] = None
    
    # Outcome
    success: bool = True
    duration_ms: float = 0.0
    error_category: Optional[str] = None
    
    # ML Features
    routing_confidence: float = 0.0
    algorithm_selected: Optional[str] = None
    
    # Metadata
    properties: Dict[str, Any] = Field(default_factory=dict)
