"""League registration client with retry logic.

Registers the agent with the league manager on startup.
Retries with exponential backoff if registration fails.
Never blocks server startup.
"""
import asyncio
import logging
from typing import Optional
import httpx

logger = logging.getLogger(__name__)


class RegistrationClient:
    """Client for registering with the league manager."""
    
    def __init__(
        self,
        display_name: str,
        version: str,
        endpoint: str,
        registration_url: str,
        initial_delay: float = 1.0,
        max_delay: float = 30.0,
        backoff_factor: float = 2.0,
    ):
        """Initialize registration client.
        
        Args:
            display_name: Agent display name
            version: Agent version
            endpoint: Agent MCP endpoint URL
            registration_url: League manager registration endpoint
            initial_delay: Initial retry delay in seconds
            max_delay: Maximum retry delay in seconds
            backoff_factor: Exponential backoff multiplier
        """
        self.display_name = display_name
        self.version = version
        self.endpoint = endpoint
        self.registration_url = registration_url
        self.initial_delay = initial_delay
        self.max_delay = max_delay
        self.backoff_factor = backoff_factor
        
        self._registered = False
        self._task: Optional[asyncio.Task] = None
    
    def start_background_registration(self) -> None:
        """Start background registration task.
        
        Does not block. Retries forever until successful.
        """
        logger.info("Starting background registration")
        self._task = asyncio.create_task(self._registration_loop())
    
    async def _registration_loop(self) -> None:
        """Registration loop with exponential backoff retry."""
        delay = self.initial_delay
        attempt = 0
        
        while not self._registered:
            attempt += 1
            
            try:
                await self._attempt_registration(attempt)
                self._registered = True
                logger.info("✓ Successfully registered with league manager")
                break
                
            except Exception as e:
                logger.warning(
                    f"Registration attempt {attempt} failed: {e}. "
                    f"Retrying in {delay:.1f}s..."
                )
                
                # Wait before retrying
                await asyncio.sleep(delay)
                
                # Exponential backoff with max limit
                delay = min(delay * self.backoff_factor, self.max_delay)
    
    async def _attempt_registration(self, attempt: int) -> None:
        """Attempt to register with the league manager.
        
        Args:
            attempt: Attempt number (for logging)
        
        Raises:
            Exception: If registration fails
        """
        payload = {
            "display_name": self.display_name,
            "version": self.version,
            "endpoint": self.endpoint,
        }
        
        logger.debug(f"Registration attempt {attempt}: {payload}")
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.registration_url,
                json=payload,
                timeout=httpx.Timeout(
                    connect=5.0,  # Connection timeout
                    read=10.0,    # Read timeout
                    write=5.0,    # Write timeout
                    pool=5.0,     # Pool timeout
                ),
            )
            
            # Raise on HTTP error status
            response.raise_for_status()
            
            # Log response
            try:
                response_data = response.json()
                logger.info(f"Registration response: {response_data}")
            except Exception:
                logger.info(f"Registration response (non-JSON): {response.text[:200]}")
    
    def is_registered(self) -> bool:
        """Check if agent is registered.
        
        Returns:
            True if registered, False otherwise
        """
        return self._registered
    
    async def stop(self) -> None:
        """Stop the registration task."""
        if self._task and not self._task.done():
            logger.info("Stopping registration task")
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass


# Global registration client instance
_registration_client: Optional[RegistrationClient] = None


def init_registration(
    display_name: str,
    version: str,
    endpoint: str,
    registration_url: str,
) -> None:
    """Initialize and start background registration.
    
    Args:
        display_name: Agent display name
        version: Agent version
        endpoint: Agent MCP endpoint URL
        registration_url: League manager registration endpoint
    """
    global _registration_client
    
    _registration_client = RegistrationClient(
        display_name=display_name,
        version=version,
        endpoint=endpoint,
        registration_url=registration_url,
    )
    
    _registration_client.start_background_registration()


def get_registration_client() -> Optional[RegistrationClient]:
    """Get the global registration client.
    
    Returns:
        Registration client instance, or None if not initialized
    """
    return _registration_client


async def stop_registration() -> None:
    """Stop the background registration task."""
    if _registration_client:
        await _registration_client.stop()
