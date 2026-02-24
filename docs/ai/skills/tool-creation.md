# Tool Creation Skill

Instructions for extending Swarm with new MCP tools.

---

## When to Use This Skill

- When a capability is missing and needed >3 times
- When automating a task that saves >5 minutes
- When the user explicitly requests a new tool

## When NOT to Use

- One-off tasks (do manually)
- Simple file edits
- Tasks AI can already do natively

## Tool Template

```python
from typing import Any
from fastmcp import FastMCP

def register(mcp: FastMCP):
    @mcp.tool()
    def my_tool(arg1: str, arg2: int = 10) -> str:
        """
        Brief description of what this tool does.
        
        Usage Heuristics:
        - Use when: [specific scenario]
        - Don't use when: [anti-pattern]
        
        Args:
            arg1: Description of first argument
            arg2: Optional second argument (default: 10)
            
        Returns:
            Description of return value
        """
        # Implementation
        return f"Processed {arg1}"
```

## File Location

Place new tools in: `mcp_core/tools/dynamic/`

## Required Elements

1. **`register(mcp)` function** - Entry point
2. **`@mcp.tool()` decorator** - Registers with MCP
3. **Type hints** - All args and return
4. **Docstring** with:
   - Brief description
   - Usage Heuristics section
   - Args documentation
   - Returns documentation

## Process

1. **ROI Check**: Is this worth building?
2. **Design**: Define signature and behavior
3. **Permission**: Ask user before creating
4. **Implement**: Create the tool file
5. **Restart**: Call `restart_server()` to load

## Example: File Counter Tool

```python
from pathlib import Path
from fastmcp import FastMCP

def register(mcp: FastMCP):
    @mcp.tool()
    def count_files(directory: str = ".", extension: str = "") -> str:
        """
        Count files in a directory, optionally filtered by extension.
        
        Usage Heuristics:
        - Use when: Need quick file counts for planning
        - Don't use when: Need detailed file information
        
        Args:
            directory: Path to count files in
            extension: Optional filter (e.g., ".py")
            
        Returns:
            Count of matching files
        """
        path = Path(directory)
        if extension:
            files = list(path.rglob(f"*{extension}"))
        else:
            files = list(path.rglob("*"))
        return f"Found {len(files)} files"
```
