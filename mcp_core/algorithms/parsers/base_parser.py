"""
Abstract base classes for language parsers.

Defines the interface that all language-specific parsers must implement
to integrate with HippoRAG's knowledge graph construction.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ASTNode:
    """
    Unified AST node representation across programming languages.
    
    This abstraction allows HippoRAG to build knowledge graphs from
    different languages using a common structure.
    
    Extended for React/Next.js support:
    - renders: JSX components used (e.g., <Button />, <Layout />)
    - framework_role: Next.js pattern (page, layout, api_route, etc.)
    - metadata: Extensible dict for hooks, props, etc.
    
    Extended for API Glue (Frontend ↔ Backend):
    - api_calls: API endpoint URLs called via fetch/axios
    - api_route: Route this handler serves (backend only)
    """
    name: str
    node_type: str  # function, class, method, interface, component, etc.
    file_path: str
    start_line: int
    end_line: int
    content: str
    calls: List[str] = field(default_factory=list)       # Functions/methods this node calls
    inherits: List[str] = field(default_factory=list)    # Base classes/interfaces
    renders: List[str] = field(default_factory=list)     # JSX components rendered (React)
    framework_role: Optional[str] = None                 # Next.js role (page, layout, etc.)
    metadata: Dict[str, Any] = field(default_factory=dict)  # Extensible (hooks, props, etc.)
    api_calls: List[str] = field(default_factory=list)   # API URLs called (frontend)
    api_route: Optional[str] = None                       # Route served (backend)


class LanguageParser(ABC):
    """
    Abstract base class for language-specific parsers.
    
    Each concrete parser implementation is responsible for:
    1. Declaring which file extensions it handles
    2. Parsing source code into ASTNode objects
    3. Extracting structural relationships (calls, inheritance)
    """
    
    @property
    @abstractmethod
    def extensions(self) -> List[str]:
        """
        File extensions this parser handles.
        
        Returns:
            List of extensions with leading dot (e.g., ['.py', '.pyw'])
        """
        pass
    
    @property
    @abstractmethod
    def language_name(self) -> str:
        """
        Human-readable language name for logging and diagnostics.
        
        Returns:
            Language name (e.g., 'Python', 'JavaScript')
        """
        pass
    
    @abstractmethod
    def parse_file(self, file_path: str, source: str) -> List[ASTNode]:
        """
        Parse source code and extract AST nodes.
        
        Args:
            file_path: Path to the source file (for metadata)
            source: Source code content to parse
            
        Returns:
            List of ASTNode objects representing functions, classes, etc.
            
        Raises:
            SyntaxError: If source code cannot be parsed
        """
        pass
