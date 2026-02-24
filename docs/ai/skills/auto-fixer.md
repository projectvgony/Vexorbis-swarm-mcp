# Auto-Fixer Skill

Skill for autonomous resolution of low-to-medium complexity issues.

---

## When to Use This Skill

- When an issue is assigned to "Agent Fixer" and an `implementation_plan.md` has been approved (by a human or an `issue-analyst`).

## The Resolution Protocol

### 1. Load context
- Read the issue and the associated `implementation_plan.md`.
- Verify the current branch is `fix/issue-<id>`.

### 2. Implementation Loop
- Execute changes as defined in the plan.
- Use `validate_all.py` relentlessly.
- **Backtrack**: If a change causes a regression, use `git restore` and update the `task.md` with the new findings.

### 3. Generate Walkthrough
- Create `docs/ai/walkthrough.md` (or update existing).
- List exactly what was fixed and what tests pass.
- Link to the `implementation_plan.md`.

### 4. Create Pull Request
- Use `format_commit_message` for a professional history.
- Use `pull_request_template.md` and populate the `AGENT_METADATA` block.

## Success Metrics

- >90% of PRs pass CI on the first attempt.
- Zero manual edits required by humans for "simple" bugs.
