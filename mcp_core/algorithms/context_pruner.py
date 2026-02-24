
import logging
from typing import List, Optional
from mcp_core.swarm_schemas import AuthorSignature
from mcp_core.search_engine import get_embedding_provider, EmbeddingProvider

logger = logging.getLogger(__name__)

class ContextPruner:
    """
    Implements 'Smart-Power' semantic pruning for the provenance log.
    
    Strategy:
    1. Always preserve the 'Tail' (last N items) for immediate continuity.
    2. Score remaining items by semantic similarity to the current task.
    3. Keep top K relevant items.
    4. Discard the rest (they remain in telemetry.db).
    """
    
    def __init__(self, embedding_provider: Optional[EmbeddingProvider] = None):
        # Auto-load provider if not passed (priority: Gemini -> OpenAI -> Local)
        self.provider = embedding_provider or get_embedding_provider(provider_type="auto")
        
    def prune(self, log: List[AuthorSignature], query: str, 
              keep_tail: int = 10, keep_relevant: int = 20) -> List[AuthorSignature]:
        """
        Prune the log to a concise, relevant subset.
        
        Args:
            log: The full (or current) provenance log.
            query: The current task description to score against.
            keep_tail: Number of most recent items to always keep.
            keep_relevant: Number of high-score items to keep from the remainder.
            
        Returns:
            A reduced list of AuthorSignatures.
        """
        if not log:
            return []
            
        total_keep = keep_tail + keep_relevant
        if len(log) <= total_keep:
            return log # No need to prune
            
        # 1. Split Tail (Always kept) and Candidates
        # Python slicing: [-N:] gets last N
        tail = log[-keep_tail:]
        candidates = log[:-keep_tail]
        
        # If we have no provider (e.g. Lite Mode), fallback to simple FIFO
        if not self.provider:
            logger.info("ContextPruner: No embedding provider. using FIFO fallback.")
            # Just keep the last 'total_keep' items effectively
            return log[-total_keep:]
            
        try:
            # 2. Embed Query
            query_embedding = self.provider.embed([query])[0]
            
            # 3. Embed Candidates (Access 'action' + 'artifact_ref' for context)
            # We construct a text rep for importance: "action on artifact"
            candidate_texts = [
                f"{c.action} {c.artifact_ref or ''} {c.role}" 
                for c in candidates
            ]
            
            # Batch embedding might be needed for very large logs, 
            # but usually this starts small. We'll embed all at once for now.
            candidate_embeddings = self.provider.embed(candidate_texts)
            
            # 4. Score
            ranked_candidates = []
            for i, sig in enumerate(candidates):
                score = self._cosine_similarity(query_embedding, candidate_embeddings[i])
                ranked_candidates.append((score, sig))
                
            # 5. Select Top K
            ranked_candidates.sort(key=lambda x: x[0], reverse=True)
            top_k = [item[1] for item in ranked_candidates[:keep_relevant]]
            
            # Re-sort Top K by timestamp (or original index) to maintain chronological order?
            # Ideally, provenance should be chronological.
            # Let's simple-sort by timestamp if possible, or just rely on the fact 
            # that we want them to appear in order.
            # Actually, `top_k` are now out of order. Let's regain order.
            
            # Optimization: Use indices to sort back
            # (score, index, sig)
            ranked_with_index = []
            for i, sig in enumerate(candidates):
                score = self._cosine_similarity(query_embedding, candidate_embeddings[i])
                ranked_with_index.append((score, i, sig))
            
            ranked_with_index.sort(key=lambda x: x[0], reverse=True)
            top_k_indices = sorted([x[1] for x in ranked_with_index[:keep_relevant]])
            
            final_candidates = [candidates[i] for i in top_k_indices]
            
            logger.info(f"ContextPruner: Pruned {len(log)} -> {len(final_candidates) + len(tail)} items.")
            return final_candidates + tail

        except Exception as e:
            logger.error(f"ContextPruner failed: {e}. Fallback to FIFO.")
            return log[-total_keep:]

    def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x ** 2 for x in a) ** 0.5
        magnitude_b = sum(x ** 2 for x in b) ** 0.5
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        return dot_product / (magnitude_a * magnitude_b)
