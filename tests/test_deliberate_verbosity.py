"""
Test verbosity trimming for the deliberate tool.
"""

import unittest
from unittest.mock import MagicMock, patch


class TestDeliberateVerbosity(unittest.TestCase):
    """Test that deliberate returns concise output by default."""
    
    @patch("server.get_orchestrator")
    def test_default_concise_output(self, mock_get_orch):
        """Test that return_json=False (default) returns short output."""
        # Import after mocking to get mocked version
        from server import deliberate
        
        # Mock orchestrator
        mock_orch = MagicMock()
        mock_result = MagicMock()
        mock_result.task_id = "test-123"
        mock_result.confidence = 0.95
        mock_result.final_answer = "The answer is 42"
        mock_result.steps = [
            MagicMock(step=1, name="Decompose", worker="HippoRAG", output=[]),
            MagicMock(step=2, name="Analyze", worker="Analysis", output={}),
        ]
        mock_result.model_dump.return_value = {"task_id": "test-123"}
        
        mock_orch.run_deliberation.return_value = mock_result
        mock_get_orch.return_value = mock_orch
        
        # Access the underlying function from the FunctionTool wrapper
        result = deliberate.fn(problem="Test problem")
        
        # Verify output is concise
        self.assertIn("✅", result)
        self.assertIn("Confidence: 0.95", result)
        self.assertIn("The answer is 42", result)
        self.assertIn("2 steps executed", result)
        
        # Verify output is short (< 500 chars)
        self.assertLess(len(result), 500, "Default output should be concise")
        
        # Verify full details are NOT in output
        self.assertNotIn("task_id", result.lower())
        self.assertNotIn('"step":', result)
    
    @patch("server.get_orchestrator")
    def test_verbose_json_output(self, mock_get_orch):
        """Test that return_json=True returns full JSON."""
        from server import deliberate
        
        # Mock orchestrator
        mock_orch = MagicMock()
        mock_result = MagicMock()
        mock_result.confidence = 0.95
        mock_result.model_dump.return_value = {"task_id": "test-123", "confidence": 0.95}
        mock_result.model_dump_json.return_value = '{"task_id": "test-123", "confidence": 0.95, "steps": [{"name": "Decompose"}, {"name": "Analyze"}]}'
        
        mock_orch.run_deliberation.return_value = mock_result
        mock_get_orch.return_value = mock_orch
        
        # Call deliberate with return_json=True (access underlying function)
        result = deliberate.fn(problem="Test problem", return_json=True)
        
        # Verify output is JSON
        self.assertIn("task_id", result)
        self.assertIn("confidence", result)
        
        # Verify output is long (> 50 chars for JSON formatting)
        self.assertGreater(len(result), 50, "JSON output should contain full details")


if __name__ == "__main__":
    unittest.main()
