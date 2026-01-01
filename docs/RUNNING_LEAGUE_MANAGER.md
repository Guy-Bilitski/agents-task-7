# Running League Manager Only - Waiting for Competitors

This guide shows how to run **just the League Manager** so it waits for competitors to connect manually.

---

## Quick Start (Recommended - Server-Only Mode)

### Using the Module Directly (Simplest)

```bash
cd /path/to/agents-task7
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only
```

This starts the League Manager in **server-only mode**:
- ✅ Starts the server and waits for registrations
- ✅ Does NOT spawn any agents automatically  
- ✅ Does NOT auto-start the league
- ✅ You start each component (referee, players) separately
- ✅ Runs until you press Ctrl+C

### With External Referee

```bash
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee
```

---

## Alternative: Using Scripts

### Option 1: Wait for Specific Number of Agents (Automatic Start)

```bash
# Wait for 4 agents, then automatically start
python3 scripts/start_league_manager.py --wait-for 4
```

When 4 agents connect, the league automatically starts!

### Option 2: Wait Indefinitely (Manual Start)

```bash
# Wait for any number of agents, manual start
python3 scripts/start_league_manager.py --wait-for 0
```

Press **Ctrl+C** when you're ready, and it will start with however many agents are connected.

### Option 3: Wait and Press ENTER to Start

```bash
# No auto-start, wait for ENTER key
python3 scripts/start_league_manager.py --wait-for 0 --no-auto-start
```

---

## Full Workflow Example (Server-Only Mode with Manual Start)

### Step 1: Start League Manager
```bash
cd /path/to/agents-task7
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee --rounds 5
```

Output:
```
League Configuration:
  Manager Port: 8000
  Mode: Server-Only
  Referee: External
  Rounds per Matchup: 5

============================================================
SERVER RUNNING IN SERVER-ONLY MODE
============================================================

Endpoints:
  Health:   http://127.0.0.1:8000/health
  Register: http://127.0.0.1:8000/register
  Agents:   http://127.0.0.1:8000/agents
  Standings: http://127.0.0.1:8000/standings

The server will accept registrations from:
  - Referee (external)
  - Player agents

Press Ctrl+C to stop
```

### Terminal 2: Start Referee
```bash
cd /path/to/agents-task7
PYTHONPATH=src python3 -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000
```

Output:
```
Referee MCP Server starting on http://127.0.0.1:8001
✓ Registered with League Manager: Referee Referee registered successfully
```

### Terminal 3-6: Start Players

**Terminal 3:**
```bash
cd /path/to/agents-task7
PYTHONPATH=src python3 -m agents.player --port 8101 --display-name Alpha --league-url http://127.0.0.1:8000 --strategy random
```

**Terminal 4:**
```bash
PYTHONPATH=src python3 -m agents.player --port 8102 --display-name Beta --league-url http://127.0.0.1:8000 --strategy always_even
```

**Terminal 5:**
```bash
PYTHONPATH=src python3 -m agents.player --port 8103 --display-name Gamma --league-url http://127.0.0.1:8000 --strategy adaptive
```

**Terminal 6:**
```bash
PYTHONPATH=src python3 -m agents.player --port 8104 --display-name Delta --league-url http://127.0.0.1:8000 --strategy counter
```

### Step 2: Verify All Agents Are Registered
```bash
curl http://127.0.0.1:8000/agents
```

You should see the referee and all players listed.

### Step 3: Start the Tournament!
```bash
curl -X POST http://127.0.0.1:8000/start
```

Response:
```json
{
  "status": "started",
  "agents": 2,
  "rounds": 5,
  "message": "League starting with 2 agents"
}
```

The tournament will now run! Watch the League Manager terminal for match results and standings.

---

## Full Workflow Example (Script-Based - Legacy)

### Terminal 1: Start League Manager
```bash
python3 scripts/start_league_manager.py --wait-for 4 --rounds 5
```

Output:
```
======================================================================
  LEAGUE MANAGER - Waiting for Competitors
======================================================================
  Port: 9000
  Waiting for: 4 agents
  Rounds: 5
  Timeout: 300s
======================================================================

✓ League Manager running on http://127.0.0.1:9000

Endpoints:
  Registration: http://127.0.0.1:9000/register
  Health check: http://127.0.0.1:9000/health
  Agents list:  http://127.0.0.1:9000/agents
  Standings:    http://127.0.0.1:9000/standings

Connect your agents:
  python scripts/start_player.py --port 8001 --display-name Agent1 --league-url http://127.0.0.1:9000 --strategy random

Waiting for 4 agents to connect (timeout: 300s)...
```

### Terminal 2-5: Connect Your Agents

**Terminal 2:**
```bash
python3 scripts/start_player.py \
  --port 8001 \
  --display-name "Alpha" \
  --league-url http://127.0.0.1:9000 \
  --strategy random
```

**Terminal 3:**
```bash
python3 scripts/start_player.py \
  --port 8002 \
  --display-name "Beta" \
  --league-url http://127.0.0.1:9000 \
  --strategy adaptive
```

**Terminal 4:**
```bash
python3 scripts/start_player.py \
  --port 8003 \
  --display-name "Gamma" \
  --league-url http://127.0.0.1:9000 \
  --strategy counter
```

**Terminal 5:**
```bash
python3 scripts/start_player.py \
  --port 8004 \
  --display-name "Delta" \
  --league-url http://127.0.0.1:9000 \
  --strategy alternating
```

### What Happens

1. Each agent connects and registers automatically
2. League Manager shows: `1/4 agents connected...`, `2/4 agents connected...`, etc.
3. When 4th agent connects: `✓ All 4 agents connected!`
4. League automatically starts!
5. Games run, standings update
6. Final results displayed

---

## Command Options

### Using Module Directly (Recommended)

```bash
PYTHONPATH=src python3 -m agents.league_manager [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--port PORT` | League Manager port | 9000 |
| `--server-only` | Run as server only (don't spawn agents) | False |
| `--use-external-referee` | Use external referee instead of embedded | False |
| `--rounds N` | Rounds per matchup | 3 |
| `--log-level LEVEL` | DEBUG, INFO, WARNING, ERROR | INFO |
| `--num-agents N` | Number of agents to spawn (auto mode only) | 4 |
| `--base-agent-port PORT` | First agent port (auto mode only) | 8001 |

**Examples:**

```bash
# Server-only with external referee
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee

# Server-only with embedded referee  
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only

# Auto mode - spawns 6 agents and runs league
PYTHONPATH=src python3 -m agents.league_manager --num-agents 6 --rounds 10
```

### Using Scripts (Legacy)

```bash
python3 scripts/start_league_manager.py [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--port` | League Manager port | 9000 |
| `--wait-for` | Number of agents to wait for (0 = infinite) | 4 |
| `--rounds` | Rounds per matchup | 3 |
| `--timeout` | Max wait time in seconds | 300 (5 min) |
| `--auto-start` | Auto-start when enough agents connect | True (if wait-for > 0) |

---

## Examples

### Example 1: Tournament Setup (6 agents, 10 rounds)
```bash
python3 scripts/start_league_manager.py --wait-for 6 --rounds 10 --timeout 600
```

### Example 2: Quick Test (2 agents, 1 round)
```bash
python3 scripts/start_league_manager.py --wait-for 2 --rounds 1
```

### Example 3: Manual Control
```bash
# Start manager, wait indefinitely
python3 scripts/start_league_manager.py --wait-for 0

# In other terminals, connect agents
# When ready, press Ctrl+C in manager terminal
# It will then start the league with connected agents
```

### Example 4: Custom Port
```bash
# Start on different port
python3 scripts/start_league_manager.py --port 9001 --wait-for 4

# Agents must connect to this URL:
python3 scripts/start_player.py --port 8001 --display-name Agent1 --league-url http://127.0.0.1:9001
```

---

## Monitoring the League

While the League Manager is running, you can check status via REST API:

### Check registered agents
```bash
curl http://127.0.0.1:9000/agents
```

Response:
```json
{
  "agents": [
    {
      "display_name": "Alpha",
      "version": "1.0.0",
      "endpoint": "http://127.0.0.1:8001/mcp"
    },
    {
      "display_name": "Beta",
      "version": "1.0.0",
      "endpoint": "http://127.0.0.1:8002/mcp"
    }
  ]
}
```

### Check health
```bash
curl http://127.0.0.1:9000/health
```

Response:
```json
{
  "ok": true,
  "registered_agents": 4,
  "total_games": 0
}
```

### Start the league (NEW!)
Once you have at least 2 agents registered, you can start the tournament:

```bash
curl -X POST http://127.0.0.1:9000/start
```

Response:
```json
{
  "status": "started",
  "agents": 2,
  "rounds": 3,
  "message": "League starting with 2 agents"
}
```

If you try to start with fewer than 2 agents:
```json
{
  "error": "Need at least 2 agents to start league"
}
```

If league is already running:
```json
{
  "error": "League is already running"
}
```

### View standings (during or after league)
```bash
curl http://127.0.0.1:9000/standings
```

Response:
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
    }
  ],
  "total_games": 6,
  "rounds_completed": 1
}
```

---

## Troubleshooting

### "Address already in use"
Something is already on port 9000:
```bash
# Clean up
bash scripts/cleanup.sh

# Or use different port
python3 scripts/start_league_manager.py --port 9001
```

### Agents not connecting
1. **Check the league URL** - Agents must use exact URL:
   ```bash
   --league-url http://127.0.0.1:9000
   ```

2. **Check agent is running**:
   ```bash
   curl http://127.0.0.1:8001/health
   ```

3. **Check registration endpoint**:
   ```bash
   curl http://127.0.0.1:9000/agents
   ```

### Timeout reached
If timeout expires before enough agents connect:
```
Only 2/4 agents connected. Starting with 2 agents...
```

To avoid this:
- Use longer timeout: `--timeout 600`
- Use `--wait-for 0` to wait indefinitely

### Need at least 2 agents
League requires minimum 2 agents. If only 1 connects:
```
Need at least 2 agents to run league. Only 1 connected.
```

---

## Integration with External Agents

You can connect agents from anywhere, even other machines!

### From Another Machine

**On Machine A (League Manager):**
```bash
# Start with accessible host
python3 scripts/start_league_manager.py --wait-for 4

# Note: You may need to bind to 0.0.0.0 for external access
# (requires code modification)
```

**On Machine B (Player Agent):**
```bash
python3 scripts/start_player.py \
  --port 8001 \
  --display-name "RemoteAgent" \
  --league-url http://MACHINE_A_IP:9000 \
  --strategy random
```

### From a Different Language

Any agent that implements the JSON-RPC 2.0 protocol can connect!

1. **Register** via `POST http://127.0.0.1:9000/register`
2. **Implement** the required MCP methods:
   - `handle_game_invitation`
   - `choose_parity` (or `parity_choose`)
   - `notify_match_result`
3. **Expose** an HTTP server with `POST /mcp` endpoint

See [docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md) for protocol details.

---

## Advanced: Using with Docker

### Run League Manager in Docker
```bash
docker run -p 9000:9000 your-league-manager
```

### Connect local agents
```bash
python3 scripts/start_player.py \
  --port 8001 \
  --display-name "Agent1" \
  --league-url http://localhost:9000
```

---

## Summary

| Use Case | Command |
|----------|---------|
| **Wait for 4 agents** | `python3 scripts/start_league_manager.py --wait-for 4` |
| **Wait indefinitely** | `python3 scripts/start_league_manager.py --wait-for 0` |
| **Tournament (6 agents, 10 rounds)** | `python3 scripts/start_league_manager.py --wait-for 6 --rounds 10` |
| **Quick test (2 agents)** | `python3 scripts/start_league_manager.py --wait-for 2 --rounds 1` |
| **Custom port** | `python3 scripts/start_league_manager.py --port 9001` |

**After starting, connect agents in separate terminals!** 🎮
