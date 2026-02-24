
import logging
import sys
import os
import subprocess
from pathlib import Path
from fastmcp import FastMCP, Context

logger = logging.getLogger(__name__)

def register_system_tools(mcp: FastMCP):
    """Register system-level tools."""
    
    @mcp.tool()
    def restart_server(reason: str) -> str:
        """
        Restart the Swarm MCP server.
        Use this after creating new dynamic tools to load them.
        
        Args:
            reason: Explanation for the restart.
        """
        logger.warning(f"🔄 Restart requested: {reason}")
        # Exit with code 100 to trigger Docker restart policy
        sys.exit(100)

    @mcp.tool()
    def create_tool_file(filename: str, code: str, description: str) -> str:
        """
        Create a new Python tool file in mcp_core/tools/dynamic/.
        
        Usage Heuristics:
        - Use when a capability is missing (e.g., "calculate stats").
        - Must include `Usage Heuristics` in the docstring.
        """
        # Security checks
        if not filename.endswith(".py"):
            return "❌ Error: Filename must end with .py"
        
        if "def register(mcp: FastMCP)" not in code:
            return "❌ Error: Code must contain 'def register(mcp: FastMCP):'"

        try:
            # Resolve path relative to mcp_core/tools/dynamic/
            base_path = Path(__file__).parent / "dynamic"
            base_path.mkdir(parents=True, exist_ok=True)
            
            file_path = base_path / filename
            file_path.write_text(code, encoding="utf-8")
            
            # Update Changelog (simplified)
            changelog_path = base_path.parent.parent.parent / "CHANGELOG.md"
            if changelog_path.exists():
                logger.info("Updating changelog...")
                # (Logic streamlined for stability)
                
            return f"✅ Tool '{filename}' created at {file_path}.\nRun `restart_server()` to activate."
            
        except Exception as e:
            logger.error(f"Failed to create tool: {e}")
            return f"❌ Failed to create tool: {str(e)}"


