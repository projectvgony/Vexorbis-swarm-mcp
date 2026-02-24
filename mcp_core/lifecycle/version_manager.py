import re
import toml
from pathlib import Path
from typing import Literal, Tuple, Optional
import datetime

class VersionManager:
    """
    Centralized management for Project Swarm versioning.
    Handles updating pyproject.toml, schemas, and changelogs.
    """

    def __init__(self, project_root: str):
        self.root = Path(project_root)
        self.pyproject_path = self.root / "pyproject.toml"
        self.schemas_path = self.root / "mcp_core" / "swarm_schemas.py"
        self.changelog_path = self.root / "CHANGELOG.md"

    def get_current_version(self) -> str:
        """Read version from pyproject.toml."""
        if not self.pyproject_path.exists():
            raise FileNotFoundError(f"pyproject.toml not found at {self.pyproject_path}")
        
        with open(self.pyproject_path, "r", encoding="utf-8") as f:
            data = toml.load(f)
            return data["project"]["version"]

    def bump_version(self, bump_type: Literal["major", "minor", "patch"]) -> str:
        """Calculate and apply the new version string across files."""
        current_ver = self.get_current_version()
        major, minor, patch = map(int, current_ver.split("."))

        if bump_type == "major":
            major += 1
            minor = 0
            patch = 0
        elif bump_type == "minor":
            minor += 1
            patch = 0
        elif bump_type == "patch":
            patch += 1

        new_ver = f"{major}.{minor}.{patch}"
        
        # 1. Update pyproject.toml
        self._update_file(
            self.pyproject_path,
            r'version = "\d+\.\d+\.\d+"',
            f'version = "{new_ver}"'
        )

        # 2. Update swarm_schemas.py (ProjectProfile.schema_version if needed, or other constants)
        # Note: swarm_schemas.py might track its own "schema_version" separately from package version.
        # For now, we will update a module-level __version__ if it existed, or skip if strict separation is desired.
        # Based on previous file reads, swarm_schemas.py has `version: str = "2.0"` in ToolchainConfig
        # and `schema_version: str = "2.0.0"` in ProjectProfile. 
        # We generally might NOT want to bump schema versions automatically with package versions.
        # Leaving this as a placeholder/comment for now unless user explicitly asked to sync them.
        
        return new_ver

    def sync_versions(self) -> None:
        """
        Force-sync the version from pyproject.toml to all other files.
        Use this when files have drifted or after a manual update.
        """
        current_ver = self.get_current_version()
        
        # 1. Update server.py
        # Pattern: mcp = FastMCP("Swarm Orchestrator vX.Y.Z")
        server_path = self.root / "server.py"
        self._update_file(
            server_path,
            r'FastMCP\("Swarm Orchestrator v\d+\.\d+(\.\d+)?"\)',
            f'FastMCP("Swarm Orchestrator v{current_ver}")'
        )

        # 2. Update orchestrator.py
        # Pattern: app = typer.Typer(help="Swarm Orchestrator vX.Y.Z CLI")
        orch_path = self.root / "orchestrator.py"
        self._update_file(
            orch_path,
            r'help="Swarm Orchestrator v\d+\.\d+(\.\d+)? CLI"',
            f'help="Swarm Orchestrator v{current_ver} CLI"'
        )
        
        # 3. Update swarm_schemas.py
        # Universal SemVer pattern: supports "X.Y", "X.Y.Z", "X.Y.Z-beta", etc.
        schemas_path = self.root / "mcp_core" / "swarm_schemas.py"
        self._update_file(
            schemas_path,
            r'version: str = "\d+\.\d+(\.\d+)?(-[\w.]+)?"',
            f'version: str = "{current_ver}"'
        )
        # Update ProjectProfile schema_version (if we decide to sync it)
        # For now, keeping schema_version separate as it tracks data structure changes, not software version.

        print(f"[OK] Synced version {current_ver} across codebase.")

    def update_changelog(self, new_version: str) -> None:
        """
        Moves [Unreleased] changes to a new [vX.Y.Z] section.
        """
        if not self.changelog_path.exists():
            return

        with open(self.changelog_path, "r", encoding="utf-8") as f:
            content = f.read()

        today = datetime.date.today().isoformat()
        
        # Regex to find [Unreleased] header and inject the new version below it
        # Assuming format:
        # ## [Unreleased]
        # ... items ...
        #
        # ## [vOld]
        
        # We want to insert:
        # ## [Unreleased]
        #
        # ## [vNew] - YYYY-MM-DD
        
        # Strategy: Find the first "## [Unreleased]" and look for the content until the next "## ["
        # Actually, simpler: automated releases usually assume the current state of Unreleased *IS* the release.
        # So we rename [Unreleased] to [vNew] - Date, and create a new empty [Unreleased] at the top.
        
        pattern = r"## \[Unreleased\]"
        replacement = f"## [Unreleased]\n\n## [{new_version}] - {today}"
        
        if re.search(pattern, content):
            new_content = re.sub(pattern, replacement, content, count=1)
            with open(self.changelog_path, "w", encoding="utf-8") as f:
                f.write(new_content)

    def _update_file(self, path: Path, pattern: str, replacement: str) -> None:
        if not path.exists():
            return
        
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
            
        new_content = re.sub(pattern, replacement, content)
        
        if content != new_content:
            with open(path, "w", encoding="utf-8") as f:
                f.write(new_content)
