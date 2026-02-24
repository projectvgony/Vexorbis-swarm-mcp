"""
SelfHealingMonitor: Autonomous failure detection and recovery.

Uses telemetry history to detect patterns and trigger corrective actions.
"""

import logging
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum

from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService
from mcp_core.telemetry.collector import collector
from mcp_core.telemetry.events import EventType

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"


@dataclass
class HealingAction:
    """A corrective action to take."""
    action_type: str  # 'skip_role', 'retry', 'fallback', 'alert'
    target: str  # Role name, tool name, or file path
    reason: str
    priority: int = 1


@dataclass
class SystemHealth:
    """Current health snapshot."""
    status: HealthStatus
    problematic_tools: List[str] = field(default_factory=list)
    failed_roles: List[str] = field(default_factory=list)
    recommended_actions: List[HealingAction] = field(default_factory=list)


class SelfHealingMonitor:
    """
    Monitors system health and recommends corrective actions.
    
    Self-Healing Capabilities:
    1. Circuit Breaker: Skip failing roles/tools temporarily
    2. Retry Logic: Suggest retries with backoff
    3. Fallback: Route to alternative implementations
    4. Pattern Detection: Identify chronic issues for FeatureScout
    """
    
    def __init__(self):
        self.analytics = TelemetryAnalyticsService()
        self.circuit_breakers: Dict[str, int] = {}  # target -> failure count
        self.trip_threshold = 3  # Failures before tripping
        self._memory_store = None  # Lazy load to avoid circular import
    
    @property
    def memory_store(self):
        if self._memory_store is None:
            from mcp_core.telemetry.memory_store import memory_store
            self._memory_store = memory_store
        return self._memory_store
    
    def check_health(self) -> SystemHealth:
        """
        Perform comprehensive health check.
        Returns current system health status and recommendations.
        """
        problematic_tools = []
        failed_roles = []
        actions = []
        
        # 1. Check tool success rates
        tools_with_issues = self.analytics.get_problematic_tools(threshold=0.7, window_days=1)
        for tool_info in tools_with_issues:
            tool_name = tool_info['tool']
            success_rate = tool_info['success_rate']
            problematic_tools.append(tool_name)
            
            # Check circuit breaker status
            status = self.analytics.get_tool_status(tool_name)
            if status == "TRIPPED":
                actions.append(HealingAction(
                    action_type="skip_tool",
                    target=tool_name,
                    reason=f"Tool circuit breaker tripped ({success_rate:.0%} success)",
                    priority=1
                ))
            elif status == "WARNING":
                actions.append(HealingAction(
                    action_type="retry_with_backoff",
                    target=tool_name,
                    reason=f"Tool degraded ({success_rate:.0%} success)",
                    priority=2
                ))
        
        # 2. Check Git role performance
        git_roles = ['feature_scout', 'code_auditor', 'issue_triage', 'branch_manager']
        for role in git_roles:
            pi = self.analytics.get_performance_index(role)
            if pi < 0.5:  # Low performance index
                failed_roles.append(role)
                actions.append(HealingAction(
                    action_type="skip_role",
                    target=role,
                    reason=f"Role has low performance index ({pi:.2f})",
                    priority=2
                ))
        
        # 3. Check memory for failure patterns
        failure_patterns = self.memory_store.get_failure_patterns(window_hours=24)
        for pattern in failure_patterns[:3]:  # Top 3 chronic issues
            actions.append(HealingAction(
                action_type="create_issue",
                target=pattern['target'],
                reason=f"Chronic failure: {pattern['failure_count']} failures in 24h",
                priority=3
            ))
        
        # Determine overall status
        if len(problematic_tools) >= 3 or len(failed_roles) >= 2:
            status = HealthStatus.CRITICAL
        elif problematic_tools or failed_roles:
            status = HealthStatus.DEGRADED
        else:
            status = HealthStatus.HEALTHY
        
        return SystemHealth(
            status=status,
            problematic_tools=problematic_tools,
            failed_roles=failed_roles,
            recommended_actions=sorted(actions, key=lambda x: x.priority)
        )
    
    def should_skip_role(self, role_name: str) -> bool:
        """Check if a role should be skipped due to circuit breaker."""
        pi = self.analytics.get_performance_index(role_name)
        return pi < 0.3  # Very low performance
    
    def record_failure(self, target: str, error: str):
        """Record a failure for circuit breaker logic."""
        self.circuit_breakers[target] = self.circuit_breakers.get(target, 0) + 1
        
        # Log to telemetry
        from mcp_core.telemetry.events import TelemetryEvent
        event = TelemetryEvent(
            session_id=collector.session_id,
            install_id=collector.install_id,
            type=EventType.ERROR,
            tool_name=target,
            success=False,
            error_category=error[:50]
        )
        collector.buffer.add_event(event)
    
    def record_success(self, target: str):
        """Record a success, reducing circuit breaker count."""
        if target in self.circuit_breakers:
            self.circuit_breakers[target] = max(0, self.circuit_breakers[target] - 1)
    
    def get_healing_summary(self) -> str:
        """Get a human-readable health summary."""
        health = self.check_health()
        
        status_emoji = {
            HealthStatus.HEALTHY: "🟢",
            HealthStatus.DEGRADED: "🟡",
            HealthStatus.CRITICAL: "🔴"
        }
        
        lines = [f"{status_emoji[health.status]} System Status: {health.status.value.upper()}"]
        
        if health.problematic_tools:
            lines.append(f"⚠️ Degraded tools: {', '.join(health.problematic_tools)}")
        
        if health.failed_roles:
            lines.append(f"⚠️ Struggling roles: {', '.join(health.failed_roles)}")
        
        if health.recommended_actions:
            lines.append("📋 Recommended actions:")
            for action in health.recommended_actions[:5]:
                lines.append(f"   - [{action.action_type}] {action.target}: {action.reason}")
        
        return "\n".join(lines)


# Global monitor instance
self_healing_monitor = SelfHealingMonitor()
