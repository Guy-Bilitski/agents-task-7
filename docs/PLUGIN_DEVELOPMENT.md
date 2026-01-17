# Plugin Development Guide

## Overview

The Even-Odd League system supports a plugin architecture that allows you to create custom parity strategies without modifying the core codebase. This guide explains how to create, test, and deploy your own strategy plugins.

---

## Table of Contents

1. [Quick Start](#quick-start)
2. [Plugin Structure](#plugin-structure)
3. [Creating a Strategy Plugin](#creating-a-strategy-plugin)
4. [Plugin Interface](#plugin-interface)
5. [Testing Your Plugin](#testing-your-plugin)
6. [Advanced Features](#advanced-features)
7. [Best Practices](#best-practices)
8. [Examples](#examples)

---

## Quick Start

Create a new strategy in 3 steps:

### Step 1: Create Plugin Directory

```bash
mkdir -p src/agents/player/plugins/my_strategy
```

### Step 2: Create Strategy File

```python
# src/agents/player/plugins/my_strategy/strategy.py

from agents.player.strategy import ParityStrategy

class MyStrategy(ParityStrategy):
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        # Your logic here
        return "even"  # or "odd"

    def get_name(self) -> str:
        return "my_strategy"

STRATEGY_CLASS = MyStrategy
```

### Step 3: Use Your Plugin

```bash
PYTHONPATH=src python3 -m agents.player \
    --port 8101 \
    --strategy my_strategy \
    --league-url http://127.0.0.1:9000
```

---

## Plugin Structure

```
src/agents/player/plugins/
├── __init__.py              # Plugin package marker
├── my_strategy/             # Your plugin directory
│   ├── __init__.py          # Optional: can export STRATEGY_CLASS
│   └── strategy.py          # Required: strategy implementation
└── another_strategy/
    └── strategy.py
```

### Required Files

| File | Purpose |
|------|---------|
| `strategy.py` | Contains your `ParityStrategy` subclass |

### Optional Files

| File | Purpose |
|------|---------|
| `__init__.py` | Export `STRATEGY_CLASS` for explicit registration |
| `config.py` | Plugin configuration |
| `tests/` | Plugin-specific tests |

---

## Creating a Strategy Plugin

### The ParityStrategy Interface

All strategies must inherit from `ParityStrategy` and implement two methods:

```python
from abc import ABC, abstractmethod

class ParityStrategy(ABC):
    @abstractmethod
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Choose parity for a game.

        Args:
            game_id: Unique game identifier (UUID)
            history: List of previous game results
            stats: Current player statistics

        Returns:
            Either "even" or "odd"
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the unique strategy name."""
        pass
```

### Method Parameters

#### `game_id: str`
A unique identifier for each game. Useful for deterministic strategies or logging.

#### `history: list`
List of previous game records. Each record is a dictionary:

```python
{
    "game_id": "abc123",
    "opponent": "agent_Beta",
    "choice": "even",
    "opponent_choice": "odd",
    "dice_roll": 42,
    "won": True,
    "timestamp": "2026-01-17T10:30:00Z"
}
```

#### `stats: dict`
Current player statistics:

```python
{
    "games_played": 10,
    "wins": 6,
    "losses": 4,
    "draws": 0,
    "win_rate": 0.6
}
```

---

## Plugin Interface

### Complete Example

```python
"""Pattern recognition strategy plugin."""

import random
from collections import Counter
from typing import Any, Dict, List

from agents.player.strategy import ParityStrategy


class PatternStrategy(ParityStrategy):
    """Recognizes patterns in opponent behavior."""

    def __init__(self):
        self.opponent_history: Dict[str, List[str]] = {}

    def choose(self, game_id: str, history: List[Dict], stats: Dict) -> str:
        # Track opponent patterns
        for game in history:
            opponent = game.get("opponent", "unknown")
            opp_choice = game.get("opponent_choice")
            if opp_choice:
                if opponent not in self.opponent_history:
                    self.opponent_history[opponent] = []
                self.opponent_history[opponent].append(opp_choice)

        # Find most common opponent choice
        all_opponent_choices = []
        for choices in self.opponent_history.values():
            all_opponent_choices.extend(choices[-10:])  # Last 10 per opponent

        if all_opponent_choices:
            counter = Counter(all_opponent_choices)
            most_common = counter.most_common(1)[0][0]
            # Counter the most common
            return "odd" if most_common == "even" else "even"

        return random.choice(["even", "odd"])

    def get_name(self) -> str:
        return "pattern"


# Export for plugin loader
STRATEGY_CLASS = PatternStrategy
```

---

## Testing Your Plugin

### Unit Testing

Create tests in your plugin directory:

```python
# src/agents/player/plugins/my_strategy/tests/test_strategy.py

import pytest
from ..strategy import MyStrategy


class TestMyStrategy:
    def test_returns_valid_choice(self):
        strategy = MyStrategy()
        choice = strategy.choose("game-1", [], {})
        assert choice in ["even", "odd"]

    def test_strategy_name(self):
        strategy = MyStrategy()
        assert strategy.get_name() == "my_strategy"

    def test_with_history(self):
        strategy = MyStrategy()
        history = [
            {"won": True, "choice": "even"},
            {"won": False, "choice": "odd"},
        ]
        choice = strategy.choose("game-2", history, {"wins": 1, "losses": 1})
        assert choice in ["even", "odd"]
```

Run tests:

```bash
PYTHONPATH=src pytest src/agents/player/plugins/my_strategy/tests/ -v
```

### Integration Testing

Test with the full system:

```bash
# Start league manager
PYTHONPATH=src python3 -m agents.league_manager --port 9000 --server-only &

# Start player with your plugin
PYTHONPATH=src python3 -m agents.player \
    --port 8101 \
    --strategy my_strategy \
    --league-url http://127.0.0.1:9000 &

# Start another player
PYTHONPATH=src python3 -m agents.player \
    --port 8102 \
    --strategy random \
    --league-url http://127.0.0.1:9000 &

# Start tournament
curl -X POST http://127.0.0.1:9000/start

# View standings
curl http://127.0.0.1:9000/standings
```

---

## Advanced Features

### Stateful Strategies

Maintain state across games:

```python
class StatefulStrategy(ParityStrategy):
    def __init__(self):
        self.game_count = 0
        self.last_results = []

    def choose(self, game_id: str, history: list, stats: dict) -> str:
        self.game_count += 1

        # Track last 5 results
        if history:
            self.last_results = [g.get("won", False) for g in history[-5:]]

        # Use state in decision
        if len(self.last_results) >= 3:
            recent_wins = sum(self.last_results[-3:])
            if recent_wins >= 2:
                return self._keep_winning_choice(history)

        return random.choice(["even", "odd"])
```

### Configuration Support

Accept configuration parameters:

```python
class ConfigurableStrategy(ParityStrategy):
    def __init__(self, aggression: float = 0.5, memory_size: int = 10):
        self.aggression = aggression
        self.memory_size = memory_size

    def choose(self, game_id: str, history: list, stats: dict) -> str:
        recent = history[-self.memory_size:]
        # Use self.aggression in decision logic
        ...
```

### Logging

Use the logging system:

```python
import logging

logger = logging.getLogger(__name__)

class LoggingStrategy(ParityStrategy):
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        logger.debug(f"Game {game_id}: history has {len(history)} entries")
        choice = self._make_choice(history)
        logger.info(f"Chose {choice} for game {game_id}")
        return choice
```

---

## Best Practices

### 1. Return Only Valid Values

```python
def choose(self, game_id, history, stats) -> str:
    choice = self._calculate_choice()
    # Always validate
    if choice not in ["even", "odd"]:
        return "even"  # Safe default
    return choice
```

### 2. Handle Empty History

```python
def choose(self, game_id, history, stats) -> str:
    if not history:
        return random.choice(["even", "odd"])
    # ... rest of logic
```

### 3. Use Type Hints

```python
from typing import Any, Dict, List

def choose(self, game_id: str, history: List[Dict[str, Any]], stats: Dict[str, Any]) -> str:
    ...
```

### 4. Document Your Strategy

```python
class MyStrategy(ParityStrategy):
    """Short description of the strategy.

    Longer description explaining the algorithm,
    its strengths, and weaknesses.

    Algorithm:
        1. Step one
        2. Step two
        3. Step three

    Attributes:
        attribute_name: Description of attribute
    """
```

### 5. Make Strategies Reproducible (When Needed)

```python
class DeterministicStrategy(ParityStrategy):
    def __init__(self, seed: int = 42):
        self.rng = random.Random(seed)

    def choose(self, game_id, history, stats) -> str:
        return self.rng.choice(["even", "odd"])
```

---

## Examples

### Built-in Strategies

Study these implementations in `src/agents/player/strategy.py`:

| Strategy | Description | Complexity |
|----------|-------------|------------|
| `RandomStrategy` | 50/50 random | Simple |
| `AlternatingStrategy` | Switches each game | Simple |
| `AdaptiveStrategy` | Learns from results | Medium |
| `CounterStrategy` | Tracks patterns | Medium |
| `BiasedRandomStrategy` | Configurable bias | Simple |

### Sample Plugin

See `src/agents/player/plugins/sample_strategy/` for a complete example of the `MomentumStrategy`.

---

## Troubleshooting

### Plugin Not Loading

1. Check directory structure
2. Verify `STRATEGY_CLASS` is exported
3. Check for import errors: `python -c "from agents.player.plugins.my_strategy import STRATEGY_CLASS"`

### Import Errors

Ensure PYTHONPATH includes `src/`:

```bash
PYTHONPATH=src python3 -c "from agents.player.strategy import ParityStrategy"
```

### Strategy Not Available

List available strategies:

```python
from agents.player.strategy import list_strategies
print(list_strategies())
```

---

## API Reference

### PluginManager

```python
from agents.player.plugin_loader import PluginManager

manager = PluginManager()
loaded = manager.discover_plugins()  # Returns list of loaded plugin names
plugins = manager.get_loaded_plugins()  # Returns dict of name -> strategy
manager.reload_plugins()  # Refresh all plugins
manager.unload_plugin("my_strategy")  # Unload specific plugin
```

### Convenience Functions

```python
from agents.player.plugin_loader import (
    discover_and_load_plugins,
    register_external_strategy,
)

# Load all plugins
discover_and_load_plugins()

# Register a strategy programmatically
register_external_strategy(MyStrategy())
```
