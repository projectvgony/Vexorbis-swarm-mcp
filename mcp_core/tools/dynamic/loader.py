"""
Dynamic Tool Loader

Automatically loads and registers tools from the dynamic/ directory.
"""

import logging
import importlib.util
import os
from pathlib import Path
from fastmcp import FastMCP

logger = logging.getLogger(__name__)

# Dev build: List of tools that should only load in debug mode
DEBUG_ONLY_TOOLS = []


def load_dynamic_tools(mcp: FastMCP, scopes: list[str] = None) -> int:
    """
    Load dynamic tools from specified scopes.
    
    Scopes:
    - 'general': User-facing project tools (mcp_core/tools/dynamic/)
    - 'internal': System maintenance tools (mcp_core/tools/internal/)
    
    Args:
        mcp: The FastMCP server instance
        scopes: List of scopes to load (default: ['general'])
        
    Returns:
        Number of tools loaded
    """
    if scopes is None:
        scopes = ['general']
    
    loaded = 0
    debug_mode = os.getenv("SWARM_DEBUG", "false").lower() == "true"
    
    # Map scopes to directories
    scope_dirs = {
        'general': Path(__file__).parent,
        'internal': Path(__file__).parent.parent / 'internal'
    }
    
    for scope in scopes:
        if scope not in scope_dirs:
            logger.warning(f"⚠️ Unknown scope: {scope} (skipping)")
            continue
        
        tools_dir = scope_dirs[scope]
        
        if not tools_dir.exists():
            logger.warning(f"⚠️ Scope directory not found: {tools_dir} (skipping)")
            continue
        
        logger.info(f"📂 Loading tools from scope: {scope}")
        
        for tool_file in tools_dir.glob("*.py"):
            # Skip loader and test files
            if tool_file.name in ("loader.py", "__init__.py"):
                continue
            
            # Skip debug-only tools in production mode (legacy check)
            if tool_file.name in DEBUG_ONLY_TOOLS and not debug_mode:
                logger.debug(f"⏭️ Skipping debug-only tool: {tool_file.name} (SWARM_DEBUG=false)")
                continue
                
            try:
                # Load module dynamically
                spec = importlib.util.spec_from_file_location(
                    tool_file.stem, 
                    tool_file
                )
                if spec is None or spec.loader is None:
                    continue
                    
                module = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(module)
                
                # Call register function if it exists
                if hasattr(module, "register"):
                    module.register(mcp)
                    logger.info(f"✅ Loaded [{scope}] tool (via register): {tool_file.name}")
                    loaded += 1
                else:
                    # Inspect module for top-level functions that look like tools
                    # Heuristic: Functions that are not private and not imported
                    import inspect
                    for name, func in inspect.getmembers(module, inspect.isfunction):
                        if name.startswith("_") or func.__module__ != module.__name__:
                            continue
                        
                        try:
                            mcp.tool()(func)
                            logger.info(f"    - Registered [{scope}] function: {name}")
                            loaded += 1
                        except ValueError as e:
                            if "already exists" in str(e):
                                logger.debug(f"ℹ️ Tool {name} already registered (skipping)")
                            else:
                                logger.warning(f"Could not register {name}: {e}")
                        except Exception as e:
                            logger.warning(f"Could not register {name}: {e}")
                    
                    logger.info(f"✅ Loaded [{scope}] tool module: {tool_file.name}")

            except Exception as e:
                logger.error(f"❌ Failed to load {tool_file.name} from [{scope}]: {e}")
                
                # [v3.4] Strict Tool Loading (Deterministic)
                # If enabled, fail the server startup on ANY tool load error
                if os.getenv("SWARM_STRICT_TOOLS", "false").lower() == "true":
                    logger.critical(f"🛑 Strict Mode: Aborting due to tool load failure: {tool_file.name}")
                    raise RuntimeError(f"Tool load failed: {tool_file.name}") from e
    
    logger.info(f"📦 Loaded {loaded} tools across scopes: {scopes}")
    return loaded
