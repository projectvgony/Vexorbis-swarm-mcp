"""
Codebase profiler for auto-detecting project characteristics.

Analyzes codebase size, complexity, and languages to recommend
appropriate execution mode (lite, standard, full).
"""

import os
from pathlib import Path
from typing import Set, List
from dataclasses import dataclass


@dataclass
class CodebaseProfile:
    """
    Detected codebase characteristics.
    
    Used to recommend appropriate execution mode and skip unnecessary features.
    """
    total_files: int
    total_lines: int
    languages: Set[str]
    has_tests: bool
    complexity_score: float  # 0-1, based on depth and file count
    
    @property
    def size_category(self) -> str:
        """
        Categorize codebase size.
        
        Returns:
            "tiny", "small", "medium", or "large"
        """
        if self.total_files < 50:
            return "tiny"
        elif self.total_files < 200:
            return "small"
        elif self.total_files < 1000:
            return "medium"
        else:
            return "large"
    
    @property
    def recommended_mode(self) -> str:
        """
        Recommend execution mode based on profile.
        
        Returns:
            "lite", "standard", or "full"
        """
        # Lite mode for tiny projects
        if self.size_category == "tiny":
            return "lite"
        
        # Full mode for multi-language projects
        if len(self.languages) > 1:
            return "full"
        
        # Standard for medium Python projects
        if self.size_category in ("small", "medium"):
            return "standard"
        
        # Full for large projects
        return "full"


class CodebaseProfiler:
    """
    Analyzes codebase to determine size, complexity, and language distribution.
    """
    
    LANGUAGE_EXTENSIONS = {
        "python": [".py", ".pyw"],
        "javascript": [".js", ".mjs", ".cjs", ".jsx"],
        "typescript": [".ts", ".tsx"],
        "go": [".go"],
        "rust": [".rs"],
        "java": [".java"],
        "cpp": [".cpp", ".cc", ".cxx", ".h", ".hpp"],
        "c": [".c", ".h"],
    }
    
    EXCLUDE_PATTERNS = [
        "node_modules", "__pycache__", ".git", "dist", "build",
        ".venv", "venv", ".pytest_cache", ".mypy_cache", "htmlcov"
    ]
    
    def analyze(self, root_path: str = ".") -> CodebaseProfile:
        """
        Analyze codebase and return profile.
        
        Args:
            root_path: Root directory of codebase
            
        Returns:
            CodebaseProfile with detected characteristics
        """
        root = Path(root_path).resolve()
        
        # Collect all relevant files
        files = self._collect_files(root)
        
        # Count lines
        total_lines = self._count_lines(files)
        
        # Detect languages
        languages = self._detect_languages(files)
        
        # Check for tests
        has_tests = any("test" in str(f).lower() for f in files)
        
        # Calculate complexity score (simple heuristic)
        max_depth = self._calculate_max_depth(root, files)
        complexity_score = min(1.0, (max_depth / 10) * (len(files) / 100))
        
        return CodebaseProfile(
            total_files=len(files),
            total_lines=total_lines,
            languages=languages,
            has_tests=has_tests,
            complexity_score=complexity_score
        )
    
    def _collect_files(self, root: Path) -> List[Path]:
        """Collect all code files, excluding common ignore patterns"""
        files = []
        
        for ext_list in self.LANGUAGE_EXTENSIONS.values():
            for ext in ext_list:
                for file_path in root.rglob(f"*{ext}"):
                    # Skip excluded patterns
                    if any(excl in str(file_path) for excl in self.EXCLUDE_PATTERNS):
                        continue
                    files.append(file_path)
        
        return files
    
    def _count_lines(self, files: List[Path]) -> int:
        """Count total lines of code"""
        total = 0
        for file_path in files:
            try:
                content = file_path.read_text(encoding="utf-8", errors="ignore")
                total += len(content.splitlines())
            except Exception:
                continue
        return total
    
    def _detect_languages(self, files: List[Path]) -> Set[str]:
        """Detect programming languages in codebase"""
        languages = set()
        
        for file_path in files:
            ext = file_path.suffix.lower()
            for lang, extensions in self.LANGUAGE_EXTENSIONS.items():
                if ext in extensions:
                    languages.add(lang)
                    break
        
        return languages
    
    def _calculate_max_depth(self, root: Path, files: List[Path]) -> int:
        """Calculate maximum directory depth"""
        max_depth = 0
        
        for file_path in files:
            try:
                rel_path = file_path.relative_to(root)
                depth = len(rel_path.parts) - 1  # Subtract filename
                max_depth = max(max_depth, depth)
            except ValueError:
                continue
        
        return max_depth
    
    def get_recommendations(self, profile: CodebaseProfile) -> List[str]:
        """
        Get actionable recommendations based on profile.
        
        Returns:
            List of recommendation strings
        """
        recommendations = []
        
        if profile.recommended_mode == "lite":
            recommendations.append("Set SWARM_LITE_MODE=true for optimal performance")
            recommendations.append("Use keyword-only search (no API keys needed)")
            recommendations.append("Python-only AST analysis sufficient")
        
        elif profile.recommended_mode == "full":
            if "javascript" in profile.languages or "typescript" in profile.languages:
                recommendations.append("Install Tree-sitter for JS/TS support:")
                recommendations.append("  pip install tree-sitter tree-sitter-javascript tree-sitter-typescript")
            
            if not os.environ.get("GEMINI_API_KEY") and not os.environ.get("OPENAI_API_KEY"):
                recommendations.append("Consider adding GEMINI_API_KEY for semantic search")
        
        else:  # standard
            recommendations.append("Current setup is optimal for this codebase size")
        
        return recommendations
