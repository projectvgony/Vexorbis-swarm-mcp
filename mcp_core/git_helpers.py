"""
Git Helper Functions for Conventional Commits

Provides utilities for formatting git commit messages according to
the Conventional Commits specification (https://conventionalcommits.org).
"""

from typing import List
from mcp_core.swarm_schemas import Task


def infer_commit_type(task: Task) -> str:
    """
    Infer conventional commit type from task context.
    
    Args:
        task: The Task object to analyze
        
    Returns:
        Commit type string (feat, fix, refactor, etc.)
    """
    desc_lower = task.description.lower()
    
    # Keyword-based inference
    if any(kw in desc_lower for kw in ["add", "implement", "feature", "introduce"]):
        return "feat"
    elif any(kw in desc_lower for kw in ["fix", "bug", "resolve", "patch"]):
        return "fix"
    elif any(kw in desc_lower for kw in ["refactor", "restructure", "reorganize"]):
        return "refactor"
    elif any(kw in desc_lower for kw in ["test", "spec", "coverage"]):
        return "test"
    elif any(kw in desc_lower for kw in ["doc", "readme", "guide"]):
        return "docs"
    elif any(kw in desc_lower for kw in ["optimize", "performance", "perf"]):
        return "perf"
    elif any(kw in desc_lower for kw in ["style", "format", "lint"]):
        return "style"
    else:
        return "chore"


def infer_scope(task: Task) -> str:
    """
    Infer scope from task metadata or output files.
    
    Args:
        task: The Task object
        
    Returns:
        Scope string (e.g., "auth", "api", "core")
    """
    # Check explicit metadata first
    if hasattr(task, 'metadata') and task.metadata:
        if "scope" in task.metadata:
            return task.metadata["scope"]
    
    # Infer from output files
    if task.output_files:
        first_file = task.output_files[0]
        # Extract directory (e.g., "mcp_core/algorithms/auth.py" -> "algorithms")
        parts = first_file.split('/')
        if len(parts) > 1:
            return parts[-2]  # Second to last (directory containing file)
    
    return "core"


def format_commit_message(task: Task, include_emoji: bool = False, contributing_model: str = None) -> str:
    """
    Format a conventional commit message from a task.
    
    Args:
        task: The Task object
        include_emoji: Whether to include 🤖 emoji prefix
        model_id: The contributing model that generated the code
        
    Returns:
        Formatted commit message following Conventional Commits spec
    """
    commit_type = infer_commit_type(task)
    scope = infer_scope(task)
    
    # Format: type(scope): description
    message = f"{commit_type}({scope}): {task.description}"
    
    # Optional emoji prefix for compatibility
    if include_emoji:
        message = f"🤖 {message}"
    
    # Add model provenance if provided
    if contributing_model:
        message += f"\n\nModel-Provenance: {contributing_model}"
    
    return message


def format_commit_body(feedback_log: List[str], max_lines: int = 5) -> str:
    """
    Format task feedback into a commit body.
    
    Args:
        feedback_log: List of feedback messages from task execution
        max_lines: Maximum number of lines to include
        
    Returns:
        Formatted commit body string (empty if no relevant feedback)
    """
    if not feedback_log:
        return ""
    
    # Extract key accomplishments (lines with ✅ or "Completed")
    accomplishments = [
        log.strip() for log in feedback_log 
        if "✅" in log or "Completed" in log or "Created" in log
    ]
    
    if accomplishments:
        # Take first N accomplishments
        selected = accomplishments[:max_lines]
        return "\n".join(f"- {a.replace('✅', '').strip()}" for a in selected)
    
    return ""
