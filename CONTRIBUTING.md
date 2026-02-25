# Contributing to Vexorbis Swarm

Thank you for your interest in contributing! 🐝

## Getting Started

### Prerequisites

- Python 3.11+
- Git

### Setup

```bash
git clone https://github.com/projectvgony/Vexorbis.git
cd Vexorbis
pip install -r requirements.txt
cp .env.example .env   # Add GEMINI_API_KEY at minimum
```

## Development Workflow

### 1. Create a Branch

We use a **Dev-First Workflow**. All feature branches should generally target `dev`, not `main`.

```bash
# Fetch latest dev
git fetch origin dev

# Create feature branch from dev
git checkout -b feature/your-feature-name origin/dev
```

### 2. Make Changes

Follow the code style guidelines below.

### 3. Run Tests

**Algorithm Tests (v3.0):**
```bash
python -m pytest tests/algorithms/ -v
```

**Legacy/Search Tests:**
```bash
python -m pytest tests/test_search_engine.py -v
```

All tests must pass before submitting.

### 4. Submit PR

- Write a clear description
- Reference any related issues
- Ensure CI passes

## Code Style

### Python

- Follow PEP 8
- Use type hints
- Maximum line length: 100 characters
- Use docstrings for public functions

### Example

```python
def retrieve_context(self, query: str, top_k: int = 5) -> List[ContextChunk]:
    """
    Retrieve context using HippoRAG.
    
    Args:
        query: Natural language query
        top_k: Number of chunks to return
    
    Returns:
        List of ranked ContextChunk objects
    """
```

## Testing Strategy

Vexorbis Swarm relies heavily on specialized algorithms. When contributing:

1. **Algorithms:** Add tests to `tests/algorithms/`.
2. **Optional Deps:** Use `pytest.importorskip("lib")` for external deps like `z3` or `pycrdt`.
3. **Coverage:** We aim for 95% coverage on `mcp_core/algorithms/`.

## Areas for Contribution

- [ ] **AST Merge Strategies:** Improve OCC Validator collision handling.
- [ ] **Embedding Seeds:** Use embeddings to find seed nodes for HippoRAG (currently substring).
- [ ] **More Z3 Contracts:** Add Python decorators for formal verification.
- [ ] **Multi-Test SBFL:** Improve Ochiai to track individual test cases.

## Questions?

Open an issue or start a discussion!
