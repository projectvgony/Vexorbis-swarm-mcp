
import sys
import subprocess
import shutil

# Configuration
CONTAINER_NAMES = ["swarm-mcp-server", "swarm-swarm-orchestrator-1"] # Candidates

def find_container():
    """Find the running swarm container."""
    if not shutil.which("docker"):
        print("❌ Docker not found in PATH")
        sys.exit(1)
        
    # Check running containers
    try:
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"], 
            capture_output=True, text=True, check=True
        )
        running = result.stdout.splitlines()
        for name in CONTAINER_NAMES:
            if name in running:
                return name
        # Fallback partial match
        for line in running:
            if "swarm" in line and "server" in line:
                return line
    except Exception as e:
        print(f"⚠️ Docker check failed: {e}")
    
    return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python dexec.py <command> [args...]")
        print("Example: python dexec.py python scripts/publish_changes.py")
        sys.exit(1)
        
    target_cmd = sys.argv[1:]
    
    container = find_container()
    if not container:
        print("❌ No Swarm container found. Is Docker running?")
        sys.exit(1)
        
    print(f"🐳 Bridging to Container: {container}")
    print(f"👉 Command: {' '.join(target_cmd)}")
    print("-" * 50)
    
    # Construct Docker Exec Command
    # We use env vars from the container, so no need to pass them usually.
    docker_cmd = ["docker", "exec", container] + target_cmd
    
    try:
        # Run and stream output
        subprocess.run(docker_cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Execution failed inside container (Exit Code: {e.returncode})")
        sys.exit(e.returncode)
    except KeyboardInterrupt:
        print("\n🛑 Interrupted")

if __name__ == "__main__":
    main()
