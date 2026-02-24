
import os
import sys
import logging
import logging
from pathlib import Path

# Add project root to path (robust)
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.append(project_root)

from mcp_core.orchestrator_loop import Orchestrator
from mcp_core.swarm_schemas import Task

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

def load_local_env():
    from pathlib import Path
    env_file = Path(".env")
    if env_file.exists():
        print(f"📂 Loading environment from {env_file}...")
        try:
            content = env_file.read_text(encoding='utf-8')
            for line in content.splitlines():
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                k, v = line.split("=", 1)
                os.environ[k.strip()] = v.strip().strip("'").strip('"')
        except Exception as e:
            print(f"⚠️ Failed to load .env: {e}")

def publish_changes():
    load_local_env()
    print("🚀 Initiating Autonomous Publish Sequence...", flush=True)
    
    # Initiate orchestrator
    try:
        orch = Orchestrator()
        
        # Check status
        if not orch.git.has_changes():
            print("✅ No uncommitted changes found. Everything is clean!", flush=True)
            return

        print(f"📝 Changes Detected. Dispatching {orch.state.worker_models.get('git-writer')}...", flush=True)

        # Create Publish Task
        task = Task(
            task_id="publish_trigger",
            description="Fix critical verification regressions: Remove Scipy dependency from PageRank and fix Orchestrator graph building/OCC removal",
            status="PENDING",
            git_branch_name="fix/verification-regressions",
            git_commit_ready=True,
            git_create_pr=False, 
            output_files=[]
        )
        
        # Manually inject to state
        orch.state.tasks[task.task_id] = task
        
        # DIRECTLY CALL Git Workflow to verify logic
        print("🤖 Executing _handle_git_workflow direct...", flush=True)
        handled = orch._handle_git_workflow(task)
        
        # Log Result
        print(f"\n📋 Workflow Handled: {handled}")
        print("\n📋 Task Feedback Log:")
        for log in task.feedback_log:
            print(f" - {log}")
            
    except Exception as e:
        print(f"\n❌ Publish Failed: {e}", flush=True)
        import traceback
        traceback.print_exc()

    except Exception as e:
        print(f"\n❌ Publish Failed: {e}")

if __name__ == "__main__":
    publish_changes()
