"""
Rust parser using Tree-sitter.

Supports Rust-specific constructs like functions, structs, impls, traits, and modules.
"""

from typing import List, TYPE_CHECKING

from mcp_core.algorithms.parsers.base_parser import ASTNode
from mcp_core.algorithms.parsers.treesitter_parser import TreeSitterParser

if TYPE_CHECKING:
    import tree_sitter


class RustParser(TreeSitterParser):
    """
    Rust parser using Tree-sitter.
    
    Extracts:
    - Function declarations
    - Struct declarations
    - Impl blocks
    - Trait declarations
    - Module declarations
    - Method definitions
    """
    
    @property
    def extensions(self) -> List[str]:
        return [".rs"]
    
    @property
    def language_name(self) -> str:
        return "Rust"
    
    @property
    def grammar_name(self) -> str:
        return "tree_sitter_rust"
    
    def _extract_nodes(
        self, 
        root_node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> List[ASTNode]:
        """Extract Rust functions, structs, impls, and traits."""
        nodes = []
        
        # Find function definitions
        for fn_node in self._find_nodes_by_type(root_node, ["function_item"]):
            node = self._extract_function(fn_node, file_path, source)
            if node:
                nodes.append(node)
        
        # Find struct definitions
        for struct_node in self._find_nodes_by_type(root_node, ["struct_item"]):
            node = self._extract_struct(struct_node, file_path, source)
            if node:
                nodes.append(node)
        
        # Find impl blocks
        for impl_node in self._find_nodes_by_type(root_node, ["impl_item"]):
            impl_nodes = self._extract_impl_block(impl_node, file_path, source)
            nodes.extend(impl_nodes)
        
        # Find trait definitions
        for trait_node in self._find_nodes_by_type(root_node, ["trait_item"]):
            node = self._extract_trait(trait_node, file_path, source)
            if node:
                nodes.append(node)
        
        # Find module declarations
        for mod_node in self._find_nodes_by_type(root_node, ["mod_item"]):
            node = self._extract_module(mod_node, file_path, source)
            if node:
                nodes.append(node)
        
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
    
    def _extract_struct(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract struct declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
        
        name = self._get_node_text(name_node, source)
        content = self._get_node_text(node, source)
        
        return ASTNode(
            name=name,
            node_type="struct",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=content,
            calls=[]
        )
    
    def _extract_impl_block(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> List[ASTNode]:
        """Extract impl block and its methods."""
        nodes = []
        
        # Get the type being implemented
        type_node = node.child_by_field_name("type")
        impl_name = self._get_node_text(type_node, source) if type_node else "UnknownImpl"
        
        # Extract methods within impl
        for method_node in self._find_nodes_by_type(node, ["function_item"]):
            method_name_node = method_node.child_by_field_name("name")
            if method_name_node:
                method_name = self._get_node_text(method_name_node, source)
                full_name = f"{impl_name}::{method_name}"
                content = self._get_node_text(method_node, source)
                calls = self._extract_calls(method_node, source)
                
                nodes.append(ASTNode(
                    name=full_name,
                    node_type="method",
                    file_path=file_path,
                    start_line=method_node.start_point[0] + 1,
                    end_line=method_node.end_point[0] + 1,
                    content=content,
                    calls=calls
                ))
        
        return nodes
    
    def _extract_trait(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract trait declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
        
        name = self._get_node_text(name_node, source)
        content = self._get_node_text(node, source)
        
        return ASTNode(
            name=name,
            node_type="trait",
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=content,
            calls=[]
        )
    
    def _extract_module(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract module declaration."""
        name_node = node.child_by_field_name("name")
        if not name_node:
            return None
        
        name = self._get_node_text(name_node, source)
        content = self._get_node_text(node, source)
        
        return ASTNode(
            name=name,
            node_type="module",
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
