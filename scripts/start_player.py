#!/usr/bin/env python3
"""
Start a single player agent for manual testing or league participation.

Usage:
    python scripts/start_player.py --port 8001 --name "Agent1"
    python scripts/start_player.py --port 8002 --name "Agent2" --league-url http://127.0.0.1:9000
"""
import sys
import os

# Add src to path (go up one level from scripts/)
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'src'))

from agents.player.main import main

if __name__ == "__main__":
    sys.exit(main())
