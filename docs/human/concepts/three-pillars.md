# The Three Pillars

Swarm is built on three core design principles that differentiate it from simple LLM wrappers.

---

## 🧠 Pillar 1: Algorithmic Core

> **Go beyond text search. Use deterministic algorithms for reliability.**

Instead of asking an LLM to "find bugs" or "understand code," Swarm uses specialized algorithms:

### HippoRAG — Code Understanding

Uses Abstract Syntax Tree (AST) analysis + Personalized PageRank to understand code semantically.

**Supported Languages:**
- Python (built-in `ast`)
- JavaScript, TypeScript (Tree-sitter)
- Go, Rust (Tree-sitter)

**Example:**
```
search_codebase("authentication logic")
→ Finds OAuth, JWT, and session code across files
```

### Ochiai SBFL — Bug Finding

Statistical fault localization that analyzes test coverage:

1. Runs test suite with coverage instrumentation
2. Calculates "suspiciousness score" for each line
3. Reports Top-N most likely bug locations

**When Used:** Automatically activated when `tests_failing=True`

### Z3 Verifier — Formal Proofs

Symbolic execution using the Z3 SMT solver:
- Prove invariants hold for ALL inputs
- Find counterexamples that break assumptions
- Verify critical business logic

**Status:** Core integration complete; high-level generators in development

---

## 🤖 Pillar 2: Autonomous Workforce

> **Let specialized agents handle the grunt work.**

### Git Agent Roles

| Role | Trigger | Capabilities |
|------|---------|--------------|
| **Feature Scout** | `feature_discovery=True` | Scan TODOs, propose features, create issues |
| **Code Auditor** | `code_audit=True` | Security review, style checks, diff analysis |
| **Issue Triage** | `issue_triage_needed=True` | Prioritize backlog (P0-P3), suggest labels |
| **Branch Manager** | `git_create_pr=True` | Create PRs, manage merge queue, prune branches |
| **Project Lifecycle** | `project_bootstrap=True` | Initialize projects, generate templates |

### Dynamic Toolsmith

Swarm can create new tools at runtime:

```python
create_tool_file(
    filename="csv_parser.py",
    code="def register(mcp): ...",
    description="Parse CSV files"
)
restart_server("Loading new csv_parser tool")
```

### Markdown-Driven Control

Control agents via `PLAN.md`:

```markdown
- [ ] Add caching layer @architect
  - Context: cache.py, redis_client.py
  - Flags: git_commit_ready=True
```

---

## 🛡️ Pillar 3: Active Governance

> **Stay in control. Audit everything.**

### Telemetry Memory

SQLite-backed persistence (`~/.swarm/telemetry.db`):
- Session context survives restarts
- Decision history for debugging
- Tool performance metrics

### Self-Healing

Detects repeated failures and takes action:

```
Tool X failed 3 times in 24 hours
→ Circuit breaker trips
→ SYSTEM_ALERT injected: "Use alternatives"
```

### Provenance Tracking

Every action is logged with:
- Agent ID and role
- Contributing model
- Timestamp and artifact reference

This enables:
- Full audit trail
- Blame tracking for code changes
- Performance analysis

### Permission-First Philosophy

Autonomous actions require explicit gates:
- Tool creation needs `restart_server()` confirmation
- PR creation respects branch protection
- Destructive operations require flags

---

## Next Steps

- [Architecture Overview](./architecture.md) — System components
- [Git Workflows Guide](../guides/git-workflows.md) — Autonomous Git in detail
