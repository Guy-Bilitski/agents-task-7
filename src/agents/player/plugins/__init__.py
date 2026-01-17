"""Strategy plugins directory.

This package contains external strategy implementations that are loaded
at runtime by the plugin loader.

To create a new plugin:
1. Create a new directory under plugins/
2. Add a strategy.py file with a ParityStrategy subclass
3. Export the class via STRATEGY_CLASS or let the loader auto-discover it

Example:
    plugins/
    └── my_strategy/
        ├── __init__.py  (optional)
        └── strategy.py  (required)

See sample_strategy/ for a complete example.
"""
