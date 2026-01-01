"""Referee agent package."""
from agents.referee.app import RefereeServer
from agents.referee.client import RefereeRegistrationClient
from agents.referee.referee import Referee, Agent, GameResult

__version__ = "1.0.0"

__all__ = [
    "RefereeServer",
    "RefereeRegistrationClient",
    "Referee",
    "Agent",
    "GameResult",
]
