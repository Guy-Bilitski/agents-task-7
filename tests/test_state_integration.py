"""Integration test for state management.

Tests that state is properly initialized, thread-safe, and deterministic.

This test requires a running agent server on port 8001.
Run: python -m agent --port 8001 --display-name TestAgent
"""
import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed


def server_is_running():
    """Check if the agent server is running."""
    try:
        resp = requests.get("http://127.0.0.1:8001/health", timeout=1)
        return resp.status_code == 200
    except:
        return False


@pytest.mark.skipif(not server_is_running(), reason="Agent server not running on port 8001")
def test_state_management():
    """Test full state management lifecycle."""
    base_url = "http://127.0.0.1:8001"
    
    # Wait for server to be ready
    for _ in range(10):
        try:
            resp = requests.get(f"{base_url}/health", timeout=1)
            if resp.status_code == 200:
                break
        except:
            time.sleep(0.5)
    else:
        raise RuntimeError("Server not ready")
    
    print("✓ Server is ready")
    
    # Test 1: Game invitation
    resp = requests.post(
        f"{base_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 1,
            "method": "handle_game_invitation",
            "params": {
                "game_id": "test_game_1",
                "from_player": "league",
                "invitation_id": "inv_001"
            }
        }
    )
    result = resp.json()
    assert result["result"]["type"] == "GAME_JOIN_ACK"
    assert result["result"]["accepted"] is True
    print("✓ Game invitation recorded")
    
    # Test 2: Deterministic parity choice
    resp1 = requests.post(
        f"{base_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 2,
            "method": "parity_choose",
            "params": {"game_id": "test_game_1"}
        }
    )
    choice1 = resp1.json()["result"]["choice"]
    
    resp2 = requests.post(
        f"{base_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 3,
            "method": "parity_choose",
            "params": {"game_id": "test_game_1"}
        }
    )
    choice2 = resp2.json()["result"]["choice"]
    
    assert choice1 == choice2
    assert choice1 in ["even", "odd"]
    print(f"✓ Deterministic parity choice: {choice1} (consistent across calls)")
    
    # Test 3: Different game IDs may give different choices
    choices = {}
    for i in range(10):
        resp = requests.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": 100 + i,
                "method": "parity_choose",
                "params": {"game_id": f"game_{i}"}
            }
        )
        choices[f"game_{i}"] = resp.json()["result"]["choice"]
    
    # Should have variation (not all the same)
    unique_choices = set(choices.values())
    assert len(unique_choices) == 2  # Should have both even and odd
    print(f"✓ Game IDs produce varied choices: {dict(list(choices.items())[:3])}...")
    
    # Test 4: Match result tracking
    # Win
    resp = requests.post(
        f"{base_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 4,
            "method": "notify_match_result",
            "params": {
                "game_id": "test_game_1",
                "winner": "TestAgent",  # Must match display name
                "details": {"rolled": 7, "parity": "odd"}
            }
        }
    )
    assert resp.json()["result"]["ok"] is True
    print("✓ Win recorded")
    
    # Loss
    resp = requests.post(
        f"{base_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 5,
            "method": "notify_match_result",
            "params": {
                "game_id": "test_game_2",
                "winner": "OtherAgent",
                "details": {"rolled": 4, "parity": "even"}
            }
        }
    )
    assert resp.json()["result"]["ok"] is True
    print("✓ Loss recorded")
    
    # Draw
    resp = requests.post(
        f"{base_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 6,
            "method": "notify_match_result",
            "params": {
                "game_id": "test_game_3",
                "winner": None,
                "details": {"rolled": 6, "parity": "even"}
            }
        }
    )
    assert resp.json()["result"]["ok"] is True
    print("✓ Draw recorded")
    
    # Test 5: Extra parameters accepted
    resp = requests.post(
        f"{base_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 7,
            "method": "handle_game_invitation",
            "params": {
                "game_id": "test_game_4",
                "from_player": "league",
                "invitation_id": "inv_002",
                "extra_field": "should_not_fail",
                "nested": {"foo": "bar"}
            }
        }
    )
    assert resp.status_code == 200
    assert resp.json()["result"]["type"] == "GAME_JOIN_ACK"
    print("✓ Extra parameters handled gracefully")
    
    # Test 6: Concurrent requests (thread safety)
    def make_choice(game_id):
        resp = requests.post(
            f"{base_url}/mcp",
            json={
                "jsonrpc": "2.0",
                "id": hash(game_id) % 10000,
                "method": "parity_choose",
                "params": {"game_id": game_id}
            }
        )
        return resp.json()
    
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(make_choice, f"concurrent_{i}") for i in range(20)]
        results = [f.result() for f in as_completed(futures)]
    
    assert len(results) == 20
    assert all("result" in r for r in results)
    assert all(r["result"]["choice"] in ["even", "odd"] for r in results)
    print("✓ Concurrent requests handled safely (20 parallel requests)")
    
    # Test 7: Verify determinism after concurrent requests
    resp = requests.post(
        f"{base_url}/mcp",
        json={
            "jsonrpc": "2.0",
            "id": 999,
            "method": "parity_choose",
            "params": {"game_id": "concurrent_0"}
        }
    )
    new_choice = resp.json()["result"]["choice"]
    
    # Find original choice for concurrent_0
    original = next(r for r in results if r["result"]["game_id"] == "concurrent_0")
    assert new_choice == original["result"]["choice"]
    print("✓ Determinism maintained after concurrent load")
    
    print("\n" + "=" * 60)
    print("ALL STATE MANAGEMENT TESTS PASSED ✓")
    print("=" * 60)


if __name__ == "__main__":
    test_state_management()
