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
