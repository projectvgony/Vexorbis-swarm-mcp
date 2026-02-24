# Conventional Commits Skill

Instructions for creating well-formatted Git commits following the Conventional Commits specification.

---

## When to Use This Skill

- After completing code changes that need to be committed
- When you see uncommitted changes in the working directory
- When a task is marked as complete and ready for version control

## Commit Message Format

```
<type>(<scope>): <description>

[optional body]

[optional footer(s)]
```

## Types

| Type | Emoji | Use For |
|------|-------|---------|
| `feat` | ✨ | New feature |
| `fix` | 🐛 | Bug fix |
| `docs` | 📚 | Documentation only |
| `style` | 💄 | Formatting, no code change |
| `refactor` | ♻️ | Code restructuring |
| `test` | ✅ | Adding/updating tests |
| `chore` | 🔧 | Maintenance tasks |
| `perf` | ⚡ | Performance improvement |

## Scope Guidelines

- Use the module or component name: `auth`, `api`, `ui`
- Use the file name for single-file changes: `server.py`
- Omit scope for broad changes

## Examples

```bash
# Feature
git commit -m "✨ feat(auth): add OAuth2 login support"

# Bug fix
git commit -m "🐛 fix(api): handle null response in user endpoint"

# Refactor
git commit -m "♻️ refactor(search): extract keyword matching to helper"

# Documentation
git commit -m "📚 docs: update API reference with new endpoints"
```

## Commit Workflow

1. **Stage files**: `git add <files>` or `git add .`
2. **Review staged**: `git status` to confirm
3. **Commit**: `git commit -m "<type>(<scope>): <description>"`
4. **Verify**: `git log -1 --oneline`

## Rules

- Keep subject line under 72 characters
- Use imperative mood ("add" not "added")
- Don't end subject with period
- Separate subject from body with blank line
- Body should explain *why*, not *what*
