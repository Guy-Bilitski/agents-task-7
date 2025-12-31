"""Mock league server for testing registration.

Simple HTTP server that accepts registration requests.
"""
import json
from http.server import HTTPServer, BaseHTTPRequestHandler
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LeagueHandler(BaseHTTPRequestHandler):
    """Handler for league registration requests."""
    
    def do_POST(self):
        """Handle POST requests."""
        if self.path == "/api/register":
            # Read request body
            content_length = int(self.headers['Content-Length'])
            body = self.rfile.read(content_length)
            
            try:
                data = json.loads(body)
                logger.info(f"Registration received: {data}")
                
                # Validate required fields
                required = ["display_name", "version", "endpoint"]
                if all(field in data for field in required):
                    response = {
                        "status": "registered",
                        "agent_id": f"agent_{data['display_name']}",
                        "message": "Successfully registered"
                    }
                    self.send_response(200)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    self.wfile.write(json.dumps(response).encode())
                    logger.info(f"✓ Registered agent: {data['display_name']}")
                else:
                    self.send_response(400)
                    self.send_header('Content-Type', 'application/json')
                    self.end_headers()
                    error = {"error": "Missing required fields"}
                    self.wfile.write(json.dumps(error).encode())
                    
            except json.JSONDecodeError:
                self.send_response(400)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                error = {"error": "Invalid JSON"}
                self.wfile.write(json.dumps(error).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_mock_league(port=9000):
    """Run mock league server."""
    server = HTTPServer(('127.0.0.1', port), LeagueHandler)
    logger.info(f"Mock league server running on http://127.0.0.1:{port}")
    logger.info("Press Ctrl+C to stop")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        logger.info("Shutting down mock league server")
        server.shutdown()


if __name__ == "__main__":
    run_mock_league()
