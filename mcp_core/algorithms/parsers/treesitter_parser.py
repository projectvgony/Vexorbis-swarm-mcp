"""
Base class for Tree-sitter based parsers.

Provides common functionality for all Tree-sitter language parsers
with lazy loading to avoid requiring dependencies when not needed.
"""

import logging
from abc import abstractmethod
from typing import List, Optional, TYPE_CHECKING

from mcp_core.algorithms.parsers.base_parser import LanguageParser, ASTNode

if TYPE_CHECKING:
    import tree_sitter

logger = logging.getLogger(__name__)


class TreeSitterParser(LanguageParser):
    """
    Base class for Tree-sitter based parsers.
    
    Handles lazy loading of Tree-sitter dependencies and provides
    common utilities for AST node extraction.
    """
    
    def __init__(self):
        self._parser: Optional['tree_sitter.Parser'] = None
        self._language: Optional['tree_sitter.Language'] = None
    
    @property
    @abstractmethod
    def grammar_name(self) -> str:
        """
        Name of the tree-sitter grammar package.
        
        Returns:
            Package name (e.g., 'tree_sitter_javascript')
        """
        pass
    
    def _ensure_parser(self) -> None:
        """
        Lazy-load Tree-sitter parser only when needed.
        
        Raises:
            ImportError: If tree-sitter or language grammar not installed
        """
        if self._parser is not None:
            return
        
        try:
            import tree_sitter
        except ImportError as e:
            raise ImportError(
                f"Tree-sitter support requires optional dependencies. "
                f"Install with: pip install tree-sitter {self.grammar_name.replace('_', '-')}"
            ) from e
        
        try:
            # Dynamically import the language grammar
            grammar_module = __import__(self.grammar_name)
            self._language = tree_sitter.Language(grammar_module.language())
            self._parser = tree_sitter.Parser(self._language)
            logger.debug(f"Loaded Tree-sitter grammar: {self.language_name}")
        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Failed to load {self.grammar_name}. "
                f"Install with: pip install {self.grammar_name.replace('_', '-')}"
            ) from e
    
    def parse_file(self, file_path: str, source: str) -> List[ASTNode]:
        """
        Parse source code using Tree-sitter.
        
        Args:
            file_path: Path to source file
            source: Source code content
            
        Returns:
            List of extracted ASTNode objects
        """
        self._ensure_parser()
        
        # Parse source into tree
        tree = self._parser.parse(source.encode('utf-8'))
        
        # Extract nodes using language-specific logic
        return self._extract_nodes(tree.root_node, file_path, source)
    
    @abstractmethod
    def _extract_nodes(
        self, 
        root_node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> List[ASTNode]:
        """
        Extract AST nodes from Tree-sitter parse tree.
        
        Args:
            root_node: Root of Tree-sitter parse tree
            file_path: Path to source file for metadata
            source: Original source code for content extraction
            
        Returns:
            List of ASTNode objects
        """
        pass
    
    def _get_node_text(self, node: 'tree_sitter.Node', source: str) -> str:
        """
        Extract source text for a Tree-sitter node.
        
        Args:
            node: Tree-sitter node
            source: Original source code
            
        Returns:
            Source code text for this node
        """
        return source[node.start_byte:node.end_byte]
    
    def _find_nodes_by_type(
        self, 
        root: 'tree_sitter.Node', 
        node_types: List[str]
    ) -> List['tree_sitter.Node']:
        """
        Recursively find all nodes of specified types.
        
        Args:
            root: Starting node
            node_types: List of node type names to find
            
        Returns:
            List of matching nodes
        """
        results = []
        
        def walk(node):
            if node.type in node_types:
                results.append(node)
            for child in node.children:
                walk(child)
        
        walk(root)
        return results
