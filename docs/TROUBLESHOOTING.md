# Troubleshooting Guide

## Common Issues and Solutions

### Port Already in Use

**Error:**
```
ERROR: Port 8000 is already in use
✗ Port 8000 is already in use. Try a different port with --port 8001
```

**Cause:** Another process is already using the port.

**Solutions:**

**Option 1: Use a different port**
```bash
# Use port 8010 instead
PYTHONPATH=src python3 -m agents.league_manager --port 8010 --server-only
```

**Option 2: Find and kill the process using the port**
```bash
# Find the process
lsof -ti:8000

# Kill it
lsof -ti:8000 | xargs kill

# Or in one command
lsof -ti:8000 | xargs kill -9
```

**Option 3: Use the cleanup script**
```bash
bash scripts/cleanup.sh
```

---

### Import Errors / Module Not Found

**Error:**
```
ModuleNotFoundError: No module named 'agents'
```

**Cause:** PYTHONPATH not set correctly.

**Solution:** Always set `PYTHONPATH=src` when running:
```bash
# Correct
PYTHONPATH=src python3 -m agents.league_manager --server-only

# Wrong
python3 -m agents.league_manager --server-only
```

---

### Components Not Registering

**Symptom:** Players or referee don't appear in `/agents` endpoint.

**Debugging Steps:**

1. **Check League Manager is running:**
```bash
curl http://127.0.0.1:8000/health
```

Should return: `{"ok": true, "registered_agents": N, "total_games": 0}`

2. **Check the component's logs:**
Look for registration messages in the component's terminal output.

**Player should show:**
```
✓ Registered with League Manager: Welcome to the league, Alpha!
```

**Referee should show:**
```
✓ Registered with League Manager: Referee Referee registered successfully
```

3. **Check the League Manager URL is correct:**
```bash
# Player registration uses --league-url
PYTHONPATH=src python3 -m agents.player \
  --port 8101 \
  --display-name Alpha \
  --league-url http://127.0.0.1:8000  # ← Must match LM port
```

4. **Check component health:**
```bash
curl http://127.0.0.1:8101/health  # Player
curl http://127.0.0.1:8001/health  # Referee
```

---

### Referee Not Found

**Error (in League Manager):**
```
RuntimeError: No referee available (neither external nor embedded)
```

**Cause:** League Manager is configured to use external referee but none is registered.

**Solutions:**

**Option 1: Start the referee**
```bash
PYTHONPATH=src python3 -m agents.referee \
  --port 8001 \
  --league-manager http://127.0.0.1:8000
```

**Option 2: Use embedded referee**
```bash
# Remove --use-external-referee flag
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only
```

---

### Connection Refused / Timeout

**Error:**
```
httpx.ConnectError: [Errno 111] Connection refused
```

**Cause:** Trying to connect to a component that isn't running.

**Solutions:**

1. **Check the component is running:**
```bash
# Check League Manager
curl http://127.0.0.1:8000/health

# Check Referee
curl http://127.0.0.1:8001/health

# Check Player
curl http://127.0.0.1:8101/health
```

2. **Check the ports match:**
```bash
# League Manager on 8000
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only

# Player must use same port in --league-url
PYTHONPATH=src python3 -m agents.player \
  --port 8101 \
  --display-name Alpha \
  --league-url http://127.0.0.1:8000  # ← Must be 8000
```

3. **Check firewall settings** (if running on different machines)

---

### JSON-RPC Errors

**Error:**
```
{"jsonrpc":"2.0","id":1,"error":{"code":-32601,"message":"Method not found"}}
```

**Cause:** Calling a method that doesn't exist.

**Common Method Names:**

**League Manager:**
- None (uses REST endpoints, not JSON-RPC)

**Referee:**
- `ping`
- `run_match`

**Players:**
- `ping`
- `handle_game_invitation`
- `choose_parity` (or `parity_choose`)
- `notify_match_result`

**Example Fix:**
```bash
# Wrong
curl -X POST http://127.0.0.1:8101/mcp \
  -d '{"jsonrpc":"2.0","id":1,"method":"parity_choice","params":{}}'

# Right (use choose_parity or parity_choose)
curl -X POST http://127.0.0.1:8101/mcp \
  -d '{"jsonrpc":"2.0","id":1,"method":"choose_parity","params":{"game_id":"test"}}'
```

---

### Server Starts Then Immediately Stops

**Symptom:** Server logs show startup, then immediately shuts down.

**Common Causes:**

1. **Port conflict** (see "Port Already in Use" above)
2. **Python version mismatch** (requires Python 3.10+)
3. **Missing dependencies**

**Check Python version:**
```bash
python3 --version
# Should be 3.10 or higher
```

**Install dependencies:**
```bash
pip install -r requirements.txt
# Or
pip install fastapi uvicorn httpx
```

---

### Tests Failing

**Error:**
```
ImportError: No module named 'agents'
```

**Solution:** Run tests with pytest from project root:
```bash
cd /path/to/agents-task7
PYTHONPATH=src pytest tests/
```

---

### Can't Stop Server (Ctrl+C doesn't work)

**Solution:** Force kill:
```bash
# Find Python processes
ps aux | grep python3

# Kill by PID
kill -9 <PID>

# Or use the cleanup script
bash scripts/cleanup.sh
```

---

### Logs Too Verbose / Too Quiet

**Too verbose:**
```bash
# Set log level to WARNING
PYTHONPATH=src python3 -m agents.league_manager \
  --port 8000 \
  --server-only \
  --log-level WARNING
```

**Too quiet:**
```bash
# Set log level to DEBUG
PYTHONPATH=src python3 -m agents.league_manager \
  --port 8000 \
  --server-only \
  --log-level DEBUG
```

---

## Getting Help

### Check Component Health

```bash
# League Manager
curl http://127.0.0.1:8000/health | python3 -m json.tool

# Referee
curl http://127.0.0.1:8001/health | python3 -m json.tool

# Player
curl http://127.0.0.1:8101/health | python3 -m json.tool
```

### Check Registered Agents

```bash
curl http://127.0.0.1:8000/agents | python3 -m json.tool
```

### Check Standings

```bash
curl http://127.0.0.1:8000/standings | python3 -m json.tool
```

### Enable Debug Logging

```bash
PYTHONPATH=src python3 -m agents.league_manager \
  --port 8000 \
  --server-only \
  --log-level DEBUG
```

### View Logs in Real-Time

If you redirected logs to files:
```bash
tail -f /tmp/lm.log     # League Manager
tail -f /tmp/ref.log    # Referee
tail -f /tmp/player.log # Player
```

---

## Still Having Issues?

1. **Clean everything and start fresh:**
```bash
bash scripts/cleanup.sh
rm -rf __pycache__ .pytest_cache
```

2. **Check the documentation:**
- `docs/RUNNING_LEAGUE_MANAGER.md`
- `docs/RUNNING_REFEREE.md`
- `docs/RUNNING_AGENTS.md`
- `SERVER_ONLY_MODE.md`

3. **Run the integration tests:**
```bash
PYTHONPATH=src pytest tests/ -v
```
