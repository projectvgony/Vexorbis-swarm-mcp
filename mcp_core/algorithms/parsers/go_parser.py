"""
Go parser using Tree-sitter.

Supports Go-specific constructs like functions, structs, interfaces, and methods.
"""

from typing import List, TYPE_CHECKING

from mcp_core.algorithms.parsers.base_parser import ASTNode
from mcp_core.algorithms.parsers.treesitter_parser import TreeSitterParser

if TYPE_CHECKING:
    import tree_sitter


class GoParser(TreeSitterParser):
    """
    Go parser using Tree-sitter.
    
    Extracts:
    - Function declarations
    - Method declarations
    - Struct declarations
    - Interface declarations
    - Type declarations
    """
    
    @property
    def extensions(self) -> List[str]:
        return [".go"]
    
    @property
    def language_name(self) -> str:
        return "Go"
    
    @property
    def grammar_name(self) -> str:
        return "tree_sitter_go"
    
    def _extract_nodes(
        self, 
        root_node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> List[ASTNode]:
        """Extract Go functions, structs, and interfaces."""
        nodes = []
        
        # Find function declarations
        for fn_node in self._find_nodes_by_type(root_node, ["function_declaration"]):
            node = self._extract_function(fn_node, file_path, source)
            if node:
                nodes.append(node)
        
        # Find method declarations
        for method_node in self._find_nodes_by_type(root_node, ["method_declaration"]):
            node = self._extract_method(method_node, file_path, source)
            if node:
                nodes.append(node)
        
        # Find type declarations (structs, interfaces)
        for type_node in self._find_nodes_by_type(root_node, ["type_declaration"]):
            type_nodes = self._extract_type_declaration(type_node, file_path, source)
            nodes.extend(type_nodes)
        
        return nodes
    
    def _extract_function(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract function declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
        
        name = self._get_node_text(name_node, source)
        content = self._get_node_text(node, source)
        calls = self._extract_calls(node, source)
        
        return ASTNode(
            name=name,
            node_type="function",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=content,
            calls=calls
        )
    
    def _extract_method(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract method declaration (function with receiver)."""
        name_node = node.child_by_field_name("name")
        receiver_node = node.child_by_field_name("receiver")
        
        if not name_node:
            return None
        
        method_name = self._get_node_text(name_node, source)
        
        # Get receiver type for full method name
        receiver_type = ""
        if receiver_node:
            # Find the type identifier in the receiver
            for child in receiver_node.children:
                if child.type == "type_identifier":
                    receiver_type = self._get_node_text(child, source)
                    break
                elif child.type == "pointer_type":
                    for subchild in child.children:
                        if subchild.type == "type_identifier":
                            receiver_type = "*" + self._get_node_text(subchild, source)
                            break
        
        full_name = f"{receiver_type}.{method_name}" if receiver_type else method_name
        content = self._get_node_text(node, source)
        calls = self._extract_calls(node, source)
        
        return ASTNode(
            name=full_name,
            node_type="method",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=content,
            calls=calls
        )
    
    def _extract_type_declaration(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> List[ASTNode]:
        """Extract type declarations (struct, interface, type alias)."""
        nodes = []
        
        # Look for type_spec children
        for child in node.children:
            if child.type == "type_spec":
                spec_node = self._extract_type_spec(child, file_path, source)
                if spec_node:
                    nodes.append(spec_node)
        
        return nodes
    
    def _extract_type_spec(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract a single type specification."""
        name_node = node.child_by_field_name("name")
        type_node = node.child_by_field_name("type")
        
        if not name_node:
            return None
        
        name = self._get_node_text(name_node, source)
        content = self._get_node_text(node, source)
        
        # Determine node type based on the type definition
        node_type = "type"
        if type_node:
            if type_node.type == "struct_type":
                node_type = "struct"
            elif type_node.type == "interface_type":
                node_type = "interface"
        
        return ASTNode(
            name=name,
            node_type=node_type,
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=content,
            calls=[]
        )
    
    def _extract_calls(self, node: 'tree_sitter.Node', source: str) -> List[str]:
        """Extract function/method calls from a node."""
        calls = []
        
        for call_node in self._find_nodes_by_type(node, ["call_expression"]):
            # Get the function being called
            func_node = call_node.child_by_field_name("function")
            if func_node:
                calls.append(self._get_node_text(func_node, source))
        
        return calls
