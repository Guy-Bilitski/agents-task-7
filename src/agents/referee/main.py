"""Referee main entry point.

Usage:
    python -m agents.referee --port 8001 --league-manager http://127.0.0.1:8000
"""
import argparse
import asyncio
import logging
import sys

from agents.referee.app import RefereeServer
from agents.referee.client import RefereeRegistrationClient

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


async def main():
    """Main entry point for referee."""
    parser = argparse.ArgumentParser(description="Even-Odd Referee Server")
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        help="Host to bind to (default: 127.0.0.1)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8001,
        help="Port to bind to (default: 8001)"
    )
    parser.add_argument(
        "--league-manager",
        default="http://127.0.0.1:8000",
        help="League Manager URL (default: http://127.0.0.1:8000)"
    )
    parser.add_argument(
        "--no-register",
        action="store_true",
        help="Don't register with League Manager (for testing)"
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging level (default: INFO)"
    )
    
    args = parser.parse_args()
    
    # Update logging level
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # Create referee server
    server = RefereeServer(host=args.host, port=args.port)
    
    # Create registration client (if enabled)
    registration_client = None
    if not args.no_register:
        referee_endpoint = f"http://{args.host}:{args.port}/mcp"
        registration_client = RefereeRegistrationClient(
            referee_endpoint=referee_endpoint,
            league_manager_url=args.league_manager,
            display_name="Referee",
            version="1.0.0"
        )
        
        # Start background registration (non-blocking)
        registration_client.start_background_registration()
    
    try:
        # Start server (blocks until shutdown)
        await server.start()
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        if registration_client:
            registration_client.stop()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted")
        sys.exit(0)
