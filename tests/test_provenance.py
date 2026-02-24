
import sqlite3
import json
from pathlib import Path
from mcp_core.telemetry.collector import collector
from mcp_core.swarm_schemas import AuthorSignature

def test_provenance_recording():
    """
    Test that record_provenance creates a signature and logs to DB.
    """
    print("🧪 Starting Provenance Test...")
    
    # 1. Record a dummy provenance event
    agent_id = "agent-test-001"
    role = "engineer"
    action = "modified"
    artifact_ref = "test_file.py"
    
    signature = collector.record_provenance(
        agent_id=agent_id,
        role=role,
        action=action,
        artifact_ref=artifact_ref
    )
    
    # 2. Verify Return Object
    assert isinstance(signature, AuthorSignature)
    assert signature.agent_id == agent_id
    assert signature.role == role
    assert signature.action == action
    print("✅ Signature object structure valid")

    # 3. Verify DB Persistance
    db_path = Path.home() / ".swarm" / "telemetry.db"
    assert db_path.exists()
    
    with sqlite3.connect(db_path) as conn:
        # Get the latest provenance event
        row = conn.execute(
            "SELECT type, data FROM events WHERE type='provenance' ORDER BY timestamp DESC LIMIT 1"
        ).fetchone()
        
    assert row is not None, "No provenance event found in DB"
    event_type, data_json = row
    data = json.loads(data_json)
    
    assert event_type == "provenance"
    properties = data.get("properties", {})
    
    assert properties["agent_id"] == agent_id
    assert properties["artifact_ref"] == artifact_ref
    assert properties["role"] == role
    
    print(f"✅ DB Event verified: {properties}")

if __name__ == "__main__":
    test_provenance_recording()
