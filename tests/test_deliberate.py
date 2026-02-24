import os
import json
import logging
from mcp_core.orchestrator_loop import Orchestrator

# Setup basic logging to see the deliberation steps
logging.basicConfig(level=logging.INFO)

def test_structured_deliberation():
    """Verify the new deliberate() tool flow."""
    print("🔍 Testing Structured Deliberation (Standard 3-Step Flow)...")
    
    # Initialize Orchestrator
    orch = Orchestrator(root_path="v:/Projects/Servers/swarm")
    
    # Define a complex problem
    problem = "Refactor the search engine to support multi-threaded indexing without race conditions."
    context = "Current search_engine.py uses a single-threaded loop. HippoRAG is already integrated."
    constraints = ["Must remain compatible with existing IndexConfig", "No external dependencies beyond stdlib"]
    
    print(f"Problem: {problem}")
    
    # Run Deliberation
    # We use steps=3 to trigger: Decompose -> Analyze -> Synthesize
    result = orch.run_deliberation(
        problem=problem,
        context=context,
        constraints=constraints,
        steps=3
    )
    
    # Verify Schema
    assert result.task_id is not None
    assert len(result.steps) >= 2 # Steps 1 and 2 are deterministic, Step 3 uses LLM
    
    print("\n--- Deliberation Trace ---")
    for step in result.steps:
        print(f"\n[Step {step.step}: {step.name}] (Worker: {step.worker})")
        print(f"Output: {step.output}")
        print(f"Duration: {step.duration_ms}ms")
    
    print("\n--- Final Answer ---")
    print(result.final_answer)
    print(f"\nConfidence: {result.confidence:.2f}")
    
    # High-level verification
    assert "refactor" in result.problem.lower()
    assert result.confidence > 0.0
    
    print("\n✅ Structured Deliberation tool verified.")

if __name__ == "__main__":
    test_structured_deliberation()
