from typing import List, Optional
import subprocess

def peek_output(command: str, lines: int = 20) -> str:
    """
    Run a command and return the first N lines of output synchronously.
    
    WARNING: Use only for fast, read-only commands (ls, git status, cat). 
    Do NOT use for long-running processes or commands that modify state interactively.
    """
    try:
        # Run command with timeout enforcement
        # Using shell=True for Windows flexibility, but safer to use string parsing for args if security is a concern.
        # For a dev tool, shell=True is acceptable if inputs are controlled.
        proc = subprocess.run(
            command, 
            capture_output=True, 
            text=True, 
            shell=True,
            timeout=5.0
        )
        
        output = proc.stdout.strip()
        if not output and proc.stderr:
            output = f"⚠️ STDERR:\n{proc.stderr.strip()}"
            
        lines_list = output.split('\n')
        preview = "\n".join(lines_list[:lines])
        
        if len(lines_list) > lines:
            preview += f"\n... ({len(lines_list) - lines} more lines)"
            
        return preview
        
    except subprocess.TimeoutExpired:
        return f"⏰ Command timed out after 5.0s: {command}"
    except Exception as e:
        return f"❌ Execution error: {e}"
