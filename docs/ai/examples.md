# Examples

Common workflows for AI agents using Project Swarm.

## Example 0: System Health & Maintenance (Internal Scope)

**Goal**: Identify why a tool is failing and optimize system performance.

1. **Check System Vitals (Internal)**
   ```python
   # Requires SWARM_INTERNAL_TOOLS=true
   check_health()
   ```

2. **Analyze Telemetry**
   ```python
   # Identifying a flaky tool from health report
   from mcp_core.telemetry.telemetry_analytics import TelemetryAnalyticsService
   analytics = TelemetryAnalyticsService()
   analytics.get_tool_success_rate("search_codebase", window_days=3)
   ```

3. **Maintenance Action**
   ```python
   # Optimize database performance
   analytics.optimize_database()
   ```

---

## Example 1: Code Discovery

**Scenario:** Find and understand authentication code

```python
# Step 1: Quick search
results = search_codebase("authentication")
# → ⚡ Auto-optimized if symbol detected
# → Returns top 5 results

# Step 2: If results incomplete, escalate
if "Few results found" in results:
    context = retrieve_context("authentication flow", top_k=15)
    # → Returns AST graph with all related code

# Step 3: Review and understand
# (Analyze returned code chunks)
```

---

## Example 2: Refactoring Workflow

**Scenario:** Refactor authentication to use async/await

```python
# Step 1: Find target code
search_codebase("auth.py")

# Step 2: Understand dependencies
retrieve_context("authentication dependencies")

# Step 3: Process refactoring task
process_task("Refactor auth.py to use async/await with proper error handling")
# → Routes to General Worker
# → Detects conflicts
# → Provides safe refactoring guidance

# Step 4: Check status
get_status()
# → Monitor task progress
```

---

## Example 3: Debugging Workflow

**Scenario:** Debug failing login test

```python
# Step 1: Locate test file
search_codebase("test_login")

# Step 2: Process debugging task
process_task("Debug test_login failure in test_auth.py - returns 401 instead of 200")
# → Routes to Ochiai SBFL
# → Runs tests with coverage
# → Identifies suspicious lines

# Step 3: Review fault localization
# (Ochiai returns ranked list of buggy lines)

# Step 4: Fix identified issues
# (Use built-in file tools to apply fixes)

# Step 5: Verify fix
# (Re-run tests)
```

---

## Example 4: Verification Workflow

**Scenario:** Verify tax calculation never returns negative

```python
# Step 1: Find function
search_codebase("calculate_tax")

# Step 2: Process verification task
process_task("Verify calculate_tax never returns negative values for any valid input")
# → Routes to Z3 Verifier
# → Generates symbolic execution guide
# → Identifies edge cases

# Step 3: Review verification results
# (Check Z3 output for counterexamples)

# Step 4: Fix edge cases if found
# (Apply fixes based on Z3 feedback)
```

---

## Example 5: Multi-File Analysis

**Scenario:** Understand database layer architecture

```python
# Step 1: Broad search
search_codebase("database models", top_k=10)

# Step 2: Deep architectural analysis
retrieve_context("database layer architecture", top_k=20)
# → Returns:
#   - Model definitions
#   - Migration files
#   - Query builders
#   - Connection managers
#   - All with call graph relationships

# Step 3: Analyze relationships
# (Review PPR scores to understand importance)
```

---

## Example 6: Performance Optimization

**Scenario:** Find and optimize slow queries

```python
# Step 1: Find query code
search_codebase("database query performance")

# Step 2: Analyze query patterns
retrieve_context("database query optimization")

# Step 3: Process optimization task
process_task("Analyze and optimize slow database queries in models.py")
# → Routes to HippoRAG for deep analysis
# → Identifies query patterns
# → Suggests optimizations
```

---

## Example 7: Error Handling Patterns

**Scenario:** Find all error handling code

```python
# Step 1: Semantic search for patterns
search_codebase("error handling patterns", top_k=15)
# → Finds try/catch, Result types, error classes

# Step 2: Understand error flow
retrieve_context("error handling architecture")
# → Maps error propagation through call graph

# Step 3: Standardize error handling
process_task("Refactor error handling to use consistent Result type pattern")
```

---

## Example 8: API Integration

**Scenario:** Add new API endpoint

```python
# Step 1: Find existing endpoints
search_codebase("API endpoints")

# Step 2: Understand routing
retrieve_context("API routing architecture")

# Step 3: Process integration task
process_task("Add new /api/users endpoint with authentication and validation")
# → Routes to General Worker
# → Ensures no conflicts with existing routes
# → Provides implementation guidance
```

---

## Example 9: Security Audit

**Scenario:** Verify authentication security

```python
# Step 1: Find auth code
search_codebase("authentication security")

# Step 2: Deep security analysis
retrieve_context("authentication and authorization flow")

# Step 3: Verify security properties
process_task("Verify authentication always validates JWT signature before granting access")
# → Routes to Z3 Verifier
# → Checks all code paths
# → Identifies security gaps
```

---

## Example 10: Code Migration

**Scenario:** Migrate from sync to async

```python
# Step 1: Find all sync code
search_codebase("synchronous database calls", top_k=20)

# Step 2: Understand dependencies
retrieve_context("database access patterns")

# Step 3: Process migration
process_task("Migrate all database calls in models.py to async/await pattern")
# → Routes to General Worker
# → Detects concurrent access issues
# → Provides safe migration path
```

---

## Pattern: Escalation Chain

```python
# Level 1: Quick keyword search
results = search_codebase("UserModel")
# → ~1ms, exact matches

# Level 2: Semantic search (if needed)
if not results:
    results = search_codebase("user data model")
    # → ~240ms, conceptual matches

# Level 3: Deep analysis (if still incomplete)
if len(results) <= 2:
    context = retrieve_context("user model architecture")
    # → ~1s, full call graph
```

---

## Pattern: Task Decomposition

```python
# Large task: Break into smaller tasks

# Don't:
process_task("Refactor entire authentication system")  # Too broad

# Do:
process_task("Refactor auth.py to use async/await")
# Wait for completion
process_task("Update auth tests for async pattern")
# Wait for completion
process_task("Migrate session handling to async")
```

---

## Pattern: Iterative Refinement

```python
# 1. Initial search
results = search_codebase("payment processing")

# 2. Refine based on results
if "stripe" in results:
    results = search_codebase("stripe payment integration")
elif "paypal" in results:
    results = search_codebase("paypal payment integration")

# 3. Deep dive
retrieve_context(f"{provider} payment flow")
```

---

## Error Recovery Examples

### Example: No Index

```python
try:
    search_codebase("UserModel")
except Exception as e:
    if "No index found" in str(e):
        # Create index first
        index_codebase()
        # Retry search
        search_codebase("UserModel")
```

### Example: Task Rejected

```python
instruction = "fix auth"

result = process_task(instruction)

if "Task Rejected" in result:
    # Make instruction more specific
    instruction = "Refactor auth.py to fix login validation error on line 45"
    result = process_task(instruction)
```

### Example: No Results

```python
results = search_codebase("NonExistentClass", keyword_only=True)

if "No exact matches" in results:
    # Try semantic search
    results = search_codebase("similar class concept")
    
    if "No results found" in results:
        # Escalate to deep analysis
        results = retrieve_context("class architecture")
```

---

## Best Practices Summary

1. **Start simple, escalate as needed**
   - search_codebase → retrieve_context

2. **Let Auto-Pilot optimize**
   - Don't manually specify keyword_only for symbols

3. **Be specific with tasks**
   - Include file names, line numbers, context

4. **Use appropriate top_k**
   - 5 for focused queries
   - 10-15 for broad exploration
   - 20+ for comprehensive analysis

5. **Check status periodically**
   - Not in tight loops
   - After task submission
   - Before next action

6. **Respect guardrails**
   - Provide specific instructions
   - Include context
   - Use clear action verbs
