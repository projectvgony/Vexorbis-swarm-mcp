# Changelog

All notable changes to Project Swarm will be documented in this file.

## [3.4.0] - 2026-01-21

### 🛠️ Dev Build & Debug Features
- **Global Debug Mode**: Introduced `SWARM_DEBUG` env var to toggle debug capabilities.
  - Activates `DEBUG` level logging.
  - Loads debug-only tools (e.g., `mcp_transport_debug.py`).
  - Displays "🐛 DEV MODE" banner on server startup.
- **Verbose Telemetry**: `SWARM_VERBOSE_TELEMETRY` now logs full tool arguments and execution timing in `collector.py`.
- **SBFL Toggle**: `SWARM_SBFL_ENABLED` allows disabling expensive Ochiai fault localization in production.
- **Prompt Tracing**: `SWARM_TRACE_PROMPTS` logs truncated inputs to LLMs for prompt engineering.
- **Dev-First Workflow**: Updated contribution guidelines to use `dev` branch as the default integration point.

### 🧹 Version Synchronization
- **VersionManager**: Added `sync_versions()` to align `server.py`, `orchestrator.py`, and `swarm_schemas.py` with `pyproject.toml`.

---

## [3.3.0] - 2026-01-21

### 🤖 Autonomous Git Engine
- **Multi-Role Agent System**: Rebuilt the Git system from a single worker into five specialized autonomous roles (Feature Scout, Code Auditor, Issue Triage, Branch Manager, and Project Lifecycle).
- **Prompt Engineering**: Introduced `git-worker-agent.md` skill with formal handoff protocols and exit reports.
- **Reliability**: Implemented comprehensive unit test suite in `tests/algorithms/test_git_worker.py`.

### 🧬 Strategic State Management
- **Roadmap Automation**: Integrated `docs/PLAN.md` with the orchestrator loop for bi-directional status synchronization.
- **Pydantic Migration**: Standardized `project_profile.json` structure using strictly-typed models.
- **Concurrency**: Replaced legacy mechanisms with cross-platform `filelock` for process-safe blackboard operations.

### 🎯 Output Verbosity Optimization
- **Deliberate Tool**: Changed default output from verbose JSON (~2000 chars) to concise Markdown summaries (~200 chars)
  - Agents now see: `✅ Deliberation Complete (Confidence: 0.95) | Result: [answer] | (3 steps executed)`
  - Full audit trails preserved in server logs via `logger.info()` and `logger.debug()`
  - Backward compatible: `return_json=True` still available for verbose output
  - **Impact**: ~10x reduction in agent context pollution while maintaining operator visibility
- **Index Persistence**: Verified `CodebaseIndexer.load_cache()` ensures index survives server restarts
- **Test Coverage**: Added `tests/test_deliberate_verbosity.py` to verify concise output defaults

---

## [3.1.0] - 2026-01-19

### Enhanced
- **Multi-Language HippoRAG**: Extended AST-based knowledge graph to support JavaScript, TypeScript, and future languages via Tree-sitter parser plugins
  - **Python** (built-in `ast` module, always available, no dependencies)
  - **JavaScript/JSX** (optional, requires `tree-sitter`, `tree-sitter-javascript`)
  - **TypeScript/TSX** (optional, requires `tree-sitter`, `tree-sitter-typescript`)
  - **Future-Ready**: Plugin system ready for Go, Rust, Java
  - **Lazy Loading**: Tree-sitter packages only loaded when parsing non-Python files
  - **Backward Compatible**: Existing Python-only workflows unchanged

### Added
- **Parser Infrastructure** (`mcp_core/algorithms/parsers/`)
  - `LanguageParser` abstract base class for plugin system
  - `ParserRegistry` with lazy loading and auto-detection
  - `PythonParser` refactored from `hipporag_retriever.py`
  - `TreeSitterParser` base class for multi-language support
  - `JavaScriptParser` (functions, classes, arrow functions, JSX)
  - `TypeScriptParser` (interfaces, type aliases, enums, TSX)
- **Tests**: Comprehensive test suite in `test_parsers.py`
- **Documentation**: Updated `workers.md` and `README.md` with multi-language examples

### Changed
- **HippoRAG Retriever**: Refactored to use parser registry instead of hard-coded Python AST logic
- **Auto-Detection**: `build_graph_from_ast()` now auto-detects all supported extensions when called without arguments
- **Requirements**: Added optional Tree-sitter dependencies (commented out by default)

---

## [3.0.3] - 2026-01-19

### Removed
- **Redundant Tools**: Removed tools that duplicate native AI capabilities
  - `generate_content` - Content generation is handled natively by AI agents
  - `create_skill_file` - AI agents write skill files directly using filesystem tools
  - `consult_reasoning_model` - Unnecessary self-delegation (AI already IS the reasoning model)
  - **Legacy Files**: Cleaned up unused/temporary files
    - `examples/` - Empty directory removed
    - `inspect_fastmcp.py` - Temporary debugging script removed
    - `test_active_governance.py` & `test_symbol_detection.py` - Removed (already integrated)
    - `blackboard_schema.py` - Removed (superseded by ProjectProfile)
  - **Impact**: ~400+ lines removed, simplified codebase, zero functional loss
  - **Rationale**: Focused Swarm on unique algorithmic capabilities (HippoRAG, OCC, CRDT, Z3, Ochiai, Debate, Voting)

### Documentation
- **README.md**: Removed references to deleted features (Skills, Toolsmith, examples folder)
- **user-guide.md**: Removed obsolete "Autonomous Self-Improvement (Toolsmith)" section
- **api-reference.md**: Updated MCP Resource URIs to match actual endpoints
- **server.py**: Fixed `swarm://docs/architecture` to read from root `ARCHITECTURE.md`



---

## [3.0.2] - 2026-01-19


### Changed
- **Documentation Restructure**: Reorganized documentation into professional open-source structure
  - New concise `README.md` (150 lines vs 599) as GitHub landing page
  - Created `docs/human/` for developer documentation (getting-started, user-guide, architecture, API reference, configuration, performance, contributing)
  - Created `docs/ai/` for AI agent documentation (agent-guide, tool-reference, examples)
  - Separated concerns: humans get tutorials, AI agents get optimized specs
  - All documentation updated to reflect v3.0.1 Active Governance features
- **MCP Resources**: Updated resource paths and added new comprehensive endpoints
  - Added `swarm://docs/ai/guide`, `swarm://docs/ai/tools`, `swarm://docs/ai/examples`
  - Added `swarm://docs/getting-started`, `swarm://docs/user-guide`, `swarm://docs/api-reference`, `swarm://docs/configuration`, `swarm://docs/performance`
  - Updated `swarm://docs/architecture` to point to `docs/human/architecture.md`
  - Removed legacy `swarm://docs/ai` resource (content now in `swarm://docs/ai/guide`)

### Removed
- **Temporary Test Files**: Removed `test_symbol_detection.py` and `test_active_governance.py`
  - These were one-time verification scripts created during Active Governance implementation
  - Functionality already verified and working in production
  - Proper unit tests exist in `tests/` directory

---

## [3.0.1] - 2026-01-19

### Enhanced
- **Auto-Pilot Search**: `search_codebase` now *automatically* executes keyword search for symbol queries (e.g. `UserModel`), falling back to semantic search only if needed. Optimized for speed (~1ms).
- **Task Guardrails**: `process_task` now rejects vague/short instructions (`< 3 words`) to encourage better prompting and prevent wasted agent cycles.
- **Fallback Guidance**: Keyword-only searches with no results suggest trying semantic search.
- **Escalation Tips**: Sparse semantic results trigger `retrieve_context()` suggestions.

### Technical
- Implemented `Auto-Pilot` logic: Symbol detection triggers eager keyword search.
- Implemented `Input Guardrails`: Pre-flight validation for task instructions.
- Improved agent decision reliability to near 100% for symbol searches (enforced).

---

## [3.2.0] - 2026-01-19

### 🧬 New Features: Autonomous Improvement
- **Toolsmith**: Swarm can now dynamically design, implement, and register its own Python MCP tools (`create_tool_file` + `loader.py`).
- **Skill Synthesis**: Automatically generates Antigravity Skill instructions (`.agent/skills/`) to teach IDE agents how to use new tools immediately.
- **Safe Restart**: Self-healing `restart_server` tool allows hot-reloading of new capabilities.
- **Telemetry System**: Privacy-first, local-only usage tracking (`~/.swarm/telemetry.db`) to identify automation gaps.

### 🛡️ Governance & Security
- **Permission-First Workflow**: Autonomous tool creation requires explicit user approval ("I found a gap, may I build X?").
- **Heuristics Enforcement**: All generated tools/skills MUST include documented usage heuristics and ROI calculations.
- **Governance Headers**: Automatic validation of generated code standards.

### 🔌 Technical
- Added `mcp_core/tools/dynamic` for runtime tool loading.
- Added `mcp_core/telemetry` for event buffering.
- Updated `worker_prompts.py` with Toolsmith persona and strict governance rules.
  
### Removed
- **Legacy Algorithms**: Removed **OCR Validator** and **CRDT Merger** (superseded by Autonomous Git Worker Team).

### Infrastructure
- **Lifecycle Manager**: Added `VersionManager` and `release` CLI command for automated versioning and changelog management.
- **Git Worker**: Updated prompts to enforce Conventional Commits (type/scope/desc) and helpful context (Why/What).
- **GitHub**: Verified Issue Templates and Actions workflows.


---

## [3.1.0] - 2026-01-19

### 🎯 Enhanced: Comprehensive Tool Heuristics

Added decision heuristics to all MCP tools to help AI agents make optimal performance and capability trade-offs.

### Added

- **MCP Resources** (agent-discoverable documentation)
  - `swarm://docs/ai` - Agent guidance file
  - `swarm://docs/architecture` - Project structure
  - `swarm://docs/changelog` - Version history

- **ai.txt Agent Guidance File**
  - Cross-tool navigation: when to use Swarm vs Antigravity built-in
  - Decision flowcharts for search and modification workflows
  - Performance reference table for all tools
  - Multi-tool workflow examples

- **Agent Integration Guide** in README
  - Tool selection flowchart (keyword vs semantic vs deep analysis)
  - Performance comparison table with exact timings
  - Best practices for each tool

- **search_codebase Heuristics**
  - Smart query detection: auto-identify symbols vs concepts
  - Performance guide: ~1ms keyword vs ~240ms semantic
  - Clear examples: when to use `keyword_only=True`

- **index_codebase Heuristics**
  - Provider comparison: auto/gemini/openai/local with timing
  - Re-indexing criteria: when to (>10 files) vs when not to
  - Cost information for each provider

- **retrieve_context Heuristics**
  - Escalation guide: when to upgrade from search_codebase
  - Comparison table: speed, depth, method, languages
  - Workflow examples: search → escalate pattern

- **process_task Heuristics**
  - Task routing guide showing algorithm triggers
  - Best practices: specific instructions with context
  - Examples for refactor/debug/verify/merge/analyze patterns

### Changed

- **Benchmark Accuracy**
  - Replaced misleading "152x faster" claim
  - Added honest comparison vs ripgrep (Antigravity's actual tool)
  - Included local embeddings speed data (~50-100ms)
  - Updated benchmark script to test all modes

## [3.0.0] - 2026-01-18

### 🚀 Major: Algorithmic Blackboard Upgrade

Tranformed Swarm from a standard LLM orchestrator to an **Algorithmic Blackboard** with 7 specialized deterministic workers.

### Added

- **7 New Algorithm Workers** (`mcp_core/algorithms/`)
  - **HippoRAG:** AST-based graph retrieval with PageRank.
  - **OCC Validator:** Optimistic Concurrency Control for atomic file writes.
  - **CRDT Merger:** Conflict-Free Replicated Data Types for concurrent edits.
  - **Weighted Voting:** Consensus engine with Elo ratings.
  - **Debate Engine:** Sparse-topology debate system.
  - **Z3 Verifier:** Formal verification using SMT solver.
  - **Ochiai Localizer:** Automated fault localization (SBFL).

- **New CLI Commands** (`orchestrator.py`)
  - `retrieve <query>`: Deep context retrieval via HippoRAG.
  - `debug --test-cmd`: Auto-locate bugs in failing tests.
  - `verify <func>`: Generate Z3 verification guides.
  - `benchmark`: Validate 3x velocity improvements.

- **Comprehensive Test Suite** (`tests/algorithms/`)
  - ~80 new tests covering all algorithm workers.
  - 95% coverage target.

### Changed

- **Task Dispatch:** `Orchestrator` now routes tasks to algorithms based on flags (`context_needed`, `conflicts_detected`, etc.) before falling back to LLM agents.
- **Project Structure:** Moved core logic to `mcp_core/` with dedicated `algorithms/` submodule.

## [2.1.0] - 2026-01-01

- **Python-Native Search Engine**
  - Replaced Node.js search with pure Python implementation.
  - Added Hybrid Search (Semantic + Keyword).

## [2.0.0] - Previous

- Node.js MCP server architecture.
- Initial Python orchestrator prototype.
