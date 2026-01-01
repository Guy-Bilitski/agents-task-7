# MCP Agent

A Model Context Protocol (MCP) agent implementation for league-based competition systems. This agent participates in parity games by handling invitations, making strategic choices, and tracking game results.

## Features

- **JSON-RPC 2.0 Protocol**: Full compliance with JSON-RPC 2.0 specification
- **Automatic League Registration**: Background registration with exponential backoff retry logic
- **Game Management**: Handles invitations, parity choices, and result notifications
- **State Tracking**: Comprehensive game statistics including wins, losses, draws, and win rates
- **Deterministic Strategy**: Hash-based parity selection algorithm
- **Health Monitoring**: Built-in health check endpoint
- **Graceful Shutdown**: SIGINT/SIGTERM signal handling
- **Comprehensive Testing**: Full test suite with integration tests

## Architecture

The agent is built with:
- **FastAPI**: High-performance HTTP server framework
- **Uvicorn**: ASGI server for production-ready deployment
- **httpx**: Async HTTP client for league communication
- **pytest**: Testing framework with async support

### Core Components

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

## Installation

### Requirements

- Python 3.10 or higher
- pip or uv package manager

### Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd agents-task7
```

2. Install dependencies:
```bash
pip install -e .
```

3. For development with testing support:
```bash
pip install -e ".[dev]"
```

## Usage

### Running the Agent

#### Command Line Arguments

```bash
python -m agent \
  --port 8001 \
  --display-name "Agent1" \
  --league-url http://127.0.0.1:9000
```

#### Environment Variables

```bash
export PORT=8001
export DISPLAY_NAME="Agent1"
export LEAGUE_URL="http://127.0.0.1:9000"

python -m agent
```

#### Configuration Options

| Argument | Environment Variable | Default | Description |
|----------|---------------------|---------|-------------|
| `--port` | `PORT` | 8001 | Server port |
| `--display-name` | `DISPLAY_NAME` | (required) | Unique agent identifier |
| `--league-url` | `LEAGUE_URL` | (required) | League manager base URL |
| `--version` | `VERSION` | 1.0.0 | Agent version |
| `--log-level` | `LOG_LEVEL` | INFO | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `--registration-path` | `REGISTRATION_PATH` | /register | League registration endpoint path |

### API Endpoints

#### Health Check

```bash
GET http://127.0.0.1:8001/health
```

Returns:
```json
{
  "status": "healthy",
  "agent_name": "Agent1",
  "registered": true,
  "stats": {
    "games_played": 10,
    "wins": 7,
    "losses": 2,
    "draws": 1,
    "win_rate": 0.7
  }
}
```

#### MCP Endpoint

```bash
POST http://127.0.0.1:8001/mcp
Content-Type: application/json

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

### Supported JSON-RPC Methods

#### 1. handle_game_invitation

Handles incoming game invitations and returns acknowledgment.

**Request:**
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

#### 2. parity_choose

Determines parity choice (even/odd) for a game using deterministic strategy.

**Request:**
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

#### 3. notify_match_result

Receives and acknowledges match result notifications.

**Request:**
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

## Development

### Running Tests

Run the full test suite:
```bash
pytest
```

Run with verbose output:
```bash
pytest -v
```

Run specific test file:
```bash
pytest tests/test_jsonrpc.py
```

Run with coverage:
```bash
pytest --cov=agent --cov-report=html
```

### Test Structure

```
tests/
├── test_jsonrpc.py            # JSON-RPC protocol tests
├── test_tools.py              # Tool handler tests
├── test_state.py              # State management tests
├── test_registration.py       # Registration client tests
├── test_integration_http.py   # HTTP integration tests
└── mock_league.py             # Mock league server for testing
```

### Code Quality

The project follows best practices:
- Type hints throughout the codebase
- Comprehensive docstrings
- Modular architecture with clear separation of concerns
- Error handling with proper JSON-RPC error responses
- Structured logging

## How It Works

### Startup Sequence

1. **Configuration**: Parse CLI args and environment variables
2. **State Initialization**: Initialize game state tracking
3. **Server Creation**: Create FastAPI application with routes
4. **Background Registration**: Start async registration with league manager
5. **Server Start**: Launch HTTP server on specified port

### Game Flow

1. **Invitation**: League sends `handle_game_invitation` → Agent accepts
2. **Parity Choice**: League requests `parity_choose` → Agent returns deterministic choice
3. **Game Execution**: League runs the game
4. **Result**: League sends `notify_match_result` → Agent updates statistics

### Parity Choice Strategy

The agent uses a deterministic hash-based strategy:
```python
def deterministic_parity_choice(game_id: str | None) -> str:
    """Deterministic parity choice based on game_id hash."""
    if not game_id:
        return "even"
    
    # Hash the game_id and use LSB to determine parity
    hash_value = hash(game_id)
    return "even" if hash_value % 2 == 0 else "odd"
```

### Registration Retry Logic

- **Initial delay**: 1 second
- **Backoff factor**: 2x
- **Max delay**: 30 seconds
- **Retries**: Infinite until success
- **Non-blocking**: Server starts immediately, registration happens in background

## Error Handling

### JSON-RPC Errors

The agent returns standard JSON-RPC 2.0 error responses:

| Code | Message | Description |
|------|---------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Request doesn't match JSON-RPC 2.0 spec |
| -32601 | Method not found | Method doesn't exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Server-side error |

Example error response:
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

## Logging

The agent provides structured logging at multiple levels:

```
INFO: Startup configuration, registration status, game events
DEBUG: Detailed protocol messages, extra fields, internal state
WARNING: Registration retries, recoverable errors
ERROR: Server errors, unhandled exceptions
```

Example log output:
```
============================================================
MCP Agent Starting
============================================================
Display Name: Agent1
Version: 1.0.0
Port: 8001
MCP Endpoint: http://127.0.0.1:8001/mcp
League URL: http://127.0.0.1:9000
Registration URL: http://127.0.0.1:9000/register
Log Level: INFO
============================================================
Agent state initialized
Starting background registration
Starting HTTP server on http://127.0.0.1:8001
Health endpoint: http://127.0.0.1:8001/health
MCP endpoint: http://127.0.0.1:8001/mcp
Press Ctrl+C to shutdown
✓ Successfully registered with league manager
Received game invitation: game_id=game_123, invitation_id=inv_456, from=Agent2
Accepting game invitation: {'type': 'GAME_JOIN_ACK', 'accepted': True, 'game_id': 'game_123', 'invitation_id': 'inv_456'}
Parity choice: even for game_id=game_123
Match result: game_id=game_123, winner=Agent1, details={'score': '10-8'}
Updated stats: games=1, W=1, L=0, D=0, win_rate=100.00%
```

## Graceful Shutdown

The agent handles SIGINT (Ctrl+C) and SIGTERM signals:

1. First signal: Initiates graceful shutdown
2. Second signal: Forces immediate exit

```
^CReceived signal 2, shutting down gracefully...
Shutdown complete
```

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]

## Support

For issues and questions, please [open an issue](link-to-issues) on GitHub.
