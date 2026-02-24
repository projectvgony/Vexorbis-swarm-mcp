import os
import json
import logging
import subprocess
from typing import Optional
from mcp_core.swarm_schemas import ToolchainConfig, IntentConfig, StackFingerprint, GateResult


class ToolchainManager:
    """
    Manages the translation of abstract intents (Build, Test, Lint)
    into concrete shell commands based on the stack.
    """

    def __init__(self, root_path: str = "."):
        self.root_path = root_path
        self.config: Optional[ToolchainConfig] = None

    def load_or_detect(self, detected_stack: StackFingerprint) -> ToolchainConfig:
        """
        1. Try to load toolchain.json
        2. If missing, generate ephemeral config based on StackFingerprint
        """
        path = os.path.join(self.root_path, "toolchain.json")
        if os.path.exists(path):
            try:
                with open(path, "r") as f:
                    data = json.load(f)
                    self.config = ToolchainConfig(**data)
                    logging.info("Loaded custom toolchain.json")
                    return self.config
            except Exception as e:
                logging.error(f"Failed to load toolchain.json: {e}")

        # Fallback: Generate Defaults
        logging.info(
            f"Generating default toolchain for {detected_stack.primary_language}")
        self.config = self._generate_defaults(detected_stack)
        return self.config

    def _generate_defaults(self, stack: StackFingerprint) -> ToolchainConfig:
        actions = {}

        if stack.primary_language == "python":
            if stack.toolchain_variant == "poetry":
                actions["test"] = IntentConfig(command="poetry run pytest")
                actions["lint"] = IntentConfig(command="poetry run flake8 .")
            else:
                actions["test"] = IntentConfig(command="pytest")
                actions["lint"] = IntentConfig(command="flake8 .")
                actions["mutate"] = IntentConfig(command="mutmut run")

        elif stack.primary_language == "node":
            actions["test"] = IntentConfig(command="npm test")
            actions["lint"] = IntentConfig(command="npm run lint")
            actions["build"] = IntentConfig(command="npm run build")
            actions["audit"] = IntentConfig(command="npm audit")

        elif stack.primary_language == "rust":
            actions["test"] = IntentConfig(command="cargo test")
            actions["lint"] = IntentConfig(command="cargo clippy")
            actions["build"] = IntentConfig(command="cargo build")
            actions["mutate"] = IntentConfig(command="XXcargo mutantsXX")

        elif stack.primary_language == "go":
            actions["test"] = IntentConfig(command="go test ./...")
            actions["build"] = IntentConfig(command="go build .")

        return ToolchainConfig(
            # type: ignore
            stack_id=f"{stack.primary_language}:{stack.toolchain_variant}",
            actions=actions
        )

    def run_intent(self, intent: str) -> GateResult:
        """
        Executes the command for the given intent.
        """
        if not self.config or intent not in self.config.actions:
            # type: ignore
            return GateResult(intent=intent, status="SKIPPED", message="No action defined")

        action = self.config.actions[intent]  # type: ignore
        logging.info(f"Executing Intent: {intent} -> {action.command}")

        try:
            # [Fix: Cost] We could enforce budget/timeout here using subprocess.run(timeout=...)
            result = subprocess.run(
                action.command,
                shell=True,
                cwd=self.root_path,
                capture_output=True,
                text=True,
                timeout=action.timeout_seconds
            )

            status = "PASSED" if result.returncode == 0 else "FAILED"
            return GateResult(
                intent=intent,  # type: ignore
                status=status,
                exit_code=result.returncode,
                message=result.stdout + "\n" + result.stderr
            )

        except subprocess.TimeoutExpired:
            # type: ignore
            return GateResult(intent=intent, status="FAILED", message="Timed out")
        except Exception as e:
            # type: ignore
            return GateResult(intent=intent, status="FAILED", message=str(e))
