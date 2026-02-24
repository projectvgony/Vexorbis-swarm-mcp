"""
Git Worker - Workflow Orchestration for External MCP Servers

Detects Git repositories and manages workflow flags.
Actual Git operations are delegated to external Git/GitHub MCP servers.
"""

import re
import logging
import subprocess
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)


class GitProvider(Enum):
    """Detected Git provider."""
    NONE = "none"
    LOCAL = "local"
    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


@dataclass
class GitConfig:
    """Detected repository configuration."""
    provider: GitProvider = GitProvider.NONE
    remote_url: str = ""
    default_branch: str = "main"
    repo_path: str = "."


class GitWorker:
    """
    Git workflow orchestrator.
    
    Detects .git and remotes, manages task flags for autonomous workflow.
    Delegates actual operations to external Git/GitHub MCP servers.
    
    Example:
        git = GitWorker(".")
        if git.is_available():
            instructions = git.get_workflow_instructions()
    """
    
    def __init__(self, repo_path: str = "."):
        self.repo_path = Path(repo_path).resolve()
        self.config = self._detect()
    
    def _detect(self) -> GitConfig:
        """Auto-detect Git configuration from .git folder."""
        git_dir = self.repo_path / ".git"
        
        if not git_dir.exists():
            logger.debug("No .git directory found")
            return GitConfig(repo_path=str(self.repo_path))
        
        config = GitConfig(
            provider=GitProvider.LOCAL,
            repo_path=str(self.repo_path)
        )
        
        # Use git config command for robust detection
        try:
            # Get Remote URL
            result = subprocess.run(
                ["git", "config", "--get", "remote.origin.url"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                url = result.stdout.strip()
                config.remote_url = url
                
                # Detect provider
                if "github.com" in url:
                    config.provider = GitProvider.GITHUB
                elif "gitlab.com" in url:
                    config.provider = GitProvider.GITLAB
                elif "bitbucket.org" in url:
                    config.provider = GitProvider.BITBUCKET

            # Get Default Branch
            result = subprocess.run(
                ["git", "branch", "--show-current"],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=False
            )
            if result.returncode == 0:
                config.default_branch = result.stdout.strip()

        except Exception as e:
            logger.warning(f"Git config detection failed: {e}")
        
        logger.info(f"Git detected: {config.provider.value}, remote: {config.remote_url or 'none'}")
        return config
    
    def is_available(self) -> bool:
        """Check if Git repository is available."""
        return self.config.provider != GitProvider.NONE
    
    def is_github(self) -> bool:
        """Check if connected to GitHub."""
        return self.config.provider == GitProvider.GITHUB
    
    def is_gitlab(self) -> bool:
        """Check if connected to GitLab."""
        return self.config.provider == GitProvider.GITLAB
    
    def has_remote(self) -> bool:
        """Check if repository has a remote configured."""
        return bool(self.config.remote_url)
    
    def has_changes(self) -> bool:
        """Check if there are any uncommitted changes (modified/staged)."""
        if not self.is_available():
            return False
            
        try:
            import subprocess
            # safe_run logic (or just concise subprocess here)
            # Using --porcelain for easy parsing (empty if clean)
            result = subprocess.run(
                ["git", "status", "--porcelain"], 
                cwd=str(self.repo_path), 
                capture_output=True, 
                text=True, 
                timeout=5
            )
            return bool(result.stdout.strip())
        except Exception as e:
            logger.warning(f"Git status check failed: {e}")
            return False
    
    def has_github_token(self) -> bool:
        """Check if GITHUB_TOKEN environment variable is set."""
        import os
        return bool(os.environ.get("GITHUB_TOKEN"))
    
    def is_github_ready(self) -> bool:
        """Check if GitHub MCP operations are ready (GitHub repo + token)."""
        return self.is_github() and self.has_github_token()
    
    def get_workflow_instructions(self) -> str:
        """
        Return instructions for coding agent to use external Git MCP tools.
        
        This is injected into worker prompts when Git is detected.
        """
        if not self.is_available():
            return ""
        
        instructions = """
<git_workflow>
Git repository detected. After completing file changes:

1. Use external MCP tools for Git operations:
   - git_status: Check current repository state
   - git_add: Stage modified files
   - git_commit: Commit with HELPFUL message.
     Format: `type(scope): description`
     
     REQUIRED: You MUST include a "Why" and "What" in the body.
     Example:
     ```
     feat(auth): enable jwt token refresh

     Why: User sessions were timing out unexpectedly.
     What: Added refresh endpoint and client-side interceptor.
     Task: #123
     ```
"""
        
        if self.has_remote():
            instructions += f"""   - git_push: Push to remote ({self.config.provider.value})
"""
        
        if self.is_github():
            if self.has_github_token():
                instructions += """   - create_pull_request: Create PR for review (GitHub) ✅
"""
            else:
                instructions += """   - create_pull_request: ⚠️ Requires GITHUB_TOKEN env var
"""
        elif self.is_gitlab():
            instructions += """   - create_merge_request: Create MR for review (GitLab)
"""
        
        instructions += """
2. Set task flags for automation:
   - git_commit_ready=True: Signal commit readiness
   - git_auto_push=True: Auto-push after commit
   - git_create_pr=True: Auto-create PR/MR

3. Branching Strategy:
   - Feature/fix branches target 'dev' by default
   - Use 'main' only for production releases
   - PR workflow: feature → dev → main
</git_workflow>
"""
        return instructions
    
    def get_provider_info(self) -> dict:
        """Get provider information for logging/debugging."""
        return {
            "provider": self.config.provider.value,
            "has_remote": self.has_remote(),
            "remote_url": self.config.remote_url,
            "default_branch": self.config.default_branch,
            "repo_path": self.config.repo_path
        }
