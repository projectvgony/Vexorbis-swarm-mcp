# Deliberate Tool - Usage Guide

The `deliberate()` tool provides structured multi-step reasoning as an alternative to "sequential thinking".

## When to Use

✅ **Use deliberate() when**:
- Complex problems requiring multiple perspectives
- Architectural decisions with trade-offs
- Verifying complex invariants
- Need to combine insights from multiple algorithms

❌ **Don't use deliberate() when**:
- Simple queries (ask directly)
- Single-algorithm tasks (use `process_task`)
- File operations (use filesystem tools)

## Basic Usage

```python
# Simple 3-step deliberation
deliberate(
    problem="Should we refactor auth.py to use async/await?",
    steps=3
)
```

## With Context

```python
# Pass relevant code context
deliberate(
    problem="Find performance bottlenecks in the payment processor",
    context=view_file("payment.py"),
    steps=3
)
```

## With Constraints

```python
# Architectural decision with constraints
deliberate(
    problem="Choose database: PostgreSQL vs MongoDB",
    context=view_file("REQUIREMENTS.md"),
    constraints=[
        "Must support 1M users",
        "Budget: $500/month",
        "Team has SQL experience"
    ],
    steps=4
)
```

## Output Formats

### Concise Markdown (Default)
```python
result = deliberate(problem="...")
# Returns concise summary (~200 chars):
# ✅ **Deliberation Complete** (Confidence: 0.95)
# 
# **Result**: The answer is 42
# 
# *(3 steps executed using HippoRAG, Analysis. Full trace in server logs.)*
```

**Benefits**:
- ~10x less verbose than JSON
- Agent-friendly, minimal context pollution
- Full audit trail preserved in server logs

### Verbose JSON
```python
result = deliberate(problem="...", return_json=True)
# Returns full structured JSON with steps, workers, confidence
# Use for debugging or when you need programmatic access to step details
```

## Deliberation Steps

| Step | Name | Worker | Purpose |
|------|------|--------|---------|
| 1 | Decompose | HippoRAG | Break problem into sub-problems |
| 2 | Analyze | Auto-routed | Route to SBFL/Z3 based on keywords |
| 3 | Synthesize | LLM | Combine worker outputs |
| 4+ | Optional | Custom | Extended analysis |

## Real-World Examples

### Example 1: Code Verification
```python
deliberate(
    problem="Verify that calculate_tax() never returns negative values",
    context=view_file("billing.py"),
    constraints=["All tax rates are 0-100%", "Input is always >= 0"],
    steps=4
)
```

### Example 2: Architecture Review
```python
deliberate(
    problem="Analyze the consequences of switching from REST to GraphQL",
    context=view_file("ARCHITECTURE.md"),
    constraints=["No breaking changes for mobile clients"],
    steps=5
)
```

### Example 3: Debugging Assistance
```python
deliberate(
    problem="Why does the login endpoint fail intermittently?",
    context=view_file("auth.py") + "\n" + view_file("test_auth.py"),
    constraints=["Must preserve current behavior", "No external dependencies"],
    steps=3
)
```
