"""
GitHubMCPClient: Async wrapper for GitHub MCP server operations.
"""

import logging
import os
import json
from typing import List, Dict, Any, Optional

class GitHubMCPClient:
    """
    Wrapper for GitHub MCP server operations.
    
    This client manages the connection to the GitHub MCP server and provides
    high-level methods for common Git/GitHub operations used by GitWorker roles.
    """
    
    def __init__(self, server_params=None):
        self.server_params = server_params
        self.session = None
        self.token = os.getenv("GITHUB_TOKEN")
        if not self.token:
            logging.warning("GitHubMCPClient: GITHUB_TOKEN not set!")

    async def connect(self):
        """Establish Stdio connection to embedded GitHub MCP server."""
        try:
            from mcp.client.stdio import stdio_client, StdioServerParameters
            from mcp.client.session import ClientSession
            from contextlib import AsyncExitStack
            
            self._exit_stack = AsyncExitStack()
            
            # Command to run the embedded server
            server_params = StdioServerParameters(
                command="npx",
                args=["-y", "@modelcontextprotocol/server-github"],
                env={**os.environ, "GITHUB_TOKEN": self.token}
            )
            
            # Enter the stdio_client context
            self._read_stream, self._write_stream = await self._exit_stack.enter_async_context(stdio_client(server_params))
            
            # Create and initialize the session
            self.session = await self._exit_stack.enter_async_context(ClientSession(self._read_stream, self._write_stream))
            await self.session.initialize()
            
            logging.info("✅ Connected to embedded GitHub MCP server (Stdio)")
            return True
            
        except Exception as e:
            logging.error(f"❌ Failed to connect to GitHub MCP: {e}")
            self.session = None
            if hasattr(self, "_exit_stack"):
                await self._exit_stack.aclose()
            return False

    async def disconnect(self):
        """Close the connection."""
        if hasattr(self, "_exit_stack"):
            await self._exit_stack.aclose()
            self.session = None
            logging.info("Disconnected from GitHub MCP server")

    async def _call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Helper to call MCP tools."""
        if not self.session:
            if not await self.connect():
                raise RuntimeError("GitHub MCP client not connected")
        
        return await self.session.call_tool(tool_name, arguments)

    async def create_issue(self, owner: str, repo: str, title: str, body: str, labels: List[str] = None) -> Dict[str, Any]:
        """Create a GitHub issue."""
        result = await self._call_tool("create_issue", {
            "owner": owner, "repo": repo, "title": title, "body": body, "labels": labels or []
        })
        return result.content[0].text if result.content else {}

    async def list_issues(self, owner: str, repo: str, state: str = "open") -> List[Dict[str, Any]]:
        """List GitHub issues."""
        # Using list_issues tool directly as verified
        result = await self._call_tool("list_issues", {
            "owner": owner, "repo": repo, "state": state
        })
        try:
            return json.loads(result.content[0].text)
        except (AttributeError, IndexError, json.JSONDecodeError, TypeError):
            # The MCP server might return structured data or a string
            if hasattr(result, "content") and result.content:
                text = result.content[0].text
                try:
                    return json.loads(text)
                except:
                    return text
            return []

    async def search_issues(self, query: str) -> List[Dict[str, Any]]:
        """Search GitHub issues using query string."""
        # Verified parameter name is 'q'
        result = await self._call_tool("search_issues", {"q": query})
        try:
            return json.loads(result.content[0].text)
        except:
            return []

    async def create_pull_request(self, owner: str, repo: str, title: str, body: str, head: str, base: str) -> Dict[str, Any]:
        """Create a GitHub pull request."""
        # Note: standard tool might range from create_pull_request to lower level API
        return await self._call_tool("create_pull_request", {
            "owner": owner, "repo": repo, "title": title, "body": body, "head": head, "base": base
        })

    async def merge_pull_request(self, owner: str, repo: str, pull_number: int, method: str = "squash") -> Dict[str, Any]:
        """Merge a GitHub pull request."""
        result = await self._call_tool("merge_pull_request", {
            "owner": owner, "repo": repo, "pull_number": pull_number, "merge_method": method
        })
        return result.content[0].text if result.content else {}

    async def get_pull_request(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Get PR details."""
        return await self._call_tool("get_pull_request", {
            "owner": owner, "repo": repo, "pull_number": pull_number
        })

    # Note: create/archive repository might not be supported by standard toolset yet
    # We keep them as stubs or try generic resource access if available
    async def create_repository(self, name: str, description: str = "", private: bool = True) -> Dict[str, Any]:
        logging.warning("create_repository not fully implemented in stdio client yet")
        return {"name": name, "status": "simulated_creation"}

    async def archive_repository(self, owner: str, repo: str) -> Dict[str, Any]:
        logging.warning("archive_repository not fully implemented in stdio client yet")
        return {"success": True, "status": "simulated_archived"}
