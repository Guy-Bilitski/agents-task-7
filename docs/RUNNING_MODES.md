# Running the League: Two Approaches

There are **two ways** to run the complete system, depending on your needs.

---

## Option 1: Complete System with External Referee ⭐ RECOMMENDED

**Script:** `scripts/run_full_league.py`

**What it does:**
- Starts League Manager
- Starts **External Referee** (separate process)
- Starts Player Agents
- Automatically runs the tournament

**Command:**
```bash
python3 scripts/run_full_league.py
```

**Architecture:**
```
┌─────────────────┐
│ League Manager  │ :9000
└────────┬────────┘
         │
         │ (delegates matches)
         │
    ┌────▼─────┐
    │ Referee  │ :8001
    └────┬─────┘
         │
         │ (runs matches)
    ┌────┴──────┬──────────┬──────────┐
    │           │          │          │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Player │  │Player │  │Player │  │Player │
│ 8101  │  │ 8102  │  │ 8103  │  │ 8104  │
└───────┘  └───────┘  └───────┘  └───────┘
```

**Pros:**
- ✅ True distributed architecture
- ✅ Referee is a separate, testable component
- ✅ Follows the MCP/JSON-RPC design spec
- ✅ Each component can be run independently
- ✅ Better for understanding the system
- ✅ Better for testing individual components

**Cons:**
- More processes to manage
- Slightly more complex

**When to use:**
- Learning the system architecture
- Testing individual components
- Building on top of the system
- Production deployments
- When you want full control

**Options:**
```bash
python3 scripts/run_full_league.py --num-agents 6       # More agents
python3 scripts/run_full_league.py --rounds 10          # More rounds
python3 scripts/run_full_league.py --log-level DEBUG    # Verbose
python3 scripts/run_full_league.py --referee-port 8050  # Custom ports
```

---

## Option 2: Simplified System with Embedded Referee

**Script:** `scripts/run_league.py`

**What it does:**
- Starts League Manager with **embedded referee**
- Starts Player Agents
- Automatically runs the tournament

**Command:**
```bash
python3 scripts/run_league.py
```

**Architecture:**
```
┌─────────────────────────┐
│ League Manager          │ :9000
│ (with embedded referee) │
└────────┬────────────────┘
         │
         │ (runs matches directly)
    ┌────┴──────┬──────────┬──────────┐
    │           │          │          │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Player │  │Player │  │Player │  │Player │
│ 8001  │  │ 8002  │  │ 8003  │  │ 8004  │
└───────┘  └───────┘  └───────┘  └───────┘
```

**Pros:**
- ✅ Simpler - fewer processes
- ✅ Faster startup
- ✅ Good for quick tests

**Cons:**
- ❌ Referee is not a separate component
- ❌ Can't test referee independently
- ❌ Not the full distributed architecture

**When to use:**
- Quick testing
- Simple demonstrations
- When you don't need separate referee control

**Options:**
```bash
python3 scripts/run_league.py --num-agents 6       # More agents
python3 scripts/run_league.py --rounds 10          # More rounds
python3 scripts/run_league.py --log-level DEBUG    # Verbose
```

---

## Side-by-Side Comparison

| Feature | External Referee | Embedded Referee |
|---------|------------------|------------------|
| **Script** | `run_full_league.py` | `run_league.py` |
| **Processes** | 4+ (LM, Referee, Players) | 3+ (LM+Referee, Players) |
| **Architecture** | Distributed | Monolithic |
| **Referee Control** | Full (separate process) | None (internal) |
| **Startup Time** | ~3-5 seconds | ~2-3 seconds |
| **Testing** | Can test each component | Limited |
| **Recommended For** | Production, Learning | Quick tests |
| **Complexity** | Medium | Low |

---

## Manual Control Mode (Advanced)

For **full manual control**, run each component separately:

### 1. Start League Manager (server-only mode)
```bash
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee
```

### 2. Start Referee
```bash
PYTHONPATH=src python3 -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000
```

### 3. Start Players (as many as you want)
```bash
PYTHONPATH=src python3 -m agents.player --port 8101 --display-name Alpha --league-url http://127.0.0.1:8000
PYTHONPATH=src python3 -m agents.player --port 8102 --display-name Beta --league-url http://127.0.0.1:8000
```

### 4. Check registration
```bash
curl http://127.0.0.1:8000/agents
```

### 5. Start the tournament manually
```bash
curl -X POST http://127.0.0.1:8000/start
```

See [docs/START_TOURNAMENT.md](docs/START_TOURNAMENT.md) for complete manual control guide.

---

## Quick Decision Guide

**Just want to see it work?**
→ Use `run_full_league.py`

**Want to understand the architecture?**
→ Use `run_full_league.py` or manual mode

**Want to test individual components?**
→ Use manual mode

**Need the simplest possible setup?**
→ Use `run_league.py`

**Building a production system?**
→ Use external referee architecture (`run_full_league.py`)

---

## Summary

- **`run_full_league.py`** - Complete system, external referee, recommended ⭐
- **`run_league.py`** - Simplified system, embedded referee, good for quick tests
- **Manual mode** - Full control, start each component separately

Most users should use **`run_full_league.py`** for the best experience!
