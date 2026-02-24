# API Reference

Programmatic interfaces for integrating with Swarm.

## MCP Protocol

Swarm implements the Model Context Protocol (MCP) specification.

### Connection

**Stdio (Docker):**
```bash
docker exec -i swarm-mcp-server fastmcp run server.py
```

**Direct (Development):**
```bash
python server.py
```

### Tool Invocation

MCP clients send tool requests as JSON:

```json
{
  "method": "tools/call",
  "params": {
    "name": "search_codebase",
    "arguments": {
      "query": "authentication",
      "keyword_only": false
    }
  }
}
```

## Python API

### Orchestrator

Direct access to the orchestrator loop:

```python
from mcp_core.orchestrator_loop import Orchestrator

# Initialize
orch = Orchestrator(root_path=".", session_id="my-session")

# Add a task
from mcp_core.swarm_schemas import Task
task = Task(
    description="Refactor authentication",
    assigned_worker="engineer"
)
orch.state.add_task(task)
orch.save_state()

# Process tasks
orch.process_task(task.task_id)
```

### LLM Router

```python
from mcp_core.llm import generate_response

response = generate_response(
    prompt="Explain this code...",
    model_alias="gemini-3-flash-preview"
)

print(response.status)  # SUCCESS, FAILED
print(response.reasoning_trace)
```

### HippoRAG

```python
from mcp_core.algorithms import HippoRAGRetriever

rag = HippoRAGRetriever()
rag.build_graph_from_ast(".", use_cache=True)

chunks = rag.retrieve_context("authentication", top_k=5)
for chunk in chunks:
    print(f"{chunk.file_path}:{chunk.start_line}")
```

### Ochiai SBFL

```python
from mcp_core.algorithms import OchiaiLocalizer

sbfl = OchiaiLocalizer()
prompt = sbfl.run_full_sbfl_analysis(
    test_command="pytest",
    source_path=".",
    top_k=5
)
print(prompt)  # Debugging instructions
```

### Telemetry

```python
from mcp_core.telemetry.collector import collector

# Record an action
signature = collector.record_provenance(
    agent_id="my-agent",
    role="engineer",
    action="file_modified",
    contributing_model="gemini-3-flash-preview",
    artifact_ref="src/auth.py"
)
```

### Sync Engine

```python
from mcp_core.sync.sync_engine import SyncEngine

sync = SyncEngine(root_path=".")

# Read PLAN.md into state
sync.sync_inbound(state)

# Write state back to PLAN.md
sync.sync_outbound(state)
```

## Schemas

### Task

```python
from mcp_core.swarm_schemas import Task

task = Task(
    description="Add user validation",
    assigned_worker="engineer",
    input_files=["user.py"],
    output_files=["user.py"],
    git_commit_ready=True
)
```

Key fields:
- `task_id`: Auto-generated UUID
- `status`: PENDING, IN_PROGRESS, COMPLETED, FAILED
- `assigned_worker`: architect, engineer, auditor, etc.
- `feedback_log`: List of execution messages

### ProjectProfile

The main state container:

```python
from mcp_core.swarm_schemas import ProjectProfile

profile = ProjectProfile()
profile.add_task(task)
profile.memory_bank["key"] = "value"
```

---

## Next Steps

- [Troubleshooting](./troubleshooting.md) — Common issues
- [Architecture](../concepts/architecture.md) — System design
