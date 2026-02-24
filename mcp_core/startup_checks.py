
"""
Startup Checks for Swarm Orchestrator.

Verifies that the environment is correctly configured (git, docker, python version)
before starting the main application loops.
"""

import sys
import shutil
import logging
import subprocess
import time
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)

# Cache for startup check results (TTL: 5 minutes)
_startup_cache: Optional[Tuple[bool, float]] = None
CACHE_TTL_SECONDS = 300

def check_command(cmd: str) -> bool:
    """Check if a command is available in the PATH."""
    return shutil.which(cmd) is not None

def check_git_version() -> Tuple[bool, str]:
    """Check Git version."""
    if not check_command("git"):
        return False, "Git not installed"
    
    try:
        result = subprocess.run(["git", "--version"], capture_output=True, text=True)
        return True, result.stdout.strip()
    except Exception as e:
        return False, f"Git check failed: {e}"

def check_docker() -> Tuple[bool, str]:
    """Check if Docker is running (or if we are inside a container)."""
    
    # 1. Check for Docker CLI (Host/DIND mode)
    if check_command("docker"):
        try:
            result = subprocess.run(["docker", "info"], capture_output=True, text=True)
            if result.returncode == 0:
                return True, "Docker available (CLI)"
        except Exception:
            pass

    # 2. Check if we are suspecting we're inside a container
    # (Common indicator: /.dockerenv file or cgroup)
    import os
    if os.path.exists("/.dockerenv"):
        # We are inside Docker, so CLI might not be needed if using mapped socket or external orchestrator
        return True, "Running inside Docker (CLI optional)"
        
    return False, "Docker CLI not found or daemon not running"

def run_startup_checks() -> bool:
    """
    Run all startup checks (cached for 5 minutes).
    Returns: True if critical checks pass, False otherwise.
    """
    global _startup_cache
    
    # Check cache
    if _startup_cache is not None:
        cached_result, cached_time = _startup_cache
        if time.time() - cached_time < CACHE_TTL_SECONDS:
            logger.debug("✅ Using cached startup check result")
            return cached_result
    
    logger.info("🔍 Running Startup Checks...")
    
    # 1. Python Version
    py_ver = sys.version.split()[0]
    logger.info(f"✅ Python: {py_ver}")
    
    # 2. Git Logic
    git_ok, git_msg = check_git_version()
    if git_ok:
        logger.info(f"✅ Git: {git_msg}")
    else:
        logger.error(f"❌ Git Critical Failure: {git_msg}")
        return False
        
    # 3. Docker (Optional but recommended)
    docker_ok, docker_msg = check_docker()
    if docker_ok:
        logger.info(f"✅ Docker: {docker_msg}")
    else:
        logger.warning(f"⚠️ Docker Warning: {docker_msg} (Containerized tools will fail)")
        
    logger.info("✅ Startup Checks Complete")
    
    # Update cache
    _startup_cache = (True, time.time())
    return True
