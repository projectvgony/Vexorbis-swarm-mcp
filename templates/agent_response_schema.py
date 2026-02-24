from typing import List, Any
from pydantic import BaseModel, Field, field_validator

class ToolCall(BaseModel):
    function: str
    arguments: Any # JSON string or Dict from LLM

class AgentResponse(BaseModel):
    """
    Standardized response format for all workers (Architect, Engineer, Auditor).
    """
    status: str = Field(pattern=r"^(PENDING|SUCCESS|FAILED|NEEDS_CLARIFICATION)$")
    reasoning_trace: str = Field(..., description="Chain of thought explaining the action")
    validation_score: float = Field(default=0.0, description="Self-reported confidence (0.0-1.0)")
    artifacts_created: List[str] = Field(default_factory=list, description="List of files created or modified")
    
    # [v3.0] Tooling & State
    tool_calls: List[ToolCall] = Field(default_factory=list, description="List of tools to execute") 
    blackboard_update: dict = Field(default_factory=dict, description="State updates")
    
    class ConfigDict:
        extra = "allow"

    @field_validator('validation_score')
    @classmethod
    def score_must_be_valid(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError('validation_score must be between 0.0 and 1.0')
        return v
