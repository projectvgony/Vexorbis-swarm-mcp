"""
Swarm v3.0 - FastMCP Server

Exposes the Swarm orchestrator functionality as an MCP server.
This allows AI agents (like Claude Desktop, VSCode, etc.) to interact
with the Swarm via the Model Context Protocol.
"""

import sys
import io

# Force UTF-8 output encoding (prevents Windows CP1252 errors with emojis/Unicode)
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


import logging
from typing import Optional
from fastmcp import FastMCP

# Import Swarm components
from mcp_core.orchestrator_loop import Orchestrator
from mcp_core.swarm_schemas import Task
from mcp_core.search_engine import CodebaseIndexer, HybridSearch, IndexConfig, get_embedding_provider
from mcp_core.telemetry.collector import collector
from mcp_core.startup_checks import run_startup_checks

from pathlib import Path
import os

# [v3.4] Startup Checks
if not run_startup_checks():
    logging.critical("Startup checks failed. Exiting.")
    sys.exit(1)

# Dev build: Check for debug mode
DEBUG_MODE = os.getenv("SWARM_DEBUG", "false").lower() == "true"

# Tool scoping: Load internal tools for system maintenance
ENABLE_INTERNAL_TOOLS = os.getenv("SWARM_INTERNAL_TOOLS", "false").lower() == "true"

# Configure logging
logging.basicConfig(
    level=logging.DEBUG if DEBUG_MODE else logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("server.log"),
        logging.StreamHandler(sys.stderr)
    ]
)
logger = logging.getLogger("SwarmServer")

if DEBUG_MODE:
    logger.info("🐛 DEV MODE: Debug features enabled (SWARM_DEBUG=true)")
    logger.info("   - Verbose telemetry: ON")
    logger.info("   - SBFL auto-analysis: ON")
    logger.info("   - Prompt tracing: ON")

# Initialize FastMCP server
mcp = FastMCP("Swarm Orchestrator v3.4.0")

# Load dynamic tools
try:
    from mcp_core.tools.dynamic.loader import load_dynamic_tools
    
    # Determine which scopes to load
    tool_scopes = ['general']
    if ENABLE_INTERNAL_TOOLS:
        tool_scopes.append('internal')
        logger.info("🔧 Internal tools enabled (SWARM_INTERNAL_TOOLS=true)")
    
    load_dynamic_tools(mcp, scopes=tool_scopes)
except ImportError as e:
    logger.warning(f"Could not load dynamic tools: {e}")

# Load system tools
try:
    from mcp_core.tools.system import register_system_tools
    register_system_tools(mcp)
except ImportError as e:
    logger.warning(f"Could not load system tools: {e}")

# Initialize orchestrator (lazy)
_orchestrator: Optional[Orchestrator] = None
_indexer: Optional[CodebaseIndexer] = None


# ============================================================================
# MCP Resources - Agent Documentation
# ============================================================================
# Note: These paths resolve relative to the Swarm server's location,
# NOT the agent's working directory. Resources are served by the MCP server.

_SERVER_DIR = Path(__file__).parent

# AI agent documentation
@mcp.resource("swarm://docs/ai/guide")
def get_ai_agent_guide() -> str:
    """Comprehensive AI agent guide with decision trees and workflows."""
    return (_SERVER_DIR / "docs" / "ai" / "agent-guide.md").read_text()

@mcp.resource("swarm://docs/ai/tools")
def get_ai_tool_reference() -> str:
    """Detailed AI tool specifications and validation rules."""
    return (_SERVER_DIR / "docs" / "ai" / "tool-reference.md").read_text()

@mcp.resource("swarm://docs/ai/examples")
def get_ai_examples() -> str:
    """Common AI agent workflow examples."""
    return (_SERVER_DIR / "docs" / "ai" / "examples.md").read_text()

# AI Skills - Procedural instructions for common workflows
@mcp.resource("swarm://skills/git-commits")
def get_skill_git_commits() -> str:
    """Conventional Commits format and workflow."""
    return (_SERVER_DIR / "docs" / "ai" / "skills" / "git-conventional-commits.md").read_text()

@mcp.resource("swarm://skills/git-pr")
def get_skill_git_pr() -> str:
    """Pull request creation best practices."""
    return (_SERVER_DIR / "docs" / "ai" / "skills" / "git-pull-request.md").read_text()

@mcp.resource("swarm://skills/git-branch")
def get_skill_git_branch() -> str:
    """Branch naming and workflow conventions."""
    return (_SERVER_DIR / "docs" / "ai" / "skills" / "git-branch-workflow.md").read_text()

@mcp.resource("swarm://skills/security-audit")
def get_skill_security_audit() -> str:
    """OWASP security checklist and audit procedures."""
    return (_SERVER_DIR / "docs" / "ai" / "skills" / "security-audit.md").read_text()

@mcp.resource("swarm://skills/tool-creation")
def get_skill_tool_creation() -> str:
    """Guide for creating new MCP tools."""
    return (_SERVER_DIR / "docs" / "ai" / "skills" / "tool-creation.md").read_text()

@mcp.resource("swarm://skills/context-deliberator")
def get_skill_context_deliberator() -> str:
    """Context-aware deliberation using historical reasoning patterns."""
    return (_SERVER_DIR / "docs" / "ai" / "skills" / "context-deliberator.md").read_text()

# Human documentation
@mcp.resource("swarm://docs/architecture")
def get_architecture() -> str:
    """Project architecture and component overview."""
    return (_SERVER_DIR / "ARCHITECTURE.md").read_text()

@mcp.resource("swarm://docs/getting-started")
def get_getting_started() -> str:
    """Installation and first steps guide."""
    return (_SERVER_DIR / "docs" / "human" / "getting-started.md").read_text()

@mcp.resource("swarm://docs/user-guide")
def get_user_guide() -> str:
    """Complete feature walkthrough and best practices."""
    return (_SERVER_DIR / "docs" / "human" / "user-guide.md").read_text()

@mcp.resource("swarm://docs/api-reference")
def get_api_reference() -> str:
    """MCP tools and CLI commands reference."""
    return (_SERVER_DIR / "docs" / "human" / "api-reference.md").read_text()

@mcp.resource("swarm://docs/configuration")
def get_configuration() -> str:
    """Environment setup and provider configuration."""
    return (_SERVER_DIR / "docs" / "human" / "configuration.md").read_text()

@mcp.resource("swarm://docs/performance")
def get_performance() -> str:
    """Benchmarks and optimization strategies."""
    return (_SERVER_DIR / "docs" / "human" / "performance.md").read_text()

@mcp.resource("swarm://docs/changelog")
def get_changelog() -> str:
    """Version history and release notes."""
    return (_SERVER_DIR / "CHANGELOG.md").read_text()

# ============================================================================
# MCP Tools - Discovery & Health
# ============================================================================

@mcp.tool()
def check_health() -> str:
    """
    Check the health of the Swarm MCP server.
    Returns status of orchestrator, indexer, and connectivity.
    """
    status = ["🟢 Swarm MCP Server is healthy."]
    
    if _orchestrator:
        status.append("✅ Orchestrator: Initialized")
    else:
        status.append("⚪ Orchestrator: Ready (Lazy-load)")
        
    if _indexer:
        status.append("✅ Indexer: Initialized")
    else:
        status.append("⚪ Indexer: Ready (Lazy-load)")
        
    import os
    if os.environ.get("IS_DOCKER"):
        status.append("🐳 Environment: Docker Container")
    else:
        status.append("💻 Environment: Local Host")
        
    return "\n".join(status)

# ============================================================================
# Helper Functions
# ============================================================================



# classify_task_intent() removed - not needed for direct tool access

def get_orchestrator() -> Orchestrator:
    """Lazy-load orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        logger.info("🚀 Initializing Swarm Orchestrator...")
        _orchestrator = Orchestrator()
    return _orchestrator


def get_indexer() -> CodebaseIndexer:
    """Lazy-load indexer instance."""
    global _indexer
    if _indexer is None:
        logger.info("📚 Initializing Codebase Indexer...")
        config = IndexConfig()
        _indexer = CodebaseIndexer(config)
        _indexer.load_cache()  # Try to load existing index
    return _indexer



# process_task() removed - use direct tools instead:
# - search_codebase() for code search
# - deliberate() for multi-step reasoning
# - retrieve_context() for HippoRAG analysis

@mcp.tool()
@collector.track_tool("deliberate")
def deliberate(
    problem: str,
    context: str = "",
    constraints: list[str] = None,
    steps: int = 3,
    return_json: bool = False
) -> str:
    """
    Structured multi-step deliberation using algorithmic workers.
    
    **Alternative to "sequential thinking"** - uses deterministic algorithms for each step
    instead of pure LLM reasoning. Best for complex problems requiring multiple perspectives.
    
    **Deliberation Flow**:
    1. **Decompose**: Break problem into sub-problems using HippoRAG
    2. **Analyze**: Route each sub-problem to appropriate worker
    3. **Synthesize**: Combine worker outputs into coherent solution
    
    **When to use**:
    - Complex problems requiring multi-faceted analysis
    - When you need to combine multiple algorithmic insights
    - Breaking down architectural decisions
    - Verifying complex invariants
    
    **When NOT to use**:
    - Simple queries (ask directly)
    - Single-algorithm tasks (use process_task)
    - File operations (use filesystem tools)
    
    **Examples**:
    ```python
    # Architecture analysis
    deliberate(
        problem="Should we use microservices or monolith?",
        context=view_file("ARCHITECTURE.md"),
        constraints=["Must support 1M users", "Team of 5 engineers"],
        steps=3
    )
    
    # Code verification
    deliberate(
        problem="Verify payment processor never loses transactions",
        context=view_file("payment.py"),
        constraints=["ACID compliance", "No negative balances"],
        steps=4
    )
    ```
    
    Args:
        problem: The core problem or question to deliberate on
        context: Optional context (code, docs, or prior analysis)
        constraints: Hard constraints that must be satisfied
        steps: Number of deliberation steps (1-5, default 3)
        return_json: Return full JSON trace (default False for concise output)
    
    Returns:
        Concise summary by default, or full JSON trace if return_json=True
    """
    if constraints is None:
        constraints = []
    
    # Validate steps
    if not 1 <= steps <= 5:
        return "❌ Error: steps must be between 1 and 5"
    
    try:
        orch = get_orchestrator()
        result = orch.run_deliberation(problem, context, constraints, steps)
        
        # Log full trace to server logs (for operator visibility)
        logger.info(f"🧠 Deliberation Complete: {result.task_id}")
        logger.info(f"   Problem: {problem[:100]}...")
        logger.info(f"   Steps: {len(result.steps)}")
        logger.info(f"   Confidence: {result.confidence:.2f}")
        logger.info(f"   Final Answer: {result.final_answer[:200]}...")
        
        # Log full JSON to file for audit
        import json
        logger.debug(f"Full Deliberation Result: {json.dumps(result.model_dump(), indent=2)}")
        
        if return_json:
            # Return full JSON (verbose mode)
            return result.model_dump_json(indent=2)
        else:
            # Return concise Markdown summary (default, agent-friendly)
            steps_summary = f"{len(result.steps)} steps executed"
            workers_used = set(s.worker for s in result.steps)
            
            return f"""✅ **Deliberation Complete** (Confidence: {result.confidence:.2f})

**Result**: {result.final_answer}

*({steps_summary} using {', '.join(workers_used)}. Full trace in server logs.)*"""
    
    except Exception as e:
        logger.error(f"Deliberation error: {e}")
        return f"❌ Error: {str(e)}"




@mcp.tool()
@collector.track_tool("get_status")
def get_status(limit: int = 10, show_all: bool = False) -> str:
    """
    Get the current status of all tasks in the Swarm blackboard.
    
    **When to use:**
    - Checking progress of previously submitted tasks
    - Monitoring Swarm's internal state
    - Debugging task execution flows
    - Before creating new tasks to avoid duplicates
    
    **When NOT to use:**
    - Checking Docker container status (use Docker MCP)
    - Viewing file contents (use filesystem tools)
    - Git repository status (use GitHub MCP)
    
    **Example:**
    ```
    get_status()
    # → Returns list of all tasks with IDs, status (PENDING/COMPLETED), descriptions
    ```

    **Best Practices:**
    - ⚠️ Do NOT poll this in a loose loop. Use it only when checking specific task progress.
    - Swarm functions asynchronously; wait a few seconds before checking status after submission.
    
    Args:
        limit: Max number of tasks to return (default: 10).
        show_all: If true, ignore limit and show all tasks.
        
    Returns:
        Formatted list of tasks with their current status
    """
    try:
        orch = get_orchestrator()
        orch.load_state()
        
        if not orch.state.tasks:
            return "📋 No tasks found in the blackboard."
        
        all_tasks = sorted(orch.state.tasks.items(), key=lambda x: x[1].task_id, reverse=True)
        total_count = len(all_tasks)
        
        if not show_all and total_count > limit:
            display_tasks = all_tasks[:limit]
            header = f"📋 Swarm Blackboard Status (Showing last {limit} of {total_count} tasks):\n"
            footer = f"\n...and {total_count - limit} older tasks (use show_all=True to see all)."
        else:
            display_tasks = all_tasks
            header = f"📋 Swarm Blackboard Status ({total_count} tasks):\n"
            footer = ""
            
        status_lines = [header]
        for task_id, task in display_tasks:
            status_lines.append(f"  • {task_id[:8]}: [{task.status}] {task.description[:50]}...")
        
        if footer:
            status_lines.append(footer)
            
        return "\n".join(status_lines)
        
    except Exception as e:
        logger.error(f"Error getting status: {e}")
        return f"❌ Error: {str(e)}"


def _is_likely_symbol(query: str) -> bool:
    """
    Heuristic to detect if query looks like an exact symbol.
    Used to auto-suggest keyword-only search for better performance.
    """
    import re
    query = query.strip()
    
    # Check common symbol patterns
    patterns = [
        r'^[A-Z][a-zA-Z0-9]+$',                # CamelCase: UserModel, HttpClient
        r'^[a-z_][a-z0-9_]+$',                 # snake_case: user_model, calculate_tax
        r'^[a-z_][a-z0-9_]*\(\)$',            # function(): authenticate(), get_user()
        r'^\.\w+$',                            # .method: .save, .validate
        r'^[A-Z][A-Z_0-9]+$',                  # CONSTANTS: MAX_SIZE, API_KEY
    ]
    
    return any(re.match(p, query) for p in patterns)


@mcp.tool()
@collector.track_tool("search_codebase")
async def search_codebase(query: str, top_k: int = 5, keyword_only: bool = False) -> str:
    """
    Search the codebase using hybrid semantic + keyword search.
    
    **Search Strategy (auto-suggested):**
    
    Use keyword_only=True (⚡ ~1ms) for exact symbols:
    - Class names: "UserModel", "HttpClient"
    - Function names: "calculate_tax", "authenticate()"
    - Variable names: "user_id", "config_path"
    - Constants: "MAX_SIZE", "API_KEY"
    
    Use semantic (default, ~240ms) for concepts:
    - "authentication logic" → finds OAuth, JWT, sessions
    - "database pooling" → finds connection managers
    - "error handling patterns" → finds try/catch, Result types
    - "user management" → finds profiles, accounts, permissions
    
    **Performance:**
    - Keyword: ~1ms (indexed hash lookup)
    - Semantic: ~200-300ms (API embedding call)
    - Trade-off: 200ms for conceptual understanding vs exact matching
    
    **When to use:**
    - Finding functions/classes by description: "authentication logic"
    - Locating implementation of features: "payment processing"
    - Discovering patterns: "error handling"
    - Quick lookups before retrieve_context()
    
    **When NOT to use:**
    - Deep architectural analysis (use retrieve_context for AST graphs)
    - File tree navigation (use filesystem MCP tools)
    - Cross-repository search (use GitHub MCP search tools)
    - Regex patterns (use grep/ripgrep tools)
    
    **Works well with:**
    - retrieve_context(): Search → deep-dive with HippoRAG
    - process_task(): Find code → refactor with Swarm
    - Docker MCP: Search → test in containers
    
    **Examples:**
    ```
    # Fast keyword search for exact symbols
    search_codebase("UserModel", keyword_only=True)  # ~1ms
    search_codebase("calculate_tax", keyword_only=True)  # ~1ms
    
    # Semantic search for concepts
    search_codebase("authentication logic")  # ~240ms, finds OAuth, JWT
    search_codebase("database connection pooling")  # understands intent
    
    # Get more results
    search_codebase("error handling", top_k=10)
    ```
    
    Args:
        query: Natural language description or exact keywords
        top_k: Number of results to return (1-50, default 5)
        keyword_only: Skip semantic matching for faster literal searches
        
    Returns:
        Formatted search results with file paths, line numbers, scores, and code snippets
    """
    import asyncio
    
    def _blocking_search():
        """Run the actual search in a thread to avoid blocking the event loop."""
        indexer = get_indexer()
        
        if not indexer.chunks:
            return "⚠️ No index found. Please run 'index' command first."
        
        # Check if query looks like a symbol (auto-suggest keyword_only)
        is_symbol = _is_likely_symbol(query)
        
        # ACTIVE GOVERNANCE: Auto-Pilot
        if is_symbol and not keyword_only:
            logger.info(f"⚡ Auto-Pilot: Detected symbol '{query}'. Attempting keyword search optimization...")
            searcher = HybridSearch(indexer, None)
            keyword_results = searcher.keyword_search(query, top_k=top_k)
            
            if keyword_results:
                result_lines = [f"⚡ Auto-optimized to keyword search (~1ms) for symbol '{query}'.\nFound {len(keyword_results)} results:\n"]
                for i, result in enumerate(keyword_results, 1):
                    result_lines.append(f"{i}. {result.file_path}:{result.start_line}-{result.end_line}")
                    result_lines.append(f"   Score: {result.score:.3f}")
                    result_lines.append(f"   {result.content[:200]}...\n")
                return "\n".join(result_lines)
            
            logger.info("Auto-Pilot: No keyword matches found. Falling back to semantic search.")

        # Get embedding provider for hybrid search (optional)
        embed_provider = None
        if not keyword_only:
            has_embeddings = any(c.embedding is not None for c in indexer.chunks)
            if has_embeddings:
                try:
                    embed_provider = get_embedding_provider("auto")
                except RuntimeError:
                    logger.warning("No API key set, falling back to keyword search")
        
        # Perform search
        searcher = HybridSearch(indexer, embed_provider)
        
        if keyword_only:
            results = searcher.keyword_search(query, top_k=top_k)
        else:
            results = searcher.search(query, top_k=top_k)
        
        if not results:
            if keyword_only:
                return "🔍 No exact matches found.\n\n💡 Tip: Try semantic search (remove keyword_only=True) to find conceptually similar code."
            else:
                return "🔍 No results found.\n\n💡 Tip: Try retrieve_context() for deeper architectural analysis with AST graphs."
        
        # Suggest escalation for sparse results
        escalation_hint = ""
        if not keyword_only and len(results) <= 2:
            escalation_hint = f"\n💡 Few results found. Consider retrieve_context() for deeper architectural analysis and call graph relationships.\n"
        
        # Format results
        result_lines = [f"🔍 Found {len(results)} results for: {query}\n"]
        for i, result in enumerate(results, 1):
            result_lines.append(f"{i}. {result.file_path}:{result.start_line}-{result.end_line}")
            result_lines.append(f"   Score: {result.score:.3f}")
            result_lines.append(f"   {result.content[:200]}...\n")
        
        return "\n".join(result_lines) + escalation_hint
    
    try:
        # Run blocking search in thread pool to avoid blocking the MCP event loop
        return await asyncio.to_thread(_blocking_search)
    except Exception as e:
        logger.error(f"Error searching codebase: {e}")
        return f"❌ Error: {str(e)}"




@mcp.tool()
@collector.track_tool("index_codebase")
async def index_codebase(path: str = ".", provider: str = "auto") -> str:
    """
    Index the codebase for semantic search capabilities.
    
    **Provider Selection Guide:**
    
    auto (default) - Auto-detects best available provider:
    - Tries: GEMINI_API_KEY → OPENAI_API_KEY → Local → Keyword-only
    - Recommended for most cases
    
    gemini - Google Gemini API embeddings:
    - Fast API calls (~2-5s for 150 chunks)
    - Best quality semantic understanding
    - Requires: GEMINI_API_KEY environment variable
    - Cost: Free tier available, then pay-per-use
    
    openai - OpenAI API embeddings:
    - Alternative to Gemini, similar quality
    - Requires: OPENAI_API_KEY environment variable
    - Cost: Pay-per-use pricing
    
    local - Offline sentence-transformers:
    - Slower indexing (60-120s for 150 chunks)
    - No API costs, works offline
    - Requires: sentence-transformers installed
    - First run downloads ~400MB model
    
    **When to Index:**
    - ✅ First-time setup
    - ✅ After adding >10 new files
    - ✅ After major refactoring
    - ✅ When switching projects/directories
    - ❌ Minor edits (index persists)
    - ❌ Before every search (wasteful)
    
    **Performance (150 chunks):**
    - Gemini/OpenAI: ~45s (API calls)
    - Local: ~60-120s (CPU-bound)
    - Keyword-only: ~0.2s (no embeddings)
    
    **When to use:**
    - Enable semantic search (concept-based queries)
    - Before using search_codebase() for the first time
    - After significant code changes
    
    **When NOT to use:**
    - Extremely large codebases (>100k files) without filtering
    - Every time before searching (index is cached)
    - If only keyword search is sufficient
    
    **Works well with:**
    - search_codebase(): Required for semantic search
    - Docker MCP: Index mounted volumes inside containers

    **Included Files:**
    - Extensions: .py, .js, .ts, .jsx, .tsx, .go, .rs, .java, .cpp, .c
    - Excludes: node_modules, .git, .venv, dist, build, __pycache__
    - Note: Non-code files (md, txt, json) are NOT indexed. Use grep_search for those.
    
    **Examples:**
    ```
    # Auto-detect best provider (recommended)
    index_codebase()
    
    # Specific provider for Gemini
    index_codebase(provider="gemini")
    
    # Offline indexing (no API)
    index_codebase(provider="local")
    
    # Index specific directory
    index_codebase("/path/to/project")
    ```
    
    Args:
        path: Absolute or relative path to codebase root (default: current directory)
        provider: Embedding provider - "auto" | "gemini" | "openai" | "local"
        
    Returns:
        Number of indexed code chunks and status message
    """
    import asyncio
    
    def _blocking_index():
        """Run the actual indexing in a thread to avoid blocking the event loop."""
        global _indexer
        
        config = IndexConfig(root_path=path)
        indexer = CodebaseIndexer(config)
        
        # Try to get embedding provider
        try:
            embed_provider = get_embedding_provider(provider)
            logger.info(f"Using embedding provider: {type(embed_provider).__name__}")
            indexer.index_all(embed_provider)
        except Exception as e:
            logger.error(f"❌ Indexing failed with provider: {e}")
            logger.warning("Falling back to keyword-only indexing (no embeddings)")
            try:
                indexer.index_all(None)
            except Exception as inner_e:
                logger.error(f"❌ Critical indexing failure: {inner_e}")
                raise inner_e
        
        # Update global indexer
        _indexer = indexer
        
        return f"✅ Indexed {len(indexer.chunks)} chunks from {path}"
    
    try:
        # Run blocking indexing in thread pool to avoid blocking the MCP event loop
        return await asyncio.to_thread(_blocking_index)
    except Exception as e:
        logger.error(f"Error indexing codebase: {e}")
        return f"❌ Error: {str(e)}"


@mcp.tool()
@collector.track_tool("retrieve_context")
def retrieve_context(query: str, top_k: int = 10) -> str:
    """
    Use HippoRAG to retrieve relevant code context via AST graph + PageRank.
    
    **Escalation Guide (when to upgrade from search_codebase):**
    
    Start with search_codebase(), escalate to retrieve_context() when:
    - ✅ Search results are incomplete or miss related code
    - ✅ You need to understand call graphs and dependencies
    - ✅ Refactoring requires full architectural context
    - ✅ Initial search found something but you need the "full picture"
    
    **Performance:**
    - Time: ~500ms-2s (builds AST graph + PageRank)
    - vs search_codebase: 5-20x slower but much deeper
    - Trade-off: Speed for architectural understanding
    
    **What it does differently:**
    - Builds Abstract Syntax Tree (AST) for all Python files
    - Creates knowledge graph of function calls, imports, classes
    - Runs Personalized PageRank to find related nodes
    - Returns results ranked by graph centrality (importance)
    
    **When to use:**
    - Understanding code architecture and relationships
    - Finding ALL code related to a feature (multi-hop reasoning)
    - Analyzing dependencies and call graphs
    - Complex refactoring requiring full context
    - After search_codebase() for deeper analysis
    
    **When NOT to use:**
    - Simple function lookups (use search_codebase keyword_only=True)
    - First-time exploration (search_codebase is faster)
    - Non-Python codebases (HippoRAG uses Python AST)
    - Quick questions (overkill for simple queries)
    
    **Comparison Table:**
    
    | Aspect | search_codebase | retrieve_context |
    |--------|-----------------|------------------|
    | Speed | ~1-240ms | ~500-2000ms |
    | Depth | Surface-level | Architectural |
    | Method | Embeddings | AST + Graph |
    | Languages | All | Python only |
    | Use for | Quick lookups | Deep analysis |
    
    **Works well with:**
    - search_codebase(): Search → retrieve_context for deep dive
    - process_task(): Get context → create informed tasks
    - Docker MCP: Analyze → test in containers
    
    **Examples:**
    ```
    # Workflow: Start with search, escalate if needed
    search_codebase("authentication")  # Fast: ~1ms or ~240ms
    # → Found auth.py but need to see everything it touches
    retrieve_context("authentication flow")  # Deep: ~1s
    
    # Understand architecture
    retrieve_context("database models and migrations", top_k=15)
    
    # Find all code involved in a feature
    retrieve_context("payment processing pipeline")
    ```
    
    Args:
        query: Natural language description of concept/feature to analyze
        top_k: Number of context chunks to return (1-50, default 10)
        
    Returns:
        Ranked code chunks with node types, PPR scores, file locations, and content
    """
    try:
        from mcp_core.algorithms import HippoRAGRetriever
        
        retriever = HippoRAGRetriever()
        
        logger.info("📊 Building AST knowledge graph...")
        retriever.build_graph_from_ast(".", extensions=[".py"])
        
        logger.info(f"🔗 Graph: {retriever.graph.number_of_nodes()} nodes, {retriever.graph.number_of_edges()} edges")
        
        chunks = retriever.retrieve_context(query, top_k=top_k)
        
        if not chunks:
            return "🔍 No context found."
        
        result_lines = [f"🔍 Retrieved {len(chunks)} context chunks for: {query}\n"]
        for i, chunk in enumerate(chunks, 1):
            result_lines.append(f"{i}. [{chunk.node_type}] {chunk.node_name}")
            result_lines.append(f"   {chunk.file_path}:{chunk.start_line}-{chunk.end_line}")
            result_lines.append(f"   PPR Score: {chunk.ppr_score:.4f}")
            result_lines.append(f"   {chunk.content[:150]}...\n")
        
        return "\n".join(result_lines)
        
    except Exception as e:
        logger.error(f"Error retrieving context: {e}")
        return f"❌ Error: {str(e)}"



if __name__ == "__main__":
    import sys
    import os

    # Auto-detect transport preference
    # 1. Explicit --sse flag
    # 2. IS_DOCKER environment variable
    # 3. Default to stdio
    
    use_sse = "--sse" in sys.argv or os.environ.get("IS_DOCKER") == "1"
    
    if use_sse:
        host = os.environ.get("MCP_HOST", "0.0.0.0")
        port = int(os.environ.get("MCP_PORT", "8000"))
        
        logger.info(f"🚀 Starting Swarm MCP Server on {host}:{port}...")
        logger.info("📡 Transport: HTTP/SSE (Server-Sent Events)")
        
        # Run in SSE mode with explicit host/port configuration
        mcp.run(transport="sse", host=host, port=port)
    else:
        # Default: Stdio mode (IDE/Local mode)
        logger.info("🚀 Starting Swarm MCP Server...")
        logger.info("🔌 Transport: Stdio (Standard Input/Output)")
        mcp.run()
