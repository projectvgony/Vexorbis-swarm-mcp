
import re
from typing import List, Dict, Optional, Tuple
from mcp_core.swarm_schemas import Task, GateStatus

class MarkdownBridge:
    """
    Bi-directional bridge between Markdown Project Plans and Swarm Tasks.
    
    Format:
    - [ ] Task Description @role
      - Context: file1.py
      - Flags: git_commit_ready=True
    """
    
    SECTION_TODO = "## Todo"
    SECTION_IN_PROGRESS = "## In Progress"
    SECTION_COMPLETED = "## Completed"
    
    def parse_file(self, content: str) -> List[Task]:
        """Parse markdown content into a list of Task objects."""
        tasks = []
        lines = content.split('\n')
        current_section = None
        
        current_task: Optional[Task] = None
        
        for line in lines:
            line_stripped = line.strip()
            
            # 1. Section Detection
            if line_stripped.startswith("##"):
                current_section = line_stripped
                continue
                
            # 2. Task Detection (- [ ] ...)
            task_match = re.match(r'^\s*-\s*\[( |x|/)\]\s+(.*)', line)
            if task_match:
                # Save previous task if exists
                if current_task:
                    tasks.append(current_task)
                
                status_char = task_match.group(1)
                full_desc = task_match.group(2)
                
                # Parse Role (@engineer)
                role = "engineer" # Default
                role_match = re.search(r'@(\w+)', full_desc)
                if role_match:
                    role = role_match.group(1)
                    full_desc = full_desc.replace(f"@{role}", "").strip()
                
                # Determine Status
                status = "PENDING"
                if status_char.lower() == 'x':
                    status = "COMPLETED"
                elif status_char == '/':
                    status = "IN_PROGRESS"
                
                # Create Task stub
                current_task = Task(
                    description=full_desc,
                    status=status,
                    assigned_worker=role
                )
                continue

            # 3. Metadata Detection (Indented items)
            if current_task and (line.startswith("  -") or line.startswith("\t-")):
                meta_content = line.strip()[1:].strip() # Remove leading dash
                
                if meta_content.lower().startswith("context:"):
                    files = meta_content[8:].strip().split(",")
                    current_task.input_files = [f.strip() for f in files]
                    
                elif meta_content.lower().startswith("flags:"):
                    flags = meta_content[6:].strip().split(",")
                    for flag in flags:
                        key, val = flag.split("=")
                        key = key.strip()
                        val = val.strip().lower() == "true"
                        
                        if hasattr(current_task, key):
                            setattr(current_task, key, val)

        # Append last task
        if current_task:
            tasks.append(current_task)
            
        return tasks

    def generate_markdown(self, tasks: List[Task], header: str = "# Project Plan") -> str:
        """Render tasks into Markdown."""
        todo = []
        in_progress = []
        completed = []
        
        for t in tasks:
            if t.status == "COMPLETED":
                completed.append(t)
            elif t.status == "IN_PROGRESS":
                in_progress.append(t)
            else:
                todo.append(t)

        output = [header, ""]
        
        def _render_task(t: Task) -> str:
            # Checkbox
            mark = " "
            if t.status == "COMPLETED": mark = "x"
            elif t.status == "IN_PROGRESS": mark = "/"
            
            # Line
            line = f"- [{mark}] {t.description}"
            if t.assigned_worker:
                line += f" @{t.assigned_worker}"
            
            sublines = []
            # Context
            if t.input_files:
                sublines.append(f"  - Context: {', '.join(t.input_files)}")
            
            # Flags (Re-serialize relevant flags)
            flags = []
            if t.git_commit_ready: flags.append("git_commit_ready=True")
            if t.git_create_pr: flags.append("git_create_pr=True")
            
            if flags:
                sublines.append(f"  - Flags: {', '.join(flags)}")
                
            return line + "\n" + "\n".join(sublines)

        output.append("## Todo")
        for t in todo:
            output.append(_render_task(t))
        output.append("")

        output.append("## In Progress")
        for t in in_progress:
            output.append(_render_task(t))
        output.append("")

        output.append("## Completed")
        for t in completed:
            output.append(_render_task(t))
            
        return "\n".join(output)
