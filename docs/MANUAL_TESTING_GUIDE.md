# Manual Testing Guide - Even-Odd League

This guide shows you how to manually run each agent separately and control the messages between them using `curl` or other HTTP tools.

## ✅ Status: All Import Issues Fixed!

The import paths have been corrected. The system is now fully functional!

---

## Quick Verification

Run the automated test to verify everything works:

```bash
python3 test_player_manual.py
```

This will start an agent, test all endpoints, and clean up automatically.

---

## Manual Testing Steps

### Step 1: Start a Player Agent

Players are agents that respond to game invitations and make parity choices.

**Terminal 1:**
```bash
# Start Player 1 on port 8001
python3 start_player.py --port 8001 --display-name "Alice" --league-url http://127.0.0.1:9000

# Expected output:
# MCP Agent Starting
# Display Name: Alice
# Port: 8001
# MCP Endpoint: http://127.0.0.1:8001/mcp
# Starting HTTP server on http://127.0.0.1:8001
```

**Test the player is running:**
```bash
curl http://127.0.0.1:8001/health
# Expected: {"ok":true}
```

---

### Step 2: Start More Players (Optional)

**Terminal 2:**
```bash
python3 start_player.py --port 8002 --display-name "Bob" --league-url http://127.0.0.1:9000
```

**Terminal 3:**
```bash
python3 start_player.py --port 8003 --display-name "Charlie" --league-url http://127.0.0.1:9000
```

---

## Manual Message Testing with curl

Now you can manually send JSON-RPC messages to test the protocol.

### 1. Send a Game Invitation to a Player

```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "handle_game_invitation",
    "params": {
      "game_id": "game-001",
      "from_player": "league",
      "invitation_id": "inv-001"
    },
    "id": 1
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "type": "GAME_JOIN_ACK",
    "accepted": true,
    "game_id": "game-001",
    "invitation_id": "inv-001"
  }
}
```

### 2. Ask a Player to Choose Parity

```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "parity_choose",
    "params": {
      "game_id": "game-001"
    },
    "id": 2
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "type": "RESPONSE_PARITY_CHOOSE",
    "choice": "even",
    "game_id": "game-001"
  }
}
```

Note: The `choice` will be either `"even"` or `"odd"` (deterministic based on game_id).

### 3. Test the `choose_parity` Alias

The agent also supports `choose_parity` as an alias for `parity_choose`:

```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "choose_parity",
    "params": {
      "game_id": "game-001"
    },
    "id": 2
  }'
```

This will return the same response format.

### 4. Notify a Player of Match Result

```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "notify_match_result",
    "params": {
      "game_id": "game-001",
      "winner": "Alice",
      "details": {
        "rolled": 7,
        "parity": "odd",
        "alice_choice": "even",
        "bob_choice": "odd"
      }
    },
    "id": 3
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "ok": true
  }
}
```

### 5. Test Invalid Method (should return error)

```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "method": "invalid_method",
    "params": {},
    "id": 4
  }'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": 4,
  "error": {
    "code": -32601,
    "message": "Method not found",
    "data": "Method 'invalid_method' is not supported"
  }
}
```

### 6. Test Invalid JSON (should return parse error)

```bash
curl -X POST http://127.0.0.1:8001/mcp \
  -H "Content-Type: application/json" \
  -d 'not valid json'
```

**Expected Response:**
```json
{
  "jsonrpc": "2.0",
  "id": null,
  "error": {
    "code": -32700,
    "message": "Parse error"
  }
}
```

---

## Using Python to Send Messages

You can also use Python scripts for more control:

```python
#!/usr/bin/env python3
import requests
import json

def send_jsonrpc(url, method, params, request_id=1):
    """Send a JSON-RPC 2.0 request."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "params": params,
        "id": request_id
    }
    
    response = requests.post(url, json=payload)
    return response.json()

# Example: Invite a player to a game
result = send_jsonrpc(
    url="http://127.0.0.1:8001/mcp",
    method="handle_game_invitation",
    params={
        "game_id": "test-game-1",
        "from_player": "referee",
        "invitation_id": "inv-123"
    }
)

print(json.dumps(result, indent=2))
```

---

## Simulating a Complete Game Flow

Here's a complete sequence to simulate a match between Alice (8001) and Bob (8002):

```bash
# 1. Invite Alice
curl -X POST http://127.0.0.1:8001/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"handle_game_invitation","params":{"game_id":"match-1","from_player":"referee"},"id":1}'

# 2. Invite Bob
curl -X POST http://127.0.0.1:8002/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"handle_game_invitation","params":{"game_id":"match-1","from_player":"referee"},"id":2}'

# 3. Get Alice's parity choice
curl -X POST http://127.0.0.1:8001/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"parity_choose","params":{"game_id":"match-1"},"id":3}'

# 4. Get Bob's parity choice
curl -X POST http://127.0.0.1:8002/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"parity_choose","params":{"game_id":"match-1"},"id":4}'

# 5. Notify Alice of result (assume Alice won)
curl -X POST http://127.0.0.1:8001/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"notify_match_result","params":{"game_id":"match-1","winner":"Alice","details":{}},"id":5}'

# 6. Notify Bob of result
curl -X POST http://127.0.0.1:8002/mcp -H "Content-Type: application/json" -d '{"jsonrpc":"2.0","method":"notify_match_result","params":{"game_id":"match-1","winner":"Alice","details":{}},"id":6}'
```

---

## Using HTTPie (Prettier Alternative to curl)

If you have HTTPie installed (`pip install httpie`), the syntax is cleaner:

```bash
# Send game invitation
http POST :8001/mcp \
  jsonrpc=2.0 \
  method=handle_game_invitation \
  params:='{"game_id":"g1","from_player":"ref"}' \
  id:=1

# Get parity choice
http POST :8001/mcp \
  jsonrpc=2.0 \
  method=parity_choose \
  params:='{"game_id":"g1"}' \
  id:=2
```

---

## Debugging Tips

### Check Logs

Players log all incoming requests, so you can see what they receive:

```bash
# In the terminal running the player, you'll see:
# [INFO] JSON-RPC request: method=handle_game_invitation, id=1
# [INFO] Method 'handle_game_invitation' succeeded
```

### Use More Verbose Logging

Start the agent with DEBUG level logging:

```bash
python3 start_player.py \
  --port 8001 \
  --display-name "Alice" \
  --league-url http://127.0.0.1:9000 \
  --log-level DEBUG
```

---

## Key Features Verified

✅ JSON-RPC 2.0 compliant endpoints  
✅ `handle_game_invitation` - accepts invitations and stores state  
✅ `parity_choose` - makes deterministic parity choices  
✅ `choose_parity` - alias method also works  
✅ `notify_match_result` - updates win/loss statistics  
✅ Error handling - proper JSON-RPC error codes  
✅ Health checks - `/health` endpoint  
✅ Background registration - retries with exponential backoff  
✅ Graceful shutdown - Ctrl+C handling  
✅ Thread-safe state management  

---

## Next Steps

1. **Explore the code**:
   - `src/agents/player/` - Player agent implementation
   - `src/shared/jsonrpc.py` - JSON-RPC protocol handling
   - `src/agents/player/state.py` - State management
   - `src/agents/player/tools.py` - Tool handlers

2. **Implement additional features**:
   - League Manager (if needed)
   - Referee (if needed)
   - More sophisticated parity strategies

3. **Run the full league** (if League Manager is implemented):
   ```bash
   python3 run_league.py --num-agents 4 --rounds 3
   ```

---

## Tools Recommendation

For easier manual testing, consider using:
- **Postman** - GUI for REST API testing
- **Insomnia** - Alternative to Postman
- **HTTPie** - Command-line tool with better syntax than curl
- **Python requests** - Script your test scenarios

All of these work great with JSON-RPC!
