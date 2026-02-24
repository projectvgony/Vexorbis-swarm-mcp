# Swarm Git System

## Project Summary

The transition from human-centric software development to autonomous agentic workflows represents a fundamental shift in engineering paradigms. Project Swarm aims to operationalize this shift by establishing a fully autonomous, self-regulating software engineering system capable of managing its own lifecycle, expanding its codebase, and interacting with external repositories without human intervention.

This document details the technical implementation strategy, focusing on a robust Two-Tier State Architecture that resolves the dichotomy between high-velocity machine execution and human-readable strategic planning. The proposed architecture moves beyond simple "copilot" interactions, establishing a multi-agent system where specialized roles—Architect, Engineer, Senior, and Document Worker—collaborate via a shared "Blackboard" state pattern.

The rapid, atomic operations of coding agents (Tier 1) are continuously synchronized with strategic narratives and roadmaps intelligible to human stakeholders (Tier 2). The system integrates advanced Git interoperability mechanisms, specifically utilizing GIT_ASKPASS and GitHub App authentication to securely clone and contribute to external repositories, effectively allowing the swarm to traverse the open-source ecosystem.

Underpinning this autonomy is a rigorous telemetry system—the Flight Recorder—which captures the provenance of every decision. By logging context, reasoning traces, and outcomes, the system enables "Smart-Power" capabilities: self-pruning context windows and auto-generated issue detection. This document serves as the comprehensive technical blueprint for realizing Project Swarm.

---

## 1. Architectural Foundation: The Two-Tier State System

The central challenge in designing autonomous agents for long-running software projects is maintaining context coherence over time. Large Language Models (LLMs) suffer from limited context windows and "drift," where the strategic goal is lost amidst the noise of immediate execution details. Project Swarm employs a Two-Tier State Architecture that explicitly decouples execution state from strategic state.

### 1.1 Tier 1: Atomic Execution State (project_profile.json)

Tier 1 serves as the "machine memory" of the swarm. It is designed for high-frequency, low-latency access, acting as the definitive source of truth for the system's operational context. Unlike unstructured text, this state is maintained in a strictly typed JSON structure—**project_profile.json**—ensuring that agents interact with deterministic data points.

#### 1.1.1 Schema Design and Formal Definition

The stability of the autonomous system relies on the rigidity of its state schema. Project Swarm uses **Pydantic** models to validate **project_profile.json** at every write operation.

The state is encapsulated in a `ProjectProfile` class with the following core namespaces:

**system_metadata** (Integrated into Profile)
- `stack_fingerprint`: Auto-detected project stack
- `worker_models`: Configuration for different worker roles

**active_context**
- `memory_bank`: Rolling window of non-obvious project events

**task_queue** (tasks)
- `task_id`: Unique identifier
- `status`: PENDING/COMPLETED
- `description`: LLM-readable goal
- `git_commit_ready`, `git_auto_push`, `git_create_pr`: Flags for the Git workflow

**knowledge_graph**
- Managed separately via **HippoRAG** (AST-based graph) and cached in `.hipporag_cache`.

#### 1.1.2 Concurrency and Locking Mechanisms

In a multi-agent system, the Swarm uses a cross-platform file locking mechanism via the `filelock` library to ensure thread-safe and process-safe state modifications.

The **Orchestrator** handles this interaction:

1. **Acquire Lock**: Uses `FileLock("project_profile.json.lock")` with a timeout.
2. **Read**: Loads JSON into a `ProjectProfile` Pydantic model.
3. **Mutate**: Modifies the model instance.
4. **Write**: Serializes back to JSON using `model_dump_json()`.
5. **Release Lock**: Automatically released by the context manager.

### 1.2 Tier 2: Strategic State (Markdown Artifacts)

While Tier 1 is for the machine, Tier 2 is for "Hybrid Intelligence"—interfaces designed for human readability and strategic alignment. The artifacts **docs/ai/PLAN.md** and **issues.md** act as the long-term memory and strategic roadmap.

#### 1.2.1 The PLAN.md Artifact and the "Round-Trip" Challenge

**PLAN.md** contains the vision, phases, and high-level architectural decisions. The challenge is allowing the Architect Agent to update this file (e.g., checking off a milestone) without destroying human-authored comments, custom formatting, or indentation.

Converting Markdown to a generic Abstract Syntax Tree (AST) and back often results in "noisy" diffs where whitespace or formatting is aggressively normalized. To solve this, Project Swarm employs a **Hybrid Parsing Strategy**:

**Structure Identification (AST)**
Use a library like `mistune` or `marko` to parse the document structure, allowing the agent to semantically identify targets like "The Task List under the 'Phase 2' Header." Map these semantic locations to line numbers.

**Surgical Modification (Regex/StringOps)**
Once the target line is identified (e.g., Line 45: `- [ ] Implement Auth`), use precise string manipulation to toggle the checkbox from `[ ]` to `[x]`. Do not regenerate the file from the AST.

**Frontmatter Management**
Utilize `python-frontmatter` to handle metadata (YAML headers) separately from body content. This allows agents to update status tags (e.g., `status: active` to `status: maintenance`) without touching narrative text.

**Technical Implementation of Task Toggling:**

import re

def toggle_task(file_path, task_text, status):
    """
    Surgically toggles a markdown checkbox without re-serializing the file.
    Preserves formatting and indentation.
    """
    with open(file_path, 'r') as f:
        lines = f.readlines()

    # Regex to find the task list item, preserving indentation
    # Captures: 1=Indent, 2=CheckState, 3=Content
    pattern = re.compile(r"^(\s*)-\s\[([ x])\]\s(.*)")
    
    for idx, line in enumerate(lines):
        match = pattern.match(line)
        if match:
            indent, current_state, content = match.groups()
            if task_text in content:  # Fuzzy match or exact logic
                new_mark = 'x' if status else ' '
                lines[idx] = f"{indent}- [{new_mark}] {content}\n"
                break
    
    with open(file_path, 'w') as f:
        f.writelines(lines)

This method ensures "Round-Trip Safety," preserving the document's human touch.

#### 1.2.2 The issues.md Synchronization Bridge

The **issues.md** file serves as the input buffer for human operators. The Document Worker agent monitors this file for changes. When a human adds a new item:

1. **Detection**: Document Worker detects the diff
2. **Parsing**: Parses the new list item
3. **ID Generation**: Generates a unique ID (e.g., TASK-104)
4. **Sync**: Creates a corresponding entry in Tier 1 (project_profile.json → task_queue)
5. **Injection**: Rewrites the line in issues.md to append the ID: `- [ ] Fix login bug` becomes `- [ ] Fix login bug [TASK-104]`

This ID injection creates a permanent link between the strategic view (Tier 2) and the execution view (Tier 1), enabling bi-directional synchronization.

---

## 2. Specialized Agent Roles and Orchestration

To emulate a high-functioning engineering team, Project Swarm moves away from a generic "coder" agent to a system of specialized roles. This specialization optimizes context usage (prompts are narrower and deeper) and enforces checks and balances.

### 2.1 The Architect: Strategic Planner

**Responsibilities**: System design, feasibility analysis, dependency mapping.
**Workflow**: Uses `prompt_architect` and HippoRAG to decompose tasks.

### 2.2 The Engineer: The Execution Loop

**Responsibilities**: Implementation, testing, and debugging.
**Workflow**: Uses `prompt_engineer` and local git tools via `_execute_git_tool`.

### 2.3 The Auditor: Quality Assurance

**Responsibilities**: Code review, security analysis, and standards enforcement.
**Workflow**: Uses `prompt_auditor` to verify task completion and commit readiness.

---

### 3.1 Authentication via GITHUB_TOKEN

The current implementation relies on the `GITHUB_TOKEN` environment variable for authentication. `GitWorker` verifies the presence of this token before enabling PR-related workflow instructions.

### 3.2 External Contribution Capabilities

1. **Detection**: `GitWorker` identifies the provider (GitHub, GitLab, etc.) via `.git/config` remote URLs.
2. **Flags**: Tasks are flagged with `git_commit_ready`, `git_auto_push`, and `git_create_pr`.
3. **Execution**: The `Orchestrator` delegates operations to local git commands or the GitHub MCP server.

---

## 4. Telemetry: The "Flight Recorder" (provenance_log)

To achieve "Smart-Power," the system needs a subconscious—a memory of past actions, failures, and reasoning. The **provenance_log** acts as this flight recorder.

### 4.1 Structured Logging (Provenance)

Every action taken by an agent is logged as an **AuthorSignature** in the `provenance_log`. This ensures cryptographic-style provenance for all changes.

**Log Entry Schema (AuthorSignature):**

```python
{
  "agent_id": "uuid",
  "role": "engineer",
  "timestamp": "ISO-8601",
  "action": "modified",
  "signature": "optional-git-signature"
}
```

### 4.2 "Smart-Power": Context-Aware Prompting

The `memory_bank` serves as a rolling window of non-obvious project events, allowing the system to maintain context without overloading the LLM.

As the log grows, it exceeds the LLM context window. Project Swarm implements a **Semantic Pruning Strategy** rather than simple FIFO (First-In, First-Out).

**Algorithm:**

1. **Relevance Scoring**: When a new task starts, compute the cosine similarity between the task description embedding and the embeddings of past log entries
2. **Condensation**: High-relevance logs are kept in full. Low-relevance logs are summarized by the Project Summary Agent into single-line descriptors (e.g., "Refactored utils.py on 2025-01-12")
3. **Tail Preservation**: The last N actions are always preserved to maintain immediate continuity

This ensures the agent has "long-term memory" of relevant past architectural decisions while maintaining "short-term memory" of recent shell commands.

---

## 5. Automation and Infrastructure

The autonomy of Project Swarm is powered by its infrastructure. The system must live in an environment that is persistent enough to maintain state but ephemeral enough to be clean and reproducible.

### 5.1 GitHub Actions Cron Triggers

To simulate an "always-on" developer, Project Swarm utilizes GitHub Actions with a cron schedule.

**Schedule:** `*/30 * * * *` (Run every 30 minutes)

**Workflow Logic:**
1. **Checkout**: Clone the repo using the App Token
2. **State Check**: Read project_profile.json. Is a task in progress? Is there a new issue in issues.md?
3. **Agent Invocation**: If work is needed, spin up the relevant agent container
4. **Commit**: If the agent modified state or code, commit and push changes back to the repo

This "heartbeat" mechanism ensures the system is constantly evaluating the project state, effectively polling for work.

### 5.2 Containerization and Security

To ensure consistent execution environments for the agents (especially the Engineer running arbitrary code), agents run within a defined Docker container.

**Base Image:** A lightweight Python image (e.g., `python:3.9-slim`) ensures rapid spin-up times

**Dependencies:** Pre-install git, nodejs, and project-specific requirements to minimize runtime setup

**Security:** Run as a non-root user inside the container to limit the blast radius of any generated code execution. The container filesystem should be read-only except for the workspace volume.

**Infrastructure Components:**

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Scheduler** | GitHub Actions (Cron) | Provides the "heartbeat" trigger for agent activity |
| **Runtime** | Docker (Alpine/Slim) | Isolates agent execution environment and dependencies |
| **Auth** | GitHub App (JWT) | Provides granular, high-privilege access for git operations |
| **Search** | mcp_core | "Accelerator" for looking up docs/errors (Hybrid search) |

---

## 6. Implementation Roadmap

### Phase 1: Foundation (Completed)
- [x] Pydantic-based `ProjectProfile`
- [x] `FileLock` concurrency
- [x] HippoRAG integration

### Phase 2: Role Stabilization (Completed)
- [x] Specialized Architect/Engineer/Auditor prompt logic
- [x] Local Git command execution loop

### Phase 3: Git Worker Reliability (Active)
- [ ] Comprehensive unit tests for `GitWorker`
- [ ] Integration verification with GitHub MCP
- [ ] Secure token handling improvements

### Phase 4: Telemetry & Advanced Auth (Future)
- [ ] Intelligent pruning for `provenance_log`
- [ ] `GIT_ASKPASS` implementation for secure cloning
- [ ] GitHub App integration for branch bypass

---

## 7. Conclusion

Project Swarm represents a sophisticated application of agentic workflows applied to software engineering. By rigorously separating execution state from strategic planning (Tier 1 vs. Tier 2) and enforcing a role-based division of labor, the system achieves a level of stability and capability exceeding simple script-based assistants.

The integration of secure Git authentication via GIT_ASKPASS and GitHub Apps ensures that the swarm can operate as a first-class citizen in the open-source ecosystem, capable of managing dependencies and contributing to external projects. With the "Flight Recorder" providing long-term memory and observability, Project Swarm is positioned to become a fully autonomous, self-improving development entity.

The roadmap provides a phased, manageable path to full deployment, with early validation at each phase. By Week 8, the system should be capable of handling real-world software engineering tasks with minimal human intervention.

---