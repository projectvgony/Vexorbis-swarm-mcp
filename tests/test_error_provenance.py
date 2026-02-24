
import unittest
import os
import shutil
from unittest.mock import MagicMock, patch
from mcp_core.orchestrator_loop import Orchestrator
from mcp_core.swarm_schemas import Task
from templates.agent_response_schema import AgentResponse

class TestErrorProvenance(unittest.TestCase):
    def setUp(self):
        self.test_state = "test_error_provenance_state.json"
        # Clean start
        if os.path.exists(self.test_state):
            os.remove(self.test_state)
            
        self.orch = Orchestrator(state_file=self.test_state)
        # Disable git for this test to focus on task failure
        self.orch._git = MagicMock()
        self.orch._git.is_available.return_value = False

    def tearDown(self):
        if os.path.exists(self.test_state):
            os.remove(self.test_state)
        if os.path.exists(self.test_state + ".lock"):
            try:
                os.remove(self.test_state + ".lock")
            except:
                pass

    @patch("mcp_core.orchestrator_loop.generate_response")
    def test_task_failed_provenance(self, mock_generate):
        # 1. Setup a failing task
        # Mock generate_response to return FAILURE
        mock_response = AgentResponse(
            status="FAILED",
            reasoning_trace="Something went wrong",
            tool_calls=[]
        )
        mock_generate.return_value = mock_response

        task = Task(description="Do something that fails", status="PENDING")
        self.orch.state.add_task(task)
        self.orch.save_state()

        # 2. Process the task
        self.orch.process_task(task.task_id)

        # 3. reload state
        self.orch.load_state()
        
        # 4. Assertions
        # Check provenance log for "task_failed"
        log = self.orch.state.provenance_log
        
        # Find the failure entry
        failure_entry = next((e for e in log if e.action == "task_failed"), None)
        
        self.assertIsNotNone(failure_entry, "Should have a 'task_failed' provenance entry")
        if failure_entry:
            self.assertEqual(failure_entry.role, "system")
            # The code sets artifact_ref to f"{task_id}:::{status}"
            self.assertIn(task.task_id, failure_entry.artifact_ref)
            self.assertIn("FAILED", failure_entry.artifact_ref)
            print(f"✅ Verified provenance entry: {failure_entry}")

    @patch("mcp_core.orchestrator_loop.generate_response")
    def test_git_error_provenance(self, mock_generate):
        # 1. Enable Git for this test
        self.orch._git.is_available.return_value = True
        self.orch._git.has_changes.return_value = True
        self.orch._git.config.remote_url = "https://github.com/owner/repo.git"

        # 2. Mock AgentResponse to trigger git_commit tool
        mock_response = AgentResponse(
            status="SUCCESS",
            reasoning_trace="Committing changes",
            tool_calls=[{
                "function": "git_commit",
                "arguments": '{"message": "feat: new thing"}'
            }]
        )
        mock_generate.return_value = mock_response

        # 3. Mock _execute_git_tool to fail
        # We patch the method on the instance or class
        with patch.object(self.orch, '_execute_git_tool', side_effect=Exception("Simulated Git Crash")):
            
            # 4. Create task ready for commit
            task = Task(description="Commit stuff", status="IN_PROGRESS", git_commit_ready=True, output_files=["file.txt"])
            self.orch.state.add_task(task)
            
            # 5. Process
            self.orch.process_task(task.task_id)

            # 6. Assertions
            log = self.orch.state.provenance_log
            error_entry = next((e for e in log if e.action == "git_error"), None)
            
            if error_entry is None:
                print("\n⚠️ Feedback Log:", task.feedback_log)
                print("⚠️ Provenance Log:", log)

            self.assertIsNotNone(error_entry, "Should have a 'git_error' provenance entry")
            if error_entry:
                self.assertIn("Simulated Git Crash", error_entry.artifact_ref)
                print(f"✅ Verified Git error entry: {error_entry}")

if __name__ == "__main__":
    unittest.main()
