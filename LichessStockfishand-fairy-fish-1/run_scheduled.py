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
from datetime import datetime, timedelta
try:
    # Python 3.9+ zoneinfo
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


def main():
    # Load local .env file if present (convenience for local runs).
    # This allows you to create a `.env` file with `LICHESS_TOKEN=...` for local testing.
    def load_dotenv(path='.env'):
        try:
            if not os.path.exists(path):
                return
            with open(path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith('#'):
                        continue
                    if '=' not in line:
                        continue
                    key, val = line.split('=', 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    # Only set if not already present in environment
                    if key and key not in os.environ:
                        os.environ[key] = val
        except Exception:
            pass

    load_dotenv()

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
    # Resolve engine binary path relative to this script so the runner can find it
    script_dir = os.path.dirname(os.path.abspath(__file__))
    default_engine_rel = os.path.join(script_dir, "stockfish/stockfish-ubuntu-x86-64-avx2")
    fairy_engine_rel = os.path.join(script_dir, "stockfish/fairy-stockfish")

    # Allow overriding engine path via environment variable (useful for Stockfish 16.1)
    env_engine = os.environ.get('STOCKFISH_PATH')
    engine_path_to_use = None
    if env_engine and os.path.exists(env_engine):
        engine_path_to_use = env_engine
    else:
        # Prefer Stockfish 17 binaries first, then 16.1, then bundled fallbacks
        candidate_names = [
            os.path.join(script_dir, 'stockfish', 'stockfish-17'),
            os.path.join(script_dir, 'stockfish', 'stockfish-17-ubuntu-x86-64'),
            os.path.join(script_dir, 'stockfish', 'stockfish-17-ubuntu-x86-64-avx2'),
            os.path.join(script_dir, 'stockfish', 'stockfish-16.1'),
            os.path.join(script_dir, 'stockfish', 'stockfish-16.1-ubuntu-x86-64'),
            default_engine_rel,
            fairy_engine_rel,
        ]
        for cand in candidate_names:
            if cand and os.path.exists(cand):
                engine_path_to_use = cand
                break

    if engine_path_to_use:
        print(f"Using engine binary at: {engine_path_to_use}")
        bot = LichessBot(token, stockfish_path=engine_path_to_use)
    else:
        print("Warning: No local engine binary found at expected paths. Falling back to default path.")
        bot = LichessBot(token)
    
    bot.manual_mode = True
    bot.manual_time_limit = 0.1
    bot.manual_depth = 35
    # Force using Stockfish (not Fairy Stockfish) for scheduled runs
    bot.use_fairy_stockfish = False
    
    # Compute wall-clock schedule in America/Chicago timezone.
    # Start is expected to be 05:45 America/Chicago when this script is launched by the workflow.
    # Wind-down: 30 minutes before shutdown. Shutdown: 23:30 America/Chicago.
    try:
        if ZoneInfo is None:
            raise RuntimeError("zoneinfo not available")

        tz = ZoneInfo("America/Chicago")
        now_local = datetime.now(tz)
        # Target shutdown today at 23:30 local
        shutdown_local = now_local.replace(hour=23, minute=30, second=0, microsecond=0)
        if now_local >= shutdown_local:
            # If it's already past shutdown, schedule to next day
            shutdown_local = shutdown_local + timedelta(days=1)

        runtime_seconds = (shutdown_local - now_local).total_seconds()
        runtime_hours = max(0.0, runtime_seconds / 3600.0)

        # Wind-down 30 minutes before shutdown
        winddown_seconds = max(0.0, runtime_seconds - 30 * 60)
        winddown_hours = winddown_seconds / 3600.0

        bot.winddown_hours = winddown_hours
        bot.max_runtime_hours = runtime_hours

        print(f"Current local time (America/Chicago): {now_local.isoformat()}")
        print(f"Scheduled shutdown local time: {shutdown_local.isoformat()}")
        print(f"Scheduled runtime: {runtime_hours:.2f} hours (wind-down at {winddown_hours:.2f} hours)")
    except Exception as e:
        # Fall back to fixed 6-hour window if zoneinfo isn't available
        print(f"Warning: failed to compute wall-clock schedule: {e}. Using default 6-hour runtime.")
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
