import httpx
import subprocess
import time
from typing import Optional

def debug_mcp_transport(target_url: Optional[str] = None, container_name: Optional[str] = None) -> str:
    """
    Debug and profile MCP transport connectivity for troubleshooting 'the gate'.
    
    **Usage Heuristics**:
    - Use when SSE (HTTP) connections are timing out or returning 5xx.
    - Use to verify 'docker exec' reachability for stdio-based container access.
    - Useful for diagnosing Windows Firewall or port mapping issues.
    """
    results = []
    
    # 1. Test HTTP/SSE Connectivity
    if target_url:
        start = time.time()
        try:
            # We use a standard sync client for simple tool check
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(target_url)
                latency = (time.time() - start) * 1000
                results.append(f"🌐 SSE [{target_url}]: Status {resp.status_code} ({latency:.1f}ms)")
        except Exception as e:
            results.append(f"🌐 SSE [{target_url}]: ❌ FAILED - {str(e)}")

    # 2. Test Docker Exec (Stdio)
    if container_name:
        start = time.time()
        try:
            # Simple health check via docker exec
            cmd = ["docker", "exec", container_name, "python", "--version"]
            proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5.0)
            latency = (time.time() - start) * 1000
            if proc.returncode == 0:
                results.append(f"🐳 Docker [{container_name}]: ✅ Stdio Reachable ({latency:.1f}ms) - {proc.stdout.strip()}")
            else:
                results.append(f"🐳 Docker [{container_name}]: ❌ EXEC FAILED - {proc.stderr.strip()}")
        except Exception as e:
            results.append(f"🐳 Docker [{container_name}]: ❌ SYSTEM ERROR - {str(e)}")

    if not results:
        return "⚠️ Error: Please provide either target_url or container_name to debug."
        
    return "\n".join(results)
