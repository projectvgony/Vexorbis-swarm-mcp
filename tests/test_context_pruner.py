
import unittest
from unittest.mock import MagicMock
from mcp_core.algorithms.context_pruner import ContextPruner
from mcp_core.swarm_schemas import AuthorSignature
from mcp_core.search_engine import EmbeddingProvider

class MockProvider(EmbeddingProvider):
    def embed(self, texts):
        # Return dummy embeddings (dim=3)
        # We'll make them deterministic based on text length for testing
        return [[len(t) * 0.1, 0.1, 0.1] for t in texts]

class TestContextPruner(unittest.TestCase):
    def setUp(self):
        self.provider = MockProvider()
        self.pruner = ContextPruner(embedding_provider=self.provider)
        
    def test_prune_no_op_small_log(self):
        """Should not prune if log size <= limit"""
        log = [
            AuthorSignature(agent_id="1", role="engineer", action="test", artifact_ref="1")
            for _ in range(5)
        ]
        result = self.pruner.prune(log, "query", keep_tail=5, keep_relevant=5)
        self.assertEqual(len(result), 5)
        
    def test_prune_maintains_tail(self):
        """Should always keep usage of tail"""
        log = []
        for i in range(20):
             log.append(AuthorSignature(
                 agent_id="1", 
                 role="engineer", 
                 action=f"action_{i}", 
                 artifact_ref=str(i)
             ))
             
        # Tail = 5, Relevant = 5 (Total 10)
        result = self.pruner.prune(log, "query", keep_tail=5, keep_relevant=5)
        
        self.assertEqual(len(result), 10)
        
        # Verify last 5 items are exactly the last 5 of original
        self.assertEqual(result[-5:], log[-5:])
        
    def test_fallback_without_provider(self):
        """Should use FIFO if provider is None"""
        pruner_lite = ContextPruner(embedding_provider=None)
        # Override internal provider logic just to be sure
        pruner_lite.provider = None
        
        log = [
            AuthorSignature(agent_id="1", role="engineer", action=f"action_{i}")
            for i in range(20)
        ]
        
        result = pruner_lite.prune(log, "query", keep_tail=5, keep_relevant=5)
        self.assertEqual(len(result), 10)
        self.assertEqual(result, log[-10:])
        
if __name__ == '__main__':
    unittest.main()
