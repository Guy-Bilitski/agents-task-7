# Referee Architecture: Separate MCP Server

## Overview

The Referee is implemented as a **separate MCP server** that communicates with both the League Manager and Player agents via JSON-RPC 2.0 over HTTP.

## Architecture

```
┌─────────────────┐
│ League Manager  │
│   (Port 8000)   │
└────────┬────────┘
         │
         │ JSON-RPC: run_match
         ▼
┌─────────────────┐
│    Referee      │
│   (Port 8001)   │
└────────┬────────┘
         │
         │ JSON-RPC: handle_game_invitation,
         │          choose_parity,
         │          notify_match_result
         ▼
┌─────────────────┐
│  Player Agents  │
│  (Ports 8101+)  │
└─────────────────┘
```

## Components

### 1. Referee MCP Server (`agents.referee.app.RefereeServer`)

**Responsibilities:**
- Runs as an independent HTTP server on port 8001 (default)
- Exposes MCP endpoint at `POST /mcp`
- Handles match orchestration between two players
- Implements game logic (invitations, parity choices, dice roll, winner determination)

**MCP Methods:**
- `ping` - Health check / connectivity test
- `run_match` - Run a complete match between two players

**Example run_match request:**
```json
{
  "jsonrpc": "2.0",
  "id": "match_123",
  "method": "run_match",
  "params": {
    "match_id": "match_123",
    "player1": {
      "display_name": "Alpha",
      "version": "1.0.0",
      "endpoint": "http://127.0.0.1:8101/mcp"
    },
    "player2": {
      "display_name": "Beta",
      "version": "1.0.0",
      "endpoint": "http://127.0.0.1:8102/mcp"
    }
  }
}
```

**Example run_match response:**
```json
{
  "jsonrpc": "2.0",
  "id": "match_123",
  "result": {
    "match_id": "match_123",
    "game_id": "game_a1b2c3d4",
    "player1": "Alpha",
    "player2": "Beta",
    "player1_choice": "even",
    "player2_choice": "odd",
    "dice_roll": 42,
    "dice_parity": "even",
    "winner": "Alpha",
    "is_draw": false
  }
}
```

### 2. Referee Registration Client (`agents.referee.client.RefereeRegistrationClient`)

**Responsibilities:**
- Registers the referee with the League Manager on startup
- Retries registration with exponential backoff
- Runs in background, does NOT block server startup

**Registration payload:**
```json
{
  "display_name": "Referee",
  "version": "1.0.0",
  "endpoint": "http://127.0.0.1:8001/mcp",
  "agent_type": "referee",
  "supported_game_types": ["even_odd"]
}
```

### 3. League Manager Integration

**Changes to League Manager:**
- Accepts referee registration at `/register` endpoint
- Stores referee endpoint when `agent_type` is "referee"
- Can operate in two modes:
  - **External Referee Mode**: Calls referee via JSON-RPC `run_match`
  - **Embedded Referee Mode**: Uses built-in Referee instance (legacy)
- Calls referee's `run_match` method for each game

## Running the System

### Option 1: External Referee (Recommended)

**Terminal 1 - League Manager:**
```bash
python -m agents.league_manager --port 8000 --use-external-referee
```

**Terminal 2 - Referee:**
```bash
python -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000
```

**Terminal 3 - Player 1:**
```bash
python -m agents.player --port 8101 --display-name Alpha --league-url http://127.0.0.1:8000
```

**Terminal 4 - Player 2:**
```bash
python -m agents.player --port 8102 --display-name Beta --league-url http://127.0.0.1:8000
```

### Option 2: Embedded Referee (Legacy)

**Terminal 1 - League Manager:**
```bash
python -m agents.league_manager --port 8000
```

**Terminal 2+ - Players:**
```bash
python -m agents.player --port 8101 --display-name Alpha --league-url http://127.0.0.1:8000
python -m agents.player --port 8102 --display-name Beta --league-url http://127.0.0.1:8000
```

## Game Flow

1. **Registration Phase:**
   - Referee registers with League Manager
   - Players register with League Manager

2. **Match Execution:**
   - League Manager calls referee's `run_match` method
   - Referee sends `handle_game_invitation` to both players
   - Referee calls `choose_parity` on both players
   - Referee rolls dice and determines winner
   - Referee calls `notify_match_result` on both players
   - Referee returns match result to League Manager

3. **Standings Update:**
   - League Manager receives match result
   - League Manager updates standings
   - Process repeats for all matches

## Benefits of Separate Referee

1. **Separation of Concerns**: League Manager focuses on scheduling and standings, Referee focuses on game mechanics
2. **Independent Scaling**: Referee can be scaled separately or replaced
3. **Testability**: Referee can be tested independently
4. **MCP Compliance**: All communication via standard JSON-RPC 2.0
5. **Fault Isolation**: Referee crashes don't bring down the league
6. **Multiple Referee Support**: Future: Different game types can have different referees

## Testing

### Manual Test
```bash
# Terminal 1
python -m agents.referee --port 8001 --no-register

# Terminal 2
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "ping",
    "params": {}
  }'
```

Expected response:
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {"ok": true, "message": "pong"}
}
```

### Integration Test
See `tests/test_integration_http.py` for full integration tests with League Manager, Referee, and Players.

## Configuration

### Referee Config (`SHARED/config/defaults/referee.json`)
```json
{
  "host": "127.0.0.1",
  "port": 8001,
  "timeout": 30.0,
  "league_manager_url": "http://127.0.0.1:8000"
}
```

## Timeouts

- **Invitation timeout**: 5 seconds per player
- **Parity choice timeout**: 30 seconds per player
- **Result notification timeout**: 10 seconds per player
- **Match timeout**: 60 seconds total (League Manager to Referee)

## Error Handling

- All errors are returned as JSON-RPC errors
- Referee never crashes on bad input
- Failed invitations/choices result in default "none" values
- League Manager continues even if a match fails
