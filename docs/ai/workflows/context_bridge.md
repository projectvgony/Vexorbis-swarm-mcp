---
description: How to bridge context between conversations using artifacts.
---

# Context Bridge Workflow

This workflow describes how to preserve high-quality context across different AI sessions.

## 1. Closing a Session (Archiving)
When a major task is completed:

1.  **Synthesize, Don't Duplicate**: 
    - Do NOT copy full artifacts if they are already accessible. 
    - Use `refresh_memory` tool to consolidate active tasks to SQL.
    - No need to create manual summary files.
2.  **Naming**: `task_<name>.md` (in `docs/ai/active/`)
3.  **Update Loader**:
    - Edit `docs/ai/ROADMAP.md`.
    - Update the **Current Focus** and **Search Triggers** for the NEXT session.

## 2. Opening a Session (Restoring)
When starting a new conversation:

1.  **Read Dashboard**:
    Always start by reading `docs/ai/ROADMAP.md`.
2.  **Retrieve Context**:
    If specific details are needed, follow the links in "Recent Context" or use the `search_codebase` tool with queries related to the topic (e.g., "search engine refactor plan").
    *Note: `index_codebase` might need to be run if the memory files were just added.*

## 3. Maintenance
- Periodically review `ROADMAP.md` and use `search_archive` to find older context.
