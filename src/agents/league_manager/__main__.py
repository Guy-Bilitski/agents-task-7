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


class AgentProcess:
    """Manages a single agent subprocess."""
    
    def __init__(self, port: int, name: str, league_url: str):
        self.port = port
        self.name = name
        self.league_url = league_url
        self.endpoint = f"http://127.0.0.1:{port}/mcp"
        self.health_url = f"http://127.0.0.1:{port}/health"
        self.process: Optional[subprocess.Popen] = None
    
    async def start(self, client: httpx.AsyncClient) -> bool:
        """Start the agent process."""
        try:
            # Find Python executable
            python_exe = sys.executable
            
            logger.info(f"Starting agent '{self.name}' on port {self.port}")
            
            self.process = subprocess.Popen(
                [
                    python_exe, "-m", "agents.player",
                    "--port", str(self.port),
                    "--display-name", self.name,
                    "--league-url", self.league_url,
                    "--log-level", "WARNING",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env={**os.environ, "PYTHONPATH": os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "src")}
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
            logger.info("     PARITY GAME LEAGUE - MULTI-AGENT COMPETITION")
            logger.info("█" * 60)
            logger.info("")
            
            # Create league manager
            manager = LeagueManager(port=config.port, rounds=config.rounds)
            league_url = f"http://127.0.0.1:{config.port}"
            
            # Start league manager in background
            logger.info("Starting League Manager...")
            server_task = asyncio.create_task(manager.start_server())
            
            # Wait for league manager to be ready (async)
            for _ in range(20):
                try:
                    resp = await client.get(f"{league_url}/health", timeout=0.5)
                    if resp.status_code == 200:
                        logger.info(f"  ✓ League Manager ready on port {config.port}")
                        break
                except Exception:
                    await asyncio.sleep(0.25)
            else:
                logger.error("  ✗ League Manager failed to start")
                return 1
            
            # Agent names
            agent_names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
            
            # Start agents
            logger.info("")
            logger.info("Starting Agents...")
            
            for i in range(config.num_agents):
                port = config.base_agent_port + i
                name = agent_names[i] if i < len(agent_names) else f"Agent{i+1}"
                
                agent = AgentProcess(port, name, league_url)
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
    
    # Log configuration
    logger.info("League Configuration:")
    logger.info(f"  Manager Port: {config.port}")
    logger.info(f"  Number of Agents: {config.num_agents}")
    logger.info(f"  Base Agent Port: {config.base_agent_port}")
    logger.info(f"  Rounds per Matchup: {config.rounds}")
    logger.info(f"  Log Level: {config.log_level}")
    
    # Run the league
    return asyncio.run(run_league(config))


if __name__ == "__main__":
    sys.exit(main())
