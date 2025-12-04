#!/usr/bin/env python3
"""
Lichess Bot - Scheduled Runner for GitHub Actions
Runs from 7am CST to 3pm CST (8 hour window)
- Normal operation for first 5.5 hours
- Wind-down at 5.5 hours (plays one last game)
- Shutdown at 6 hours
"""

import os
import sys
from lichess_bot import LichessBot


def main():
    print("=" * 60)
    print("Lichess Bot - GitHub Actions Scheduled Run")
    print("Settings: 100ms per move, Depth 30")
    print("Schedule: 5.5h wind-down, 6h shutdown")
    print("=" * 60)
    
    token = os.environ.get('LICHESS_TOKEN')
    if not token:
        print("\nERROR: LICHESS_TOKEN not found in environment")
        print("Please set LICHESS_TOKEN in GitHub repository secrets")
        sys.exit(1)
    
    print("\nInitializing bot...")
    bot = LichessBot(token)
    
    bot.manual_mode = True
    bot.manual_time_limit = 0.1
    bot.manual_depth = 35
    # Force using Stockfish (not Fairy Stockfish) for scheduled runs
    bot.use_fairy_stockfish = False
    
    bot.winddown_hours = 5.5
    bot.max_runtime_hours = 6.0
    
    if bot.engine:
        bot.engine.configure({
            "Threads": min(8, os.cpu_count() or 4),
            "Hash": 2048,
            "Move Overhead": 50
        })
    
    print(f"\nManual mode enabled:")
    print(f"  - Time limit: {bot.manual_time_limit * 1000:.0f}ms per move")
    print(f"  - Search depth: {bot.manual_depth}")
    print(f"  - Threads: {min(8, os.cpu_count() or 4)}")
    print(f"  - Hash: 2048 MB")
    print(f"\nSchedule:")
    print(f"  - Wind-down after: {bot.winddown_hours} hours")
    print(f"  - Shutdown after: {bot.max_runtime_hours} hours")
    
    print("\n" + "=" * 60)
    print("Starting bot...")
    print("=" * 60 + "\n")
    
    try:
        bot.run(auto_challenge_bots=True)
    except KeyboardInterrupt:
        print("\n\nStopping bot...")
        bot.stop()
    except Exception as e:
        print(f"\nError: {e}")
        bot.cleanup()
        sys.exit(1)
    
    print("\nBot session completed successfully.")


if __name__ == '__main__':
    main()
