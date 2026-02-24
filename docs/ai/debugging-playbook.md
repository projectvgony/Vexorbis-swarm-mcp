# Debugging Playbook - Swarm at Scale

This playbook provides actionable strategies for debugging and maintaining Swarm as it scales. It is designed for **Internal Use** - utilizing system-level tools available only when `SWARM_INTERNAL_TOOLS=true`.

---

## Quick Reference

| Symptom | Tool | Action |
|---------|------|--------|
| Failing tools | `check_health()` | Check success rates |
| Loop detected | Review provenance log | Use `Orchestrator.check_loop_state()` |
| Transport issues | `debug_mcp_transport()` | Test SSE/Docker connectivity |
| Slow queries | Telemetry analytics | Optimize or prune DB |

---

## 1. Telemetry & Observability

### Core Infrastructure

**Telemetry Database**: `~/.swarm/telemetry.db`
- Tracks all tool usage, success rates, and durations
- Automatic WAL mode for concurrent access
- Retention: 30 days (configurable)

**Analytics Service**: `TelemetryAnalyticsService`
```python
from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService

analytics = TelemetryAnalyticsService()

# Check tool reliability
success_rate = analytics.get_tool_success_rate("search_codebase", window_days=7)
print(f"Success rate: {success_rate:.1%}")

# Find problematic tools
problems = analytics.get_problematic_tools(threshold=0.7)
for p in problems:
    print(f"{p['tool']}: {p['success_rate']:.1%} ({p['total_uses']} uses)")
```

### Health Check Tool

**Internal Tool**: `check_health()`

Available only when `SWARM_INTERNAL_TOOLS=true`. Provides:
- Telemetry DB size and status
- Tool success rate summary
- PostgreSQL connection status
- Environment configuration

**Usage**:
```bash
# Enable internal tools
export SWARM_INTERNAL_TOOLS=true

# Run health check
# (call check_health() via MCP)
```

### Circuit Breaker Pattern

Tools are monitored for reliability using a three-state circuit breaker:

- **READY** (≥70% success): Normal operation
- **WARNING** (30-70% success): Monitor closely
- **TRIPPED** (<30% success): Temporarily disabled

```python
status = analytics.get_tool_status("my_tool", window_days=1)
# Returns: "READY", "WARNING", or "TRIPPED"
```

---

## 2. Loop Detection & Recovery

### Detection Mechanism

`Orchestrator.check_loop_state()` uses provenance logs to detect stuck tasks:
- Computes state fingerprint from last N provenance entries
- Detects repeated state hashes
- Automatically fails looped tasks

### Recovery Strategies

**When a loop is detected:**

1. **Review Provenance Log**:
   ```python
   profile = orchestrator.state
   recent_log = profile.provenance_log[-10:]
   # Examine action patterns
   ```

2. **Analyze Task History**:
   Check if the same tool chain is repeating

3. **Adjust Constraints**:
   Add constraints to break the cycle:
   ```python
   deliberate(problem="...", constraints=["Avoid using tool X"])
   ```

### Tuning

Adjust loop detection sensitivity in `orchestrator_loop.py`:
- **Window size**: Number of provenance entries to analyze
- **Threshold**: Number of repeated hashes to trigger detection

---

## 3. Transport Debugging

### MCP "The Gate" Issues

**Internal Tool**: `debug_mcp_transport()`

Use when experiencing connectivity problems.

**SSE (HTTP) Connection Testing**:
```python
debug_mcp_transport(target_url="http://localhost:8000/sse")
# Reports: Status code, latency, errors
```

**Docker Stdio Testing**:
```python
debug_mcp_transport(container_name="swarm-container")
# Verifies: docker exec reachability, Python runtime
```

### Common Issues

| Error | Cause | Solution |
|-------|-------|----------|
| `Connection Refused` | Port not exposed | Check Docker `-p` mappings |
| `Timeout` | Firewall blocking | Allow port in Windows Firewall |
| `EOF` | Container not running | Check `docker ps` |

---

## 4. Fault Localization (SBFL)

### Ochiai Localizer

**When tests fail**, use SBFL to pinpoint suspected lines:

```python
from mcp_core.algorithms import OchiaiLocalizer

localizer = OchiaiLocalizer()
# Requires pytest coverage data
localizer.analyze_from_coverage(".coverage")

# Get ranked suspiciousness scores
suspicious_lines = localizer.get_ranked_suspects(top_k=10)
```

### Integration with Debugger Skill

The `debugger.md` skill automatically uses SBFL when `tests_failing` flag is set:
1. Run failing tests
2. Capture coverage data
3. Rank suspicious lines
4. Focus debugging effort

---

## 5. Scale Maintenance

### Database Optimization

**Prune Old Events**:
```python
analytics = TelemetryAnalyticsService()
deleted = analytics.prune_old_events(retention_days=30)
print(f"Pruned {deleted} old events")
```

**Optimize DB**:
```python
analytics.optimize_database()
# Runs VACUUM and enables WAL mode
```

### Monitoring Thresholds

**Recommended alerts**:
- Telemetry DB > 100 MB → Prune
- Any tool <30% success → Investigate
- Loop detected → Review task constraints
- PostgreSQL disconnected → Check config

### Automated Checks

Create a cron job or GitHub Action:
```bash
#!/bin/bash
export SWARM_INTERNAL_TOOLS=true
python -c "
from mcp_core.tools.internal.check_health import check_health
print(check_health())
"
```

---

## Troubleshooting Workflows

### Workflow 1: Tool Failure Investigation

1. Run `check_health()` → Identify failing tool
2. Query telemetry:
   ```python
   analytics.get_tool_success_rate("tool_name", window_days=7)
   ```
3. Check error categories:
   ```sql
   SELECT error_category, COUNT(*) 
   FROM events 
   WHERE tool_name = 'tool_name' AND success = 0
   GROUP BY error_category;
   ```
4. Implement fix or disable tool temporarily

### Workflow 2: Performance Degradation

1. Check DB size: `ls -lh ~/.swarm/telemetry.db`
2. Prune old events: `analytics.prune_old_events()`
3. Analyze slow tools: `analytics.get_avg_duration("tool_name")`
4. Optimize indexing or caching

### Workflow 3: System Health Audit

1. Enable internal tools: `export SWARM_INTERNAL_TOOLS=true`
2. Run health check: Call `check_health()`
3. Review telemetry summary
4. Test transport: `debug_mcp_transport(...)`
5. Verify PostgreSQL connectivity

---

## Best Practices

### DO:
- ✅ Run `check_health()` before major operations
- ✅ Monitor telemetry DB growth weekly
- ✅ Use circuit breaker status to disable flaky tools
- ✅ Prune telemetry data monthly
- ✅ Enable verbose logging (`SWARM_VERBOSE_TELEMETRY=true`) during debugging

### DON'T:
- ❌ Disable telemetry collection (needed for self-healing)
- ❌ Ignore WARNING status tools (they may degrade further)
- ❌ Let telemetry DB exceed 500 MB
- ❌ Skip loop detection tuning for your workload
- ❌ Use internal tools in production client code

---

## Related Documentation

- [`debugger.md`](../skills/debugger.md) - Agent debugging skill
- [`telemetry_analytics.py`](../../mcp_core/telemetry/telemetry_analytics.py) - Analytics implementation
- [`orchestrator_loop.py`](../../mcp_core/orchestrator_loop.py) - Loop detection code
- [ARCHITECTURE.md](../../ARCHITECTURE.md) - System architecture overview

---

**Last Updated**: 2026-01-22  
**Scope**: Internal System Maintenance
