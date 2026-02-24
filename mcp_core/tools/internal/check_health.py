"""
Internal Health Check Tool

System diagnostic for Swarm's self-maintenance.
Queries telemetry.db and reports on tool reliability.
"""

from typing import Dict, Any
from pathlib import Path

def check_health() -> str:
    """
    Comprehensive health check for the Swarm system.
    
    **Usage Heuristics**:
    - Use when debugging system-level issues
    - Run periodically to catch problems early
    - Check before major operations
    
    Internal Tool: Only available when SWARM_INTERNAL_TOOLS=true
    
    Returns:
        Formatted health report with telemetry stats and system status
    """
    from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService
    import os
    
    analytics = TelemetryAnalyticsService()
    report_lines = ["🏥 Swarm System Health Check\n"]
    
    # 1. Telemetry Database Status
    db_path = Path.home() / ".swarm" / "telemetry.db"
    if db_path.exists():
        db_size_mb = db_path.stat().st_size / (1024 * 1024)
        report_lines.append(f"✅ Telemetry DB: {db_size_mb:.2f} MB")
        
        # Check for problematic tools
        problems = analytics.get_problematic_tools(threshold=0.7, window_days=3)
        if problems:
            report_lines.append(f"\n⚠️  Found {len(problems)} tools with low success rates:")
            for p in problems:
                report_lines.append(f"   - {p['tool']}: {p['success_rate']:.1%} ({p['total_uses']} uses)")
        else:
            report_lines.append("✅ All tools performing well (>70% success)")
    else:
        report_lines.append("⚪ Telemetry DB: Not initialized (first run)")
    
    # 2. PostgreSQL Status
    try:
        pg_url = os.environ.get("POSTGRES_URL")
        if pg_url:
            report_lines.append("✅ PostgreSQL: Configured (URL present)")
        else:
            report_lines.append("⚠️  PostgreSQL: Not configured (POSTGRES_URL missing)")
    except Exception as e:
        report_lines.append(f"❌ PostgreSQL: {str(e)[:50]}")
    
    # 3. Environment Info
    is_docker = os.environ.get("IS_DOCKER") == "1"
    debug_mode = os.environ.get("SWARM_DEBUG", "false").lower() == "true"
    
    report_lines.append(f"\n📊 Environment:")
    report_lines.append(f"   Container: {'Yes' if is_docker else 'No'}")
    report_lines.append(f"   Debug Mode: {'On' if debug_mode else 'Off'}")
    
    return "\n".join(report_lines)


def register(mcp):
    """Register this tool with the FastMCP server."""
    mcp.tool()(check_health)
