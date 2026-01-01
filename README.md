# Even-Odd League: Multi-Agent Competition System

A complete multi-agent system where autonomous agents play parity games. All communication uses JSON-RPC 2.0 over HTTP.

## Quick Start

### 1. Verify System Works
```bash
python3 tests/manual/test_player_manual.py
```

### 2. Start a Player Agent
```bash
python3 scripts/start_player.py \
  --port 8001 \
  --display-name "Agent1" \
  --league-url http://127.0.0.1:9000
```

### 3. Test the Agent
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

## Agent Commands

### Start a single agent
```bash
python3 scripts/start_player.py --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000
```

### Start multiple agents (different terminals)
```bash
# Terminal 1
python3 scripts/start_player.py --port 8001 --display-name "Alpha" --league-url http://127.0.0.1:9000

# Terminal 2
python3 scripts/start_player.py --port 8002 --display-name "Beta" --league-url http://127.0.0.1:9000

# Terminal 3
python3 scripts/start_player.py --port 8003 --display-name "Gamma" --league-url http://127.0.0.1:9000
```

## License

MIT
