# Even-Odd League: Multi-Agent Competition System

[![CI Pipeline](https://github.com/YOUR_USERNAME/agents-task7/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_USERNAME/agents-task7/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A distributed multi-agent system where autonomous agents compete in parity games. All communication uses JSON-RPC 2.0 over HTTP.

---

## Quick Start

### Option 1: Complete System (External Referee) - **Recommended** ⭐

Run the entire system with one command:

```bash
python3 scripts/run_full_league.py
```

This automatically:
- Starts the League Manager on port 9000
- Starts an External Referee on port 8001
- Spawns 4 player agents (ports 8101-8104) with different strategies
- Runs a complete tournament
- Displays final standings

**Custom options:**
```bash
python3 scripts/run_full_league.py --num-agents 6    # Run with 6 agents
python3 scripts/run_full_league.py --rounds 5        # 5 rounds per matchup
python3 scripts/run_full_league.py --log-level DEBUG # Verbose logging
```

### Option 2: Manual Control

**Step 1: Start the League Manager**
```bash
PYTHONPATH=src python3 -m agents.league_manager --port 8000 --server-only --use-external-referee
```

**Step 2: Start the Referee**
```bash
PYTHONPATH=src python3 -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000
```

**Step 3: Start Player Agents** (in separate terminals)
```bash
PYTHONPATH=src python3 -m agents.player --port 8101 --display-name "Alpha" --league-url http://127.0.0.1:8000 --strategy random
PYTHONPATH=src python3 -m agents.player --port 8102 --display-name "Beta" --league-url http://127.0.0.1:8000 --strategy adaptive
PYTHONPATH=src python3 -m agents.player --port 8103 --display-name "Gamma" --league-url http://127.0.0.1:8000 --strategy counter
PYTHONPATH=src python3 -m agents.player --port 8104 --display-name "Delta" --league-url http://127.0.0.1:8000 --strategy always_even
```

**Step 4: Start the tournament**
```bash
curl -X POST http://127.0.0.1:8000/start
```

**Monitor progress:**
```bash
curl http://127.0.0.1:8000/standings
```

---

## Requirements

- Python 3.10+
- Dependencies: `fastapi`, `uvicorn`, `httpx`, `requests`

```bash
pip install fastapi uvicorn httpx requests
```

---

## System Architecture

```
┌─────────────────┐
│ League Manager  │  :9000 (Orchestration, REST API, Standings)
└────────┬────────┘
         │ JSON-RPC 2.0
    ┌────▼─────┐
    │ Referee  │  :8001 (Match execution)
    └────┬─────┘
         │ JSON-RPC 2.0
    ┌────┴──────┬──────────┬──────────┐
    │           │          │          │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│Player │  │Player │  │Player │  │Player │
│ 8101  │  │ 8102  │  │ 8103  │  │ 8104  │
└───────┘  └───────┘  └───────┘  └───────┘
```

### Components

**League Manager**
- Central orchestrator
- Manages agent registration
- Schedules round-robin matches
- Tracks standings and statistics
- REST API endpoints: `/health`, `/agents`, `/standings`, `/start`

**Referee**
- Runs individual matches
- Sends game invitations to players
- Collects parity choices
- Determines winners based on dice roll
- Notifies players of results

**Player Agents**
- Autonomous bots with different AI strategies
- Respond to game invitations
- Make parity choices (even/odd)
- Track statistics and match history

---

## Features

✅ **Distributed Architecture** - Each component runs independently
✅ **JSON-RPC 2.0 Protocol** - Standard, language-agnostic communication
✅ **9+ AI Strategies** - random, adaptive, counter, always_even, always_odd, and more
✅ **Plugin Architecture** - Extensible strategy system for custom implementations
✅ **Real-time Match Output** - See each agent's decision and outcome
✅ **Thread-safe State Management** - Concurrent request handling
✅ **Automatic Registration** - Background retry with exponential backoff
✅ **REST API** - Monitor league status and standings
✅ **Comprehensive Testing** - Unit, integration, and end-to-end tests
✅ **CI/CD Pipeline** - Automated testing, linting, and security scanning
✅ **Pre-commit Hooks** - Automated code quality checks
✅ **Professional Documentation** - PRD, ADD, and budget tracking  

---

## Available Strategies

| Strategy | Description |
|----------|-------------|
| `random` | 50/50 random choice (default) |
| `always_even` | Always chooses even |
| `always_odd` | Always chooses odd |
| `alternating` | Switches between even/odd each game |
| `adaptive` | Learns from wins/losses |
| `counter` | Tracks opponent patterns |
| `deterministic` | Hash-based, reproducible |
| `biased_random_70` | 70% even, 30% odd |
| `biased_random_30` | 30% even, 70% odd |

See [docs/STRATEGIES.md](docs/STRATEGIES.md) for detailed information.

---

## Documentation

### Project Planning & Design
- **[docs/PRODUCT_REQUIREMENTS.md](docs/PRODUCT_REQUIREMENTS.md)** - Product Requirements Document (PRD)
- **[docs/ARCHITECTURE_DESIGN.md](docs/ARCHITECTURE_DESIGN.md)** - Architecture Design Document (ADD)
- **[docs/BUDGET_TRACKING.md](docs/BUDGET_TRACKING.md)** - Budget and resource tracking

### Getting Started
- **[QUICKSTART.md](QUICKSTART.md)** - Complete beginner guide with examples
- **[docs/START_TOURNAMENT.md](docs/START_TOURNAMENT.md)** - How to start tournaments
- **[docs/RUNNING_MODES.md](docs/RUNNING_MODES.md)** - Comparison of running modes
- **[QUICK_REFERENCE.md](QUICK_REFERENCE.md)** - Command quick reference

### Reference
- **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)** - Complete API documentation
- **[docs/UNDERSTANDING_MATCH_OUTPUT.md](docs/UNDERSTANDING_MATCH_OUTPUT.md)** - Reading match decisions
- **[docs/STRATEGIES.md](docs/STRATEGIES.md)** - AI strategy details
- **[docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Architecture overview

### Extensibility
- **[docs/PLUGIN_DEVELOPMENT.md](docs/PLUGIN_DEVELOPMENT.md)** - Creating custom strategy plugins
- **[docs/STRATEGY_IMPLEMENTATION.md](docs/STRATEGY_IMPLEMENTATION.md)** - How to add new strategies

### Running Components
- **[docs/RUNNING_LEAGUE_MANAGER.md](docs/RUNNING_LEAGUE_MANAGER.md)** - League Manager guide
- **[docs/RUNNING_REFEREE.md](docs/RUNNING_REFEREE.md)** - Referee guide
- **[docs/RUNNING_AGENTS.md](docs/RUNNING_AGENTS.md)** - Player agent guide

### Development & Contributing
- **[CONTRIBUTING.md](CONTRIBUTING.md)** - Contribution guidelines
- **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[docs/MANUAL_TESTING_GUIDE.md](docs/MANUAL_TESTING_GUIDE.md)** - Testing with curl

---

## Project Structure

```
.
├── .github/
│   └── workflows/
│       └── ci.yml            # CI/CD pipeline configuration
│
├── src/
│   ├── agents/
│   │   ├── player/           # Player agent implementation
│   │   │   └── plugins/      # Strategy plugins directory
│   │   ├── league_manager/   # Central orchestrator
│   │   └── referee/          # Match runner
│   └── shared/               # Shared utilities (JSON-RPC, HTTP, logging)
│
├── scripts/                   # Convenience scripts
│   ├── run_full_league.py    # Complete system runner
│   ├── run_league.py         # Simplified system (embedded referee)
│   ├── start_player.py       # Start individual player
│   ├── start_referee.py      # Start referee
│   └── cleanup.sh            # Clean up processes
│
├── tests/                     # Test suite
│   ├── test_*.py             # Unit and integration tests
│   └── manual/               # Manual testing scripts
│
├── docs/                      # Documentation
│   ├── PRODUCT_REQUIREMENTS.md
│   ├── ARCHITECTURE_DESIGN.md
│   ├── BUDGET_TRACKING.md
│   └── ...                   # Additional documentation
│
├── .pre-commit-config.yaml   # Pre-commit hooks configuration
├── pyproject.toml            # Project config with linting tools
└── SHARED/                    # Runtime data (config, logs, league data)
```

---

## Common Commands

```bash
# Run complete league (easiest)
python3 scripts/run_full_league.py

# Run with more agents
python3 scripts/run_full_league.py --num-agents 6

# Check status
curl http://127.0.0.1:9000/health
curl http://127.0.0.1:9000/agents
curl http://127.0.0.1:9000/standings

# Start tournament (manual mode)
curl -X POST http://127.0.0.1:9000/start

# Clean up processes
bash scripts/cleanup.sh

# Run tests
pytest tests/
```

---

## Troubleshooting

### Port Already in Use
```bash
bash scripts/cleanup.sh
```

### Agents Not Registering
- Ensure League Manager is running first
- Check the `--league-url` matches the League Manager's address
- Verify connectivity: `curl http://127.0.0.1:9000/health`
- Enable debug logging: `--log-level DEBUG`

### Import Errors
Make sure you're in the project root directory and using `PYTHONPATH=src` when running modules directly.

See [docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) for more solutions.

---

## Development Setup

### Install Development Dependencies

```bash
pip install -e ".[dev]"
```

### Pre-commit Hooks

Install and run pre-commit hooks for automated code quality:

```bash
# Install hooks
pip install pre-commit
pre-commit install

# Run on all files
pre-commit run --all-files
```

### Code Quality Tools

The project uses several code quality tools configured in `pyproject.toml`:

| Tool | Purpose | Command |
|------|---------|---------|
| **black** | Code formatting | `black src/ tests/` |
| **isort** | Import sorting | `isort src/ tests/` |
| **flake8** | Linting | `flake8 src/` |
| **pylint** | Advanced linting | `pylint src/` |
| **mypy** | Type checking | `mypy src/` |
| **bandit** | Security scanning | `bandit -r src/` |

### CI/CD Pipeline

The GitHub Actions pipeline (`.github/workflows/ci.yml`) automatically runs:
- Code formatting checks (black, isort)
- Linting (flake8, pylint)
- Type checking (mypy)
- Tests on Python 3.10, 3.11, 3.12
- Security scanning (bandit, safety)
- Package build verification

---

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_jsonrpc.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=html

# Run only unit tests
pytest tests/ -v -m unit

# Run only integration tests
pytest tests/ -v -m integration
```

---

## Protocol Compliance

The system implements strict JSON-RPC 2.0 specification:
- All requests/responses use proper JSON-RPC 2.0 envelopes
- Standard error codes (-32700 through -32603)
- Method aliasing support (`choose_parity` / `parity_choose`)
- Extra fields accepted without rejection
- Graceful error handling without crashes

---

## License

MIT
