"""Main entrypoint for running the complete league.

Usage:
    python -m league                      # Run with 4 agents, 3 rounds
    python -m league --num-agents 6       # Run with 6 agents
    python -m league --rounds 5           # Run 5 rounds per matchup
    python -m league --log-level DEBUG    # Verbose logging
"""
import asyncio
import logging
import os
import subprocess
import sys
from typing import List, Optional

import httpx

from agents.league_manager import setup_logging
from agents.league_manager.config import parse_league_args, LeagueConfig
from agents.league_manager.manager import LeagueManager

logger = logging.getLogger(__name__)


# Filter to suppress CancelledError during shutdown
class SuppressCancelledErrorFilter(logging.Filter):
    def filter(self, record):
        if record.exc_info:
            exc_type = record.exc_info[0]
            if exc_type is asyncio.CancelledError:
                return False
        return True


class AgentProcess:
    """Manages a single agent subprocess."""
    
    def __init__(self, port: int, name: str, league_url: str, strategy: str = "random"):
        self.port = port
        self.name = name
        self.league_url = league_url
        self.strategy = strategy
        self.endpoint = f"http://127.0.0.1:{port}/mcp"
        self.health_url = f"http://127.0.0.1:{port}/health"
        self.process: Optional[subprocess.Popen] = None
    
    async def start(self, client: httpx.AsyncClient) -> bool:
        """Start the agent process."""
        try:
            # Find Python executable
            python_exe = sys.executable
            
            # Calculate src directory (go up from agents/league_manager/__main__.py to project root, then add src)
            current_file = os.path.abspath(__file__)
            project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
            src_path = os.path.join(project_root, "src")
            
            logger.info(f"Starting agent '{self.name}' on port {self.port} with strategy '{self.strategy}'")
            
            env = os.environ.copy()
            env["PYTHONPATH"] = src_path
            
            self.process = subprocess.Popen(
                [
                    python_exe, "-m", "agents.player",
                    "--port", str(self.port),
                    "--display-name", self.name,
                    "--league-url", self.league_url,
                    "--strategy", self.strategy,
                    "--log-level", "WARNING",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=env
            )
            
            # Wait for health check (async)
            for _ in range(30):  # 15 seconds timeout
                try:
                    resp = await client.get(self.health_url, timeout=0.5)
                    if resp.status_code == 200:
                        logger.info(f"  ✓ Agent '{self.name}' ready on port {self.port}")
                        return True
                except Exception:
                    await asyncio.sleep(0.5)
            
            # Agent failed - try to get error output
            if self.process.poll() is not None:
                # Process has terminated
                stderr = self.process.stderr.read().decode() if self.process.stderr else ""
                stdout = self.process.stdout.read().decode() if self.process.stdout else ""
                if stderr:
                    logger.error(f"  ✗ Agent stderr: {stderr[:200]}")
                if stdout:
                    logger.debug(f"  Agent stdout: {stdout[:200]}")
            
            logger.error(f"  ✗ Agent '{self.name}' failed to start")
            return False
            
        except Exception as e:
            logger.error(f"  ✗ Error starting agent '{self.name}': {e}")
            return False
    
    def stop(self):
        """Stop the agent process."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
                logger.debug(f"Agent '{self.name}' stopped")
            except subprocess.TimeoutExpired:
                self.process.kill()
                logger.warning(f"Agent '{self.name}' force killed")


async def run_league(config: LeagueConfig) -> int:
    """Run the complete league competition.
    
    Args:
        config: League configuration
    
    Returns:
        Exit code (0 for success)
    """
    agents: List[AgentProcess] = []
    manager: Optional[LeagueManager] = None
    
    async with httpx.AsyncClient() as client:
        try:
            # Print banner
            logger.info("")
            logger.info("█" * 60)
            if config.server_only:
                logger.info("     LEAGUE MANAGER - SERVER ONLY MODE")
            else:
                logger.info("     PARITY GAME LEAGUE - MULTI-AGENT COMPETITION")
            logger.info("█" * 60)
            logger.info("")
            
            # Create league manager
            manager = LeagueManager(
                port=config.port,
                rounds=config.rounds,
                use_external_referee=config.use_external_referee
            )
            league_url = f"http://127.0.0.1:{config.port}"
            
            # Start league manager in background
            logger.info("Starting League Manager...")
            server_task = asyncio.create_task(manager.start_server())
            
            # Give server a moment to detect port conflicts
            await asyncio.sleep(0.1)
            
            # Check if server task has failed immediately (e.g., port conflict)
            if server_task.done():
                try:
                    server_task.result()
                except Exception as e:
                    error_msg = str(e)
                    logger.error(f"  ✗ {error_msg}")
                    return 1
            
            # Wait for league manager to be ready (async)
            server_ready = False
            for i in range(20):
                # Check if server task has failed during startup
                if server_task.done():
                    try:
                        server_task.result()
                    except Exception as e:
                        logger.error(f"  ✗ League Manager failed to start: {e}")
                        return 1
                
                try:
                    resp = await client.get(f"{league_url}/health", timeout=0.5)
                    if resp.status_code == 200:
                        logger.info(f"  ✓ League Manager ready on port {config.port}")
                        server_ready = True
                        break
                except Exception:
                    await asyncio.sleep(0.25)
            
            if not server_ready:
                logger.error("  ✗ League Manager failed to start (timeout)")
                return 1
            
            # If server-only mode, just run the server and wait
            if config.server_only:
                logger.info("")
                logger.info("=" * 60)
                logger.info("SERVER RUNNING IN SERVER-ONLY MODE")
                logger.info("=" * 60)
                logger.info("")
                logger.info("Endpoints:")
                logger.info(f"  Health:   http://127.0.0.1:{config.port}/health")
                logger.info(f"  Register: http://127.0.0.1:{config.port}/register")
                logger.info(f"  Agents:   http://127.0.0.1:{config.port}/agents")
                logger.info(f"  Standings: http://127.0.0.1:{config.port}/standings")
                logger.info("")
                logger.info("The server will accept registrations from:")
                if config.use_external_referee:
                    logger.info("  - Referee (external)")
                else:
                    logger.info("  - Referee (embedded)")
                logger.info("  - Player agents")
                logger.info("")
                logger.info("Press Ctrl+C to stop")
                logger.info("")
                
                # Wait forever (until Ctrl+C)
                await server_task
                return 0
            
            # Agent names and strategies
            agent_names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
            # Rotate through different strategies to make games interesting
            strategies = ["random", "always_even", "always_odd", "alternating", "adaptive", "deterministic", "biased_random_70", "counter"]
            
            # Start agents
            logger.info("")
            logger.info("Starting Agents...")
            
            for i in range(config.num_agents):
                port = config.base_agent_port + i
                name = agent_names[i] if i < len(agent_names) else f"Agent{i+1}"
                strategy = strategies[i % len(strategies)]  # Rotate through strategies
                
                agent = AgentProcess(port, name, league_url, strategy)
                if await agent.start(client):
                    agents.append(agent)
                else:
                    logger.error(f"Failed to start agent {name}")
                    return 1
            
            logger.info(f"\n✓ All {len(agents)} agents started successfully")
            
            # Wait for agents to register
            logger.info("")
            logger.info("Waiting for agents to register with League Manager...")
            
            for _ in range(30):  # 15 seconds timeout
                try:
                    resp = await client.get(f"{league_url}/agents", timeout=1.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        if len(data.get("agents", [])) >= config.num_agents:
                            logger.info(f"  ✓ All {config.num_agents} agents registered")
                            break
                except Exception:
                    pass
                await asyncio.sleep(0.5)
            else:
                logger.warning(f"Only {len(manager.agents)} agents registered, proceeding anyway")
            
            # Run the league
            await manager.run_league()
            
            # Show final standings via API
            logger.info("")
            logger.info("Fetching final standings from API...")
            try:
                resp = await client.get(f"{league_url}/standings", timeout=5.0)
                if resp.status_code == 200:
                    standings = resp.json()
                    logger.info(f"\nAPI Response: {standings}")
            except Exception as e:
                logger.warning(f"Could not fetch standings: {e}")
            
            return 0
            
        except KeyboardInterrupt:
            logger.info("\n\nLeague interrupted by user")
            return 130
            
        except Exception as e:
            logger.error(f"\nLeague error: {e}", exc_info=True)
            return 1
            
        finally:
            # Cleanup
            logger.info("")
            logger.info("Shutting down...")
            
            # Stop agents
            for agent in agents:
                agent.stop()
            
            # Stop manager
            if manager:
                await manager.stop_server()
            
            logger.info("✓ Cleanup complete")


def main() -> int:
    """Main entrypoint."""
    # Parse configuration
    config = parse_league_args()
    
    # Setup logging
    setup_logging(config.log_level)
    
    # Add filter to suppress CancelledError on shutdown
    error_filter = SuppressCancelledErrorFilter()
    logging.getLogger("uvicorn.error").addFilter(error_filter)
    logging.getLogger("uvicorn").addFilter(error_filter)
    
    # Log configuration
    logger.info("League Configuration:")
    logger.info(f"  Manager Port: {config.port}")
    logger.info(f"  Mode: {'Server-Only' if config.server_only else 'Full League'}")
    logger.info(f"  Referee: {'External' if config.use_external_referee else 'Embedded'}")
    if not config.server_only:
        logger.info(f"  Number of Agents: {config.num_agents}")
        logger.info(f"  Base Agent Port: {config.base_agent_port}")
    logger.info(f"  Rounds per Matchup: {config.rounds}")
    logger.info(f"  Log Level: {config.log_level}")
    
    # Run the league
    return asyncio.run(run_league(config))


if __name__ == "__main__":
    sys.exit(main())
