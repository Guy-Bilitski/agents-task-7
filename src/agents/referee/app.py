"""Referee MCP Server - Handles game orchestration.

The Referee runs as a separate MCP server that:
1. Registers with the League Manager
2. Accepts match requests via JSON-RPC
3. Orchestrates games between players
4. Reports results back to the League Manager
"""
import asyncio
import logging
from typing import Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from shared.jsonrpc import (
    create_success_response,
    create_error_response,
    parse_error,
    method_not_found_error,
    internal_error,
    PARSE_ERROR,
    INVALID_REQUEST,
    METHOD_NOT_FOUND,
    INTERNAL_ERROR,
    JSONRPCError
)
from agents.referee.referee import Referee, Agent

logger = logging.getLogger(__name__)


class RefereeServer:
    """MCP server for the Referee agent."""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8001):
        """Initialize referee server.
        
        Args:
            host: Host to bind to
            port: Port to bind to
        """
        self.host = host
        self.port = port
        self.referee = Referee(timeout=30.0)  # 30s timeout for player operations
        self.app = self._create_app()
    
    def _create_app(self) -> FastAPI:
        """Create the FastAPI application."""
        app = FastAPI(
            title="Referee MCP Server",
            description="Even-Odd Game Referee",
            version="1.0.0",
            docs_url=None,
            redoc_url=None
        )
        
        @app.get("/health")
        async def health():
            """Health check endpoint."""
            return {"ok": True, "service": "referee", "version": "1.0.0"}
        
        @app.post("/mcp")
        async def mcp_endpoint(request: Request):
            """Main MCP endpoint for JSON-RPC calls."""
            try:
                # Parse JSON body
                try:
                    body = await request.json()
                except Exception as e:
                    logger.error(f"JSON parse error: {e}")
                    error = JSONRPCError(code=PARSE_ERROR, message="Parse error", data=str(e))
                    return JSONResponse(
                        content=create_error_response(None, error),
                        status_code=200
                    )
                
                # Validate JSON-RPC request
                if not isinstance(body, dict):
                    error = JSONRPCError(code=INVALID_REQUEST, message="Invalid Request", data="Request must be an object")
                    return JSONResponse(
                        content=create_error_response(None, error),
                        status_code=200
                    )
                
                jsonrpc = body.get("jsonrpc")
                method = body.get("method")
                params = body.get("params", {})
                req_id = body.get("id")
                
                if jsonrpc != "2.0":
                    error = JSONRPCError(code=INVALID_REQUEST, message="Invalid Request", data="Invalid jsonrpc version")
                    return JSONResponse(
                        content=create_error_response(req_id, error),
                        status_code=200
                    )
                
                if not isinstance(method, str):
                    error = JSONRPCError(code=INVALID_REQUEST, message="Invalid Request", data="Method must be a string")
                    return JSONResponse(
                        content=create_error_response(req_id, error),
                        status_code=200
                    )
                
                # Route to handler
                try:
                    result = await self._handle_method(method, params)
                    
                    # If no id, it's a notification - don't respond
                    if req_id is None:
                        return JSONResponse(content={}, status_code=200)
                    
                    return JSONResponse(
                        content=create_success_response(req_id, result),
                        status_code=200
                    )
                    
                except NotImplementedError:
                    error = method_not_found_error(method)
                    return JSONResponse(
                        content=create_error_response(req_id, error),
                        status_code=200
                    )
                except Exception as e:
                    logger.error(f"Error handling {method}: {e}", exc_info=True)
                    error = internal_error(e)
                    return JSONResponse(
                        content=create_error_response(req_id, error),
                        status_code=200
                    )
            
            except Exception as e:
                logger.error(f"Unexpected error in MCP endpoint: {e}", exc_info=True)
                error = JSONRPCError(code=INTERNAL_ERROR, message="Internal server error", data=str(e))
                return JSONResponse(
                    content=create_error_response(None, error),
                    status_code=500
                )
        
        return app
    
    async def _handle_method(self, method: str, params: dict) -> dict:
        """Handle JSON-RPC method calls.
        
        Args:
            method: Method name
            params: Method parameters
        
        Returns:
            Method result
        
        Raises:
            NotImplementedError: If method not found
        """
        if method == "ping":
            return await self._handle_ping(params)
        elif method == "run_match":
            return await self._handle_run_match(params)
        else:
            raise NotImplementedError(f"Unknown method: {method}")
    
    async def _handle_ping(self, params: dict) -> dict:
        """Handle ping request.
        
        Args:
            params: Request parameters
        
        Returns:
            Pong response
        """
        return {"ok": True, "message": "pong"}
    
    async def _handle_run_match(self, params: dict) -> dict:
        """Handle match run request from League Manager.
        
        Expected params:
        {
            "match_id": "match_123",
            "player1": {
                "display_name": "Player1",
                "version": "1.0.0",
                "endpoint": "http://127.0.0.1:8101/mcp"
            },
            "player2": {
                "display_name": "Player2",
                "version": "1.0.0",
                "endpoint": "http://127.0.0.1:8102/mcp"
            }
        }
        
        Args:
            params: Match parameters
        
        Returns:
            Match result with winner and details
        """
        # Validate parameters
        if "player1" not in params or "player2" not in params:
            raise ValueError("Missing player1 or player2 in params")
        
        match_id = params.get("match_id", "unknown")
        
        # Create Agent objects
        p1_data = params["player1"]
        p2_data = params["player2"]
        
        player1 = Agent(
            display_name=p1_data.get("display_name", "Player1"),
            version=p1_data.get("version", "1.0.0"),
            endpoint=p1_data.get("endpoint")
        )
        
        player2 = Agent(
            display_name=p2_data.get("display_name", "Player2"),
            version=p2_data.get("version", "1.0.0"),
            endpoint=p2_data.get("endpoint")
        )
        
        logger.info(f"Running match {match_id}: {player1.display_name} vs {player2.display_name}")
        
        # Run the game
        result = await self.referee.run_game(player1, player2)
        
        # Convert GameResult to dict
        return {
            "match_id": match_id,
            "game_id": result.game_id,
            "player1": result.player1,
            "player2": result.player2,
            "player1_choice": result.player1_choice,
            "player2_choice": result.player2_choice,
            "dice_roll": result.dice_roll,
            "dice_parity": result.dice_parity,
            "winner": result.winner,
            "is_draw": result.is_draw
        }
    
    async def start(self):
        """Start the referee server."""
        import uvicorn
        
        config = uvicorn.Config(
            app=self.app,
            host=self.host,
            port=self.port,
            log_level="info",
            access_log=False
        )
        
        server = uvicorn.Server(config)
        
        logger.info(f"Referee MCP Server starting on http://{self.host}:{self.port}")
        logger.info(f"MCP endpoint: http://{self.host}:{self.port}/mcp")
        
        await server.serve()
