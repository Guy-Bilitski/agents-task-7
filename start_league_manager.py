#!/usr/bin/env python3
"""
Start the League Manager server.

Usage:
    python start_league_manager.py
    python start_league_manager.py --port 9000
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

# The league manager needs to import its own main
# For now, let's check if it exists
try:
    from agents.league_manager.app import create_app
    from agents.league_manager.config import parse_league_args
    import uvicorn
    
    config = parse_league_args()
    app = create_app()
    uvicorn.run(app, host="127.0.0.1", port=config.port)
except ImportError as e:
    print(f"League Manager not fully implemented yet: {e}")
    print("You can start individual player agents with:")
    print("  python start_player.py --port 8001 --display-name Agent1 --league-url http://127.0.0.1:9000")
    sys.exit(1)
