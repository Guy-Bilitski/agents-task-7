# Running the Referee as a Separate MCP Server

## Quick Start

The referee can run as either:
1. **Separate MCP Server** (recommended) - Independent service that the League Manager calls via JSON-RPC
2. **Embedded** (legacy) - Built into the League Manager

## Option 1: Separate Referee Server (Recommended)

### Start Each Component Separately

**Terminal 1 - League Manager:**
```bash
cd /path/to/agents-task7
python -m agents.league_manager --port 8000 --use-external-referee --no-autostart
```

**Terminal 2 - Referee:**
```bash
cd /path/to/agents-task7
python -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000
```

**Terminal 3 - Player Alpha:**
```bash
cd /path/to/agents-task7
python -m agents.player --port 8101 --display-name Alpha --league-url http://127.0.0.1:8000 --strategy random
```

**Terminal 4 - Player Beta:**
```bash
cd /path/to/agents-task7
python -m agents.player --port 8102 --display-name Beta --league-url http://127.0.0.1:8000 --strategy always_even
```

### What Happens

1. **League Manager** starts on port 8000 and waits for registrations
2. **Referee** starts on port 8001 and registers with League Manager
3. **Players** start on ports 8101+ and register with League Manager
4. **League Manager** creates match schedule
5. For each match:
   - League Manager calls Referee's `run_match` via JSON-RPC
   - Referee orchestrates the game with the two players
   - Referee returns the result to League Manager
   - League Manager updates standings

## Option 2: Using the Launcher Script

**Single command to run everything:**
```bash
cd /path/to/agents-task7
python scripts/run_league.py --use-external-referee --num-agents 4 --rounds 3
```

This will:
- Start the League Manager
- Start the Referee
- Spawn 4 player agents
- Run 3 rounds of competition
- Display final standings
- Clean up all processes

## Testing the Referee Standalone

### 1. Start Referee Without Registration
```bash
python -m agents.referee --port 8001 --no-register
```

### 2. Test Ping Method
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "ping",
    "params": {}
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "ok": true,
    "message": "pong"
  }
}
```

### 3. Test run_match Method (with mock players)

First start two players in separate terminals:
```bash
# Terminal 1
python -m agents.player --port 8101 --display-name Alpha --no-register

# Terminal 2
python -m agents.player --port 8102 --display-name Beta --no-register
```

Then call the referee:
```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "test_match",
    "method": "run_match",
    "params": {
      "match_id": "test_match_1",
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
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": "test_match",
  "result": {
    "match_id": "test_match_1",
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

## Command Line Arguments

### Referee Server

```
python -m agents.referee [OPTIONS]

Options:
  --host HOST              Host to bind to (default: 127.0.0.1)
  --port PORT              Port to bind to (default: 8001)
  --league-manager URL     League Manager URL (default: http://127.0.0.1:8000)
  --no-register            Don't register with League Manager (for testing)
  -h, --help               Show help message
```

### League Manager (with external referee support)

```
python -m agents.league_manager [OPTIONS]

Options:
  --port PORT              Port to bind to (default: 8000)
  --use-external-referee   Use external referee instead of embedded (default: False)
  --no-autostart           Don't auto-start league; wait for manual trigger
  --rounds N               Number of rounds per matchup (default: 3)
  -h, --help               Show help message
```

## Configuration Files

### Referee Config
Location: `SHARED/config/defaults/referee.json`

```json
{
  "host": "127.0.0.1",
  "port": 8001,
  "timeout": 30.0,
  "league_manager_url": "http://127.0.0.1:8000",
  "display_name": "Referee",
  "version": "1.0.0"
}
```

## Troubleshooting

### Referee won't connect to League Manager
- **Symptom**: Referee logs show "Cannot connect to League Manager"
- **Solution**: Ensure League Manager is started first and is running on the expected port
- **Note**: Referee will retry forever with exponential backoff - this is expected behavior

### League Manager says "No referee available"
- **Symptom**: League Manager error: "No referee available (neither external nor embedded)"
- **Solutions**:
  1. If using external referee: Start referee before running matches
  2. If using embedded referee: Don't pass `--use-external-referee` flag
  3. Check referee registered successfully (look for "Registered referee" in LM logs)

### Match timeout
- **Symptom**: Referee times out waiting for players
- **Solutions**:
  1. Check players are running and healthy
  2. Check player endpoints are correct
  3. Increase timeout in referee config
  4. Check network connectivity

## Architecture Diagram

```
┌──────────────────────────────────────────────────────┐
│              League Manager (Port 8000)              │
│  - Accepts registrations                             │
│  - Creates match schedule                            │
│  - Tracks standings                                  │
└──────────────────┬───────────────────────────────────┘
                   │
                   │ POST /mcp
                   │ method: run_match
                   ▼
┌──────────────────────────────────────────────────────┐
│               Referee (Port 8001)                    │
│  - Registers with League Manager                     │
│  - Orchestrates games                                │
│  - Implements game logic                             │
└──────────────────┬───────────────────────────────────┘
                   │
                   │ POST /mcp
                   │ methods: handle_game_invitation,
                   │          choose_parity,
                   │          notify_match_result
                   ▼
┌──────────────────────────────────────────────────────┐
│            Player Agents (Ports 8101+)               │
│  - Register with League Manager                      │
│  - Respond to referee calls                          │
│  - Implement strategies                              │
└──────────────────────────────────────────────────────┘
```

## Benefits of Separate Referee

1. **Separation of Concerns**: League Manager handles scheduling, Referee handles game logic
2. **Independent Scaling**: Referee can be scaled or replaced independently
3. **Better Testing**: Each component can be tested in isolation
4. **MCP Compliance**: All communication via standard JSON-RPC 2.0
5. **Fault Isolation**: Issues in referee don't crash the league
6. **Flexibility**: Different referees for different game types

## Next Steps

- See `docs/REFEREE_ARCHITECTURE.md` for detailed architecture
- See `tests/test_integration_http.py` for integration tests
- See `docs/MANUAL_TESTING_GUIDE.md` for comprehensive testing guide
