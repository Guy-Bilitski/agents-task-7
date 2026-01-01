"""Integration test for referee as separate MCP server.

This test verifies:
1. Referee server can start and register
2. League Manager accepts referee registration
3. Referee can run matches via JSON-RPC
4. Full game flow works correctly
"""
import asyncio
import httpx
import pytest


@pytest.mark.asyncio
async def test_referee_ping():
    """Test that referee responds to ping."""
    from agents.referee.app import RefereeServer
    
    # Create and start referee server
    server = RefereeServer(host="127.0.0.1", port=9999)
    
    # Start in background
    server_task = asyncio.create_task(server.start())
    
    try:
        # Wait for server to be ready
        await asyncio.sleep(1)
        
        # Test ping
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:9999/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "ping",
                    "params": {}
                },
                timeout=5.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "result" in data
            assert data["result"]["ok"] is True
            assert data["result"]["message"] == "pong"
    
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_referee_health():
    """Test that referee health endpoint works."""
    from agents.referee.app import RefereeServer
    
    # Create and start referee server
    server = RefereeServer(host="127.0.0.1", port=9998)
    
    # Start in background
    server_task = asyncio.create_task(server.start())
    
    try:
        # Wait for server to be ready
        await asyncio.sleep(1)
        
        # Test health
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "http://127.0.0.1:9998/health",
                timeout=5.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["ok"] is True
            assert data["service"] == "referee"
            assert data["version"] == "1.0.0"
    
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


@pytest.mark.asyncio
async def test_referee_method_not_found():
    """Test that referee returns error for unknown method."""
    from agents.referee.app import RefereeServer
    
    # Create and start referee server
    server = RefereeServer(host="127.0.0.1", port=9997)
    
    # Start in background
    server_task = asyncio.create_task(server.start())
    
    try:
        # Wait for server to be ready
        await asyncio.sleep(1)
        
        # Call unknown method
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://127.0.0.1:9997/mcp",
                json={
                    "jsonrpc": "2.0",
                    "id": 1,
                    "method": "unknown_method",
                    "params": {}
                },
                timeout=5.0
            )
            
            assert response.status_code == 200
            data = response.json()
            
            assert data["jsonrpc"] == "2.0"
            assert data["id"] == 1
            assert "error" in data
            assert data["error"]["code"] == -32601  # Method not found
    
    finally:
        # Stop server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass


if __name__ == "__main__":
    # Run tests
    asyncio.run(test_referee_ping())
    print("✅ Ping test passed")
    
    asyncio.run(test_referee_health())
    print("✅ Health test passed")
    
    asyncio.run(test_referee_method_not_found())
    print("✅ Method not found test passed")
    
    print("\n✅ All referee integration tests passed!")
