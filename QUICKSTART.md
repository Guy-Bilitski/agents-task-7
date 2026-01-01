# Quick Start Guide

Get the Even-Odd League running in minutes.

---

## Option 1: One-Command Start (Easiest) ⭐

Run the complete system with external referee:

```bash
python3 scripts/run_full_league.py
```

**That's it!** The system will:
1. Start League Manager on `http://127.0.0.1:9000`
2. Start External Referee on `http://127.0.0.1:8001`
3. Spawn 4 player agents with different strategies (ports 8101-8104)
4. Run a complete tournament
5. Display final standings

**Customize:**
```bash
# More agents
python3 scripts/run_full_league.py --num-agents 6

# More rounds per matchup
python3 scripts/run_full_league.py --rounds 10

# Verbose logging
python3 scripts/run_full_league.py --log-level DEBUG
```

**Alternative (simpler, embedded referee):**
```bash
python3 scripts/run_league.py
```

---

## Option 2: Manual Control (Full Flexibility)

### Step 1: Start League Manager

```bash
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee
```

**Verify it's running:**
```bash
curl http://127.0.0.1:8000/health
# Expected: {"ok":true}
```

### Step 2: Start Referee

```bash
PYTHONPATH=src python3 -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000
```

### Step 3: Start Player Agents

Open separate terminals for each agent:

```bash
# Terminal 1
PYTHONPATH=src python3 -m agents.player --port 8101 --display-name "Alpha" --league-url http://127.0.0.1:8000 --strategy random

# Terminal 2
PYTHONPATH=src python3 -m agents.player --port 8102 --display-name "Beta" --league-url http://127.0.0.1:8000 --strategy adaptive

# Terminal 3
PYTHONPATH=src python3 -m agents.player --port 8103 --display-name "Gamma" --league-url http://127.0.0.1:8000 --strategy counter

# Terminal 4
PYTHONPATH=src python3 -m agents.player --port 8104 --display-name "Delta" --league-url http://127.0.0.1:8000 --strategy always_even
```

### Step 4: Verify Registration

```bash
curl http://127.0.0.1:8000/agents
```

You should see all 4 agents plus the referee listed.

### Step 5: Start Tournament

```bash
curl -X POST http://127.0.0.1:8000/start
```

### Step 6: Monitor Progress

```bash
curl http://127.0.0.1:8000/standings
```

---

## What You'll See

When running `python3 scripts/run_full_league.py`, you'll see:

**1. Configuration:**
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

See [docs/UNDERSTANDING_MATCH_OUTPUT.md](docs/UNDERSTANDING_MATCH_OUTPUT.md) for details on reading match decisions.

---

## Available Strategies

| Strategy | Behavior |
|----------|----------|
| `random` | 50/50 random (default) |
| `always_even` | Always chooses even |
| `always_odd` | Always chooses odd |
| `alternating` | Switches each game |
| `adaptive` | Learns from wins/losses |
| `counter` | Tracks opponent patterns |
| `deterministic` | Hash-based, reproducible |
| `biased_random_70` | 70% even, 30% odd |
| `biased_random_30` | 30% even, 70% odd |

Usage: `--strategy <name>`

See [docs/STRATEGIES.md](docs/STRATEGIES.md) for detailed information.

---

## Troubleshooting

### "Address already in use"

Clean up old processes:
```bash
bash scripts/cleanup.sh
```

Or manually:
```bash
lsof -i :9000
kill <PID>
```

### Import Errors

Make sure you're in the project root directory:
```bash
cd /path/to/agents-task7
python3 scripts/run_full_league.py
```

### League Manager Won't Start

Try running directly as a module:
```bash
PYTHONPATH=src python3 -m agents.league_manager
```

### Agents Won't Register

1. Verify League Manager is running:
   ```bash
   curl http://127.0.0.1:8000/health
   ```

2. Check agent logs in the terminal

3. Make sure the `--league-url` parameter matches:
   ```bash
   --league-url http://127.0.0.1:8000
   ```

---

## System Architecture

```
┌─────────────────┐
│  League Manager │  :9000 (Orchestration, REST API)
└────────┬────────┘
         │ JSON-RPC 2.0
    ┌────▼─────┐
    │ Referee  │  :8001 (Match execution)
    └────┬─────┘
         │ JSON-RPC 2.0
    ┌────┴──────┬──────────┬──────────┐
┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Player │  │Player │  │Player │  │Player │
│ 8101  │  │ 8102  │  │ 8103  │  │ 8104  │
└───────┘  └───────┘  └───────┘  └───────┘
```

**Communication:** All components use JSON-RPC 2.0 over HTTP

---

## Common Commands

```bash
# Run complete system
python3 scripts/run_full_league.py

# Run with more agents
python3 scripts/run_full_league.py --num-agents 8

# Run more rounds
python3 scripts/run_full_league.py --rounds 10

# Debug mode
python3 scripts/run_full_league.py --log-level DEBUG

# Check status
curl http://127.0.0.1:9000/health
curl http://127.0.0.1:9000/agents
curl http://127.0.0.1:9000/standings

# Start tournament (manual mode)
curl -X POST http://127.0.0.1:9000/start

# Clean up
bash scripts/cleanup.sh

# Run tests
pytest tests/
```

---

## Next Steps

- Read [docs/START_TOURNAMENT.md](docs/START_TOURNAMENT.md) for detailed tournament guide
- Read [docs/RUNNING_MODES.md](docs/RUNNING_MODES.md) to compare running modes
- Read [docs/API_REFERENCE.md](docs/API_REFERENCE.md) for complete API documentation
- Modify player strategies in `src/agents/player/strategy.py`
- Run tests: `pytest tests/`

---

## Need Help?

1. Check [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)
2. Run `bash scripts/cleanup.sh` to reset
3. Make sure you're in the project root directory
4. See [docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md) for curl examples

---

**Ready to play?**
```bash
python3 scripts/run_full_league.py
```
