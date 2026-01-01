"""Configuration management for MCP Agent.

Supports both CLI arguments and environment variable overrides.
"""
import argparse
import os
from dataclasses import dataclass


@dataclass
class Config:
    """Agent configuration."""
    
    port: int
    display_name: str
    league_url: str
    version: str = "1.0.0"
    log_level: str = "INFO"
    registration_path: str = "/register"
    strategy: str = "random"  # Parity choice strategy
    
    @property
    def endpoint(self) -> str:
        """Full MCP endpoint URL."""
        return f"http://127.0.0.1:{self.port}/mcp"
    
    @property
    def registration_url(self) -> str:
        """Full league registration URL."""
        return f"{self.league_url.rstrip('/')}{self.registration_path}"


def parse_args() -> Config:
    """Parse CLI arguments and environment variables.
    
    Environment variables override defaults but CLI args override everything.
    """
    parser = argparse.ArgumentParser(
        description="MCP Agent - League Competition Agent Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m agent --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000
  PORT=8002 python -m agent --display-name "Agent2" --league-url http://127.0.0.1:9000

Environment Variables:
  PORT              Server port (default: 8001)
  DISPLAY_NAME      Agent display name
  LEAGUE_URL        League manager URL
  LOG_LEVEL         Logging level (default: INFO)
  REGISTRATION_PATH Registration endpoint path (default: /register)
        """
    )
    
    # Required arguments
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.getenv("PORT", "8001")),
        help="Port to run the agent server on (env: PORT)"
    )
    parser.add_argument(
        "--display-name",
        type=str,
        default=os.getenv("DISPLAY_NAME", ""),
        help="Unique display name for this agent (env: DISPLAY_NAME)",
        required=not os.getenv("DISPLAY_NAME")
    )
    parser.add_argument(
        "--league-url",
        type=str,
        default=os.getenv("LEAGUE_URL", ""),
        help="League manager base URL (env: LEAGUE_URL)",
        required=not os.getenv("LEAGUE_URL")
    )
    
    # Optional arguments
    parser.add_argument(
        "--version",
        type=str,
        default=os.getenv("VERSION", "1.0.0"),
        help="Agent version (env: VERSION)"
    )
    parser.add_argument(
        "--log-level",
        type=str,
        default=os.getenv("LOG_LEVEL", "INFO"),
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (env: LOG_LEVEL)"
    )
    parser.add_argument(
        "--registration-path",
        type=str,
        default=os.getenv("REGISTRATION_PATH", "/register"),
        help="League registration endpoint path (env: REGISTRATION_PATH)"
    )
    parser.add_argument(
        "--strategy",
        type=str,
        default=os.getenv("STRATEGY", "random"),
        help="Parity choice strategy (env: STRATEGY). Available: random, always_even, always_odd, deterministic, alternating, adaptive, counter, biased_random_70, biased_random_30"
    )
    
    args = parser.parse_args()
    
    return Config(
        port=args.port,
        display_name=args.display_name,
        league_url=args.league_url,
        version=args.version,
        log_level=args.log_level,
        registration_path=args.registration_path,
        strategy=args.strategy
    )
