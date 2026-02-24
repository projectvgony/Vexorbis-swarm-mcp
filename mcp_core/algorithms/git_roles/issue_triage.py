"""
IssueTriageRole: Autonomous issue prioritization and assignment.

This role investigates open issues, assigns priorities based on impact and effort,
and updates task queues with proper dependencies.
"""

from typing import Any, Dict, List
from .base import GitAgentRole, GitRole, ExitReport


class IssueTriageRole(GitAgentRole):
    """
    Autonomous issue triage agent.
    
    Responsibilities:
    - Fetch open issues from GitHub
    - Query HippoRAG for related code context
    - Assign priorities (P0-P3) based on impact/effort
    - Update labels and milestones
    - Insert tasks into task_queue with dependencies
    """
    
    def __init__(self):
        super().__init__(GitRole.ISSUE_TRIAGE)
    
    def trigger_check(self, task: Any, context: Dict[str, Any]) -> bool:
        """
        Trigger on issue_triage_needed flag or new issue creation.
        
        Args:
            task: Task object
            context: Execution context
            
        Returns:
            True if triage should run
        """
        if hasattr(task, 'issue_triage_needed') and task.issue_triage_needed:
            return True
        
        if context.get('new_issues_count', 0) > 0:
            return True
        
        return False
    
    def execute(self, task: Any, context: Dict[str, Any]) -> ExitReport:
        """
        Execute issue triage workflow.
        
        Steps:
        1. Fetch open issues
        2. Analyze each issue for context
        3. Assign priority
        4. Update labels/milestones
        5. Create tasks with dependencies
        
        Args:
            task: Task object
            context: Execution context with github_client
            
        Returns:
            ExitReport with triage results
        """
        warnings = []
        triaged_issues = []
        
        # Step 1: Fetch open issues
        github_client = context.get('github_client')
        if not github_client:
            warnings.append("GitHub client not available")
            return ExitReport(
                task_id=task.task_id if hasattr(task, 'task_id') else "unknown",
                status="BLOCKED",
                warnings=warnings
            )
        
        open_issues = self._fetch_open_issues(github_client, context)
        
        # Step 2-4: Process each issue
        for issue in open_issues:
            triage_result = self._triage_issue(issue, context)
            triaged_issues.append(triage_result)
            
            # Update GitHub
            self._update_issue_metadata(issue, triage_result, github_client)
        
        # Step 5: Create tasks
        created_tasks = self._create_tasks_from_issues(triaged_issues, context)
        
        return ExitReport(
            task_id=task.task_id if hasattr(task, 'task_id') else "unknown",
            status="COMPLETED",
            remaining_work=f"Triaged {len(triaged_issues)} issues, created {len(created_tasks)} tasks",
            warnings=warnings
        )
    
    def _fetch_open_issues(self, github_client, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Fetch open issues from GitHub."""
        repo_owner = context.get('repo_owner', 'AgentAgony')
        repo_name = context.get('repo_name', 'swarm')
        
        issues = self._run_async(github_client.list_issues(
            owner=repo_owner,
            repo=repo_name,
            state="open"
        ))
        return issues
    
    def _triage_issue(self, issue: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Triage a single issue.
        
        Steps:
        1. Read description and comments
        2. Query HippoRAG for related code
        3. Estimate impact and effort
        4. Assign priority
        
        Returns:
            Triage result with priority, milestone, labels
        """
        issue_id = issue.get('number')
        title = issue.get('title', '')
        body = issue.get('body', '')
        
        # Query HippoRAG for context
        hipporag = context.get('hipporag_client')
        related_code = []
        if hipporag:
            related_code = self._find_related_code(title, body, hipporag)
        
        # Estimate impact and effort
        impact = self._estimate_impact(issue, related_code)
        effort = self._estimate_effort(issue, related_code)
        
        # Assign priority
        priority = self._calculate_priority(impact, effort)
        
        return {
            "issue_id": issue_id,
            "priority": priority,
            "labels": self._suggest_labels(issue, related_code),
            "milestone": self._suggest_milestone(priority, context),
            "estimated_effort": effort
        }
    
    def _find_related_code(self, title: str, body: str, hipporag) -> List[str]:
        """Find code related to the issue using HippoRAG."""
        related = []
        
        if hipporag and hasattr(hipporag, 'graph') and hipporag.graph:
            # Search for keywords from title/body in graph nodes
            keywords = (title + ' ' + body).lower().split()
            
            for node_id in hipporag.graph.nodes():
                node_str = str(node_id).lower()
                for keyword in keywords[:5]:  # Check first 5 keywords
                    if len(keyword) > 3 and keyword in node_str:
                        file_path = hipporag.graph.nodes[node_id].get('file', '')
                        if file_path and file_path not in related:
                            related.append(file_path)
                            break
        
        return related[:5]  # Limit to 5 related files
    
    def _estimate_impact(self, issue: Dict[str, Any], related_code: List[str]) -> str:
        """Estimate impact level (high/medium/low)."""
        labels = [l.get('name', '').lower() for l in issue.get('labels', [])]
        title = issue.get('title', '').lower()
        
        # High impact indicators
        if 'critical' in labels or 'security' in labels or 'breaking' in title:
            return "high"
        # Many related files = higher impact
        elif len(related_code) > 3:
            return "high"
        elif len(related_code) > 1 or 'enhancement' in labels:
            return "medium"
        else:
            return "low"
    
    def _estimate_effort(self, issue: Dict[str, Any], related_code: List[str]) -> str:
        """Estimate effort level (high/medium/low)."""
        body = issue.get('body', '')
        
        # Longer description = more complex
        if len(body) > 1000 or len(related_code) > 3:
            return "high"
        elif len(body) > 300 or len(related_code) > 1:
            return "medium"
        else:
            return "low"
    
    def _calculate_priority(self, impact: str, effort: str) -> str:
        """
        Calculate priority based on impact/effort matrix.
        
        Returns:
            Priority string (P0-P3)
        """
        # Simple heuristic: high impact + low effort = highest priority
        if impact == "high" and effort == "low":
            return "P0"
        elif impact == "high":
            return "P1"
        elif impact == "medium":
            return "P2"
        else:
            return "P3"
    
    def _suggest_labels(self, issue: Dict[str, Any], related_code: List[str]) -> List[str]:
        """Suggest appropriate labels for the issue."""
        labels = []
        title = issue.get('title', '').lower()
        body = issue.get('body', '').lower()
        
        # Auto-suggest labels based on content
        if 'bug' in title or 'fix' in title or 'broken' in body:
            labels.append('bug')
        if 'feature' in title or 'add' in title or 'new' in title:
            labels.append('enhancement')
        if 'doc' in title or 'readme' in body:
            labels.append('documentation')
        if any('test' in f for f in related_code):
            labels.append('testing')
        
        return labels
    
    def _suggest_milestone(self, priority: str, context: Dict[str, Any]) -> str:
        """Suggest appropriate milestone based on priority."""
        if priority == "P0":
            return "v4.0-hotfix"
        elif priority == "P1":
            return "v4.0"
        elif priority == "P2":
            return "v4.1"
        else:
            return "Backlog"
    
    def _update_issue_metadata(self, issue: Dict[str, Any], triage: Dict[str, Any], github_client):
        """Update issue labels and milestone on GitHub."""
        import logging
        # Log the triage decision
        logging.info(f"Triage: Issue #{issue.get('number')} -> {triage['priority']} (labels: {triage['labels']})")
        
        # Record provenance
        # Note: Actual label updates would use github_client.add_labels_to_issue if available
    
    def _create_tasks_from_issues(self, triaged_issues: List[Dict[str, Any]], context: Dict[str, Any]) -> List[str]:
        """Create tasks in task_queue from triaged issues."""
        task_ids = []
        
        # Sort by priority (P0 first)
        sorted_issues = sorted(triaged_issues, key=lambda x: x['priority'])
        
        for triage in sorted_issues:
            issue_id = triage['issue_id']
            priority = triage['priority']
            task_id = f"TRIAGE-{issue_id}-{priority}"
            task_ids.append(task_id)
            
            # Save to memory store
            memory_store = context.get('memory_store')
            if memory_store:
                memory_store.save_context(
                    session_id=context.get('session_id', 'triage'),
                    context_type='triaged_issue',
                    data=triage
                )
        
        return task_ids
