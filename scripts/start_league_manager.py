#!/usr/bin/env python3
"""
Run only the League Manager to wait for competitors.

This script starts the League Manager and waits for player agents to connect.
It does NOT spawn any agents automatically - competitors must connect manually.

Usage:
    python scripts/start_league_manager.py
    python scripts/start_league_manager.py --port 9000 --wait-for 4 --rounds 5
"""
import sys
import os
import asyncio
import signal
import logging

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from agents.league_manager.manager import LeagueManager
from agents.league_manager.config import LeagueConfig
import argparse

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="League Manager - Waits for competitors to connect",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Start and wait for 4 agents
  python scripts/start_league_manager.py --wait-for 4
  
  # Start and wait for any agents (manual start)
  python scripts/start_league_manager.py --wait-for 0
  
  # Custom port and rounds
  python scripts/start_league_manager.py --port 9001 --rounds 10 --wait-for 6

After starting, connect your agents:
  python scripts/start_player.py --port 8001 --display-name "Agent1" --league-url http://127.0.0.1:9000 --strategy random
  python scripts/start_player.py --port 8002 --display-name "Agent2" --league-url http://127.0.0.1:9000 --strategy adaptive
        """
    )
    
    parser.add_argument(
        '--port',
        type=int,
        default=9000,
        help='Port for League Manager (default: 9000)'
    )
    parser.add_argument(
        '--wait-for',
        type=int,
        default=4,
        help='Number of agents to wait for before starting league (0 = wait indefinitely, default: 4)'
    )
    parser.add_argument(
        '--rounds',
        type=int,
        default=3,
        help='Number of rounds per matchup (default: 3)'
    )
    parser.add_argument(
        '--timeout',
        type=int,
        default=300,
        help='Timeout in seconds to wait for agents (default: 300 = 5 minutes)'
    )
    parser.add_argument(
        '--auto-start',
        action='store_true',
        help='Automatically start league when enough agents connect (otherwise wait for Ctrl+C then "start")'
    )
    
    return parser.parse_args()


async def main():
    """Main entrypoint."""
    args = parse_args()
    
    # Banner
    print("=" * 70)
    print("  LEAGUE MANAGER - Waiting for Competitors")
    print("=" * 70)
    print(f"  Port: {args.port}")
    print(f"  Waiting for: {args.wait_for if args.wait_for > 0 else 'any number of'} agents")
    print(f"  Rounds: {args.rounds}")
    print(f"  Timeout: {args.timeout}s")
    print("=" * 70)
    print()
    
    # Create league manager
    manager = LeagueManager(port=args.port, rounds=args.rounds)
    
    # Start server in background
    logger.info("Starting League Manager server...")
    server_task = asyncio.create_task(manager.start_server())
    
    # Wait for server to be ready
    await asyncio.sleep(1)
    
    logger.info(f"✓ League Manager running on http://127.0.0.1:{args.port}")
    logger.info("")
    logger.info("Endpoints:")
    logger.info(f"  Registration: http://127.0.0.1:{args.port}/register")
    logger.info(f"  Health check: http://127.0.0.1:{args.port}/health")
    logger.info(f"  Agents list:  http://127.0.0.1:{args.port}/agents")
    logger.info(f"  Standings:    http://127.0.0.1:{args.port}/standings")
    logger.info("")
    logger.info("Connect your agents:")
    logger.info(f"  python scripts/start_player.py --port 8001 --display-name Agent1 --league-url http://127.0.0.1:{args.port} --strategy random")
    logger.info(f"  python scripts/start_player.py --port 8002 --display-name Agent2 --league-url http://127.0.0.1:{args.port} --strategy adaptive")
    logger.info("")
    
    # Wait for agents to connect
    if args.wait_for > 0:
        logger.info(f"Waiting for {args.wait_for} agents to connect (timeout: {args.timeout}s)...")
        waited = 0
        while len(manager.agents) < args.wait_for and waited < args.timeout:
            await asyncio.sleep(1)
            waited += 1
            
            # Show progress every 5 seconds
            if waited % 5 == 0 and len(manager.agents) < args.wait_for:
                logger.info(f"  {len(manager.agents)}/{args.wait_for} agents connected... (waited {waited}s)")
        
        if len(manager.agents) < args.wait_for:
            logger.warning(f"Timeout reached. Only {len(manager.agents)}/{args.wait_for} agents connected.")
        else:
            logger.info(f"✓ All {args.wait_for} agents connected!")
    else:
        logger.info("Waiting for agents to connect... (press Ctrl+C when ready)")
        try:
            # Wait forever or until interrupted
            while True:
                await asyncio.sleep(5)
                if len(manager.agents) > 0:
                    logger.info(f"  {len(manager.agents)} agent(s) connected: {list(manager.agents.keys())}")
        except KeyboardInterrupt:
            logger.info("\nStarting league with connected agents...")
    
    # Check if we have enough agents
    if len(manager.agents) < 2:
        logger.error(f"Need at least 2 agents to run league. Only {len(manager.agents)} connected.")
        logger.error("Shutting down...")
        await manager.stop_server()
        return 1
    
    logger.info("")
    logger.info(f"Connected agents ({len(manager.agents)}):")
    for name, agent in manager.agents.items():
        logger.info(f"  - {name} ({agent.version}) at {agent.endpoint}")
    
    # Run the league
    logger.info("")
    if args.auto_start or args.wait_for > 0:
        logger.info("Starting league competition...")
        await manager.run_league(wait_for_agents=0)  # Already waited above
    else:
        input("\nPress ENTER to start the league (or Ctrl+C to cancel)...")
        logger.info("Starting league competition...")
        await manager.run_league(wait_for_agents=0)
    
    # Keep server running to show final standings
    logger.info("")
    logger.info("League complete! Server still running for queries.")
    logger.info(f"View standings: http://127.0.0.1:{args.port}/standings")
    logger.info("Press Ctrl+C to shutdown")
    
    try:
        await server_task
    except (KeyboardInterrupt, asyncio.CancelledError):
        logger.info("\nShutting down...")
        await manager.stop_server()
    
    return 0


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nShutdown requested")
        sys.exit(0)
