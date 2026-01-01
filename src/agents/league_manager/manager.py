"""League Manager - Orchestrates the parity game competition.

The League Manager:
1. Accepts agent registrations
2. Schedules games between all registered agents
3. Tracks standings and statistics
4. Runs multiple rounds of competition
"""
import asyncio
import json
import logging
import signal
import sys
import uuid
from dataclasses import dataclass, field
from itertools import combinations
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn
import httpx

from agents.referee.referee import Agent, Referee, GameResult

logger = logging.getLogger(__name__)


@dataclass
class Standing:
    """Agent standings in the league."""
    
    wins: int = 0
    losses: int = 0
    draws: int = 0
    games_played: int = 0
    
    @property
    def points(self) -> int:
        """Calculate points (3 for win, 1 for draw, 0 for loss)."""
        return (self.wins * 3) + self.draws
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate."""
        if self.games_played == 0:
            return 0.0
        return self.wins / self.games_played


@dataclass
class LeagueStats:
    """Overall league statistics."""
    
    total_games: int = 0
    total_rounds_completed: int = 0
    standings: dict[str, Standing] = field(default_factory=dict)
    game_history: list[GameResult] = field(default_factory=list)


class LeagueManager:
    """Central league manager server."""
    
    def __init__(self, port: int, rounds: int = 3, use_external_referee: bool = False):
        """Initialize league manager.
        
        Args:
            port: Port to run the server on
            rounds: Number of rounds for each matchup
            use_external_referee: If True, use external referee via JSON-RPC; if False, use embedded referee
        """
        self.port = port
        self.rounds = rounds
        self.agents: dict[str, Agent] = {}
        self.stats = LeagueStats()
        self.use_external_referee = use_external_referee
        self.referee_endpoint: Optional[str] = None  # External referee endpoint
        self.referee = Referee(timeout=5.0) if not use_external_referee else None  # Embedded referee (legacy)
        self._running = False
        self._league_running = False
        self._server: Optional[uvicorn.Server] = None
        
        # Create FastAPI app
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(
            title="League Manager",
            description="Parity Game League Manager",
            version="1.0.0",
            docs_url=None,
            redoc_url=None
        )
        
        @app.get("/health")
        async def health():
            """Health check endpoint."""
            return {
                "ok": True,
                "registered_agents": len(self.agents),
                "total_games": self.stats.total_games
            }
        
        @app.post("/register")
        async def register(request: Request):
            """Handle agent registration (players and referee)."""
            try:
                data = await request.json()
                
                # Validate required fields
                required_fields = ["display_name", "version", "endpoint"]
                missing = [f for f in required_fields if f not in data]
                
                if missing:
                    return JSONResponse(
                        content={"error": f"Missing required fields: {missing}"},
                        status_code=400
                    )
                
                display_name = data["display_name"]
                version = data["version"]
                endpoint = data["endpoint"]
                agent_type = data.get("agent_type", "player")  # "player" or "referee"
                
                # Handle referee registration
                if agent_type == "referee":
                    self.referee_endpoint = endpoint
                    logger.info(f"✓ Registered referee: {display_name} (v{version}) at {endpoint}")
                    return {
                        "status": "registered",
                        "agent_type": "referee",
                        "message": f"Referee {display_name} registered successfully"
                    }
                
                # Handle player registration
                agent = Agent(
                    display_name=display_name,
                    version=version,
                    endpoint=endpoint
                )
                
                self.agents[display_name] = agent
                
                # Initialize standings if not exists
                if display_name not in self.stats.standings:
                    self.stats.standings[display_name] = Standing()
                
                logger.info(f"✓ Registered agent: {display_name} (v{version}) at {endpoint}")
                
                return {
                    "status": "registered",
                    "agent_id": f"agent_{display_name}",
                    "message": f"Welcome to the league, {display_name}!"
                }
                
            except json.JSONDecodeError:
                return JSONResponse(
                    content={"error": "Invalid JSON"},
                    status_code=400
                )
            except Exception as e:
                logger.error(f"Registration error: {e}")
                return JSONResponse(
                    content={"error": str(e)},
                    status_code=500
                )
        
        @app.get("/standings")
        async def standings():
            """Get current league standings."""
            sorted_standings = sorted(
                self.stats.standings.items(),
                key=lambda x: (x[1].points, x[1].wins, -x[1].losses),
                reverse=True
            )
            
            return {
                "standings": [
                    {
                        "rank": i + 1,
                        "agent": name,
                        "points": standing.points,
                        "wins": standing.wins,
                        "losses": standing.losses,
                        "draws": standing.draws,
                        "games_played": standing.games_played,
                        "win_rate": f"{standing.win_rate:.1%}"
                    }
                    for i, (name, standing) in enumerate(sorted_standings)
                ],
                "total_games": self.stats.total_games,
                "rounds_completed": self.stats.total_rounds_completed
            }
        
        @app.get("/agents")
        async def list_agents():
            """List registered agents."""
            return {
                "agents": [
                    {
                        "display_name": agent.display_name,
                        "version": agent.version,
                        "endpoint": agent.endpoint
                    }
                    for agent in self.agents.values()
                ]
            }
        
        @app.post("/start")
        async def start_league():
            """Start the league competition with currently registered agents."""
            if len(self.agents) < 2:
                return JSONResponse(
                    content={"error": "Need at least 2 agents to start league"},
                    status_code=400
                )
            
            if self._league_running:
                return JSONResponse(
                    content={"error": "League is already running"},
                    status_code=409
                )
            
            # Run league in background
            asyncio.create_task(self._run_league_background())
            
            return {
                "status": "started",
                "agents": len(self.agents),
                "rounds": self.rounds,
                "message": f"League starting with {len(self.agents)} agents"
            }
        
        return app
    
    async def run_league(self, wait_for_agents: int = 0, wait_timeout: float = 30.0) -> dict:
        """Run the full league competition.
        
        Args:
            wait_for_agents: Number of agents to wait for before starting (0 = start immediately)
            wait_timeout: Timeout in seconds to wait for agents
        
        Returns:
            Final standings
        """
        # Wait for agents if specified
        if wait_for_agents > 0:
            logger.info(f"Waiting for {wait_for_agents} agents to register (timeout: {wait_timeout}s)...")
            waited = 0
            while len(self.agents) < wait_for_agents and waited < wait_timeout:
                await asyncio.sleep(0.5)
                waited += 0.5
            
            if len(self.agents) < wait_for_agents:
                logger.warning(f"Only {len(self.agents)}/{wait_for_agents} agents registered")
        
        if len(self.agents) < 2:
            logger.error("Need at least 2 agents to run a league")
            return {"error": "Not enough agents"}
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("STARTING LEAGUE COMPETITION")
        logger.info("=" * 60)
        logger.info(f"Registered agents: {list(self.agents.keys())}")
        logger.info(f"Rounds per matchup: {self.rounds}")
        logger.info("")
        
        # Get all matchups (each pair plays)
        agent_list = list(self.agents.values())
        matchups = list(combinations(agent_list, 2))
        
        logger.info(f"Total matchups: {len(matchups)}")
        logger.info(f"Total games: {len(matchups) * self.rounds}")
        logger.info("")
        
        # Run all matchups
        for round_num in range(self.rounds):
            logger.info(f"\n{'='*60}")
            logger.info(f"ROUND {round_num + 1} of {self.rounds}")
            logger.info(f"{'='*60}")
            
            for player1, player2 in matchups:
                # Run game via referee (external or embedded)
                if self.use_external_referee:
                    result = await self._run_game_via_external_referee(player1, player2)
                elif self.referee is not None:
                    result = await self.referee.run_game(player1, player2)
                else:
                    raise RuntimeError("No referee available (neither external nor embedded)")
                
                self._record_result(result)
                self.stats.game_history.append(result)
                
                # Brief pause between games
                await asyncio.sleep(0.1)
            
            self.stats.total_rounds_completed = round_num + 1
            
            # Show standings after each round
            self._print_standings()
        
        logger.info("")
        logger.info("=" * 60)
        logger.info("LEAGUE COMPETITION COMPLETE")
        logger.info("=" * 60)
        self._print_final_standings()
        
        return self._get_final_standings()
    
    async def _run_league_background(self):
        """Run league in background (wrapper for API endpoint)."""
        try:
            self._league_running = True
            logger.info("League started via API endpoint")
            await self.run_league(wait_for_agents=0)
        except Exception as e:
            logger.error(f"Error running league: {e}", exc_info=True)
        finally:
            self._league_running = False
            logger.info("League completed")
    
    async def _run_game_via_external_referee(self, player1: Agent, player2: Agent) -> GameResult:
        """Run a game via external referee MCP server.
        
        Args:
            player1: First player agent
            player2: Second player agent
        
        Returns:
            GameResult from the referee
        
        Raises:
            RuntimeError: If referee is not registered or call fails
        """
        if not self.referee_endpoint:
            raise RuntimeError("No referee registered")
        
        match_id = f"match_{uuid.uuid4().hex[:8]}"
        
        # Prepare JSON-RPC request
        payload = {
            "jsonrpc": "2.0",
            "id": match_id,
            "method": "run_match",
            "params": {
                "match_id": match_id,
                "player1": {
                    "display_name": player1.display_name,
                    "version": player1.version,
                    "endpoint": player1.endpoint
                },
                "player2": {
                    "display_name": player2.display_name,
                    "version": player2.version,
                    "endpoint": player2.endpoint
                }
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.referee_endpoint,
                    json=payload,
                    timeout=60.0  # Long timeout for match execution
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    error = data["error"]
                    raise RuntimeError(f"Referee error: {error.get('message', 'Unknown error')}")
                
                result = data.get("result", {})
                
                # Convert result dict back to GameResult
                return GameResult(
                    game_id=result.get("game_id", "unknown"),
                    player1=result.get("player1", player1.display_name),
                    player2=result.get("player2", player2.display_name),
                    player1_choice=result.get("player1_choice", "none"),
                    player2_choice=result.get("player2_choice", "none"),
                    dice_roll=result.get("dice_roll", 0),
                    dice_parity=result.get("dice_parity", "none"),
                    winner=result.get("winner")
                )
                
        except Exception as e:
            logger.error(f"Error calling external referee: {e}")
            # Return a default result on error
            return GameResult(
                game_id=match_id,
                player1=player1.display_name,
                player2=player2.display_name,
                player1_choice="error",
                player2_choice="error",
                dice_roll=0,
                dice_parity="none",
                winner=None
            )
    
    def _record_result(self, result: GameResult):
        """Record a game result in standings."""
        self.stats.total_games += 1
        
        # Update player 1 stats
        if result.player1 in self.stats.standings:
            s1 = self.stats.standings[result.player1]
            s1.games_played += 1
            if result.winner == result.player1:
                s1.wins += 1
            elif result.winner == result.player2:
                s1.losses += 1
            else:
                s1.draws += 1
        
        # Update player 2 stats
        if result.player2 in self.stats.standings:
            s2 = self.stats.standings[result.player2]
            s2.games_played += 1
            if result.winner == result.player2:
                s2.wins += 1
            elif result.winner == result.player1:
                s2.losses += 1
            else:
                s2.draws += 1
    
    def _print_standings(self):
        """Print current standings to log."""
        sorted_standings = sorted(
            self.stats.standings.items(),
            key=lambda x: (x[1].points, x[1].wins),
            reverse=True
        )
        
        logger.info("")
        logger.info("Current Standings:")
        logger.info("-" * 50)
        logger.info(f"{'Rank':<5} {'Agent':<15} {'Pts':<5} {'W':<4} {'L':<4} {'D':<4}")
        logger.info("-" * 50)
        
        for i, (name, standing) in enumerate(sorted_standings):
            logger.info(
                f"{i+1:<5} {name:<15} {standing.points:<5} "
                f"{standing.wins:<4} {standing.losses:<4} {standing.draws:<4}"
            )
    
    def _print_final_standings(self):
        """Print final standings."""
        sorted_standings = sorted(
            self.stats.standings.items(),
            key=lambda x: (x[1].points, x[1].wins),
            reverse=True
        )
        
        logger.info("")
        logger.info("FINAL STANDINGS")
        logger.info("=" * 60)
        logger.info(f"{'Rank':<6} {'Agent':<15} {'Points':<8} {'W-L-D':<12} {'Win Rate':<10}")
        logger.info("-" * 60)
        
        for i, (name, standing) in enumerate(sorted_standings):
            wld = f"{standing.wins}-{standing.losses}-{standing.draws}"
            wr = f"{standing.win_rate:.1%}"
            logger.info(f"{i+1:<6} {name:<15} {standing.points:<8} {wld:<12} {wr:<10}")
        
        logger.info("=" * 60)
        
        if sorted_standings:
            winner = sorted_standings[0][0]
            logger.info(f"\n🏆 CHAMPION: {winner} 🏆")
    
    def _get_final_standings(self) -> dict:
        """Get final standings as dict."""
        sorted_standings = sorted(
            self.stats.standings.items(),
            key=lambda x: (x[1].points, x[1].wins),
            reverse=True
        )
        
        return {
            "standings": [
                {
                    "rank": i + 1,
                    "agent": name,
                    "points": standing.points,
                    "wins": standing.wins,
                    "losses": standing.losses,
                    "draws": standing.draws,
                    "games_played": standing.games_played,
                    "win_rate": standing.win_rate
                }
                for i, (name, standing) in enumerate(sorted_standings)
            ],
            "total_games": self.stats.total_games,
            "champion": sorted_standings[0][0] if sorted_standings else None
        }
    
    async def start_server(self):
        """Start the league manager server (blocks until shutdown)."""
        # Check if port is available first by attempting to connect
        import socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(0.1)
        try:
            # If we can connect, something is already running on this port
            result = sock.connect_ex(("127.0.0.1", self.port))
            if result == 0:
                sock.close()
                logger.error(f"Port {self.port} is already in use")
                raise RuntimeError(f"Port {self.port} is already in use. Try a different port with --port {self.port + 1}")
        except socket.timeout:
            # Timeout means nothing is listening - port is available
            pass
        finally:
            sock.close()
        
        # Suppress asyncio CancelledError logging during shutdown
        logging.getLogger("uvicorn.error").setLevel(logging.CRITICAL)
        
        config = uvicorn.Config(
            app=self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="critical",  # Suppress shutdown errors
            access_log=False
        )
        self._server = uvicorn.Server(config)
        self._running = True
        
        logger.info(f"League Manager starting on http://127.0.0.1:{self.port}")
        
        try:
            await self._server.serve()
        except (asyncio.CancelledError, KeyboardInterrupt):
            # Normal shutdown, suppress error
            pass
        except SystemExit:
            # Catch uvicorn's sys.exit() and convert to exception
            raise RuntimeError(f"Server failed to start on port {self.port}")
        finally:
            # Ensure we don't propagate the error
            self._running = False
    
    async def start_server_background(self):
        """Start the server in the background (returns immediately)."""
        config = uvicorn.Config(
            app=self.app,
            host="127.0.0.1",
            port=self.port,
            log_level="warning",
            access_log=False
        )
        self._server = uvicorn.Server(config)
        self._running = True
        
        logger.info(f"League Manager starting on http://127.0.0.1:{self.port}")
        
        # Start server in background task
        asyncio.create_task(self._server.serve())
        
        # Wait for server to be ready
        import httpx
        for _ in range(40):  # Up to 10 seconds
            try:
                async with httpx.AsyncClient() as client:
                    resp = await client.get(f"http://127.0.0.1:{self.port}/health", timeout=0.5)
                    if resp.status_code == 200:
                        logger.info(f"League Manager ready on http://127.0.0.1:{self.port}")
                        return True
            except Exception:
                await asyncio.sleep(0.25)
        
        logger.error("League Manager failed to start")
        return False
    
    async def stop_server(self):
        """Stop the league manager server."""
        if self._server:
            self._running = False
            self._server.should_exit = True
            logger.info("League Manager stopped")
