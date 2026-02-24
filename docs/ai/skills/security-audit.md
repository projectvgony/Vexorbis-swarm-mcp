# Security Audit Skill

Instructions for performing security audits on code changes.

---

## When to Use This Skill

- When reviewing code for security vulnerabilities
- When `audit` keyword appears in task description
- Before merging sensitive code (auth, payments, data handling)

## Reasoning Protocol

Before auditing, use `<thinking>` tags to:
1. Identify the attack surface of changes
2. List applicable OWASP categories
3. Plan verification approach

## Tool Selection

- **Pattern Search**: Use `grep_search` for known vulnerability patterns
- **Context**: Use `view_code_item` to examine specific functions
- **Dependencies**: Check for known CVEs in requirements/package files

## Guardrails

- Do NOT approve code with unresolved security findings
- Do NOT skip OWASP checklist items
- Do NOT assume security controls exist—verify them

## OWASP Top 10 Checklist

### A01: Broken Access Control
- [ ] Authorization checks on all endpoints
- [ ] No direct object references exposed
- [ ] CORS properly configured

### A02: Cryptographic Failures
- [ ] Sensitive data encrypted at rest
- [ ] TLS for data in transit
- [ ] No hardcoded secrets

### A03: Injection
- [ ] Parameterized queries (no string concatenation)
- [ ] Input validation on all user data
- [ ] Output encoding for XSS prevention

### A04: Insecure Design
- [ ] Threat modeling completed
- [ ] Rate limiting implemented
- [ ] Fail-secure defaults

### A05: Security Misconfiguration
- [ ] Debug mode disabled in production
- [ ] Default credentials changed
- [ ] Error messages don't leak info

### A06: Vulnerable Components
- [ ] Dependencies up to date
- [ ] No known CVEs in deps
- [ ] Minimal dependency footprint

### A07: Auth Failures
- [ ] Strong password policy
- [ ] Multi-factor available
- [ ] Session timeout configured

### A08: Data Integrity
- [ ] Signed updates/downloads
- [ ] CI/CD pipeline secured
- [ ] Deployment artifacts verified

### A09: Logging Failures
- [ ] Security events logged
- [ ] Logs don't contain sensitive data
- [ ] Log injection prevented

### A10: SSRF
- [ ] URL validation on external requests
- [ ] Allowlist for external services
- [ ] No user-controlled redirects

## Code Review Patterns

### Python
```python
# BAD: SQL Injection
query = f"SELECT * FROM users WHERE id = {user_id}"

# GOOD: Parameterized
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
```

### Secrets
```python
# BAD: Hardcoded
API_KEY = "sk-abc123"

# GOOD: Environment
API_KEY = os.environ.get("API_KEY")
```

## Output Format (SARIF 2.1.0)

```json
{
  "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
  "version": "2.1.0",
  "runs": [{
    "tool": {"driver": {"name": "Swarm-Auditor"}},
    "results": [{
      "ruleId": "OWASP-A03",
      "level": "error",
      "message": {"text": "SQL injection vulnerability"},
      "locations": [{
        "physicalLocation": {
          "artifactLocation": {"uri": "src/db.py"},
          "region": {"startLine": 45}
        }
      }]
    }]
  }]
}
```
