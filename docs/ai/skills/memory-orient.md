# Memory Orienting Skill

Guide for agents to orient themselves within the Swarm context using the LLM-native memory system.

---

## When to Use This Skill

- Upon session start / context reset.
- When switching between major task phases.
- When arriving at a "What was I doing?" crossroad.

## The Orienting Protocol

### 1. Load the Context Bridge
Always start by reading the current high-level roadmap and search triggers:
```powershell
view_file("v:\Projects\Servers\swarm\docs\PLAN.md")
```

### 2. Trigger Targeted Memory Retrieval
Do NOT read entire directories. Use the `Search Triggers` found in `PLAN.md` to pull relevant artifacts:
- **Search Query**: Found in the triggers (e.g., `search_codebase("Swarm Master Plan")`).
- **Goal**: Load just enough context into the current window to understand the goal.

### 3. Identify Active Constraints
Cross-reference the `active/` directory for ongoing task files:
```powershell
list_dir("v:\Projects\Servers\swarm\docs\ai\memory\active")
```

## Success Metrics

- Agent identifies the 3 most critical files for the current task in under 2 tool calls.
- Context window usage is kept < 10% for "memory overhead".
