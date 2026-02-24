# Troubleshooting

Common issues and solutions.

## Installation Issues

### Docker container won't start

**Symptom:** `docker compose up` fails or container exits immediately.

**Solutions:**
1. Check logs: `docker logs swarm-mcp-server`
2. Verify API keys are set: `echo $GEMINI_API_KEY`
3. Rebuild: `docker compose down && docker compose up -d --build`

### "No module named 'mcp_core'"

**Symptom:** Import errors when running directly.

**Solution:**
```bash
pip install -e ".[dev]"
```

### Port already in use

**Symptom:** `bind: address already in use`

**Solution:**
```bash
# Find what's using port 8000
netstat -ano | findstr :8000  # Windows
lsof -i :8000                  # Linux/Mac

# Or change the port in docker-compose.yml
```

## Connection Issues

### IDE not connecting to Swarm

**Symptom:** MCP tools not appearing in IDE.

**Checklist:**
1. Container running? `docker ps | grep swarm`
2. Correct config path? Check IDE's MCP settings file
3. Restart IDE after config change
4. Check Docker logs for startup errors

### "Connection refused" errors

**Symptom:** Can't connect to `localhost:8000`

**Solutions:**
1. Check container is running
2. Verify port mapping: `docker port swarm-mcp-server`
3. Try `127.0.0.1` instead of `localhost`

## LLM Issues

### "No API keys available"

**Symptom:** Mock responses instead of real LLM output.

**Solution:**
```bash
export GEMINI_API_KEY="your-key-here"
# Then restart container
docker compose restart
```

### "Gemini API Error: 429"

**Symptom:** Rate limiting from Google.

**Solutions:**
1. Wait and retry (exponential backoff built-in)
2. Use fallback: Swarm cascades to other models
3. Consider local LLM: `ollama/llama3`

### Slow responses

**Symptom:** Tools take 30+ seconds.

**Causes:**
1. First-time indexing (normal for large codebases)
2. Semantic search API calls
3. Large context windows

**Solutions:**
1. Use `keyword_only=True` for fast searches
2. Pre-index: call `index_codebase()` once
3. Check network connectivity to Gemini API

## Git Issues

### "Uncommitted changes" blocking task completion

**Symptom:** Task stuck in PENDING after work is done.

**Cause:** Strict Git Mode (default).

**Solutions:**
1. Let Swarm commit: It will auto-commit
2. Commit manually: `git add . && git commit -m "..."`
3. Disable strict mode: `SWARM_STRICT_GIT=false`

### GitHub API errors

**Symptom:** Can't create issues/PRs.

**Checklist:**
1. Token set? `echo $GITHUB_TOKEN`
2. Token has correct scopes? (repo, issues, pull_request)
3. Rate limited? Check `docker logs swarm-mcp-server`

## Search Issues

### "No results found"

**Symptom:** `search_codebase` returns empty.

**Solutions:**
1. Re-index: `index_codebase()`
2. Try keyword search: `keyword_only=True`
3. Check file extensions are supported (.py, .js, .ts, .go, .rs)

### Semantic search returning irrelevant results

**Symptom:** Results don't match query intent.

**Solutions:**
1. Be more specific in query
2. Use `retrieve_context()` for architectural queries
3. Re-index with different provider

## Telemetry Issues

### "Database is locked"

**Symptom:** SQLite locking errors.

**Solution:**
```bash
# Restart container to release locks
docker compose restart

# Or manually clear locks (last resort)
rm ~/.swarm/telemetry.db-journal
```

### Telemetry DB growing too large

**Symptom:** Slow startup, large `~/.swarm/telemetry.db`.

**Solution:** Swarm auto-prunes events >30 days. For manual cleanup:
```python
from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService
analytics = TelemetryAnalyticsService()
analytics.prune_old_events(retention_days=7)
analytics.optimize_database()
```

## Getting Help

1. **Check logs:** `docker logs swarm-mcp-server`
2. **Enable debug:** `SWARM_DEBUG=true`
3. **GitHub Issues:** [AgentAgony/swarm/issues](https://github.com/AgentAgony/swarm/issues)

---

## Next Steps

- [Configuration](./configuration.md) — All settings
- [Installation](../getting-started/installation.md) — Setup guide
