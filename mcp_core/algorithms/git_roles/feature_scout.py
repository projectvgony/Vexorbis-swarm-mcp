"""
FeatureScoutRole: Autonomous feature discovery and proposal.

This role scans the codebase for improvement opportunities, gaps in functionality,
and TODOs, then generates structured feature proposals.
"""

from typing import Any, Dict
from .base import GitAgentRole, GitRole, ExitReport


class FeatureScoutRole(GitAgentRole):
    """
    Autonomous feature discovery agent.
    
    Responsibilities:
    - Analyze memory_bank for recent patterns and gaps
    - Query HippoRAG for underdeveloped modules or TODOs
    - Generate structured feature proposals
    - Create issues.md entries or GitHub issues
    - Log AuthorSignature with role 'feature_scout'
    """
    
    def __init__(self):
        super().__init__(GitRole.FEATURE_SCOUT)
    
    def trigger_check(self, task: Any, context: Dict[str, Any]) -> bool:
        """
        Trigger when feature_discovery flag is set or periodic scan is requested.
        
        Args:
            task: Task object
            context: Execution context
            
        Returns:
            True if feature discovery should run
        """
        # Check for explicit feature_discovery flag
        if hasattr(task, 'feature_discovery') and task.feature_discovery:
            return True
        
        # Check for periodic trigger in context
        if context.get('periodic_feature_scan', False):
            return True
        
        return False
    
    def execute(self, task: Any, context: Dict[str, Any]) -> ExitReport:
        """
        Execute feature discovery workflow.
        
        Steps:
        1. Analyze memory_bank for gaps
        2. Query HippoRAG for TODOs and underdeveloped areas
        3. Generate feature proposals
        4. Create issues or tasks
        5. Log provenance
        
        Args:
            task: Task object
            context: Execution context with memory_bank, hipporag, etc.
            
        Returns:
            ExitReport with discovered features
        """
        warnings = []
        discovered_features = []
        
        # Step 1: Analyze memory_bank
        memory_bank = context.get('memory_bank', {})
        recent_events = memory_bank.get('recent_events', [])
        
        # Look for patterns of repeated issues or gaps
        patterns = self._analyze_patterns(recent_events)
        
        # Step 2: Query HippoRAG for code analysis
        hipporag = context.get('hipporag_client')
        if hipporag:
            # Search for TODO comments
            todos = self._find_todos(hipporag)
            
            # Identify underdeveloped modules (low PageRank, few connections)
            underdeveloped = self._find_underdeveloped_modules(hipporag)
            
            discovered_features.extend(todos)
            discovered_features.extend(underdeveloped)
        else:
            warnings.append("HippoRAG client not available - skipping code analysis")
        
        # Step 3: Generate structured proposals
        proposals = []
        for feature_idea in discovered_features:
            proposal = self._generate_proposal(feature_idea, context)
            proposals.append(proposal)
        
        # Step 4: Create issues
        issues_created = []
        github_client = context.get('github_client')
        repo_owner = context.get('repo_owner', 'AgentAgony') # Default to current repo
        repo_repo = context.get('repo_name', 'swarm')

        for proposal in proposals:
            if github_client:
                issue = self._run_async(github_client.create_issue(
                    owner=repo_owner,
                    repo=repo_repo,
                    title=f"[Feature] {proposal['title']}",
                    body=proposal.get('rationale', 'No description provided'),
                    labels=["enhancement", "auto-generated"]
                ))
                if issue:
                    issues_created.append(f"#{issue.get('number')}")
            else:
                issue_id = self._create_issue(proposal, context)
                if issue_id:
                    issues_created.append(issue_id)
        
        # Step 5: Log provenance
        self._log_provenance(task, proposals, context)
        
        return ExitReport(
            task_id=task.task_id if hasattr(task, 'task_id') else "unknown",
            status="COMPLETED",
            files_touched=[],
            remaining_work=f"Created {len(issues_created)} feature proposals: {', '.join(issues_created)}",
            warnings=warnings
        )
    
    def _analyze_patterns(self, events: list) -> list:
        """Analyze recent events for patterns indicating missing features."""
        patterns = []
        
        # Use telemetry analytics if available in context
        try:
            from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService
            analytics = TelemetryAnalyticsService()
            
            # Find problematic tools (low success rate)
            problematic = analytics.get_problematic_tools(threshold=0.7, window_days=7)
            for tool_info in problematic:
                patterns.append({
                    "title": f"Improve reliability of {tool_info['tool']}",
                    "file": "mcp_core/tools/",
                    "rationale": f"Tool has {tool_info['success_rate']:.1%} success rate over last 7 days (used {tool_info['total_uses']} times)"
                })
            
            # Analyze events for high-frequency errors
            error_counts = {}
            for event in events:
                if isinstance(event, dict) and event.get('type') == 'error':
                    file_path = event.get('file', 'unknown')
                    error_counts[file_path] = error_counts.get(file_path, 0) + 1
            
            # Files with multiple recent errors are refactoring candidates
            for file_path, count in error_counts.items():
                if count >= 3:
                    patterns.append({
                        "title": f"Refactor error-prone code in {file_path}",
                        "file": file_path,
                        "rationale": f"File has {count} recent errors, may need refactoring"
                    })
        except Exception as e:
            # Telemetry not available, skip pattern analysis
            pass
        
        return patterns[:5]  # Limit to top 5 patterns
    
    def _find_todos(self, hipporag) -> list:
        """Search codebase for TODO comments."""
        import subprocess
        from pathlib import Path
        
        todos = []
        
        # Use grep to find TODO and FIXME comments
        try:
            # Search for TODO patterns in Python files
            result = subprocess.run(
                ['grep', '-rn', '--include=*.py', '-E', '(TODO|FIXME):', '.'],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
                timeout=10
            )
            
            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    # Parse grep output: filename:line_number:content
                    parts = line.split(':', 2)
                    if len(parts) >= 3:
                        file_path, line_num, content = parts
                        todos.append({
                            "title": f"TODO in {Path(file_path).name}",
                            "file": file_path,
                            "line": line_num,
                            "rationale": content.strip()
                        })
        except (subprocess.TimeoutExpired, FileNotFoundError) as e:
            # grep not available or timeout - fallback to manual search
            pass
        
        return todos[:10]  # Limit to top 10 to avoid overwhelming
    
    def _find_underdeveloped_modules(self, hipporag) -> list:
        """Identify modules with low connectivity or missing documentation."""
        underdeveloped = []
        
        if not hipporag or not hasattr(hipporag, 'graph') or hipporag.graph is None:
            return []
        
        try:
            graph = hipporag.graph
            
            # Find nodes with low out-degree (functions/classes that call nothing)
            for node_id in graph.nodes():
                out_degree = graph.out_degree(node_id)
                
                # If a function/class has no outgoing calls, it might be:
                # 1. A stub/placeholder
                # 2. Missing implementation
                # 3. An orphaned utility
                if out_degree == 0:
                    node_data = graph.nodes[node_id]
                    node_type = node_data.get('type', '')
                    
                    # Focus on functions and classes, skip simple variables
                    if node_type in ['function', 'class', 'method']:
                        file_path = node_data.get('file', '')
                        if file_path and 'test' not in file_path:  # Skip test files
                            underdeveloped.append({
                                "title": f"Underdeveloped: {node_id.split(':')[-1]}",
                                "file": file_path,
                                "line": node_data.get('line', 0),
                                "rationale": f"Low connectivity ({node_type} with no outgoing calls)"
                            })
        except Exception as e:
            # Graph analysis failed, return empty
            pass
        
        return underdeveloped[:5]  # Limit to top 5
    
    def _generate_proposal(self, feature_idea: dict, context: Dict[str, Any]) -> dict:
        """
        Generate a structured feature proposal.
        
        Returns:
            Proposal dict with title, rationale, complexity, breakdown
        """
        from mcp_core.llm import generate_response
        
        title = feature_idea.get("title", "Untitled Feature")
        file_path = feature_idea.get("file", "")
        rationale = feature_idea.get("rationale", "")
        
        # Use LLM to enrich the proposal
        prompt = f"""You are a software architect analyzing a codebase improvement opportunity.

Feature Idea: {title}
Location: {file_path}
Context: {rationale}

Generate a structured feature proposal with:
1. A clear, concise title
2. A detailed rationale (2-3 sentences)
3. Estimated complexity (low/medium/high)
4. 2-3 specific implementation sub-tasks

Format as JSON:
{{
  "title": "...",
  "rationale": "...",
  "estimated_complexity": "...",
  "sub_tasks": ["...", "..."]
}}
"""
        
        try:
            response = generate_response(prompt, temperature=0.7, max_tokens=500)
            # Try to parse JSON from response
            import json
            import re
            
            # Extract JSON from markdown code blocks if present
            json_match = re.search(r'```(?:json)?\s*({.*?})\s*```', response, re.DOTALL)
            if json_match:
                proposal = json.loads(json_match.group(1))
            else:
                # Try to parse the whole response as JSON
                proposal = json.loads(response)
            
            return proposal
        except Exception as e:
            # Fallback to basic proposal if LLM fails
            return {
                "title": title,
                "rationale": rationale or "Identified via automated codebase scan.",
                "estimated_complexity": "medium",
                "sub_tasks": []
            }
    
    def _create_issue(self, proposal: dict, context: Dict[str, Any]) -> str:
        """
        Create an issue in issues.md or GitHub.
        
        Returns:
            Issue/task ID if created, None otherwise
        """
        from pathlib import Path
        from datetime import datetime
        
        # Append to issues.md (fallback when GitHub is unavailable)
        issues_file = Path("docs/ai/issues.md")
        
        try:
            # Ensure parent directory exists
            issues_file.parent.mkdir(parents=True, exist_ok=True)
            
            # Create header if file doesn't exist
            if not issues_file.exists():
                issues_file.write_text("# Feature Proposals\n\n", encoding='utf-8')
            
            # Generate unique ID
            issue_id = f"FEATURE-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            
            # Format issue entry
            issue_entry = f"""## {issue_id}: {proposal['title']}

**Status**: Proposed  
**Complexity**: {proposal.get('estimated_complexity', 'medium')}  
**Created**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

### Rationale
{proposal.get('rationale', 'No rationale provided')}

### Sub-Tasks
{chr(10).join(f"- [ ] {task}" for task in proposal.get('sub_tasks', []))}

---

"""
            
            # Append to file
            with open(issues_file, 'a', encoding='utf-8') as f:
                f.write(issue_entry)
            
            return issue_id
        except Exception as e:
            return None
    
    def _log_provenance(self, task: Any, proposals: list, context: Dict[str, Any]):
        """Log AuthorSignature to provenance_log."""
        try:
            from mcp_core.telemetry.collector import collector
            
            # Record provenance for each proposal
            for proposal in proposals:
                signature = collector.record_provenance(
                    agent_id="feature_scout",
                    role="feature_scout",
                    action="feature_proposed",
                    contributing_model=context.get('llm_model', 'unknown'),
                    artifact_ref=proposal.get('title', 'untitled')
                )
                
                # Attach signature to context for state containment
                if 'provenance_signatures' not in context:
                    context['provenance_signatures'] = []
                context['provenance_signatures'].append(signature)
        except Exception as e:
            # Telemetry not available, skip provenance logging
            pass
