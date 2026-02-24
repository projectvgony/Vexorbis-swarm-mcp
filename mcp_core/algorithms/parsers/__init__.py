"""
Language parser plugins for HippoRAG multi-language support.

Provides abstract base classes and concrete implementations for parsing
various programming languages into unified AST representations.
"""

from mcp_core.algorithms.parsers.base_parser import (
    LanguageParser,
    ASTNode
)
from mcp_core.algorithms.parsers.parser_registry import ParserRegistry
from mcp_core.algorithms.parsers.python_parser import PythonParser

# Optional Tree-sitter parsers (only importable if dependencies installed)
try:
    from mcp_core.algorithms.parsers.javascript_parser import JavaScriptParser
    from mcp_core.algorithms.parsers.typescript_parser import TypeScriptParser
    _TREESITTER_AVAILABLE = True
except ImportError:
    _TREESITTER_AVAILABLE = False
    JavaScriptParser = None  # type: ignore
    TypeScriptParser = None  # type: ignore

__all__ = [
    "LanguageParser",
    "ASTNode",
    "ParserRegistry",
    "PythonParser",
]

if _TREESITTER_AVAILABLE:
    __all__.extend(["JavaScriptParser", "TypeScriptParser"])
