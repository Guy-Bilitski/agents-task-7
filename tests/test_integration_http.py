"""Integration tests for HTTP endpoints."""
import pytest
import subprocess
import time
import requests
import signal


@pytest.fixture(scope="module")
def agent_server():
    """Start an agent server for testing."""
    proc = subprocess.Popen(
        [
            "venv/bin/python", "-m", "agent",
            "--port", "8099",
            "--display-name", "IntegrationTestAgent",
            "--league-url", "http://127.0.0.1:9999",  # Non-existent league
            "--registration-path", "/api/register",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    
    # Wait for server to start
    for _ in range(20):
        try:
            resp = requests.get("http://127.0.0.1:8099/health", timeout=0.5)
            if resp.status_code == 200:
                break
        except:
            time.sleep(0.5)
    else:
        proc.kill()
        raise RuntimeError("Agent server failed to start")
    
    yield "http://127.0.0.1:8099"
    
    # Cleanup
    proc.send_signal(signal.SIGTERM)
    proc.wait(timeout=2)


class TestHealthEndpoint:
    """Test /health endpoint."""
    
    def test_health_returns_ok(self, agent_server):
        """Test health endpoint returns OK."""
        resp = requests.get(f"{agent_server}/health")
        
        assert resp.status_code == 200
        assert resp.json() == {"ok": True}


class TestMCPEndpoint:
    """Test /mcp JSON-RPC endpoint."""
    
    def test_valid_json_rpc_request(self, agent_server):
        """Test valid JSON-RPC request."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "parity_choose",
            "params": {"game_id": "test_game"}
        }
        
        resp = requests.post(f"{agent_server}/mcp", json=payload)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 1
        assert "result" in data
        assert data["result"]["type"] == "RESPONSE_PARITY_CHOOSE"
    
    def test_invalid_json(self, agent_server):
        """Test invalid JSON returns parse error."""
        resp = requests.post(
            f"{agent_server}/mcp",
            data=b"{invalid json}",
            headers={"Content-Type": "application/json"}
        )
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert "error" in data
        assert data["error"]["code"] == -32700  # Parse error
    
    def test_missing_jsonrpc_field(self, agent_server):
        """Test missing jsonrpc field returns invalid request."""
        payload = {
            "id": 2,
            "method": "test"
        }
        
        resp = requests.post(f"{agent_server}/mcp", json=payload)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"]["code"] == -32600  # Invalid request
    
    def test_method_not_found(self, agent_server):
        """Test unknown method returns method not found."""
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "unknown_method",
            "params": {}
        }
        
        resp = requests.post(f"{agent_server}/mcp", json=payload)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["error"]["code"] == -32601  # Method not found
    
    def test_notification_returns_no_content(self, agent_server):
        """Test notification (no id) returns HTTP 204."""
        payload = {
            "jsonrpc": "2.0",
            "method": "parity_choose",
            "params": {"game_id": "notification_test"}
        }
        
        resp = requests.post(f"{agent_server}/mcp", json=payload)
        
        assert resp.status_code == 204
        assert len(resp.content) == 0


class TestGameInvitation:
    """Test handle_game_invitation integration."""
    
    def test_game_invitation_flow(self, agent_server):
        """Test complete game invitation flow."""
        payload = {
            "jsonrpc": "2.0",
            "id": 100,
            "method": "handle_game_invitation",
            "params": {
                "game_id": "integration_game_1",
                "from_player": "league_server",
                "invitation_id": "inv_100"
            }
        }
        
        resp = requests.post(f"{agent_server}/mcp", json=payload)
        
        assert resp.status_code == 200
        data = resp.json()
        assert data["jsonrpc"] == "2.0"
        assert data["id"] == 100
        
        result = data["result"]
        assert result["type"] == "GAME_JOIN_ACK"
        assert result["accepted"] is True
        assert result["game_id"] == "integration_game_1"
        assert result["invitation_id"] == "inv_100"


class TestParityChoice:
    """Test parity_choose integration."""
    
    def test_parity_choice_flow(self, agent_server):
        """Test complete parity choice flow."""
        payload = {
            "jsonrpc": "2.0",
            "id": 200,
            "method": "parity_choose",
            "params": {"game_id": "integration_game_2"}
        }
        
        resp = requests.post(f"{agent_server}/mcp", json=payload)
        
        assert resp.status_code == 200
        data = resp.json()
        
        result = data["result"]
        assert result["type"] == "RESPONSE_PARITY_CHOOSE"
        assert result["choice"] in ["even", "odd"]
        assert result["game_id"] == "integration_game_2"
    
    def test_deterministic_across_requests(self, agent_server):
        """Test same game_id returns same choice."""
        game_id = "deterministic_integration_test"
        
        payload = {
            "jsonrpc": "2.0",
            "id": 201,
            "method": "parity_choose",
            "params": {"game_id": game_id}
        }
        
        resp1 = requests.post(f"{agent_server}/mcp", json=payload)
        choice1 = resp1.json()["result"]["choice"]
        
        payload["id"] = 202
        resp2 = requests.post(f"{agent_server}/mcp", json=payload)
        choice2 = resp2.json()["result"]["choice"]
        
        assert choice1 == choice2


class TestMatchResult:
    """Test notify_match_result integration."""
    
    def test_match_result_flow(self, agent_server):
        """Test complete match result flow."""
        payload = {
            "jsonrpc": "2.0",
            "id": 300,
            "method": "notify_match_result",
            "params": {
                "game_id": "integration_game_3",
                "winner": "IntegrationTestAgent",
                "details": {"rolled": 7, "parity": "odd"}
            }
        }
        
        resp = requests.post(f"{agent_server}/mcp", json=payload)
        
        assert resp.status_code == 200
        data = resp.json()
        
        result = data["result"]
        assert result["ok"] is True


class TestFullGameFlow:
    """Test complete game flow end-to-end."""
    
    def test_invitation_choice_result_sequence(self, agent_server):
        """Test complete game sequence."""
        game_id = "full_flow_game"
        
        # Step 1: Invitation
        resp1 = requests.post(f"{agent_server}/mcp", json={
            "jsonrpc": "2.0",
            "id": 1001,
            "method": "handle_game_invitation",
            "params": {
                "game_id": game_id,
                "from_player": "league",
                "invitation_id": "flow_inv"
            }
        })
        assert resp1.status_code == 200
        assert resp1.json()["result"]["accepted"] is True
        
        # Step 2: Parity choice
        resp2 = requests.post(f"{agent_server}/mcp", json={
            "jsonrpc": "2.0",
            "id": 1002,
            "method": "parity_choose",
            "params": {"game_id": game_id}
        })
        assert resp2.status_code == 200
        choice = resp2.json()["result"]["choice"]
        assert choice in ["even", "odd"]
        
        # Step 3: Match result
        resp3 = requests.post(f"{agent_server}/mcp", json={
            "jsonrpc": "2.0",
            "id": 1003,
            "method": "notify_match_result",
            "params": {
                "game_id": game_id,
                "winner": "IntegrationTestAgent",
                "details": {"rolled": 5, "parity": "odd"}
            }
        })
        assert resp3.status_code == 200
        assert resp3.json()["result"]["ok"] is True
