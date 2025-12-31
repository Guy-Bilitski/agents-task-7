"""FastAPI application for MCP Agent.

Provides:
- POST /mcp: JSON-RPC 2.0 endpoint
- GET /health: Health check endpoint
"""
import logging
from typing import Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

from agent.jsonrpc import (
    parse_request,
    create_success_response,
    create_error_response,
    method_not_found_error,
    internal_error,
    JSONRPCError,
)
from agent.registration import init_registration, stop_registration

logger = logging.getLogger(__name__)

# Store config for lifespan
_app_config: Optional[Any] = None


def create_app(config: Optional[Any] = None) -> FastAPI:
    """Create and configure FastAPI application.
    
    Args:
        config: Optional configuration object for registration
    """
    global _app_config
    _app_config = config
    
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        """Handle startup and shutdown."""
        # Startup
        logger.info("FastAPI application started")
        
        # Start background registration if config provided
        if _app_config:
            init_registration(
                display_name=_app_config.display_name,
                version=_app_config.version,
                endpoint=_app_config.endpoint,
                registration_url=_app_config.registration_url,
            )
            logger.info("Background registration initiated")
        
        yield
        
        # Shutdown
        logger.info("FastAPI application shutting down")
        await stop_registration()
    
    app = FastAPI(
        title="MCP Agent",
        description="Model Context Protocol Agent for League Competition",
        version="1.0.0",
        docs_url=None,  # Disable docs in production
        redoc_url=None,
        lifespan=lifespan,
    )
    
    @app.get("/health")
    async def health() -> dict[str, bool]:
        """Health check endpoint.
        
        Returns:
            {"ok": true} if server is running
        """
        return {"ok": True}
    
    @app.post("/mcp", response_model=None)
    async def mcp_endpoint(request: Request):
        """MCP JSON-RPC 2.0 endpoint.
        
        Accepts JSON-RPC 2.0 requests and dispatches to appropriate handlers.
        """
        request_id = None
        
        try:
            # Read raw body
            body = await request.body()
            
            # Parse and validate JSON-RPC request
            rpc_request, error = parse_request(body)
            
            # If parsing failed, return error
            if error:
                response = create_error_response(None, error)
                logger.warning(f"Invalid JSON-RPC request: {error.message}")
                return JSONResponse(content=response)
            
            # Extract request ID for logging and responses
            request_id = rpc_request.id
            logger.info(f"JSON-RPC request: method={rpc_request.method}, id={request_id}")
            
            # Check if this is a notification (no response needed)
            if rpc_request.is_notification:
                logger.info(f"Notification received (no response): method={rpc_request.method}")
                # Still process the method, just don't respond
                try:
                    from agent.tools import dispatch_method
                    dispatch_method(rpc_request.method, rpc_request.params)
                except Exception as e:
                    logger.error(f"Error processing notification: {e}", exc_info=True)
                return Response(status_code=204)  # No content
            
            # Dispatch to method handler
            try:
                from agent.tools import dispatch_method
                result = dispatch_method(rpc_request.method, rpc_request.params)
                response = create_success_response(request_id, result)
                logger.info(f"Method '{rpc_request.method}' succeeded")
                return JSONResponse(content=response)
            
            except KeyError as e:
                # Method not found
                error = method_not_found_error(rpc_request.method)
                response = create_error_response(request_id, error)
                logger.warning(f"Method not found: {rpc_request.method}")
                return JSONResponse(content=response)
            
            except JSONRPCError as e:
                # Handler raised a JSON-RPC error (e.g., invalid params)
                response = create_error_response(request_id, e)
                logger.warning(f"Handler error: {e.message}")
                return JSONResponse(content=response)
            
        except Exception as e:
            # Catch any unexpected errors
            logger.error(f"Unexpected error in MCP endpoint: {e}", exc_info=True)
            error = internal_error(e)
            response = create_error_response(request_id, error)
            return JSONResponse(content=response, status_code=500)
    
    return app
