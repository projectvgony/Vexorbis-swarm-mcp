
import os
import logging
from typing import List, Dict
from mcp_core.swarm_schemas import ProjectProfile, Task
from mcp_core.sync.markdown_bridge import MarkdownBridge

logger = logging.getLogger(__name__)

class SyncEngine:
    """
    Synchronizes the 'Human Tier' (Markdown Artifacts) with the 'Machine Tier' (Blackboard).
    """
    
    def __init__(self, root_path: str = ".", plan_file: str = "docs/ai/PLAN.md"):
        self.root_path = root_path
        self.plan_path = os.path.join(root_path, plan_file)
        self.bridge = MarkdownBridge()
        
    def sync_inbound(self, profile: ProjectProfile) -> bool:
        """
        Read PLAN.md and update ProjectProfile tasks.
        Returns True if changes were made.
        """
        if not os.path.exists(self.plan_path):
            logger.warning(f"Plan file not found: {self.plan_path}")
            return False
            
        try:
            with open(self.plan_path, "r", encoding="utf-8") as f:
                content = f.read()
                
            imported_tasks = self.bridge.parse_file(content)
            changes = False
            
            # Map existing tasks by description for ID lookup
            existing_map = {t.description: t for t in profile.tasks.values()}
            
            for t_new in imported_tasks:
                if t_new.description in existing_map:
                    # Update existing task
                    t_old = existing_map[t_new.description]
                    
                    # Merge Flags (User intent in MD overrides)
                    if t_new.input_files: t_old.input_files = t_new.input_files
                    t_old.assigned_worker = t_new.assigned_worker
                    
                    # Status Merge Logic
                    # If MD says COMPLETED/IN_PROGRESS, trust it.
                    # If MD says PENDING but Agent is RUNNING, keep Agent status.
                    if t_new.status != "PENDING":
                        t_old.status = t_new.status
                    
                    # Update flags
                    t_old.git_commit_ready = t_new.git_commit_ready
                    t_old.git_create_pr = t_new.git_create_pr
                    
                    profile.tasks[t_old.task_id] = t_old
                    
                else:
                    # Create New Task
                    logger.info(f"🆕 New Task from Plan: {t_new.description}")
                    profile.add_task(t_new)
                    changes = True
            
            logger.info(f"✅ Synced {len(imported_tasks)} tasks from {self.plan_path}")
            return changes
            
        except Exception as e:
            logger.error(f"Sync Inbound Failed: {e}")
            return False

    def sync_outbound(self, profile: ProjectProfile) -> None:
        """
        Dump ProjectProfile tasks to PLAN.md.
        """
        try:
            tasks = list(profile.tasks.values())
            markdown = self.bridge.generate_markdown(tasks)
            
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.plan_path), exist_ok=True)
            
            with open(self.plan_path, "w", encoding="utf-8") as f:
                f.write(markdown)
                
            logger.info(f"💾 Updated Plan: {self.plan_path}")
            
        except Exception as e:
            logger.error(f"Sync Outbound Failed: {e}")
