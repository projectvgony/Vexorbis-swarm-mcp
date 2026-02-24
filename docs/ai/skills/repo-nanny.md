# Skill: Repo Nanny 🧹

Maintain project hygiene, security, and public readiness with a multi-step check.

## Usage Heuristics
- Use when preparing for a public release/push.
- Use after large refactors to ensure no logs or secrets were leaked.
- Use to verify project documentation matches implementation.

## 5-Point Check Procedure

### 1. Secret Scanning 🔒
Run a multi-regex search for common key patterns.
- **Patterns**: `AI_KEY`, `API_KEY`, `sk-[a-zA-Z0-9]{32,}`, `TOKEN`, `SECRET`.
- **Action**: Check all files except `.gitignore` and `.env`.

### 2. Hygiene Check 🧼
Identify and remove "ghost" artifacts.
- **Logs**: `*.log`, `server.log`, `npm-debug.log`.
- **Caches**: `__pycache__/`, `.pytest_cache/`, `.swarm-cache/`.
- **Artifacts**: Local `.venv/`, `.idea/`, `.vscode/mcp.json` (if not intended for repo).
- **Glitch Folders**: Check for recursive or malformed path names (e.g., matching the root path inside itself).

### 3. Licensing & Headers ⚖️
Ensure the project is legally compliant.
- **LICENSE**: Verify the `LICENSE` file exists in the root.
- **Headers**: Check for consistent copyright headers in core source files.
- **README**: Ensure the License type is mentioned.

### 4. Gitignore Audit 🛑
Verify that sensitive files aren't being tracked.
- **Procedure**: Run `git ls-files -i --exclude-standard` to find files that *should* be ignored but are currently tracked.
- **Check**: Specifically look for `.env`, `project_profile.json.lock`, or private keys.

### 5. Documentation Parity 📚
Ensure the user-facing documentation is accurate.
- **CLI Commands**: Match `README.md` examples against current Typer/CLI definitions.
- **Architecture**: Ensure `ARCHITECTURE.md` reflects current component wiring (e.g., Gateways, Algorithmic Workers).
- **Prerequisites**: Verify `requirements.txt` includes all mandatory dependencies found in imports.

---

## Escalation Logic
If secrets are found:
1. **Rotate**: Immediately inform the user to rotate the key.
2. **Purge**: Use `git filter-repo` or similar if the secret was committed.
3. **Guard**: Add the pattern to `.gitignore` strictly.
