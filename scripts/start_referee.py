#!/usr/bin/env python3
"""Start the referee server.

Usage:
    python scripts/start_referee.py [--port PORT] [--league-manager URL]
"""
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

import asyncio
from agents.referee.main import main

if __name__ == "__main__":
    asyncio.run(main())
