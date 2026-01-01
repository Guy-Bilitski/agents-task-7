"""Allow running referee as: python -m agents.referee"""
import asyncio
from agents.referee.main import main

if __name__ == "__main__":
    asyncio.run(main())
