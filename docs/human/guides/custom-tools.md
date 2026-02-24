# Creating Custom Tools

Extend Swarm with new capabilities at runtime.

## Overview

Swarm's Dynamic Toolsmith allows agents to create new MCP tools without restarting the entire system.

## Creating a Tool

### Step 1: Use create_tool_file

```python
create_tool_file(
    filename="csv_analyzer.py",
    code='''
from fastmcp import FastMCP

def register(mcp: FastMCP):
    @mcp.tool()
    def analyze_csv(file_path: str, column: str) -> str:
        """
        Analyze a column in a CSV file.
        
        Usage Heuristics:
        - Use when: User wants statistics on CSV data
        - Returns: Mean, median, mode statistics
        """
        import pandas as pd
        df = pd.read_csv(file_path)
        col = df[column]
        return f"Mean: {col.mean()}, Median: {col.median()}"
''',
    description="Analyze CSV file columns"
)
```

### Step 2: Restart Server

```python
restart_server("Loading new csv_analyzer tool")
```

### Step 3: Use the Tool

```
Analyze the 'price' column in data.csv
```

## Tool Requirements

Every tool file must:

1. **Import FastMCP:**
   ```python
   from fastmcp import FastMCP
   ```

2. **Have a register function:**
   ```python
   def register(mcp: FastMCP):
       ...
   ```

3. **Use the @mcp.tool() decorator:**
   ```python
   @mcp.tool()
   def my_tool(arg: str) -> str:
       ...
   ```

4. **Include Usage Heuristics in docstring:**
   ```python
   """
   Tool description.
   
   Usage Heuristics:
   - Use when: [conditions]
   - Don't use when: [conditions]
   """
   ```

## Tool Location

Created tools are saved to:
```
mcp_core/tools/dynamic/your_tool.py
```

## Example: Project Stats Tool

```python
def register(mcp: FastMCP):
    @mcp.tool()
    def project_stats() -> str:
        """
        Get project statistics.
        
        Usage Heuristics:
        - Use when: User asks about project size or metrics
        - Returns: File counts, line counts, language breakdown
        """
        from pathlib import Path
        import os
        
        stats = {"files": 0, "lines": 0, "by_ext": {}}
        
        for root, dirs, files in os.walk("."):
            dirs[:] = [d for d in dirs if not d.startswith(".")]
            for f in files:
                path = Path(root) / f
                ext = path.suffix or "no_ext"
                stats["files"] += 1
                stats["by_ext"][ext] = stats["by_ext"].get(ext, 0) + 1
                try:
                    stats["lines"] += len(path.read_text().splitlines())
                except:
                    pass
        
        return f"Files: {stats['files']}, Lines: {stats['lines']}, By type: {stats['by_ext']}"
```

## Security Considerations

- Tools run with the same permissions as Swarm
- Code is validated for the `register` function
- User approval is required for `restart_server`

## Debugging Tools

Enable verbose logging:
```bash
export SWARM_DEBUG=true
```

View tool loading:
```bash
docker logs swarm-mcp-server 2>&1 | grep "tool"
```

---

## Next Steps

- [Tools Reference](../reference/tools.md) — Built-in tools
- [Configuration](../reference/configuration.md) — Environment settings
