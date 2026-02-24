# Swarm AI Agent Guide: Autonomous Git Operations

## Overview
Swarm v3.2 introduces an **Autonomous Git Worker Team**. As an agent, you interact with this system by setting flags on the `Task` object. The Orchestrator handles the execution.

## 🧠 Decision Heuristics: When to use Git?

### 1. The "Unit of Work" Rule
Do NOT use Git for every file save. Use it when a logical **Task** is complete.
- **Bad**: "Fixed typo in line 10" -> Commit
- **Good**: "Implemented User Authentication" -> Commit + PR

### 2. Autonomous vs. Manual
- **Manual (Standard)**: You edit files. User commits later.
- **Autonomous (Git Flags)**: You set `git_commit_ready=True`. System commits immediately.
  - **Use when**: You are confident the task is 100% complete and tested.
  - **Avoid when**: You are "exploring" or "debugging" in a loop.

### 3. Branching Strategy
- **Feature Work**: Always use `git_branch_name="feature/..."`.
- **Hotfixes**: Use `git_branch_name="fix/..."`.
- **Main Branch**: Avoid direct commits to `main` unless told otherwise.

### 4. Human-in-the-Loop Nudge
- If you finish a task (`status="COMPLETED"`) but forget to set Git flags:
- The system checks `git status`.
- If changes exist, it adds a **Tip** to the feedback log: "📝 Uncommitted changes detected..."
- This prompts the user (or you in a later turn) to run the Git Worker explicitly.

## 🛡️ Spam Prevention & Safety

### Safety Check
- The Commit Worker **verifies file changes** before running.
- If `git status` is clean, it skips the commit (even if you requested it).
- **Why?** Prevents empty commits if the user reverted changes manually.

### Rate Limiting
- The system prevents "loops" by processing Git flags only once per task execution.
- **Auto-PR Guardrail**: `_handle_git_workflow` only creates a PR if the task status is `COMPLETED`.

### Idempotency
- If you set `git_create_pr=True` twice, the GitHub MCP (via Docker) handles "PR already exists" errors gracefully.
- However, aim to set it only once at the end of the workflow.

## 💰 Cost & Model Guidance

The system uses **Role-Based Model Routing** to save costs:

| Role | Model Alias | Recommended | Cost |
|------|-------------|-------------|------|
| **Engineer** | `gemini-3-flash-preview` | Complex Logic | Free (Google) |
| **Git Writer**| `gemini-3-flash-preview` | Commit Msgs, PRs | Free (Google) |
| **Local** | `ollama/llama3` | Offline/Secure | Free (Local) |

### How to use Local LLMs?
If you want to run completely offline (e.g. for privacy or zero cost):
1. Run Ollama or LM Studio.
2. Update config or env var `LOCAL_LLM_URL`.
3. Set `"git-writer": "ollama/llama3"` in `mcp_config.json`.

## 🔒 Internal Systems & Maintenance

Swarm v3.4 introduces **Tool Scoping** to separate general project tools from internal system maintenance.

### 1. Tool Scopes
- **General Scope** (Default): Standard tools for coding, searching, and git (`search_codebase`, `deliberate`, `git_worker`).
- **Internal Scope**: System-level tools for Swarm's own health (`check_health`, `mcp_transport_debug`).

### 2. Accessing Internal Tools
To access internal tools (e.g., for self-debugging), the environment must be configured:
- **Flag**: `SWARM_INTERNAL_TOOLS=true`
- **Effect**: Unlocks `check_health()` and transport debuggers.

### 3. Debugging Playbook
If you are tasked with debugging Swarm itself (not the user's project), refer to the [Debugging Playbook](debugging-playbook.md).

---

## 📝 Conventional Commits Format

All commits follow [Conventional Commits](https://conventionalcommits.org) specification:

**Format**: `type(scope): description`

**Types**:
- `feat`: New feature (minor version bump)
- `fix`: Bug fix (patch version bump)
- `docs`: Documentation only
- `refactor`: Code restructuring (no behavior change)
- `perf`: Performance improvement
- `test`: Adding/updating tests
- `chore`: Build process, tooling, dependencies
- `style`: Code formatting (no logic change)

**Scope Inference**:
- From `task.metadata["scope"]` if provided
- Otherwise inferred from first `output_file` directory
- Default: `"core"`

**Examples**:
```
feat(auth): implement OAuth2 login
fix(api): resolve null pointer in user endpoint
docs: update README with Docker setup
refactor(db)!: migrate to PostgreSQL

BREAKING CHANGE: Database schema changed
```

**Breaking Changes**:
Add `!` after scope OR include `BREAKING CHANGE:` footer for major version bumps.

**Auto-Inference**:
The system uses keywords in `task.description` to infer commit type automatically.

## ⚠️ CRITICAL: IDE Workflow vs Git State

**Your edits are NOT immediately visible to git.**

### The Three-Stage Pipeline

```
Agent Edit → IDE Approval → Git Detection
   (You)      (User)         (git status)
```

1. **Stage 1: You call `write_to_file`**
   - File change shown to user as "pending" in IDE
   - **NOT** written to disk yet
   - **NOT** visible to `git status`

2. **Stage 2: User accepts the change**
   - File written to filesystem
   - Now visible to `git status`

3. **Stage 3: Git operations can proceed**
   - `git add`, `git commit` work as expected

### Common Mistake

```python
# ❌ WRONG ASSUMPTION
write_to_file("server.py", ...)
run_command("git status")  # Will NOT show server.py (not accepted yet!)
```

### When checking git state

- `git status` shows **accepted changes** + **previous branch state**
- It does NOT show your current session's pending edits
- Staged files might be from OTHER branches or sessions

### Practical Tip

If you need to commit YOUR work:
1. Tell the user: "Please accept the file changes, then I'll commit"
2. OR use `git_commit_ready=True` flag (system handles timing)
3. Never assume `git status` reflects your current edits

---

## 📋 Checklist for Agents

1. **Check Context**: Is `git_available` in your prompt found?
2. **Work**: `write_to_file(...)`
3. **Verify**: Run tests.
4. **Finalize**:
   - Set `status="COMPLETED"`
   - Set `git_branch_name="feature/my-feature"`
   - (Optional) Set `git_commit_ready=True`
   - (Optional) Set `git_create_pr=True`

The **Orchestrator** will take it from there.
