# 6h-sf16-bot
6h long bot program for lichess

## Deployment / Workflow

The repository includes a GitHub Actions workflow that starts the scheduled bot daily at 12:00 UTC (06:00 America/Chicago local time):

- Workflow file: `.github/workflows/lichess-bot.yml`
- It expects a repository secret named `LICHESS_TOKEN` (your Lichess bot API token).

Quick checks and manual trigger

1. In GitHub, go to `Actions` → `Lichess Bot Scheduled Run` → `Run workflow` to trigger immediately.
2. In the run logs check for these steps:
	- Checkout repository
	- Set up Python
	- `chmod +x` step for the engine binary (ensures the stockfish binary is executable)
	- `run_scheduled.py` startup lines (should show connected username and engine id)

Local test

```bash
export LICHESS_TOKEN="your_token_here"
chmod +x LichessStockfishand-fairy-fish-1/stockfish/stockfish-ubuntu-x86-64-avx2
python3 LichessStockfishand-fairy-fish-1/run_scheduled.py
```

Notes
- GitHub Actions cron uses UTC. The workflow is configured to start at 12:00 UTC which corresponds to 06:00 America/Chicago (CST/CDT transition is handled by the timezone conversion here in the code).
- The bot calculates the runtime until 11:05 America/Chicago on the same day and will begin wind-down at 11:00 (finishing any current game). If zoneinfo is unavailable, it falls back to a default behavior.

Using Stockfish 17.1
- To run the bot with Stockfish 17, place the Stockfish 17 binary into `LichessStockfishand-fairy-fish-1/stockfish/` and name it one of the following (preferred order):
	- `stockfish-17`
	- `stockfish-17-ubuntu-x86-64`
	- `stockfish-17-ubuntu-x86-64-avx2`

- If you don't want to place the binary in the repo, set a custom path via environment variable `STOCKFISH_PATH` (or add it to your local `.env`):

```bash
export STOCKFISH_PATH="/path/to/your/stockfish-17.1"
```

The runner prefers `STOCKFISH_PATH` if set and the file exists. If no custom path or Stockfish 17 binary is found, the script will fall back to Stockfish 16.1 (if present) and then to bundled binaries.
