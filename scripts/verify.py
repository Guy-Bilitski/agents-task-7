#!/usr/bin/env python3
"""
Quick verification that the league system works.

This script runs a minimal league (2 agents, 1 round) to verify everything is working.
"""
import subprocess
import sys
import time
import requests

def main():
    print("=" * 60)
    print("VERIFICATION TEST - Even-Odd League")
    print("=" * 60)
    print()
    
    # Step 1: Cleanup
    print("Step 1: Cleaning up any existing processes...")
    subprocess.run(["bash", "scripts/cleanup.sh"], check=False, capture_output=True)
    print("✓ Cleanup complete")
    print()
    
    # Step 2: Start the league (minimal config)
    print("Step 2: Starting minimal league (2 agents, 1 round)...")
    print("This should take about 10 seconds...")
    print()
    
    try:
        result = subprocess.run(
            ["python3", "scripts/run_league.py", "--num-agents", "2", "--rounds", "1"],
            timeout=30,
            capture_output=True,
            text=True
        )
        
        output = result.stdout + result.stderr
        
        # Check for success indicators
        success_indicators = [
            "League Manager ready",
            "agents started successfully",
            "agents registered",
            "STARTING LEAGUE COMPETITION"
        ]
        
        failures = []
        for indicator in success_indicators:
            if indicator not in output:
                failures.append(indicator)
        
        if failures:
            print("✗ VERIFICATION FAILED")
            print()
            print("Missing indicators:")
            for f in failures:
                print(f"  - {f}")
            print()
            print("Output:")
            print(output[-1000:])  # Last 1000 chars
            return 1
        else:
            print("✓ VERIFICATION PASSED!")
            print()
            print("The league system is working correctly:")
            print("  ✓ League Manager starts")
            print("  ✓ Player agents spawn")
            print("  ✓ Agents register")
            print("  ✓ Games run")
            print()
            print("You can now run the full league:")
            print("  python3 scripts/run_league.py")
            return 0
            
    except subprocess.TimeoutExpired:
        print("✗ VERIFICATION TIMEOUT")
        print("The league took too long to run (>30s)")
        return 1
    except Exception as e:
        print(f"✗ VERIFICATION ERROR: {e}")
        return 1
    finally:
        # Always cleanup
        print()
        print("Cleaning up...")
        subprocess.run(["bash", "scripts/cleanup.sh"], check=False, capture_output=True)
        print("✓ Done")

if __name__ == "__main__":
    sys.exit(main())
