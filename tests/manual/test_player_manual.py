#!/usr/bin/env python3
"""Simple test to verify player agent responds correctly to JSON-RPC calls."""
import sys
import os

# Add src directory to path (go up 2 levels from tests/manual/)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', 'src'))

import subprocess
import time
import requests
import json

def main():
    print("=" * 60)
    print("PLAYER AGENT VERIFICATION TEST")
    print("=" * 60)
    
    # Start agent
    print("\n1. Starting player agent on port 8001...")
    
    # Get project root (2 levels up from tests/manual/)
    project_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
    src_path = os.path.join(project_root, 'src')
    
    env = os.environ.copy()
    env['PYTHONPATH'] = src_path
    
    agent_proc = subprocess.Popen(
        [sys.executable, "-m", "agents.player", 
         "--port", "8001",
         "--display-name", "TestAgent",
         "--league-url", "http://127.0.0.1:9000"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
        cwd=project_root
    )
    
    # Wait for startup
    print("   Waiting for agent to start...")
    time.sleep(2)
    
    # Check health
    print("\n2. Checking /health endpoint...")
    try:
        resp = requests.get("http://127.0.0.1:8001/health", timeout=2)
        if resp.status_code == 200 and resp.json().get("ok"):
            print("   ✓ Health check passed")
        else:
            print(f"   ✗ Health check failed: {resp.status_code}")
            agent_proc.terminate()
            return 1
    except Exception as e:
        print(f"   ✗ Health check error: {e}")
        agent_proc.terminate()
        return 1
    
    # Test handle_game_invitation
    print("\n3. Testing handle_game_invitation...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "handle_game_invitation",
            "params": {
                "game_id": "test_game_1",
                "invitation_id": "inv_1",
                "from_player": "league"
            }
        }
        resp = requests.post("http://127.0.0.1:8001/mcp", json=payload, timeout=2)
        data = resp.json()
        
        if resp.status_code == 200 and data.get("result", {}).get("type") == "GAME_JOIN_ACK":
            print(f"   ✓ Invitation accepted: {data['result']}")
        else:
            print(f"   ✗ Unexpected response: {data}")
            agent_proc.terminate()
            return 1
    except Exception as e:
        print(f"   ✗ Error: {e}")
        agent_proc.terminate()
        return 1
    
    # Test parity_choose (method alias: choose_parity)
    print("\n4. Testing choose_parity (parity_choose)...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "parity_choose",
            "params": {"game_id": "test_game_1"}
        }
        resp = requests.post("http://127.0.0.1:8001/mcp", json=payload, timeout=2)
        data = resp.json()
        
        result = data.get("result", {})
        if resp.status_code == 200 and result.get("type") == "RESPONSE_PARITY_CHOOSE":
            choice = result.get("choice")
            if choice in ["even", "odd"]:
                print(f"   ✓ Parity choice made: {choice}")
            else:
                print(f"   ✗ Invalid choice: {choice}")
                agent_proc.terminate()
                return 1
        else:
            print(f"   ✗ Unexpected response: {data}")
            agent_proc.terminate()
            return 1
    except Exception as e:
        print(f"   ✗ Error: {e}")
        agent_proc.terminate()
        return 1
    
    # Test notify_match_result
    print("\n5. Testing notify_match_result...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "notify_match_result",
            "params": {
                "game_id": "test_game_1",
                "winner": "TestAgent",
                "details": {"rolled": 7, "parity": "odd"}
            }
        }
        resp = requests.post("http://127.0.0.1:8001/mcp", json=payload, timeout=2)
        data = resp.json()
        
        if resp.status_code == 200 and data.get("result", {}).get("ok"):
            print(f"   ✓ Match result acknowledged")
        else:
            print(f"   ✗ Unexpected response: {data}")
            agent_proc.terminate()
            return 1
    except Exception as e:
        print(f"   ✗ Error: {e}")
        agent_proc.terminate()
        return 1
    
    # Test method not found
    print("\n6. Testing method_not_found error...")
    try:
        payload = {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "nonexistent_method",
            "params": {}
        }
        resp = requests.post("http://127.0.0.1:8001/mcp", json=payload, timeout=2)
        data = resp.json()
        
        if resp.status_code == 200 and data.get("error", {}).get("code") == -32601:
            print(f"   ✓ Method not found error returned correctly")
        else:
            print(f"   ✗ Unexpected response: {data}")
            agent_proc.terminate()
            return 1
    except Exception as e:
        print(f"   ✗ Error: {e}")
        agent_proc.terminate()
        return 1
    
    # Cleanup
    print("\n7. Stopping agent...")
    agent_proc.terminate()
    agent_proc.wait(timeout=5)
    print("   ✓ Agent stopped")
    
    print("\n" + "=" * 60)
    print("ALL TESTS PASSED ✓")
    print("=" * 60)
    print("\nThe player agent is working correctly!")
    print("You can now run the full league with:")
    print("  python3 scripts/run_league.py")
    print("Or start individual agents with:")
    print("  python3 scripts/start_player.py --port 8001 --display-name Agent1 --league-url http://127.0.0.1:9000")
    print("=" * 60)
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
