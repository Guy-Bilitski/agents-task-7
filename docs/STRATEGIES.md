# Parity Game Strategies

The Even-Odd League now supports **multiple AI strategies** for making parity choices! Each agent can use a different strategy, making games more interesting and competitive.

## Available Strategies

### 1. **random** (Default)
Randomly chooses "even" or "odd" with 50/50 probability.
- **Best for:** Unpredictable play, good baseline strategy
- **Weakness:** No adaptation or learning

### 2. **always_even**
Always chooses "even".
- **Best for:** Testing, simplicity
- **Weakness:** Completely predictable

### 3. **always_odd**
Always chooses "odd".
- **Best for:** Testing, simplicity
- **Weakness:** Completely predictable

### 4. **deterministic**
Chooses based on a hash of the game_id (same game_id = same choice).
- **Best for:** Reproducible testing, debugging
- **Weakness:** Predictable if opponent knows the game_id

### 5. **alternating**
Alternates between "even" and "odd" with each game.
- **Best for:** Balanced play over many games
- **Weakness:** Predictable pattern

### 6. **adaptive**
Learns from recent performance and adapts:
- If winning → keeps the same choice
- If losing → switches to the opposite
- **Best for:** Learning opponents' patterns
- **Weakness:** Slow to adapt in early games

### 7. **counter**
Tracks which choices have been winning and picks accordingly.
- **Best for:** Meta-game strategy
- **Weakness:** Relies on having enough game history

### 8. **biased_random_70**
Random choice with 70% probability of "even", 30% "odd".
- **Best for:** Exploiting opponents who favor odd
- **Weakness:** Slight bias can be detected

### 9. **biased_random_30**
Random choice with 30% probability of "even", 70% "odd".
- **Best for:** Exploiting opponents who favor even
- **Weakness:** Slight bias can be detected

---

## Using Strategies

### In the League

When running the full league, agents automatically get assigned different strategies:

```bash
python3 scripts/run_league.py
```

The 4 agents will use:
- **Alpha**: random
- **Beta**: always_even
- **Gamma**: always_odd
- **Delta**: alternating

If you run with 8 agents:
```bash
python3 scripts/run_league.py --num-agents 8
```

They'll rotate through all strategies:
- Alpha: random
- Beta: always_even
- Gamma: always_odd
- Delta: alternating
- Epsilon: adaptive
- Zeta: deterministic
- Eta: biased_random_70
- Theta: counter

### For a Single Agent

Start an agent with a specific strategy:

```bash
python3 scripts/start_player.py \
  --port 8001 \
  --display-name "MyAgent" \
  --league-url http://127.0.0.1:9000 \
  --strategy random
```

### Using Environment Variables

```bash
STRATEGY=adaptive python3 scripts/start_player.py \
  --port 8001 \
  --display-name "Learner" \
  --league-url http://127.0.0.1:9000
```

---

## Strategy Performance

Here's how different strategies might perform:

| Strategy | vs Random | vs Always Even | vs Always Odd | Overall |
|----------|-----------|----------------|---------------|---------|
| **random** | 50% | 50% | 50% | ⭐⭐⭐ Good baseline |
| **always_even** | 50% | 50% (draw) | 50% | ⭐⭐ Predictable |
| **always_odd** | 50% | 50% | 50% (draw) | ⭐⭐ Predictable |
| **alternating** | 50% | 50% | 50% | ⭐⭐⭐ Balanced |
| **adaptive** | 55%+ | 75%+ | 75%+ | ⭐⭐⭐⭐ Learns |
| **counter** | 55%+ | 70%+ | 70%+ | ⭐⭐⭐⭐ Meta-game |
| **biased_random** | 50% | 60%+ | 40%- | ⭐⭐⭐ Exploitative |

**Note:** Actual performance depends on dice variance and game count.

---

## Creating Your Own Strategy

Want to create a custom strategy? It's easy!

### 1. Edit `src/agents/player/strategy.py`

```python
class MyCustomStrategy(ParityStrategy):
    """Your custom strategy description."""
    
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Make your choice logic here.
        
        Args:
            game_id: Current game ID
            history: List of past game results with outcomes
            stats: Player statistics (wins, losses, win_rate, etc.)
            
        Returns:
            Either "even" or "odd"
        """
        # Your logic here
        # Example: choose based on win rate
        if stats["win_rate"] > 0.5:
            return "even"
        else:
            return "odd"
    
    def get_name(self) -> str:
        return "my_custom"
```

### 2. Register it in the `STRATEGIES` dict:

```python
STRATEGIES: Dict[str, ParityStrategy] = {
    # ... existing strategies ...
    "my_custom": MyCustomStrategy(),
}
```

### 3. Use it:

```bash
python3 scripts/start_player.py \
  --port 8001 \
  --display-name "Custom" \
  --league-url http://127.0.0.1:9000 \
  --strategy my_custom
```

---

## Strategy Tips

### For Competitive Play

1. **Use random as baseline** - It's hard to beat
2. **Adaptive strategies need time** - They improve with more games
3. **Mix strategies in tournaments** - Diversity makes it interesting
4. **Track your win rate** - See which strategy performs best

### For Testing

1. **Use deterministic** - Same game_id → same result
2. **Use always_even/always_odd** - Easy to verify behavior
3. **Use alternating** - Test pattern recognition

### For Fun

1. **Run 8 agents** - See all strategies compete!
2. **Watch adaptive agents learn** - They get smarter over time
3. **Create custom strategies** - Make your own AI!

---

## Examples

### Random Agent
```bash
python3 scripts/start_player.py \
  --port 8001 \
  --display-name "Lucky" \
  --league-url http://127.0.0.1:9000 \
  --strategy random
```

### Adaptive Learning Agent
```bash
python3 scripts/start_player.py \
  --port 8002 \
  --display-name "Learner" \
  --league-url http://127.0.0.1:9000 \
  --strategy adaptive
```

### Counter-Strategy Agent
```bash
python3 scripts/start_player.py \
  --port 8003 \
  --display-name "Meta" \
  --league-url http://127.0.0.1:9000 \
  --strategy counter
```

---

## Advanced: Strategy Analysis

Want to see which strategy wins the most? Run a tournament:

```bash
# Run with all 8 strategies
python3 scripts/run_league.py --num-agents 8 --rounds 10

# The standings will show which strategy performs best!
```

The output will show:
```
Final Standings:
1. Epsilon (adaptive)     - 18 wins
2. Theta (counter)        - 16 wins
3. Alpha (random)         - 14 wins
4. Zeta (deterministic)   - 12 wins
...
```

---

## Summary

- ✅ **9 strategies available** out of the box
- ✅ **Easy to use** with `--strategy` flag
- ✅ **Easy to extend** - create your own strategies
- ✅ **Automatic variety** - league assigns different strategies to agents
- ✅ **Fun & competitive** - watch strategies compete!

Enjoy the games! 🎲
