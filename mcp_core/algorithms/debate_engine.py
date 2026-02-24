"""
Debate Engine - Multi-Agent Debate with Sycophancy Mitigation

Implements Sparse Debate from v3.0 spec Sections 3.3-4.4
with blind drafting and sparse communication topology.
"""

import logging
from typing import List, Dict, Optional, Literal
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class DebatePhase(Enum):
    """Current phase of debate"""
    BLIND_DRAFT = "blind_draft"
    CRITIQUE = "critique"
    REVISION = "revision"
    CONVERGED = "converged"


@dataclass
class Critique:
    """A critique from one agent to another"""
    from_agent: str
    to_agent: str
    round_num: int
    message: str
    severity: Literal["blocking", "suggestion", "clarification"] = "suggestion"


@dataclass
class DebateState:
    """Current state of a debate session"""
    agents: List[str]
    phase: DebatePhase = DebatePhase.BLIND_DRAFT
    current_round: int = 0
    drafts: Dict[str, str] = field(default_factory=dict)
    critiques: List[Critique] = field(default_factory=list)
    revisions: Dict[str, List[str]] = field(default_factory=dict)
    topology: Literal["ring", "pairs", "tree"] = "ring"


@dataclass
class SpeakerConstraints:
    """Constraints for speaker selection"""
    no_consecutive_repeats: bool = True
    max_turns_per_agent: Optional[int] = None
    previous_speaker: Optional[str] = None


class DebateEngine:
    """
    Multi-agent debate with sycophancy mitigation.
    
    Key features:
    - Blind drafting: agents generate independently to preserve diversity
    - Sparse topology: limits cross-talk to slow false consensus
    - Dynamic speaker selection: context-aware turn-taking
    """
    
    def __init__(self, max_rounds: int = 5, convergence_threshold: int = 2):
        """
        Args:
            max_rounds: Maximum debate rounds before forced termination
            convergence_threshold: Rounds without changes to declare convergence
        """
        self.max_rounds = max_rounds
        self.convergence_threshold = convergence_threshold
        
        self.active_debates: Dict[str, DebateState] = {}
    
    def start_debate(
        self,
        debate_id: str,
        agents: List[str],
        topology: Literal["ring", "pairs", "tree"] = "ring"
    ) -> DebateState:
        """
        Initialize a new debate session.
        
        Args:
            debate_id: Unique identifier for debate
            agents: List of participating agent IDs
            topology: Communication topology
            
        Returns:
            Initial debate state
        """
        if len(agents) < 2:
            raise ValueError("Debate requires at least 2 agents")
        
        state = DebateState(
            agents=agents,
            topology=topology
        )
        
        self.active_debates[debate_id] = state
        logger.info(
            f"Debate started: {debate_id} with {len(agents)} agents "
            f"(topology={topology})"
        )
        
        return state
    
    def blind_draft_phase(
        self,
        debate_id: str,
        drafts: Dict[str, str]
    ) -> None:
        """
        Record independent drafts from each agent.
        
        Agents generate WITHOUT seeing each other's work,
        preserving ensemble diversity.
        
        Args:
            debate_id: Debate identifier
            drafts: Map of {agent_id: draft_content}
        """
        if debate_id not in self.active_debates:
            raise ValueError(f"Debate {debate_id} not found")
        
        state = self.active_debates[debate_id]
        
        if state.phase != DebatePhase.BLIND_DRAFT:
            raise ValueError(f"Debate not in BLIND_DRAFT phase")
        
        state.drafts = drafts
        state.phase = DebatePhase.CRITIQUE
        
        logger.info(f"Blind drafts collected: {len(drafts)} agents")
    
    def sparse_critique_phase(
        self,
        debate_id: str,
        generate_critique_fn: callable
    ) -> List[Critique]:
        """
        Limited visibility debate rounds.
        
        Uses sparse topology to restrict who sees whose work,
        slowing false consensus propagation.
        
        Args:
            debate_id: Debate identifier
            generate_critique_fn: Function(agent_id, visible_drafts) -> critique
            
        Returns:
            List of critiques generated this round
        """
        if debate_id not in self.active_debates:
            raise ValueError(f"Debate {debate_id} not found")
        
        state = self.active_debates[debate_id]
        
        if state.phase != DebatePhase.CRITIQUE:
            raise ValueError(f"Debate not in CRITIQUE phase")
        
        # Determine visibility based on topology
        pairings = self._get_topology_pairings(state)
        
        critiques = []
        for critic_id, target_id in pairings:
            # Critic only sees target's draft (sparse visibility)
            visible_draft = {target_id: state.drafts[target_id]}
            
            critique_text = generate_critique_fn(critic_id, visible_draft)
            
            critique = Critique(
                from_agent=critic_id,
                to_agent=target_id,
                round_num=state.current_round,
                message=critique_text
            )
            
            critiques.append(critique)
            state.critiques.append(critique)
        
        state.phase = DebatePhase.REVISION
        logger.info(f"Critiques generated: {len(critiques)}")
        
        return critiques
    
    def _get_topology_pairings(
        self,
        state: DebateState
    ) -> List[tuple]:
        """
        Get agent pairings based on topology.
        
        Args:
            state: Current debate state
            
        Returns:
            List of (critic, target) tuples
        """
        agents = state.agents
        n = len(agents)
        
        if state.topology == "ring":
            # Each agent critiques next agent in ring
            return [(agents[i], agents[(i + 1) % n]) for i in range(n)]
        
        elif state.topology == "pairs":
            # Random pairing (simplified: just first half critiques second half)
            mid = n // 2
            return list(zip(agents[:mid], agents[mid:mid + mid]))
        
        elif state.topology == "tree":
            # Binary tree: agent i critiques agents 2i+1 and 2i+2
            pairings = []
            for i in range(n):
                left = 2 * i + 1
                right = 2 * i + 2
                if left < n:
                    pairings.append((agents[i], agents[left]))
                if right < n:
                    pairings.append((agents[i], agents[right]))
            return pairings
        
        return []
    
    def revision_phase(
        self,
        debate_id: str,
        revisions: Dict[str, str]
    ) -> bool:
        """
        Apply agent revisions and check convergence.
        
        Args:
            debate_id: Debate identifier
            revisions: Map of {agent_id: revised_draft}
            
        Returns:
            True if debate has converged, False otherwise
        """
        if debate_id not in self.active_debates:
            raise ValueError(f"Debate {debate_id} not found")
        
        state = self.active_debates[debate_id]
        
        if state.phase != DebatePhase.REVISION:
            raise ValueError(f"Debate not in REVISION phase")
        
        # Track changes
        unchanged_count = 0
        for agent_id, new_draft in revisions.items():
            if agent_id not in state.revisions:
                state.revisions[agent_id] = []
            
            state.revisions[agent_id].append(new_draft)
            
            # Check if unchanged from previous
            old_draft = state.drafts.get(agent_id, "")
            if old_draft == new_draft:
                unchanged_count += 1
        
        # Update drafts for next round
        state.drafts.update(revisions)
        state.current_round += 1
        
        # Check convergence
        converged = (unchanged_count >= len(state.agents) - 1)
        converged = converged or (state.current_round >= self.max_rounds)
        
        if converged:
            state.phase = DebatePhase.CONVERGED
            logger.info(f"Debate converged after {state.current_round} rounds")
        else:
            state.phase = DebatePhase.CRITIQUE
            logger.info(f"Round {state.current_round}: {unchanged_count} unchanged")
        
        return converged
    
    def select_next_speaker(
        self,
        state: DebateState,
        constraints: SpeakerConstraints
    ) -> Optional[str]:
        """
        Dynamic speaker selection based on state.
        
        Implements speaker transition constraints to prevent
        repetition and ensure equitable participation.
        
        Args:
            state: Current debate state
            constraints: Selection constraints
            
        Returns:
            Selected agent ID or None if no valid speaker
        """
        available = set(state.agents)
        
        # Apply constraints
        if constraints.no_consecutive_repeats and constraints.previous_speaker:
            available.discard(constraints.previous_speaker)
        
        if constraints.max_turns_per_agent is not None:
            # Count turns per agent (simplified)
            for agent_id in state.agents:
                turn_count = sum(
                    1 for c in state.critiques if c.from_agent == agent_id
                )
                if turn_count >= constraints.max_turns_per_agent:
                    available.discard(agent_id)
        
        if not available:
            return None
        
        # Simple selection: first available
        # Production would use context-aware selection
        return list(available)[0]
    
    def get_final_consensus(self, debate_id: str) -> Dict[str, str]:
        """
        Get final drafts after convergence.
        
        Args:
            debate_id: Debate identifier
            
        Returns:
            Map of {agent_id: final_draft}
        """
        if debate_id not in self.active_debates:
            raise ValueError(f"Debate {debate_id} not found")
        
        state = self.active_debates[debate_id]
        
        if state.phase != DebatePhase.CONVERGED:
            logger.warning(f"Debate {debate_id} not yet converged")
        
        return state.drafts.copy()
