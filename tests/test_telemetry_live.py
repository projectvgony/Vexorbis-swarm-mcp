
import sqlite3
import time
from pathlib import Path
from mcp_core.telemetry.collector import collector

def test_live_telemetry():
    """
    Test that the telemetry collector writes to the SQLite DB.
    """
    print("🧪 Starting Live Telemetry Test...")
    
    # 1. Define a tracked dummy function
    @collector.track_tool("test_dummy_tool")
    def dummy_tool(x: int):
        print(f"   Executing dummy_tool({x})...")
        time.sleep(0.1) # Simulate work
        return x * 2

    # 2. Get initial count
    db_path = Path.home() / ".swarm" / "telemetry.db"
    initial_count = 0
    if db_path.exists():
        with sqlite3.connect(db_path) as conn:
            initial_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
    
    print(f"   Initial DB count: {initial_count}")

    # 3. Call the tool
    result = dummy_tool(21)
    assert result == 42
    
    # 4. Verify DB update
    assert db_path.exists(), "DB file not created!"
    
    with sqlite3.connect(db_path) as conn:
        new_count = conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        latest_event = conn.execute("SELECT type, data FROM events ORDER BY timestamp DESC LIMIT 1").fetchone()

    print(f"   New DB count: {new_count}")
    
    assert new_count > initial_count, "DB count did not increase!"
    assert latest_event[0] == "tool_use", "Event type incorrect"
    print(f"   Latest Event Data: {latest_event[1][:100]}...")
    
    print("✅ Live Telemetry Test Passed!")

if __name__ == "__main__":
    test_live_telemetry()
