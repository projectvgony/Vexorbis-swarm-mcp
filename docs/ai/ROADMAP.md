# Swarm Project Roadmap

> **Role**: Strategic Roadmap & Long-Term Memory
> **Usage**: Reference this file to understand the project's strategic direction and current status.

## 🌟 Strategic Goal
Create a self-organizing, autonomous "Swarm" of AI agents capable of maintaining and evolving a codebase with minimal human intervention.

## 🗺️ Roadmap & Status

### Phase 3: The Sensor (Completed ✅)
- [x] **HippoRAG Retriever**: AST-based knowledge graph for deep context.
- [x] **Ochiai Localizer**: Statistical fault localization (SBFL).
- [x] **Polyglot Parsing**: Tree-sitter integration for Python, JS, TS, Go, Rust.
- [x] **Hybrid Search**: Semantic + Keyword + Graph optimization.

### Phase 4: Dynamic Tooling & Debug (Completed ✅)
- [x] **Dynamic Tool Loader**: Load MCP tools at runtime.
- [x] **Multiplexed Terminal**: Interactive terminal sessions.
- [x] **Transport Debugger**: SSE/Stdio connectivity probes.

### Phase 4.5: The Hands (Current Focus 🚧)
- [ ] **Autonomous Git Engine (In Progress)**:
    - [ ] `FeatureScout`: Proactive feature proposal (Skeleton).
    - [ ] `CodeAuditor`: Automated quality control (Skeleton).
    - [ ] `IssueTriage`: Backlog management (Skeleton).
    - [ ] `BranchManager`: Stacked PR handling (Skeleton).
- [ ] **Deliberation Tool**: Multi-step algorithmic reasoning (Stub).

### Phase 5: Future Horizons (Backlog)
- [ ] **Collaborative Swarm**: Enable Swarm-to-Swarm communication protocol.
- [ ] **Neural Bug Detection**: ML model on provenance logs to predict failure points.
- [ ] **Advanced Verification**: High-level Z3 contract generators.
- [ ] **Java Support**: Additional language parser.

## 🧠 Memory Bank Index
*Memory is now managed by PostgreSQL (pgvector). Use the following tools to access long-term memory:*

- **Search Content**: `search_archived_memory(query)`
- **Retrieve Architecture**: `retrieve_context("Swarm Architecture")`
- **Error History**: `diagnose_error(error_msg)`
- **Session State**: Managed automatically by `postgres_client.py`

## 📝 Active Constraints
1.  **Duplicate Storage**: Do NOT duplicate artifacts. Synthesis only.
2.  **Server Config**: Must use `127.0.0.1` for MCP connectivity on Windows.

- [/] New Test Task (claimed by test_verification_session)
- [ ] Surprise Task
- [ ] New Test Task
- [ ] New Test Task
- [/] New Test Task 1771892063 (claimed by test_verification_session)
- [ ] Surprise Task