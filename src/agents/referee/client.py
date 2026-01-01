"""Referee registration client - handles registration with League Manager."""
import asyncio
import logging
import httpx
from typing import Optional

logger = logging.getLogger(__name__)


class RefereeRegistrationClient:
    """Handles referee registration with the League Manager."""
    
    def __init__(
        self,
        referee_endpoint: str,
        league_manager_url: str,
        display_name: str = "Referee",
        version: str = "1.0.0"
    ):
        """Initialize registration client.
        
        Args:
            referee_endpoint: Full MCP endpoint URL for this referee
            league_manager_url: League Manager base URL
            display_name: Referee display name
            version: Referee version
        """
        self.referee_endpoint = referee_endpoint
        self.league_manager_url = league_manager_url
        self.display_name = display_name
        self.version = version
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def register_once(self) -> bool:
        """Attempt registration once.
        
        Returns:
            True if successful, False otherwise
        """
        payload = {
            "display_name": self.display_name,
            "version": self.version,
            "endpoint": self.referee_endpoint,
            "agent_type": "referee",
            "supported_game_types": ["even_odd"]
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.league_manager_url}/register",
                    json=payload,
                    timeout=5.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    logger.info(f"✓ Registered with League Manager: {data.get('message', 'OK')}")
                    return True
                else:
                    logger.warning(f"Registration failed: HTTP {response.status_code}")
                    return False
                    
        except httpx.ConnectError:
            logger.debug(f"Cannot connect to League Manager at {self.league_manager_url}")
            return False
        except Exception as e:
            logger.error(f"Registration error: {e}")
            return False
    
    async def register_with_retry(self, max_interval: float = 30.0):
        """Register with exponential backoff retry loop.
        
        This runs in the background and retries forever until successful.
        Server startup is NOT blocked by this.
        
        Args:
            max_interval: Maximum interval between retries in seconds
        """
        self._running = True
        interval = 1.0
        
        logger.info(f"Starting registration loop for {self.display_name}")
        
        while self._running:
            success = await self.register_once()
            
            if success:
                logger.info("Registration successful, stopping retry loop")
                break
            
            # Exponential backoff
            logger.debug(f"Retrying registration in {interval:.1f}s...")
            await asyncio.sleep(interval)
            interval = min(interval * 2, max_interval)
    
    def start_background_registration(self):
        """Start background registration task.
        
        This does NOT block - server can start immediately.
        """
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self.register_with_retry())
            logger.info("Background registration task started")
    
    def stop(self):
        """Stop the registration loop."""
        self._running = False
        if self._task and not self._task.done():
            self._task.cancel()
            logger.info("Registration task stopped")
