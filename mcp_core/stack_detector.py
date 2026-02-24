import os
import tomllib  # Built-in in Python 3.11+, use pip install tomli if <3.11
import json
from typing import List
from mcp_core.swarm_schemas import StackFingerprint


class StackDetector:
    """
    Implements the Swarm Detection Strategy
    to identify the technology stack of the workspace.
    """

    def __init__(self, root_path: str = "."):
        self.root_path = root_path

    def detect(self) -> StackFingerprint:
        """
        Main entry point. Scans root for marker files and returns a fingerprint.
        """
        files = os.listdir(self.root_path)

        # Priority 1: Workspace Orchestrators (Polyglot)
        if "nx.json" in files:
            return StackFingerprint(
                primary_language="polyglot",
                toolchain_variant="nx",
                is_monorepo=True
            )

        # Priority 2: Language Specific
        # Rust
        if "Cargo.toml" in files:
            return self._analyze_rust(files)

        # Python
        if "pyproject.toml" in files or "requirements.txt" in files:
            return self._analyze_python(files)

        # Node.js
        if "package.json" in files:
            return self._analyze_node(files)

        # Go
        if "go.mod" in files:
            return StackFingerprint(primary_language="go", toolchain_variant="mod")

        # Fallback
        return StackFingerprint(primary_language="unknown", toolchain_variant="generic")

    def _analyze_rust(self, files: List[str]) -> StackFingerprint:
        # Check for workspace in Cargo.toml
        is_workspace = False
        try:
            with open(os.path.join(self.root_path, "Cargo.toml"), "rb") as f:
                data = tomllib.load(f)
                if "workspace" in data:
                    is_workspace = True
        except Exception:
            pass

        return StackFingerprint(
            primary_language="rust",
            toolchain_variant="cargo",
            is_monorepo=is_workspace
        )

    def _analyze_node(self, files: List[str]) -> StackFingerprint:
        frameworks = []
        is_monorepo = False

        try:
            with open(os.path.join(self.root_path, "package.json"), "r") as f:
                data = json.load(f)
                deps = data.get("dependencies", {})
                dev_deps = data.get("devDependencies", {})
                all_deps = {**deps, **dev_deps}

                # Simple framework detection
                if "react" in all_deps:
                    frameworks.append("react")
                if "next" in all_deps:
                    frameworks.append("next")
                if "express" in all_deps:
                    frameworks.append("express")
                if "vue" in all_deps:
                    frameworks.append("vue")
                if "nest" in all_deps:
                    frameworks.append("nest")

                # Monorepo check
                if "workspaces" in data:
                    is_monorepo = True
        except Exception:
            pass

        return StackFingerprint(
            primary_language="node",
            toolchain_variant="npm",
            is_monorepo=is_monorepo,
            frameworks=frameworks
        )

    def _analyze_python(self, files: List[str]) -> StackFingerprint:
        variant = "pip"
        if "pyproject.toml" in files:
            # check for poetry
            try:
                with open(os.path.join(self.root_path, "pyproject.toml"), "rb") as f:
                    data = tomllib.load(f)
                    if "tool" in data and "poetry" in data["tool"]:
                        variant = "poetry"
            except Exception:
                pass

        return StackFingerprint(
            primary_language="python",
            toolchain_variant=variant
        )
