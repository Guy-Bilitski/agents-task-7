"""Self-test harness for MCP Agent.

Launches 4 agents and simulates a mini league to validate all functionality.

Usage:
    python -m agent.selftest
"""
import subprocess
import time
import requests
import signal
import sys
import logging
from typing import List, Dict
import json

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class AgentProcess:
    """Manages a single agent process."""
    
    def __init__(self, port: int, name: str):
        self.port = port
        self.name = name
        self.endpoint = f"http://127.0.0.1:{port}/mcp"
        self.health_url = f"http://127.0.0.1:{port}/health"
        self.process: subprocess.Popen | None = None
    
    def start(self) -> bool:
        """Start the agent process.
        
        Returns:
            True if started successfully
        """
        try:
            logger.info(f"Starting agent '{self.name}' on port {self.port}")
            
            self.process = subprocess.Popen(
                [
                    "venv/bin/python", "-m", "agent",
                    "--port", str(self.port),
                    "--display-name", self.name,
                    "--league-url", "http://127.0.0.1:9999",  # Non-existent league
                    "--registration-path", "/api/register",
                    "--log-level", "WARNING",  # Reduce noise
                ],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            # Wait for health check
            for _ in range(20):
                try:
                    resp = requests.get(self.health_url, timeout=0.5)
                    if resp.status_code == 200:
                        logger.info(f"✓ Agent '{self.name}' is ready")
                        return True
                except:
                    time.sleep(0.5)
            
            logger.error(f"✗ Agent '{self.name}' failed to start")
            return False
            
        except Exception as e:
            logger.error(f"✗ Error starting agent '{self.name}': {e}")
            return False
    
    def stop(self):
        """Stop the agent process."""
        if self.process:
            try:
                self.process.send_signal(signal.SIGTERM)
                self.process.wait(timeout=2)
                logger.info(f"✓ Agent '{self.name}' stopped")
            except:
                self.process.kill()
                logger.warning(f"⚠ Agent '{self.name}' force killed")
    
    def call(self, method: str, params: dict, request_id: int = 1) -> dict:
        """Make JSON-RPC call to agent.
        
        Args:
            method: JSON-RPC method name
            params: Method parameters
            request_id: Request ID
        
        Returns:
            Response data
        
        Raises:
            Exception if call fails
        """
        payload = {
            "jsonrpc": "2.0",
            "id": request_id,
            "method": method,
            "params": params
        }
        
        resp = requests.post(self.endpoint, json=payload, timeout=5)
        resp.raise_for_status()
        
        data = resp.json()
        if "error" in data:
            raise Exception(f"JSON-RPC error: {data['error']}")
        
        return data


class LeagueSimulator:
    """Simulates a mini league with 4 agents."""
    
    def __init__(self, agents: List[AgentProcess]):
        self.agents = agents
        self.results = {
            "invitations": 0,
            "choices": 0,
            "results": 0,
            "errors": []
        }
    
    def run(self) -> bool:
        """Run the league simulation.
        
        Returns:
            True if all tests pass
        """
        logger.info("\n" + "=" * 60)
        logger.info("RUNNING LEAGUE SIMULATION")
        logger.info("=" * 60)
        
        success = True
        success &= self.test_invitations()
        success &= self.test_parity_choices()
        success &= self.test_match_results()
        success &= self.test_full_game_flow()
        success &= self.test_concurrent_requests()
        
        return success
    
    def test_invitations(self) -> bool:
        """Test game invitations for all agents."""
        logger.info("\n[TEST 1] Game Invitations")
        
        for i, agent in enumerate(self.agents):
            try:
                resp = agent.call(
                    "handle_game_invitation",
                    {
                        "game_id": f"game_{i}",
                        "from_player": "league",
                        "invitation_id": f"inv_{i}"
                    },
                    request_id=100 + i
                )
                
                result = resp["result"]
                assert result["type"] == "GAME_JOIN_ACK", "Wrong result type"
                assert result["accepted"] is True, "Invitation not accepted"
                assert result["game_id"] == f"game_{i}", "Game ID mismatch"
                
                self.results["invitations"] += 1
                logger.info(f"  ✓ {agent.name}: Invitation accepted")
                
            except Exception as e:
                logger.error(f"  ✗ {agent.name}: {e}")
                self.results["errors"].append(f"Invitation failed for {agent.name}: {e}")
                return False
        
        logger.info(f"✓ All {len(self.agents)} agents accepted invitations")
        return True
    
    def test_parity_choices(self) -> bool:
        """Test parity choices for all agents."""
        logger.info("\n[TEST 2] Parity Choices")
        
        for i, agent in enumerate(self.agents):
            try:
                resp = agent.call(
                    "parity_choose",
                    {"game_id": f"game_{i}"},
                    request_id=200 + i
                )
                
                result = resp["result"]
                assert result["type"] == "RESPONSE_PARITY_CHOOSE", "Wrong result type"
                assert result["choice"] in ["even", "odd"], "Invalid choice"
                assert result["game_id"] == f"game_{i}", "Game ID mismatch"
                
                self.results["choices"] += 1
                logger.info(f"  ✓ {agent.name}: Chose {result['choice']}")
                
            except Exception as e:
                logger.error(f"  ✗ {agent.name}: {e}")
                self.results["errors"].append(f"Choice failed for {agent.name}: {e}")
                return False
        
        logger.info(f"✓ All {len(self.agents)} agents made choices")
        return True
    
    def test_match_results(self) -> bool:
        """Test match results for all agents."""
        logger.info("\n[TEST 3] Match Results")
        
        outcomes = ["win", "loss", "draw", "win"]  # Varied outcomes
        
        for i, agent in enumerate(self.agents):
            try:
                outcome = outcomes[i % len(outcomes)]
                winner = agent.name if outcome == "win" else (
                    "OtherAgent" if outcome == "loss" else None
                )
                
                resp = agent.call(
                    "notify_match_result",
                    {
                        "game_id": f"game_{i}",
                        "winner": winner,
                        "details": {"rolled": 5, "parity": "odd"}
                    },
                    request_id=300 + i
                )
                
                result = resp["result"]
                assert result["ok"] is True, "Result not acknowledged"
                
                self.results["results"] += 1
                logger.info(f"  ✓ {agent.name}: Recorded {outcome}")
                
            except Exception as e:
                logger.error(f"  ✗ {agent.name}: {e}")
                self.results["errors"].append(f"Result failed for {agent.name}: {e}")
                return False
        
        logger.info(f"✓ All {len(self.agents)} agents recorded results")
        return True
    
    def test_full_game_flow(self) -> bool:
        """Test complete game flow for each agent."""
        logger.info("\n[TEST 4] Full Game Flow")
        
        for i, agent in enumerate(self.agents):
            try:
                game_id = f"full_flow_game_{i}"
                
                # Step 1: Invitation
                resp1 = agent.call(
                    "handle_game_invitation",
                    {
                        "game_id": game_id,
                        "from_player": "league",
                        "invitation_id": f"flow_inv_{i}"
                    },
                    request_id=400 + i * 3
                )
                assert resp1["result"]["accepted"] is True
                
                # Step 2: Choice
                resp2 = agent.call(
                    "parity_choose",
                    {"game_id": game_id},
                    request_id=401 + i * 3
                )
                choice = resp2["result"]["choice"]
                assert choice in ["even", "odd"]
                
                # Step 3: Result
                resp3 = agent.call(
                    "notify_match_result",
                    {
                        "game_id": game_id,
                        "winner": agent.name,
                        "details": {"rolled": 7, "parity": choice}
                    },
                    request_id=402 + i * 3
                )
                assert resp3["result"]["ok"] is True
                
                logger.info(f"  ✓ {agent.name}: Complete flow successful")
                
            except Exception as e:
                logger.error(f"  ✗ {agent.name}: {e}")
                self.results["errors"].append(f"Full flow failed for {agent.name}: {e}")
                return False
        
        logger.info(f"✓ All {len(self.agents)} agents completed full flow")
        return True
    
    def test_concurrent_requests(self) -> bool:
        """Test all agents can handle concurrent requests."""
        logger.info("\n[TEST 5] Concurrent Requests")
        
        import concurrent.futures
        
        def make_choice(agent, i):
            return agent.call(
                "parity_choose",
                {"game_id": f"concurrent_{i}"},
                request_id=500 + i
            )
        
        try:
            with concurrent.futures.ThreadPoolExecutor(max_workers=8) as executor:
                futures = []
                for i in range(20):
                    agent = self.agents[i % len(self.agents)]
                    future = executor.submit(make_choice, agent, i)
                    futures.append(future)
                
                results = [f.result(timeout=10) for f in futures]
            
            assert len(results) == 20
            logger.info(f"  ✓ Processed {len(results)} concurrent requests")
            return True
            
        except Exception as e:
            logger.error(f"  ✗ Concurrent test failed: {e}")
            self.results["errors"].append(f"Concurrent test failed: {e}")
            return False


def main() -> int:
    """Main self-test entrypoint."""
    logger.info("\n" + "█" * 60)
    logger.info("MCP AGENT SELF-TEST HARNESS")
    logger.info("█" * 60)
    logger.info("\nThis will:")
    logger.info("  1. Launch 4 agent processes")
    logger.info("  2. Run a simulated mini league")
    logger.info("  3. Validate all protocol interactions")
    logger.info("  4. Clean up all processes\n")
    
    # Create agent processes
    agents = [
        AgentProcess(8001, "Alpha"),
        AgentProcess(8002, "Beta"),
        AgentProcess(8003, "Gamma"),
        AgentProcess(8004, "Delta"),
    ]
    
    started = []
    
    try:
        # Start all agents
        logger.info("=" * 60)
        logger.info("STARTING AGENTS")
        logger.info("=" * 60)
        
        for agent in agents:
            if agent.start():
                started.append(agent)
            else:
                raise RuntimeError(f"Failed to start agent {agent.name}")
        
        logger.info(f"\n✓ All {len(started)} agents started successfully\n")
        
        # Run league simulation
        simulator = LeagueSimulator(started)
        success = simulator.run()
        
        # Print results
        logger.info("\n" + "=" * 60)
        logger.info("TEST RESULTS")
        logger.info("=" * 60)
        logger.info(f"Invitations: {simulator.results['invitations']}/{len(agents)}")
        logger.info(f"Choices: {simulator.results['choices']}/{len(agents)}")
        logger.info(f"Results: {simulator.results['results']}/{len(agents)}")
        logger.info(f"Errors: {len(simulator.results['errors'])}")
        
        if simulator.results["errors"]:
            logger.info("\nErrors:")
            for error in simulator.results["errors"]:
                logger.error(f"  - {error}")
        
        logger.info("\n" + "█" * 60)
        if success:
            logger.info("ALL TESTS PASSED ✓")
            logger.info("█" * 60)
            return 0
        else:
            logger.error("SOME TESTS FAILED ✗")
            logger.info("█" * 60)
            return 1
        
    except KeyboardInterrupt:
        logger.warning("\nInterrupted by user")
        return 130
        
    except Exception as e:
        logger.error(f"\n✗ Self-test failed: {e}", exc_info=True)
        return 1
        
    finally:
        # Clean up all agents
        logger.info("\n" + "=" * 60)
        logger.info("CLEANUP")
        logger.info("=" * 60)
        
        for agent in started:
            agent.stop()
        
        logger.info("✓ Cleanup complete\n")


if __name__ == "__main__":
    sys.exit(main())
