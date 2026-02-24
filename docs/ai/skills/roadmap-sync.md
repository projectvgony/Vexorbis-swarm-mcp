# Roadmap Alignment Skill

Syncing short-term task progress with long-term memory (The Master Plan).

---

## When to Use This Skill

- When closing a major task.
- When the `MASTER_PLAN.md` milestones are achieved.
- Transitioning to a new Phase (e.g., moving from Phase 2 to Phase 3).

## Alignment Protocol

### 1. Verify Milestone Completion
Read the `docs/ai/ROADMAP.md` and identify the current active Phase.
```powershell
view_file("docs/ai/ROADMAP.md")
```

### 2. Checkmate Update
If all sub-tasks for a phase are done, update the milestone marker:
- Change `[ ]` to `[x]`.
- Add a "Date Completed" marker.
- Define the "High-Level Goal" for the next phase if it's missing.

### 3. Search Trigger Maintenance
If the Phase name changed, update `docs/ai/PLAN.md` to ensure the "Next Steps" section reflects the actual roadmap.

## Goal
The `ROADMAP.md` should always be the "Single Source of Truth" for the project's evolution, ensuring different agent sessions stay on the same vector.
