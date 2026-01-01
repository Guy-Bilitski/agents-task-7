# League Manager API Reference

## Base URL

```
http://127.0.0.1:<PORT>
```

Default port: 9000 (configurable with `--port`)

---

## Endpoints

### 1. Health Check

**GET** `/health`

Check if the League Manager is running and get basic stats.

**Response:**
```json
{
  "ok": true,
  "registered_agents": 4,
  "total_games": 12
}
```

**Example:**
```bash
curl http://127.0.0.1:8000/health
```

---

### 2. Register Agent

**POST** `/register`

Register a player agent or referee with the League Manager.

**Request Body:**
```json
{
  "display_name": "Alpha",
  "version": "1.0.0",
  "endpoint": "http://127.0.0.1:8101/mcp",
  "agent_type": "player"
}
```

**Fields:**
- `display_name` (required): Name of the agent
- `version` (required): Version string (e.g., "1.0.0")
- `endpoint` (required): Full MCP endpoint URL
- `agent_type` (optional): "player" or "referee" (default: "player")

**Response (Player):**
```json
{
  "status": "registered",
  "agent_id": "agent_Alpha",
  "message": "Welcome to the league, Alpha!"
}
```

**Response (Referee):**
```json
{
  "status": "registered",
  "agent_type": "referee",
  "message": "Referee RefereeBot registered successfully"
}
```

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{
    "display_name": "MyAgent",
    "version": "1.0.0",
    "endpoint": "http://127.0.0.1:8101/mcp"
  }'
```

---

### 3. List Agents

**GET** `/agents`

Get a list of all registered agents.

**Response:**
```json
{
  "agents": [
    {
      "display_name": "Alpha",
      "version": "1.0.0",
      "endpoint": "http://127.0.0.1:8101/mcp"
    },
    {
      "display_name": "Beta",
      "version": "1.0.0",
      "endpoint": "http://127.0.0.1:8102/mcp"
    }
  ]
}
```

**Example:**
```bash
curl http://127.0.0.1:8000/agents
```

---

### 4. Get Standings

**GET** `/standings`

Get current or final league standings.

**Response:**
```json
{
  "standings": [
    {
      "rank": 1,
      "agent": "Alpha",
      "points": 9,
      "wins": 3,
      "losses": 0,
      "draws": 0,
      "games_played": 3,
      "win_rate": "100.0%"
    },
    {
      "rank": 2,
      "agent": "Beta",
      "points": 6,
      "wins": 2,
      "losses": 1,
      "draws": 0,
      "games_played": 3,
      "win_rate": "66.7%"
    }
  ],
  "total_games": 6,
  "rounds_completed": 2
}
```

**Scoring:**
- Win: 3 points
- Draw: 1 point
- Loss: 0 points

**Example:**
```bash
curl http://127.0.0.1:8000/standings
```

---

### 5. Start Tournament ⭐ NEW!

**POST** `/start`

Start the league tournament with currently registered agents.

**Requirements:**
- At least 2 player agents must be registered
- League must not already be running

**Response (Success):**
```json
{
  "status": "started",
  "agents": 4,
  "rounds": 3,
  "message": "League starting with 4 agents"
}
```

**Response (Not Enough Agents):**
```json
{
  "error": "Need at least 2 agents to start league"
}
```
HTTP Status: 400

**Response (Already Running):**
```json
{
  "error": "League is already running"
}
```
HTTP Status: 409

**Example:**
```bash
curl -X POST http://127.0.0.1:8000/start
```

---

## Workflow Example

### 1. Start League Manager
```bash
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --rounds 5
```

### 2. Verify it's running
```bash
curl http://127.0.0.1:8000/health
# {"ok": true, "registered_agents": 0, "total_games": 0}
```

### 3. Start player agents (they auto-register)
```bash
# In separate terminals
PYTHONPATH=src python3 -m agents.player --port 8101 --display-name Alpha --league-url http://127.0.0.1:8000
PYTHONPATH=src python3 -m agents.player --port 8102 --display-name Beta --league-url http://127.0.0.1:8000
```

### 4. Check registered agents
```bash
curl http://127.0.0.1:8000/agents
# {"agents": [{"display_name": "Alpha", ...}, {"display_name": "Beta", ...}]}
```

### 5. Start the tournament
```bash
curl -X POST http://127.0.0.1:8000/start
# {"status": "started", "agents": 2, "rounds": 5, "message": "League starting with 2 agents"}
```

### 6. Monitor progress
Watch the League Manager terminal output for match results.

### 7. View final standings
```bash
curl http://127.0.0.1:8000/standings
```

---

## Error Codes

### HTTP Error Codes

- **200 OK**: Request successful
- **400 Bad Request**: Invalid request (missing fields, invalid data)
- **409 Conflict**: League already running
- **500 Internal Server Error**: Server error

### JSON Error Responses

```json
{
  "error": "Error message here"
}
```

---

## JSON-RPC 2.0 (For Agent Implementation)

Player agents must implement a JSON-RPC 2.0 endpoint at `POST /mcp`.

**Required methods:**
- `handle_game_invitation` - Accept game invitation
- `choose_parity` (and alias `parity_choose`) - Choose "even" or "odd"
- `notify_match_result` - Receive match result notification

See the [Player Agent Implementation Guide](../src/agents/player/README.md) for details.

---

## Configuration

### League Manager Options

```bash
PYTHONPATH=src python3 -m agents.league_manager [OPTIONS]
```

| Option | Description | Default |
|--------|-------------|---------|
| `--port PORT` | League Manager HTTP port | 9000 |
| `--server-only` | Run as server only (manual start) | False |
| `--use-external-referee` | Use external referee | False |
| `--rounds N` | Rounds per matchup | 3 |
| `--num-agents N` | Auto-spawn N agents (auto mode) | 4 |
| `--log-level LEVEL` | Log level (DEBUG/INFO/WARNING/ERROR) | INFO |

**Server-only mode** (recommended for manual control):
```bash
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only
```

**Auto mode** (spawns agents automatically):
```bash
PYTHONPATH=src python3 -m agents.league_manager --num-agents 6 --rounds 10
```

---

## See Also

- [START_TOURNAMENT.md](START_TOURNAMENT.md) - Step-by-step tournament guide
- [RUNNING_LEAGUE_MANAGER.md](RUNNING_LEAGUE_MANAGER.md) - League Manager detailed guide
- [MANUAL_TESTING_GUIDE.md](MANUAL_TESTING_GUIDE.md) - Testing with curl
- [QUICKSTART.md](../QUICKSTART.md) - Quick start guide
