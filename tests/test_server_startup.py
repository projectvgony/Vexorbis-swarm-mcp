"""
Test server startup to verify debug banner appears.
"""
import subprocess
import time
import sys

print("=" * 60)
print("Testing Server Startup (Debug Mode)")
print("=" * 60)
print()

# Start server and capture initial output
proc = subprocess.Popen(
    [sys.executable, "server.py"],
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True,
    encoding="utf-8",
)

print("Starting server... (will capture first 5 seconds of output)")
print()

# Collect output for 5 seconds
output_lines = []
start_time = time.time()
try:
    while time.time() - start_time < 5:
        line = proc.stdout.readline()
        if line:
            output_lines.append(line.strip())
            print(line.strip())
        time.sleep(0.1)
finally:
    proc.terminate()
    proc.wait(timeout=2)

print()
print("=" * 60)
print("VERIFICATION")
print("=" * 60)

# Check for debug banner
debug_banner_found = any("DEV MODE" in line for line in output_lines)
verbose_telemetry_mentioned = any("Verbose telemetry" in line for line in output_lines)
sbfl_mentioned = any("SBFL" in line for line in output_lines)
prompt_tracing_mentioned = any("Prompt tracing" in line for line in output_lines)

print(f"✅ Debug banner found: {debug_banner_found}")
print(f"✅ Verbose telemetry mentioned: {verbose_telemetry_mentioned}")
print(f"✅ SBFL mentioned: {sbfl_mentioned}")
print(f"✅ Prompt tracing mentioned: {prompt_tracing_mentioned}")

if debug_banner_found:
    print("\n✅ SERVER STARTUP TEST PASSED - Debug mode active!")
else:
    print("\n❌ SERVER STARTUP TEST FAILED - Debug banner not found")
