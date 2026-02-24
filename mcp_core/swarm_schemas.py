import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Literal
from pydantic import BaseModel, Field
from mcp_core.config_loader import load_global_model_config

# --- 1. Enums & Literal Types ---
StackType = Literal["custom", "python:pip",
                    "node:npm", "rust:cargo", "go:mod", "polyglot:nx"]
IntentType = Literal["build", "test", "lint",
                     "format", "audit", "mutate", "clean"]
GateStatus = Literal["PENDING", "RUNNING", "PASSED", "FAILED", "SKIPPED"]

# --- 2. Toolchain Schemas ---


class IntentConfig(BaseModel):
    """Configuration for a single intent (e.g., 'test' -> 'npm test')."""
    command: str
    timeout_seconds: int = 300
    output_format: Literal["text", "junit_xml", "sarif", "json"] = "text"
    output_path: Optional[str] = None
    adapter: Optional[str] = None  # e.g. "junit_adapter"


class ToolchainConfig(BaseModel):
    """The capabilities map for the project."""
    version: str = "3.4.0"
    stack_id: StackType
    actions: Dict[IntentType, IntentConfig] = Field(default_factory=dict)
    environment: Dict[str, str] = Field(default_factory=dict)

    # [Fix: Cost] Budget & Safety
    max_retries: int = Field(
        default=3, description="Max retries for a failing task")
    budget_cap_tokens: int = Field(
        default=100000, description="Max tokens per session")

# --- 3. Stack Detection Schemas ---


class StackFingerprint(BaseModel):
    """The result of the Stack Detection Strategy."""
    primary_language: str
    toolchain_variant: str
    detected_version: Optional[str] = None
    is_monorepo: bool = False
    frameworks: List[str] = Field(default_factory=list)

# --- 4. Validation Loop Schemas ---


class GateResult(BaseModel):
    """The outcome of a single validation gate."""
    intent: IntentType
    status: GateStatus
    exit_code: int = 0
    message: str = ""
    artifact_ref: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)


class ValidationLifecycle(BaseModel):
    """The current state of the validation loop."""
    phase: Literal["IDLE", "ANALYZING", "TESTING",
                   "MUTATING", "COMPLETED"] = "IDLE"
    results: Dict[IntentType, GateResult] = Field(default_factory=dict)

# --- 5. The Brain: ProjectProfile ---



class AuthorSignature(BaseModel):
    """Cryptographic provenance for an artifact change."""
    agent_id: str
    role: Literal["architect", "engineer", "auditor", "system"]
    contributing_model: Optional[str] = None # The actual model used (e.g. gpt-4, llama-3.2-3b)
    timestamp: datetime = Field(default_factory=datetime.now)
    action: str  # e.g., "created", "modified", "approved"
    artifact_ref: Optional[str] = None # The file or task ID being signed
    signature: Optional[str] = None  # Git provides attribution for Ide usage


class Task(BaseModel):
    """Swarm v3.0 Task (Standardized)."""
    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str
    status: str = Field(pattern=r"^(PENDING|IN_PROGRESS|COMPLETED|FAILED)$")
    assigned_worker: Optional[str] = None
    
    # [New: Graph primitives]
    depends_on: List[str] = Field(default_factory=list, description="IDs of prerequisite tasks")
    input_files: List[str] = Field(default_factory=list, description="Files required context")
    output_files: List[str] = Field(default_factory=list, description="Files expected to change")

    # [v3.0: Algorithm Dispatch Flags]
    conflicts_detected: bool = Field(default=False, description="Trigger external conflict resolution")
    context_needed: bool = Field(default=False, description="Trigger HippoRAG retrieval")
    requires_consensus: bool = Field(default=False, description="Trigger weighted voting")
    requires_debate: bool = Field(default=False, description="Trigger debate engine")
    verification_required: bool = Field(default=False, description="Trigger Z3 verifier")
    tests_failing: bool = Field(default=False, description="Trigger Ochiai SBFL")
    
    # [v3.1: Git Workflow Flags]
    git_commit_ready: bool = Field(default=False, description="Signal for Git workflow")
    git_auto_push: bool = Field(default=False, description="Auto-push after commit")
    git_create_pr: bool = Field(default=False, description="Auto-create PR/MR")
    
    # [v3.2: Branch & PR Management]
    git_branch_name: Optional[str] = Field(default=None, description="Feature branch name")
    git_base_branch: str = Field(default="dev", description="Base branch for PR")
    git_pr_title: Optional[str] = Field(default=None, description="PR title")
    git_pr_body: Optional[str] = Field(default=None, description="PR description")

    # [v3.3: GitWorker Role Flags]
    feature_discovery: bool = Field(default=False, description="Trigger FeatureScoutRole")
    code_audit: bool = Field(default=False, description="Trigger CodeAuditorRole")
    issue_triage_needed: bool = Field(default=False, description="Trigger IssueTriageRole")
    project_bootstrap: bool = Field(default=False, description="Trigger ProjectLifecycleRole (start)")

    feedback_log: List[str] = Field(default_factory=list)
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: datetime = Field(default_factory=datetime.now)


class ProjectProfile(BaseModel):
    """
    The Single Source of Truth for Project Swarm v3.0.
    """
    schema_version: str = "3.4.0"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    # [New: Provenance]
    provenance_log: List[AuthorSignature] = Field(default_factory=list)

    # Stack Identity
    stack_fingerprint: Optional[StackFingerprint] = None
    toolchain_config: Optional[ToolchainConfig] = None

    # State
    tasks: Optional[Dict[str, Task]] = None
    validation: Optional[ValidationLifecycle] = None
    
    # [Fix: Context] Context Window Management
    active_context: Optional[Dict[str, Any]] = None
    memory_bank: Optional[Dict[str, Any]] = None


    worker_models: Dict[str, str] = Field(
        default_factory=lambda: {
            "default": "gemini-3-flash-preview",
            "architect": "gemini-3-flash-preview",
            "engineer": "gemini-3-flash-preview",
            "auditor": "gemini-3-flash-preview",
            "git-writer": "llama-3.2-3b",
            **load_global_model_config()
        },
        description="Map roles to model IDs"
    )

    def model_post_init(self, __context: Any) -> None:
        if self.tasks is None:
            self.tasks = {}
        if self.validation is None:
            self.validation = ValidationLifecycle()
        if self.active_context is None:
            self.active_context = {}
        if self.memory_bank is None:
            self.memory_bank = {}

    def get_task(self, task_id: str) -> Optional[Task]:
        # safety check
        if self.tasks is None:
            self.tasks = {}
        return self.tasks.get(task_id)

    def add_task(self, task: Task) -> None:
        self.tasks[task.task_id] = task

    def update_validation(self, intent: IntentType, result: GateResult) -> None:
        self.validation.results[intent] = result
        self.validation.phase = "COMPLETED"  # Simplified logic

# --- 6. Deliberation Schemas (v3.3) ---

class DeliberationStep(BaseModel):
    """A single step in the deliberation process."""
    step: int
    name: str
    worker: str
    output: Any
    duration_ms: int = 0
    timestamp: datetime = Field(default_factory=datetime.now)


class DeliberationResult(BaseModel):
    """The complete result of a deliberation."""
    task_id: str
    problem: str
    context: str = ""
    constraints: List[str] = Field(default_factory=list)
    steps: List[DeliberationStep] = Field(default_factory=list)
    final_answer: str = ""
    confidence: float = 0.0
    created_at: datetime = Field(default_factory=datetime.now)
