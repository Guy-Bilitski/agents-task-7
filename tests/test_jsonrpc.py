"""Unit tests for JSON-RPC 2.0 protocol implementation."""
import json
import pytest
from agent.jsonrpc import (
    parse_request,
    create_success_response,
    create_error_response,
    JSONRPCError,
    parse_error,
    invalid_request_error,
    method_not_found_error,
    invalid_params_error,
    internal_error,
)


class TestParseRequest:
    """Test JSON-RPC request parsing."""
    
    def test_valid_request_with_object_params(self):
        """Test parsing valid request with object params."""
        body = json.dumps({
            "jsonrpc": "2.0",
            "method": "test_method",
            "params": {"key": "value"},
            "id": 1
        }).encode()
        
        request, error = parse_request(body)
        
        assert error is None
        assert request is not None
        assert request.jsonrpc == "2.0"
        assert request.method == "test_method"
        assert request.params == {"key": "value"}
        assert request.id == 1
        assert request.is_notification is False
    
    def test_valid_request_with_array_params(self):
        """Test parsing valid request with array params."""
        body = json.dumps({
            "jsonrpc": "2.0",
            "method": "test_method",
            "params": [1, 2, 3],
            "id": "test-id"
        }).encode()
        
        request, error = parse_request(body)
        
        assert error is None
        assert request.params == [1, 2, 3]
        assert request.id == "test-id"
    
    def test_valid_request_without_params(self):
        """Test parsing valid request without params."""
        body = json.dumps({
            "jsonrpc": "2.0",
            "method": "test_method",
            "id": 42
        }).encode()
        
        request, error = parse_request(body)
        
        assert error is None
        assert request.params is None
    
    def test_notification_request(self):
        """Test parsing notification (no id)."""
        body = json.dumps({
            "jsonrpc": "2.0",
            "method": "notify_me",
            "params": {"data": "value"}
        }).encode()
        
        request, error = parse_request(body)
        
        assert error is None
        assert request.is_notification is True
        assert request.id is None
    
    def test_invalid_json(self):
        """Test parse error for invalid JSON."""
        body = b"{invalid json}"
        
        request, error = parse_request(body)
        
        assert request is None
        assert error is not None
        assert error.code == -32700
        assert "parse error" in error.message.lower()
    
    def test_missing_jsonrpc_field(self):
        """Test error for missing jsonrpc field."""
        body = json.dumps({
            "method": "test",
            "id": 1
        }).encode()
        
        request, error = parse_request(body)
        
        assert request is None
        assert error is not None
        assert error.code == -32600
    
    def test_invalid_jsonrpc_version(self):
        """Test error for wrong jsonrpc version."""
        body = json.dumps({
            "jsonrpc": "1.0",
            "method": "test",
            "id": 1
        }).encode()
        
        request, error = parse_request(body)
        
        assert request is None
        assert error is not None
        assert error.code == -32600
    
    def test_missing_method_field(self):
        """Test error for missing method field."""
        body = json.dumps({
            "jsonrpc": "2.0",
            "id": 1
        }).encode()
        
        request, error = parse_request(body)
        
        assert request is None
        assert error is not None
        assert error.code == -32600
    
    def test_invalid_params_type(self):
        """Test error for invalid params type (not object or array)."""
        body = json.dumps({
            "jsonrpc": "2.0",
            "method": "test",
            "params": "string_not_allowed",
            "id": 1
        }).encode()
        
        request, error = parse_request(body)
        
        assert request is None
        assert error is not None
        assert error.code == -32600


class TestCreateResponses:
    """Test JSON-RPC response creation."""
    
    def test_create_success_response(self):
        """Test creating success response."""
        result = {"status": "ok", "data": [1, 2, 3]}
        response = create_success_response(123, result)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 123
        assert response["result"] == result
        assert "error" not in response
    
    def test_create_error_response(self):
        """Test creating error response."""
        error = JSONRPCError(code=-32600, message="Invalid Request")
        response = create_error_response(456, error)
        
        assert response["jsonrpc"] == "2.0"
        assert response["id"] == 456
        assert response["error"]["code"] == -32600
        assert response["error"]["message"] == "Invalid Request"
        assert "result" not in response
    
    def test_create_error_response_with_data(self):
        """Test creating error response with additional data."""
        error = JSONRPCError(
            code=-32603,
            message="Internal error",
            data={"details": "Something went wrong"}
        )
        response = create_error_response(789, error)
        
        assert response["error"]["data"] == {"details": "Something went wrong"}


class TestErrorConstructors:
    """Test error constructor functions."""
    
    def test_parse_error(self):
        """Test parse error constructor."""
        error = parse_error(Exception("Bad JSON"))
        
        assert error.code == -32700
        assert "parse error" in error.message.lower()
        assert "Bad JSON" in str(error.data)
    
    def test_invalid_request_error(self):
        """Test invalid request error constructor."""
        error = invalid_request_error("Missing jsonrpc field")
        
        assert error.code == -32600
        assert error.message == "Invalid Request"
        assert error.data == "Missing jsonrpc field"
    
    def test_method_not_found_error(self):
        """Test method not found error constructor."""
        error = method_not_found_error("unknown_method")
        
        assert error.code == -32601
        assert error.message == "Method not found"
        assert "unknown_method" in str(error.data)
    
    def test_invalid_params_error(self):
        """Test invalid params error constructor."""
        error = invalid_params_error("params must be an object")
        
        assert error.code == -32602
        assert error.message == "Invalid params"
        assert error.data == "params must be an object"
    
    def test_internal_error(self):
        """Test internal error constructor."""
        exc = ValueError("Something broke")
        error = internal_error(exc)
        
        assert error.code == -32603
        assert error.message == "Internal error"
        assert "ValueError" in str(error.data)
        assert "Something broke" in str(error.data)


class TestJSONRPCError:
    """Test JSONRPCError class."""
    
    def test_error_is_exception(self):
        """Test that JSONRPCError can be raised."""
        error = JSONRPCError(code=-32600, message="Test error")
        
        with pytest.raises(JSONRPCError) as exc_info:
            raise error
        
        assert exc_info.value.code == -32600
        assert exc_info.value.message == "Test error"
    
    def test_error_string_representation(self):
        """Test error string representation."""
        error = JSONRPCError(code=-32601, message="Method not found", data="test")
        
        error_str = str(error)
        assert "-32601" in error_str
        assert "Method not found" in error_str
