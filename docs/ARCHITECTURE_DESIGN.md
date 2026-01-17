# Architecture Design Document (ADD)

## Even-Odd League: Multi-Agent Competition System

**Document Version:** 1.0
**Last Updated:** January 2026
**Status:** Approved

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Architectural Goals and Constraints](#2-architectural-goals-and-constraints)
3. [System Overview](#3-system-overview)
4. [Architectural Patterns](#4-architectural-patterns)
5. [Component Architecture](#5-component-architecture)
6. [Data Architecture](#6-data-architecture)
7. [Communication Architecture](#7-communication-architecture)
8. [Plugin Architecture](#8-plugin-architecture)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Security Architecture](#10-security-architecture)
11. [Quality Attributes](#11-quality-attributes)
12. [Architectural Decision Records](#12-architectural-decision-records)

---

## 1. Introduction

### 1.1 Purpose

This document describes the software architecture of the Even-Odd League Multi-Agent Competition System. It provides a comprehensive view of the system's structure, components, relationships, and design decisions.

### 1.2 Scope

This architecture covers:
- All three agent types (League Manager, Referee, Player)
- Communication protocols and data flows
- Plugin extensibility mechanisms
- Deployment configurations

### 1.3 Definitions and Acronyms

| Term | Definition |
|------|------------|
| ADD | Architecture Design Document |
| ADR | Architecture Decision Record |
| API | Application Programming Interface |
| JSON-RPC | JSON Remote Procedure Call |
| MCP | Model Context Protocol |
| REST | Representational State Transfer |

---

## 2. Architectural Goals and Constraints

### 2.1 Architectural Goals

| ID | Goal | Priority |
|----|------|----------|
| AG-1 | **Modularity**: Each component can be developed, tested, and deployed independently | High |
| AG-2 | **Extensibility**: New strategies and agents can be added without core changes | High |
| AG-3 | **Protocol Standardization**: Use industry-standard protocols (JSON-RPC 2.0) | High |
| AG-4 | **Observability**: System state is transparent and monitorable | Medium |
| AG-5 | **Simplicity**: Minimize dependencies and complexity | Medium |

### 2.2 Constraints

| ID | Constraint | Rationale |
|----|------------|-----------|
| C-1 | Python 3.10+ runtime | Modern language features, type hints |
| C-2 | HTTP transport only | Simplicity, wide tooling support |
| C-3 | In-memory state | Simplifies deployment, suitable for educational use |
| C-4 | Single-host deployment | Initial scope limitation |
| C-5 | No authentication | Educational system, trusted environment |

### 2.3 Key Quality Attributes

```
                    ┌─────────────────┐
                    │   Modularity    │
                    │      ★★★★★      │
                    └────────┬────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐   ┌───────────────┐   ┌───────────────┐
│ Extensibility │   │  Simplicity   │   │ Testability   │
│    ★★★★☆      │   │    ★★★★★      │   │    ★★★★★      │
└───────────────┘   └───────────────┘   └───────────────┘
```

---

## 3. System Overview

### 3.1 Context Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│                         SYSTEM BOUNDARY                             │
│                                                                     │
│  ┌─────────────────────────────────────────────────────────────┐    │
│  │               EVEN-ODD LEAGUE SYSTEM                        │    │
│  │                                                             │    │
│  │   ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │    │
│  │   │   League     │  │   Referee    │  │   Player     │     │    │
│  │   │   Manager    │◄─┤              │◄─┤   Agents     │     │    │
│  │   │              │  │              │  │   (1..N)     │     │    │
│  │   └──────────────┘  └──────────────┘  └──────────────┘     │    │
│  │          │                                                  │    │
│  │          │ REST API                                         │    │
│  │          ▼                                                  │    │
│  │   ┌──────────────┐                                          │    │
│  │   │  Monitoring  │                                          │    │
│  │   │  Interface   │                                          │    │
│  │   └──────────────┘                                          │    │
│  │                                                             │    │
│  └─────────────────────────────────────────────────────────────┘    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
        │
        │  HTTP/REST
        ▼
┌───────────────┐
│   External    │
│   Operator    │
│   (Human/     │
│    Script)    │
└───────────────┘
```

### 3.2 Container Diagram

```
┌────────────────────────────────────────────────────────────────────┐
│                                                                    │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                    LEAGUE MANAGER                          │    │
│  │                    Container: Python/FastAPI               │    │
│  │                    Port: 9000                              │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │    │
│  │  │   REST API   │ │  Tournament  │ │   Agent      │        │    │
│  │  │   Handler    │ │  Scheduler   │ │   Registry   │        │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘        │    │
│  │  ┌──────────────┐ ┌──────────────┐                         │    │
│  │  │  Standings   │ │    State     │                         │    │
│  │  │   Tracker    │ │   Manager    │                         │    │
│  │  └──────────────┘ └──────────────┘                         │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              │                                     │
│                              │ JSON-RPC 2.0 / HTTP                 │
│                              ▼                                     │
│  ┌────────────────────────────────────────────────────────────┐    │
│  │                       REFEREE                              │    │
│  │                    Container: Python/FastAPI               │    │
│  │                    Port: 8001                              │    │
│  │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐        │    │
│  │  │    Match     │ │    Game      │ │   Result     │        │    │
│  │  │ Orchestrator │ │   Engine     │ │  Reporter    │        │    │
│  │  └──────────────┘ └──────────────┘ └──────────────┘        │    │
│  │  ┌──────────────┐                                          │    │
│  │  │   HTTP       │                                          │    │
│  │  │   Client     │                                          │    │
│  │  └──────────────┘                                          │    │
│  └────────────────────────────────────────────────────────────┘    │
│                              │                                     │
│                              │ JSON-RPC 2.0 / HTTP                 │
│              ┌───────────────┼───────────────┐                     │
│              │               │               │                     │
│              ▼               ▼               ▼                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                │
│  │   PLAYER A   │ │   PLAYER B   │ │   PLAYER N   │                │
│  │  Port: 8101  │ │  Port: 8102  │ │  Port: 810N  │                │
│  │  ┌────────┐  │ │  ┌────────┐  │ │  ┌────────┐  │                │
│  │  │Strategy│  │ │  │Strategy│  │ │  │Strategy│  │                │
│  │  │ Plugin │  │ │  │ Plugin │  │ │  │ Plugin │  │                │
│  │  └────────┘  │ │  └────────┘  │ │  └────────┘  │                │
│  │  ┌────────┐  │ │  ┌────────┐  │ │  ┌────────┐  │                │
│  │  │ State  │  │ │  │ State  │  │ │  │ State  │  │                │
│  │  │Manager │  │ │  │Manager │  │ │  │Manager │  │                │
│  │  └────────┘  │ │  └────────┘  │ │  └────────┘  │                │
│  └──────────────┘ └──────────────┘ └──────────────┘                │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## 4. Architectural Patterns

### 4.1 Service-Oriented Architecture (SOA)

The system employs a lightweight service-oriented architecture where each agent operates as an independent service.

**Benefits:**
- Independent deployment and scaling
- Technology agnosticism (agents can be reimplemented in any language)
- Clear service boundaries

**Implementation:**
```
Each Agent = Microservice with:
├── HTTP Server (FastAPI/Uvicorn)
├── JSON-RPC Handler (POST /mcp)
├── REST Endpoints (GET /health, etc.)
└── Internal Business Logic
```

### 4.2 Event-Driven Communication

Match execution follows an event-driven pattern:

```
┌─────────────────────────────────────────────────────────────┐
│                     MATCH LIFECYCLE                         │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  1. INVITATION EVENT                                        │
│     Referee ──► Player A: handle_game_invitation            │
│     Referee ──► Player B: handle_game_invitation            │
│                                                             │
│  2. CHOICE EVENT                                            │
│     Referee ──► Player A: choose_parity → "even"            │
│     Referee ──► Player B: choose_parity → "odd"             │
│                                                             │
│  3. RESOLUTION EVENT                                        │
│     Referee: dice_roll = random(1, 100)                     │
│     Referee: determine_winner()                             │
│                                                             │
│  4. NOTIFICATION EVENT                                      │
│     Referee ──► Player A: notify_match_result               │
│     Referee ──► Player B: notify_match_result               │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.3 Strategy Pattern

Player agents use the Strategy pattern for parity selection:

```
                    ┌─────────────────────┐
                    │  ParityStrategy     │
                    │  <<abstract>>       │
                    ├─────────────────────┤
                    │ + choose()          │
                    │ + get_name()        │
                    └──────────┬──────────┘
                               │
           ┌───────────────────┼───────────────────┐
           │                   │                   │
           ▼                   ▼                   ▼
┌─────────────────┐ ┌─────────────────┐ ┌─────────────────┐
│ RandomStrategy  │ │AdaptiveStrategy │ │ CounterStrategy │
├─────────────────┤ ├─────────────────┤ ├─────────────────┤
│ + choose()      │ │ + choose()      │ │ + choose()      │
│ + get_name()    │ │ + get_name()    │ │ + get_name()    │
└─────────────────┘ └─────────────────┘ └─────────────────┘
```

### 4.4 Plugin Architecture

The system supports runtime-loadable strategy plugins:

```
┌─────────────────────────────────────────────────────────────┐
│                    PLUGIN SYSTEM                            │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Plugin Manager                         │    │
│  │  - discover_plugins(directory)                      │    │
│  │  - load_plugin(module_path)                         │    │
│  │  - register_strategy(strategy)                      │    │
│  └─────────────────────────────────────────────────────┘    │
│                          │                                  │
│                          ▼                                  │
│  ┌─────────────────────────────────────────────────────┐    │
│  │              Strategy Registry                      │    │
│  │  {                                                  │    │
│  │    "random": RandomStrategy(),                      │    │
│  │    "adaptive": AdaptiveStrategy(),                  │    │
│  │    "my_custom": MyCustomStrategy(),  # Plugin      │    │
│  │  }                                                  │    │
│  └─────────────────────────────────────────────────────┘    │
│                                                             │
│  Plugin Directory Structure:                                │
│  plugins/                                                   │
│  ├── my_strategy/                                           │
│  │   ├── __init__.py                                        │
│  │   └── strategy.py  (implements ParityStrategy)           │
│  └── another_strategy/                                      │
│      └── ...                                                │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 5. Component Architecture

### 5.1 League Manager Components

```
src/agents/league_manager/
├── __main__.py          # Entry point
├── app.py               # FastAPI application
├── manager.py           # Core orchestration logic
├── config.py            # Configuration management
└── tools.py             # JSON-RPC method handlers

┌──────────────────────────────────────────────────────────┐
│                   LeagueManager Class                    │
├──────────────────────────────────────────────────────────┤
│ Responsibilities:                                        │
│ - Maintain agent registry                                │
│ - Generate round-robin schedule                          │
│ - Coordinate with referee for match execution            │
│ - Track and compute standings                            │
│                                                          │
│ Dependencies:                                            │
│ - FastAPI (HTTP server)                                  │
│ - httpx (HTTP client for referee communication)          │
│                                                          │
│ State:                                                   │
│ - agents: Dict[str, AgentInfo]                           │
│ - matches: List[MatchResult]                             │
│ - standings: Dict[str, StandingsEntry]                   │
│ - tournament_state: Enum(NOT_STARTED, RUNNING, DONE)     │
└──────────────────────────────────────────────────────────┘
```

### 5.2 Referee Components

```
src/agents/referee/
├── __main__.py          # Entry point
├── app.py               # FastAPI application
├── referee.py           # Core match execution logic
└── client.py            # HTTP client for player communication

┌──────────────────────────────────────────────────────────┐
│                     Referee Class                        │
├──────────────────────────────────────────────────────────┤
│ Responsibilities:                                        │
│ - Send game invitations to players                       │
│ - Collect parity choices                                 │
│ - Generate random dice rolls                             │
│ - Determine match winners                                │
│ - Notify players of results                              │
│                                                          │
│ Key Methods:                                             │
│ - run_game(player_a, player_b) -> MatchResult            │
│ - _send_invitation(player) -> bool                       │
│ - _get_parity_choice(player) -> str                      │
│ - _notify_result(player, result) -> None                 │
└──────────────────────────────────────────────────────────┘
```

### 5.3 Player Agent Components

```
src/agents/player/
├── __init__.py          # Logging setup
├── main.py              # Entry point
├── app.py               # FastAPI application
├── config.py            # CLI argument parsing
├── strategy.py          # AI strategy implementations
├── state.py             # Player state management
├── tools.py             # JSON-RPC method handlers
├── registration.py      # League registration
├── selftest.py          # Self-test harness
└── plugins/             # External strategy plugins

┌──────────────────────────────────────────────────────────┐
│                   Player Agent Class                     │
├──────────────────────────────────────────────────────────┤
│ Responsibilities:                                        │
│ - Register with league manager                           │
│ - Respond to game invitations                            │
│ - Select parity using configured strategy                │
│ - Track game history and statistics                      │
│                                                          │
│ Key Components:                                          │
│ - Strategy: Pluggable decision-making                    │
│ - State: Game history, win/loss stats                    │
│ - Registration: Background retry with backoff            │
└──────────────────────────────────────────────────────────┘
```

---

## 6. Data Architecture

### 6.1 Data Flow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         DATA FLOWS                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  REGISTRATION FLOW                                              │
│  ─────────────────                                              │
│  Player ──POST /register──► League Manager                      │
│         {display_name, version, endpoint}                       │
│                                                                 │
│  League Manager ──Response──► Player                            │
│                 {status, agent_id, message}                     │
│                                                                 │
│  MATCH EXECUTION FLOW                                           │
│  ────────────────────                                           │
│  Referee ──JSON-RPC──► Player                                   │
│          {method: "choose_parity", params: {game_id}}           │
│                                                                 │
│  Player ──Response──► Referee                                   │
│         {result: "even" | "odd"}                                │
│                                                                 │
│  RESULT NOTIFICATION FLOW                                       │
│  ────────────────────────                                       │
│  Referee ──JSON-RPC──► Player                                   │
│          {method: "notify_match_result",                        │
│           params: {game_id, won, opponent, dice_roll}}          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 6.2 State Management

```
┌─────────────────────────────────────────────────────────────────┐
│                     STATE ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  LEAGUE MANAGER STATE                                           │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  agents: Dict[agent_id, AgentInfo]                      │    │
│  │  referee: Optional[RefereeInfo]                         │    │
│  │  matches: List[MatchResult]                             │    │
│  │  tournament_state: Enum                                 │    │
│  │  current_round: int                                     │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  PLAYER STATE                                                   │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  games_played: int                                      │    │
│  │  wins: int                                              │    │
│  │  losses: int                                            │    │
│  │  draws: int                                             │    │
│  │  history: List[GameRecord]                              │    │
│  │  strategy: ParityStrategy                               │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  Note: All state is in-memory. For persistence, use             │
│  repositories in src/shared/repositories/                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7. Communication Architecture

### 7.1 Protocol Specification

**JSON-RPC 2.0 Compliance:**

```json
// Request format
{
  "jsonrpc": "2.0",
  "method": "choose_parity",
  "params": {"game_id": "game-123"},
  "id": 1
}

// Success response
{
  "jsonrpc": "2.0",
  "result": "even",
  "id": 1
}

// Error response
{
  "jsonrpc": "2.0",
  "error": {
    "code": -32601,
    "message": "Method not found"
  },
  "id": 1
}
```

### 7.2 Error Codes

| Code | Name | Description |
|------|------|-------------|
| -32700 | Parse error | Invalid JSON |
| -32600 | Invalid Request | Invalid JSON-RPC request |
| -32601 | Method not found | Method does not exist |
| -32602 | Invalid params | Invalid method parameters |
| -32603 | Internal error | Internal JSON-RPC error |

### 7.3 Endpoint Mapping

| Component | Endpoint | Protocol | Purpose |
|-----------|----------|----------|---------|
| League Manager | POST /mcp | JSON-RPC 2.0 | Agent communication |
| League Manager | GET /health | REST | Health check |
| League Manager | POST /register | REST | Agent registration |
| League Manager | GET /agents | REST | List agents |
| League Manager | GET /standings | REST | Get standings |
| League Manager | POST /start | REST | Start tournament |
| Referee | POST /mcp | JSON-RPC 2.0 | Match commands |
| Referee | GET /health | REST | Health check |
| Player | POST /mcp | JSON-RPC 2.0 | Game actions |
| Player | GET /health | REST | Health check |

---

## 8. Plugin Architecture

### 8.1 Plugin Interface

All strategy plugins must implement the `ParityStrategy` abstract base class:

```python
from abc import ABC, abstractmethod

class ParityStrategy(ABC):
    """Base class for parity selection strategies."""

    @abstractmethod
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        """Choose parity for a game.

        Args:
            game_id: Unique game identifier
            history: List of previous game results
            stats: Current player statistics

        Returns:
            Either "even" or "odd"
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return the strategy name."""
        pass
```

### 8.2 Plugin Discovery

```
Plugin Loading Sequence:
─────────────────────────

1. Startup
   │
   ▼
2. Scan plugins/ directory
   │
   ▼
3. For each subdirectory:
   ├── Import module
   ├── Find ParityStrategy subclass
   └── Register in STRATEGIES dict
   │
   ▼
4. Strategies available for selection via --strategy flag
```

### 8.3 Creating a Plugin

```
plugins/
└── my_strategy/
    ├── __init__.py
    └── strategy.py

# strategy.py
from agents.player.strategy import ParityStrategy

class MyCustomStrategy(ParityStrategy):
    def choose(self, game_id: str, history: list, stats: dict) -> str:
        # Custom logic here
        return "even"

    def get_name(self) -> str:
        return "my_custom"

# Exported for plugin discovery
STRATEGY_CLASS = MyCustomStrategy
```

---

## 9. Deployment Architecture

### 9.1 Single-Host Deployment

```
┌─────────────────────────────────────────────────────────────────┐
│                         HOST MACHINE                            │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │                    Python Runtime                       │    │
│  │                    (Python 3.10+)                       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────────┐    │
│  │   League    │ │   Referee   │ │   Player Agents (1-N)   │    │
│  │   Manager   │ │             │ │                         │    │
│  │   :9000     │ │   :8001     │ │   :8101, :8102, ...     │    │
│  └─────────────┘ └─────────────┘ └─────────────────────────┘    │
│                                                                 │
│  Network: localhost (127.0.0.1)                                 │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 9.2 Port Allocation

| Component | Default Port | Range |
|-----------|--------------|-------|
| League Manager | 9000 | 9000-9099 |
| Referee | 8001 | 8001-8099 |
| Player Agents | 8101+ | 8101-8199 |

### 9.3 Startup Sequence

```
1. Start League Manager
   python -m agents.league_manager --port 9000
   │
   ▼
2. Start Referee
   python -m agents.referee --port 8001 --league-manager http://127.0.0.1:9000
   │
   ▼
3. Start Player Agents (any order)
   python -m agents.player --port 8101 --league-url http://127.0.0.1:9000
   python -m agents.player --port 8102 --league-url http://127.0.0.1:9000
   │
   ▼
4. Trigger Tournament
   curl -X POST http://127.0.0.1:9000/start
```

---

## 10. Security Architecture

### 10.1 Security Model

```
┌─────────────────────────────────────────────────────────────────┐
│                     SECURITY BOUNDARIES                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  TRUST BOUNDARY: localhost                                      │
│  ─────────────────────────                                      │
│  - All components run on same host                              │
│  - No external network access required                          │
│  - No authentication (trusted environment)                      │
│                                                                 │
│  INPUT VALIDATION                                               │
│  ────────────────                                               │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │  All JSON-RPC requests validated:                       │    │
│  │  - JSON syntax (parse_error if invalid)                 │    │
│  │  - Required fields (invalid_request if missing)         │    │
│  │  - Method existence (method_not_found if unknown)       │    │
│  │  - Parameter types (invalid_params if wrong type)       │    │
│  └─────────────────────────────────────────────────────────┘    │
│                                                                 │
│  SAFE DEFAULTS                                                  │
│  ─────────────                                                  │
│  - Bind to 127.0.0.1 by default                                 │
│  - No file system writes (except logs)                          │
│  - No credential storage                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 10.2 Threat Model

| Threat | Mitigation | Status |
|--------|------------|--------|
| Malformed JSON injection | JSON-RPC validation | Mitigated |
| Resource exhaustion | In-memory limits | Partial |
| Network interception | Localhost-only by default | Mitigated |
| Unauthorized tournament start | None (trusted environment) | Accepted |

---

## 11. Quality Attributes

### 11.1 Testability

```
┌─────────────────────────────────────────────────────────────────┐
│                      TEST ARCHITECTURE                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  tests/                                                         │
│  ├── test_jsonrpc.py         # Protocol unit tests             │
│  ├── test_state.py           # State management tests          │
│  ├── test_tools.py           # Tool handler tests              │
│  ├── test_registration.py    # Registration flow tests         │
│  ├── test_integration_*.py   # Integration tests               │
│  └── manual/                 # Manual testing scripts          │
│                                                                 │
│  Test Categories:                                               │
│  - Unit: Individual component testing                           │
│  - Integration: Multi-component interaction                     │
│  - End-to-end: Full system tournament                           │
│                                                                 │
│  Run: pytest tests/ -v --cov=src                                │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### 11.2 Maintainability

| Metric | Target | Measurement |
|--------|--------|-------------|
| Cyclomatic Complexity | < 10 | pylint |
| Code Duplication | < 5% | pylint |
| Documentation Coverage | > 50% | docstring audit |
| Type Annotation Coverage | > 80% | mypy |

### 11.3 Observability

```
Logging Architecture:
─────────────────────

┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Agent      │ ──► │   Logger     │ ──► │   Console    │
│   Code       │     │   (Python)   │     │   / File     │
└──────────────┘     └──────────────┘     └──────────────┘

Log Levels:
- DEBUG: Detailed debugging information
- INFO: General operational events
- WARNING: Unusual but handled situations
- ERROR: Errors that don't stop operation

Log Format:
[2026-01-17 10:30:45] [INFO] [player.Alpha] Registered with league manager
[2026-01-17 10:30:46] [DEBUG] [referee] Sending invitation to Alpha
```

---

## 12. Architectural Decision Records

### ADR-001: JSON-RPC 2.0 over REST

**Status:** Accepted

**Context:** Need a protocol for agent-to-agent communication.

**Decision:** Use JSON-RPC 2.0 for all inter-agent communication.

**Consequences:**
- (+) Standard, well-documented protocol
- (+) Language-agnostic
- (+) Clear error handling
- (-) Slightly more verbose than custom protocol

---

### ADR-002: In-Memory State

**Status:** Accepted

**Context:** Need to decide on state persistence strategy.

**Decision:** Use in-memory state with optional file persistence.

**Consequences:**
- (+) Simple deployment
- (+) Fast operation
- (-) State lost on restart
- (-) Not suitable for production use

---

### ADR-003: Strategy Pattern for AI

**Status:** Accepted

**Context:** Need flexible, pluggable AI decision-making.

**Decision:** Implement Strategy pattern with abstract base class.

**Consequences:**
- (+) Easy to add new strategies
- (+) Testable in isolation
- (+) Supports runtime plugin loading
- (-) Slight overhead from abstraction

---

### ADR-004: FastAPI Framework

**Status:** Accepted

**Context:** Need HTTP framework for all agents.

**Decision:** Use FastAPI with Uvicorn for all HTTP servers.

**Consequences:**
- (+) Modern, fast, async-capable
- (+) Automatic OpenAPI documentation
- (+) Type hints integration
- (-) Adds dependency

---

### ADR-005: Plugin Architecture for Extensibility

**Status:** Accepted

**Context:** Users need to add custom strategies without modifying core code.

**Decision:** Implement plugin discovery and loading system.

**Consequences:**
- (+) Extensible without core changes
- (+) Encourages experimentation
- (-) Increases complexity
- (-) Security considerations for loading external code

---

## Appendix A: File Structure

```
.
├── src/
│   ├── agents/
│   │   ├── league_manager/     # Central orchestrator
│   │   ├── referee/            # Match runner
│   │   └── player/             # Player agent
│   │       └── plugins/        # Strategy plugins
│   └── shared/                 # Shared utilities
│       ├── jsonrpc.py         # JSON-RPC implementation
│       ├── http.py            # HTTP client
│       ├── logging.py         # Logging configuration
│       └── repositories/       # Data persistence
├── tests/                      # Test suite
├── scripts/                    # Utility scripts
├── docs/                       # Documentation
└── SHARED/                     # Runtime data
```

---

## Appendix B: Technology Stack

| Layer | Technology | Version |
|-------|------------|---------|
| Language | Python | 3.10+ |
| Web Framework | FastAPI | 0.104+ |
| ASGI Server | Uvicorn | 0.24+ |
| HTTP Client | httpx | 0.25+ |
| Testing | pytest | 7.4+ |
| Linting | pylint, flake8 | Latest |
| Type Checking | mypy | Latest |
| Formatting | black | Latest |

---

**Document Approval:**

| Role | Name | Date |
|------|------|------|
| Architect | Development Team | January 2026 |
| Reviewer | - | Pending |
