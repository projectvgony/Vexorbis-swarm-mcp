# Configuration

All environment variables and settings for Swarm.

## Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (primary LLM) | `AIza...` |
| `OPENAI_API_KEY` | OpenAI API key (fallback) | `sk-...` |

At least one LLM key is required for full functionality.

## Optional Variables

### LLM Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `LOCAL_LLM_URL` | `http://localhost:11434/v1` | Ollama/LM Studio endpoint |
| `LOCAL_EMBED_MODEL` | `nomic-embed-text` | Local embedding model |
| `EMBEDDING_PROVIDER` | `auto` | `gemini`, `openai`, `local`, `auto` |

### Git Integration

| Variable | Default | Description |
|----------|---------|-------------|
| `GITHUB_TOKEN` | - | GitHub Personal Access Token |
| `SWARM_STRICT_GIT` | `true` | Enforce commit before task completion |

### Debugging

| Variable | Default | Description |
|----------|---------|-------------|
| `SWARM_DEBUG` | `false` | Enable verbose logging |
| `SWARM_TRACE_PROMPTS` | `false` | Log LLM prompts (truncated) |
| `SWARM_VERBOSE_TELEMETRY` | `false` | Detailed telemetry output |
| `SWARM_SBFL_ENABLED` | `false` | Enable Ochiai fault localization |

### Internal Tools

| Variable | Default | Description |
|----------|---------|-------------|
| `SWARM_INTERNAL_TOOLS` | `false` | Load debug/maintenance tools |

### Database

| Variable | Default | Description |
|----------|---------|-------------|
| `POSTGRES_URL` | - | PostgreSQL connection URL for session persistence |
| `SWARM_SESSION_ID` | auto-generated | Override session identifier |
| `SWARM_AGENT_ID` | auto-generated | Override agent identifier |

## Configuration Files

### project_profile.json

The Blackboard state file. Key fields:

```json
{
  "stack_fingerprint": {
    "primary_language": "python",
    "frameworks": ["fastapi", "pydantic"]
  },
  "worker_models": {
    "default": "gemini-3-flash-preview",
    "architect": "gemini-2.5-pro",
    "git-writer": "gemini-3-flash-preview"
  },
  "toolchain_config": {
    "test_command": "pytest",
    "lint_command": "ruff check ."
  }
}
```

### PLAN.md

Roadmap file for Antigravity Sync. Location: project root or `docs/ai/PLAN.md`.

See [Using PLAN.md](../guides/plan-syntax.md) for syntax.

## Docker Configuration

### docker-compose.yml Overrides

```yaml
services:
  swarm:
    environment:
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - GITHUB_TOKEN=${GITHUB_TOKEN}
      - SWARM_DEBUG=true
    volumes:
      - ./:/app
      - ~/.swarm:/root/.swarm  # Persist telemetry DB
```

### Resource Limits

Default limits in docker-compose.yml:

```yaml
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 2G
```

## Security Settings

Docker containers run with:
- `security_opt: no-new-privileges:true`
- `cap_drop: ALL`
- Read-only filesystem with tmpfs mounts

---

## Next Steps

- [API Reference](./api.md) — Programmatic interfaces
- [Troubleshooting](./troubleshooting.md) — Common issues
