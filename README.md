# MCP Agent - Parity Game League Competition

A Model Context Protocol (MCP) agent implementation for participating in a multi-agent parity game competition. This agent is designed to compete against other agents in a league managed by a central league manager server.

## Table of Contents

1. [What Is This Game?](#what-is-this-game)
2. [How The Parity Game Works](#how-the-parity-game-works)
3. [System Architecture](#system-architecture)
4. [Installation](#installation)
5. [Starting The League](#starting-the-league)
6. [Testing The Agent](#testing-the-agent)
7. [API Reference](#api-reference)
8. [Development](#development)

---

## What Is This Game?

This project implements an **agent** that plays in a **parity game competition**. Think of it like a multiplayer gaming system where:

- Multiple **agents** (players) compete against each other
- A **league manager** server orchestrates the games and tracks scores
- Each agent runs as an independent HTTP server that responds to game invitations
- Agents make strategic choices during games to try to win
- The league manager keeps track of wins, losses, and rankings

### The Players

- **League Manager**: A central server (not included in this repo) that:
  - Manages the competition
  - Sends game invitations to agents
  - Runs the games
  - Determines winners
  - Tracks statistics and rankings

- **Agents** (this implementation): Individual players that:
  - Register with the league manager
  - Accept game invitations
  - Make strategic parity choices ("even" or "odd")
  - Receive match results and track their statistics

---

## How The Parity Game Works

The parity game is a simple strategic game played between two agents. Here's the step-by-step flow:

### Step 1: Game Invitation
The league manager selects two agents to play against each other and sends a **game invitation** to both:

```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "handle_game_invitation",
  "params": {
    "game_id": "game_123",
    "invitation_id": "inv_456",
    "from_player": "LeagueManager"
  }
}
```

**Agent Response**: The agent accepts the invitation:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "type": "GAME_JOIN_ACK",
    "accepted": true,
    "game_id": "game_123",
    "invitation_id": "inv_456"
  }
}
```

### Step 2: Parity Choice
The league manager asks each agent to choose **"even"** or **"odd"**:

```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "parity_choose",
  "params": {
    "game_id": "game_123"
  }
}
```

**Agent Response**: The agent makes its strategic choice:
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "type": "RESPONSE_PARITY_CHOOSE",
    "choice": "even",
    "game_id": "game_123"
  }
}
```

### Step 3: Game Execution
The league manager:
1. Collects both agents' choices
2. Runs the game logic (the exact game mechanics are determined by the league manager)
3. Determines which agent won based on the parity choices

### Step 4: Result Notification
The league manager notifies both agents of the outcome:

```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "notify_match_result",
  "params": {
    "game_id": "game_123",
    "winner": "Agent1",
    "details": {
      "score": "10-8",
      "duration": 120
    }
  }
}
```

**Agent Response**: The agent acknowledges and updates its statistics:
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "ok": true
  }
}
```

### Strategy

The key to winning is choosing the right parity! This implementation uses a **deterministic hash-based strategy**:
- The agent hashes the `game_id` 
- Based on the hash, it consistently chooses either "even" or "odd" for that specific game
- This provides consistent behavior while distributing choices across different games

You can implement more sophisticated strategies by analyzing past game history, opponent patterns, and win rates (see the optional Milestone I documentation).

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     League Manager                          │
│                  (Orchestrates Games)                       │
│  - Sends game invitations                                   │
│  - Collects parity choices                                  │
│  - Determines winners                                       │
│  - Tracks rankings                                          │
└──────────┬────────────┬────────────┬────────────┬───────────┘
           │            │            │            │
           │ JSON-RPC   │ JSON-RPC   │ JSON-RPC   │ JSON-RPC
           │ over HTTP  │ over HTTP  │ over HTTP  │ over HTTP
           │            │            │            │
      ┌────▼───┐   ┌───▼────┐   ┌───▼────┐   ┌───▼────┐
      │ Agent1 │   │ Agent2 │   │ Agent3 │   │ Agent4 │
      │:8001   │   │:8002   │   │:8003   │   │:8004   │
      └────────┘   └────────┘   └────────┘   └────────┘
```

### Communication Protocol

All communication uses **JSON-RPC 2.0 over HTTP**:
- **Transport**: HTTP POST requests to `/mcp` endpoint
- **Protocol**: JSON-RPC 2.0 (fully compliant)
- **Methods**: Three game-related methods (invitation, choice, result)

### Agent Components

```
agent/
├── app.py           # FastAPI application and HTTP routing
├── config.py        # Configuration management (CLI + env vars)
├── jsonrpc.py       # JSON-RPC 2.0 protocol implementation
├── main.py          # Application entrypoint
├── registration.py  # League registration client with retry logic
├── state.py         # Game state and statistics management
└── tools.py         # Game method handlers (invitation, choice, result)
```

---

## Installation

### Requirements

- Python 3.10 or higher
- pip or uv package manager

### Setup

1. **Clone the repository** (or navigate to the project directory):
   ```bash
   cd agents-task7
   ```

2. **Create a virtual environment** (recommended):
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install the package**:
   ```bash
   pip install -e .
   ```

4. **For development with testing support**:
   ```bash
   pip install -e ".[dev]"
   ```

5. **Verify installation**:
   ```bash
   python -m agent --help
   ```

   You should see the help message with all available options.

---

## Starting The League

This section provides step-by-step instructions for setting up and running a complete league competition.

### Option 1: Self-Test Mode (Quickest Way to See It Work)

The easiest way to see the entire system in action is to run the built-in self-test:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the self-test harness
python -m agent.selftest
```

**What happens:**
1. A mock league manager starts on port 9000
2. Four agents start on ports 8001-8004 with names Agent1, Agent2, Agent3, Agent4
3. All agents register with the league manager
4. The mock league sends test messages to each agent:
   - Game invitations
   - Parity choice requests
   - Match result notifications
5. All responses are validated for correctness
6. Complete statistics are displayed
7. Everything shuts down cleanly

**Expected output:**
```
[INFO] Starting mock league manager on port 9000
[INFO] League manager started successfully
[INFO] Starting agent Agent1 on port 8001
[INFO] Starting agent Agent2 on port 8002
[INFO] Starting agent Agent3 on port 8003
[INFO] Starting agent Agent4 on port 8004
[INFO] All agents started successfully
[INFO] Waiting for agents to register...
[INFO] All 4 agents registered successfully
[INFO] Testing agent Agent1...
✓ Test 1/12: handle_game_invitation - PASSED
✓ Test 2/12: parity_choose - PASSED
✓ Test 3/12: notify_match_result - PASSED
...
[INFO] All tests passed! (12/12)
[INFO] Shutting down agents...
[INFO] Self-test completed successfully
```

### Option 2: Running a Single Agent Manually

To run a single agent for testing or development:

```bash
# Activate virtual environment
source venv/bin/activate

# Start the agent
python -m agent \
  --port 8001 \
  --display-name "MyAgent" \
  --league-url http://127.0.0.1:9000
```

**What happens:**
1. Agent starts HTTP server on port 8001
2. Attempts to register with league manager at http://127.0.0.1:9000
3. If no league manager is running, shows registration warnings (this is normal)
4. Agent is ready to receive JSON-RPC requests

**Check agent health:**
```bash
curl http://127.0.0.1:8001/health
```

**Expected response:**
```json
{
  "ok": true
}
```

**Send a test game invitation:**
```bash
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
```

### Option 3: Running Multiple Agents with a League Manager

To run a full league competition, you need a league manager server (not included in this repository). Once you have one:

**Terminal 1 - Start League Manager:**
```bash
# Start your league manager on port 9000
# (The exact command depends on your league manager implementation)
python -m league_manager --port 9000
```

**Terminal 2 - Start Agent 1:**
```bash
source venv/bin/activate
python -m agent --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000
```

**Terminal 3 - Start Agent 2:**
```bash
source venv/bin/activate
python -m agent --port 8002 --display-name "Agent2" --league-url http://127.0.0.1:9000
```

**Terminal 4 - Start Agent 3:**
```bash
source venv/bin/activate
python -m agent --port 8003 --display-name "Agent3" --league-url http://127.0.0.1:9000
```

**Terminal 5 - Start Agent 4:**
```bash
source venv/bin/activate
python -m agent --port 8004 --display-name "Agent4" --league-url http://127.0.0.1:9000
```

**What happens:**
1. Each agent starts and registers with the league manager
2. League manager can now orchestrate games between agents
3. Each agent responds to invitations and makes parity choices
4. Statistics are tracked and displayed in health endpoints

**Monitor agent statistics:**
```bash
# Check Agent1's statistics
curl http://127.0.0.1:8001/health

# Check Agent2's statistics
curl http://127.0.0.1:8002/health
```

### Option 4: Using Environment Variables

You can configure agents using environment variables instead of command-line arguments:

```bash
# Set environment variables
export PORT=8001
export DISPLAY_NAME="Agent1"
export LEAGUE_URL="http://127.0.0.1:9000"
export LOG_LEVEL="DEBUG"

# Start agent
python -m agent
```

### Configuration Options

| Argument | Environment Variable | Default | Description |
|----------|---------------------|---------|-------------|
| `--port` | `PORT` | 8001 | Server port |
| `--display-name` | `DISPLAY_NAME` | (required) | Unique agent identifier |
| `--league-url` | `LEAGUE_URL` | (required) | League manager base URL |
| `--version` | `VERSION` | 1.0.0 | Agent version |
| `--log-level` | `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `--registration-path` | `REGISTRATION_PATH` | /register | League registration endpoint path |

### Understanding Registration Warnings

When you start an agent, you may see warnings like:
```
[WARNING] agent.registration: Registration attempt 1 failed: All connection attempts failed. Retrying in 1.0s...
```

**This is normal** if:
- You're testing the agent without a league manager running
- The league manager isn't ready yet
- You provided a test league URL

The agent will:
- Continue to work normally
- Accept JSON-RPC requests
- Retry registration in the background with exponential backoff
- Never block the HTTP server

---

## Testing The Agent

### Run All Tests

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
pytest
```

### Run Tests with Verbose Output

```bash
pytest -v
```

### Run Specific Test File

```bash
# Test JSON-RPC protocol
pytest tests/test_jsonrpc.py

# Test game tools
pytest tests/test_tools.py

# Test HTTP integration
pytest tests/test_integration_http.py
```

### Run Tests with Coverage

```bash
pytest --cov=agent --cov-report=html
```

### Test Structure

```
tests/
├── test_jsonrpc.py            # JSON-RPC protocol compliance tests
├── test_tools.py              # Tool handler logic tests
├── test_state.py              # State management tests
├── test_registration.py       # Registration client tests
├── test_integration_http.py   # HTTP endpoint integration tests
└── mock_league.py             # Mock league server for testing
```

### Manual Testing

**Test health endpoint:**
```bash
curl http://127.0.0.1:8001/health
```

**Test game invitation:**
```bash
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
```

**Test parity choice:**
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "parity_choose",
    "params": {
      "game_id": "test_game"
    }
  }'
```

**Test match result:**
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "notify_match_result",
    "params": {
      "game_id": "test_game",
      "winner": "Agent1",
      "details": {
        "score": "10-8"
      }
    }
  }'
```

---

## API Reference

### HTTP Endpoints

#### `GET /health`

Health check endpoint that returns agent status and statistics.

**Response:**
```json
{
  "ok": true
}
```

#### `POST /mcp`

Main JSON-RPC endpoint for game communication.

**Content-Type:** `application/json`

**Request format:** JSON-RPC 2.0 (see methods below)

### JSON-RPC Methods

All methods follow JSON-RPC 2.0 specification:
- Request must include: `jsonrpc: "2.0"`, `method`, `id`
- Optional: `params` (object or array)
- Response includes: `jsonrpc: "2.0"`, `id`, and either `result` or `error`

#### 1. `handle_game_invitation`

Handles incoming game invitations.

**Parameters:**
- `game_id` (string, optional): Unique game identifier
- `invitation_id` (string, optional): Unique invitation identifier
- `from_player` (string, optional): Player sending the invitation

**Request example:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "handle_game_invitation",
  "params": {
    "game_id": "game_123",
    "invitation_id": "inv_456",
    "from_player": "Agent2"
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
    "game_id": "game_123",
    "invitation_id": "inv_456"
  }
}
```

**Time limit:** Must respond within 5 seconds

#### 2. `parity_choose`

Requests the agent's parity choice for a game.

**Parameters:**
- `game_id` (string, optional): Game identifier

**Request example:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "parity_choose",
  "params": {
    "game_id": "game_123"
  }
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
    "game_id": "game_123"
  }
}
```

**Possible choices:** `"even"` or `"odd"`

**Time limit:** Must respond within 30 seconds

#### 3. `notify_match_result`

Notifies the agent of a match result.

**Parameters:**
- `game_id` (string, optional): Game identifier
- `winner` (string, optional): Name of winning agent
- `details` (object, optional): Additional game details

**Request example:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "notify_match_result",
  "params": {
    "game_id": "game_123",
    "winner": "Agent1",
    "details": {
      "score": "10-8",
      "duration": 120
    }
  }
}
```

**Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "ok": true
  }
}
```

**Time limit:** Must respond within 10 seconds

### JSON-RPC Error Codes

The agent returns standard JSON-RPC 2.0 error responses:

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON received |
| -32600 | Invalid Request | Request doesn't match JSON-RPC 2.0 spec |
| -32601 | Method not found | Requested method doesn't exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Server-side error during execution |

**Error response example:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "error": {
    "code": -32602,
    "message": "Invalid params",
    "data": "params must be an object"
  }
}
```

---

## Development

### Project Structure

```
agents-task7/
├── agent/                      # Main package
│   ├── __init__.py
│   ├── __main__.py            # Module entry point
│   ├── app.py                 # FastAPI application
│   ├── config.py              # Configuration management
│   ├── jsonrpc.py             # JSON-RPC protocol
│   ├── main.py                # CLI entry point
│   ├── registration.py        # League registration
│   ├── state.py               # State management
│   ├── selftest.py            # Self-test harness
│   └── tools.py               # Game method handlers
├── tests/                      # Test suite
│   ├── __init__.py
│   ├── test_jsonrpc.py
│   ├── test_tools.py
│   ├── test_state.py
│   ├── test_registration.py
│   ├── test_integration_http.py
│   └── mock_league.py
├── .opencode/                  # Implementation documentation
│   └── agent/
│       ├── START_HERE.md
│       ├── python_engineer.md
│       ├── IMPLEMENTATION_SUMMARY.md
│       └── tasks/              # Step-by-step implementation guides
├── pyproject.toml             # Package configuration
├── pytest.ini                 # Pytest configuration
├── README.md                  # This file
└── .gitignore
```

### Key Features

- **JSON-RPC 2.0 Compliance**: Strict adherence to the JSON-RPC 2.0 specification
- **Automatic Registration**: Background registration with exponential backoff retry logic
- **Thread-Safe State**: Lock-protected state management for concurrent requests
- **Deterministic Strategy**: Hash-based parity selection for consistent behavior
- **Comprehensive Testing**: Full test suite with unit and integration tests
- **Graceful Shutdown**: Proper signal handling for clean termination
- **Health Monitoring**: Built-in health check endpoint with statistics
- **Extensive Logging**: Structured logging at multiple levels

### Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for production-ready deployment
- **httpx**: Async HTTP client for league communication
- **pytest**: Testing framework with async support

### Logging

The agent provides structured logging at multiple levels:

```
DEBUG: Detailed protocol messages, extra fields, internal state
INFO:  Startup, registration status, game events, statistics
WARN:  Registration retries, recoverable errors
ERROR: Server errors, unhandled exceptions
```

**Set log level:**
```bash
python -m agent --log-level DEBUG --display-name "Agent1" --league-url http://127.0.0.1:9000
```

### Graceful Shutdown

The agent handles SIGINT (Ctrl+C) and SIGTERM signals:

1. **First signal**: Initiates graceful shutdown
2. **Second signal**: Forces immediate exit

```
^C
Received signal 2, shutting down gracefully...
Shutdown complete
```

### Code Quality

The project follows best practices:
- Type hints throughout the codebase
- Comprehensive docstrings
- Modular architecture with clear separation of concerns
- Proper error handling with JSON-RPC error responses
- Thread-safe state management
- Extensive test coverage

### Implementation Documentation

Detailed implementation guides are available in `.opencode/agent/`:

- **START_HERE.md**: Quick start guide for implementers
- **python_engineer.md**: Complete technical specification
- **tasks/**: Step-by-step implementation milestones (A through H)
- **validation-checklist.md**: Pre-submission validation checklist

These documents provide a complete blueprint for understanding or re-implementing the agent.

---

## Troubleshooting

### Agent won't start

**Problem**: `ModuleNotFoundError: No module named 'uvicorn'`

**Solution**: Install dependencies
```bash
source venv/bin/activate
pip install -e .
```

### Registration keeps failing

**Problem**: `[WARNING] Registration attempt X failed: All connection attempts failed`

**Solution**: This is normal if no league manager is running. The agent will:
- Keep retrying in the background
- Still accept JSON-RPC requests
- Work perfectly for testing

If you want to stop the warnings, start a league manager on the configured URL.

### Port already in use

**Problem**: `OSError: [Errno 98] Address already in use`

**Solution**: Choose a different port
```bash
python -m agent --port 8002 --display-name "Agent1" --league-url http://127.0.0.1:9000
```

### Tests failing

**Problem**: `pytest` shows failures

**Solution**: 
1. Make sure you're in the virtual environment: `source venv/bin/activate`
2. Reinstall the package: `pip install -e .`
3. Check for port conflicts: Make sure no agents are running
4. Run with verbose output: `pytest -v` to see details

---

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please [open an issue](link-to-issues) on GitHub.

---

## Quick Reference Card

### Start Self-Test
```bash
source venv/bin/activate
python -m agent.selftest
```

### Start Single Agent
```bash
source venv/bin/activate
python -m agent --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000
```

### Check Agent Health
```bash
curl http://127.0.0.1:8001/health
```

### Run Tests
```bash
source venv/bin/activate
pytest
```

### View Logs with Debug Info
```bash
python -m agent --log-level DEBUG --display-name "Agent1" --league-url http://127.0.0.1:9000
```
