# Running the Agents

## Quick Start

### Option 1: Run the Complete League System

The easiest way to run everything:

```bash
python3 scripts/run_league.py
```

This automatically:
- Starts the League Manager on port 9000
- Spawns 4 player agents (ports 8101-8104)
- Runs matches and displays standings

**With options:**
```bash
python3 scripts/run_league.py --num-agents 6    # 6 agents
python3 scripts/run_league.py --rounds 5        # 5 rounds per match
python3 scripts/run_league.py --log-level DEBUG # Verbose logging
```

### Option 2: Run Components Separately

#### Step 1: Start the League Manager

```bash
python3 scripts/start_league_manager.py
```

**Or with custom port:**
```bash
python3 scripts/start_league_manager.py --port 9000
```

**Verify it's running:**
```bash
curl http://127.0.0.1:9000/health
# Expected: {"ok":true}
```

The League Manager provides:
- Agent registration endpoint
- Match scheduling and execution (referee functionality)
- Standings tracking
- REST API at `/health`, `/agents`, `/standings`

#### Step 2: Start Player Agents

Now start your player agents in separate terminals:

**Terminal 1:**
```bash
python3 scripts/start_player.py --port 8001 --display-name "Alpha" --league-url http://127.0.0.1:9000
```

**Terminal 2:**
```bash
python3 scripts/start_player.py --port 8002 --display-name "Beta" --league-url http://127.0.0.1:9000
```

**Terminal 3:**
```bash
python3 scripts/start_player.py --port 8003 --display-name "Gamma" --league-url http://127.0.0.1:9000
```

**Terminal 4:**
```bash
python3 scripts/start_player.py --port 8004 --display-name "Delta" --league-url http://127.0.0.1:9000
```

**Check registered agents:**
```bash
curl http://127.0.0.1:9000/agents
```

### Option 3: Test a Single Player Agent

For development and testing without the League Manager:

```bash
python3 tests/manual/test_player_manual.py
```

Or start a single agent manually:
```bash
python3 scripts/start_player.py --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000
```

## Testing Agents with curl

### Health Check
```bash
curl http://127.0.0.1:8001/health
```

### Send Game Invitation
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "handle_game_invitation",
    "params": {
      "game_id": "game_001",
      "from_player": "referee",
      "invitation_id": "inv_001"
    }
  }'
```

### Request Parity Choice
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "parity_choose",
    "params": {
      "game_id": "game_001"
    }
  }'
```

### Notify Match Result
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "notify_match_result",
    "params": {
      "game_id": "game_001",
      "winner": "Agent1",
      "details": {"rolled": 7, "parity": "odd"}
    }
  }'
```

## Agent Options

```bash
python3 scripts/start_player.py \
  --port <PORT> \
  --display-name <NAME> \
  --league-url <URL> \
  --log-level <LEVEL>
```

- `--port`: Server port (default: 8001)
- `--display-name`: Agent name (required)
- `--league-url`: League manager URL (required)
- `--log-level`: DEBUG, INFO, WARNING, ERROR (default: INFO)

## Troubleshooting

### Port Already in Use
```bash
# Find process
lsof -i :8001

# Kill it
kill -9 <PID>
```

### Stop an Agent
Press `Ctrl+C` once for graceful shutdown.

Press `Ctrl+C` twice for immediate stop.

## Documentation

- **MANUAL_TESTING_GUIDE.md** - Detailed testing instructions with more examples
- **PROJECT_STRUCTURE.md** - System architecture and design
- **validation-checklist.md** - Compliance requirements
