# Algorithmic Worker Tasks

These are demonstration tasks that showcase how Swarm's specialized algorithmic workers solve real engineering problems.

---

## Task 1: Verify Memory Lifecycle Invariants (Z3 Verifier)

**Objective**: Use formal verification to prove the memory refresh protocol never loses data.

**Algorithmic Worker**: Z3 Verifier (SMT Solver)

**Task Description**:
```
process_task("Verify that the Memory Refresh protocol preserves all critical insights when archiving files from active/ to archive/. Specifically, prove that: 1) No ERROR_LOG entries are lost, 2) All MASTER_PLAN checkmarks are preserved, 3) Archive summaries contain all key learnings from source files.")
```

**Expected Output**: Z3 constraints that model the archival process and proof that data integrity is maintained.

**Trigger Keywords**: "verify", "prove", "guarantee", "invariant"

---

## Task 2: Debug Search Engine Performance Regression (Ochiai SBFL)

**Objective**: Locate suspicious code causing semantic search timeouts.

**Algorithmic Worker**: Ochiai Localizer (Statistical Bug Localization)

**Task Description**:
```
process_task("Debug why semantic search with Gemini embeddings occasionally times out after ~60 seconds. The failing test scenario is: index_codebase() with 200+ markdown files, then search_codebase('memory system') causes httpx.ReadError. Locate the suspicious lines in search_engine.py.")
```

**Expected Output**: Ranked list of suspicious lines with Ochiai coefficients, highlighting async blocking or batch size issues.

**Trigger Keywords**: "debug", "why failing", "locate bug", "timeout"

---

## Task 3: Refactor Dual-Mode Transport Logic (General Worker)

**Objective**: Safely refactor server.py to extract transport logic into separate modules.

**Algorithmic Worker**: General Worker

**Task Description**:
```
process_task("Refactor server.py to extract the dual-mode transport logic (Stdio vs SSE) into a separate TransportManager class. The refactoring must preserve the --sse flag behavior and ensure backward compatibility with existing mcp_config.json files.")
```

**Expected Output**: Conflict-free code changes with version stamps, ensuring no race conditions if multiple agents work on server.py.

**Trigger Keywords**: "refactor", "restructure", "extract"

---

## Task 4: Map Memory Access Dependency Graph (HippoRAG)

**Objective**: Understand the architectural relationships between memory files and search triggers.

**Algorithmic Worker**: HippoRAG (AST + PageRank)

**Task Description**:
```
process_task("Analyze the memory system architecture and generate a dependency graph showing: 1) Which files reference 00_MASTER_PLAN.md, 2) Which workflows trigger memory archival, 3) The call chain from PLAN.md search triggers to actual file reads. Focus on docs/ai/memory/ and docs/PLAN.md.")
```

**Expected Output**: AST-based knowledge graph with PageRank scores showing the centrality of each memory component.

**Trigger Keywords**: "analyze", "understand", "map dependencies", "architecture"

---



## How to Execute

All of these tasks can be run via the `process_task` MCP tool or the CLI:

```bash
# Via CLI
python orchestrator.py task "Verify that the Memory Refresh protocol..."

# Via MCP
process_task("Debug why semantic search with Gemini...")
```

The orchestrator automatically routes each task to the appropriate algorithmic worker based on the instruction keywords.
