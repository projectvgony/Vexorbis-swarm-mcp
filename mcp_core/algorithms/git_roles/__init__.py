"""Git agent roles package - individual role implementations."""

from .base import GitRole, HandoffProtocol, ExitReport, GitAgentRole
from .feature_scout import FeatureScoutRole
from .code_auditor import CodeAuditorRole
from .issue_triage import IssueTriageRole
from .branch_manager import BranchManagerRole
from .project_lifecycle import ProjectLifecycleRole

__all__ = [
    "GitRole",
    "HandoffProtocol",
    "ExitReport",
    "GitAgentRole",
    "FeatureScoutRole",
    "CodeAuditorRole",
    "IssueTriageRole",
    "BranchManagerRole",
    "ProjectLifecycleRole"
]
