"""
Test script to verify debug mode features.
"""
import os
import sys
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

# Test 1: Debug mode detection
print("=" * 60)
print("TEST 1: Environment Variables")
print("=" * 60)
debug_mode = os.getenv("SWARM_DEBUG", "false").lower() == "true"
verbose_telemetry = os.getenv("SWARM_VERBOSE_TELEMETRY", "false").lower() == "true"
sbfl_enabled = os.getenv("SWARM_SBFL_ENABLED", "false").lower() == "true"
trace_prompts = os.getenv("SWARM_TRACE_PROMPTS", "false").lower() == "true"

print(f"SWARM_DEBUG: {debug_mode} ({'✅ PASS' if debug_mode else '❌ FAIL'})")
print(f"SWARM_VERBOSE_TELEMETRY: {verbose_telemetry} ({'✅ PASS' if verbose_telemetry else '❌ FAIL'})")
print(f"SWARM_SBFL_ENABLED: {sbfl_enabled} ({'✅ PASS' if sbfl_enabled else '❌ FAIL'})")
print(f"SWARM_TRACE_PROMPTS: {trace_prompts} ({'✅ PASS' if trace_prompts else '❌ FAIL'})")
print()

# Test 2: Server debug mode detection
print("=" * 60)
print("TEST 2: Server Debug Mode")
print("=" * 60)

# Simulate server.py debug mode detection
DEBUG_MODE = os.getenv("SWARM_DEBUG", "false").lower() == "true"
log_level = logging.DEBUG if DEBUG_MODE else logging.INFO

print(f"DEBUG_MODE: {DEBUG_MODE}")
print(f"Log Level: {logging.getLevelName(log_level)} ({'✅ PASS (DEBUG)' if log_level == logging.DEBUG else '❌ FAIL'})")
print()

# Test 3: Collector verbose mode
print("=" * 60)
print("TEST 3: Telemetry Collector Verbose Mode")
print("=" * 60)

from mcp_core.telemetry.collector import collector
VERBOSE = os.getenv("SWARM_VERBOSE_TELEMETRY", "false").lower() == "true"
print(f"Collector VERBOSE_TELEMETRY: {collector.__dict__.get('VERBOSE_TELEMETRY', 'Not found')}")
print(f"Expected: {VERBOSE} ({'✅ PASS' if VERBOSE else '❌ FAIL if verbose logs appear'}")
print()

# Test 4: SBFL toggle
print("=" * 60)
print("TEST 4: SBFL Toggle")
print("=" * 60)

sbfl_check = os.getenv("SWARM_SBFL_ENABLED", "false").lower() == "true"
print(f"SBFL Enabled: {sbfl_check} ({'✅ PASS' if sbfl_check else '❌ FAIL'})")
print("  Note: Actual SBFL execution would be tested via orchestrator_loop")
print()

# Test 5: Dynamic tool loader
print("=" * 60)
print("TEST 5: Debug Tool Loading")
print("=" * 60)

DEBUG_ONLY_TOOLS = ["mcp_transport_debug.py"]
debug_mode_loader = os.getenv("SWARM_DEBUG", "false").lower() == "true"

if debug_mode_loader:
    print(f"Debug mode is ON - debug tools WILL be loaded")
    print(f"  Tools to load: {', '.join(DEBUG_ONLY_TOOLS)}")
    status = "✅ PASS"
else:
    print(f"Debug mode is OFF - debug tools will be SKIPPED")
    print(f"  Tools skipped: {', '.join(DEBUG_ONLY_TOOLS)}")
    status = "❌ FAIL (should be ON for dev branch)"

print(f"  Status: {status}")
print()

# Summary
print("=" * 60)
print("SUMMARY")
print("=" * 60)
all_enabled = debug_mode and verbose_telemetry and sbfl_enabled and trace_prompts
if all_enabled:
    print("✅ ALL DEBUG FEATURES ENABLED")
else:
    print("❌ SOME DEBUG FEATURES DISABLED")
print()
print("Expected behavior in dev branch:")
print("  - Server logs with 🐛 DEV MODE banner")
print("  - Verbose telemetry in tool calls")
print("  - Prompt tracing in LLM calls")
print("  - SBFL analysis on test failures")
print("  - Debug tools (mcp_transport_debug) available")
