"""Allow running as python -m agent."""
from agent.main import main
import sys

if __name__ == "__main__":
    sys.exit(main())
