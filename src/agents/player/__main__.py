"""Allow running as python -m agents.player."""
from agents.player.main import main
import sys

if __name__ == "__main__":
    sys.exit(main())
