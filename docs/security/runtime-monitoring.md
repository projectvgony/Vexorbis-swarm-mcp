# Runtime Security Monitoring

This document outlines recommended runtime security monitoring for production Swarm deployments.

## Falco (Recommended)

[Falco](https://falco.org/) is the runtime security standard for detecting anomalous behavior in containers.

### Installation (Kubernetes)

```bash
helm repo add falcosecurity https://falcosecurity.github.io/charts
helm install falco falcosecurity/falco \
  --namespace falco --create-namespace \
  --set tty=true
```

### Custom Rules for Swarm

```yaml
# swarm-falco-rules.yaml
- rule: Swarm Unexpected Network Connection
  desc: Detect unexpected outbound connections from swarm container
  condition: >
    container.name = "swarm-mcp-server" and
    evt.type in (connect) and
    fd.net != "127.0.0.0/8" and
    fd.sport != 8000 and
    fd.sport != 5432
  output: "Unexpected network connection from Swarm (connection=%fd.name)"
  priority: WARNING
```

## Docker Security Scanning

For non-Kubernetes deployments:

```bash
# Scan running containers
docker scan swarm-mcp:latest

# Enable content trust
export DOCKER_CONTENT_TRUST=1
```

## Monitoring Checklist

- [ ] Enable container logging to centralized system
- [ ] Monitor for privilege escalation attempts
- [ ] Alert on unexpected process execution
- [ ] Track network connections to/from container
- [ ] Monitor file system changes in `/app`
