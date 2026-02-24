"""
BranchManagerRole: Autonomous branch merging and PR lifecycle management.

This role manages the merging of approved PRs, handles stacked PR chains,
and maintains clean branch hygiene.
"""

from typing import Any, Dict, List
from .base import GitAgentRole, GitRole, ExitReport


class BranchManagerRole(GitAgentRole):
    """
    Autonomous branch and PR manager.
    
    Responsibilities:
    - Monitor PR status (approvals, CI)
    - Execute merge operations (squash/rebase)
    - Manage stacked PR chain updates
    - Update PLAN.md checkboxes
    - Prune merged feature branches
    """
    
    def __init__(self):
        super().__init__(GitRole.BRANCH_MANAGER)
    
    def trigger_check(self, task: Any, context: Dict[str, Any]) -> bool:
        """
        Trigger when PR is approved and CI is passing.
        
        Args:
            task: Task object
            context: Execution context
            
        Returns:
            True if branch management should run
        """
        # Check if there's an approved PR
        pr_status = context.get('pr_status', {})
        if pr_status.get('approved') and pr_status.get('ci_passing'):
            return True
        
        # Check for stacked PR update needed
        if context.get('stacked_pr_update_needed', False):
            return True
        
        return False
    
    def execute(self, task: Any, context: Dict[str, Any]) -> ExitReport:
        """
        Execute branch management workflow.
        
        Steps:
        1. Verify PR is ready to merge
        2. Execute merge (squash/rebase per config)
        3. Update dependent stacked PRs
        4. Update PLAN.md if applicable
        5. Prune merged branch
        
        Args:
            task: Task object
            context: Execution context with github_client
            
        Returns:
            ExitReport with merge results
        """
        warnings = []
        
        github_client = context.get('github_client')
        if not github_client:
            return ExitReport(
                task_id=task.task_id if hasattr(task, 'task_id') else "unknown",
                status="BLOCKED",
                warnings=["GitHub client not available"]
            )
        
        pr_number = context.get('pr_number')
        if not pr_number:
            return ExitReport(
                task_id=task.task_id if hasattr(task, 'task_id') else "unknown",
                status="BLOCKED",
                warnings=["No PR number provided"]
            )
        
        # Step 1: Verify PR status
        pr_details = self._get_pr_details(pr_number, github_client)
        if not self._is_ready_to_merge(pr_details):
            warnings.append(f"PR #{pr_number} not ready: {self._get_blocking_reasons(pr_details)}")
            return ExitReport(
                task_id=task.task_id if hasattr(task, 'task_id') else "unknown",
                status="BLOCKED",
                pr_url=pr_details.get('url'),
                warnings=warnings
            )
        
        # Step 2: Execute merge
        merge_result = self._merge_pr(pr_number, pr_details, github_client, context)
        
        # Step 3: Handle stacked PRs
        dependent_prs = self._find_dependent_prs(pr_details, context)
        for dep_pr in dependent_prs:
            self._update_stacked_pr(dep_pr, github_client)
        
        # Step 4: Update PLAN.md
        self._update_plan_checkboxes(task, context)
        
        # Step 5: Prune branch
        branch_name = pr_details.get('head', {}).get('ref')
        if branch_name:
            self._prune_branch(branch_name, github_client)
        
        return ExitReport(
            task_id=task.task_id if hasattr(task, 'task_id') else "unknown",
            status="COMPLETED",
            branch=branch_name,
            pr_url=pr_details.get('url'),
            remaining_work=f"Merged PR #{pr_number}, updated {len(dependent_prs)} dependent PRs",
            warnings=warnings
        )
    
    def _get_pr_details(self, pr_number: int, github_client) -> Dict[str, Any]:
        """Fetch PR details from GitHub."""
        repo_owner = "AgentAgony" # Context should ideally provide this
        repo_name = "swarm"
        
        pr = self._run_async(github_client.get_pull_request(
            owner=repo_owner,
            repo=repo_name,
            pull_number=pr_number
        ))
        return pr
    
    def _is_ready_to_merge(self, pr_details: Dict[str, Any]) -> bool:
        """Check if PR meets all merge criteria."""
        # Check approvals, CI status, conflicts
        return (
            pr_details.get('approved', False) and
            pr_details.get('ci_passing', False) and
            pr_details.get('mergeable', False)
        )
    
    def _get_blocking_reasons(self, pr_details: Dict[str, Any]) -> str:
        """Get human-readable reason why PR can't merge."""
        reasons = []
        if not pr_details.get('approved'):
            reasons.append("needs approval")
        if not pr_details.get('ci_passing'):
            reasons.append("CI failing")
        if not pr_details.get('mergeable'):
            reasons.append("has conflicts")
        return ", ".join(reasons)
    
    def _merge_pr(
        self, 
        pr_number: int, 
        pr_details: Dict[str, Any], 
        github_client,
        context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute PR merge."""
        repo_owner = context.get('repo_owner', 'AgentAgony')
        repo_name = context.get('repo_name', 'swarm')
        merge_method = context.get('merge_method', 'squash')
        
        result = self._run_async(github_client.merge_pull_request(
            owner=repo_owner,
            repo=repo_name,
            pull_number=pr_number,
            method=merge_method
        ))
        return result
    
    def _find_dependent_prs(self, merged_pr: Dict[str, Any], context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find PRs that depend on this one (stacked PRs)."""
        # Look for PRs whose base branch matches the merged PR's head branch
        merged_branch = merged_pr.get('head', {}).get('ref', '')
        
        # Save dependency info to memory store for future analysis
        memory_store = context.get('memory_store')
        if memory_store:
            memory_store.save_context(
                session_id=context.get('session_id', 'branch_manager'),
                context_type='pr_merged',
                data={'branch': merged_branch, 'pr_number': merged_pr.get('number')}
            )
        
        # In a real implementation, would query GitHub for PRs with base=merged_branch
        return []
    
    def _update_stacked_pr(self, pr: Dict[str, Any], github_client):
        """Update a stacked PR after its dependency merged."""
        import logging
        pr_number = pr.get('number')
        logging.info(f"BranchManager: Would rebase/update stacked PR #{pr_number}")
        
        # In a real implementation:
        # 1. Update the base branch to the new merged target
        # 2. Trigger a rebase if needed
    
    def _update_plan_checkboxes(self, task: Any, context: Dict[str, Any]):
        """Update PLAN.md checkboxes if task corresponds to roadmap item."""
        import logging
        task_id = task.task_id if hasattr(task, 'task_id') else 'unknown'
        logging.info(f"BranchManager: Would update PLAN.md for task {task_id}")
        
        # Record provenance
        collector = context.get('telemetry_collector')
        if collector:
            collector.record_provenance(
                agent_id="branch_manager",
                role="branch_manager",
                action="pr_merged",
                artifact_ref=task_id
            )
    
    def _prune_branch(self, branch_name: str, github_client):
        """Delete merged feature branch."""
        import logging
        logging.info(f"BranchManager: Pruning branch {branch_name}")
        
        # In a real implementation, would call:
        # github_client.delete_branch(owner, repo, branch_name)
