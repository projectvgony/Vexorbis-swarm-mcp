# Memory Capture Skill

Instructions for recording high-fidelity context into the Swarm's "active" memory tier.

---

## When to Use This Skill

- After identifying a non-obvious root cause of a bug.
- When making a strategic design decision.
- When starting a task that will span multiple turns or restarts.

## Capture Heuristics

### 1. Create Active Task Log
If a task is complex, create a dedicated file:
`docs/ai/active/task_<name>.md`

### 2. Include "Current State" Snapshots
Don't just describe the plan; capture the state of the world:
- File paths involved.
- Command outputs (errors/success).
- Pending blockers.

### 3. Log Errors Immediately
If a "Connection Refused" or "EOF" occurs, query `diagnose_error()` before attempting a second fix. This prevents "infinite loops" of failed patterns. If you fix a new type of error, use `contribute_error_fix()` to update the global knowledge.

## Required Format

- **Context**: Why are we doing this?
- **Pattern**: What error or code structure was found?
- **Insight**: Why did the generic fix fail?
- **Action**: What is the specific solution?
