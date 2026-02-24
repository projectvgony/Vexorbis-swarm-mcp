"""
GitRoleDispatcher: Central coordinator for role-based Git operations.
"""

import logging
from typing import List, Dict, Any, Optional
from mcp_core.swarm_schemas import Task
from mcp_core.algorithms.git_roles import GitRole, ExitReport, HandoffProtocol
from mcp_core.algorithms.git_roles.feature_scout import FeatureScoutRole
from mcp_core.algorithms.git_roles.code_auditor import CodeAuditorRole
from mcp_core.algorithms.git_roles.issue_triage import IssueTriageRole
from mcp_core.algorithms.git_roles.branch_manager import BranchManagerRole
from mcp_core.algorithms.git_roles.project_lifecycle import ProjectLifecycleRole
from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService


class GitRoleDispatcher:
    """
    Central dispatcher for autonomous Git agent roles.
    """
    
    def __init__(self, orchestrator):
        self.orchestrator = orchestrator
        self.roles = {
            GitRole.FEATURE_SCOUT: FeatureScoutRole(),
            GitRole.CODE_AUDITOR: CodeAuditorRole(),
            GitRole.ISSUE_TRIAGE: IssueTriageRole(),
            GitRole.BRANCH_MANAGER: BranchManagerRole(),
            GitRole.PROJECT_LIFECYCLE: ProjectLifecycleRole()
        }
        self.analytics = TelemetryAnalyticsService()
    
    def dispatch(self, task: Task) -> List[ExitReport]:
        """
        Execute all triggered roles for the given task.
        Includes self-healing: skips failing roles, records outcomes.
        """
        from mcp_core.telemetry.self_healing import self_healing_monitor
        
        reports = []
        context = self._prepare_context(task)
        
        # Self-healing: Check system health before dispatch
        health = self_healing_monitor.check_health()
        if health.status.value == 'critical':
            logging.warning(f"⚠️ System health CRITICAL. {len(health.recommended_actions)} healing actions pending.")
        
        execution_order = self._get_optimized_execution_order()
        
        for role_key in execution_order:
            role = self.roles[role_key]
            
            # Self-healing: Skip role if circuit breaker tripped
            if self_healing_monitor.should_skip_role(role_key.value):
                logging.warning(f"🔴 Skipping {role_key.value} - circuit breaker tripped")
                reports.append(ExitReport(
                    task_id=task.task_id,
                    status="SKIPPED",
                    warnings=["Skipped due to low performance index"]
                ))
                continue
            
            if role.trigger_check(task, context):
                logging.info(f"🚀 Dispatching Git Role: {role_key.value}")
                try:
                    report = role.execute(task, context)
                    reports.append(report)
                    
                    # Self-healing: Record success
                    self_healing_monitor.record_success(role_key.value)
                    logging.info(f"✅ {role_key.value} completed with status: {report.status}")
                except Exception as e:
                    logging.error(f"❌ {role_key.value} failed: {e}")
                    
                    # Self-healing: Record failure
                    self_healing_monitor.record_failure(role_key.value, str(e))
                    
                    reports.append(ExitReport(
                        task_id=task.task_id,
                        status="FAILED",
                        warnings=[str(e)]
                    ))
        
        return reports

    def _get_optimized_execution_order(self) -> List[GitRole]:
        """
        [V3.8: Adaptive Telemetry] Performance Index scoring.
        PI = (SuccessRate * 0.7) + (SpeedScore * 0.3)
        High-PI roles run first.
        """
        default_order = [
            GitRole.PROJECT_LIFECYCLE,
            GitRole.ISSUE_TRIAGE,
            GitRole.FEATURE_SCOUT,
            GitRole.CODE_AUDITOR,
            GitRole.BRANCH_MANAGER
        ]
        
        # Calculate Performance Index for each role
        scored_roles = []
        for role_key in default_order:
            role_name = role_key.value
            pi = self.analytics.get_performance_index(role_name)
            scored_roles.append((role_key, pi))
            logging.debug(f"Role {role_name}: PI = {pi:.2f}")
            
        # Sort by PI (descending - higher is better)
        scored_roles.sort(key=lambda x: x[1], reverse=True)
        logging.info(f"🎯 PI-optimized order: {[r[0].value for r in scored_roles]}")
        
        return [r[0] for r in scored_roles]
    
    def _prepare_context(self, task: Task) -> Dict[str, Any]:
        """
        Prepare execution context for roles.
        Merges active_context (memory_bank) into top-level for easier access.
        """
        from mcp_core.telemetry.collector import collector
        from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService
        from mcp_core.telemetry.memory_store import memory_store
        from mcp_core.telemetry.self_healing import self_healing_monitor
        
        active_context = self.orchestrator.state.active_context or {}
        context = {
            "memory_bank": active_context,
            "hipporag_client": self.orchestrator.rag,
            "github_client": getattr(self.orchestrator, 'github_client', None),
            "git_worker": self.orchestrator.git,
            "orchestrator": self.orchestrator,
            "telemetry_collector": collector,
            "telemetry_analytics": TelemetryAnalyticsService(),
            "memory_store": memory_store,
            "self_healing": self_healing_monitor
        }
        # Merge active_context keys into top-level for convenience in trigger_check
        context.update(active_context)
        return context
