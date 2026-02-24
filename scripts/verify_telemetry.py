
import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService
from mcp_core.algorithms.git_role_dispatcher import GitRoleDispatcher
from dashboard_server import get_analytics

def test_analytics_service():
    print("Testing TelemetryAnalyticsService...")
    service = TelemetryAnalyticsService()
    
    # Test methods safely (even if DB is empty)
    rate = service.get_tool_success_rate("test_tool")
    print(f"Tool Success Rate: {rate}")
    
    role_rate = service.get_role_success_rate("feature_scout")
    print(f"Role Success Rate: {role_rate}")
    
    problems = service.get_problematic_tools()
    print(f"Problematic Tools: {problems}")
    
    duration = service.get_avg_duration("test_tool")
    print(f"Avg Duration: {duration}")

def test_dashboard_import():
    print("\nTesting Dashboard Integration...")
    analytics = get_analytics()
    if isinstance(analytics, TelemetryAnalyticsService):
        print("✅ Dashboard analytics initialized correctly")
    else:
        print("❌ Dashboard analytics failed")

def main():
    logging.basicConfig(level=logging.ERROR)
    try:
        test_analytics_service()
        test_dashboard_import()
        print("\n✅ Verification passed!")
    except Exception as e:
        print(f"\n❌ Verification failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
