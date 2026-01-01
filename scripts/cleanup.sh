#!/bin/bash
# Cleanup script to kill all running league components

echo "Stopping all league components..."

# Kill League Manager on port 9000
if lsof -ti:9000 >/dev/null 2>&1; then
    echo "  Stopping League Manager (port 9000)..."
    kill $(lsof -ti:9000) 2>/dev/null
fi

# Kill player agents on ports 8001-8110
for port in {8001..8110}; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  Stopping agent on port $port..."
        kill $(lsof -ti:$port) 2>/dev/null
    fi
done

sleep 1

# Force kill if still running
for port in 9000 {8001..8110}; do
    if lsof -ti:$port >/dev/null 2>&1; then
        echo "  Force stopping port $port..."
        kill -9 $(lsof -ti:$port) 2>/dev/null
    fi
done

echo "✓ Cleanup complete!"
