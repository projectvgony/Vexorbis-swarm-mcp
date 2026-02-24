"""
Project Swarm v3.0 - Algorithm Workers Package

Provides advanced algorithms for concurrency control, consensus,
retrieval, and verification.
"""


from mcp_core.algorithms.hipporag_retriever import HippoRAGRetriever, ContextChunk

from mcp_core.algorithms.voting_consensus import WeightedVotingConsensus, Vote, ConsensusResult
from mcp_core.algorithms.debate_engine import DebateEngine, DebateState, Critique
from mcp_core.algorithms.z3_verifier import Z3Verifier, VerificationResult
from mcp_core.algorithms.ochiai_localizer import OchiaiLocalizer, CoverageSpectrum
from mcp_core.algorithms.git_worker import GitWorker
from mcp_core.algorithms.context_pruner import ContextPruner

# Parser infrastructure (for multi-language support)
from mcp_core.algorithms.parsers import (
    LanguageParser,
    ASTNode,
    ParserRegistry,
    PythonParser
)

__all__ = [
    "HippoRAGRetriever",
    "ContextChunk",
    "WeightedVotingConsensus",
    "Vote",
    "ConsensusResult",
    "DebateEngine",
    "DebateState",
    "Critique",
    "Z3Verifier",
    "VerificationResult",
    "OchiaiLocalizer",
    "CoverageSpectrum",
    "GitWorker",
    "ContextPruner",
    # Parser infrastructure
    "LanguageParser",
    "ASTNode",
    "ParserRegistry",
    "PythonParser",
]
