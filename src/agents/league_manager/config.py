"""Configuration for League Manager.

Supports both CLI arguments and environment variable overrides.
"""
import argparse
import os
from dataclasses import dataclass


@dataclass
class LeagueConfig:
    """League Manager configuration."""
    
    port: int
    num_agents: int
    base_agent_port: int
    rounds: int
    log_level: str = "INFO"
    registration_path: str = "/register"
    server_only: bool = False  # If True, don't spawn agents or auto-start league
    use_external_referee: bool = False  # If True, use external referee via JSON-RPC
    
    @property
    def registration_endpoint(self) -> str:
        """Full registration endpoint path."""
        return f"http://127.0.0.1:{self.port}{self.registration_path}"


def parse_league_args() -> LeagueConfig:
    """Parse CLI arguments for league manager."""
    parser = argparse.ArgumentParser(
        description="League Manager - Orchestrates parity game competitions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m league --port 9000 --num-agents 4 --rounds 10
  python -m league --port 9000 --num-agents 4 --base-agent-port 8001 --rounds 5

Environment Variables:
  LEAGUE_PORT       Manager port (default: 9000)
  NUM_AGENTS        Number of agents to run (default: 4)
  BASE_AGENT_PORT   First agent port (default: 8001)
  ROUNDS            Number of rounds per matchup (default: 3)
  LOG_LEVEL         Logging level (default: INFO)
        """
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("LEAGUE_PORT", "9000")),
        help="Port for league manager server"
    )
    parser.add_argument(
        "--num-agents",
        type=int,
        default=int(os.getenv("NUM_AGENTS", "4")),
        help="Number of agents to spawn"
    )
    parser.add_argument(
        "--base-agent-port",
        type=int,
        default=int(os.getenv("BASE_AGENT_PORT", "8001")),
        help="Base port for agents (will use consecutive ports)"
    )
    parser.add_argument(
        "--rounds",
        type=int,
        default=int(os.getenv("ROUNDS", "3")),
        help="Number of rounds per matchup"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level"
    )
    parser.add_argument(
        "--server-only",
        action="store_true",
        help="Run as server only (don't spawn agents or auto-start league)"
    )
    parser.add_argument(
        "--use-external-referee",
        action="store_true",
        help="Use external referee server instead of embedded referee"
    )
    
    args = parser.parse_args()
    
    return LeagueConfig(
        port=args.port,
        num_agents=args.num_agents,
        base_agent_port=args.base_agent_port,
        rounds=args.rounds,
        log_level=args.log_level,
        server_only=args.server_only,
        use_external_referee=args.use_external_referee
    )
