# Tools Reference

Complete reference for all Swarm MCP tools.

## Search Tools

### search_codebase

Hybrid keyword + semantic code search.

```python
search_codebase(
    query: str,           # What to search for
    keyword_only: bool = False,  # Skip semantic matching
    top_k: int = 5        # Number of results
) -> str
```

**Performance:**
- Keyword only: ~1ms
- Semantic: ~240ms (requires embedding API call)

**Examples:**
```python
# Fast exact symbol lookup
search_codebase("UserAuthService", keyword_only=True)

# Conceptual search
search_codebase("authentication logic")
```

### retrieve_context

Deep AST analysis with PageRank for architectural understanding.

```python
retrieve_context(
    query: str,           # What to analyze
    top_k: int = 10       # Number of chunks
) -> str
```

**When to use:** After `search_codebase` when you need the "full picture."

### index_codebase

Build the semantic search index.

```python
index_codebase(
    path: str = ".",      # Root directory
    provider: str = "auto"  # gemini, openai, local, auto
) -> str
```

**Call this:** First time setup, after major code changes.

---

## Reasoning Tools

### deliberate

Structured problem-solving: Decompose → Analyze → Synthesize.

```python
deliberate(
    problem: str,         # The question
    steps: int = 3,       # Deliberation depth
    context: str = "",    # Additional context
    constraints: List[str] = None,  # Hard constraints
    return_json: bool = False
) -> str
```

**Example:**
```python
deliberate(
    problem="Should we use microservices?",
    context="Team of 5, 1M users expected",
    constraints=["Must deploy in 2 months"]
)
```

---

## Project Tools

### get_project_structure

Project tree with entry points and key files.

```python
get_project_structure(
    root_path: str = ".",
    max_depth: int = 3
) -> str
```

### count_files

Quick file counting.

```python
count_files(
    directory: str = ".",
    extension: str = ""   # e.g., ".py"
) -> int
```

---

## Memory Tools

### orient_context

Initialize session using memory systems.

```python
orient_context(session_id: str = None) -> str
```

### search_archive

Semantic search over historical sessions.

```python
search_archive(query: str, top_k: int = 5) -> str
```

### diagnose_error

Match error against knowledge base.

```python
diagnose_error(error_msg: str) -> str
```

---

## Git Tools

### validate_branch_name

Check branch naming convention.

```python
validate_branch_name(name: str) -> str
# Returns: "✅ Valid" or error with examples
```

### format_commit_message

Generate Conventional Commit message.

```python
format_commit_message(
    type: str,            # feat, fix, docs, etc.
    scope: str,           # Component name
    description: str,     # Short description
    body: str = "",       # Detailed body
    footer: str = ""      # BREAKING CHANGE, Closes #123
) -> str
```

### get_pr_template

Get standard PR body template.

```python
get_pr_template(type: str = "default") -> str
```

---

## System Tools

### restart_server

Restart Swarm to load new tools.

```python
restart_server(reason: str) -> str
```

### create_tool_file

Create new dynamic tool.

```python
create_tool_file(
    filename: str,        # e.g., "my_tool.py"
    code: str,            # Python code with register()
    description: str      # What it does
) -> str
```

### check_health

Server health status.

```python
check_health() -> str
```

### get_status

Current task queue status.

```python
get_status(limit: int = 10, show_all: bool = False) -> str
```

---

## Next Steps

- [Configuration](./configuration.md) — Environment variables
- [Troubleshooting](./troubleshooting.md) — Common issues
