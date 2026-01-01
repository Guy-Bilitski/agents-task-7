# Running the Agents

## Quick Start

### Verify Everything Works
```bash
python3 test_player_manual.py
```

### Start a Player Agent

```bash
python3 start_player.py --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000
```

### Start Multiple Agents (in separate terminals)

**Terminal 1:**
```bash
python3 start_player.py --port 8001 --display-name "Alpha" --league-url http://127.0.0.1:9000
```

**Terminal 2:**
```bash
python3 start_player.py --port 8002 --display-name "Beta" --league-url http://127.0.0.1:9000
```

**Terminal 3:**
```bash
python3 start_player.py --port 8003 --display-name "Gamma" --league-url http://127.0.0.1:9000
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
python3 start_player.py \
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
