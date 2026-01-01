#!/usr/bin/env python3
"""
Run a complete Parity Game League with External Referee.

This script runs the entire system with all components:
1. Starts a League Manager
2. Starts an External Referee
3. Spawns multiple player agents
4. Runs a full league competition
5. Shows final standings

This is the COMPLETE system with external referee architecture.

Usage:
    python scripts/run_full_league.py                      # Run with defaults (4 agents, 3 rounds)
    python scripts/run_full_league.py --num-agents 6       # Run with 6 agents
    python scripts/run_full_league.py --rounds 5           # Run 5 rounds per matchup
    python scripts/run_full_league.py --log-level DEBUG    # Verbose logging
"""
import asyncio
import logging
import os
import subprocess
import sys
import argparse
import signal
from typing import List, Optional

import httpx

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

logger = logging.getLogger(__name__)


class ProcessManager:
    """Manages external processes (referee and players)."""
    
    def __init__(self):
        self.processes: List[subprocess.Popen] = []
    
    def start_process(self, cmd: List[str], name: str, env: Optional[dict] = None, capture_output: bool = True) -> subprocess.Popen:
        """Start a subprocess and track it."""
        logger.info(f"Starting {name}...")
        process_env = env if env is not None else os.environ.copy()
        
        if capture_output:
            proc = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=process_env
            )
        else:
            proc = subprocess.Popen(
                cmd,
                env=process_env
            )
        self.processes.append(proc)
        return proc
    
    def stop_all(self):
        """Stop all managed processes."""
        logger.info("Stopping all processes...")
        for proc in self.processes:
            try:
                proc.terminate()
                proc.wait(timeout=3)
            except subprocess.TimeoutExpired:
                proc.kill()
                logger.warning("Force killed a process")
        self.processes.clear()


async def wait_for_health(url: str, timeout: float = 10.0, name: str = "service") -> bool:
    """Wait for a service to be healthy."""
    logger.info(f"Waiting for {name} to be ready...")
    
    start = asyncio.get_event_loop().time()
    async with httpx.AsyncClient() as client:
        while (asyncio.get_event_loop().time() - start) < timeout:
            try:
                resp = await client.get(url, timeout=0.5)
                if resp.status_code == 200:
                    logger.info(f"  ✓ {name} is ready")
                    return True
            except Exception:
                await asyncio.sleep(0.25)
    
    logger.error(f"  ✗ {name} failed to start (timeout)")
    return False


async def run_full_league(
    port: int = 9000,
    referee_port: int = 8001,
    num_agents: int = 4,
    base_agent_port: int = 8101,
    rounds: int = 3,
    log_level: str = "INFO"
) -> int:
    """Run the complete league with external referee.
    
    Args:
        port: League Manager port
        referee_port: Referee port
        num_agents: Number of player agents to spawn
        base_agent_port: First player agent port
        rounds: Number of rounds per matchup
        log_level: Logging level
    
    Returns:
        Exit code (0 for success)
    """
    proc_manager = ProcessManager()
    
    try:
        # Setup paths
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        src_path = os.path.join(project_root, "src")
        python_exe = sys.executable
        
        env = os.environ.copy()
        env["PYTHONPATH"] = src_path
        
        league_url = f"http://127.0.0.1:{port}"
        
        # Print banner
        logger.info("")
        logger.info("=" * 70)
        logger.info("  PARITY GAME LEAGUE - COMPLETE SYSTEM WITH EXTERNAL REFEREE")
        logger.info("=" * 70)
        logger.info("")
        logger.info(f"Configuration:")
        logger.info(f"  League Manager: http://127.0.0.1:{port}")
        logger.info(f"  Referee:        http://127.0.0.1:{referee_port}")
        logger.info(f"  Players:        {num_agents} agents on ports {base_agent_port}-{base_agent_port + num_agents - 1}")
        logger.info(f"  Rounds:         {rounds}")
        logger.info("")
        
        # Step 1: Start League Manager
        logger.info("Step 1: Starting League Manager...")
        lm_proc = proc_manager.start_process(
            [
                python_exe, "-m", "agents.league_manager",
                "--port", str(port),
                "--server-only",
                "--use-external-referee",
                "--rounds", str(rounds),
                "--log-level", "WARNING"
            ],
            "League Manager",
            env
        )
        
        if not await wait_for_health(f"{league_url}/health", name="League Manager"):
            return 1
        
        # Step 2: Start External Referee
        logger.info("")
        logger.info("Step 2: Starting External Referee...")
        ref_proc = proc_manager.start_process(
            [
                python_exe, "-m", "agents.referee",
                "--port", str(referee_port),
                "--league-manager", league_url,
                "--log-level", "INFO"
            ],
            "Referee",
            env,
            capture_output=False  # Show referee output with game decisions
        )
        
        if not await wait_for_health(f"http://127.0.0.1:{referee_port}/health", name="Referee"):
            return 1
        
        # Give referee time to register
        await asyncio.sleep(0.5)
        
        # Step 3: Start Player Agents
        logger.info("")
        logger.info(f"Step 3: Starting {num_agents} Player Agents...")
        
        agent_names = ["Alpha", "Beta", "Gamma", "Delta", "Epsilon", "Zeta", "Eta", "Theta"]
        strategies = ["random", "always_even", "always_odd", "alternating", "adaptive", "counter", "biased_random_70", "deterministic"]
        
        logger.info("")
        logger.info("Agent Strategies:")
        for i in range(num_agents):
            agent_name = agent_names[i] if i < len(agent_names) else f"Agent{i+1}"
            strategy = strategies[i % len(strategies)]
            logger.info(f"  • {agent_name}: {strategy}")
        logger.info("")
        
        for i in range(num_agents):
            agent_port = base_agent_port + i
            agent_name = agent_names[i] if i < len(agent_names) else f"Agent{i+1}"
            strategy = strategies[i % len(strategies)]
            
            proc_manager.start_process(
                [
                    python_exe, "-m", "agents.player",
                    "--port", str(agent_port),
                    "--display-name", agent_name,
                    "--league-url", league_url,
                    "--strategy", strategy,
                    "--log-level", "WARNING"
                ],
                f"Player {agent_name}",
                env
            )
            
            # Wait for player to be healthy
            if not await wait_for_health(f"http://127.0.0.1:{agent_port}/health", timeout=5, name=f"Player {agent_name}"):
                logger.error(f"Failed to start player {agent_name}")
                return 1
        
        # Step 4: Wait for all agents to register
        logger.info("")
        logger.info("Step 4: Waiting for all agents to register...")
        
        async with httpx.AsyncClient() as client:
            for _ in range(30):  # 15 seconds timeout
                try:
                    resp = await client.get(f"{league_url}/agents", timeout=1.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        registered = len(data.get("agents", []))
                        if registered >= num_agents:
                            logger.info(f"  ✓ All {num_agents} players registered")
                            break
                        else:
                            logger.debug(f"  {registered}/{num_agents} agents registered...")
                except Exception as e:
                    logger.debug(f"Waiting for registration: {e}")
                await asyncio.sleep(0.5)
            else:
                logger.warning(f"Not all agents registered in time, proceeding anyway")
            
            # Step 5: Start the tournament
            logger.info("")
            logger.info("=" * 70)
            logger.info("Step 5: Starting Tournament!")
            logger.info("=" * 70)
            logger.info("")
            
            try:
                resp = await client.post(f"{league_url}/start", timeout=5.0)
                if resp.status_code == 200:
                    result = resp.json()
                    logger.info(f"✓ Tournament started: {result.get('message')}")
                else:
                    logger.error(f"Failed to start tournament: {resp.text}")
                    return 1
            except Exception as e:
                logger.error(f"Error starting tournament: {e}")
                return 1
            
            # Step 6: Wait for tournament to complete
            logger.info("")
            logger.info("Tournament in progress...")
            logger.info("(Watch the League Manager output for match details)")
            logger.info("")
            
            # Poll for completion (check if total_games increases)
            expected_games = (num_agents * (num_agents - 1) // 2) * rounds
            logger.info(f"Expected total games: {expected_games}")
            
            last_games = 0
            for _ in range(300):  # 5 minutes max
                try:
                    resp = await client.get(f"{league_url}/standings", timeout=1.0)
                    if resp.status_code == 200:
                        data = resp.json()
                        total_games = data.get("total_games", 0)
                        rounds_completed = data.get("rounds_completed", 0)
                        
                        if total_games != last_games:
                            logger.info(f"  Progress: {total_games}/{expected_games} games, {rounds_completed}/{rounds} rounds")
                            last_games = total_games
                        
                        if total_games >= expected_games:
                            logger.info(f"  ✓ Tournament complete!")
                            break
                except Exception:
                    pass
                
                await asyncio.sleep(1.0)
            
            # Step 7: Display final standings
            logger.info("")
            logger.info("=" * 70)
            logger.info("FINAL STANDINGS")
            logger.info("=" * 70)
            
            try:
                resp = await client.get(f"{league_url}/standings", timeout=5.0)
                if resp.status_code == 200:
                    data = resp.json()
                    standings = data.get("standings", [])
                    
                    logger.info("")
                    logger.info(f"{'Rank':<6} {'Agent':<15} {'Points':<8} {'W-L-D':<12} {'Win Rate':<10}")
                    logger.info("-" * 70)
                    
                    for standing in standings:
                        rank = standing["rank"]
                        agent = standing["agent"]
                        points = standing["points"]
                        wins = standing["wins"]
                        losses = standing["losses"]
                        draws = standing["draws"]
                        win_rate = standing["win_rate"]
                        
                        wld = f"{wins}-{losses}-{draws}"
                        logger.info(f"{rank:<6} {agent:<15} {points:<8} {wld:<12} {win_rate:<10}")
                    
                    logger.info("=" * 70)
                    
                    if standings:
                        champion = standings[0]["agent"]
                        logger.info(f"\n🏆 CHAMPION: {champion} 🏆\n")
                    
                    logger.info(f"Total games played: {data.get('total_games')}")
                    logger.info(f"Rounds completed: {data.get('rounds_completed')}")
            except Exception as e:
                logger.error(f"Error fetching final standings: {e}")
        
        logger.info("")
        logger.info("Tournament complete!")
        return 0
        
    except KeyboardInterrupt:
        logger.info("\n\nInterrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"Error running league: {e}", exc_info=True)
        return 1
        
    finally:
        # Cleanup
        proc_manager.stop_all()
        logger.info("✓ All processes stopped")


def main():
    """Main entrypoint."""
    parser = argparse.ArgumentParser(
        description="Run complete Parity Game League with external referee",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/run_full_league.py
  python scripts/run_full_league.py --num-agents 6 --rounds 5
  python scripts/run_full_league.py --port 9000 --referee-port 8001
  python scripts/run_full_league.py --log-level DEBUG
        """
    )
    
    parser.add_argument("--port", type=int, default=9000, help="League Manager port")
    parser.add_argument("--referee-port", type=int, default=8001, help="Referee port")
    parser.add_argument("--num-agents", type=int, default=4, help="Number of player agents")
    parser.add_argument("--base-agent-port", type=int, default=8101, help="First player port")
    parser.add_argument("--rounds", type=int, default=3, help="Rounds per matchup")
    parser.add_argument("--log-level", type=str, default="INFO", 
                       choices=["DEBUG", "INFO", "WARNING", "ERROR"],
                       help="Logging level")
    
    args = parser.parse_args()
    
    # Setup logging
    logging.basicConfig(
        level=getattr(logging, args.log_level),
        format='%(asctime)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    
    # Run the league
    exit_code = asyncio.run(run_full_league(
        port=args.port,
        referee_port=args.referee_port,
        num_agents=args.num_agents,
        base_agent_port=args.base_agent_port,
        rounds=args.rounds,
        log_level=args.log_level
    ))
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
