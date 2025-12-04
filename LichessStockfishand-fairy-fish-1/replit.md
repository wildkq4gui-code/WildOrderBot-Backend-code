# Lichess Chess Bot with Stockfish 16 - Test Copy

## Overview
A test copy of the Lichess chess bot configured to run Stockfish at 100ms per move with depth 30. This is a simplified command-line version without the web frontend, designed for scheduled runs on GitHub Actions.

## Current State
- **Bot Account**: WildorderBot (connected)
- **Engine**: Stockfish (configured for 100ms per move, depth 30)
- **Mode**: Manual speed control enabled
- **Status**: Console-only (no web interface), Wind-down mode active

## Configuration
- **Time per move**: 100 milliseconds
- **Search depth**: 30
- **Threads**: 8 (or max available)
- **Hash**: 2048 MB
- **Move overhead**: 50ms

## Scheduling
- **Wind-down time**: 5.5 hours (stops accepting new challenges)
- **Shutdown time**: 6 hours (forces shutdown)
- **GitHub Actions**: Runs daily at 7am CST (13:00 UTC)

## Project Architecture

### Main Components
- `main.py`: CLI script that runs the bot in wind-down mode (finish current game only)
- `run_scheduled.py`: Script for GitHub Actions with full scheduling (5.5h wind-down, 6h shutdown)
- `lichess_bot.py`: Main bot script with Lichess API integration and scheduling logic
- `.github/workflows/lichess-bot.yml`: GitHub Actions workflow for scheduled runs
- `stockfish/`: Stockfish binary directory
- `opening_book.py`: Opening book for standard chess
- `middlegame_book.py`: Middlegame patterns
- `endgame_book.py`: Endgame book
- `variant_opening_books.py`: Opening books for variants

### Dependencies
- `berserk`: Official Lichess API Python client
- `python-chess`: Chess library with UCI engine support
- `stockfish`: Binary (x86_64 AVX2)

## Environment Variables
- `LICHESS_TOKEN`: Bot account API token (required, set in Secrets or GitHub Secrets)

## Usage

### Local Testing (Wind-Down Mode)
Run `python main.py` to start the bot in wind-down mode:
- Finishes current game if any
- Declines all new challenges
- Shuts down after game completes

### GitHub Actions (Scheduled)
The bot runs automatically via GitHub Actions:
1. Starts at 7am CST daily
2. Runs normally for 5.5 hours, accepting and playing games
3. At 5.5 hours: Enters wind-down mode (no new challenges)
4. Plays one final game
5. Shuts down at 6 hour mark

To set up:
1. Add `LICHESS_TOKEN` to your GitHub repository secrets
2. Push the code to GitHub
3. The workflow runs automatically or can be triggered manually

## Recent Changes
### Dec 4, 2025 - Scheduling and GitHub Actions
- Added time-based scheduling with wind-down and shutdown logic
- Wind-down at 5.5 hours: Stops accepting new challenges
- Shutdown at 6 hours: Forces bot to stop
- Created GitHub Actions workflow for daily 7am CST runs
- Added `run_scheduled.py` for GitHub Actions
- `main.py` now runs in wind-down mode (finish current game and stop)
- Bot properly declines challenges when winding down

### Dec 4, 2025 - Simplified Test Copy
- Removed Flask web frontend
- Removed templates folder
- Created simple CLI runner (main.py)
- Fixed settings: 100ms per move, depth 30
- Bot auto-starts on program launch
