"""
TypeScript/TSX parser using Tree-sitter.

Supports TypeScript, TSX, and TypeScript-specific constructs like interfaces.
"""

from typing import List, TYPE_CHECKING

from mcp_core.algorithms.parsers.base_parser import ASTNode
from mcp_core.algorithms.parsers.treesitter_parser import TreeSitterParser

if TYPE_CHECKING:
    import tree_sitter


class TypeScriptParser(TreeSitterParser):
    """
    TypeScript/TSX parser using Tree-sitter.
    
    Extracts:
    - Function declarations
    - Arrow functions
    - Class declarations
    - Interface declarations
    - Type aliases
    - Method definitions
    - Function calls
    - Inheritance (extends/implements)
    """
    
    @property
    def extensions(self) -> List[str]:
        return [".ts", ".tsx", ".mts", ".cts"]
    
    @property
    def language_name(self) -> str:
        return "TypeScript"
    
    @property
    def grammar_name(self) -> str:
        return "tree_sitter_typescript"
    
    def _extract_nodes(
        self, 
        root_node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> List[ASTNode]:
        """Extract TypeScript functions, classes, and interfaces"""
        nodes = []
        
        # Find function declarations
        for node in self._find_nodes_by_type(root_node, ['function_declaration']):
            nodes.append(self._extract_function_declaration(node, file_path, source))
        
        # Find arrow functions (those assigned to variables)
        for node in self._find_nodes_by_type(root_node, ['variable_declarator']):
            if self._is_arrow_function_assignment(node):
                nodes.append(self._extract_arrow_function(node, file_path, source))
        
        # Find class declarations
        for node in self._find_nodes_by_type(root_node, ['class_declaration']):
            nodes.append(self._extract_class_declaration(node, file_path, source))
        
        # Find interface declarations (TypeScript-specific)
        for node in self._find_nodes_by_type(root_node, ['interface_declaration']):
            nodes.append(self._extract_interface_declaration(node, file_path, source))
        
        # Find type aliases (TypeScript-specific)
        for node in self._find_nodes_by_type(root_node, ['type_alias_declaration']):
            nodes.append(self._extract_type_alias(node, file_path, source))
        
        return nodes
    
    def _extract_function_declaration(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract function declaration"""
        # Get function name
        name_node = node.child_by_field_name('name')
        name = self._get_node_text(name_node, source) if name_node else '<anonymous>'
        
        # Extract function calls
        calls = self._extract_calls(node, source)
        
        return ASTNode(
            name=name,
            node_type="function",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_text(node, source),
            calls=calls,
            inherits=[]
        )
    
    def _is_arrow_function_assignment(self, node: 'tree_sitter.Node') -> bool:
        """Check if variable_declarator contains arrow function"""
        value_node = node.child_by_field_name('value')
        return value_node is not None and value_node.type == 'arrow_function'
    
    def _extract_arrow_function(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract arrow function assigned to variable"""
        # Get variable name
        name_node = node.child_by_field_name('name')
        name = self._get_node_text(name_node, source) if name_node else '<anonymous>'
        
        # Get the arrow function node
        arrow_node = node.child_by_field_name('value')
        
        # Extract function calls
        calls = self._extract_calls(arrow_node, source)
        
        return ASTNode(
            name=name,
            node_type="function",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_text(node, source),
            calls=calls,
            inherits=[]
        )
    
    def _extract_class_declaration(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract class declaration"""
        # Get class name
        name_node = node.child_by_field_name('name')
        name = self._get_node_text(name_node, source) if name_node else '<anonymous>'
        
        # Get base class (extends) and interfaces (implements)
        inherits = []
        
        # Check for extends
        heritage = node.child_by_field_name('heritage')
        if heritage:
            for child in heritage.children:
                if child.type in ['extends_clause', 'implements_clause']:
                    # Extract type names
                    for type_node in child.children:
                        if type_node.type == 'identifier':
                            inherits.append(self._get_node_text(type_node, source))
        
        # Extract calls (from methods)
        calls = self._extract_calls(node, source)
        
        return ASTNode(
            name=name,
            node_type="class",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_text(node, source),
            calls=calls,
            inherits=inherits
        )
    
    def _extract_interface_declaration(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract interface declaration (TypeScript-specific)"""
        # Get interface name
        name_node = node.child_by_field_name('name')
        name = self._get_node_text(name_node, source) if name_node else '<anonymous>'
        
        # Get extended interfaces
        inherits = []
        heritage = node.child_by_field_name('heritage')
        if heritage:
            for child in heritage.children:
                if child.type == 'extends_clause':
                    for type_node in child.children:
                        if type_node.type == 'identifier':
                            inherits.append(self._get_node_text(type_node, source))
        
        return ASTNode(
            name=name,
            node_type="interface",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_text(node, source),
            calls=[],
            inherits=inherits
        )
    
    def _extract_type_alias(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract type alias declaration (TypeScript-specific)"""
        # Get type name
        name_node = node.child_by_field_name('name')
        name = self._get_node_text(name_node, source) if name_node else '<anonymous>'
        
        return ASTNode(
            name=name,
            node_type="type",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_text(node, source),
            calls=[],
            inherits=[]
        )
    
    def _extract_calls(self, node: 'tree_sitter.Node', source: str) -> List[str]:
        """Extract function/method calls from a node"""
        call_nodes = self._find_nodes_by_type(node, ['call_expression'])
        calls = []
        
        for call_node in call_nodes:
            func_node = call_node.child_by_field_name('function')
            if func_node:
                if func_node.type == 'identifier':
                    # Simple call: foo()
                    calls.append(self._get_node_text(func_node, source))
                elif func_node.type == 'member_expression':
                    # Method call: obj.foo()
                    property_node = func_node.child_by_field_name('property')
                    if property_node:
                        calls.append(self._get_node_text(property_node, source))
        
        return calls
