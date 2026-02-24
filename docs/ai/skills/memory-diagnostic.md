# Memory Diagnostic Skill

Routing new errors through previous knowledge to find instant solutions.

---

## When to Use This Skill

- As the VERY FIRST STEP when a command fails.
- When a tool returns an EOF, Timeout, or Permission error.

## The Diagnostic Routing

### Step 1: Query the Knowledge Base
Run the diagnostic tool with the error message you received:
```powershell
diagnose_error("connectex: No connection could be made...")
```

### Step 2: Compare Patterns
- If matching entries are found: Apply the documented "Fix" immediately. Do NOT troubleshoot from scratch.
- If NO entries are found: Proceed to standard debugging.

### Step 3: Update on Delta
If you discover a new fix or a variation:
1. Apply the fix.
2. Use `contribute_error_fix(pattern, symptom, recommendation)` to strengthen the collective memory.

## Routing Logic
- **Known Problem**: Fixed in 1 tool call.
- **New Problem**: Debug → Resolve → Contribute Fix.
