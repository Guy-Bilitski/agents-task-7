"""Self-test harness for MCP Agent.

Launches a League Manager and 4 agents, runs a mini league to validate all functionality.

Usage:
    python -m agent.selftest
"""
import asyncio
import os
import subprocess
import sys
import time
import logging
from typing import List, Optional

import httpx

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)

# Configuration
LEAGUE_PORT = 9000
BASE_AGENT_PORT = 8001
NUM_AGENTS = 4
AGENT_NAMES = ["Alpha", "Beta", "Gamma", "Delta"]


class AgentProcess:
    """Manages a single agent subprocess."""
    
    def __init__(self, port: int, name: str, league_url: str):
        self.port = port
        self.name = name
        self.league_url = league_url
        self.endpoint = f"http://127.0.0.1:{port}/mcp"
        self.health_url = f"http://127.0.0.1:{port}/health"
        self.process: Optional[subprocess.Popen] = None
    
    def start(self) -> bool:
        """Start the agent process."""
        try:
            python_exe = sys.executable
            
            logger.info(f"  Starting agent '{self.name}' on port {self.port}...")
            
            self.process = subprocess.Popen(
                [
                    python_exe, "-m", "agent",
                    "--port", str(self.port),
                    "--display-name", self.name,
                    "--league-url", self.league_url,
                    "--log-level", "WARNING",
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            )
            
            # Wait for health check
            for _ in range(30):
                try:
                    resp = httpx.get(self.health_url, timeout=0.5)
                    if resp.status_code == 200:
                        logger.info(f"  ✓ Agent '{self.name}' ready")
                        return True
                except Exception:
                    time.sleep(0.5)
            
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
            except subprocess.TimeoutExpired:
                self.process.kill()
    
    def call(self, method: str, params: dict, request_id: int = 1) -> dict:
        """Make JSON-RPC call to agent."""
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        resp = httpx.post(self.endpoint, json=payload, timeout=5)
        resp.raise_for_status()
        
        data = resp.json()
        if "error" in data:
            raise Exception(f"JSON-RPC error: {data['error']}")
        
        return data


class LeagueManagerProcess:
    """Manages the league manager subprocess."""
    
    def __init__(self, port: int, num_agents: int, rounds: int = 2):
        self.port = port
        self.num_agents = num_agents
        self.rounds = rounds
        self.health_url = f"http://127.0.0.1:{port}/health"
        self.process: Optional[subprocess.Popen] = None
    
    def start(self) -> bool:
        """Start the league manager subprocess that only runs the server (not the full league)."""
        # For the selftest, we'll directly use the LeagueManager class instead
        # This is simpler and gives us more control
        return True
    
    def stop(self):
        """Stop the league manager."""
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                self.process.kill()


async def run_selftest():
    """Run the self-test suite."""
    from league.manager import LeagueManager
    
    agents: List[AgentProcess] = []
    manager: Optional[LeagueManager] = None
    
    test_results = {
        "passed": 0,
        "failed": 0,
        "tests": []
    }
    
    def record_test(name: str, passed: bool, details: str = ""):
        test_results["tests"].append({
            "name": name,
            "passed": passed,
            "details": details
        })
        if passed:
            test_results["passed"] += 1
            logger.info(f"  ✓ {name}")
        else:
            test_results["failed"] += 1
            logger.error(f"  ✗ {name}: {details}")
    
    try:
        # Print banner
        logger.info("")
        logger.info("█" * 60)
        logger.info("     MCP AGENT SELF-TEST HARNESS")
        logger.info("█" * 60)
        logger.info("")
        logger.info("This will:")
        logger.info("  1. Start a League Manager")
        logger.info("  2. Start 4 agent processes")
        logger.info("  3. Run individual JSON-RPC tests")
        logger.info("  4. Run a complete mini-league")
        logger.info("  5. Validate all results")
        logger.info("")
        
        # ===== Phase 1: Start League Manager =====
        logger.info("=" * 60)
        logger.info("PHASE 1: Starting League Manager")
        logger.info("=" * 60)
        
        manager = LeagueManager(port=LEAGUE_PORT, rounds=2)
        
        # Start server in background
        manager_ready = await manager.start_server_background()
        league_url = f"http://127.0.0.1:{LEAGUE_PORT}"
        
        record_test("League Manager starts", manager_ready)
        if not manager_ready:
            raise RuntimeError("League Manager failed to start")
        
        # ===== Phase 2: Start Agents =====
        logger.info("")
        logger.info("=" * 60)
        logger.info("PHASE 2: Starting Agents")
        logger.info("=" * 60)
        
        for i in range(NUM_AGENTS):
            port = BASE_AGENT_PORT + i
            name = AGENT_NAMES[i]
            
            agent = AgentProcess(port, name, league_url)
            if agent.start():
                agents.append(agent)
                record_test(f"Agent {name} starts", True)
            else:
                record_test(f"Agent {name} starts", False, "Failed to start")
                raise RuntimeError(f"Agent {name} failed to start")
        
        # ===== Phase 3: Test Registration =====
        logger.info("")
        logger.info("=" * 60)
        logger.info("PHASE 3: Testing Agent Registration")
        logger.info("=" * 60)
        
        # Wait for registration with polling (using async httpx)
        all_registered = False
        registered_agents = []
        
        async with httpx.AsyncClient() as client:
            for _ in range(20):  # 10 seconds max
                try:
                    resp = await client.get(f"{league_url}/agents", timeout=2)
                    registered_agents = resp.json().get("agents", [])
                    if len(registered_agents) == NUM_AGENTS:
                        all_registered = True
                        break
                except Exception:
                    pass
                await asyncio.sleep(0.5)
        
        record_test(
            "All agents register with League Manager",
            all_registered,
            f"{len(registered_agents)}/{NUM_AGENTS} registered" if not all_registered else ""
        )
        
        # ===== Phase 4: Test JSON-RPC Methods =====
        logger.info("")
        logger.info("=" * 60)
        logger.info("PHASE 4: Testing JSON-RPC Methods")
        logger.info("=" * 60)
        
        for agent in agents:
            # Test handle_game_invitation
            try:
                resp = agent.call(
                    "handle_game_invitation",
                    {
                        "game_id": f"test_{agent.name}",
                        "invitation_id": "test_inv",
                        "from_player": "SelfTest"
                    }
                )
                result = resp.get("result", {})
                passed = (
                    result.get("type") == "GAME_JOIN_ACK" and
                    result.get("accepted") is True
                )
                record_test(f"{agent.name}: handle_game_invitation", passed)
            except Exception as e:
                record_test(f"{agent.name}: handle_game_invitation", False, str(e))
            
            # Test parity_choose
            try:
                resp = agent.call(
                    "parity_choose",
                    {"game_id": f"test_{agent.name}"}
                )
                result = resp.get("result", {})
                passed = (
                    result.get("type") == "RESPONSE_PARITY_CHOOSE" and
                    result.get("choice") in ("even", "odd")
                )
                record_test(f"{agent.name}: parity_choose", passed)
            except Exception as e:
                record_test(f"{agent.name}: parity_choose", False, str(e))
            
            # Test notify_match_result
            try:
                resp = agent.call(
                    "notify_match_result",
                    {
                        "game_id": f"test_{agent.name}",
                        "winner": agent.name,
                        "details": {"test": True}
                    }
                )
                result = resp.get("result", {})
                passed = result.get("ok") is True
                record_test(f"{agent.name}: notify_match_result", passed)
            except Exception as e:
                record_test(f"{agent.name}: notify_match_result", False, str(e))
        
        # ===== Phase 5: Run Mini League =====
        logger.info("")
        logger.info("=" * 60)
        logger.info("PHASE 5: Running Mini League")
        logger.info("=" * 60)
        
        try:
            final_standings = await manager.run_league()
            
            # Validate league results
            standings = final_standings.get("standings", [])
            total_games = final_standings.get("total_games", 0)
            
            # With 4 agents and 2 rounds, we expect 6 matchups * 2 rounds = 12 games
            expected_games = 12  # C(4,2) * 2 = 6 * 2 = 12
            
            record_test(
                "League completes successfully",
                len(standings) == NUM_AGENTS,
                f"{len(standings)} agents in standings"
            )
            
            record_test(
                f"Correct number of games played",
                total_games == expected_games,
                f"{total_games}/{expected_games} games"
            )
            
            # Check that all agents have games recorded
            for standing in standings:
                agent_name = standing.get("agent")
                games = standing.get("games_played", 0)
                # Each agent plays 3 opponents * 2 rounds = 6 games
                expected_agent_games = (NUM_AGENTS - 1) * 2
                record_test(
                    f"{agent_name} played correct number of games",
                    games == expected_agent_games,
                    f"{games}/{expected_agent_games} games"
                )
            
            # Check champion determination
            if standings:
                champion = final_standings.get("champion")
                record_test(
                    "Champion determined",
                    champion is not None,
                    f"Champion: {champion}"
                )
            
        except Exception as e:
            record_test("League completes successfully", False, str(e))
            import traceback
            traceback.print_exc()
        
        # ===== Phase 6: Test Error Handling =====
        logger.info("")
        logger.info("=" * 60)
        logger.info("PHASE 6: Testing Error Handling")
        logger.info("=" * 60)
        
        test_agent = agents[0]
        
        # Test unknown method
        try:
            payload = {
                "jsonrpc": "2.0",
                "id": 999,
                "method": "unknown_method",
                "params": {}
            }
            resp = httpx.post(test_agent.endpoint, json=payload, timeout=5)
            data = resp.json()
            passed = (
                "error" in data and
                data["error"].get("code") == -32601  # Method not found
            )
            record_test("Unknown method returns error -32601", passed)
        except Exception as e:
            record_test("Unknown method returns error -32601", False, str(e))
        
        # Test invalid JSON
        try:
            resp = httpx.post(
                test_agent.endpoint,
                content="not json",
                headers={"Content-Type": "application/json"},
                timeout=5
            )
            data = resp.json()
            passed = (
                "error" in data and
                data["error"].get("code") == -32700  # Parse error
            )
            record_test("Invalid JSON returns error -32700", passed)
        except Exception as e:
            record_test("Invalid JSON returns error -32700", False, str(e))
        
        # Test missing jsonrpc field
        try:
            payload = {"method": "parity_choose", "id": 1}
            resp = httpx.post(test_agent.endpoint, json=payload, timeout=5)
            data = resp.json()
            passed = (
                "error" in data and
                data["error"].get("code") == -32600  # Invalid request
            )
            record_test("Missing jsonrpc field returns error -32600", passed)
        except Exception as e:
            record_test("Missing jsonrpc field returns error -32600", False, str(e))
        
        # ===== Results =====
        logger.info("")
        logger.info("█" * 60)
        logger.info("     SELF-TEST RESULTS")
        logger.info("█" * 60)
        logger.info("")
        logger.info(f"  Total Tests: {test_results['passed'] + test_results['failed']}")
        logger.info(f"  Passed: {test_results['passed']}")
        logger.info(f"  Failed: {test_results['failed']}")
        logger.info("")
        
        if test_results["failed"] == 0:
            logger.info("  ✓ ALL TESTS PASSED!")
            return 0
        else:
            logger.error("  ✗ SOME TESTS FAILED")
            logger.info("")
            logger.info("Failed tests:")
            for test in test_results["tests"]:
                if not test["passed"]:
                    logger.error(f"  - {test['name']}: {test['details']}")
            return 1
        
    except KeyboardInterrupt:
        logger.info("\n\nSelf-test interrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"\nSelf-test error: {e}", exc_info=True)
        return 1
        
    finally:
        # Cleanup
        logger.info("")
        logger.info("Shutting down...")
        
        for agent in agents:
            agent.stop()
        
        if manager:
            await manager.stop_server()
        
        logger.info("✓ Cleanup complete")


def main() -> int:
    """Main entrypoint."""
    return asyncio.run(run_selftest())


if __name__ == "__main__":
    sys.exit(main())
