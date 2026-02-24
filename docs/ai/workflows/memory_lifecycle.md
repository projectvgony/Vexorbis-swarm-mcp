# Memory Lifecycle Workflow

> **Usage**: Follow this protocol to prevent memory bloat while keeping knowledge accessible.

## Tiers
- **`active/`**: Current. Max ~10 files. High detail.
- **`archive`**: Historical. Moved to PostgreSQL (pgvector).

## Protocol: "Consolidate & Prune"

### 1. Task Start
Create a file in `active/` for significant tasks:
```
docs/ai/active/task_<short_name>.md
```

### 2. Task End
Update the file with a **Resolution** section.

### 3. Refresh (Weekly/Sprint Boundary)
When `active/` exceeds 10 files:
3.  Run `refresh_memory()` tool.
4.  This tool archives content to PostgreSQL and **deletes** the original files.

## Permanent Files (Never Delete)
- `ROADMAP.md`: Strategic roadmap.
- `PostgreSQL Error Knowledge`: Database-backed diagnostic knowledge base accessible via `diagnose_error`.
