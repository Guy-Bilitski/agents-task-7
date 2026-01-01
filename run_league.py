#!/usr/bin/env python3
"""
Run a complete Parity Game League Competition.

This script is the easiest way to run the entire system:
1. Starts a League Manager
2. Spawns multiple agents
3. Runs a full league competition
4. Shows final standings

Usage:
    python run_league.py                    # Run with defaults (4 agents, 3 rounds)
    python run_league.py --num-agents 6     # Run with 6 agents
    python run_league.py --rounds 5         # Run 5 rounds per matchup
    python run_league.py --log-level DEBUG  # Verbose logging

Requirements:
    pip install -e .
"""
import sys
import os

# Add src directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from agents.league_manager.__main__ import main

if __name__ == "__main__":
    sys.exit(main())
