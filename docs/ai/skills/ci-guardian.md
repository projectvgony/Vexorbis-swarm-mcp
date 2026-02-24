# CI Guardian Skill

Skill for proactive architectural review and validation of Pull Requests.

---

## When to Use This Skill

- Automatically when a Pull Request is opened in the repository.
- Manually during "Pre-merge Audit".

## The Guardian Protocol

### 1. The Surface Scan
- Check the CI status badge in README (from the CI run).
- Scan the PR diff for "smells" (e.g., hardcoded secrets, large deletions).

### 2. Architectural Deep-Dive
- Use HippoRAG (`retrieve_context`) on changed files to see if call signatures broke downstream dependencies NOT included in the PR.
- Check if the `walkthrough.md` matches the code changes.

### 3. Verification Audit
- Look for the `AGENT_METADATA` in the PR.
- If missing, flag as "Manual Review Required".
- If present, verify the `validation_gates` listed in the metadata were actually run (by checking CI logs).

### 4. Certification
- Post a comment summarizing the architectural risk.
- **Vote**: "Approving" (Safe to merge), "Requesting Changes" (Architectural risk), or "Observation" (Minor issues).

## Success Metrics

- Zero "breaking changes" merged into `main` without a warning from the Guardian.
- Average audit time under 3 minutes.
