# Branch Workflow Skill

Instructions for creating and managing Git feature branches.

---

## When to Use This Skill

- Starting work on a new feature or fix
- When `git_branch_name` is specified on a task
- Before making changes that should be isolated

## Branch Naming Convention

```
<type>/<short-description>
```

### Examples

| Type | Pattern | Example |
|------|---------|---------|
| Feature | `feature/<name>` | `feature/oauth-login` |
| Bug fix | `fix/<name>` | `fix/null-response` |
| Hotfix | `hotfix/<name>` | `hotfix/security-patch` |
| Refactor | `refactor/<name>` | `refactor/search-engine` |
| Docs | `docs/<name>` | `docs/api-reference` |

## Workflow

### 1. Start Fresh from Main
```bash
git checkout main
git pull origin main
```

### 2. Create Feature Branch
```bash
git checkout -b feature/<name>
```

### 3. Work on Feature
- Make changes
- Commit frequently with conventional commits
- Push to remote regularly

### 4. Keep Updated
```bash
git fetch origin
git rebase origin/main  # or merge
```

### 5. Push Branch
```bash
git push -u origin feature/<name>
```

## Rules

- Use lowercase and hyphens (no spaces)
- Keep names short but descriptive
- Delete branches after merge
- One branch per feature/fix

## Common Commands

```bash
# List branches
git branch -a

# Switch branches
git checkout <branch>

# Delete local branch
git branch -d <branch>

# Delete remote branch
git push origin --delete <branch>
```
