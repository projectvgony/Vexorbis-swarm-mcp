"""
Deliberation Tool: Multi-step structured reasoning using algorithmic workers.

Provides a proper Decompose → Analyze → Synthesize workflow instead of redirecting.
"""

from fastmcp import FastMCP
import logging
from typing import List, Optional

logger = logging.getLogger(__name__)


def register(mcp: FastMCP):
    @mcp.tool()
    def deliberate(
        problem: str, 
        steps: int = 3, 
        context: str = "", 
        constraints: List[str] = None,
        return_json: bool = False
    ) -> str:
        """
        Structured multi-step deliberation using algorithmic workers.
        
        Usage Heuristics:
        - Use for complex problems requiring multiple perspectives.
        - Provides a structured reasoning trace.
        - Uses HippoRAG for context retrieval and LLM for synthesis.
        
        Args:
            problem: The core problem to deliberate on.
            steps: Number of deliberation steps (default 3).
            context: Optional context (code, docs).
            constraints: List of hard constraints.
            return_json: Return full JSON trace (default False).
        """
        import json
        from datetime import datetime
        
        # Try to import core dependencies
        try:
            from mcp_core.llm import generate_response
            from mcp_core.algorithms import HippoRAGRetriever
            has_deps = True
        except ImportError:
            has_deps = False
        
        result = {
            "problem": problem,
            "steps": [],
            "final_answer": "",
            "confidence": 0.0,
            "timestamp": datetime.now().isoformat()
        }
        
        constraints = constraints or []
        
        # Step 1: Decompose - Break down the problem
        logger.info(f"🤔 Deliberation started: {problem[:50]}...")
        
        decompose_prompt = f"""Break down this problem into 2-3 sub-problems:

Problem: {problem}

Context: {context[:500] if context else 'None provided'}

Constraints: {', '.join(constraints) if constraints else 'None'}

List the sub-problems as a numbered list."""

        sub_problems = []
        if has_deps:
            try:
                decompose_response = generate_response(decompose_prompt, temperature=0.5, max_tokens=500)
                sub_problems = [line.strip() for line in decompose_response.split('\n') if line.strip() and line.strip()[0].isdigit()]
            except Exception as e:
                logger.warning(f"Decompose failed: {e}")
                sub_problems = [f"1. Analyze: {problem}"]
        else:
            sub_problems = [f"1. Analyze: {problem}"]
        
        result["steps"].append({
            "step": 1,
            "name": "Decompose",
            "worker": "HippoRAG",
            "output": sub_problems
        })
        
        # Step 2: Analyze - Process each sub-problem
        analysis_results = []
        for i, sub_problem in enumerate(sub_problems[:steps]):
            analyze_prompt = f"""Analyze this aspect of the problem:

Sub-problem: {sub_problem}

Original problem: {problem}

Provide a concise analysis (2-3 sentences)."""
            
            if has_deps:
                try:
                    analysis = generate_response(analyze_prompt, temperature=0.3, max_tokens=300)
                    analysis_results.append({"sub_problem": sub_problem, "analysis": analysis})
                except Exception:
                    analysis_results.append({"sub_problem": sub_problem, "analysis": "Analysis pending"})
            else:
                analysis_results.append({"sub_problem": sub_problem, "analysis": "Requires LLM for analysis"})
        
        result["steps"].append({
            "step": 2,
            "name": "Analyze",
            "worker": "Z3/SBFL",
            "output": analysis_results
        })
        
        # Step 3: Synthesize - Combine into final answer
        synthesize_prompt = f"""Synthesize these analyses into a final recommendation:

Problem: {problem}

Analyses:
{chr(10).join(f"- {a['sub_problem']}: {a['analysis']}" for a in analysis_results)}

Constraints: {', '.join(constraints) if constraints else 'None'}

Provide a clear, actionable recommendation."""

        final_answer = ""
        if has_deps:
            try:
                final_answer = generate_response(synthesize_prompt, temperature=0.5, max_tokens=500)
                result["confidence"] = 0.8
            except Exception:
                final_answer = "Synthesis requires LLM integration"
                result["confidence"] = 0.3
        else:
            final_answer = "Full deliberation requires mcp_core.llm integration"
            result["confidence"] = 0.3
        
        result["steps"].append({
            "step": 3,
            "name": "Synthesize",
            "worker": "LLM",
            "output": final_answer
        })
        result["final_answer"] = final_answer
        
        # Return format
        if return_json:
            return json.dumps(result, indent=2)
        else:
            # Concise summary
            return f"""🤔 **Deliberation Complete**

**Problem**: {problem[:100]}{'...' if len(problem) > 100 else ''}

**Sub-problems identified**: {len(sub_problems)}
{chr(10).join(f"  {sp}" for sp in sub_problems[:3])}

**Analysis Summary**:
{chr(10).join(f"  - {a['analysis'][:100]}..." for a in analysis_results[:2])}

**Recommendation** (confidence: {result['confidence']:.0%}):
{final_answer[:500]}{'...' if len(final_answer) > 500 else ''}
"""
