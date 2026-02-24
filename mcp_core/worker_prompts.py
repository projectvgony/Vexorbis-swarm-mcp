
from typing import Dict, Any
from pathlib import Path

# Base path for skills
_SKILLS_DIR = Path(__file__).parent.parent / "docs" / "ai" / "skills"

def _load_skill(filename: str) -> str:
    """Helper to load a skill markdown file."""
    try:
        return (_SKILLS_DIR / filename).read_text(encoding="utf-8")
    except Exception as e:
        return f"Error loading skill {filename}: {e}"

def prompt_architect(task: Any, memory: Dict[str, Any], contributing_model: str = None) -> str:
    """Generates the prompt for the Architect worker using the planning skill."""
    skill_content = _load_skill("architect-planning.md")
    
    return f"""
{skill_content}

<mission>
Analyze the following Request and produce a formal Implementation Plan.
TASK: {task.description}
CONTEXT: {memory}
MODEL_ID: {contributing_model or 'Unknown'}
</mission>
"""

def prompt_engineer(task: Any, memory: Dict[str, Any], context: Dict[str, Any], contributing_model: str = None) -> str:
    """Generates the prompt for the Engineer worker using the engineering skill."""
    skill_content = _load_skill("software-engineering.md")
    
    # Inject Git workflow instructions if Git is available
    git_section = ""
    if context.get("git_available"):
        git_workflow = context.get("git_workflow_instructions", "")
        if git_workflow:
            git_section = f"\n{git_workflow}\n"
    
    return f"""
{skill_content}

{git_section}

<mission>
TASK: {task.description}
CONTEXT: {context}
MEMORY: {memory}
MODEL_ID: {contributing_model or 'Unknown'}
</mission>
"""

def prompt_auditor(task: Any, context: Dict[str, Any], contributing_model: str = None) -> str:
    """Generates the prompt for the Auditor worker using the security audit skill."""
    skill_content = _load_skill("security-audit.md")
    
    return f"""
{skill_content}

<mission>
Review the artifacts produced in Task: {task.description}
MODEL_ID: {contributing_model or 'Unknown'}
</mission>
"""

def prompt_debugger(task: Any, memory: Dict[str, Any], context: Dict[str, Any], contributing_model: str = None) -> str:
    """Generates the prompt for the Debugger worker using the debugging skill."""
    skill_content = _load_skill("debugger.md")
    
    # Include test output if available
    test_output = context.get("test_output", "No test output provided")
    
    return f"""
{skill_content}

<mission>
Diagnose and fix failing test(s):
TASK: {task.description}
TEST OUTPUT: {test_output}
CONTEXT: {context}
MEMORY: {memory}
MODEL_ID: {contributing_model or 'Unknown'}
</mission>
"""

def prompt_researcher(task: Any, memory: Dict[str, Any], contributing_model: str = None) -> str:
    """Generates the prompt for the Researcher worker using the research skill."""
    skill_content = _load_skill("researcher.md")
    
    return f"""
{skill_content}

<mission>
Research and document findings:
QUESTION: {task.description}
CONTEXT: {memory}
MODEL_ID: {contributing_model or 'Unknown'}
</mission>
"""

def prompt_toolsmith(task: Any, context: Dict[str, Any]) -> str:
    """Generates the prompt for the Toolsmith worker using the tool creation skill."""
    skill_content = _load_skill("tool-creation.md")
    
    return f"""
{skill_content}

<mission>
Analyze the request and build a new MCP tool.
REQUEST: {task.description}
CONTEXT: {context}
</mission>
"""

# ============================================================================
# Git Worker Prompts (v3.2)
# ============================================================================

def prompt_git_commit(task: Any, context: Dict[str, Any], contributing_model: str = None) -> str:
    """Generates the prompt for the Commit Worker using the Conventional Commits skill."""
    from mcp_core.git_helpers import format_commit_message, format_commit_body
    
    skill_content = _load_skill("git-conventional-commits.md")
    files = context.get("output_files", [])
    
    # Generate conventional commit message
    commit_msg = format_commit_message(task, include_emoji=True, contributing_model=contributing_model)
    body = format_commit_body(task.feedback_log)
    full_commit = f"{commit_msg}\n\n{body}" if body else commit_msg
    
    return f"""
{skill_content}

<mission>
Stage and commit the following files:
{', '.join(files) if files else 'All modified files'}

Task: {task.description}
</mission>

<generated_template>
Use this commit message if appropriate:
{full_commit}
</generated_template>
"""

def prompt_git_pr(task: Any, context: Dict[str, Any], contributing_model: str = None) -> str:
    """Generates the prompt for the PR Worker using the PR skill."""
    skill_content = _load_skill("git-pull-request.md")
    
    branch = context.get("git_branch_name", "feature/unknown")
    base = context.get("git_base_branch", "main")
    pr_title = context.get("git_pr_title", task.description[:60])
    pr_body = context.get("git_pr_body", f"Automated PR from Swarm task {task.task_id[:8]}")
    
    pr_body_template = f'''## Swarm Task: {task.task_id[:8]}

{pr_body}

### Files Modified
{', '.join(context.get('output_files', []))}

---
*Automated PR from Swarm Orchestrator ({contributing_model or 'Unknown Model'})*'''
    
    return f"""
{skill_content}

<mission>
Create a pull request:
- Branch: {branch}
- Target: {base}
- Title: {pr_title}
</mission>

<tools>
Use GitHub MCP server:
create_pull_request(
    owner="{context.get('repo_owner', 'DETECT_FROM_REMOTE')}",
    repo="{context.get('repo_name', 'DETECT_FROM_REMOTE')}",
    title="{pr_title}",
    head="{branch}",
    base="{base}",
    body="{pr_body_template}"
)
</tools>
"""

def prompt_git_branch(task: Any, context: Dict[str, Any]) -> str:
    """Generates the prompt for the Branch Worker using the Branch skill."""
    skill_content = _load_skill("git-branch-workflow.md")
    
    branch_name = context.get("git_branch_name", f"feature/task-{task.task_id[:8]}")
    base_branch = context.get("git_base_branch", "main")
    
    return f"""
{skill_content}

<mission>
Create and switch to branch: {branch_name}
Base: {base_branch}
</mission>
"""


# ============================================================================
# Deliberation Prompts (v3.3)
# ============================================================================

def prompt_synthesizer(sub_problems: list, worker_outputs: dict, constraints: list[str]) -> str:
    """Generates the prompt for synthesizing multi-worker outputs into a coherent solution."""
    
    constraints_text = "\\n".join(f"- {c}" for c in constraints) if constraints else "None"
    
    outputs_text = ""
    for i, (worker, output) in enumerate(worker_outputs.items(), 1):
        outputs_text += f"\\n### Worker {i}: {worker}\\n{output}\\n"
    
    return f"""
You are the Synthesizer in a structured deliberation process.

Your role is to combine the outputs from multiple algorithmic workers into a coherent, actionable solution.

## Sub-Problems Analyzed:
{chr(10).join(f'{i+1}. {sp}' for i, sp in enumerate(sub_problems))}

## Worker Outputs:
{outputs_text}

## Constraints:
{constraints_text}

## Your Task:
Synthesize these worker outputs into a single, coherent recommendation. Include:
1. **Solution Summary**: What should be done?
2. **Supporting Evidence**: Which worker outputs support this?
3. **Confidence Score** (0.0-1.0): How confident are you in this synthesis?
4. **Next Actions**: Concrete steps to implement this.

Provide your synthesis in a clear, structured format.
"""

def prompt_git_worker(task: Any, context: Dict[str, Any], contributing_model: str = None) -> str:
    """Generates the prompt for the Autonomous GitWorker Agent."""
    skill_content = _load_skill("git-worker-agent.md")
    
    project_profile = context.get("project_profile", "{}")
    repo_context = context.get("repo_context", "{}")
    
    return f"""
{skill_content}

<input_contract>
Target Task:
{task.json() if hasattr(task, 'json') else str(task)}

Project Profile Snapshot:
{project_profile}

Repo Context:
{repo_context}

Model ID: {contributing_model or 'Unknown'}
</input_contract>
"""

def prompt_tool_planner(goal: str, tools: list, context: dict = None) -> str:
    """Generates the prompt for the Tool Planner (Meta-Orchestrator)."""
    import json
    tools_json = json.dumps(tools, indent=2)
    context_text = json.dumps(context, indent=2) if context else "None"
    
    return f"""
You are the Swarm Meta-Orchestrator. Your mission is to plan the execution of a complex task using ONLY the tools provided by the client (IDE).

### Available Tools (from Client):
{tools_json}

### Operational Context:
{context_text}

### User Goal:
{goal}

### Instructions:
1. Analyze the User Goal and break it down into logical steps.
2. For each step, select the most appropriate tool from the "Available Tools" list.
3. Provide a sequence of tool calls that will achieve the goal.
4. Each entry in the sequence MUST include:
   - `tool_name`: Exact name from the provided list.
   - `arguments`: Dictionary of arguments for the tool.
   - `reasoning`: Why this tool is chosen for this step.

### Response Format:
Respond ONLY with a JSON object containing a `plan` key, which is a list of tool call objects.
Example:
{{
  "plan": [
    {{
      "tool_name": "list_dir",
      "arguments": {{ "path": "." }},
      "reasoning": "Identify project structure"
    }}
  ]
}}
"""
