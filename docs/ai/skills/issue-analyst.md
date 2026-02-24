# Issue Analyst Skill

Skill for performing automated "pre-flight" technical impact analysis on new issues.

---

## When to Use This Skill

- Automatically when a new Issue is assigned to the "Agent Analyst" (or via workflow trigger).
- Manually when requested to "analyze the impact of this issue".

## The Analyst Protocol

### 1. Contextualize the Issue
- Read the issue body fully.
- Identify core keywords, error snippets, or mentioned files.

### 2. Trace the Impact
- Use `search_codebase` (keyword) for specific symbols.
- Use `retrieve_context` (HippoRAG) to find architectural dependencies and call sites.
- **Goal**: Identify the "Blast Radius" – which files see this change.

### 3. Generate Technical Impact Plan
- Create an `implementation_plan.md` in `docs/ai/active/`.
- **Must Include**:
    - **Root Cause Analysis**: Why is this happening?
    - **Affected Components**: List of files.
    - **Risk Level**: High/Med/Low (e.g., "High" if changing HippoRAG retrieval logic).
    - **Verification Strategy**: Specific tests to run.

### 4. Report to GitHub
- Post the "Technical Impact Summary" as a comment on the GitHub issue.
- Link to the local `implementation_plan.md` (or paste a condensed version).

## Success Metrics

- Analyst identifies >80% of affected files in the first pass.
- Impact report is posted within 60 seconds of issue detection.
