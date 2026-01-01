#!/usr/bin/env python3
"""
Comprehensive validation script for Even-Odd League system.

Tests:
1. JSON-RPC 2.0 protocol compliance
2. All player agent methods
3. Error handling
4. Registration flow
5. Full league integration

Run this script to validate the entire system meets specification requirements.
"""

import subprocess
import time
import requests
import json
import sys
from typing import Dict, Any, Optional


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def log_info(msg: str):
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {msg}")


def log_success(msg: str):
    print(f"{Colors.GREEN}✓{Colors.RESET} {msg}")


def log_error(msg: str):
    print(f"{Colors.RED}✗{Colors.RESET} {msg}")


def log_test(msg: str):
    print(f"\n{Colors.BOLD}{msg}{Colors.RESET}")


def jsonrpc_call(url: str, method: str, params: Optional[Dict[str, Any]] = None, 
                 call_id: Any = 1) -> Dict[str, Any]:
    """Make a JSON-RPC 2.0 call."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": call_id
    }
    if params is not None:
        payload["params"] = params
    
    response = requests.post(url, json=payload, timeout=10)
    return response


def validate_jsonrpc_envelope(response: Dict[str, Any], expected_id: Any) -> bool:
    """Validate JSON-RPC 2.0 envelope structure."""
    if not isinstance(response, dict):
        log_error(f"Response is not a JSON object: {type(response)}")
        return False
    
    if response.get("jsonrpc") != "2.0":
        log_error(f"Missing or incorrect jsonrpc version: {response.get('jsonrpc')}")
        return False
    
    if response.get("id") != expected_id:
        log_error(f"ID mismatch: expected {expected_id}, got {response.get('id')}")
        return False
    
    has_result = "result" in response
    has_error = "error" in response
    
    if has_result and has_error:
        log_error("Response has both result and error")
        return False
    
    if not has_result and not has_error:
        log_error("Response has neither result nor error")
        return False
    
    if has_error:
        error = response["error"]
        if not isinstance(error, dict):
            log_error(f"Error is not an object: {type(error)}")
            return False
        if "code" not in error or "message" not in error:
            log_error(f"Error missing code or message: {error}")
            return False
    
    return True


def test_protocol_compliance(agent_url: str) -> bool:
    """Test JSON-RPC 2.0 protocol compliance."""
    log_test("TEST 1: JSON-RPC 2.0 Protocol Compliance")
    
    all_passed = True
    
    # Test 1.1: Valid method call
    log_info("1.1: Testing valid method call (ping)...")
    try:
        response = jsonrpc_call(agent_url, "ping", {})
        data = response.json()
        
        if validate_jsonrpc_envelope(data, 1):
            if "result" in data:
                log_success("Valid method call: envelope correct, has result")
            else:
                log_error(f"Valid call returned error: {data.get('error')}")
                all_passed = False
        else:
            log_error("Invalid JSON-RPC envelope")
            all_passed = False
    except Exception as e:
        log_error(f"Exception during valid call: {e}")
        all_passed = False
    
    # Test 1.2: Method not found
    log_info("1.2: Testing method not found...")
    try:
        response = jsonrpc_call(agent_url, "nonexistent_method", {})
        data = response.json()
        
        if validate_jsonrpc_envelope(data, 1):
            if "error" in data and data["error"]["code"] == -32601:
                log_success("Method not found: correct error code -32601")
            else:
                log_error(f"Wrong error code: {data.get('error', {}).get('code')}")
                all_passed = False
        else:
            log_error("Invalid JSON-RPC envelope")
            all_passed = False
    except Exception as e:
        log_error(f"Exception during method not found test: {e}")
        all_passed = False
    
    # Test 1.3: Invalid JSON
    log_info("1.3: Testing parse error (invalid JSON)...")
    try:
        response = requests.post(
            agent_url,
            data="invalid json{",
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        data = response.json()
        
        if "error" in data and data["error"]["code"] == -32700:
            log_success("Parse error: correct error code -32700")
        else:
            log_error(f"Wrong error code for parse error: {data.get('error', {}).get('code')}")
            all_passed = False
    except Exception as e:
        log_error(f"Exception during parse error test: {e}")
        all_passed = False
    
    # Test 1.4: Missing required fields
    log_info("1.4: Testing invalid request (missing method)...")
    try:
        response = requests.post(
            agent_url,
            json={"jsonrpc": "2.0", "id": 1},
            timeout=10
        )
        data = response.json()
        
        if "error" in data and data["error"]["code"] == -32600:
            log_success("Invalid request: correct error code -32600")
        else:
            log_error(f"Wrong error code for invalid request: {data.get('error', {}).get('code')}")
            all_passed = False
    except Exception as e:
        log_error(f"Exception during invalid request test: {e}")
        all_passed = False
    
    return all_passed


def test_player_methods(agent_url: str) -> bool:
    """Test all required player methods."""
    log_test("TEST 2: Player Agent Methods")
    
    all_passed = True
    game_id = "validation_game_123"
    
    # Test 2.1: handle_game_invitation
    log_info("2.1: Testing handle_game_invitation...")
    try:
        response = jsonrpc_call(
            agent_url,
            "handle_game_invitation",
            {
                "game_id": game_id,
                "from_player": "validation_test",
                "invitation_id": "inv_123",
                "extra_field": "should_be_accepted"
            }
        )
        data = response.json()
        
        if validate_jsonrpc_envelope(data, 1):
            result = data.get("result", {})
            if result.get("type") == "GAME_JOIN_ACK" and result.get("accepted"):
                log_success("handle_game_invitation: correct response format")
            else:
                log_error(f"handle_game_invitation: wrong result format: {result}")
                all_passed = False
        else:
            all_passed = False
    except Exception as e:
        log_error(f"Exception in handle_game_invitation: {e}")
        all_passed = False
    
    # Test 2.2: choose_parity
    log_info("2.2: Testing choose_parity...")
    try:
        response = jsonrpc_call(
            agent_url,
            "choose_parity",
            {"game_id": game_id, "extra_field": "accepted"}
        )
        data = response.json()
        
        if validate_jsonrpc_envelope(data, 1):
            result = data.get("result", {})
            if (result.get("type") == "RESPONSE_PARITY_CHOOSE" and
                result.get("choice") in ["even", "odd"]):
                log_success(f"choose_parity: correct response, choice={result['choice']}")
            else:
                log_error(f"choose_parity: wrong result format: {result}")
                all_passed = False
        else:
            all_passed = False
    except Exception as e:
        log_error(f"Exception in choose_parity: {e}")
        all_passed = False
    
    # Test 2.3: parity_choose (alias)
    log_info("2.3: Testing parity_choose (alias)...")
    try:
        response = jsonrpc_call(
            agent_url,
            "parity_choose",
            {"game_id": game_id}
        )
        data = response.json()
        
        if validate_jsonrpc_envelope(data, 1):
            result = data.get("result", {})
            if (result.get("type") == "RESPONSE_PARITY_CHOOSE" and
                result.get("choice") in ["even", "odd"]):
                log_success(f"parity_choose: alias works, choice={result['choice']}")
            else:
                log_error(f"parity_choose: wrong result format: {result}")
                all_passed = False
        else:
            all_passed = False
    except Exception as e:
        log_error(f"Exception in parity_choose: {e}")
        all_passed = False
    
    # Test 2.4: notify_match_result
    log_info("2.4: Testing notify_match_result...")
    try:
        response = jsonrpc_call(
            agent_url,
            "notify_match_result",
            {
                "game_id": game_id,
                "winner": "validation_test",
                "details": {"rolled": 7, "parity": "odd"}
            }
        )
        data = response.json()
        
        if validate_jsonrpc_envelope(data, 1):
            result = data.get("result", {})
            if result.get("ok"):
                log_success("notify_match_result: correct acknowledgment")
            else:
                log_error(f"notify_match_result: wrong result format: {result}")
                all_passed = False
        else:
            all_passed = False
    except Exception as e:
        log_error(f"Exception in notify_match_result: {e}")
        all_passed = False
    
    return all_passed


def test_health_endpoint(agent_url: str) -> bool:
    """Test health endpoint."""
    log_test("TEST 3: Health Endpoint")
    
    try:
        health_url = agent_url.replace("/mcp", "/health")
        response = requests.get(health_url, timeout=5)
        
        if response.status_code == 200:
            log_success(f"Health check: {response.status_code} OK")
            return True
        else:
            log_error(f"Health check failed: {response.status_code}")
            return False
    except Exception as e:
        log_error(f"Exception in health check: {e}")
        return False


def test_registration_retry(league_url: str, agent_port: int = 8199) -> bool:
    """Test that agents retry registration without blocking startup."""
    log_test("TEST 4: Registration Retry Behavior")
    
    log_info(f"4.1: Starting agent without league manager running...")
    
    # Start agent pointing to non-existent league
    proc = subprocess.Popen(
        [
            sys.executable,
            "scripts/start_player.py",
            "--port", str(agent_port),
            "--display-name", "RetryTestAgent",
            "--league-url", "http://127.0.0.1:9999",  # Non-existent
            "--log-level", "WARNING"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Give it time to start
    time.sleep(3)
    
    # Check if health endpoint works despite registration failures
    try:
        agent_url = f"http://127.0.0.1:{agent_port}"
        response = requests.get(f"{agent_url}/health", timeout=5)
        
        if response.status_code == 200:
            log_success("Agent started successfully despite registration failures")
            log_success("Registration is non-blocking ✓")
            proc.terminate()
            proc.wait(timeout=5)
            return True
        else:
            log_error("Agent health check failed")
            proc.terminate()
            proc.wait(timeout=5)
            return False
    except Exception as e:
        log_error(f"Exception testing registration retry: {e}")
        proc.terminate()
        proc.wait(timeout=5)
        return False


def test_full_league() -> bool:
    """Test full league integration."""
    log_test("TEST 5: Full League Integration")
    
    log_info("Running quick verification script...")
    
    try:
        result = subprocess.run(
            [sys.executable, "scripts/verify.py"],
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0 and "VERIFICATION PASSED" in result.stdout:
            log_success("Full league integration test passed")
            return True
        else:
            log_error("Full league integration test failed")
            print(result.stdout)
            print(result.stderr)
            return False
    except Exception as e:
        log_error(f"Exception in full league test: {e}")
        return False


def main():
    """Run all validation tests."""
    print(f"\n{Colors.BOLD}{'=' * 60}")
    print("Even-Odd League: Comprehensive Validation")
    print(f"{'=' * 60}{Colors.RESET}\n")
    
    # Start a test agent
    log_info("Starting test agent on port 8198...")
    agent_proc = subprocess.Popen(
        [
            sys.executable,
            "scripts/start_player.py",
            "--port", "8198",
            "--display-name", "ValidationAgent",
            "--league-url", "http://127.0.0.1:9000",
            "--log-level", "WARNING"
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for agent to start
    time.sleep(3)
    
    agent_url = "http://127.0.0.1:8198/mcp"
    
    try:
        # Run all tests
        results = []
        
        results.append(("JSON-RPC 2.0 Protocol", test_protocol_compliance(agent_url)))
        results.append(("Player Methods", test_player_methods(agent_url)))
        results.append(("Health Endpoint", test_health_endpoint(agent_url)))
        
        # Stop test agent
        agent_proc.terminate()
        agent_proc.wait(timeout=5)
        
        results.append(("Registration Retry", test_registration_retry("http://127.0.0.1:9000")))
        results.append(("Full League", test_full_league()))
        
        # Print summary
        print(f"\n{Colors.BOLD}{'=' * 60}")
        print("VALIDATION SUMMARY")
        print(f"{'=' * 60}{Colors.RESET}\n")
        
        passed = 0
        failed = 0
        
        for name, result in results:
            if result:
                log_success(f"{name}: PASSED")
                passed += 1
            else:
                log_error(f"{name}: FAILED")
                failed += 1
        
        print(f"\n{Colors.BOLD}Total: {passed} passed, {failed} failed{Colors.RESET}\n")
        
        if failed == 0:
            print(f"{Colors.GREEN}{Colors.BOLD}✓ ALL VALIDATIONS PASSED{Colors.RESET}")
            print(f"{Colors.GREEN}System is ready for production!{Colors.RESET}\n")
            return 0
        else:
            print(f"{Colors.RED}{Colors.BOLD}✗ SOME VALIDATIONS FAILED{Colors.RESET}")
            print(f"{Colors.RED}Please review the errors above.{Colors.RESET}\n")
            return 1
    
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Interrupted by user{Colors.RESET}")
        agent_proc.terminate()
        return 1
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        agent_proc.terminate()
        return 1


if __name__ == "__main__":
    sys.exit(main())
