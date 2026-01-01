# How to Start a Tournament

## Quick Answer

Once you have a League Manager running with at least 2 registered player agents:

```bash
curl -X POST http://127.0.0.1:8000/start
```

(Replace `8000` with your League Manager port)

---

## Complete Step-by-Step Guide

### Step 1: Start the League Manager in Server-Only Mode

```bash
cd /path/to/agents-task7
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee
```

**What this does:**
- Starts the League Manager on port 8000
- Waits for agents to register
- Does NOT auto-start the tournament
- Uses external referee (you'll start it separately)

---

### Step 2: Start the Referee

In a new terminal:

```bash
cd /path/to/agents-task7
PYTHONPATH=src python3 -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000
```

The referee will automatically register with the League Manager.

---

### Step 3: Start Player Agents

In separate terminals, start at least 2 players:

**Terminal 3:**
```bash
cd /path/to/agents-task7
PYTHONPATH=src python3 -m agents.player --port 8101 --display-name Alpha --league-url http://127.0.0.1:8000 --strategy random
```

**Terminal 4:**
```bash
cd /path/to/agents-task7
PYTHONPATH=src python3 -m agents.player --port 8102 --display-name Beta --league-url http://127.0.0.1:8000 --strategy adaptive
```

Each player will automatically register with the League Manager.

---

### Step 4: Verify Registration

Check that all agents are registered:

```bash
curl http://127.0.0.1:8000/agents
```

**Expected response:**
```json
{
  "agents": [
    {
      "display_name": "Alpha",
      "version": "1.0.0",
      "endpoint": "http://127.0.0.1:8101/mcp"
    },
    {
      "display_name": "Beta",
      "version": "1.0.0",
      "endpoint": "http://127.0.0.1:8102/mcp"
    }
  ]
}
```

You should see at least 2 players listed.

---

### Step 5: Start the Tournament! 🎮

```bash
curl -X POST http://127.0.0.1:8000/start
```

**Expected response:**
```json
{
  "status": "started",
  "agents": 2,
  "rounds": 3,
  "message": "League starting with 2 agents"
}
```

---

### Step 6: Watch the Tournament

The League Manager terminal will show:
- Match announcements
- Player choices
- Dice rolls
- Winners
- Updated standings after each round

---

### Step 7: View Standings

During or after the tournament:

```bash
curl http://127.0.0.1:8000/standings
```

**Expected response:**
```json
{
  "standings": [
    {
      "rank": 1,
      "agent": "Alpha",
      "points": 9,
      "wins": 3,
      "losses": 0,
      "draws": 0,
      "games_played": 3,
      "win_rate": "100.0%"
    },
    {
      "rank": 2,
      "agent": "Beta",
      "points": 0,
      "wins": 0,
      "losses": 3,
      "draws": 0,
      "games_played": 3,
      "win_rate": "0.0%"
    }
  ],
  "total_games": 3,
  "rounds_completed": 3
}
```

---

## Error Messages

### "Need at least 2 agents to start league"

**Problem:** You tried to start with fewer than 2 players registered.

**Solution:** Start more player agents, then try again:
```bash
curl http://127.0.0.1:8000/agents  # Check how many are registered
```

---

### "League is already running"

**Problem:** The tournament has already been started.

**Solution:** Wait for it to complete, then check standings:
```bash
curl http://127.0.0.1:8000/standings
```

---

## Alternative: Auto-Start Mode

If you don't want to manually trigger the tournament, use auto mode:

```bash
# Start League Manager that auto-runs when 4 agents connect
PYTHONPATH=src python3 -m agents.league_manager --num-agents 4 --rounds 5
```

This will:
1. Start the League Manager
2. Spawn 4 player agents automatically
3. Run the tournament automatically
4. Show final standings

---

## Summary

**Manual start workflow:**
1. Start League Manager with `--server-only`
2. Start referee (if using `--use-external-referee`)
3. Start player agents
4. Verify registration: `curl http://127.0.0.1:8000/agents`
5. **Start tournament: `curl -X POST http://127.0.0.1:8000/start`**
6. Watch results and view standings

**Key insight:** The `/start` endpoint is what triggers the tournament to begin!

---

## See Also

- [RUNNING_LEAGUE_MANAGER.md](RUNNING_LEAGUE_MANAGER.md) - Detailed League Manager guide
- [QUICKSTART.md](../QUICKSTART.md) - Quick start for the entire system
- [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) - Testing with curl commands
