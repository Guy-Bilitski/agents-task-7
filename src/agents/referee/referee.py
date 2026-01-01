"""Referee - Runs individual parity games between agents.

The Referee:
1. Sends game invitations to both players
2. Collects parity choices from both players
3. Determines the winner based on game rules
4. Notifies both players of the result
"""
import logging
import random
import uuid
from dataclasses import dataclass
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


@dataclass
class Agent:
    """Registered agent information."""
    
    display_name: str
    version: str
    endpoint: str  # Full MCP endpoint URL
    
    def __hash__(self):
        return hash(self.display_name)


@dataclass
class GameResult:
    """Result of a single game."""
    
    game_id: str
    player1: str
    player2: str
    player1_choice: str
    player2_choice: str
    dice_roll: int
    dice_parity: str
    winner: Optional[str]  # None for draw (shouldn't happen in parity)
    
    @property
    def is_draw(self) -> bool:
        return self.winner is None


class Referee:
    """Runs parity games between agents."""
    
    def __init__(self, timeout: float = 5.0):
        """Initialize referee.
        
        Args:
            timeout: Timeout for agent communication in seconds
        """
        self.timeout = timeout
    
    async def run_game(self, player1: Agent, player2: Agent) -> GameResult:
        """Run a single parity game between two players.
        
        Args:
            player1: First player
            player2: Second player
        
        Returns:
            GameResult with winner determination
        """
        game_id = f"game_{uuid.uuid4().hex[:8]}"
        invitation_id = f"inv_{uuid.uuid4().hex[:8]}"
        
        logger.info(f"Starting game {game_id}: {player1.display_name} vs {player2.display_name}")
        
        # Step 1: Send invitations to both players
        inv1_ok = await self._send_invitation(player1, game_id, invitation_id + "_1")
        inv2_ok = await self._send_invitation(player2, game_id, invitation_id + "_2")
        
        if not inv1_ok or not inv2_ok:
            logger.error(f"Game {game_id}: Invitation failed")
            # Return a default result (both lose effectively)
            return GameResult(
                game_id=game_id,
                player1=player1.display_name,
                player2=player2.display_name,
                player1_choice="none",
                player2_choice="none",
                dice_roll=0,
                dice_parity="none",
                winner=None
            )
        
        # Step 2: Get parity choices from both players
        choice1 = await self._get_parity_choice(player1, game_id)
        choice2 = await self._get_parity_choice(player2, game_id)
        
        if not choice1 or not choice2:
            logger.error(f"Game {game_id}: Failed to get parity choices")
            return GameResult(
                game_id=game_id,
                player1=player1.display_name,
                player2=player2.display_name,
                player1_choice=choice1 or "none",
                player2_choice=choice2 or "none",
                dice_roll=0,
                dice_parity="none",
                winner=None
            )
        
        # Step 3: Roll the dice (1-100) and determine parity
        dice_roll = random.randint(1, 100)
        dice_parity = "even" if dice_roll % 2 == 0 else "odd"
        
        # Log decisions prominently
        logger.info(f"")
        logger.info(f"🎲 Game {game_id}: {player1.display_name} vs {player2.display_name}")
        logger.info(f"   {player1.display_name} chose: {choice1}")
        logger.info(f"   {player2.display_name} chose: {choice2}")
        logger.info(f"   Dice rolled: {dice_roll} ({dice_parity})")
        
        # Step 4: Determine winner
        # Player wins if their choice matches the dice parity
        p1_correct = (choice1 == dice_parity)
        p2_correct = (choice2 == dice_parity)
        
        if p1_correct and not p2_correct:
            winner = player1.display_name
            logger.info(f"   ✓ Winner: {winner} (correct prediction)")
        elif p2_correct and not p1_correct:
            winner = player2.display_name
            logger.info(f"   ✓ Winner: {winner} (correct prediction)")
        else:
            # Both correct or both wrong = draw (we'll give it to neither)
            winner = None
            result_reason = "both correct" if p1_correct and p2_correct else "both wrong"
            logger.info(f"   ⚖️  Result: DRAW ({result_reason})")
        logger.info(f"")
        
        result = GameResult(
            game_id=game_id,
            player1=player1.display_name,
            player2=player2.display_name,
            player1_choice=choice1,
            player2_choice=choice2,
            dice_roll=dice_roll,
            dice_parity=dice_parity,
            winner=winner
        )
        
        # Step 5: Notify both players of the result
        await self._notify_result(player1, result)
        await self._notify_result(player2, result)
        
        return result
    
    async def _send_invitation(self, player: Agent, game_id: str, invitation_id: str) -> bool:
        """Send game invitation to a player.
        
        Args:
            player: The agent to invite
            game_id: Game identifier
            invitation_id: Invitation identifier
        
        Returns:
            True if invitation accepted, False otherwise
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "handle_game_invitation",
            "params": {
                "game_id": game_id,
                "invitation_id": invitation_id,
                "from_player": "LeagueManager"
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    player.endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    logger.error(f"Invitation error from {player.display_name}: {data['error']}")
                    return False
                
                result = data.get("result", {})
                if result.get("type") == "GAME_JOIN_ACK" and result.get("accepted"):
                    logger.debug(f"Invitation accepted by {player.display_name}")
                    return True
                else:
                    logger.warning(f"Invitation not accepted by {player.display_name}: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error sending invitation to {player.display_name}: {e}")
            return False
    
    async def _get_parity_choice(self, player: Agent, game_id: str) -> Optional[str]:
        """Get parity choice from a player.
        
        Args:
            player: The agent to query
            game_id: Game identifier
        
        Returns:
            "even" or "odd", or None on error
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "parity_choose",
            "params": {
                "game_id": game_id
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    player.endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    logger.error(f"Parity choice error from {player.display_name}: {data['error']}")
                    return None
                
                result = data.get("result", {})
                choice = result.get("choice")
                
                if choice in ("even", "odd"):
                    return choice
                else:
                    logger.warning(f"Invalid choice from {player.display_name}: {choice}")
                    return None
                    
        except Exception as e:
            logger.error(f"Error getting parity choice from {player.display_name}: {e}")
            return None
    
    async def _notify_result(self, player: Agent, result: GameResult) -> bool:
        """Notify a player of the match result.
        
        Args:
            player: The agent to notify
            result: Game result
        
        Returns:
            True if notification acknowledged
        """
        payload = {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "notify_match_result",
            "params": {
                "game_id": result.game_id,
                "winner": result.winner,
                "details": {
                    "dice_roll": result.dice_roll,
                    "dice_parity": result.dice_parity,
                    "your_opponent": result.player2 if player.display_name == result.player1 else result.player1,
                    "player1": result.player1,
                    "player2": result.player2,
                    "player1_choice": result.player1_choice,
                    "player2_choice": result.player2_choice
                }
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    player.endpoint,
                    json=payload,
                    timeout=self.timeout
                )
                response.raise_for_status()
                data = response.json()
                
                if "error" in data:
                    logger.warning(f"Result notification error from {player.display_name}: {data['error']}")
                    return False
                
                result_data = data.get("result", {})
                if result_data.get("ok"):
                    logger.debug(f"Result acknowledged by {player.display_name}")
                    return True
                else:
                    logger.warning(f"Result not acknowledged by {player.display_name}")
                    return False
                    
        except Exception as e:
            logger.error(f"Error notifying {player.display_name}: {e}")
            return False
