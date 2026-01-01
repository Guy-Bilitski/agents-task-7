# Even-Odd League: Multi-Agent Competition System

A complete multi-agent system where autonomous agents play parity games. All communication uses JSON-RPC 2.0 over HTTP.

## Quick Start

### Option 1: Run the Complete League (Easiest)

Run the entire system with one command:

```bash
python3 scripts/run_league.py
```

This automatically:
- Starts the League Manager on port 9000
- Spawns 4 player agents (ports 8101-8104)
- Runs a full competition with matches
- Displays final standings

**Custom options:**
```bash
python3 scripts/run_league.py --num-agents 6    # Run with 6 agents
python3 scripts/run_league.py --rounds 5        # 5 rounds per matchup
python3 scripts/run_league.py --log-level DEBUG # Verbose logging
```

### Option 2: Run Components Separately

**Step 1: Start the League Manager**
```bash
python3 scripts/start_league_manager.py
```

The League Manager runs on `http://127.0.0.1:9000` and handles:
- Agent registration
- Match scheduling
- Running matches (referee functionality)
- Maintaining standings

**Verify it's running:**
```bash
curl http://127.0.0.1:9000/health
```

**Step 2: Start Your Player Agents** (in separate terminals)
```bash
# Terminal 1
python3 scripts/start_player.py --port 8001 --display-name "Alpha" --league-url http://127.0.0.1:9000

# Terminal 2
python3 scripts/start_player.py --port 8002 --display-name "Beta" --league-url http://127.0.0.1:9000

# Terminal 3
python3 scripts/start_player.py --port 8003 --display-name "Gamma" --league-url http://127.0.0.1:9000

# Terminal 4
python3 scripts/start_player.py --port 8004 --display-name "Delta" --league-url http://127.0.0.1:9000
```

**Check registered agents:**
```bash
curl http://127.0.0.1:9000/agents
```

### Option 3: Test a Single Player Agent

**Start one agent:**
```bash
python3 scripts/start_player.py \
  --port 8001 \
  --display-name "Agent1" \
  --league-url http://127.0.0.1:9000
```

**Test it manually:**
```bash
# Health check
curl http://127.0.0.1:8001/health

# Send game invitation
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "handle_game_invitation",
    "params": {"game_id": "g1", "from_player": "test"}
  }'
```

**Run automated verification:**
```bash
python3 tests/manual/test_player_manual.py
```

## Project Structure

```
.
├── docs/                      # Documentation
│   ├── RUNNING_AGENTS.md     # How to run agents
│   ├── MANUAL_TESTING_GUIDE.md
│   └── PROJECT_STRUCTURE.md
│
├── scripts/                   # Convenience scripts
│   ├── start_player.py       # Start a player agent
│   ├── start_league_manager.py
│   └── run_league.py
│
├── src/                       # Source code
│   ├── agents/
│   │   ├── player/           # Player agent (fully implemented)
│   │   ├── league_manager/   # League orchestrator
│   │   └── referee/          # Match runner
│   └── shared/               # Shared utilities
│       └── jsonrpc.py        # JSON-RPC 2.0 protocol
│
└── tests/                     # Tests
    ├── manual/
    │   └── test_player_manual.py
    └── test_*.py              # Unit tests
```

## Documentation

- **[docs/RUNNING_AGENTS.md](docs/RUNNING_AGENTS.md)** - Quick start guide
- **[docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md)** - Detailed examples with curl
- **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Architecture overview

## Features

✅ **Player Agent** - Fully operational
- JSON-RPC 2.0 endpoint at `POST /mcp`
- Health check at `GET /health`
- Required methods: `handle_game_invitation`, `parity_choose`, `notify_match_result`
- Background registration with exponential backoff
- Thread-safe state management

✅ **Protocol Compliance**
- Strict JSON-RPC 2.0 specification
- All standard error codes (-32700 through -32603)
- Method aliasing support
- Extra fields accepted and stored

## Requirements

- Python 3.10+
- Dependencies: `fastapi`, `uvicorn`, `httpx`, `requests`

```bash
pip install fastapi uvicorn httpx requests
```

## System Components

### League Manager
The League Manager is the central orchestrator that:
- Accepts agent registrations via JSON-RPC
- Creates match schedules (round-robin)
- Runs matches (acts as referee)
- Maintains standings and persists league data
- Provides REST API for status: `/health`, `/agents`, `/standings`

**Default port:** 9000

### Player Agents
Player agents are autonomous bots that:
- Register with the League Manager on startup
- Respond to game invitations
- Make parity choices (even/odd)
- Receive match results and update statistics
- Expose JSON-RPC 2.0 endpoints at `POST /mcp`

**Default ports:** 8001-8104

### Referee
The referee functionality is **integrated into the League Manager**, not a separate service.

## Player Agent Options

```bash
python3 scripts/start_player.py \
  --port <PORT> \
  --display-name <NAME> \
  --league-url <URL> \
  --log-level <LEVEL>
```

- `--port`: Server port (default: 8001)
- `--display-name`: Agent name (required)
- `--league-url`: League Manager URL (required)
- `--log-level`: DEBUG, INFO, WARNING, ERROR (default: INFO)

## Troubleshooting

### Port Already in Use
```bash
# Find process using the port
lsof -i :8001

# Kill it
kill -9 <PID>
```

### League Manager Won't Start
```bash
# Try using Python module syntax
python3 -m agents.league_manager

# Or use the all-in-one script
python3 scripts/run_league.py
```

### Agents Not Registering
- Ensure League Manager is running first
- Check the `--league-url` matches the League Manager's address
- Verify connectivity: `curl http://127.0.0.1:9000/health`
- Enable debug logging: `--log-level DEBUG`

## License

MIT
