"""Tool handlers for MCP Agent.

Implements the three required JSON-RPC methods:
1. handle_game_invitation
2. parity_choose
3. notify_match_result
"""
import logging
from typing import Any, Callable

from agent.jsonrpc import JSONRPCError, invalid_params_error
from agent.state import get_state, deterministic_parity_choice

logger = logging.getLogger(__name__)


def handle_game_invitation(params: dict | list | None) -> dict:
    """Handle game invitation and return GAME_JOIN_ACK.
    
    Args:
        params: Invitation parameters (expected to be a dict)
    
    Returns:
        GAME_JOIN_ACK response
    
    Raises:
        JSONRPCError: If params are invalid
    """
    # Validate params
    if params is None or not isinstance(params, dict):
        raise invalid_params_error("params must be an object")
    
    # Extract known fields
    game_id = params.get("game_id")
    invitation_id = params.get("invitation_id")
    from_player = params.get("from_player")
    
    # Extract extra fields (for debugging)
    known_fields = {"game_id", "invitation_id", "from_player"}
    extra_fields = {k: v for k, v in params.items() if k not in known_fields}
    
    logger.info(
        f"Received game invitation: game_id={game_id}, "
        f"invitation_id={invitation_id}, from={from_player}"
    )
    
    if extra_fields:
        logger.debug(f"Extra fields in invitation: {extra_fields}")
    
    # Record in state
    state = get_state()
    state.record_invitation(game_id, invitation_id, from_player, extra_fields)
    
    # Return GAME_JOIN_ACK
    response = {
        "type": "GAME_JOIN_ACK",
        "accepted": True,
    }
    
    # Include game_id if provided
    if game_id:
        response["game_id"] = game_id
    
    # Include invitation_id if provided
    if invitation_id:
        response["invitation_id"] = invitation_id
    
    logger.info(f"Accepting game invitation: {response}")
    return response


def parity_choose(params: dict | list | None) -> dict:
    """Handle parity choice and return RESPONSE_PARITY_CHOOSE.
    
    Args:
        params: Choice parameters (expected to be a dict)
    
    Returns:
        RESPONSE_PARITY_CHOOSE response
    
    Raises:
        JSONRPCError: If params are invalid
    """
    # Validate params
    if params is None or not isinstance(params, dict):
        raise invalid_params_error("params must be an object")
    
    game_id = params.get("game_id")
    
    # Extract extra fields
    known_fields = {"game_id"}
    extra_fields = {k: v for k, v in params.items() if k not in known_fields}
    
    logger.info(f"Parity choice requested for game_id={game_id}")
    
    if extra_fields:
        logger.debug(f"Extra fields in parity_choose: {extra_fields}")
    
    # Determine choice using deterministic strategy
    choice = deterministic_parity_choice(game_id)
    
    # Record in state
    state = get_state()
    state.record_choice(game_id, choice, extra_fields)
    
    response = {
        "type": "RESPONSE_PARITY_CHOOSE",
        "choice": choice,
    }
    
    # Include game_id if provided
    if game_id:
        response["game_id"] = game_id
    
    logger.info(f"Parity choice: {choice} for game_id={game_id}")
    return response


def notify_match_result(params: dict | list | None) -> dict:
    """Handle match result notification and acknowledge.
    
    Args:
        params: Result parameters (expected to be a dict)
    
    Returns:
        Acknowledgment response
    
    Raises:
        JSONRPCError: If params are invalid
    """
    # Validate params
    if params is None or not isinstance(params, dict):
        raise invalid_params_error("params must be an object")
    
    game_id = params.get("game_id")
    winner = params.get("winner")
    details = params.get("details", {})
    
    # Extract extra fields
    known_fields = {"game_id", "winner", "details"}
    extra_fields = {k: v for k, v in params.items() if k not in known_fields}
    
    logger.info(f"Match result: game_id={game_id}, winner={winner}, details={details}")
    
    if extra_fields:
        logger.debug(f"Extra fields in match result: {extra_fields}")
    
    # Record in state
    state = get_state()
    state.record_result(game_id, winner, details, extra_fields)
    
    # Log updated statistics
    stats = state.get_stats()
    logger.info(
        f"Updated stats: games={stats.games_played}, "
        f"W={stats.wins}, L={stats.losses}, D={stats.draws}, "
        f"win_rate={stats.win_rate:.2%}"
    )
    
    # Return acknowledgment
    response = {"ok": True}
    
    logger.info(f"Match result acknowledged for game_id={game_id}")
    return response


# Method registry: maps method names to handler functions
METHOD_REGISTRY: dict[str, Callable[[dict | list | None], dict]] = {
    "handle_game_invitation": handle_game_invitation,
    "parity_choose": parity_choose,
    "notify_match_result": notify_match_result,
}


def dispatch_method(method: str, params: dict | list | None) -> dict:
    """Dispatch method call to appropriate handler.
    
    Args:
        method: Method name
        params: Method parameters
    
    Returns:
        Handler result
    
    Raises:
        KeyError: If method not found in registry
        JSONRPCError: If handler raises validation error
    """
    if method not in METHOD_REGISTRY:
        raise KeyError(f"Method '{method}' not found")
    
    handler = METHOD_REGISTRY[method]
    
    # Call handler
    result = handler(params)
    
    return result


def get_supported_methods() -> list[str]:
    """Get list of supported method names.
    
    Returns:
        List of method names
    """
    return list(METHOD_REGISTRY.keys())
