# Introduction to Swarm

Swarm is a **Model Context Protocol (MCP) server** that transforms your AI coding assistant into an autonomous engineering team. Instead of relying purely on LLM reasoning, Swarm uses specialized algorithmic workers to deliver faster, more reliable results.

## What Problem Does Swarm Solve?

Traditional AI coding assistants are powerful but have limitations:

| Problem | How Swarm Solves It |
|---------|---------------------|
| LLMs guess at code structure | **HippoRAG** builds AST graphs for precise understanding |
| Debugging is trial-and-error | **Ochiai SBFL** statistically locates bugs |
| Git workflows are manual | **Git Agents** automate commits, PRs, and reviews |
| Context is lost between sessions | **Telemetry Memory** persists insights in SQLite |

## Who Is Swarm For?

- **Solo developers** who want AI assistance without babysitting
- **Teams** who need consistent, auditable AI-driven workflows
- **Organizations** requiring governance over autonomous agents

## The Three Pillars

Swarm is built on three core principles:

### 🧠 Algorithmic Core
Go beyond text search. Use AST analysis, statistical debugging, and formal verification.

### 🤖 Autonomous Workforce  
Let specialized agents handle git commits, code reviews, and issue triage.

### 🛡️ Active Governance
Stay in control with permission-first workflows and self-healing telemetry.

---

## Next Steps

- [Installation](./installation.md) — Get Swarm running in 5 minutes
- [Quick Start](./quickstart.md) — Your first task with Swarm
- [Architecture Overview](../concepts/architecture.md) — How it all fits together
