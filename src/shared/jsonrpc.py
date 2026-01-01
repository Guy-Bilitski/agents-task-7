"""JSON-RPC 2.0 protocol implementation.

Handles request validation, response generation, and error handling
according to JSON-RPC 2.0 specification.

Specification: https://www.jsonrpc.org/specification
"""
import json
import logging
from typing import Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

# JSON-RPC 2.0 Error Codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603


@dataclass
class JSONRPCRequest:
    """Validated JSON-RPC request."""
    
    jsonrpc: str
    method: str
    params: Optional[dict | list]
    id: Optional[int | str]
    
    @property
    def is_notification(self) -> bool:
        """Check if this is a notification (no response needed)."""
        return self.id is None


@dataclass
class JSONRPCError(Exception):
    """JSON-RPC error details."""
    
    code: int
    message: str
    data: Optional[Any] = None
    
    def __str__(self) -> str:
        """String representation of error."""
        if self.data:
            return f"JSONRPCError({self.code}): {self.message} - {self.data}"
        return f"JSONRPCError({self.code}): {self.message}"


def parse_request(body: bytes) -> tuple[Optional[JSONRPCRequest], Optional[JSONRPCError]]:
    """Parse and validate JSON-RPC request.
    
    Args:
        body: Raw request body
    
    Returns:
        Tuple of (request, error). One will be None.
        - If valid: (JSONRPCRequest, None)
        - If invalid: (None, JSONRPCError)
    """
    # Step 1: Parse JSON
    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        logger.warning(f"JSON parse error: {e}")
        return None, JSONRPCError(
            code=PARSE_ERROR,
            message="Parse error",
            data=str(e)
        )
    
    # Step 2: Validate structure (must be object)
    if not isinstance(data, dict):
        logger.warning(f"Invalid request: not an object, got {type(data)}")
        return None, JSONRPCError(
            code=INVALID_REQUEST,
            message="Invalid Request",
            data="Request must be a JSON object"
        )
    
    # Step 3: Validate jsonrpc field
    if "jsonrpc" not in data:
        logger.warning("Invalid request: missing 'jsonrpc' field")
        return None, JSONRPCError(
            code=INVALID_REQUEST,
            message="Invalid Request",
            data="Missing 'jsonrpc' field"
        )
    
    if data["jsonrpc"] != "2.0":
        logger.warning(f"Invalid request: jsonrpc = {data['jsonrpc']}, expected '2.0'")
        return None, JSONRPCError(
            code=INVALID_REQUEST,
            message="Invalid Request",
            data="'jsonrpc' must be '2.0'"
        )
    
    # Step 4: Validate method field
    if "method" not in data:
        logger.warning("Invalid request: missing 'method' field")
        return None, JSONRPCError(
            code=INVALID_REQUEST,
            message="Invalid Request",
            data="Missing 'method' field"
        )
    
    if not isinstance(data["method"], str):
        logger.warning(f"Invalid request: method not a string, got {type(data['method'])}")
        return None, JSONRPCError(
            code=INVALID_REQUEST,
            message="Invalid Request",
            data="'method' must be a string"
        )
    
    # Step 5: Validate params (optional, but if present must be object or array)
    params = data.get("params")
    if params is not None and not isinstance(params, (dict, list)):
        logger.warning(f"Invalid request: params must be object or array, got {type(params)}")
        return None, JSONRPCError(
            code=INVALID_REQUEST,
            message="Invalid Request",
            data="'params' must be an object or array"
        )
    
    # Step 6: Extract id (optional, can be string, number, or null)
    request_id = data.get("id")
    if request_id is not None and not isinstance(request_id, (int, str, type(None))):
        logger.warning(f"Invalid request: id must be string, number, or null, got {type(request_id)}")
        return None, JSONRPCError(
            code=INVALID_REQUEST,
            message="Invalid Request",
            data="'id' must be a string, number, or null"
        )
    
    # Valid request
    request = JSONRPCRequest(
        jsonrpc=data["jsonrpc"],
        method=data["method"],
        params=params,
        id=request_id
    )
    
    logger.debug(f"Parsed valid JSON-RPC request: method={request.method}, id={request.id}")
    return request, None


def create_success_response(request_id: int | str | None, result: Any) -> dict:
    """Create JSON-RPC success response.
    
    Args:
        request_id: Request ID from original request
        result: Result data (any JSON-serializable value)
    
    Returns:
        JSON-RPC success response dict
    """
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result
    }


def create_error_response(
    request_id: int | str | None,
    error: JSONRPCError
) -> dict:
    """Create JSON-RPC error response.
    
    Args:
        request_id: Request ID from original request (or None if couldn't parse)
        error: Error details
    
    Returns:
        JSON-RPC error response dict
    """
    response = {
        "jsonrpc": "2.0",
        "id": request_id,
        "error": {
            "code": error.code,
            "message": error.message
        }
    }
    
    if error.data is not None:
        response["error"]["data"] = error.data
    
    return response


def parse_error(exception: Exception) -> JSONRPCError:
    """Create parse error from exception.
    
    Args:
        exception: Exception that occurred during parsing
    
    Returns:
        JSONRPCError
    """
    return JSONRPCError(
        code=PARSE_ERROR,
        message="Parse error",
        data=str(exception)
    )


def invalid_request_error(message: str) -> JSONRPCError:
    """Create invalid request error.
    
    Args:
        message: Description of what's invalid
    
    Returns:
        JSONRPCError
    """
    return JSONRPCError(
        code=INVALID_REQUEST,
        message="Invalid Request",
        data=message
    )


def method_not_found_error(method: str) -> JSONRPCError:
    """Create method not found error.
    
    Args:
        method: Method name that wasn't found
    
    Returns:
        JSONRPCError
    """
    return JSONRPCError(
        code=METHOD_NOT_FOUND,
        message="Method not found",
        data=f"Method '{method}' is not supported"
    )


def invalid_params_error(message: str) -> JSONRPCError:
    """Create invalid params error.
    
    Args:
        message: Description of what's wrong with params
    
    Returns:
        JSONRPCError
    """
    return JSONRPCError(
        code=INVALID_PARAMS,
        message="Invalid params",
        data=message
    )


def internal_error(exception: Exception) -> JSONRPCError:
    """Create internal error from exception.
    
    Args:
        exception: Exception that occurred
    
    Returns:
        JSONRPCError
    """
    return JSONRPCError(
        code=INTERNAL_ERROR,
        message="Internal error",
        data=f"{type(exception).__name__}: {str(exception)}"
    )
