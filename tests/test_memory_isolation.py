import shutil
from pathlib import Path
from fastmcp import FastMCP
import sys
import pytest
import asyncio

# Add swarm root to path so we can import the worker
import os
SWARM_ROOT = Path(os.getcwd())
sys.path.insert(0, str(SWARM_ROOT))

from mcp_core.tools.dynamic import memory_worker

# Setup Test Environment
TEST_SESSION_ID = "test_verification_session"
SESSION_ROOT = SWARM_ROOT / "docs" / "sessions" / TEST_SESSION_ID
GLOBAL_PLAN = SWARM_ROOT / "docs" / "ai" / "ROADMAP.md"

@pytest.fixture(autouse=True)
def manage_test_env():
    """Setup and teardown the test session environment."""
    if SESSION_ROOT.exists():
        shutil.rmtree(SESSION_ROOT)
    yield
    if SESSION_ROOT.exists():
        shutil.rmtree(SESSION_ROOT)

@pytest.mark.anyio
def test_isolation():
    print("🔍 Testing Memory Isolation...")
    
    # 1. Initialize MCP for side effects (if any), but import logic directly
    # mcp = FastMCP("test_memory") 
    # memory_worker.register(mcp)
    
    # Import logic directly
    from mcp_core.tools.dynamic.memory_worker import _orient_context, _refresh_memory, _claim_task, _merge_session
    
    orient = _orient_context
    refresh = _refresh_memory
    claim = _claim_task
    merge = _merge_session
    
    # 2. Test Global Behavior
    print("\n--- Testing Global Context ---")
    global_res = orient()
    assert "Roadmap Snapshot" in global_res
    print("✅ Global context reads correct PLAN.md")
    
    # 3. Test Session Initialization
    print(f"\n--- Testing Session Context ({TEST_SESSION_ID}) ---")
    session_res = orient(session_id=TEST_SESSION_ID)
    
    print(f"DEBUG: Checking {SESSION_ROOT}")
    assert SESSION_ROOT.exists(), "Session root not created"
    assert (SESSION_ROOT / "PLAN.md").exists(), "Session plan not copied"
    
    print("✅ Session context created and reads isolated PLAN.md")
    
    # 4. Test Locking (Claim Task)
    print("\n--- Testing Claim Task ---")
    import time
    unique_task = f"New Test Task {int(time.time())}"
    # Add a dummy task to global plan first
    original_plan = GLOBAL_PLAN.read_text(encoding="utf-8")
    GLOBAL_PLAN.write_text(original_plan + f"\n- [ ] {unique_task}", encoding="utf-8")
    
    # Claim it
    claim_res = claim(session_id=TEST_SESSION_ID, task_description=unique_task)
    print(f"Claim Result: {claim_res}")
    assert "✅ Task claimed" in claim_res
    
    # Verify Global Plan updated
    updated_plan = GLOBAL_PLAN.read_text(encoding="utf-8")
    assert f"[/] {unique_task} (claimed by {TEST_SESSION_ID})" in updated_plan
    print("✅ Global plan updated with claim")
    
    # Verify Session Plan updated (sync)
    sess_plan = (SESSION_ROOT / "PLAN.md").read_text(encoding="utf-8")
    assert f"[/] {unique_task} (claimed by {TEST_SESSION_ID})" in sess_plan
    print("✅ Session plan synced after claim")
    
    # 5. Test Drift Detection
    print("\n--- Testing Drift Detection ---")
    # Modify global plan "behind the back"
    GLOBAL_PLAN.write_text(updated_plan + "\n- [ ] Surprise Task", encoding="utf-8")
    
    drift_res = orient(session_id=TEST_SESSION_ID)
    assert "WARNING: Global PLAN.md has changed" in drift_res
    print("✅ Drift warning detected")
    
    # 6. Test Merge Session
    print("\n--- Testing Merge Session ---")
    merge_res = asyncio.run(merge(session_id=TEST_SESSION_ID))
    print(f"Merge Result: {merge_res}")
    assert "Session merged" in merge_res
    
    # Verify Global Plan marked completed
    final_plan = GLOBAL_PLAN.read_text(encoding="utf-8")
    # Should find [x] New Test Task (without claim tag)
    assert f"[x] {unique_task}" in final_plan
    assert "(claimed by" not in final_plan
    print("✅ Global plan updated with completion")
    
    # Cleanup Global Plan (restore)
    GLOBAL_PLAN.write_text(original_plan, encoding="utf-8")

    print("\n🏆 Verification Successful: Overlap Management Works!")


