# Installation

Get Swarm up and running in minutes.

## Prerequisites

- **Docker** (recommended) or Python 3.11+
- An AI coding assistant that supports MCP:
  - Antigravity
  - Cursor
  - Claude Desktop
- API key for at least one LLM provider:
  - `GEMINI_API_KEY` (recommended)
  - `OPENAI_API_KEY` (fallback)

## Docker Installation (Recommended)

The fastest way to get started:

```bash
# Clone the repository
git clone https://github.com/projectvgony/Vexorbis.git
cd Vexorbis

# Copy env template and add your API key
cp .env.example .env

# Start the server
docker compose up -d --build
```

Verify it's running:
```bash
docker ps | grep swarm
# Should show: swarm-mcp-server
```

## Manual Installation

For development or customization:

```bash
# Clone and setup
git clone https://github.com/projectvgony/Vexorbis.git
cd Vexorbis

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install dependencies
pip install -e ".[dev]"

# Set your API key (copy from .env.example)
cp .env.example .env

# Run the server
python server.py
```

## IDE Configuration

Add Swarm to your IDE's MCP configuration.

### Antigravity

Edit `~/.antigravity/settings.json`:

```json
{
  "mcpServers": {
    "swarm-orchestrator": {
      "command": "docker",
      "args": ["exec", "-i", "swarm-mcp-server", "fastmcp", "run", "server.py"]
    }
  }
}
```

### Cursor

Edit `~/.cursor/mcp.json`:

```json
{
  "servers": {
    "swarm": {
      "command": "docker",
      "args": ["exec", "-i", "swarm-mcp-server", "fastmcp", "run", "server.py"]
    }
  }
}
```

## Verify Installation

In your IDE, try using the `search_codebase` tool:

```
Search for "authentication" in this project
```

If Swarm responds with code results, you're ready!

---

## Next Steps

- [Quick Start](./quickstart.md) — Run your first Swarm task
- [Configuration](../reference/configuration.md) — Customize Swarm's behavior
