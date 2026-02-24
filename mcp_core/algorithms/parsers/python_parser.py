"""
Python AST parser using built-in ast module.

Refactored from hipporag_retriever.py to fit the LanguageParser interface.
No external dependencies required.
"""

import ast
from typing import List
from mcp_core.algorithms.parsers.base_parser import LanguageParser, ASTNode


class PythonParser(LanguageParser):
    """
    Python AST parser using the standard library ast module.
    
    This is the default parser with no external dependencies.
    Extracts functions, classes, and their relationships.
    """
    
    @property
    def extensions(self) -> List[str]:
        return [".py", ".pyw"]
    
    @property
    def language_name(self) -> str:
        return "Python"
    
    def parse_file(self, file_path: str, source: str) -> List[ASTNode]:
        """
        Parse Python source code using ast module.
        
        Args:
            file_path: Path to Python file
            source: Python source code
            
        Returns:
            List of ASTNode objects for functions and classes
        """
        try:
            tree = ast.parse(source, filename=file_path)
        except SyntaxError:
            # Re-raise original SyntaxError to maintain line/column info for tests
            raise
        
        nodes = []
        
        # Extract top-level functions and classes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                nodes.append(self._extract_function(node, file_path, source))
            elif isinstance(node, ast.ClassDef):
                nodes.append(self._extract_class(node, file_path, source))
        
        return nodes
    
    def _extract_function(
        self, 
        node: ast.FunctionDef, 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract function definition as ASTNode"""
        # Extract function calls
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    # Handle method calls like obj.method()
                    calls.append(child.func.attr)
        
        # Extract API route from decorators (@app.get("/api/users"))
        api_route = self._extract_api_route(node)
        
        return ASTNode(
            name=node.name,
            node_type="function",
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            content=self._extract_source(source, node),
            calls=calls,
            inherits=[],
            api_route=api_route
        )
    
    def _extract_class(
        self, 
        node: ast.ClassDef, 
        file_path: str, 
        source: str
    ) -> ASTNode:
        """Extract class definition as ASTNode"""
        # Extract base classes
        inherits = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                inherits.append(base.id)
            elif isinstance(base, ast.Attribute):
                # Handle qualified names like module.BaseClass
                inherits.append(base.attr)
        
        # Extract method calls (simplified - could be expanded)
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
        
        return ASTNode(
            name=node.name,
            node_type="class",
            file_path=file_path,
            start_line=node.lineno,
            end_line=node.end_lineno or node.lineno,
            content=self._extract_source(source, node),
            calls=calls,
            inherits=inherits
        )
    
    def _extract_source(self, source: str, node: ast.AST) -> str:
        """Extract source code for AST node"""
        lines = source.splitlines()
        start = node.lineno - 1
        end = node.end_lineno if hasattr(node, 'end_lineno') else node.lineno
        
        return "\n".join(lines[start:end])
    
    def _extract_api_route(self, node: ast.FunctionDef) -> str | None:
        """
        Extract API route from decorators.
        
        Detects FastAPI/Flask patterns:
        - @app.get("/api/users")
        - @router.post("/api/comments")
        - @app.route("/api/data", methods=["POST"])
        """
        for decorator in node.decorator_list:
            route = None
            
            # Case 1: @app.get("/api/...")
            if isinstance(decorator, ast.Call):
                func = decorator.func
                
                # Check if it's app.get, router.post, etc.
                if isinstance(func, ast.Attribute):
                    method = func.attr
                    if method in ('get', 'post', 'put', 'delete', 'patch', 'route'):
                        # Extract first argument (the route string)
                        if decorator.args and isinstance(decorator.args[0], ast.Constant):
                            route = decorator.args[0].value
                            if isinstance(route, str) and route.startswith('/api'):
                                return route
        
        return None

