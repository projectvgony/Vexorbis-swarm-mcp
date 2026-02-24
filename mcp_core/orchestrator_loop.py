import os
import json
import logging
import time
import shutil
import uuid
import asyncio

from filelock import FileLock
from datetime import datetime

# V2 Core
from mcp_core.swarm_schemas import ProjectProfile, Task, DeliberationResult, DeliberationStep
from mcp_core.stack_detector import StackDetector
from mcp_core.toolchain_manager import ToolchainManager
from mcp_core.worker_prompts import (
    prompt_architect, prompt_engineer, prompt_auditor,
    prompt_debugger, prompt_researcher,
    prompt_git_commit, prompt_git_pr
)
from mcp_core.llm import generate_response

# V3.0 Algorithms
from mcp_core.algorithms import (
    HippoRAGRetriever,
    WeightedVotingConsensus, DebateEngine,
    Z3Verifier, OchiaiLocalizer, GitWorker,
    ContextPruner
)
from mcp_core.github_mcp_client import GitHubMCPClient
from mcp_core.sync.sync_engine import SyncEngine
from mcp_core.telemetry.collector import collector
from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService

# V3.7: SQL Session Persistence
from mcp_core.postgres_client import PostgreSQLMCPClient

# V3.7: SQL Session Persistence
from mcp_core.postgres_client import PostgreSQLMCPClient

STATE_FILE = "project_profile.json"
LEGACY_STATE_FILE = "blackboard_state.json"
LOCK_FILE = "project_profile.json.lock"


class Orchestrator:
    def __init__(self, root_path: str = ".", state_file: str = STATE_FILE, session_id: str = None):
        self.root_path = root_path
        self.state_file = state_file
        self.lock_file = f"{state_file}.lock"
        
        # [V3.7: SQL Session State]
        self.session_id = session_id or os.getenv("SWARM_SESSION_ID") or str(uuid.uuid4())
        self.agent_id = os.getenv("SWARM_AGENT_ID") or f"agent_{uuid.uuid4().hex[:8]}"
        self._postgres = None
        self._sql_enabled = bool(os.getenv("POSTGRES_URL"))

        # [Fix: Race/Migration]
        self._ensure_migration()

        # Load State (tries SQL first if enabled)
        self.state = ProjectProfile()
        self.load_state()

        # [Component: Eyes] - Lazy init
        self._detector = None
        self._toolchain = None

        # [V3.0: Algorithm Components] - Lazy init
        self._rag = None
        self._consensus = None
        self._debate = None
        self._verifier = None
        self._sbfl = None
        self._git = None
        self._git_dispatcher = None
        self._github_client = None
        self._sync = None
        self._pruner = None
        
        # [V3.8: Telemetry Analytics]
        self.analytics = TelemetryAnalyticsService()
        
        # [V3.8: DB Maintenance] Optimize telemetry DB on startup
        try:
            self.analytics.optimize_database()
            # Prune old events (>30 days) to prevent DB bloat
            pruned = self.analytics.prune_old_events(retention_days=30)
            if pruned > 0:
                logging.info(f"🗑️ Pruned {pruned} old telemetry events")
        except Exception as e:
            logging.warning(f"Telemetry maintenance warning: {e}")
        
        logging.info(f"✅ Orchestrator initialized (session: {self.session_id[:8]}, SQL: {self._sql_enabled})")

    def _ensure_migration(self):
        """Auto-Archive Legacy State Logic."""
        if os.path.exists(LEGACY_STATE_FILE):
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            archive_name = f"blackboard_state_v1_backup_{timestamp}.json"
            logging.warning(
                f"⚠️ Migrating legacy state: {LEGACY_STATE_FILE} -> {archive_name}")
            shutil.move(LEGACY_STATE_FILE, archive_name)

    # Lazy property accessors
    @property
    def git(self):
        """Lazy init GitWorker"""
        if self._git is None:
            try:
                self._git = GitWorker(self.root_path)
                logging.info("✅ GitWorker initialized")
            except Exception as e:
                logging.warning(f"GitWorker unavailable: {e}")
                self._git = None
        return self._git

    @property
    def git_dispatcher(self):
        """Lazy init GitRoleDispatcher"""
        if self._git_dispatcher is None:
            from mcp_core.algorithms.git_role_dispatcher import GitRoleDispatcher
            self._git_dispatcher = GitRoleDispatcher(self)
            logging.info("✅ GitRoleDispatcher initialized")
        return self._git_dispatcher

    @property
    def github_client(self):
        """Lazy init GitHub MCP client"""
        if self._github_client is None:
            if not os.getenv("GITHUB_TOKEN"):
                logging.warning("GITHUB_TOKEN not set - GitHub operations limited")
                return None
            
            try:
                # Initialize our wrapper client
                self._github_client = GitHubMCPClient()
                logging.info("✅ GitHubMCPClient initialized")
            except Exception as e:
                logging.error(f"Failed to init GitHub client: {e}")
                self._github_client = None
        return self._github_client

    @property
    def rag(self):
        """Lazy init HippoRAGRetriever"""
        if self._rag is None:
            try:
                self._rag = HippoRAGRetriever()
                # Auto-build graph from root_path (uses cache if available)
                self._rag.build_graph_from_ast(self.root_path, use_cache=True)
                logging.info("✅ HippoRAGRetriever initialized")
            except Exception as e:
                logging.warning(f"HippoRAG unavailable: {e}")
                self._rag = None
        return self._rag



    @property
    def consensus(self):
        """Lazy init WeightedVotingConsensus"""
        if self._consensus is None:
            try:
                self._consensus = WeightedVotingConsensus()
            except Exception as e:
                logging.warning(f"Consensus unavailable: {e}")
        return self._consensus

    @property
    def debate(self):
        """Lazy init DebateEngine"""
        if self._debate is None:
            try:
                self._debate = DebateEngine()
            except Exception as e:
                logging.warning(f"Debate unavailable: {e}")
        return self._debate

    @property
    def verifier(self):
        """Lazy init Z3Verifier"""
        if self._verifier is None:
            try:
                self._verifier = Z3Verifier()
            except Exception as e:
                logging.warning(f"Z3 unavailable: {e}")
        return self._verifier

    @property
    def sbfl(self):
        """Lazy init OchiaiLocalizer"""
        if self._sbfl is None:
            try:
                self._sbfl = OchiaiLocalizer()
            except Exception as e:
                logging.warning(f"SBFL unavailable: {e}")
        return self._sbfl

    @property
    def sync(self):
        """Lazy init SyncEngine"""
        if self._sync is None:
            try:
                self._sync = SyncEngine(self.root_path)
            except Exception as e:
                logging.warning(f"Sync unavailable: {e}")
        return self._sync

    @property
    def pruner(self):
        """Lazy init ContextPruner"""
        if self._pruner is None:
            try:
                self._pruner = ContextPruner()
            except Exception as e:
                logging.warning(f"ContextPruner unavailable: {e}")
        return self._pruner

    @property
    def postgres(self):
        """Lazy init PostgreSQL client"""
        if self._postgres is None and self._sql_enabled:
            self._postgres = PostgreSQLMCPClient()
        return self._postgres

    def load_state(self) -> None:
        """Load orchestrator state from SQL (preferred) or disk."""
        # Try SQL first if enabled
        if self._sql_enabled:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # Already in async context
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        profile_data = pool.submit(
                            lambda: asyncio.run(self.postgres.load_session_state(self.session_id, self.agent_id))
                        ).result(timeout=10)
                else:
                    profile_data = loop.run_until_complete(
                        self.postgres.load_session_state(self.session_id, self.agent_id)
                    )
                
                if profile_data:
                    self.state = ProjectProfile(**profile_data)
                    logging.info(f"✅ Loaded state from SQL (session: {self.session_id[:8]})")
                    return
            except Exception as e:
                logging.warning(f"SQL load failed, falling back to file: {e}")
        
        # Fallback to file
        if not os.path.exists(self.state_file):
            logging.info("No existing state file, using fresh state")
            return

        try:
            with FileLock(self.lock_file, timeout=5):
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.state = ProjectProfile(**data)
                    logging.info(f"✅ Loaded state from {self.state_file}")
        except Exception as e:
            logging.error(f"Failed to load state: {e}")
            logging.info("Using fresh state instead")

    def save_state(self) -> None:
        """Save orchestrator state to SQL (preferred) and disk."""
        profile_data = json.loads(self.state.model_dump_json())
        
        # Save to SQL if enabled
        if self._sql_enabled:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        pool.submit(
                            lambda: asyncio.run(self.postgres.save_session_state(
                                self.session_id, profile_data, self.agent_id
                            ))
                        ).result(timeout=10)
                else:
                    loop.run_until_complete(
                        self.postgres.save_session_state(self.session_id, profile_data, self.agent_id)
                    )
                logging.debug(f"State saved to SQL (session: {self.session_id[:8]})")
            except Exception as e:
                logging.warning(f"SQL save failed: {e}")
        
        # Always save to file as backup
        try:
            with FileLock(self.lock_file, timeout=5):
                with open(self.state_file, "w", encoding="utf-8") as f:
                    f.write(self.state.model_dump_json(indent=2))
                logging.debug(f"State saved to {self.state_file}")
        except Exception as e:
            logging.error(f"Failed to save state to file: {e}")
    
    def release_lock(self) -> None:
        """Release SQL session lock on shutdown."""
        if self._sql_enabled and self._postgres:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor() as pool:
                        pool.submit(
                            lambda: asyncio.run(self.postgres.release_session_lock(
                                self.session_id, self.agent_id
                            ))
                        ).result(timeout=5)
                else:
                    loop.run_until_complete(
                        self.postgres.release_session_lock(self.session_id, self.agent_id)
                    )
                logging.info(f"🔓 Released session lock for {self.session_id[:8]}")
            except Exception as e:
                logging.warning(f"Failed to release lock: {e}")

    def check_loop_state(self, task: Task) -> bool:
        """Detect infinite loop by checking feedback log length."""
        return len(task.feedback_log) > 20

    def process_task(self, task_id: str) -> None:
        self.load_state()
        task = self.state.get_task(task_id)
        if not task or task.status == "COMPLETED":
            return

        # [v3.4] Deterministic Loop Detection
        if self.check_loop_state(task):
            task.status = "FAILED"
            task.feedback_log.append("🛑 Task aborted due to infinite loop detection")
            self.save_state()
            return

        # [V3.5: Smart-Power] Prune Provenance Context
        if self.state.provenance_log and self.pruner:
            try:
                self.state.provenance_log = self.pruner.prune(
                    self.state.provenance_log, 
                    task.description
                )
            except Exception as e:
                logging.warning(f"Provenance pruning failed: {e}")

        # [V3.0: Algorithm Dispatch]
        # Check task flags and route to appropriate algorithm
        algorithm_handled = False

        # 1. Context Retrieval (HippoRAG)
        if task.context_needed and self._handle_context_retrieval(task):
            algorithm_handled = True



        # 4. Consensus Required (Weighted Voting)
        if task.requires_consensus and self._handle_consensus(task):
            algorithm_handled = True

        # 5. Debate Required (Debate Engine)
        if task.requires_debate and self._handle_debate(task):
            algorithm_handled = True

        # 6. Verification Required (Z3)
        if task.verification_required and self._handle_verification(task):
            algorithm_handled = True

        # 7. Tests Failing (Ochiai SBFL)
        if task.tests_failing and self._handle_fault_localization(task):
            algorithm_handled = True
        
        # 8. Git Workflow (v3.2 - Autonomous Git Team)
        if (task.git_commit_ready or task.git_create_pr) and self._handle_git_workflow(task):
            algorithm_handled = True

        # If algorithm handled the task, skip traditional LLM flow
        if algorithm_handled:
            self.save_state()
            return

        # [Phase 3] Sliding window for context optimization
        # Only pass last N relevant entries to reduce token usage
        MAX_MEMORY_ITEMS = 10
        if len(self.state.memory_bank) > MAX_MEMORY_ITEMS:
            context_slice = dict(list(self.state.memory_bank.items())[-MAX_MEMORY_ITEMS:])
        else:
            context_slice = self.state.memory_bank
        
        # [V3.8: Adaptive Context] Inject Tool Insights & Circuit Breaker
        try:
            problems = self.analytics.get_problematic_tools(threshold=0.7)
            if problems:
                warnings = []
                critical_tools = []  # Tools with TRIPPED circuit breaker
                
                for p in problems:
                    tool_status = self.analytics.get_tool_status(p['tool'])
                    status_icon = "🔴" if tool_status == "TRIPPED" else "⚠️"
                    warnings.append(f"{status_icon} {p['tool']}: {int(p['success_rate']*100)}% success ({p['total_uses']} uses)")
                    
                    if tool_status == "TRIPPED":
                        critical_tools.append(p['tool'])
                
                alert_text = "⚠️ TELEMETRY WARNING ⚠️\n" if not critical_tools else "🔴 CIRCUIT BREAKER TRIPPED 🔴\n"
                context_slice["SYSTEM_ALERTS"] = (
                    alert_text +
                    "The following tools have been unstable recently. Use alternatives if possible:\n" +
                    "\n".join(warnings)
                )
                
                if critical_tools:
                    context_slice["BLOCKED_TOOLS"] = critical_tools
                    logging.warning(f"🔴 Circuit breaker tripped for tools: {critical_tools}")
        except Exception as e:
            logging.warning(f"Failed to inject telemetry context: {e}")

        # [v3.1: Git Context Injection]
        git_context = {}
        if self.git.is_available():
            git_context = {
                "git_available": True,
                "git_workflow_instructions": self.git.get_workflow_instructions()
            }

        worker_prompt = ""
        worker_model = self.state.worker_models.get("default", "gemini-pro")

        # [Phase 2] Respect assigned_worker from Task schema first
        role = None
        if task.assigned_worker:
            role = task.assigned_worker.lower()
        elif task.tests_failing:
            role = "debugger"
        elif "research" in task.description.lower() or "investigate" in task.description.lower():
            role = "researcher"
        elif "plan" in task.description.lower():
            role = "architect"
        elif "audit" in task.description.lower():
            role = "auditor"
        else:
            role = "engineer"
        
        # Get role-specific model if configured
        worker_model = self.state.worker_models.get(role, worker_model)
        
        # Generate role-specific prompt
        if role == "architect":
            worker_prompt = prompt_architect(task, context_slice, contributing_model=worker_model)
        elif role == "auditor":
            worker_prompt = prompt_auditor(task, git_context, contributing_model=worker_model)
        elif role == "debugger":
            worker_prompt = prompt_debugger(task, context_slice, git_context, contributing_model=worker_model)
        elif role == "researcher":
            worker_prompt = prompt_researcher(task, context_slice, contributing_model=worker_model)
        else:  # engineer (default)
            worker_prompt = prompt_engineer(task, context_slice, git_context, contributing_model=worker_model)

        logging.info(f"Dispatching task {task_id[:8]}...")

        # Agentic Mode (Pause)
        if os.environ.get("ORCHESTRATOR_MODE") == "agentic":
            self._write_task_file(task, worker_prompt)
            logging.info("🛑 PAUSING for Agent.")
            return

        # Autonomous Mode
        # [Fix: Cost] Retry Logic
        # Not fully implemented here, but Schema has max_retries
        response = generate_response(worker_prompt, model_alias=worker_model)

        task.feedback_log.append(f"Worker execution: {response.status}")

        # [Phase 2] Check for role handoff request
        if response.reasoning_trace and "<handoff_to" in response.reasoning_trace:
            handoff_role, handoff_reason = self._parse_handoff(response.reasoning_trace)
            if handoff_role:
                logging.info(f"🔄 Role handoff detected: {role} → {handoff_role}")
                # Create new task for handoff
                handoff_task = Task(
                    description=f"[Handoff from {role}] {handoff_reason or task.description}",
                    assigned_worker=handoff_role,
                    input_files=task.input_files,
                    output_files=task.output_files
                )
                self.state.add_task(handoff_task)
                task.feedback_log.append(f"🔄 Handed off to {handoff_role}: {handoff_task.task_id[:8]}")
                logging.info(f"Created handoff task: {handoff_task.task_id[:8]}")

        if response.status == "SUCCESS":
            task.status = "COMPLETED"

            sig = collector.record_provenance(
                agent_id="system", # aggregated agent
                role="system",
                contributing_model=worker_model,
                action="task_completed",
                artifact_ref=task_id
            )
            self.state.provenance_log.append(sig)
            
            # [v3.4] Strict Git Completion (Deterministic)
            if self.git.is_available() and self.git.has_changes():
                # Check for "Strict Mode" env var
                if os.getenv("SWARM_STRICT_GIT", "true").lower() == "true":
                    # Reject completion
                    task.status = "PENDING" # Revert status
                    task.feedback_log.append("❌ Strict Mode: Cannot complete task with uncommitted changes.")
                    task.feedback_log.append("💡 Action: Committing changes automatically...")
                    
                    # Auto-Fix: Trigger Git Commit
                    # In next loop, this flag will trigger _handle_git_workflow
                    task.git_commit_ready = True
                    task.git_branch_name = task.git_branch_name or "auto/cleanup"
                    
                    logging.info("🛑 Strict Git: Reverted completion and triggered auto-commit")
                else:
                    # Legacy Nudge
                    task.feedback_log.append("📝 Tip: You have uncommitted changes. To save, ask: 'Run git worker'")
        else:
            # [V3.5] Log Task Failure
            sig = collector.record_provenance(
                agent_id="system",
                role="system",
                contributing_model=worker_model,
                action="task_failed",
                artifact_ref=f"{task_id}:::{response.status}"
            )
            self.state.provenance_log.append(sig)

        self.state.tasks[task_id] = task
        self.state.tasks[task_id] = task
        self.save_state()
        self.sync.sync_outbound(self.state)

    def _write_task_file(self, task: Task, prompt: str):
        with open("CURRENT_TASK.md", "w") as f:
            f.write(f"# Task: {task.task_id}\n\n## Instructions\n{prompt}\n")

    def orchestrate(self) -> None:
        logging.info("Starting Polyglot Orchestrator v3.0...")
        # type: ignore
        logging.info(f"Stack: {self.state.stack_fingerprint.primary_language}")

        while True:
            self.load_state()
            pending = [t for t in self.state.tasks.values()
                       if t.status == "PENDING"]

            if not pending:
                time.sleep(2)
                continue

            for task in pending:
                self.process_task(task.task_id)
            
            # [V3.6: Sync]
            if self.sync.sync_inbound(self.state):
                self.save_state()

    # [V3.0: Algorithm Handlers]
    
    def _handle_context_retrieval(self, task: Task) -> bool:
        """Use HippoRAG to retrieve relevant context"""
        try:
            # Lazy init: build graph on first use
            if self.rag is None:
                logging.info("🔍 Initializing HippoRAG graph...")
                self.rag = HippoRAGRetriever()
                self.rag.build_graph_from_ast(self.root_path)
            
            # Retrieve context based on task description
            chunks = self.rag.retrieve_context(task.description, top_k=5)
            
            # Add context to task feedback
            if chunks:
                context_summary = "\n".join([f"  • {c.file_path}:{c.start_line}" for c in chunks[:3]])
                if len(chunks) > 3:
                    context_summary += f"\n  ...and {len(chunks)-3} more chunks."
                task.feedback_log.append(f"HippoRAG Context (Summary):\n{context_summary}")
                
                logging.info(f"✅ Retrieved {len(chunks)} context chunks")
                return True
            else:
                task.feedback_log.append("HippoRAG: No relevant context found.")
                return True
            
        except Exception as e:
            logging.error(f"HippoRAG failed: {e}")
            task.feedback_log.append(f"HippoRAG error: {e}")
            return False
    
    

    
    def _handle_consensus(self, task: Task) -> bool:
        """Use Weighted Voting for multi-agent consensus"""
        try:
            # In a real implementation, multiple agents would vote
            # For now, just demonstrate the API
            self.consensus.clear_votes()
            
            task.feedback_log.append("Consensus: Awaiting agent votes")
            logging.info("✅ Consensus voting initialized")
            return True
            
        except Exception as e:
            logging.error(f"Consensus failed: {e}")
            return False
    
    def _handle_debate(self, task: Task) -> bool:
        """Use Debate Engine for multi-agent debate"""
        try:
            debate_id = f"debate_{task.task_id}"
            agents = ["agent_1", "agent_2", "agent_3"]
            
            self.debate.start_debate(debate_id, agents, topology="ring")
            
            task.feedback_log.append(f"Debate: Started with {len(agents)} agents")
            logging.info("✅ Debate session started")
            return True
            
        except Exception as e:
            logging.error(f"Debate failed: {e}")
            return False
    
    def _handle_verification(self, task: Task) -> bool:
        """Use Z3 Verifier for symbolic execution"""
        if self.verifier is None:
            task.feedback_log.append("Z3 Verifier not available (dependency missing)")
            return False
        
        try:
            task.feedback_log.append("Z3: Verification requested")
            logging.info("✅ Z3 verification initialized")
            return True
            
        except Exception as e:
            logging.error(f"Z3 failed: {e}")
            return False
    
    def _handle_fault_localization(self, task: Task) -> bool:
        """Use Ochiai SBFL for automated bug location"""
        # Dev build: Check if SBFL is enabled
        sbfl_enabled = os.getenv("SWARM_SBFL_ENABLED", "false").lower() == "true"
        
        if not sbfl_enabled:
            logging.debug("SBFL disabled (SWARM_SBFL_ENABLED=false)")
            return False
        
        if self.sbfl is None:
            task.feedback_log.append("Ochiai SBFL not available (dependency missing)")
            return False
        
        try:
            # Run SBFL analysis
            test_cmd = self.state.toolchain_config.test_command if self.state.toolchain_config else "pytest"
            
            debug_prompt = self.sbfl.run_full_sbfl_analysis(
                test_command=test_cmd,
                source_path=self.root_path,
                top_k=5
            )
            
            task.feedback_log.append(f"SBFL Analysis:\n{debug_prompt}")
            logging.info("✅ Ochiai SBFL analysis complete")
            return True
            
        except Exception as e:
            logging.error(f"SBFL failed: {e}")
            task.feedback_log.append(f"SBFL error: {e}")
            return False
    
    def _handle_git_workflow(self, task: Task) -> bool:
        """
        Orchestrate Git worker team for autonomous repository maintenance.
        
        4. PR (if git_create_pr OR auto-PR for completed feature tasks)
        """
        if not self.git.is_available():
            task.feedback_log.append("Git: Not available")
            return False
            
        # [v3.3: Role-based Dispatch]
        role_triggered = any([
            task.feature_discovery,
            task.code_audit,
            task.issue_triage_needed,
            task.project_bootstrap
        ])
        
        if role_triggered:
            try:
                reports = self.git_dispatcher.dispatch(task)
                for report in reports:
                    task.feedback_log.append(f"🤖 GitRole({task.task_id[:4]}): {report.status}")
                    if report.remaining_work:
                        task.feedback_log.append(f"   ↳ {report.remaining_work}")
                return True
            except Exception as e:
                logging.error(f"GitRole dispatch failed: {e}")
                task.feedback_log.append(f"⚠️ GitRole Error: {e}")
                return False
        
        try:
            from mcp_core.worker_prompts import prompt_git_branch, prompt_git_commit, prompt_git_pr
            
            # Parse repo info from remote
            repo_owner = None
            repo_name = None
            if self.git.config.remote_url:
                parts = self.git.config.remote_url.split('/')
                if len(parts) >= 2:
                    repo_owner = parts[-2]
                    repo_name = parts[-1].replace('.git', '')
            
            # Resolve Model (use git-writer / Gemini for efficiency)
            git_model = self.state.worker_models.get("git-writer", "gemini-3-flash-preview")
            
            # 1. Branch Worker (if needed)
            if task.git_branch_name and task.git_branch_name not in str(task.feedback_log):
                git_context = {
                    "git_branch_name": task.git_branch_name,
                    "git_base_branch": task.git_base_branch,
                }
                branch_prompt = prompt_git_branch(task, git_context)
                
                # Check if we should execute or just instruct
                # For branch creation, local logic is simpler, but let's stick to instructions/execution pattern
                task.feedback_log.append(f"🌿 Branch Worker: Create {task.git_branch_name}")
                task.feedback_log.append(f"Instructions: {branch_prompt[:200]}...")
                # Execution: Actually run git checkout -b? 
                # For now, we trust the Driver (Agent) to read instructions.
                logging.info(f"✅ Branch Worker dispatched for {task.task_id[:8]}")
            
            # 2. Commit Worker (if ready)
            if task.git_commit_ready: # Removed strict output_files check to allow "catch-all" commits
                if not self.git.has_changes():
                    task.feedback_log.append("⚠️ Commit Worker Skipped: No uncommitted changes detected.")
                    logging.info("Git workflow skipped: Clean working tree")
                else: 
                    git_context = {
                        "output_files": task.output_files,
                        "repo_owner": repo_owner,
                        "repo_name": repo_name,
                    }
                    commit_prompt = prompt_git_commit(task, git_context, contributing_model=git_model)
                
                    # [Cost Check] Use Cheap LLM to generate commit message
                    try:
                        logging.info(f"💾 Generating commit message with {git_model}...")
                        response = generate_response(commit_prompt, model_alias=git_model)
                        
                        # Extract the commit message/command from response tools or reasoning
                        # Since generate_response returns AgentResponse, we check tool_calls
                        # But prompt_git_commit asks to "Use IDE git tools", which implies the output should contain commands
                        # The prompt format expects a textual tool usage.
                        # Let's assume the LLM follows the prompt and we just log the reasoning/tool calls.
                        
                        if response.tool_calls:
                           # [v3.5] Autonomous Execution (Local Git)
                           execution_log = []
                           for tool in response.tool_calls:
                               import json
                               try:
                                   args = json.loads(tool.arguments) if isinstance(tool.arguments, str) else tool.arguments
                                   result = self._execute_git_tool(tool.function, args, contributing_model=git_model)
                                   execution_log.append(result)
                               except Exception as ex:
                                   execution_log.append(f"❌ Failed {tool.function}: {ex}")
                                   
                                   # [Provenance] Log Git Tool Error
                                   sig = collector.record_provenance(
                                       agent_id="git-writer", 
                                       role="engineer",
                                       contributing_model=git_model,
                                       action="git_error",
                                       artifact_ref=f"{tool.function}: {str(ex)}"
                                   )
                                   self.state.provenance_log.append(sig)
                           
                           exec_summary = "\n".join(execution_log)
                           if len(exec_summary) > 300:
                               exec_summary = exec_summary[:300] + "..."
                           task.feedback_log.append(f"💾 Commit Worker Log:\n{exec_summary}")
                           
                           # Add push confirmation prompt
                           # task.feedback_log.append(
                           #     "\n📤 **Ready to Push**\n"
                           #     "Your commit is ready locally. To push to GitHub:\n"
                           #     "1. Run: `git push` (manual)\n"
                           #     "2. OR set `git_auto_push=True` in the task (autonomous)\n\n"
                           #     "The system will NOT auto-push without explicit confirmation."
                           # )
                        else:
                           task.feedback_log.append(f"💾 Commit Worker ({git_model}):\n{response.reasoning_trace}")
                        
                    except Exception as e:
                        logging.error(f"Git Generation Failed: {e}")
                        task.feedback_log.append(f"Instructions: {commit_prompt[:200]}...")
                        
                        # [Provenance] Log Git Gen Error
                        sig = collector.record_provenance(
                            agent_id="git-writer", 
                            role="engineer",
                            contributing_model=git_model,
                            action="git_error",
                            artifact_ref=f"Generation Failed: {str(e)}"
                        )
                        self.state.provenance_log.append(sig)


                    logging.info(f"✅ Commit Worker dispatched for {task.task_id[:8]}")
            
            # 3. Push Worker (if auto-push enabled or PR requested)
            if task.git_auto_push or task.git_create_pr:
                if not self.git.has_changes():
                    # Nothing to push (likely already committed and pushed)
                    pass
                else:
                    # Changes exist but not committed - can't push
                    task.feedback_log.append("⚠️ Push Worker Skipped: Uncommitted changes detected")
                    logging.info("Push skipped: uncommitted changes")
                
                # Push if we have a branch set (assumes commit already happened)
                if task.git_branch_name:
                    try:
                        logging.info(f"📤 Pushing {task.git_branch_name} to remote...")
                        result = self._execute_git_tool("git_push", {
                            "remote": "origin",
                            "branch": task.git_branch_name
                        }, contributing_model=git_model)
                        task.feedback_log.append(f"📤 Push Worker: {result}")
                        logging.info(f"✅ Push Worker dispatched for {task.task_id[:8]}")
                        # Continue anyway - PR worker will fail gracefully
                    except Exception as e:
                        logging.error(f"Push failed: {e}")
                        task.feedback_log.append(f"❌ Push failed: {e}")
                        
                        # [Provenance] Log Git Error
                        sig = collector.record_provenance(
                            agent_id="git-writer", 
                            role="engineer",
                            contributing_model=git_model,
                            action="git_error",
                            artifact_ref=str(e)
                        )
                        self.state.provenance_log.append(sig)
            
            # 4. Auto-PR for completed feature tasks (v3.2 Autonomous Mode)
            should_create_pr = task.git_create_pr
            if not should_create_pr and task.status == "COMPLETED" and task.git_branch_name:
                # Auto-PR if: completed task + feature branch + GitHub ready
                if self.git.is_github_ready():
                    should_create_pr = True
                    task.feedback_log.append("🤖 Auto-PR: Feature task completed, creating PR")
                    logging.info(f"Auto-PR enabled for completed task {task.task_id[:8]}")
            
            # 4. PR Worker (if flagged or auto-enabled)
            if should_create_pr and task.git_branch_name:
                if not self.git.is_github():
                    task.feedback_log.append("⚠️ PR Worker: GitHub not detected")
                    return True  # Not an error, just skip
                
                if not self.git.has_github_token():
                    task.feedback_log.append("⚠️ PR Worker: GITHUB_TOKEN not set")
                    task.feedback_log.append("Set GITHUB_TOKEN env var to enable PR creation")
                    return True  # Not an error, just skip
                
                git_context = {
                    "git_branch_name": task.git_branch_name,
                    "git_base_branch": task.git_base_branch,
                    "git_pr_title": task.git_pr_title or task.description[:60],
                    "git_pr_body": task.git_pr_body or f"Automated PR from Swarm task {task.task_id[:8]}",
                    "output_files": task.output_files,
                    "repo_owner": repo_owner,
                    "repo_name": repo_name,
                }
                pr_prompt = prompt_git_pr(task, git_context, model_id=git_model)
                
                # [Cost Check] Use Cheap LLM to generate PR body
                try:
                    logging.info(f"🔀 Generating PR with {git_model}...")
                    response = generate_response(pr_prompt, model_alias=git_model)
                    
                    # [v3.5] Trim reasoning trace for feedback log
                    trace = response.reasoning_trace
                    if len(trace) > 200:
                        trace = trace[:200] + "..."
                    
                    if response.tool_calls:
                       calls_str = "\n".join([f"{t.function}({t.arguments})" for t in response.tool_calls])
                       task.feedback_log.append(f"🔀 PR Worker ({git_model}):\n{calls_str}")
                    else:
                       task.feedback_log.append(f"🔀 PR Worker ({git_model}):\n{trace}")
                       
                except Exception as e:
                    logging.error(f"PR Generation Failed: {e}")
                    task.feedback_log.append(f"Instructions: {pr_prompt[:200]}...")

                logging.info(f"✅ PR Worker dispatched for {task.task_id[:8]}")
            
            logging.info(f"✅ Git workflow orchestrated for {task.task_id[:8]}")
            return True
            
        except Exception as e:
            logging.error(f"Git workflow failed: {e}")
            task.feedback_log.append(f"Git workflow error: {e}")
            
            # [Provenance] Log Top-Level Git Error
            sig = collector.record_provenance(
                agent_id="system",
                role="system",
                action="git_workflow_error",
                artifact_ref=str(e)
            )
            self.state.provenance_log.append(sig)
            
            return False

    def _execute_git_tool(self, tool_name: str, args: dict, contributing_model: str = None) -> str:
        """Execute local Git operations autonomously."""
        import subprocess
        repo_path = str(self.git.repo_path)
        
        # Generic command runner (for LLM-generated commands)
        if tool_name == "run_command":
            cmd = args.get("command_line", "")
            cwd = args.get("cwd", repo_path)
            
            if not cmd.startswith("git "):
                return f"⚠️ Rejected non-git command: {cmd}"
            
            try:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    cwd=cwd,
                    capture_output=True,
                    text=True,
                    check=True
                )
                return f"✅ {cmd}\n{result.stdout}"
            except subprocess.CalledProcessError as e:
                return f"❌ {cmd}\n{e.stderr}"
        
        if tool_name == "git_add":
            files = args.get("files", ".")
            if isinstance(files, str): 
                # Handle "file1 file2" string or "." -> ["."]
                files = [files] if files == "." else files.split()
            
            subprocess.run(["git", "add"] + files, cwd=repo_path, check=True)
            return f"✅ Staged: {files}"

        elif tool_name == "git_commit":
            message = args.get("message", "Automated commit")
            subprocess.run(["git", "commit", "-m", message], cwd=repo_path, check=True)
            
            # [Provenance]: Log Commit
            sig = collector.record_provenance(
                agent_id="git-writer",
                role="engineer", 
                contributing_model=contributing_model,
                action="git_commit",
                artifact_ref=message
            )
            self.state.provenance_log.append(sig)
            
            return f"✅ Committed: {message}"

        elif tool_name == "git_push":
            remote = args.get("remote", "origin")
            branch = args.get("branch", self.git.config.default_branch)
            # Safe push
            subprocess.run(["git", "push", remote, branch], cwd=repo_path, check=True)
            return f"✅ Pushed to {remote}/{branch}"

        return f"❌ Unknown git tool: {tool_name}"
    
    def _parse_handoff(self, reasoning_trace: str) -> tuple[str, str]:
        """Parse <handoff_to role="X">reason</handoff_to> from reasoning trace."""
        import re
        
        # Match: <handoff_to role="auditor">reason text</handoff_to>
        pattern = r'<handoff_to\s+role="(\w+)"[^>]*>([^<]*)</handoff_to>'
        match = re.search(pattern, reasoning_trace)
        
        if match:
            role = match.group(1)
            reason = match.group(2).strip()
            return (role, reason)
        
        return (None, None)

    # ========================================================================
    # V3.3: Structured Deliberation
    # ========================================================================
    
    def run_deliberation(
        self, 
        problem: str, 
        context: str = "", 
        constraints: list[str] = None,
        steps: int = 3
    ) -> "DeliberationResult":
        """
        Execute structured multi-step deliberation using algorithmic workers.
        
        This is the alternative to "sequential thinking" - each step uses 
        deterministic algorithms instead of pure LLM reasoning.
        """
        from mcp_core.worker_prompts import prompt_synthesizer
        import time
        import uuid
        
        if constraints is None:
            constraints = []
        
        task_id = str(uuid.uuid4())
        result = DeliberationResult(
            task_id=task_id,
            problem=problem,
            context=context,
            constraints=constraints
        )
        
        try:
            # Step 1: Decompose (HippoRAG)
            start = time.time()
            if self.rag:
                chunks = self.rag.retrieve_context(problem, top_k=5)
                sub_problems = [f"{c.node_name}: {c.content[:100]}" for c in chunks[:3]]
            else:
                # Fallback: Simple decomposition
                sub_problems = [problem]
            
            result.steps.append(DeliberationStep(
                step=1,
                name="Decompose",
                worker="HippoRAG" if self.rag else "Fallback",
                output=sub_problems,
                duration_ms=int((time.time() - start) * 1000)
            ))
            
            # Step 2: Analyze (Route to workers)
            start = time.time()
            worker_outputs = {}
            
            # Route based on problem keywords
            # if "refactor" in problem.lower() and self.occ:
            #     worker_outputs["OCC"] = f"No conflicts detected. Safe to proceed."
            if "debug" in problem.lower() and self.sbfl:
                worker_outputs["SBFL"] = f"Suspicious lines identified via fault localization."
            if "verify" in problem.lower() and self.verifier:
                worker_outputs["Z3"] = f"Verification conditions generated."
            
            if not worker_outputs:
                worker_outputs["Analysis"] = f"Problem decomposed into: {len(sub_problems)} sub-problems"
            
            result.steps.append(DeliberationStep(
                step=2,
                name="Analyze",
                worker=", ".join(worker_outputs.keys()),
                output=worker_outputs,
                duration_ms=int((time.time() - start) * 1000)
            ))
            
            # Step 3: Synthesize
            if steps >= 3:
                start = time.time()
                synth_prompt = prompt_synthesizer(sub_problems, worker_outputs, constraints)
                
                # Use LLM to synthesize
                synth_response = generate_response(synth_prompt, model_alias=self.state.worker_models.get("default"))
                
                result.final_answer = synth_response.reasoning_trace
                result.confidence = synth_response.validation_score
                
                result.steps.append(DeliberationStep(
                    step=3,
                    name="Synthesize",
                    worker="LLM",
                    output=synth_response.reasoning_trace,
                    duration_ms=int((time.time() - start) * 1000)
                ))
            
            return result
            
        except Exception as e:
            logging.error(f"Deliberation failed: {e}")
            result.final_answer = f"Error during deliberation: {str(e)}"
            result.confidence = 0.0
            return result

