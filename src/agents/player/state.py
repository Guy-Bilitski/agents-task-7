"""Thread-safe state management for MCP Agent.

Maintains in-memory state for:
- Game invitations
- Parity choices
- Match results
- Statistics
- Event history
- Parity strategy
"""
import hashlib
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from agents.player.strategy import ParityStrategy

logger = logging.getLogger(__name__)


@dataclass
class GameInvitation:
    """Game invitation details."""
    
    game_id: Optional[str]
    invitation_id: Optional[str]
    from_player: Optional[str]
    timestamp: str
    extra_fields: dict = field(default_factory=dict)


@dataclass
class ParityChoice:
    """Parity choice details."""
    
    game_id: Optional[str]
    choice: str  # "even" or "odd"
    timestamp: str
    extra_fields: dict = field(default_factory=dict)


@dataclass
class MatchResult:
    """Match result details."""
    
    game_id: Optional[str]
    winner: Optional[str]
    details: dict
    timestamp: str
    extra_fields: dict = field(default_factory=dict)


@dataclass
class Statistics:
    """Agent statistics."""
    
    games_invited: int = 0
    games_played: int = 0
    wins: int = 0
    losses: int = 0
    draws: int = 0
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played


class AgentState:
    """Thread-safe agent state.
    
    Stores all game-related state and provides thread-safe access.
    """
    
    def __init__(self, display_name: str, strategy: Optional['ParityStrategy'] = None):
        """Initialize agent state.
        
        Args:
            display_name: Agent's display name (for determining wins)
            strategy: Parity choice strategy (optional)
        """
        self.display_name = display_name
        self.strategy = strategy
        self._lock = threading.Lock()
        
        # Current state
        self.invitations: dict[str, GameInvitation] = {}
        self.choices: dict[str, ParityChoice] = {}
        self.results: dict[str, MatchResult] = {}
        
        # Statistics
        self.stats = Statistics()
        
        # Event history (for debugging and learning)
        self.history: list[dict] = []
        
        strategy_name = strategy.get_name() if strategy else "none"
        logger.info(f"Agent state initialized for '{display_name}' with strategy '{strategy_name}'")
    
    def record_invitation(
        self,
        game_id: Optional[str],
        invitation_id: Optional[str],
        from_player: Optional[str],
        extra_fields: dict
    ) -> GameInvitation:
        """Record a game invitation.
        
        Args:
            game_id: Game ID
            invitation_id: Invitation ID
            from_player: Sender
            extra_fields: Any extra parameters
        
        Returns:
            GameInvitation object
        """
        with self._lock:
            invitation = GameInvitation(
                game_id=game_id,
                invitation_id=invitation_id,
                from_player=from_player,
                timestamp=datetime.utcnow().isoformat(),
                extra_fields=extra_fields
            )
            
            # Store by game_id if available, otherwise by invitation_id
            key = game_id or invitation_id or f"unknown_{len(self.invitations)}"
            self.invitations[key] = invitation
            
            # Update stats
            self.stats.games_invited += 1
            
            # Add to history
            self.history.append({
                "type": "invitation",
                "timestamp": invitation.timestamp,
                "game_id": game_id,
                "invitation_id": invitation_id,
                "from_player": from_player
            })
            
            logger.info(f"Recorded invitation: game_id={game_id}, total_invited={self.stats.games_invited}")
            return invitation
    
    def record_choice(
        self,
        game_id: Optional[str],
        choice: str,
        extra_fields: dict
    ) -> ParityChoice:
        """Record a parity choice.
        
        Args:
            game_id: Game ID
            choice: "even" or "odd"
            extra_fields: Any extra parameters
        
        Returns:
            ParityChoice object
        """
        with self._lock:
            parity_choice = ParityChoice(
                game_id=game_id,
                choice=choice,
                timestamp=datetime.utcnow().isoformat(),
                extra_fields=extra_fields
            )
            
            # Store by game_id
            key = game_id or f"unknown_{len(self.choices)}"
            self.choices[key] = parity_choice
            
            # Add to history
            self.history.append({
                "type": "choice",
                "timestamp": parity_choice.timestamp,
                "game_id": game_id,
                "choice": choice
            })
            
            logger.info(f"Recorded choice: game_id={game_id}, choice={choice}")
            return parity_choice
    
    def record_result(
        self,
        game_id: Optional[str],
        winner: Optional[str],
        details: dict,
        extra_fields: dict
    ) -> MatchResult:
        """Record a match result.
        
        Args:
            game_id: Game ID
            winner: Winner name
            details: Result details
            extra_fields: Any extra parameters
        
        Returns:
            MatchResult object
        """
        with self._lock:
            result = MatchResult(
                game_id=game_id,
                winner=winner,
                details=details,
                timestamp=datetime.utcnow().isoformat(),
                extra_fields=extra_fields
            )
            
            # Store by game_id
            key = game_id or f"unknown_{len(self.results)}"
            self.results[key] = result
            
            # Update statistics
            self.stats.games_played += 1
            
            if winner == self.display_name:
                self.stats.wins += 1
                outcome = "win"
            elif winner is None or winner == "":
                self.stats.draws += 1
                outcome = "draw"
            else:
                self.stats.losses += 1
                outcome = "loss"
            
            # Add to history with outcome info
            choice_made = self.choices.get(key)
            self.history.append({
                "type": "result",
                "timestamp": result.timestamp,
                "game_id": game_id,
                "winner": winner,
                "outcome": outcome,
                "won": (outcome == "win"),
                "choice": choice_made.choice if choice_made else None,
                "details": details
            })
            
            logger.info(
                f"Recorded result: game_id={game_id}, outcome={outcome}, "
                f"stats=(W:{self.stats.wins} L:{self.stats.losses} D:{self.stats.draws})"
            )
            return result
    
    def get_stats(self) -> Statistics:
        """Get current statistics.
        
        Returns:
            Statistics object (copy)
        """
        with self._lock:
            return Statistics(
                games_invited=self.stats.games_invited,
                games_played=self.stats.games_played,
                wins=self.stats.wins,
                losses=self.stats.losses,
                draws=self.stats.draws
            )
    
    def get_history(self) -> list[dict]:
        """Get event history.
        
        Returns:
            List of history events (copy)
        """
        with self._lock:
            return list(self.history)
    
    def make_parity_choice(self, game_id: Optional[str]) -> str:
        """Make a parity choice using the configured strategy.
        
        Args:
            game_id: Game ID
            
        Returns:
            "even" or "odd"
        """
        with self._lock:
            if self.strategy:
                # Use configured strategy
                # Get game history (only completed games with results)
                game_history = [h for h in self.history if h.get("type") == "result"]
                stats_dict = {
                    "games_played": self.stats.games_played,
                    "wins": self.stats.wins,
                    "losses": self.stats.losses,
                    "draws": self.stats.draws,
                    "win_rate": self.stats.win_rate
                }
                choice = self.strategy.choose(game_id or "", game_history, stats_dict)
            else:
                # Fallback to deterministic
                choice = deterministic_parity_choice(game_id)
            
            return choice


def deterministic_parity_choice(game_id: Optional[str]) -> str:
    """Choose parity deterministically based on game_id.
    
    This ensures the same game_id always gets the same choice,
    but different game_ids get varied choices.
    
    Args:
        game_id: Game ID (or None)
    
    Returns:
        "even" or "odd"
    """
    if game_id is None:
        # Default to "even" if no game_id
        return "even"
    
    # Hash the game_id to get deterministic but varied choice
    hash_value = int(hashlib.sha256(game_id.encode()).hexdigest(), 16)
    
    # Choose based on hash parity
    return "even" if hash_value % 2 == 0 else "odd"


# Global state instance (will be initialized in main.py)
_global_state: Optional[AgentState] = None


def init_state(display_name: str, strategy: Optional['ParityStrategy'] = None) -> AgentState:
    """Initialize global state.
    
    Args:
        display_name: Agent's display name
        strategy: Parity choice strategy (optional)
    
    Returns:
        AgentState instance
    """
    global _global_state
    _global_state = AgentState(display_name, strategy)
    return _global_state


def get_state() -> AgentState:
    """Get global state instance.
    
    Returns:
        AgentState instance
    
    Raises:
        RuntimeError: If state not initialized
    """
    if _global_state is None:
        raise RuntimeError("State not initialized. Call init_state() first.")
    return _global_state
