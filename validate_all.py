import sys
import logging
from mcp_core.stack_detector import StackDetector
from mcp_core.toolchain_manager import ToolchainManager


logging.basicConfig(level=logging.INFO)


def main():
    print("🚀 Starting Project Swarm Polyglot Validation...")

    # 1. Detect Stack
    detector = StackDetector(".")
    stack = detector.detect()
    print(f"🔍 Stack: {stack.primary_language}:{stack.toolchain_variant}")
    if stack.is_monorepo:
        print("📦 Monorepo Detected")

    # 2. Load Toolchain
    toolchain = ToolchainManager(".")
    toolchain.load_or_detect(stack)

    # 3. Execute Gates
    # The gates are now abstract intents!
    gates = ["test", "lint", "mutate"]

    overall_success = True

    for gate in gates:
        print(f"\n⚡ Running Gate: {gate.upper()}")
        result = toolchain.run_intent(gate)

        if result.status == "SKIPPED":
            print("⏭️  Skipped (Not defined for this stack)")
            continue

        if result.status == "PASSED":
            print("✅ PASSED")
        else:
            print("❌ FAILED")
            print(result.message)
            overall_success = False
            # We run all gates if possible

    if overall_success:
        print("\n🎉 All Gates Passed!")
        sys.exit(0)
    else:
        print("\n🛑 Verification Failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
