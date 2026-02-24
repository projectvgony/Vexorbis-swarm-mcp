# Memory Refresh Skill

Procedures for consolidating and compressing the Swarm's memory to prevent context bloat.

---

## When to Use This Skill

- When `docs/ai/memory/active/` contains > 10 files.
- At the end of every work session.
- Weekly/Daily boundaries.

## Consolidation Protocol

### 1. The Audit
Scan the `active/` directory for "Completed" tasks or resolved issues.
```powershell
list_dir("v:\Projects\Servers\swarm\docs\ai\memory\active")
```

### 2. Summarize & Extract
For each completed task:
- Extract the **Core Insight** (the "lesson learned").
- Extract the **Permanent Fix** (the configuration/code change).
- Ignore the conversational logs or intermediate trial/error.

### 3. Append to Archive
Add the extracted insights to the monthly summary:
`docs/ai/memory/archive/2026_01_Summary.md`

### 4. Prune
Delete the raw `task_*.md` files once captured in the archive summary.

## Safety Guard
NEVER delete:
- `00_MASTER_PLAN.md`
- PostgreSQL Error Knowledge (Managed by DB)
- Any file with an `[ACTIVE]` tag.
