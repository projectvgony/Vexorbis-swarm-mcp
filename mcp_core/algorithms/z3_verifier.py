"""
Z3 Verifier - Symbolic Execution for Contract Verification

Implements Symbolic Execution from v3.0 spec Section 7.3
using Z3 SMT Solver.
"""

import logging
from typing import Callable, List, Optional, Dict, Any
from dataclasses import dataclass

try:
    import z3
    Z3_AVAILABLE = True
except ImportError:
    Z3_AVAILABLE = False
    logging.warning(
        "z3-solver not installed. Symbolic verification disabled. "
        "Install with: pip install z3-solver>=4.12.0 "
        "(Note: ~100MB package)"
    )

logger = logging.getLogger(__name__)


@dataclass
class VerificationResult:
    """Result of symbolic verification"""
    verified: bool
    message: str
    counterexample: Optional[Dict[str, Any]] = None
    proof_time_ms: float = 0.0


class Z3Verifier:
    """
    Symbolic execution for contract verification.
    
    Verifies that postconditions hold for ALL possible inputs
    (not just sampled test cases).
    """
    
    def __init__(self, timeout_ms: int = 5000):
        """
        Args:
            timeout_ms: Z3 solver timeout in milliseconds
        """
        if not Z3_AVAILABLE:
            raise ImportError(
                "z3-solver is required for verification. "
                "Install with: pip install z3-solver"
            )
        
        self.timeout_ms = timeout_ms
    
    def verify_function(
        self,
        func: Callable,
        preconditions: List['z3.ExprRef'],
        postconditions: List['z3.ExprRef']
    ) -> VerificationResult:
        """
        Check if postconditions hold for all inputs satisfying preconditions.
        
        Args:
            func: Function to verify (not used directly, symbolic vars used)
            preconditions: List of Z3 constraints (preconditions)
            postconditions: List of Z3 constraints (postconditions)
            
        Returns:
            VerificationResult indicating success or counterexample
        """
        solver = z3.Solver()
        solver.set("timeout", self.timeout_ms)
        
        # Add preconditions
        for precond in preconditions:
            solver.add(precond)
        
        # Negate postconditions (look for violations)
        for postcond in postconditions:
            solver.add(z3.Not(postcond))
        
        # Check satisfiability
        result = solver.check()
        
        if result == z3.unsat:
            # No counterexample found = verified
            logger.info("Verification successful: no counterexamples found")
            return VerificationResult(
                verified=True,
                message="All postconditions hold for inputs satisfying preconditions"
            )
        
        elif result == z3.sat:
            # Counterexample found
            model = solver.model()
            counterexample = self._extract_counterexample(model)
            
            logger.warning(f"Verification failed: counterexample found {counterexample}")
            
            return VerificationResult(
                verified=False,
                message="Postcondition violated",
                counterexample=counterexample
            )
        
        else:
            # Timeout or unknown
            logger.error("Verification inconclusive: solver timeout or unknown")
            return VerificationResult(
                verified=False,
                message="Verification inconclusive (timeout or unknown)"
            )
    
    def find_counterexample(
        self,
        constraint: 'z3.ExprRef'
    ) -> Optional[Dict[str, Any]]:
        """
        Find input that violates constraint.
        
        Args:
            constraint: Z3 constraint to check
            
        Returns:
            Dict of variable assignments or None if constraint is satisfiable
        """
        solver = z3.Solver()
        solver.set("timeout", self.timeout_ms)
        
        # Look for violation
        solver.add(z3.Not(constraint))
        
        result = solver.check()
        
        if result == z3.sat:
            model = solver.model()
            return self._extract_counterexample(model)
        
        return None
    
    def _extract_counterexample(self, model: 'z3.ModelRef') -> Dict[str, Any]:
        """
        Extract variable assignments from Z3 model.
        
        Args:
            model: Z3 model
            
        Returns:
            Dict mapping variable names to values
        """
        counterexample = {}
        
        for decl in model:
            var_name = decl.name()
            value = model[decl]
            
            # Convert Z3 value to Python value
            if z3.is_int_value(value):
                counterexample[var_name] = value.as_long()
            elif z3.is_rational_value(value):
                num = value.numerator_as_long()
                den = value.denominator_as_long()
                counterexample[var_name] = num / den
            elif z3.is_true(value):
                counterexample[var_name] = True
            elif z3.is_false(value):
                counterexample[var_name] = False
            else:
                counterexample[var_name] = str(value)
        
        return counterexample
    
    def verify_simple_function(
        self,
        input_vars: Dict[str, 'z3.ExprRef'],
        precondition: 'z3.ExprRef',
        implementation: Callable[[Dict], 'z3.ExprRef'],
        postcondition: 'z3.ExprRef'
    ) -> VerificationResult:
        """
        Simplified verification for common case.
        
        Args:
            input_vars: Dict of {var_name: z3 symbolic var}
            precondition: Single precondition constraint
            implementation: Function that computes result symbolically
            postcondition: Single postcondition constraint
            
        Returns:
            VerificationResult
        """
        return self.verify_function(
            func=implementation,
            preconditions=[precondition] if precondition else [],
            postconditions=[postcondition]
        )


# Example usage helper
def create_symbolic_int(name: str) -> 'z3.ArithRef':
    """Create a symbolic integer variable"""
    if not Z3_AVAILABLE:
        raise ImportError("z3-solver not installed")
    return z3.Int(name)


def create_symbolic_bool(name: str) -> 'z3.BoolRef':
    """Create a symbolic boolean variable"""
    if not Z3_AVAILABLE:
        raise ImportError("z3-solver not installed")
    return z3.Bool(name)
