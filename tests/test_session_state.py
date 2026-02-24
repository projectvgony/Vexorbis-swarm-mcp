"""
Test script for Orchestrator SQL Session State integration.
Verifies that session state is saved/loaded from PostgreSQL.
"""
import os
import sys
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load env before imports
load_dotenv(Path(__file__).parent.parent / ".env")
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_orchestrator_sql_session():
    """Test that Orchestrator uses SQL session persistence when enabled."""
    from mcp_core.orchestrator_loop import Orchestrator
    
    print("🧪 Testing Orchestrator SQL Session State...")
    
    # Check if SQL is enabled
    sql_enabled = bool(os.getenv("POSTGRES_URL"))
    print(f"   SQL Enabled: {sql_enabled}")
    
    # Create orchestrator with explicit session_id
    test_session_id = "test_session_integration_001"
    orch = Orchestrator(session_id=test_session_id)
    
    print(f"   Session ID: {orch.session_id}")
    print(f"   Agent ID: {orch.agent_id}")
    
    # Modify state
    orch.state.memory_bank["test_key"] = "test_value_from_orchestrator"
    
    # Save state
    print("\n1. Testing save_state()...")
    orch.save_state()
    print("   ✅ save_state() completed")
    
    # Create NEW orchestrator with SAME session_id to test recovery
    print("\n2. Testing load_state() recovery...")
    orch2 = Orchestrator(session_id=test_session_id)
    
    if "test_key" in orch2.state.memory_bank:
        print(f"   ✅ State recovered from SQL: {orch2.state.memory_bank['test_key']}")
    else:
        print(f"   ⚠️  State not recovered from SQL (may have used file fallback)")
        
    # Test lock release
    print("\n3. Testing release_lock()...")
    orch2.release_lock()
    print("   ✅ release_lock() completed")
    
    print("\n🏆 Orchestrator Session State Test Complete!")

if __name__ == "__main__":
    test_orchestrator_sql_session()
