
import os
import sys
import json
from pathlib import Path

# Add project root to path so we can import mcp_core
sys.path.append(str(Path(__file__).parent.parent))

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
    print(f"🔑 API Key loaded: {'✅ Yes' if os.getenv('GEMINI_API_KEY') else '❌ No'}")
except ImportError:
    print("⚠️ python-dotenv not installed. Install with: pip install python-dotenv")

from mcp_core.llm import generate_response
from mcp_core.worker_prompts import prompt_tool_planner

def simulate():
    print("🚀 Starting Swarm Meta-Orchestrator Simulation...")
    
    # 1. Define Client Tools (as if sent from an IDE)
    ide_tools = [
        {
            "name": "list_dir",
            "description": "List files in a directory",
            "parameters": {"path": "string"}
        },
        {
            "name": "view_file",
            "description": "Read file content",
            "parameters": {"path": "string", "start": "int", "end": "int"}
        },
        {
            "name": "search_symbols",
            "description": "Search for function/class definitions",
            "parameters": {"query": "string"}
        },
        {
            "name": "edit_file",
            "description": "Apply a diff to a file",
            "parameters": {"path": "string", "diff": "string"}
        },
        {
            "name": "run_command",
            "description": "Run a shell command",
            "parameters": {"command": "string"}
        }
    ]
    
    # 2. Define Goal
    goal = "Implement a new log rotation utility in the telemetry module and verify it with a dummy test."
    
    # 3. Internal Swarm Context (e.g. knowing where telemetry is)
    swarm_context = {
        "project_type": "python/mcp",
        "telemetry_root": "mcp_core/telemetry",
        "existing_utils": ["collector.py", "telemetry_analytics.py"]
    }
    
    # 4. Generate Prompt
    prompt = prompt_tool_planner(goal, ide_tools, swarm_context)
    
    print("\n--- GENERATED PROMPT ---")
    print(prompt)
    
    print("\n🧠 Generating Plan from Swarm (LLM)...")
    
    # Use a cheap model for simulation if possible, or default
    response = generate_response(prompt, model_alias="gemini-3-flash-preview")
    
    if response.status == "SUCCESS":
        # Extra reasoning might be in reasoning_trace
        print("\n✅ Plan Generated Successfully!")
        
        # Swarm's LLM output is expected to be JSON with a 'plan' key
        # generate_response usually returns an AgentResponse object
        # The content of the plan might be in reasoning_trace or if it processed it into blackboard_update
        # Based on llm.py, it parses text into dict and returns AgentResponse
        
        # Let's extract the actual raw text from the trace if needed, or if it hit tool_calls
        # For simplicity in this simulation, we'll assume the LLM returned the JSON plan.
        
        print("\n--- SWARM PROPOSAL ---")
        try:
            # Re-parse if it's nested or just print what we got
            plan_data = response.model_dump()
            print(json.dumps(plan_data, indent=2))
        except Exception as e:
            print(f"Error displaying plan: {e}")
            print(f"Raw Reasoning: {response.reasoning_trace}")
    else:
        print(f"\n❌ Plan Generation Failed: {response.reasoning_trace}")

if __name__ == "__main__":
    simulate()
