"""Main entrypoint for MCP Agent.

Usage:
    python -m agent --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000
"""
import logging
import signal
import sys
import asyncio

import uvicorn

from agent import setup_logging
from agent.config import parse_args
from agent.app import create_app
from agent.state import init_state

logger = logging.getLogger(__name__)


def main() -> int:
    """Main entrypoint."""
    # Parse configuration
    config = parse_args()
    
    # Setup logging
    setup_logging(config.log_level)
    
    # Log startup configuration
    logger.info("=" * 60)
    logger.info("MCP Agent Starting")
    logger.info("=" * 60)
    logger.info(f"Display Name: {config.display_name}")
    logger.info(f"Version: {config.version}")
    logger.info(f"Port: {config.port}")
    logger.info(f"MCP Endpoint: {config.endpoint}")
    logger.info(f"League URL: {config.league_url}")
    logger.info(f"Registration URL: {config.registration_url}")
    logger.info(f"Log Level: {config.log_level}")
    logger.info("=" * 60)
    
    # Initialize agent state
    init_state(config.display_name)
    logger.info("Agent state initialized")
    
    # Setup graceful shutdown
    shutdown_requested = False
    
    def signal_handler(signum, frame):
        nonlocal shutdown_requested
        if not shutdown_requested:
            logger.info(f"Received signal {signum}, shutting down gracefully...")
            shutdown_requested = True
        else:
            logger.warning("Force shutdown requested")
            sys.exit(1)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Create FastAPI app with config for registration
    app = create_app(config)
    
    # Configure uvicorn
    uvicorn_config = uvicorn.Config(
        app=app,
        host="127.0.0.1",
        port=config.port,
        log_level=config.log_level.lower(),
        access_log=False,  # We'll log at application level
    )
    
    # Create server
    server = uvicorn.Server(uvicorn_config)
    
    logger.info(f"Starting HTTP server on http://127.0.0.1:{config.port}")
    logger.info(f"Health endpoint: http://127.0.0.1:{config.port}/health")
    logger.info(f"MCP endpoint: {config.endpoint}")
    logger.info("Press Ctrl+C to shutdown")
    
    # Run server
    try:
        server.run()
    except Exception as e:
        logger.error(f"Server error: {e}", exc_info=True)
        return 1
    
    logger.info("Shutdown complete")
    return 0


if __name__ == "__main__":
    sys.exit(main())
