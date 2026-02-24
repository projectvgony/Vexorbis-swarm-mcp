"""
Central registry for language parsers with lazy loading.

Manages parser discovery and file extension mapping.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from mcp_core.algorithms.parsers.base_parser import LanguageParser
from mcp_core.algorithms.parsers.python_parser import PythonParser

logger = logging.getLogger(__name__)


class ParserRegistry:
    """
    Registry for language parsers with lazy loading of optional parsers.
    
    Python parser is always registered (no external dependencies).
    Tree-sitter-based parsers are loaded on-demand if dependencies are installed.
    """
    
    def __init__(self):
        self._parsers: Dict[str, LanguageParser] = {}
        self._extension_map: Dict[str, str] = {}
        self._treesitter_attempted = False
        
        # Always register Python (built-in ast module)
        self.register(PythonParser())
        logger.info("Registered parser: Python (built-in)")
    
    def register(self, parser: LanguageParser) -> None:
        """
        Register a parser for its declared file extensions.
        
        Args:
            parser: Language parser instance to register
        """
        lang_name = parser.language_name
        
        for ext in parser.extensions:
            self._extension_map[ext.lower()] = lang_name
        
        self._parsers[lang_name] = parser
    
    def get_parser_for_file(self, file_path: str) -> Optional[LanguageParser]:
        """
        Get parser based on file extension.
        
        Automatically attempts to load Tree-sitter parsers on first use.
        
        Args:
            file_path: Path to source file
            
        Returns:
            LanguageParser instance if extension is supported, None otherwise
        """
        # Lazy-load Tree-sitter parsers on first request
        if not self._treesitter_attempted:
            self._try_register_treesitter_parsers()
            self._treesitter_attempted = True
        
        ext = Path(file_path).suffix.lower()
        lang = self._extension_map.get(ext)
        
        if lang is None:
            return None
        
        return self._parsers.get(lang)
    
    def supported_extensions(self) -> List[str]:
        """
        Get list of all supported file extensions.
        
        Returns:
            List of extensions with leading dot (e.g., ['.py', '.js'])
        """
        # Trigger lazy loading
        if not self._treesitter_attempted:
            self._try_register_treesitter_parsers()
            self._treesitter_attempted = True
        
        return sorted(self._extension_map.keys())
    
    def supported_languages(self) -> List[str]:
        """
        Get list of all registered language names.
        
        Returns:
            List of language names (e.g., ['Python', 'JavaScript'])
        """
        # Trigger lazy loading
        if not self._treesitter_attempted:
            self._try_register_treesitter_parsers()
            self._treesitter_attempted = True
        
        return sorted(self._parsers.keys())
    
    def register_optional_parsers(self) -> None:
        """
        Attempt to load optional Tree-sitter parsers.
        
        Silently skips parsers whose dependencies are not installed.
        """
        if self._treesitter_attempted:
            return
            
        registered = []
        
        # Try JavaScript/JSX
        try:
            from mcp_core.algorithms.parsers.javascript_parser import JavaScriptParser
            self.register(JavaScriptParser())
            registered.append("JavaScript")
        except ImportError:
            logger.debug("Tree-sitter-javascript not installed, skipping")
        
        # Try TypeScript/TSX
        try:
            from mcp_core.algorithms.parsers.typescript_parser import TypeScriptParser
            self.register(TypeScriptParser())
            registered.append("TypeScript")
        except ImportError:
            logger.debug("Tree-sitter-typescript not installed, skipping")
        
        # Try Rust
        try:
            from mcp_core.algorithms.parsers.rust_parser import RustParser
            self.register(RustParser())
            registered.append("Rust")
        except ImportError:
            logger.debug("Tree-sitter-rust not installed, skipping")
        
        # Try Go
        try:
            from mcp_core.algorithms.parsers.go_parser import GoParser
            self.register(GoParser())
            registered.append("Go")
        except ImportError:
            logger.debug("Tree-sitter-go not installed, skipping")
            
        self._treesitter_attempted = True
        
        if registered:
            logger.info(f"Multi-language support enabled: {', '.join(registered)}")
        else:
            logger.debug(
                "No optional language parsers loaded. "
                "Install tree-sitter packages for JS/TS/Rust/Go support."
            )


    def _try_register_treesitter_parsers(self) -> None:
        """Deprecated alias for register_optional_parsers."""
        self.register_optional_parsers()
