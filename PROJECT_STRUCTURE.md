# Parity League - Project Structure

## Overview

This is a distributed multi-agent league system implementing the Even-Odd game using JSON-RPC 2.0 over HTTP.

## Directory Structure

```
.
├── .opencode/                      # OpenCode agent configuration
│   └── agent/
│       ├── python_engineer.md      # Main engineering spec
│       └── tasks/                  # Step-by-step implementation milestones
│           ├── 00-overview.md
│           ├── 01-milestone-a-skeleton.md
│           ├── 02-milestone-b-http-server.md
│           ├── 03-milestone-c-jsonrpc-core.md
│           ├── 04-milestone-d-tool-routing.md
│           ├── 05-milestone-e-state-and-tool-behavior.md
│           ├── 06-milestone-f-registration.md
│           ├── 07-milestone-g-tests.md
│           └── 08-milestone-h-selftest.md
│
├── src/                            # Main source code directory
│   ├── __init__.py
│   │
│   ├── agents/                     # All agents (player, league_manager, referee)
│   │   ├── __init__.py
│   │   │
│   │   ├── player/                 # Player agent implementation
│   │   │   ├── __init__.py         # Logging setup, version
│   │   │   ├── __main__.py         # Entry point: python -m src.agents.player
│   │   │   ├── app.py              # FastAPI server: POST /mcp, GET /health
│   │   │   ├── config.py           # CLI args + env config
│   │   │   ├── main.py             # Main function, server startup
│   │   │   ├── registration.py     # Background league registration
│   │   │   ├── state.py            # In-memory state + threading lock
│   │   │   ├── strategy.py         # Parity choice logic (deterministic)
│   │   │   ├── tools.py            # JSON-RPC tool handlers
│   │   │   └── selftest.py         # Self-test harness (4 agents + simulator)
│   │   │
│   │   ├── league_manager/         # League orchestrator
│   │   │   ├── __init__.py
│   │   │   ├── __main__.py         # Entry point: python -m src.agents.league_manager
│   │   │   ├── app.py              # FastAPI server for league (placeholder)
│   │   │   ├── config.py           # League configuration
│   │   │   ├── manager.py          # Core LeagueManager class
│   │   │   └── tools.py            # JSON-RPC methods (register_*, create_schedule, etc.)
│   │   │
│   │   └── referee/                # Match orchestrator
│   │       ├── __init__.py
│   │       ├── app.py              # Optional MCP server (ping + health)
│   │       ├── client.py           # HTTP client for calling players + LM
│   │       ├── main.py             # Entry point: python -m src.agents.referee
│   │       └── referee.py          # Match runner logic (Agent, GameResult, Referee)
│   │
│   └── shared/                     # Shared utilities
│       ├── __init__.py
│       ├── http.py                 # HTTP client helpers (timeouts, retries)
│       ├── jsonrpc.py              # JSON-RPC 2.0 parsing, validation, errors
│       ├── logging.py              # StructuredLogger + JsonLogger (JSONL)
│       ├── models.py               # Dataclasses/Pydantic models for messages
│       └── repositories/           # Data persistence
│           ├── __init__.py
│           ├── match_repo.py
│           ├── player_history_repo.py
│           ├── rounds_repo.py
│           └── standings_repo.py
│
├── SHARED/                         # Shared runtime data (not in src/)
│   ├── config/
│   │   └── defaults/
│   │       ├── player.json         # Default player config
│   │       └── referee.json        # Default referee config
│   ├── data/
│   │   └── leagues/
│   │       └── <league_id>/        # Per-league data (runtime)
│   │           ├── standings.json
│   │           ├── rounds.json
│   │           └── ...
│   └── logs/
│       ├── system/                 # System-wide JSONL logs
│       └── league/                 # Per-league JSONL logs
│           └── <league_id>/
│
├── tests/                          # Test suite
│   ├── __init__.py
│   ├── mock_league.py              # Mock league server for testing
│   ├── test_jsonrpc.py             # JSON-RPC validation tests
│   ├── test_tools.py               # Tool handler tests
│   ├── test_state.py               # State management tests
│   ├── test_state_integration.py   # State integration tests
│   ├── test_registration.py        # Registration tests
│   └── test_integration_http.py    # HTTP integration tests
│
├── pyproject.toml                  # Python project config
├── pytest.ini                      # Pytest configuration
├── README.md                       # Project documentation
├── run_league.py                   # Convenience script to run a local league
└── validation-checklist.md         # Pre-submission checklist

```

## Component Responsibilities

### Player Agent (`src/agents/player/`)

**Purpose**: Autonomous agent that participates in league matches.

**Entry Point**: `python -m src.agents.player --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000`

**JSON-RPC Methods (Tools)**:
- `handle_game_invitation` - Accept game invitations
- `parity_choose` (alias: `choose_parity`) - Return parity choice (even/odd)
- `notify_match_result` - Receive match results and update stats
- `ping` - Health check

**Key Features**:
- Background registration to league manager with retries
- In-memory state with thread-safe locking
- Deterministic strategy (can be extended to LLM-based)
- Never crashes on bad input
- Self-test harness for local validation

---

### League Manager (`src/agents/league_manager/`)

**Purpose**: Central orchestrator for the league competition.

**Entry Point**: `python -m src.agents.league_manager --port 9000`

**JSON-RPC Methods**:
- `register_referee` - Register referee
- `register_player` - Register player agent
- `create_schedule` - Create round-robin schedule
- `report_match_result` - Receive match results from referee
- `get_standings` (alias: `league_query`) - Get current standings

**Key Features**:
- Tracks agent registrations
- Manages standings and statistics
- Broadcasts notifications (ROUND_ANNOUNCEMENT, LEAGUE_STANDINGS_UPDATE)
- Persists data to `SHARED/data/leagues/<league_id>/`

---

### Referee (`src/agents/referee/`)

**Purpose**: Orchestrates individual matches between two players.

**Workflow**:
1. Send `GAME_INVITATION` to both players
2. Collect parity choices via `choose_parity`
3. Determine outcome based on dice roll
4. Notify players via `notify_match_result`
5. Report to league manager via `report_match_result`

**Key Features**:
- Timeout handling for player responses
- Concurrent match execution (optional)
- Result reporting to league manager

---

### Shared Utilities (`src/shared/`)

**jsonrpc.py**: JSON-RPC 2.0 implementation
- Request parsing and validation
- Response/error generation
- Standard error codes (-32700 to -32603)

**http.py**: HTTP client utilities
- Configurable timeouts
- Retry logic with exponential backoff
- Connection pooling

**logging.py**: Structured logging
- JSON-formatted logs (JSONL)
- Per-league log files
- System-wide logs

**models.py**: Shared data models
- Message schemas
- Protocol payloads

**repositories/**: Data persistence layer
- Standings, rounds, matches, player history
- File-based storage in `SHARED/data/`

---

## Running the System

### Local Development

**Terminal 1: Start League Manager**
```bash
python -m src.agents.league_manager --port 9000
```

**Terminal 2-5: Start Player Agents**
```bash
python -m src.agents.player --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000
python -m src.agents.player --port 8002 --display-name "Agent2" --league-url http://127.0.0.1:9000
python -m src.agents.player --port 8003 --display-name "Agent3" --league-url http://127.0.0.1:9000
python -m src.agents.player --port 8004 --display-name "Agent4" --league-url http://127.0.0.1:9000
```

**Terminal 6: Run League**
```bash
python run_league.py
```

### Self-Test

Run the integrated self-test:
```bash
python -m src.agents.player.selftest
```

This launches 4 agents and simulates a full league cycle.

---

## Protocol Details

### Transport
- HTTP POST to `/mcp` endpoint
- JSON-RPC 2.0 envelope

### Message Format
```json
{
  "jsonrpc": "2.0",
  "method": "method_name",
  "params": { ... },
  "id": 1
}
```

### Response Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": { ... }
}
```

### Error Format
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32600,
    "message": "Invalid Request",
    "data": "..."
  }
}
```

---

## Testing

Run all tests:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_jsonrpc.py -v
```

Run with coverage:
```bash
pytest --cov=src --cov-report=html
```

---

## Development Milestones

Follow the tasks in `.opencode/agent/tasks/` for step-by-step implementation:

1. **Milestone A**: Skeleton - CLI, config, logging
2. **Milestone B**: HTTP server - FastAPI endpoints
3. **Milestone C**: JSON-RPC core - Request/response validation
4. **Milestone D**: Tool routing - Method dispatch
5. **Milestone E**: State and tool behavior - Tool implementations
6. **Milestone F**: Registration - Background registration with retries
7. **Milestone G**: Tests - Unit and integration tests
8. **Milestone H**: Self-test - Local league simulation

---

## Quality Checklist

Before submission, verify:
- [ ] All JSON-RPC 2.0 envelopes correct
- [ ] All 3 player methods implemented (invitation, parity, result)
- [ ] Handles invalid input without crashing
- [ ] Registration includes name, version, endpoint
- [ ] Self-test runs 4 agents successfully
- [ ] No blocking operations in tool handlers
- [ ] Clean shutdown (Ctrl+C)
- [ ] Tests pass: `pytest -v`

---

## Dependencies

Core:
- `fastapi>=0.104.0` - Web framework
- `uvicorn[standard]>=0.24.0` - ASGI server
- `httpx>=0.25.0` - Async HTTP client
- `requests>=2.31.0` - Sync HTTP client

Dev:
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.21.0` - Async test support

---

## License

MIT
