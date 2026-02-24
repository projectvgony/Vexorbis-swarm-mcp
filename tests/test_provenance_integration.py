
import os
import json
import unittest
from unittest.mock import MagicMock, patch
from mcp_core.orchestrator_loop import Orchestrator
from mcp_core.swarm_schemas import Task, ProjectProfile

class TestProvenanceIntegration(unittest.TestCase):
    def setUp(self):
        self.test_state_file = "test_project_profile.json"
        # Reset state file
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)
            
    def tearDown(self):
        if os.path.exists(self.test_state_file):
            os.remove(self.test_state_file)
        if os.path.exists(self.test_state_file + ".lock"):
            os.remove(self.test_state_file + ".lock")

    @patch("mcp_core.orchestrator_loop.generate_response")
    def test_process_task_logs_provenance(self, mock_generate):
        # Setup Mock LLM Response
        mock_response = MagicMock()
        mock_response.status = "SUCCESS"
        mock_response.reasoning_trace = "Done"
        mock_generate.return_value = mock_response

        # Init Orchestrator
        orch = Orchestrator(state_file=self.test_state_file)
        
        # Create Dummy Task
        task = Task(description="Test Task", status="PENDING")
        orch.state.add_task(task)
        orch.save_state()
        
        # Run Process
        print(f"Testing task {task.task_id}...")
        orch.process_task(task.task_id)
        
        # Reload State to verify persistence
        with open(self.test_state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
        profile = ProjectProfile(**data)
        
        # Verify Provenance Log
        print(f"Provenance Log: {profile.provenance_log}")
        self.assertTrue(len(profile.provenance_log) > 0, "Provenance log should not be empty")
        
        entry = profile.provenance_log[-1]
        self.assertEqual(entry.action, "task_completed")
        self.assertEqual(entry.artifact_ref, task.task_id)
        self.assertEqual(entry.role, "system")
        self.assertIsNotNone(entry.contributing_model, "Contributing model should be recorded in provenance")
        
        print("✅ Integration test passed!")

if __name__ == "__main__":
    import logging
    logging.basicConfig(level=logging.DEBUG)
    try:
        if os.path.exists("debug_error.log"):
            os.remove("debug_error.log")
        unittest.main(exit=False)
    finally:
        if os.path.exists("debug_error.log"):
            print("\n============ DEBUG ERROR LOG ============")
            with open("debug_error.log", "r") as f:
                print(f.read())
            print("=========================================")
