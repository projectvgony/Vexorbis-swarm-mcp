"""
Base definitions for GitWorker Agent Role System.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class GitRole(Enum):
    """Available autonomous Git agent roles."""
    FEATURE_SCOUT = "feature_scout"
    CODE_AUDITOR = "code_auditor"
    ISSUE_TRIAGE = "issue_triage"
    BRANCH_MANAGER = "branch_manager"
    PROJECT_LIFECYCLE = "project_lifecycle"


@dataclass
class HandoffProtocol:
    """
    Standardized handoff structure between Git agent roles.
    """
    from_role: GitRole
    to_role: GitRole
    task_id: str
    status: str  # PENDING | IN_PROGRESS | COMPLETED | BLOCKED
    context: Dict[str, Any] = field(default_factory=dict)
    notes: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for logging/storage."""
        return {
            "from_role": self.from_role.value,
            "to_role": self.to_role.value,
            "task_id": self.task_id,
            "status": self.status,
            "context": self.context,
            "notes": self.notes
        }


@dataclass
class ExitReport:
    """
    Standardized exit report for all Git agent roles.
    """
    task_id: str
    status: str  # COMPLETED | IN_PROGRESS | BLOCKED
    files_touched: List[str] = field(default_factory=list)
    branch: Optional[str] = None
    pr_url: Optional[str] = None
    remaining_work: str = ""
    warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize to dictionary for logging/storage."""
        return {
            "task_id": self.task_id,
            "status": self.status,
            "files_touched": self.files_touched,
            "branch": self.branch,
            "pr_url": self.pr_url,
            "remaining_work": self.remaining_work,
            "warnings": self.warnings
        }


class GitAgentRole(ABC):
    """
    Abstract base class for all Git agent roles.
    """
    
    def __init__(self, role: GitRole):
        self.role = role
    
    def _run_async(self, coro):
        """Helper to run async coroutines from synchronous execute methods."""
        import asyncio
        import threading
        
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
        if loop.is_running():
            # If we're already in a loop (like FastMCP), we need a bridge
            # This is a bit complex in a single thread. 
            # For now, let's use a simpler approach: 
            # if we are in a loop, we can't easily wait synchronously.
            # However, for testing and MVP, we can try to use a temporary loop in a thread.
            from concurrent.futures import ThreadPoolExecutor
            with ThreadPoolExecutor() as executor:
                return executor.submit(lambda: asyncio.run(coro)).result()
        else:
            return loop.run_until_complete(coro)

    @abstractmethod
    def trigger_check(self, task: Any, context: Dict[str, Any]) -> bool:
        pass
    
    @abstractmethod
    def execute(self, task: Any, context: Dict[str, Any]) -> ExitReport:
        pass
    
    def generate_handoff(
        self, 
        next_role: GitRole, 
        task_id: str, 
        status: str,
        context: Optional[Dict[str, Any]] = None,
        notes: str = ""
    ) -> HandoffProtocol:
        return HandoffProtocol(
            from_role=self.role,
            to_role=next_role,
            task_id=task_id,
            status=status,
            context=context or {},
            notes=notes
        )
