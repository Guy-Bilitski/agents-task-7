"""Sample strategy plugin.

This plugin demonstrates how to create a custom parity strategy
that can be loaded at runtime.
"""

from .strategy import MomentumStrategy

# Export the strategy class for the plugin loader
STRATEGY_CLASS = MomentumStrategy
