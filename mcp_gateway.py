from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
import httpx
import asyncio
import os
import sys
import logging
from rich.console import Console

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("MCPGateway")
console = Console()

mcp = FastMCP("Docker MCP Gateway")

# Internal cache of discovered servers
_discovered_servers: List[Dict[str, Any]] = []

async def refresh_discovery():
    """Refresh the list of running Docker MCP servers."""
    global _discovered_servers
    try:
        from scripts.mcp_discovery import get_docker_mcp_servers
        _discovered_servers = get_docker_mcp_servers()
        logger.info(f"Gateway discovered {len(_discovered_servers)} servers.")
    except Exception as e:
        logger.error(f"Discovery failed: {e}")

@mcp.tool()
async def list_docker_servers() -> str:
    """List all Docker MCP servers currently accessible via the gateway."""
    await refresh_discovery()
    if not _discovered_servers:
        return "No Docker MCP servers discovered."
    
    result = ["📡 Discovered MCP Servers:"]
    for s in _discovered_servers:
        result.append(f"- {s['name']} (Port: {s['port']}, Status: {s['status']})")
    
    return "\n".join(result)

@mcp.tool()
async def route_task(server_name: str, task_instruction: str) -> str:
    """
    Route a task to a specific Docker MCP server.
    Example: route_task("swarm-mcp-server", "Refactor auth.py")
    """
    await refresh_discovery()
    target = next((s for s in _discovered_servers if server_name in s['name']), None)
    
    if not target:
        return f"❌ Server '{server_name}' not found."
    
    # In a real gateway, we would proxy the MCP request.
    # Here we simulate routing by calling the target server's process_task tool.
    # This requires an MCP client. For simplicity, we'll suggest using the config.
    
    return (f"🔗 Gateway routing instruction to {server_name} at {target['url']}...\n"
            f"Note: Use the generated MCP config to connect directly for full tool access.")

@mcp.tool()
async def mcp_gateway_health_check() -> str:
    """
    Monitor the health and latency of connections to Docker MCP servers.
    Checks reachability and reports metrics.
    """
    await refresh_discovery()
    if not _discovered_servers:
        return "🔴 Gateway Healthy | Backend: 0 servers discovered."
    
    results = [f"🟢 Gateway Healthy | Backend: {len(_discovered_servers)} servers"]
    
    async with httpx.AsyncClient(timeout=2.0) as client:
        for s in _discovered_servers:
            try:
                # Attempt to ping the host (basic check)
                start_time = asyncio.get_event_loop().time()
                # Just a root check if it's up
                resp = await client.get(f"http://localhost:{s['port']}/")
                latency = (asyncio.get_event_loop().time() - start_time) * 1000
                
                status = "✅" if resp.status_code < 500 else "⚠️"
                results.append(f"  - {s['name']}: {status} ({latency:.1f}ms)")
            except Exception as e:
                results.append(f"  - {s['name']}: ❌ (Offline) - {str(e)}")
                
    return "\n".join(results)

if __name__ == "__main__":
    import uvicorn
    
    # Auto-detect mode
    if "--sse" in sys.argv:
        port = int(os.environ.get("GATEWAY_PORT", "8765"))
        logger.info(f"🚀 Starting MCP Gateway on port {port} (SSE)...")
        mcp.run(transport="sse", host="0.0.0.0", port=port)
    else:
        logger.info("🚀 Starting MCP Gateway (Stdio)...")
        mcp.run()
