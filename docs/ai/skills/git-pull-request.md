# Pull Request Skill

Instructions for creating well-documented pull requests on GitHub.

---

## When to Use This Skill

- After pushing a feature branch to remote
- When a task is complete and ready for review
- When `git_create_pr` flag is set on a task

## PR Title Format

```
<type>(<scope>): <description>
```

Same format as commits. Keep under 72 characters.

## PR Body Template

```markdown
## Summary
[1-2 sentence description of what this PR does]

## Changes
- [Bullet list of specific changes]
- [Include file names when helpful]

## Testing
- [ ] Unit tests pass
- [ ] Manual testing completed
- [ ] No regressions

## Related
- Closes #<issue_number>
- Related to #<issue_number>

---
*Automated PR from Swarm Orchestrator*
```

## Workflow

1. **Ensure branch is pushed**: `git push origin <branch>`
2. **Create PR** using GitHub MCP or CLI:
   ```
   gh pr create --title "<title>" --body "<body>" --base main
   ```
3. **Add reviewers** if required
4. **Link issues** in description

## Best Practices

- One PR per feature/fix
- Keep PRs small (<400 lines ideally)
- Include screenshots for UI changes
- Request specific reviewers for domain expertise
- Respond to review comments promptly

## GitHub MCP Tool

```python
create_pull_request(
    owner="<repo_owner>",
    repo="<repo_name>",
    title="<type>(<scope>): <description>",
    head="<feature_branch>",
    base="main",
    body="<pr_body>"
)
```
