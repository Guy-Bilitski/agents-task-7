"""Parity game strategies for player agents.

This module provides different strategies for choosing parity (even/odd) in games.
Players can use different strategies to make their choices more interesting and competitive.
"""
import random
import hashlib
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional


class ParityStrategy(ABC):
    """Base class for parity selection strategies."""
    
    @abstractmethod
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Choose parity for a game.
        
        Args:
            game_id: Unique game identifier
            history: List of previous game results
            stats: Current player statistics (wins, losses, etc.)
            
        Returns:
            Either "even" or "odd"
        """
        pass
    
    @abstractmethod
    def get_name(self) -> str:
        """Return the strategy name."""
        pass


class RandomStrategy(ParityStrategy):
    """Randomly choose even or odd with 50/50 probability."""
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Choose randomly between even and odd."""
        return random.choice(["even", "odd"])
    
    def get_name(self) -> str:
        return "random"


class AlwaysEvenStrategy(ParityStrategy):
    """Always choose even."""
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Always return even."""
        return "even"
    
    def get_name(self) -> str:
        return "always_even"


class AlwaysOddStrategy(ParityStrategy):
    """Always choose odd."""
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Always return odd."""
        return "odd"
    
    def get_name(self) -> str:
        return "always_odd"


class DeterministicStrategy(ParityStrategy):
    """Deterministically choose based on game_id hash.
    
    This ensures the same game_id always produces the same choice,
    which is useful for testing and debugging.
    """
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Choose based on hash of game_id."""
        hash_val = int(hashlib.md5(game_id.encode()).hexdigest(), 16)
        return "even" if hash_val % 2 == 0 else "odd"
    
    def get_name(self) -> str:
        return "deterministic"


class AlternatingStrategy(ParityStrategy):
    """Alternate between even and odd based on game count."""
    
    def __init__(self):
        self.game_count = 0
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Alternate choices."""
        self.game_count += 1
        return "even" if self.game_count % 2 == 0 else "odd"
    
    def get_name(self) -> str:
        return "alternating"


class AdaptiveStrategy(ParityStrategy):
    """Adapt based on previous results.
    
    If losing, switch preference. If winning, keep the same.
    Falls back to random when no history exists.
    """
    
    def __init__(self):
        self.last_choice = None
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Choose based on recent performance."""
        # Start with random if no history
        if not history:
            choice = random.choice(["even", "odd"])
            self.last_choice = choice
            return choice
        
        # Look at recent games (last 5)
        recent = history[-5:]
        wins = sum(1 for game in recent if game.get("won", False))
        
        # If winning more than 50%, keep last choice
        if wins > len(recent) / 2 and self.last_choice:
            return self.last_choice
        
        # Otherwise switch or randomize
        if self.last_choice == "even":
            self.last_choice = "odd"
        elif self.last_choice == "odd":
            self.last_choice = "even"
        else:
            self.last_choice = random.choice(["even", "odd"])
        
        return self.last_choice
    
    def get_name(self) -> str:
        return "adaptive"


class CounterStrategy(ParityStrategy):
    """Try to counter opponent's likely choice.
    
    Tracks what choices tend to win and picks accordingly.
    """
    
    def __init__(self):
        self.even_wins = 0
        self.odd_wins = 0
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Choose based on what's been winning."""
        # Update stats from history
        for game in history:
            if game.get("won"):
                if game.get("choice") == "even":
                    self.even_wins += 1
                else:
                    self.odd_wins += 1
        
        # If no data, random
        if self.even_wins + self.odd_wins == 0:
            return random.choice(["even", "odd"])
        
        # Pick what's been winning more
        return "even" if self.even_wins >= self.odd_wins else "odd"
    
    def get_name(self) -> str:
        return "counter"


class BiasedRandomStrategy(ParityStrategy):
    """Random with a bias toward one choice.
    
    Args:
        even_probability: Probability of choosing even (0.0 to 1.0)
    """
    
    def __init__(self, even_probability: float = 0.7):
        self.even_probability = max(0.0, min(1.0, even_probability))
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Choose with bias."""
        return "even" if random.random() < self.even_probability else "odd"
    
    def get_name(self) -> str:
        return f"biased_random_{int(self.even_probability * 100)}"


# Strategy registry
STRATEGIES: Dict[str, ParityStrategy] = {
    "random": RandomStrategy(),
    "always_even": AlwaysEvenStrategy(),
    "always_odd": AlwaysOddStrategy(),
    "deterministic": DeterministicStrategy(),
    "alternating": AlternatingStrategy(),
    "adaptive": AdaptiveStrategy(),
    "counter": CounterStrategy(),
    "biased_random_70": BiasedRandomStrategy(0.7),
    "biased_random_30": BiasedRandomStrategy(0.3),
}


def get_strategy(name: str) -> ParityStrategy:
    """Get a strategy by name.
    
    Args:
        name: Strategy name (e.g., "random", "always_even")
        
    Returns:
        ParityStrategy instance
        
    Raises:
        ValueError: If strategy name is not found
    """
    if name not in STRATEGIES:
        available = ", ".join(STRATEGIES.keys())
        raise ValueError(f"Unknown strategy '{name}'. Available: {available}")
    
    return STRATEGIES[name]


def list_strategies() -> list:
    """Return list of available strategy names."""
    return list(STRATEGIES.keys())


# Default strategy
DEFAULT_STRATEGY = "random"
