"""
Meta-Orchestrator Test - Direct LLM Call (Bypasses AgentResponse schema)
"""
import os
import json

def test_meta_orchestrator():
    from mcp_core.worker_prompts import prompt_tool_planner
    
    # Define IDE tools
    tools = [
        {"name": "list_dir", "description": "List directory contents", "parameters": {"path": "string"}},
        {"name": "view_file", "description": "Read file content", "parameters": {"path": "string", "start": "int", "end": "int"}},
        {"name": "search_symbols", "description": "Search for symbols", "parameters": {"query": "string"}},
        {"name": "edit_file", "description": "Apply edits to file", "parameters": {"path": "string", "diff": "string"}},
        {"name": "run_command", "description": "Execute shell command", "parameters": {"command": "string"}}
    ]
    
    # Goal
    goal = "Implement log rotation in the telemetry module and add a test"
    context = {"project_type": "python/mcp", "telemetry_root": "mcp_core/telemetry"}
    
    # Generate prompt
    prompt = prompt_tool_planner(goal, tools, context)
    
    print("="*60)
    print("META-ORCHESTRATOR TEST")
    print("="*60)
    print(f"\n📋 Goal: {goal}\n")
    
    # Call Gemini API directly (bypass generate_response schema validation)
    try:
        import google.generativeai as genai
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        model = genai.GenerativeModel("gemini-2.0-flash-exp")
        
        response = model.generate_content(prompt)
        raw_text = response.text
        
        print("🧠 RAW LLM RESPONSE:")
        print("-"*60)
        print(raw_text)
        print("-"*60)
        
        # Parse as JSON
        plan = json.loads(raw_text)
        
        print("\n✅ PARSED PLAN:")
        print(json.dumps(plan, indent=2))
        
        print(f"\n📊 ANALYSIS:")
        print(f"  • Steps: {len(plan.get('plan', []))}")
        for i, step in enumerate(plan.get('plan', []), 1):
            print(f"\n  {i}. {step.get('tool_name', 'unknown')}")
            args = step.get('arguments', {})
            print(f"     Args: {json.dumps(args, indent=6)}")
            reasoning = step.get('reasoning', 'N/A')
            print(f"     Why: {reasoning[:80]}...")
        
        print("\n" + "="*60)
        print("✅ META-ORCHESTRATOR TEST PASSED!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_meta_orchestrator()
