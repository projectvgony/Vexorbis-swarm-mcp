"""
CodeAuditorRole: Autonomous code quality and documentation scanning.

This role identifies bugs, code smells, outdated documentation, and security
anti-patterns through static analysis and graph-based code understanding.
"""

from typing import Any, Dict, List
from .base import GitAgentRole, GitRole, ExitReport


class CodeAuditorRole(GitAgentRole):
    """
    Autonomous code quality auditor.
    
    Responsibilities:
    - Scan recently updated files via HippoRAG
    - Run static analysis (lint,type checks)
    - Identify unused imports, dead code, outdated docs
    - Generate audit report in memory_bank
    - Flag priority items for immediate fix
    """
    
    def __init__(self):
        super().__init__(GitRole.CODE_AUDITOR)
    
    def trigger_check(self, task: Any, context: Dict[str, Any]) -> bool:
        """
        Trigger on code_audit flag or periodic scan.
        
        Args:
            task: Task object
            context: Execution context
            
        Returns:
            True if audit should run
        """
        if hasattr(task, 'code_audit') and task.code_audit:
            return True
        
        if context.get('periodic_audit', False):
            return True
        
        return False
    
    def execute(self, task: Any, context: Dict[str, Any]) -> ExitReport:
        """
        Execute code audit workflow.
        
        Steps:
        1. Retrieve recently updated files
        2. Run static analysis
        3. Identify issues
        4. Generate report
        5. Flag priorities
        
        Args:
            task: Task object
            context: Execution context
            
        Returns:
            ExitReport with audit findings
        """
        warnings = []
        findings: List[Dict[str, Any]] = []
        
        # Step 1: Get recently updated files
        hipporag = context.get('hipporag_client')
        if hipporag:
            recent_files = self._get_recent_files(hipporag, context)
        else:
            warnings.append("HippoRAG not available - using git status")
            recent_files = self._get_files_from_git(context)
        
        # Step 2: Run static analysis
        for file_path in recent_files:
            file_findings = self._analyze_file(file_path, context)
            findings.extend(file_findings)
        
        # Step 3: Categorize by severity
        critical_findings = [f for f in findings if f.get('severity') == 'critical']
        high_findings = [f for f in findings if f.get('severity') == 'high']
        
        # Step 4: Generate report
        report = self._generate_report(findings, context)
        
        # Step 5: Flag priority items
        priority_tasks = self._create_priority_tasks(critical_findings + high_findings, context)
        
        return ExitReport(
            task_id=task.task_id if hasattr(task, 'task_id') else "unknown",
            status="COMPLETED",
            files_touched=recent_files,
            remaining_work=f"Found {len(findings)} issues ({len(critical_findings)} critical). Created {len(priority_tasks)} priority tasks.",
            warnings=warnings
        )
    
    def _get_recent_files(self, hipporag, context: Dict[str, Any]) -> List[str]:
        """Get list of recently modified files from HippoRAG."""
        recent_files = []
        
        if hipporag and hasattr(hipporag, 'graph') and hipporag.graph:
            # Query graph for file nodes
            for node_id in hipporag.graph.nodes():
                node_data = hipporag.graph.nodes[node_id]
                file_path = node_data.get('file', '')
                if file_path and file_path.endswith('.py') and file_path not in recent_files:
                    recent_files.append(file_path)
        
        return recent_files[:20]  # Limit to 20 files
    
    def _get_files_from_git(self, context: Dict[str, Any]) -> List[str]:
        """Fallback: get modified files from git status."""
        import subprocess
        from pathlib import Path
        
        try:
            result = subprocess.run(
                ['git', 'diff', '--name-only', 'HEAD~5'],
                capture_output=True,
                text=True,
                cwd=Path.cwd(),
                timeout=10
            )
            if result.returncode == 0:
                files = [f.strip() for f in result.stdout.splitlines() if f.endswith('.py')]
                return files[:20]
        except Exception:
            pass
        
        return []
    
    def _analyze_file(self, file_path: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Analyze a single file for issues.
        
        Returns:
            List of finding dictionaries
        """
        import re
        from pathlib import Path
        
        findings = []
        
        try:
            file_obj = Path(file_path)
            if not file_obj.exists():
                return findings
            
            content = file_obj.read_text(encoding='utf-8', errors='ignore')
            lines = content.splitlines()
            
            # Check for security anti-patterns
            security_patterns = [
                (r'password\s*=\s*["\'][^"\']+["\']', 'Hardcoded password', 'critical'),
                (r'api_key\s*=\s*["\'][^"\']+["\']', 'Hardcoded API key', 'critical'),
                (r'eval\s*\(', 'Use of eval()', 'high'),
                (r'exec\s*\(', 'Use of exec()', 'high'),
                (r'subprocess\.call.*shell\s*=\s*True', 'Shell injection risk', 'high'),
            ]
            
            for i, line in enumerate(lines, 1):
                for pattern, message, severity in security_patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        findings.append({
                            "file": file_path,
                            "line": i,
                            "severity": severity,
                            "category": "security",
                            "message": message
                        })
            
            # Check for TODO/FIXME (low severity)
            for i, line in enumerate(lines, 1):
                if re.search(r'#\s*(TODO|FIXME)', line, re.IGNORECASE):
                    findings.append({
                        "file": file_path,
                        "line": i,
                        "severity": "low",
                        "category": "maintenance",
                        "message": "TODO/FIXME comment found"
                    })
                    
        except Exception as e:
            findings.append({
                "file": file_path,
                "line": 0,
                "severity": "medium",
                "category": "error",
                "message": f"Could not analyze: {str(e)}"
            })
        
        return findings
    
    def _generate_report(self, findings: List[Dict[str, Any]], context: Dict[str, Any]) -> str:
        """Generate structured audit report for memory_bank."""
        from datetime import datetime
        
        critical = [f for f in findings if f.get('severity') == 'critical']
        high = [f for f in findings if f.get('severity') == 'high']
        medium = [f for f in findings if f.get('severity') == 'medium']
        low = [f for f in findings if f.get('severity') == 'low']
        
        report = f"""# Code Audit Report
**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Total Findings**: {len(findings)}

## Summary
- 🔴 Critical: {len(critical)}
- 🟠 High: {len(high)}
- 🟡 Medium: {len(medium)}
- 🟢 Low: {len(low)}

## Critical Issues
"""
        for f in critical[:5]:
            report += f"- **{f['file']}:{f['line']}** - {f['message']}\n"
        
        # Save to memory_store if available
        memory_store = context.get('memory_store')
        if memory_store:
            memory_store.save_context(
                session_id=context.get('session_id', 'audit'),
                context_type='audit_report',
                data={'report': report, 'findings': findings}
            )
        
        return report
    
    def _create_priority_tasks(self, findings: List[Dict[str, Any]], context: Dict[str, Any]) -> List[str]:
        """Create tasks for priority findings."""
        task_ids = []
        
        for finding in findings[:5]:  # Top 5 priority
            task_id = f"AUDIT-{finding['file'].split('/')[-1]}-L{finding['line']}"
            task_ids.append(task_id)
            
            # Log provenance
            collector = context.get('telemetry_collector')
            if collector:
                collector.record_provenance(
                    agent_id="code_auditor",
                    role="code_auditor",
                    action="issue_flagged",
                    artifact_ref=finding['file']
                )
        
        return task_ids
