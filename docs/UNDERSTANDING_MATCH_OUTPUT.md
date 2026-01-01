# Understanding Match Output

This guide explains how to read and understand the match output when running the full league system.

## Game Decision Format

Each game decision is logged by the referee in this format:

```
🎲 Game game_e54193f4: Alpha vs Beta
   Alpha chose: odd
   Beta chose: even
   Dice rolled: 35 (odd)
   ✓ Winner: Alpha (correct prediction)
```

### Components

1. **Game ID**: Unique identifier for the match (e.g., `game_e54193f4`)
2. **Players**: The two agents competing (e.g., `Alpha vs Beta`)
3. **Player Choices**: Each agent's parity selection:
   - `even` - Agent predicts the dice will be even
   - `odd` - Agent predicts the dice will be odd
4. **Dice Roll**: The random number (1-100) and its parity
5. **Result**: Who won and why, or if it was a draw

## Result Types

### Winner
```
✓ Winner: Alpha (correct prediction)
```
One player correctly predicted the parity, the other didn't.

### Draw (Both Correct)
```
⚖️  Result: DRAW (both correct)
```
Both players predicted the same parity and were correct.

### Draw (Both Wrong)
```
⚖️  Result: DRAW (both wrong)
```
Both players predicted the same parity and were both incorrect.

## Agent Strategies

At startup, you'll see which strategy each agent is using:

```
Agent Strategies:
  • Alpha: random
  • Beta: always_even
  • Gamma: always_odd
  • Delta: alternating
```

### Available Strategies

| Strategy | Behavior |
|----------|----------|
| `random` | Randomly chooses even or odd each game |
| `always_even` | Always predicts even |
| `always_odd` | Always predicts odd |
| `alternating` | Alternates between even and odd |
| `adaptive` | Learns from opponent's patterns |
| `counter` | Predicts opposite of opponent's last choice |
| `biased_random_70` | 70% chance of one parity, 30% other |
| `deterministic` | Uses game ID hash to make consistent choices |

## Reading Full Tournament Output

### 1. Initialization
```
Configuration:
  League Manager: http://127.0.0.1:9000
  Referee:        http://127.0.0.1:8001
  Players:        4 agents on ports 8101-8104
  Rounds:         3
```

### 2. Agent Strategies
```
Agent Strategies:
  • Alpha: random
  • Beta: always_even
  • Gamma: always_odd
  • Delta: alternating
```

### 3. Tournament Progress
```
Expected total games: 18
  Progress: 7/18 games, 1/3 rounds
```

### 4. Individual Match Results
Watch for the referee's game logs:
```
🎲 Game game_abc123: Alpha vs Beta
   Alpha chose: odd
   Beta chose: even
   Dice rolled: 35 (odd)
   ✓ Winner: Alpha (correct prediction)
```

### 5. Final Standings
```
Rank   Agent           Points   W-L-D        Win Rate
----------------------------------------------------------------------
1      Alpha           18       5-1-3        55.6%
2      Beta            14       4-3-2        44.4%
3      Gamma           9        2-4-3        22.2%
4      Delta           6        0-3-6        0.0%
```

## Points System

- **Win**: 3 points
- **Draw**: 1 point
- **Loss**: 0 points

## Analyzing Strategy Performance

By watching the match decisions, you can see:
- Which strategies perform best against each other
- Pattern recognition effectiveness
- How random chance affects deterministic strategies
- Counter-strategy effectiveness

## Example Analysis

If you see:
```
🎲 Game 1: Alpha vs Beta
   Alpha chose: odd       (random strategy)
   Beta chose: even       (always_even strategy)
   Dice rolled: 42 (even)
   ✓ Winner: Beta

🎲 Game 2: Alpha vs Beta  
   Alpha chose: even      (random strategy)
   Beta chose: even       (always_even strategy)
   Dice rolled: 17 (odd)
   ⚖️  Result: DRAW (both wrong)

🎲 Game 3: Alpha vs Beta
   Alpha chose: odd       (random strategy)
   Beta chose: even       (always_even strategy)
   Dice rolled: 84 (even)
   ✓ Winner: Beta
```

You can conclude:
- Beta's deterministic `always_even` strategy won 2/3 games
- Random strategies have no inherent advantage over deterministic ones
- The dice outcome is the only factor determining winners

## Tips for Understanding Results

1. **Watch for patterns**: Does a strategy consistently beat another?
2. **Count draws**: High draw rates indicate similar strategies
3. **Check win rates**: Compare actual performance vs theoretical 50/50
4. **Note the dice distribution**: Is it truly random over many games?
5. **Observe adaptation**: Do adaptive strategies improve over time?

## Running with Verbose Output

To see all match decisions:

```bash
python scripts/run_full_league.py --rounds 3 --num-agents 4
```

The referee output is now visible by default, showing every game decision.

## Troubleshooting

If you don't see match decisions:
- Check that referee logging is set to INFO level (default)
- Ensure the referee process is running (check health endpoint)
- Verify players are registered (check `/agents` endpoint)
- Look for error messages in the output

## Advanced: Analyzing Strategy Effectiveness

To determine which strategies work best:

1. Run multiple tournaments with different agent counts
2. Note which strategies consistently rank higher
3. Compare head-to-head matchups between specific strategies
4. Calculate win rates for each strategy type across all games

Remember: With a fair dice roll, all strategies have a theoretical 50% win rate against random dice. The game tests implementation correctness, not strategic superiority.
