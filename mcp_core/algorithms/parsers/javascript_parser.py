"""
JavaScript/JSX parser using Tree-sitter.

Supports JavaScript (ES6+), JSX, and modern JS features.
"""

from typing import List, TYPE_CHECKING

from mcp_core.algorithms.parsers.base_parser import ASTNode
from mcp_core.algorithms.parsers.treesitter_parser import TreeSitterParser

if TYPE_CHECKING:
    import tree_sitter


class JavaScriptParser(TreeSitterParser):
    """
    JavaScript/JSX parser using Tree-sitter.
    
    Extracts:
    - Function declarations
    - Arrow functions
    - Class declarations
    - Method definitions
    - Function calls
    - Import/export relationships
    
    React/Next.js Support:
    - React Component detection (uppercase + returns JSX)
    - JSX component rendering relationships
    - Next.js file-based routing patterns
    - React Hooks usage
    """
    
    @property
    def extensions(self) -> List[str]:
        return [".js", ".jsx", ".mjs", ".cjs"]
    
    @property
    def language_name(self) -> str:
        return "JavaScript"
    
    @property
    def grammar_name(self) -> str:
        return "tree_sitter_javascript"
    
    def _extract_nodes(
        self, 
        root_node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> List[ASTNode]:
        """Extract JavaScript functions and classes"""
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
        
        return nodes
    
    def _extract_function_declaration(
        self, 
        node: 'tree_sitter.Node', 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract function declaration with React component detection"""
        # Get function name
        name_node = node.child_by_field_name('name')
        name = self._get_node_text(name_node, source) if name_node else '<anonymous>'
        
        # Extract function calls
        calls = self._extract_calls(node, source)
        
        # Check if this is a React component
        is_component = self._is_react_component(node, name, source)
        node_type = "component" if is_component else "function"
        
        # Extract React-specific data
        renders = self._extract_jsx_components(node, source) if is_component else []
        hooks = self._extract_hooks_used(node, source) if is_component else []
        framework_role = self._detect_nextjs_role(file_path)
        
        # Extract API calls (fetch/axios)
        api_calls = self._extract_api_calls(node, source)
        
        metadata = {}
        if hooks:
            metadata['hooks'] = hooks
        
        return ASTNode(
            name=name,
            node_type=node_type,
            file_path=file_path,
            start_line=node.start_point[0] + 1,  # Tree-sitter uses 0-indexed lines
            end_line=node.end_point[0] + 1,
            content=self._get_node_text(node, source),
            calls=calls,
            inherits=[],
            renders=renders,
            framework_role=framework_role,
            metadata=metadata,
            api_calls=api_calls
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
        """Extract arrow function assigned to variable with React detection"""
        # Get variable name
        name_node = node.child_by_field_name('name')
        name = self._get_node_text(name_node, source) if name_node else '<anonymous>'
        
        # Get the arrow function node
        arrow_node = node.child_by_field_name('value')
        
        # Extract function calls
        calls = self._extract_calls(arrow_node, source)
        
        # Check if this is a React component
        is_component = self._is_react_component(arrow_node, name, source)
        node_type = "component" if is_component else "function"
        
        # Extract React-specific data
        renders = self._extract_jsx_components(arrow_node, source) if is_component else []
        hooks = self._extract_hooks_used(arrow_node, source) if is_component else []
        framework_role = self._detect_nextjs_role(file_path)
        
        # Extract API calls (fetch/axios)
        api_calls = self._extract_api_calls(arrow_node, source)
        
        metadata = {}
        if hooks:
            metadata['hooks'] = hooks
        
        return ASTNode(
            name=name,
            node_type=node_type,
            file_path=file_path,
            start_line=node.start_point[0] + 1,
            end_line=node.end_point[0] + 1,
            content=self._get_node_text(node, source),
            calls=calls,
            inherits=[],
            renders=renders,
            framework_role=framework_role,
            metadata=metadata,
            api_calls=api_calls
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
        
        # Get base class (extends)
        inherits = []
        heritage = node.child_by_field_name('heritage')
        if heritage:
            for child in heritage.children:
                if child.type == 'identifier':
                    inherits.append(self._get_node_text(child, source))
        
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
    
    def _is_react_component(self, node: 'tree_sitter.Node', name: str, source: str) -> bool:
        """
        Check if function is a React component.
        
        Heuristic:
        - Name starts with uppercase letter (React convention)
        - Contains JSX elements in body
        """
        # Check 1: Uppercase first letter
        if not name or name == '<anonymous>' or not name[0].isupper():
            return False
        
        # Check 2: Contains JSX elements
        jsx_nodes = self._find_nodes_by_type(node, ['jsx_element', 'jsx_self_closing_element'])
        return len(jsx_nodes) > 0
    
    def _extract_jsx_components(self, node: 'tree_sitter.Node', source: str) -> List[str]:
        """
        Extract component names used in JSX.
        
        Returns list of uppercase component names (ignores lowercase HTML tags).
        """
        components = []
        
        # Find JSX opening tags and self-closing tags
        jsx_elements = self._find_nodes_by_type(node, [
            'jsx_opening_element',
            'jsx_self_closing_element'
        ])
        
        for jsx_node in jsx_elements:
            name_node = jsx_node.child_by_field_name('name')
            if name_node:
                comp_name = self._get_node_text(name_node, source)
                # Only track uppercase (components, not HTML tags like <div>)
                if comp_name and comp_name[0].isupper():
                    components.append(comp_name)
        
        return list(set(components))  # Remove duplicates
    
    def _detect_nextjs_role(self, file_path: str) -> str | None:
        """
        Detect Next.js framework role from file path.
        
        Returns:
            - 'next_page' - Pages Router page
            - 'next_layout' - App Router layout
            - 'next_app_route' - App Router page
            - 'next_api_route' - Pages Router API route
            - 'next_api_handler' - App Router API route handler
            - 'next_app' - _app.tsx
            - 'next_document' - _document.tsx
            - None - Not a Next.js special file
        """
        from pathlib import Path
        path = Path(file_path)
        path_str = str(path).replace('\\', '/')
        
        # Pages Router
        if 'pages/' in path_str or '/pages/' in path_str:
            if path.name == '_app.tsx' or path.name == '_app.jsx':
                return 'next_app'
            elif path.name == '_document.tsx' or path.name == '_document.jsx':
                return 'next_document'
            elif 'api/' in path_str or '/api/' in path_str:
                return 'next_api_route'
            else:
                return 'next_page'
        
        # App Router (Next.js 13+)
        if 'app/' in path_str or '/app/' in path_str:
            if path.name in ['layout.tsx', 'layout.jsx']:
                return 'next_layout'
            elif path.name in ['page.tsx', 'page.jsx']:
                return 'next_app_route'
            elif path.name in ['route.ts', 'route.js']:
                return 'next_api_handler'
        
        return None
    
    def _extract_hooks_used(self, node: 'tree_sitter.Node', source: str) -> List[str]:
        """
        Extract React hooks used in component.
        
        Detects calls like useState, useEffect, useCustomHook (starts with 'use').
        """
        hooks = []
        
        for call_node in self._find_nodes_by_type(node, ['call_expression']):
            func_node = call_node.child_by_field_name('function')
            if func_node and func_node.type == 'identifier':
                name = self._get_node_text(func_node, source)
                # Hooks start with 'use' and have uppercase after
                if name and name.startswith('use') and len(name) > 3 and name[3].isupper():
                    hooks.append(name)
        
        return list(set(hooks))  # Remove duplicates
    
    def _extract_api_calls(self, node: 'tree_sitter.Node', source: str) -> List[str]:
        """
        Extract API endpoint URLs from fetch() and axios calls.
        
        Detects:
        - fetch('/api/users')
        - fetch(`/api/users/${id}`)
        - axios.get('/api/comments')
        - axios.post('/api/data', {...})
        """
        api_urls = []
        
        for call_node in self._find_nodes_by_type(node, ['call_expression']):
            func_node = call_node.child_by_field_name('function')
            if not func_node:
                continue
            
            # Case 1: fetch('/api/...')
            if func_node.type == 'identifier':
                func_name = self._get_node_text(func_node, source)
                if func_name == 'fetch':
                    url = self._extract_first_string_arg(call_node, source)
                    if url and url.startswith('/api'):
                        api_urls.append(url)
            
            # Case 2: axios.get('/api/...'), axios.post(...), etc.
            elif func_node.type == 'member_expression':
                obj_node = func_node.child_by_field_name('object')
                method_node = func_node.child_by_field_name('property')
                
                if obj_node and method_node:
                    obj_name = self._get_node_text(obj_node, source)
                    method_name = self._get_node_text(method_node, source)
                    
                    if obj_name == 'axios' and method_name in ('get', 'post', 'put', 'delete', 'patch'):
                        url = self._extract_first_string_arg(call_node, source)
                        if url and url.startswith('/api'):
                            api_urls.append(url)
        
        return list(set(api_urls))  # Remove duplicates
    
    def _extract_first_string_arg(self, call_node: 'tree_sitter.Node', source: str) -> str | None:
        """Extract the first string argument from a call expression"""
        args_node = call_node.child_by_field_name('arguments')
        if not args_node:
            return None
        
        for child in args_node.children:
            # String literal: '/api/users'
            if child.type == 'string':
                text = self._get_node_text(child, source)
                # Remove quotes
                return text.strip('"').strip("'")
            
            # Template literal: `/api/users/${id}`
            elif child.type == 'template_string':
                text = self._get_node_text(child, source)
                # Extract static prefix from template
                # `/api/users/${id}` → /api/users
                import re
                match = re.match(r'`([^${}]+)', text)
                if match:
                    return match.group(1)
        
        return None

