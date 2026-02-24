"""
Project Map Tool

Generates a high-level cached map of the project structure to reduce search overhead.

Usage Heuristics:
- Use when: Agent needs to understand project structure without repeated searches
- Don't use when: Searching for specific code content (use search_codebase)
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Optional
from collections import defaultdict
import ast







def register(mcp):
    """Register project_map tools with FastMCP server."""
    
    @mcp.tool()
    def get_project_structure(root_path: str = ".", max_depth: int = 3) -> str:
        """
        Generate a high-level project structure map.
        
        **When to use:**
        - Understanding project layout without repeated searches
        - Finding entry points (main.py, server.py, etc.)
        - Identifying key files (largest, most important)
        
        **When NOT to use:**
        - Searching for specific code content (use search_codebase)
        - Deep dependency analysis (use retrieve_context)
        
        Args:
            root_path: Root directory to map (default: current directory)
            max_depth: Maximum directory depth to traverse (default: 3)
            
        Returns:
            JSON string with project structure, entry points, and key files
        """
        result = _get_project_structure(root_path, max_depth)
        import json
        return json.dumps(result, indent=2)
    
    @mcp.tool()
    def analyze_dependencies(module_path: str) -> str:
        """
        Analyze imports and dependencies for a specific Python module.
        
        **When to use:**
        - Understanding what a module imports
        - Finding exported classes/functions from a module
        - Analyzing module coupling
        
        Args:
            module_path: Path to Python module
            
        Returns:
            JSON string with imports, from_imports, and exports (classes/functions)
        """
        result = _analyze_dependencies(module_path)
        import json
        return json.dumps(result, indent=2)




def _get_project_structure(root_path: str = ".", max_depth: int = 3) -> Dict:
    """Internal implementation of get_project_structure."""
    root = Path(root_path).resolve()
    
    structure = {
        "root": str(root),
        "directories": {},
        "entry_points": [],
        "key_files": []
    }
    
    # Common entry point patterns
    entry_patterns = ["main.py", "app.py", "server.py", "__main__.py", "index.py"]
    
    # Exclusions
    exclude_dirs = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache", "build", "dist"}
    
    def scan_directory(path: Path, depth: int = 0):
        if depth > max_depth:
            return None
            
        dir_info = {
            "files": [],
            "subdirs": [],
            "total_files": 0
        }
        
        try:
            for item in path.iterdir():
                if item.name.startswith('.') and item.name not in ['.env']:
                    continue
                    
                if item.is_dir():
                    if item.name not in exclude_dirs:
                        subdir_info = scan_directory(item, depth + 1)
                        if subdir_info:
                            dir_info["subdirs"].append({
                                "name": item.name,
                                "path": str(item.relative_to(root)),
                                **subdir_info
                            })
                            dir_info["total_files"] += subdir_info.get("total_files", 0)
                else:
                    # Track files
                    dir_info["files"].append(item.name)
                    dir_info["total_files"] += 1
                    
                    # Identify entry points
                    if item.name in entry_patterns:
                        structure["entry_points"].append(str(item.relative_to(root)))
                    
                    # Track key files (large files, configs, etc.)
                    if item.suffix in ['.py', '.js', '.ts', '.go', '.rs']:
                        size = item.stat().st_size
                        if size > 5000:  # Files > 5KB are likely important
                            structure["key_files"].append({
                                "path": str(item.relative_to(root)),
                                "size": size,
                                "type": item.suffix
                            })
        except PermissionError:
            pass
            
        return dir_info
    
    structure["directories"] = scan_directory(root)
    
    # Sort key files by size
    structure["key_files"] = sorted(structure["key_files"], key=lambda x: x["size"], reverse=True)[:20]
    
    return structure


def _analyze_dependencies(module_path: str) -> Dict:
    """Internal implementation of analyze_dependencies."""
    path = Path(module_path)
    
    if not path.exists():
        return {"error": f"Module not found: {module_path}"}
    
    if path.suffix != '.py':
        return {"error": "Only Python modules supported"}
    
    try:
        content = path.read_text(encoding='utf-8')
        tree = ast.parse(content)
    except Exception as e:
        return {"error": f"Failed to parse module: {str(e)}"}
    
    dependencies = {
        "imports": [],
        "from_imports": [],
        "exports": {
            "classes": [],
            "functions": []
        }
    }
    
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                dependencies["imports"].append(alias.name)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                dependencies["from_imports"].append(f"{module}.{alias.name}")
        elif isinstance(node, ast.ClassDef):
            dependencies["exports"]["classes"].append(node.name)
        elif isinstance(node, ast.FunctionDef):
            # Only top-level functions
            if isinstance(node, ast.FunctionDef) and not any(
                isinstance(parent, ast.ClassDef) for parent in ast.walk(tree)
            ):
                dependencies["exports"]["functions"].append(node.name)
    
    return dependencies


if __name__ == "__main__":
    # Self-test / CLI mode
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "structure":
            result = _get_project_structure()
            print(json.dumps(result, indent=2))
        elif sys.argv[1] == "deps" and len(sys.argv) > 2:
            result = _analyze_dependencies(sys.argv[2])
            print(json.dumps(result, indent=2))
    else:
        print("Usage: project_map.py [structure|deps <file>]")

