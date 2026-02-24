"""
Weighted Voting Consensus - Multi-Agent Decision Making

Implements Weighted Majority Voting from v3.0 spec Section 3.2
with Elo reputation tracking.
"""

import logging
from typing import List, Dict, Optional
from dataclasses import dataclass, field
from collections import defaultdict
import math

logger = logging.getLogger(__name__)


@dataclass
class Vote:
    """A single agent vote with confidence weight"""
    agent_id: str
    decision: str
    confidence: float  # 0.0 to 1.0
    domain: str = "general"


@dataclass
class ConsensusResult:
    """Result of consensus computation"""
    decision: str
    total_weight: float
    vote_distribution: Dict[str, float] = field(default_factory=dict)
    winning_margin: float = 0.0


class WeightedVotingConsensus:
    """
    Aggregate agent votes with confidence-based weights.
    
    Implements weighted majority voting with dynamic Elo ratings
    to adaptively weight agents based on historical accuracy.
    """
    
    def __init__(self, k_factor: float = 32.0, initial_rating: float = 1500.0):
        """
        Args:
            k_factor: Elo K-factor (higher = faster rating changes)
            initial_rating: Starting Elo rating for new agents
        """
        self.k_factor = k_factor
        self.initial_rating = initial_rating
        
        # Domain-specific Elo ratings per agent
        # Format: {agent_id: {domain: rating}}
        self.ratings: Dict[str, Dict[str, float]] = defaultdict(
            lambda: defaultdict(lambda: initial_rating)
        )
        
        # Vote history for provenance
        self.vote_history: List[Vote] = []
    
    def register_vote(
        self,
        agent_id: str,
        decision: str,
        confidence: float,
        domain: str = "general"
    ) -> None:
        """
        Record a vote with weight = confidence.
        
        Args:
            agent_id: Unique agent identifier
            decision: The decision being voted for
            confidence: Agent's confidence (0.0-1.0)
            domain: Task domain for Elo tracking
        """
        if not (0.0 <= confidence <= 1.0):
            raise ValueError(f"Confidence must be in [0, 1], got {confidence}")
        
        vote = Vote(
            agent_id=agent_id,
            decision=decision,
            confidence=confidence,
            domain=domain
        )
        
        self.vote_history.append(vote)
        logger.debug(
            f"Vote registered: {agent_id} → {decision} "
            f"(confidence={confidence:.2f}, domain={domain})"
        )
    
    def compute_decision(
        self,
        votes: Optional[List[Vote]] = None,
        use_elo: bool = True
    ) -> ConsensusResult:
        """
        Compute winning decision using weighted majority voting.
        
        Formula: D = argmax_k Σ(w_i · I(v_i = k))
        where w_i = confidence_i * (elo_i / 1500) if use_elo else confidence_i
        
        Args:
            votes: List of votes to aggregate (defaults to all registered)
            use_elo: Whether to multiply confidence by normalized Elo
            
        Returns:
            ConsensusResult with winning decision
        """
        if votes is None:
            votes = self.vote_history
        
        if not votes:
            raise ValueError("No votes to aggregate")
        
        # Aggregate weighted votes
        weighted_votes: Dict[str, float] = defaultdict(float)
        
        for vote in votes:
            weight = vote.confidence
            
            if use_elo:
                # Normalize Elo rating (1500 = neutral weight of 1.0)
                elo_rating = self.ratings[vote.agent_id][vote.domain]
                elo_multiplier = elo_rating / self.initial_rating
                weight *= elo_multiplier
            
            weighted_votes[vote.decision] += weight
        
        # Find decision with max weight
        if not weighted_votes:
            raise ValueError("All votes had zero weight")
        
        winner = max(weighted_votes.items(), key=lambda x: x[1])
        decision, total_weight = winner
        
        # Calculate winning margin
        sorted_weights = sorted(weighted_votes.values(), reverse=True)
        margin = sorted_weights[0] - sorted_weights[1] if len(sorted_weights) > 1 else sorted_weights[0]
        
        logger.info(
            f"Consensus: {decision} (weight={total_weight:.2f}, margin={margin:.2f})"
        )
        
        return ConsensusResult(
            decision=decision,
            total_weight=total_weight,
            vote_distribution=dict(weighted_votes),
            winning_margin=margin
        )
    
    def update_elo_rating(
        self,
        agent_id: str,
        was_correct: bool,
        domain: str = "general",
        opponent_rating: Optional[float] = None
    ) -> float:
        """
        Update agent's Elo rating based on outcome.
        
        Args:
            agent_id: Agent whose rating to update
            was_correct: Whether agent's vote was correct
            domain: Task domain
            opponent_rating: Average rating of disagreeing agents
            
        Returns:
            New Elo rating
        """
        current_rating = self.ratings[agent_id][domain]
        
        if opponent_rating is None:
            # Use average rating as opponent
            opponent_rating = self.initial_rating
        
        # Expected score (probability of being correct)
        expected = 1.0 / (1.0 + 10 ** ((opponent_rating - current_rating) / 400))
        
        # Actual score
        actual = 1.0 if was_correct else 0.0
        
        # Elo update
        new_rating = current_rating + self.k_factor * (actual - expected)
        
        self.ratings[agent_id][domain] = new_rating
        
        logger.info(
            f"Elo update: {agent_id} in {domain}: "
            f"{current_rating:.0f} → {new_rating:.0f}"
        )
        
        return new_rating
    
    def get_agent_rating(self, agent_id: str, domain: str = "general") -> float:
        """
        Get current Elo rating for agent in domain.
        
        Args:
            agent_id: Agent identifier
            domain: Task domain
            
        Returns:
            Current Elo rating
        """
        return self.ratings[agent_id][domain]
    
    def get_top_agents(self, domain: str = "general", top_k: int = 5) -> List[tuple]:
        """
        Get top-rated agents for a domain.
        
        Args:
            domain: Task domain
            top_k: Number of agents to return
            
        Returns:
            List of (agent_id, rating) tuples
        """
        agent_ratings = [
            (agent_id, ratings[domain])
            for agent_id, ratings in self.ratings.items()
        ]
        
        return sorted(agent_ratings, key=lambda x: x[1], reverse=True)[:top_k]
    
    def clear_votes(self) -> None:
        """Clear vote history (preserves Elo ratings)"""
        self.vote_history.clear()
        logger.debug("Vote history cleared")
