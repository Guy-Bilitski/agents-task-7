# 🎮 Parity Game League - Multi-Agent Competition System

A complete multi-agent competition system where autonomous agents play parity games against each other. The system includes a League Manager, Referee, and multiple competing agents that communicate via JSON-RPC 2.0 over HTTP.

## 📋 Table of Contents

1. [Overview](#overview)
2. [Quick Start](#quick-start)
3. [How the Game Works](#how-the-game-works)
4. [System Architecture](#system-architecture)
5. [Running the League](#running-the-league)
6. [Running Individual Components](#running-individual-components)
7. [API Reference](#api-reference)
8. [Development](#development)
9. [Troubleshooting](#troubleshooting)

---

## 🎯 Overview

This project implements a **multi-agent parity game competition** with three main components:

| Component | Role |
|-----------|------|
| **League Manager** | Central server that orchestrates the competition, accepts registrations, schedules games, and tracks standings |
| **Referee** | Runs individual games between two agents, collects choices, determines winners |
| **Agents** | Autonomous players that register with the league, accept game invitations, and make strategic parity choices |

### Key Features

- 🔄 **Fully Autonomous**: Once started, the system runs a complete competition without human intervention
- 📊 **Live Standings**: Track wins, losses, draws, and points in real-time
- 🔌 **Standard Protocol**: All communication uses JSON-RPC 2.0 over HTTP
- 🧪 **Self-Testing**: Built-in test harness validates the entire system
- 📈 **Configurable**: Adjust number of agents, rounds, and other parameters

---

## 🚀 Quick Start

### Prerequisites

- Python 3.10 or higher
- pip package manager

### Installation

```bash
# Clone or navigate to the project
cd agents-task7

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install the package
pip install -e ".[dev]"
```

### Run a Complete League

The easiest way to see everything in action:

```bash
# Run a league with 4 agents and 3 rounds per matchup
python run_league.py

# Or use python -m
python -m league
```

**What happens:**
1. League Manager starts on port 9000
2. Four agents (Alpha, Beta, Gamma, Delta) start on ports 8001-8004
3. Each agent registers with the League Manager
4. All possible matchups are played for each round
5. Final standings are displayed with a champion

### Run the Self-Test

To validate the entire system works correctly:

```bash
python -m agent.selftest
```

---

## 🎲 How the Game Works

The parity game is a simple strategic game between two agents:

### Game Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      GAME FLOW                              │
├─────────────────────────────────────────────────────────────┤
│  1. League Manager sends INVITATION to both agents         │
│     ↓                                                       │
│  2. Both agents respond with GAME_JOIN_ACK                  │
│     ↓                                                       │
│  3. League Manager asks each agent for PARITY_CHOOSE        │
│     ↓                                                       │
│  4. Each agent responds with "even" or "odd"                │
│     ↓                                                       │
│  5. Referee rolls a dice (1-100)                            │
│     ↓                                                       │
│  6. Agent whose choice matches the dice parity WINS         │
│     ↓                                                       │
│  7. Both agents receive MATCH_RESULT notification           │
└─────────────────────────────────────────────────────────────┘
```

### Scoring

| Outcome | Points |
|---------|--------|
| Win | 3 points |
| Draw (both right or both wrong) | 1 point |
| Loss | 0 points |

### Strategy

The included agents use a **deterministic hash-based strategy**:
- Hash the game_id to get a consistent choice for each game
- This provides varied but reproducible behavior
- You can implement more sophisticated strategies!

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     LEAGUE MANAGER                          │
│                    (Port 9000)                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ • Accepts agent registrations at /register           │   │
│  │ • Tracks standings at /standings                     │   │
│  │ • Lists agents at /agents                            │   │
│  │ • Health check at /health                            │   │
│  └─────────────────────────────────────────────────────┘   │
│                           │                                 │
│                    ┌──────┴──────┐                         │
│                    │   REFEREE   │                         │
│                    │ (Game Logic)│                         │
│                    └──────┬──────┘                         │
└───────────────────────────┼─────────────────────────────────┘
                            │
          ┌─────────────────┼─────────────────┐
          │                 │                 │
    ┌─────▼─────┐     ┌─────▼─────┐     ┌─────▼─────┐
    │  AGENT 1  │     │  AGENT 2  │     │  AGENT N  │
    │ Port 8001 │     │ Port 8002 │     │ Port 800N │
    │           │     │           │     │           │
    │ /mcp      │     │ /mcp      │     │ /mcp      │
    │ /health   │     │ /health   │     │ /health   │
    └───────────┘     └───────────┘     └───────────┘
```

### Directory Structure

```
agents-task7/
├── agent/                    # Agent implementation
│   ├── __init__.py
│   ├── __main__.py          # Entry: python -m agent
│   ├── app.py               # FastAPI HTTP server
│   ├── config.py            # CLI and env configuration
│   ├── jsonrpc.py           # JSON-RPC 2.0 protocol
│   ├── main.py              # Agent startup
│   ├── registration.py      # League registration client
│   ├── selftest.py          # Self-test harness
│   ├── state.py             # Game state management
│   └── tools.py             # JSON-RPC method handlers
│
├── league/                   # League infrastructure
│   ├── __init__.py
│   ├── __main__.py          # Entry: python -m league
│   ├── config.py            # League configuration
│   ├── manager.py           # League Manager server
│   └── referee.py           # Game referee logic
│
├── tests/                    # Test suite
│   ├── test_jsonrpc.py
│   ├── test_tools.py
│   ├── test_integration_http.py
│   └── ...
│
├── run_league.py            # Easy league runner
├── pyproject.toml           # Package configuration
└── README.md                # This file
```

---

## 🏃 Running the League

### Option 1: One Command (Recommended)

```bash
# Default: 4 agents, 3 rounds per matchup
python run_league.py

# Custom configuration
python run_league.py --num-agents 6 --rounds 5

# With verbose logging
python run_league.py --log-level DEBUG
```

### Option 2: Using Python Module

```bash
python -m league --num-agents 4 --rounds 3
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `--port` | 9000 | League Manager port |
| `--num-agents` | 4 | Number of agents to spawn |
| `--base-agent-port` | 8001 | Starting port for agents |
| `--rounds` | 3 | Rounds per matchup |
| `--log-level` | INFO | Logging verbosity |

### Expected Output

```
████████████████████████████████████████████████████████████
     PARITY GAME LEAGUE - MULTI-AGENT COMPETITION
████████████████████████████████████████████████████████████

Starting League Manager...
  ✓ League Manager ready on port 9000

Starting Agents...
  ✓ Agent 'Alpha' ready on port 8001
  ✓ Agent 'Beta' ready on port 8002
  ✓ Agent 'Gamma' ready on port 8003
  ✓ Agent 'Delta' ready on port 8004

============================================================
STARTING LEAGUE COMPETITION
============================================================
Registered agents: ['Alpha', 'Beta', 'Gamma', 'Delta']
Rounds per matchup: 3
Total matchups: 6
Total games: 18

============================================================
ROUND 1 of 3
============================================================
Starting game game_abc123: Alpha vs Beta
Game game_abc123: Dice rolled 73 (odd)
Game game_abc123: Alpha chose even, Beta chose odd
Game game_abc123: Winner is Beta
...

============================================================
FINAL STANDINGS
============================================================
Rank   Agent           Points   W-L-D        Win Rate  
------------------------------------------------------------
1      Delta           15       5-3-1        55.6%     
2      Beta            13       4-3-2        44.4%     
3      Alpha           10       3-4-2        33.3%     
4      Gamma           7        2-4-3        22.2%     
============================================================

🏆 CHAMPION: Delta 🏆
```

---

## 🔧 Running Individual Components

### Running a Single Agent

```bash
# Start an agent manually
python -m agent \
    --port 8001 \
    --display-name "MyAgent" \
    --league-url http://127.0.0.1:9000

# Check agent health
curl http://127.0.0.1:8001/health
```

### Running League Manager Only

You can start just the league manager for testing:

```python
import asyncio
from league.manager import LeagueManager

async def main():
    manager = LeagueManager(port=9000, rounds=3)
    await manager.start_server()

asyncio.run(main())
```

### Testing Agent Endpoints Manually

```bash
# Send a game invitation
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "handle_game_invitation",
    "params": {
      "game_id": "test_game",
      "invitation_id": "test_inv",
      "from_player": "TestPlayer"
    }
  }'

# Get parity choice
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "parity_choose",
    "params": {"game_id": "test_game"}
  }'

# Notify match result
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "notify_match_result",
    "params": {
      "game_id": "test_game",
      "winner": "MyAgent",
      "details": {"dice_roll": 42, "dice_parity": "even"}
    }
  }'
```

---

## 📡 API Reference

### League Manager Endpoints

#### `GET /health`
Returns league manager status.

```json
{"ok": true, "registered_agents": 4, "total_games": 18}
```

#### `POST /register`
Register an agent with the league.

**Request:**
```json
{
  "display_name": "MyAgent",
  "version": "1.0.0",
  "endpoint": "http://127.0.0.1:8001/mcp"
}
```

**Response:**
```json
{
  "status": "registered",
  "agent_id": "agent_MyAgent",
  "message": "Welcome to the league, MyAgent!"
}
```

#### `GET /standings`
Get current league standings.

```json
{
  "standings": [
    {
      "rank": 1,
      "agent": "Delta",
      "points": 15,
      "wins": 5,
      "losses": 3,
      "draws": 1,
      "games_played": 9,
      "win_rate": "55.6%"
    }
  ],
  "total_games": 18,
  "rounds_completed": 3
}
```

#### `GET /agents`
List registered agents.

```json
{
  "agents": [
    {"display_name": "Alpha", "version": "1.0.0", "endpoint": "http://127.0.0.1:8001/mcp"}
  ]
}
```

### Agent JSON-RPC Methods

All agent communication uses JSON-RPC 2.0 on the `/mcp` endpoint.

#### `handle_game_invitation`

Accept a game invitation.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "handle_game_invitation",
  "params": {
    "game_id": "game_abc123",
    "invitation_id": "inv_xyz",
    "from_player": "LeagueManager"
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "type": "GAME_JOIN_ACK",
    "accepted": true,
    "game_id": "game_abc123"
  }
}
```

#### `parity_choose`

Make a parity choice.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "parity_choose",
  "params": {"game_id": "game_abc123"}
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "type": "RESPONSE_PARITY_CHOOSE",
    "choice": "even",
    "game_id": "game_abc123"
  }
}
```

#### `notify_match_result`

Receive match result.

**Request:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "notify_match_result",
  "params": {
    "game_id": "game_abc123",
    "winner": "Alpha",
    "details": {"dice_roll": 42, "dice_parity": "even"}
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {"ok": true}
}
```

### JSON-RPC Error Codes

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Missing required JSON-RPC fields |
| -32601 | Method not found | Unknown method name |
| -32602 | Invalid params | Wrong parameter types |
| -32603 | Internal error | Server-side error |

---

## 🛠️ Development

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/test_jsonrpc.py

# Run with coverage
pytest --cov=agent --cov=league
```

### Adding a New Agent Strategy

Edit `agent/state.py` and modify the `deterministic_parity_choice` function:

```python
def deterministic_parity_choice(game_id: Optional[str]) -> str:
    """Your custom strategy here."""
    # Example: Random choice
    import random
    return random.choice(["even", "odd"])
    
    # Example: Always even
    return "even"
    
    # Example: Based on time
    import time
    return "even" if int(time.time()) % 2 == 0 else "odd"
```

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `PORT` | Agent server port | 8001 |
| `DISPLAY_NAME` | Agent name | (required) |
| `LEAGUE_URL` | League manager URL | (required) |
| `LOG_LEVEL` | Logging level | INFO |
| `LEAGUE_PORT` | League manager port | 9000 |
| `NUM_AGENTS` | Number of agents | 4 |
| `ROUNDS` | Rounds per matchup | 3 |

---

## 🔍 Troubleshooting

### Port Already in Use

```
OSError: [Errno 98] Address already in use
```

**Solution:** Kill existing processes or use different ports:
```bash
# Find and kill process
lsof -i :8001
kill <PID>

# Or use different ports
python -m agent --port 8010 --display-name Agent1 --league-url http://127.0.0.1:9000
```

### Registration Warnings

```
[WARNING] Registration attempt X failed: All connection attempts failed
```

**This is normal** if no league manager is running. The agent will:
- Continue working and accepting requests
- Retry registration with exponential backoff
- Never block the HTTP server

### Module Not Found

```
ModuleNotFoundError: No module named 'uvicorn'
```

**Solution:** Install dependencies:
```bash
source venv/bin/activate
pip install -e ".[dev]"
```

### Self-Test Failures

1. Make sure no other agents are running on ports 8001-8004
2. Make sure port 9000 is free for the league manager
3. Run with debug logging: `python -m agent.selftest 2>&1 | head -100`

---

## 📄 License

[MIT License](LICENSE)

---

## 🙏 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests: `pytest`
5. Submit a pull request

---

## 📞 Quick Reference

```bash
# Install
pip install -e ".[dev]"

# Run full league
python run_league.py

# Run self-test
python -m agent.selftest

# Start single agent
python -m agent --port 8001 --display-name Agent1 --league-url http://127.0.0.1:9000

# Check health
curl http://127.0.0.1:8001/health

# Run tests
pytest -v
```
