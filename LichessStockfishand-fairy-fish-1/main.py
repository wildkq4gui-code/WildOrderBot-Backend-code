#!/usr/bin/env python3
"""
Lichess Bot - Simple CLI Runner
Runs Stockfish at 100ms per move with depth 30
Scheduled to run for 6 hours with wind-down at 5.5 hours
"""

import os
import sys
from lichess_bot import LichessBot


def main():
    print("=" * 60)
    print("Lichess Bot - Stockfish 16 Test Runner")
    print("Settings: 100ms per move, Depth 30")
    print("=" * 60)
    
    token = os.environ.get('LICHESS_TOKEN')
    if not token:
        print("\nERROR: LICHESS_TOKEN not found in environment")
        print("Please set your Lichess API token as LICHESS_TOKEN")
        sys.exit(1)
    
    print("\nInitializing bot...")
    bot = LichessBot(token)
    
    bot.manual_mode = True
    bot.manual_time_limit = 0.1
    bot.manual_depth = 35
    # Force using Stockfish (not Fairy Stockfish) for CLI runs
    bot.use_fairy_stockfish = False
    
    bot.winddown_hours = 5.5
    bot.max_runtime_hours = 6.0
    
    bot.winding_down = True
    bot.final_game_played = False
    print("\n*** WIND-DOWN MODE ACTIVE ***")
    print("Bot will finish current game and not accept new challenges.")
    
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
    
    print("\n" + "=" * 60)
    print("Starting bot... (Press Ctrl+C to stop)")
    print("=" * 60 + "\n")
    
    try:
        bot.run(auto_challenge_bots=False)
    except KeyboardInterrupt:
        print("\n\nStopping bot...")
        bot.stop()
        print("Bot stopped.")


if __name__ == '__main__':
    main()
