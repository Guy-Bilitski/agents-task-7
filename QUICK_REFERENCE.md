# Quick Reference - Even-Odd League

## Three Ways to Run

### 1. All-in-One with External Referee (Easiest) ⭐ RECOMMENDED
```bash
python3 scripts/run_full_league.py
```
Automatically starts League Manager + External Referee + 4 player agents with different strategies.

**Shows agent decisions in real-time!** See [docs/UNDERSTANDING_MATCH_OUTPUT.md](docs/UNDERSTANDING_MATCH_OUTPUT.md) for details.

### 2. All-in-One with Embedded Referee (Simpler)
```bash
python3 scripts/run_league.py
```
Starts League Manager (with built-in referee) + 4 player agents.

### 3. Manager + Manual Agents (Most Flexible)
```bash
# Terminal 1: Start manager (server-only mode)
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee

# Terminal 2: Start referee
PYTHONPATH=src python3 -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000

# Terminal 3-6: Connect agents
PYTHONPATH=src python3 -m agents.player --port 8101 --display-name Agent1 --league-url http://127.0.0.1:8000 --strategy random
PYTHONPATH=src python3 -m agents.player --port 8102 --display-name Agent2 --league-url http://127.0.0.1:8000 --strategy adaptive

# Start tournament
curl -X POST http://127.0.0.1:8000/start
```

### 4. Testing Single Agent
```bash
python3 tests/manual/test_player_manual.py
```

---

## Common Commands

| Task | Command |
|------|---------|
| **Run complete league (external referee)** | `python3 scripts/run_full_league.py` ⭐ |
| **Run complete league (embedded referee)** | `python3 scripts/run_league.py` |
| **Start tournament manually** | `curl -X POST http://127.0.0.1:8000/start` |
| **Clean up all processes** | `bash scripts/cleanup.sh` |
| **Check manager health** | `curl http://127.0.0.1:8000/health` |
| **List registered agents** | `curl http://127.0.0.1:8000/agents` |
| **View standings** | `curl http://127.0.0.1:8000/standings` |

---

## Strategies

| Strategy | Behavior | Use Case |
|----------|----------|----------|
| `random` | 50/50 random | Default, unpredictable |
| `always_even` | Always even | Testing, predictable |
| `always_odd` | Always odd | Testing, predictable |
| `deterministic` | Hash-based | Reproducible tests |
| `alternating` | Switches each game | Balanced |
| `adaptive` | Learns from wins/losses | Competitive AI |
| `counter` | Tracks winning patterns | Meta-game |
| `biased_random_70` | 70% even, 30% odd | Exploitative |
| `biased_random_30` | 30% even, 70% odd | Exploitative |

Usage: `--strategy <name>`

---

## Configuration Options

### Complete System (External Referee)
```bash
python3 scripts/run_full_league.py \
  --port 9000 \                # League Manager port
  --referee-port 8001 \        # Referee port
  --num-agents 4 \             # Number of agents
  --base-agent-port 8101 \     # First agent port
  --rounds 3 \                 # Rounds per matchup
  --log-level INFO             # DEBUG|INFO|WARNING|ERROR
```

### Simplified System (Embedded Referee)
```bash
python3 scripts/run_league.py \
  --port 9000 \                # Manager port
  --num-agents 4 \             # Number of agents
  --base-agent-port 8001 \     # First agent port
  --rounds 3 \                 # Rounds per matchup
  --log-level INFO             # Log verbosity
```

### League Manager (Server-Only)
```bash
PYTHONPATH=src python3 -m agents.league_manager \
  --port 8000 \                # Manager port
  --server-only \              # Don't auto-spawn agents
  --use-external-referee \     # Use external referee
  --rounds 3                   # Rounds per matchup
```

### Player Agent
```bash
PYTHONPATH=src python3 -m agents.player \
  --port 8101 \                # Agent server port
  --display-name "Agent1" \    # Agent name
  --league-url http://127.0.0.1:8000 \  # Manager URL
  --strategy random \          # AI strategy
  --log-level INFO             # DEBUG|INFO|WARNING|ERROR
```

---

## What You'll See

When you run `python3 scripts/run_full_league.py`, you'll see:

**1. Setup Information:**
```
Configuration:
  League Manager: http://127.0.0.1:9000
  Referee:        http://127.0.0.1:8001
  Players:        4 agents on ports 8101-8104
  Rounds:         3

Agent Strategies:
  • Alpha: random
  • Beta: always_even
  • Gamma: always_odd
  • Delta: alternating
```

**2. Match Decisions (Real-Time):**
```
🎲 Game game_abc123: Alpha vs Beta
   Alpha chose: odd        (random strategy)
   Beta chose: even        (always_even strategy)
   Dice rolled: 42 (even)
   ✓ Winner: Beta (correct prediction)

🎲 Game game_def456: Gamma vs Delta
   Gamma chose: odd        (always_odd strategy)
   Delta chose: even       (alternating strategy)
   Dice rolled: 17 (odd)
   ✓ Winner: Gamma (correct prediction)
```

**3. Final Standings:**
```
Rank   Agent           Points   W-L-D        Win Rate
----------------------------------------------------------------------
1      Alpha           18       5-1-3        55.6%
2      Beta            14       4-3-2        44.4%
3      Gamma           9        2-4-3        22.2%
4      Delta           6        0-3-6        0.0%
======================================================================

🏆 CHAMPION: Alpha 🏆

Total games played: 18
Rounds completed: 3
```

**See [docs/UNDERSTANDING_MATCH_OUTPUT.md](docs/UNDERSTANDING_MATCH_OUTPUT.md) for a complete guide to reading match decisions!**

---

## Quick Examples

### Tournament with 6 agents (external referee)
```bash
python3 scripts/run_full_league.py --num-agents 6 --rounds 10
```

### Tournament with 8 agents (embedded referee)
```bash
python3 scripts/run_league.py --num-agents 8 --rounds 10
```

### Custom strategies (manual control)
```bash
# Start League Manager
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee &

# Start Referee
PYTHONPATH=src python3 -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000 &

# Start players with specific strategies
PYTHONPATH=src python3 -m agents.player --port 8101 --display-name "Learner" --league-url http://127.0.0.1:8000 --strategy adaptive &
PYTHONPATH=src python3 -m agents.player --port 8102 --display-name "Random" --league-url http://127.0.0.1:8000 --strategy random &

# Start tournament
curl -X POST http://127.0.0.1:8000/start
```

### Debug mode
```bash
python3 scripts/run_full_league.py --log-level DEBUG
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| Port in use | `bash scripts/cleanup.sh` |
| Agents won't connect | Check `--league-url` matches manager |
| Manager won't start | Use different port: `--port 9001` |
| Import errors | Run from project root |
| Timeout waiting for agents | Use `--timeout 600` or `--wait-for 0` |

---

## REST API Endpoints

Manager runs on `http://127.0.0.1:8000` (or custom port):

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/register` | POST | Agent registration |
| `/agents` | GET | List registered agents |
| `/standings` | GET | Current standings |
| `/start` | POST | **Start tournament** ⭐ NEW! |

---

## Documentation

| Guide | Topic |
|-------|-------|
| **QUICKSTART.md** | Complete beginner guide |
| **docs/START_TOURNAMENT.md** | How to start tournaments ⭐ NEW! |
| **docs/API_REFERENCE.md** | Complete API reference ⭐ NEW! |
| **docs/RUNNING_MODES.md** | Running mode comparison ⭐ NEW! |
| **docs/RUNNING_LEAGUE_MANAGER.md** | League Manager details |
| **docs/STRATEGIES.md** | AI strategy details |
| **docs/MANUAL_TESTING_GUIDE.md** | Testing with curl |

---

## Need Help?

1. Read [QUICKSTART.md](QUICKSTART.md)
2. Check [docs/RUNNING_LEAGUE_MANAGER.md](docs/RUNNING_LEAGUE_MANAGER.md)
3. Run `bash scripts/cleanup.sh` to reset
4. Make sure you're in the project root directory

---

**Ready to play?**
```bash
python3 scripts/run_full_league.py
```

**Want the simplest option?**
```bash
python3 scripts/run_league.py
```

**Want manual control?**
See [docs/START_TOURNAMENT.md](docs/START_TOURNAMENT.md)
