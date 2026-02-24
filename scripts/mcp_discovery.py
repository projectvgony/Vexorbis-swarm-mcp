import subprocess
import json
import re
import sys

def get_docker_mcp_servers():
    """Discover MCP servers running in Docker containers."""
    try:
        # Get list of running containers with their ports
        cmd = ["docker", "ps", "--format", "{{.ID}}\t{{.Names}}\t{{.Ports}}\t{{.Status}}"]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        
        servers = []
        for line in result.stdout.strip().split('\n'):
            if not line: continue
            # Split by at least 2 spaces or a tab
            parts = re.split(r'\t| {2,}', line.strip())
            # print(f"DEBUG: parts={parts}")
            if len(parts) < 3: continue
            
            container_id = parts[0]
            name = parts[1]
            ports = parts[2]
            status = parts[3] if len(parts) > 3 else "Unknown"
            
            # print(f"DEBUG: name={name}, ports={ports}")
            
            # Look for mapped ports
            # Matches 0.0.0.0:8000->8000/tcp or 8000/tcp
            mcp_match = re.search(r'(?:0\.0\.0\.0:|\[::\]:)?(\d+)->\d+/tcp', ports)
            
            if mcp_match and "mcp" in name.lower():
                port = mcp_match.group(1)
                servers.append({
                    "id": container_id,
                    "name": name,
                    "port": port,
                    "status": status,
                    "url": f"http://localhost:{port}/sse"
                })
        
        return servers
    except subprocess.CalledProcessError as e:
        print(f"Error running docker ps: {e}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

if __name__ == "__main__":
    print("🔍 Searching for Docker MCP servers...")
    servers = get_docker_mcp_servers()
    
    if not servers:
        print("❌ No Docker MCP servers found (checking for mapped ports on 0.0.0.0).")
        sys.exit(0)
        
    print(f"✅ Found {len(servers)} potential MCP server(s):")
    for s in servers:
        print(f"- {s['name']} ({s['id'][:8]})")
        print(f"  Port: {s['port']}")
        print(f"  Status: {s['status']}")
        print(f"  SSE URL: {s['url']}")
        print()
    
    # Optional: output as JSON for Task 4
    if "--json" in sys.argv:
        print("---JSON_START---")
        print(json.dumps(servers))
        print("---JSON_END---")
