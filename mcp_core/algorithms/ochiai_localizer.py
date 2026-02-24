"""
Ochiai Localizer - Spectrum-Based Fault Localization

Implements SBFL from v3.0 spec Section 7.4
for automated bug location using test coverage.
"""

import logging
import subprocess
import json
import math
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass
from collections import defaultdict

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
    logging.warning(
        "coverage not installed. SBFL functionality disabled. "
        "Install with: pip install coverage>=7.0"
    )

logger = logging.getLogger(__name__)


@dataclass
class CoverageSpectrum:
    """Coverage data for passing and failing tests"""
    passed_tests: Dict[str, Set[int]]  # {file: set of lines}
    failed_tests: Dict[str, Set[int]]
    total_passed: int
    total_failed: int


class OchiaiLocalizer:
    """
    Spectrum-Based Fault Localization for automated bug location.
    
    Uses the Ochiai algorithm to rank lines by suspiciousness:
    S(l) = failed(l) / sqrt(total_failed * (failed(l) + passed(l)))
    """
    
    def __init__(self):
        """Initialize SBFL localizer"""
        if not COVERAGE_AVAILABLE:
            raise ImportError(
                "coverage is required for SBFL. "
                "Install with: pip install coverage"
            )
    
    def collect_coverage(
        self,
        test_command: str,
        source_path: str,
        cwd: Optional[str] = None
    ) -> CoverageSpectrum:
        """
        Run tests with coverage to get pass/fail per line.
        
        Args:
            test_command: Command to run tests (e.g., "pytest tests/")
            source_path: Path to source code directory
            cwd: Working directory for command
            
        Returns:
            CoverageSpectrum with pass/fail data
        """
        cwd = cwd or "."
        
        # Run tests with coverage
        logger.info(f"Running tests with coverage: {test_command}")
        
        # Use coverage.py programmatically
        cov = coverage.Coverage(source=[source_path])
        cov.start()
        
        try:
            # Run test command
            result = subprocess.run(
                test_command,
                shell=True,
                cwd=cwd,
                capture_output=True,
                text=True
            )
            
            test_passed = (result.returncode == 0)
            
        finally:
            cov.stop()
            cov.save()
        
        # Extract coverage data
        passed_coverage = defaultdict(set)
        failed_coverage = defaultdict(set)
        
        # Get line-level coverage
        analysis = cov.analysis2()
        
        for file_path, executed, excluded, missing in analysis:
            covered_lines = set(executed)
            
            if test_passed:
                passed_coverage[file_path] = covered_lines
            else:
                failed_coverage[file_path] = covered_lines
        
        # In practice, this would run individual tests and track each
        # For simplicity, we're treating entire suite as one test
        
        total_passed = 1 if test_passed else 0
        total_failed = 0 if test_passed else 1
        
        logger.info(
            f"Coverage collection complete: "
            f"{total_passed} passed, {total_failed} failed"
        )
        
        return CoverageSpectrum(
            passed_tests=dict(passed_coverage),
            failed_tests=dict(failed_coverage),
            total_passed=total_passed,
            total_failed=total_failed
        )
    
    def calculate_suspiciousness(
        self,
        spectrum: CoverageSpectrum
    ) -> Dict[Tuple[str, int], float]:
        """
        Calculate Ochiai suspiciousness score for each line.
        
        Ochiai formula:
        S(l) = failed(l) / sqrt(total_failed * (failed(l) + passed(l)))
        
        Args:
            spectrum: Coverage spectrum from tests
            
        Returns:
            Dict mapping (file, line) to suspiciousness score (0.0-1.0)
        """
        suspiciousness = {}
        
        # Get all files
        all_files = set(spectrum.passed_tests.keys()) | set(spectrum.failed_tests.keys())
        
        for file_path in all_files:
            passed_lines = spectrum.passed_tests.get(file_path, set())
            failed_lines = spectrum.failed_tests.get(file_path, set())
            
            all_lines = passed_lines | failed_lines
            
            for line_num in all_lines:
                # Count how many passing/failing tests covered this line
                failed_count = 1 if line_num in failed_lines else 0
                passed_count = 1 if line_num in passed_lines else 0
                
                if failed_count == 0:
                    # Line not executed in any failing test
                    score = 0.0
                else:
                    # Ochiai formula
                    total_failed = spectrum.total_failed
                    denominator = math.sqrt(
                        total_failed * (failed_count + passed_count)
                    )
                    
                    if denominator == 0:
                        score = 0.0
                    else:
                        score = failed_count / denominator
                
                suspiciousness[(file_path, line_num)] = score
        
        logger.info(f"Calculated suspiciousness for {len(suspiciousness)} lines")
        
        return suspiciousness
    
    def get_top_suspicious_lines(
        self,
        suspiciousness: Dict[Tuple[str, int], float],
        top_k: int = 10
    ) -> List[Tuple[str, int, float]]:
        """
        Get most suspicious lines ranked by score.
        
        Args:
            suspiciousness: Dict from calculate_suspiciousness
            top_k: Number of lines to return
            
        Returns:
            List of (file, line, score) tuples
        """
        ranked = sorted(
            suspiciousness.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_k]
        
        return [(file, line, score) for (file, line), score in ranked]
    
    def generate_debug_prompt(
        self,
        suspicious_lines: List[Tuple[str, int, float]],
        source_snippets: Optional[Dict[Tuple[str, int], str]] = None
    ) -> str:
        """
        Create targeted debugging prompt for LLM agent.
        
        Args:
            suspicious_lines: List from get_top_suspicious_lines
            source_snippets: Optional dict of {(file, line): code_snippet}
            
        Returns:
            Formatted prompt for agent
        """
        if not suspicious_lines:
            return "No suspicious lines identified."
        
        prompt = "🐛 **Automated Fault Localization Results**\n\n"
        prompt += "The tests failed. The Ochiai algorithm identified the following lines as most suspicious:\n\n"
        
        for i, (file_path, line_num, score) in enumerate(suspicious_lines, 1):
            prompt += f"{i}. **{Path(file_path).name}:L{line_num}** "
            prompt += f"(Suspiciousness: {score:.2f})\n"
            
            if source_snippets and (file_path, line_num) in source_snippets:
                snippet = source_snippets[(file_path, line_num)]
                prompt += f"   ```python\n   {snippet}\n   ```\n"
        
        prompt += "\n**Action Required:**\n"
        prompt += "Analyze these high-suspicion lines first. "
        prompt += "The bug is likely in one of these locations.\n"
        
        return prompt
    
    def run_full_sbfl_analysis(
        self,
        test_command: str,
        source_path: str,
        top_k: int = 5
    ) -> str:
        """
        Complete SBFL pipeline: collect, analyze, generate prompt.
        
        Args:
            test_command: Command to run tests
            source_path: Path to source code
            top_k: Number of suspicious lines to report
            
        Returns:
            Debug prompt for agent
        """
        # Step 1: Collect coverage
        spectrum = self.collect_coverage(test_command, source_path)
        
        if spectrum.total_failed == 0:
            return "All tests passed. No fault localization needed."
        
        # Step 2: Calculate suspiciousness
        suspiciousness = self.calculate_suspiciousness(spectrum)
        
        # Step 3: Get top suspects
        top_lines = self.get_top_suspicious_lines(suspiciousness, top_k)
        
        # Step 4: Generate prompt
        prompt = self.generate_debug_prompt(top_lines)
        
        logger.info(f"SBFL analysis complete: {len(top_lines)} suspects identified")
        
        return prompt
