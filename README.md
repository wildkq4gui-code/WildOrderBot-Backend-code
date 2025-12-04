# 6h-sf16-bot
6h long bot program for lichess

## Deployment / Workflow

The repository includes a GitHub Actions workflow that runs the scheduled bot daily at 13:00 UTC (07:00 CST when CST = UTC−6):

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
- GitHub Actions cron uses UTC. If your local timezone observes DST and you want a fixed local 07:00, let me know and I can add DST-aware scheduling options.
- The bot will run for ~6 hours from startup (wind-down at 5.5h, full shutdown at 6h).
