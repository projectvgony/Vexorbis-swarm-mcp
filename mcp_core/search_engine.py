"""
Swarm v3.0 - Python-Native Search Engine

Provides semantic search capabilities using API-based embeddings (Gemini/OpenAI)
with optional local embeddings for offline environments.
"""

import os
import json
import logging
from pathlib import Path
from typing import List, Optional, Dict, Any
from dataclasses import dataclass, field

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# Data Models
# ============================================================================

@dataclass
class Chunk:
    """A chunk of code with metadata."""
    file_path: str
    content: str
    start_line: int
    end_line: int
    embedding: Optional[List[float]] = None


@dataclass
class SearchResult:
    """A search result with relevance score breakdown."""
    file_path: str
    content: str
    start_line: int
    end_line: int
    score: float
    semantic_score: float = 0.0
    exact_match_score: float = 0.0
    partial_match_score: float = 0.0


@dataclass
class IndexConfig:
    """Configuration for the codebase indexer."""
    root_path: str = "."
    extensions: List[str] = field(default_factory=lambda: [
        ".py", ".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".java", ".cpp", ".c", ".md", ".txt"
    ])
    exclude_patterns: List[str] = field(default_factory=lambda: [
        "node_modules", "__pycache__", ".git", "dist", "build", ".venv", "venv", 
        ".swarm", "server.log", "*.tmp", "*.bak"
    ])
    chunk_size: int = 50  # lines per chunk
    chunk_overlap: int = 10  # overlapping lines


@dataclass
class HybridSearchConfig:
    """Configuration for hybrid search scoring."""
    semantic_weight: float = 0.7       # Weight for semantic similarity
    exact_match_boost: float = 1.5     # Boost when exact query is found
    partial_match_weight: float = 0.3  # Weight for partial word matches
    min_word_length: int = 2           # Minimum word length for partial matching


# ============================================================================
# Embedding Providers
# ============================================================================

class EmbeddingProvider:
    """Base class for embedding providers."""
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError


class GeminiEmbedding(EmbeddingProvider):
    """Google Gemini API embeddings."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not set")
        
        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)
            self.client = genai
        except ImportError:
            raise ImportError("google-generativeai not installed. Run: pip install google-generativeai")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = []
        for text in texts:
            # [v3.5] Use Gemini Embedding 001
            result = self.client.embed_content(
                model="models/text-embedding-004", # Updated to latest stable
                content=text
            )
            embeddings.append(result['embedding'])
        return embeddings


class OpenAIEmbedding(EmbeddingProvider):
    """OpenAI API embeddings."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        try:
            from openai import OpenAI
            self.client = OpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("openai not installed. Run: pip install openai")
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        response = self.client.embeddings.create(
            model="text-embedding-3-small",
            input=texts
        )
        return [item.embedding for item in response.data]


class LocalEmbedding(EmbeddingProvider):
    """Local sentence-transformers embeddings (offline mode)."""
    
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        try:
            from sentence_transformers import SentenceTransformer
            self.model = SentenceTransformer(model_name)
        except ImportError:
            raise ImportError(
                "sentence-transformers not installed. "
                "Uncomment in requirements.txt and run: pip install sentence-transformers"
            )
    
    def embed(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()


# ============================================================================
# Codebase Indexer
# ============================================================================

class CodebaseIndexer:
    """Scans and indexes a codebase into searchable chunks."""
    
    def __init__(self, config: Optional[IndexConfig] = None):
        self.config = config or IndexConfig()
        self.chunks: List[Chunk] = []
        self.cache_path = Path(self.config.root_path) / ".swarm-cache" / "index.json"
    
    def scan_files(self) -> List[Path]:
        """Scan the codebase for indexable files, pruning excluded directories."""
        root = Path(self.config.root_path)
        files = []
        
        # Extensions set for fast lookup
        ext_set = set(self.config.extensions)
        
        for dirpath, dirnames, filenames in os.walk(str(root)):
            # Prune excluded directories in-place (MODIFY dirnames)
            # This prevents os.walk from entering them
            dirnames[:] = [
                d for d in dirnames 
                if not any(excl in os.path.join(dirpath, d) for excl in self.config.exclude_patterns)
                and not any(excl in d for excl in self.config.exclude_patterns)
            ]
            
            for f in filenames:
                _, ext = os.path.splitext(f)
                if ext in ext_set:
                    file_path = Path(dirpath) / f
                    
                    # Double check file exclusions (though dir exclusion handles most)
                    if any(excl in str(file_path) for excl in self.config.exclude_patterns):
                        continue
                        
                    files.append(file_path)
        
        logger.info(f"Found {len(files)} files to index")
        return files
    
    def chunk_file(self, file_path: Path) -> List[Chunk]:
        """Split a file into overlapping chunks."""
        chunks = []
        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            lines = content.splitlines()
            
            for i in range(0, len(lines), self.config.chunk_size - self.config.chunk_overlap):
                end = min(i + self.config.chunk_size, len(lines))
                chunk_lines = lines[i:end]
                
                if chunk_lines:
                    chunks.append(Chunk(
                        file_path=str(file_path),
                        content="\n".join(chunk_lines),
                        start_line=i + 1,
                        end_line=end
                    ))
        except Exception as e:
            logger.warning(f"Failed to read {file_path}: {e}")
        
        return chunks
    
    def index_all(self, provider: Optional[EmbeddingProvider] = None, max_workers: int = 4) -> None:
        """
        Index all files and generate embeddings with multi-threading.
        
        Args:
            provider: Optional embedding provider for semantic search
            max_workers: Number of threads for parallel file processing (default: 4)
        """
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from threading import Lock
        
        files = self.scan_files()
        self.chunks = []
        chunks_lock = Lock()
        
        logger.info(f"Indexing {len(files)} files with {max_workers} threads...")
        
        # Multi-threaded file chunking
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all file chunking tasks
            futures = {executor.submit(self.chunk_file, file_path): file_path for file_path in files}
            
            # Collect results as they complete
            for future in as_completed(futures):
                try:
                    file_chunks = future.result()
                    with chunks_lock:
                        self.chunks.extend(file_chunks)
                except Exception as e:
                    file_path = futures[future]
                    logger.error(f"Error chunking {file_path}: {e}")
        
        logger.info(f"Created {len(self.chunks)} chunks")
        
        # Generate embeddings if provider is available
        if provider and self.chunks:
            logger.info("Generating embeddings...")
            texts = [c.content for c in self.chunks]
            
            # Batch to avoid API limits
            batch_size = 20
            for i in range(0, len(texts), batch_size):
                batch_texts = texts[i:i + batch_size]
                batch_embeddings = provider.embed(batch_texts)
                
                for j, emb in enumerate(batch_embeddings):
                    self.chunks[i + j].embedding = emb
            
            logger.info("Embeddings generated")
        
        # Save cache
        self._save_cache()
    
    def _save_cache(self) -> None:
        """Save index to cache file."""
        self.cache_path.parent.mkdir(parents=True, exist_ok=True)
        
        cache_data = [
            {
                "file_path": c.file_path,
                "content": c.content,
                "start_line": c.start_line,
                "end_line": c.end_line,
                "embedding": c.embedding
            }
            for c in self.chunks
        ]
        
        self.cache_path.write_text(json.dumps(cache_data, indent=2))
        logger.info(f"Cache saved to {self.cache_path}")
    
    def load_cache(self) -> bool:
        """Load index from cache if available."""
        if not self.cache_path.exists():
            return False
        
        try:
            cache_data = json.loads(self.cache_path.read_text())
            self.chunks = [Chunk(**item) for item in cache_data]
            logger.info(f"Loaded {len(self.chunks)} chunks from cache")
            return True
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return False


# ============================================================================
# Hybrid Search (Semantic + Exact Match)
# ============================================================================

class HybridSearch:
    """
    Performs hybrid search combining semantic similarity with exact text matching.
    
    1. Semantic similarity with configurable weight
    2. Exact match boost for literal query matches
    3. Partial word matching for multi-word queries
    """
    
    def __init__(
        self,
        indexer: CodebaseIndexer,
        provider: Optional[EmbeddingProvider] = None,
        config: Optional[HybridSearchConfig] = None
    ):
        self.indexer = indexer
        self.provider = provider
        self.config = config or HybridSearchConfig()
    
    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Hybrid search combining semantic and exact matching.
        
        Args:
            query: Search query (natural language or specific terms)
            top_k: Number of results to return
        
        Returns:
            List of SearchResult sorted by combined score
        """
        if not self.indexer.chunks:
            logger.warning("No chunks indexed. Run indexer.index_all() first.")
            return []
        
        # Prepare query for matching
        lower_query = query.lower()
        query_words = [w for w in lower_query.split() if len(w) > self.config.min_word_length]
        
        # Get query embedding if provider available
        query_embedding = None
        if self.provider:
            try:
                query_embedding = self.provider.embed([query])[0]
            except Exception as e:
                logger.warning(f"Embedding failed, falling back to keyword search: {e}")
        
        results = []
        for chunk in self.indexer.chunks:
            lower_content = chunk.content.lower()
            
            # 1. Semantic Score
            semantic_score = 0.0
            if query_embedding and chunk.embedding:
                semantic_score = self._cosine_similarity(query_embedding, chunk.embedding)
            
            # 2. Exact Match Boost
            exact_match_score = 0.0
            if lower_query in lower_content:
                exact_match_score = self.config.exact_match_boost
            
            # 3. Partial Word Matching
            partial_match_score = 0.0
            if query_words and not exact_match_score:
                matched_words = sum(1 for word in query_words if word in lower_content)
                if matched_words > 0:
                    partial_match_score = (matched_words / len(query_words)) * self.config.partial_match_weight
            
            # Combined Score
            total_score = (
                (semantic_score * self.config.semantic_weight) +
                exact_match_score +
                partial_match_score
            )
            
            # Only include if there's some relevance
            if total_score > 0 or exact_match_score > 0 or partial_match_score > 0:
                results.append(SearchResult(
                    file_path=chunk.file_path,
                    content=chunk.content,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    score=total_score,
                    semantic_score=semantic_score,
                    exact_match_score=exact_match_score,
                    partial_match_score=partial_match_score
                ))
        
        # Sort by total score descending
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    def keyword_search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """
        Keyword-only search without embeddings.
        Useful for literal function names, class names, etc.
        
        Args:
            query: Exact or partial term to search for
            top_k: Number of results to return
        
        Returns:
            List of SearchResult sorted by match quality
        """
        if not self.indexer.chunks:
            logger.warning("No chunks indexed. Run indexer.index_all() first.")
            return []
        
        lower_query = query.lower()
        query_words = [w for w in lower_query.split() if len(w) > self.config.min_word_length]
        
        results = []
        for chunk in self.indexer.chunks:
            lower_content = chunk.content.lower()
            
            # Exact match gets highest score
            if lower_query in lower_content:
                # Count occurrences for ranking
                occurrences = lower_content.count(lower_query)
                score = self.config.exact_match_boost + (occurrences * 0.1)
                
                results.append(SearchResult(
                    file_path=chunk.file_path,
                    content=chunk.content,
                    start_line=chunk.start_line,
                    end_line=chunk.end_line,
                    score=score,
                    semantic_score=0.0,
                    exact_match_score=score,
                    partial_match_score=0.0
                ))
            elif query_words:
                # Partial word matching
                matched_words = sum(1 for word in query_words if word in lower_content)
                if matched_words > 0:
                    score = (matched_words / len(query_words)) * self.config.partial_match_weight
                    results.append(SearchResult(
                        file_path=chunk.file_path,
                        content=chunk.content,
                        start_line=chunk.start_line,
                        end_line=chunk.end_line,
                        score=score,
                        semantic_score=0.0,
                        exact_match_score=0.0,
                        partial_match_score=score
                    ))
        
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]
    
    @staticmethod
    def _cosine_similarity(a: List[float], b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        dot_product = sum(x * y for x, y in zip(a, b))
        magnitude_a = sum(x ** 2 for x in a) ** 0.5
        magnitude_b = sum(x ** 2 for x in b) ** 0.5
        
        if magnitude_a == 0 or magnitude_b == 0:
            return 0.0
        
        return dot_product / (magnitude_a * magnitude_b)


# ============================================================================
# Factory Function
# ============================================================================

def get_embedding_provider(
    provider_type: str = "auto",
    api_key: Optional[str] = None
) -> Optional[EmbeddingProvider]:
    """
    Get an embedding provider by type.
    
    Args:
        provider_type: "gemini", "openai", "local", "keyword", or "auto" (tries in order)
        api_key: Optional API key override
    
    Returns:
        An initialized EmbeddingProvider, or None if provider_type="keyword"
        
    Lite Mode (No API Keys):
        Use provider_type="keyword" for fast, offline search without embeddings.
        This enables exact-match and partial word matching only (~1ms).
    """
    # Keyword-only mode (no embeddings needed)
    if provider_type == "keyword":
        logger.info("Running in keyword-only mode (no API keys required)")
        return None
    
    # [v3.5] Prioritize Gemini (Default)
    if provider_type == "gemini" or (provider_type == "auto"):
        # Auto-detect key if not provided
        key = api_key or os.environ.get("GEMINI_API_KEY")
        if key:
            try:
                return GeminiEmbedding(key)
            except Exception as e:
                logger.warning(f"Gemini init failed: {e}")
                # Fallthrough to others only if explicit "auto"
                if provider_type == "gemini": raise
    
    if provider_type == "openai" or (provider_type == "auto" and os.environ.get("OPENAI_API_KEY")):
        try:
            return OpenAIEmbedding(api_key)
        except (ImportError, ValueError) as e:
            if provider_type == "openai":
                raise
            logger.warning(f"OpenAI unavailable: {e}")
    
    if provider_type == "local" or provider_type == "auto":
        try:
            return LocalEmbedding()
        except ImportError as e:
            if provider_type == "local":
                raise
            logger.warning(f"Local embeddings unavailable: {e}")
    
    # Auto fallback to keyword-only if no providers work
    if provider_type == "auto":
        logger.info(
            "No embedding providers available. Falling back to keyword-only mode.\n"
            "For semantic search, set GEMINI_API_KEY or OPENAI_API_KEY in environment."
        )
        return None
    
    raise RuntimeError("No embedding provider available. Set GEMINI_API_KEY or OPENAI_API_KEY.")

