# Security Policy


## Security Considerations

### API Keys

- **Never commit API keys** to version control
- Use environment variables: `GEMINI_API_KEY`, `OPENAI_API_KEY`
- Consider using a `.env` file (add to `.gitignore`)

### Automated Code Execution

Swarm v3.0 includes capabilities that execute code or commands:

- **`orchestrator.py debug` (SBFL)**: Runs the test command provided by the user (e.g., `pytest`). Ensure you trust the test suite of the project you are debugging.
- **Toolchain Manager**: Can execute build/lint commands.

**Best Practice:** Only run Swarm on projects/codebases you trust.

### File System Access


- **HippoRAG**: Reads and parses all `.py` files in the directory.
- **Swarm Cache**: Data is stored in `.swarm-cache/`.

### Docker

- The container runs as non-root by default
- Mount volumes carefully when using `-v`
- Do not expose the container to untrusted networks

## Best Practices

1. **Keep dependencies updated**: `pip install --upgrade -r requirements.txt`
2. **Review before running**: Be aware of what `debug` and `run` commands will execute.
3. **Use file permissions**: Restrict access to `.swarm-cache/`
4. **Audit API usage**: Monitor embedding/LLM API calls for unexpected activity

## Secrets Management

### Environment Variables (Development)

```bash
# .env file (add to .gitignore)
GITHUB_TOKEN=ghp_xxxx
GEMINI_API_KEY=AIzaSy...
OPENAI_API_KEY=sk-...
```

### Docker Secrets (Production)

```bash
# Create secrets
echo "your-api-key" | docker secret create gemini_api_key -

# Use in docker-compose.yml
services:
  swarm:
    secrets:
      - gemini_api_key
    environment:
      - GEMINI_API_KEY_FILE=/run/secrets/gemini_api_key
```

### External Secret Managers

For production deployments, use:
- **HashiCorp Vault**: `vault kv get secret/swarm/api-keys`
- **AWS Secrets Manager**: Integrated via IAM roles
- **Azure Key Vault**: Use managed identity

### Never Do This

- ❌ Commit secrets to git
- ❌ Pass secrets as command arguments
- ❌ Log environment variables
- ❌ Embed secrets in Docker images

## Container Security

### Image Verification

Published images are signed with Cosign:

```bash
cosign verify ghcr.io/AGENTagony/swarm:latest
```

### Security Scanning

- **Trivy**: Runs on every push to `main`
- **SBOM**: Generated for each image build
- **Dependabot**: Monitors for vulnerable dependencies

### Runtime Hardening

See [Runtime Monitoring Guide](docs/security/runtime-monitoring.md) for Falco setup.

