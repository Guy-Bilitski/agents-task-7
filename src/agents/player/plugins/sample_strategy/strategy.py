"""Momentum-based parity strategy plugin.

This module demonstrates a custom strategy plugin implementation
that uses "momentum" - continuing with the same choice when winning
streaks occur, and switching when losing.

This serves as an example of how to create custom strategy plugins
for the Even-Odd League system.
"""

import random
from typing import Any, Dict, List

# Import the base class from the parent package
# Note: When loaded as a plugin, this import path will work
import sys
from pathlib import Path

# Add parent path for imports when running as plugin
parent_path = Path(__file__).parent.parent.parent
if str(parent_path) not in sys.path:
    sys.path.insert(0, str(parent_path))

from strategy import ParityStrategy


class MomentumStrategy(ParityStrategy):
    """A strategy that builds momentum based on winning/losing streaks.

    This strategy tracks consecutive wins and losses to determine when
    to stick with a choice or switch. The idea is that streaks might
    indicate patterns worth following or breaking.

    Algorithm:
    - If on a winning streak of 2+, keep the same choice (momentum)
    - If on a losing streak of 2+, switch the choice (break the pattern)
    - Otherwise, make a weighted random choice based on recent history

    Attributes:
        current_choice: The last choice made
        streak: Current streak count (positive = wins, negative = losses)
        momentum_threshold: Number of consecutive results before adjusting
    """

    def __init__(self, momentum_threshold: int = 2):
        """Initialize the momentum strategy.

        Args:
            momentum_threshold: Number of consecutive wins/losses before
                               adjusting behavior. Default is 2.
        """
        self.current_choice: str = random.choice(["even", "odd"])
        self.streak: int = 0
        self.momentum_threshold = momentum_threshold
        self._total_games: int = 0
        self._switches: int = 0

    def choose(self, game_id: str, history: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
        """Choose parity based on momentum from recent game history.

        Args:
            game_id: Unique identifier for this game
            history: List of previous game records with 'won' and 'choice' keys
            stats: Current player statistics

        Returns:
            Either "even" or "odd"
        """
        self._total_games += 1

        # First game - random choice
        if not history:
            return self.current_choice

        # Update streak based on last game
        last_game = history[-1]
        won = last_game.get("won", False)

        if won:
            if self.streak >= 0:
                self.streak += 1
            else:
                self.streak = 1
        else:
            if self.streak <= 0:
                self.streak -= 1
            else:
                self.streak = -1

        # Apply momentum logic
        if self.streak >= self.momentum_threshold:
            # Winning streak - keep the momentum going
            pass  # Keep current_choice unchanged

        elif self.streak <= -self.momentum_threshold:
            # Losing streak - time to switch
            self._switch_choice()

        else:
            # No clear streak - use weighted random based on recent wins
            recent = history[-5:] if len(history) >= 5 else history
            recent_wins = sum(1 for g in recent if g.get("won", False))
            win_rate = recent_wins / len(recent) if recent else 0.5

            # If winning less than 40%, consider switching
            if win_rate < 0.4 and random.random() < 0.3:
                self._switch_choice()

        return self.current_choice

    def _switch_choice(self) -> None:
        """Switch the current choice to the opposite parity."""
        self.current_choice = "odd" if self.current_choice == "even" else "even"
        self._switches += 1

    def get_name(self) -> str:
        """Return the strategy name for registration.

        Returns:
            The unique name for this strategy.
        """
        return "momentum"

    def get_stats(self) -> Dict[str, Any]:
        """Get strategy-specific statistics.

        Returns:
            Dictionary of strategy statistics.
        """
        return {
            "total_games": self._total_games,
            "switches": self._switches,
            "current_streak": self.streak,
            "current_choice": self.current_choice,
            "switch_rate": self._switches / self._total_games if self._total_games > 0 else 0,
        }


# For explicit plugin discovery
STRATEGY_CLASS = MomentumStrategy
