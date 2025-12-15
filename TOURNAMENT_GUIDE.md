# Chess Engine Tournament System - User Guide

Complete guide for running tournaments between chess engine versions.

---

## Overview

The tournament system allows you to test and compare different engine versions by running multiple games and collecting statistics. Two interfaces are available:

1. **CLI Tournament** (`tournament.py`) - Fast, headless execution with progress tracking
2. **GUI Tournament** (`tournament_gui.py`) - Visual interface with live board display

---

## CLI Tournament: `tournament.py`

### Basic Usage

```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4
```

### All Arguments

| Argument | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `--engine1` | string | - | **Yes** | First engine module name (e.g., `engine_v3`) |
| `--engine2` | string | - | **Yes** | Second engine module name (e.g., `engine_v4`) |
| `--games` | int | `100` | No | Number of games to play in the match |
| `--depth1` | int | `5` | No | Search depth for engine 1 |
| `--depth2` | int | `5` | No | Search depth for engine 2 |
| `--time` | float | `None` | No | Time limit per move in seconds (if set, overrides depth) |
| `--output-dir` | string | `"games"` | No | Directory where game PGN files will be saved |
| `--quiet` | flag | `False` | No | Minimize output (show only final results) |
| `--quick` | flag | `False` | No | Quick test mode (automatically sets games to 10) |

### Examples

#### Basic 100-game match
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4
```
- Default: 100 games, depth 5 vs 5, no time limit

#### Quick 10-game test
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --quick
```
- Runs 10 games instead of 100
- Good for rapid testing of changes

#### Custom configuration
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --games 200 \
    --depth1 6 \
    --depth2 5 \
    --time 2.0
```
- 200 games
- Engine 1 at depth 6, Engine 2 at depth 5
- 2 seconds per move time limit

#### Fast test with depth 3
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --games 50 \
    --depth1 3 \
    --depth2 3 \
    --time 0.1
```
- 50 games at shallow depth
- Very fast for initial testing

#### Quiet mode (minimal output)
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --quiet
```
- Suppresses progress updates
- Shows only final statistics

#### Custom output directory
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --output-dir my_tests
```
- Saves games to `my_tests/` directory instead of `games/`

### Output

The CLI tournament will:
1. Display real-time progress with a progress bar
2. Show current game number and live score (W-D-L)
3. Display estimated time remaining
4. Save each game as a PGN file
5. Print comprehensive statistics at the end
6. Save a JSON summary of the match

**Games are saved to:**
```
games/
└── engine1_vs_engine2/
    └── match_YYYY-MM-DD_HHMMSS/
        ├── game_001.pgn
        ├── game_002.pgn
        ├── ...
        └── match_summary.json
```

---

## GUI Tournament: `tournament_gui.py`

### Basic Usage

```bash
python tournament_gui.py
```

### All Arguments

| Argument | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `--engine1` | string | `"engine_v3"` | No | First engine module name |
| `--engine2` | string | `"engine_v4"` | No | Second engine module name |
| `--games` | int | `10` | No | Number of games to play |
| `--depth1` | int | `5` | No | Search depth for engine 1 |
| `--depth2` | int | `5` | No | Search depth for engine 2 |
| `--time` | float | `None` | No | Time limit per move in seconds |

### Examples

#### Default configuration
```bash
python tournament_gui.py
```
- engine_v3 vs engine_v4
- 10 games
- Depth 5 vs 5

#### Custom engines and game count
```bash
python tournament_gui.py --engine1 engine_v3 --engine2 engine_v4 --games 20
```
- 20 games between v3 and v4

#### Quick test with shallow depth
```bash
python tournament_gui.py --games 5 --depth1 3 --depth2 3
```
- 5 games at depth 3 (very fast)

#### Time-controlled match
```bash
python tournament_gui.py --time 2.0 --games 10
```
- 10 games with 2 seconds per move

#### Different depths for testing
```bash
python tournament_gui.py --depth1 6 --depth2 5 --games 10
```
- Test engine 1 at depth 6 vs engine 2 at depth 5

### GUI Controls

#### Mouse Controls
- **Start Button** - Begin the tournament
- **Pause Button** - Pause/Resume the tournament
- **Stop Button** - Stop the tournament completely
- **Speed Buttons** - Adjust playback speed (1x, 10x, 50x, 100x)

#### Keyboard Shortcuts
- **SPACE** - Start tournament / Pause-Resume
- **S** - Stop tournament
- **Q** - Quit the application
- **1** - Set speed to 1x (normal)
- **2** - Set speed to 10x (fast)
- **3** - Set speed to 50x (very fast)
- **4** - Set speed to 100x (maximum speed)

### Speed Modes

| Speed | Description | Best For |
|-------|-------------|----------|
| **1x** | Normal speed, see every move | Analyzing individual games |
| **10x** | Fast, updates every 10 moves | Watching games progress |
| **50x** | Very fast, position updates only | Quick completion |
| **100x** | Maximum speed, stats only | Running through many games |

### GUI Display

The GUI shows:
- **Live chess board** with current position
- **Match configuration** (engines, depth, time control)
- **Current game number** (e.g., "Game 5/10")
- **Live score** (Wins-Draws-Losses for each engine)
- **Last move information** (move, time, nodes searched)
- **Status** (Running, Paused, Ready)
- **Speed indicator** (current playback speed)

---

## Viewing Results

After a tournament completes, view the results:

```bash
python results_viewer.py games/engine_v3_vs_engine_v4/match_YYYY-MM-DD_HHMMSS/
```

### Results Viewer Arguments

```bash
# View results
python results_viewer.py path/to/match/

# Export to JSON
python results_viewer.py path/to/match/ --json

# Export to CSV
python results_viewer.py path/to/match/ --csv

# Export both
python results_viewer.py path/to/match/ --export-all
```

### What Results Show

- **Overall score** (W-D-L for each engine)
- **Score by color** (as White and as Black)
- **Game statistics** (avg length, longest, shortest)
- **Performance metrics** (time/move, nodes/move, NPS)
- **Elo estimate** (approximate strength difference)

---

## Recommended Testing Workflow

### Step 1: Quick Test (10 games)
```bash
python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4 \
    --depth1 3 --depth2 3 --time 0.1
```
**Time:** ~1 minute
**Purpose:** Fast validation of changes

### Step 2: Standard Test (100 games)
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --games 100 --depth1 3 --depth2 3 --time 0.1
```
**Time:** ~10-15 minutes
**Purpose:** Statistical validation

### Step 3: Deep Validation (200 games)
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --games 200 --depth1 5 --depth2 5 --time 0.5
```
**Time:** ~2-3 hours
**Purpose:** Final validation before production

---

## Success Criteria

An engine improvement is considered successful if:
- **Win rate > 55%** over 100+ games
- **Win rate > 60%** is excellent
- No significant performance regression (time/nodes similar)
- Passes visual inspection (no obvious blunders)

### Elo Estimates from Win Rate

| Win Rate | Elo Difference |
|----------|----------------|
| 55% | +35 Elo |
| 60% | +70 Elo |
| 65% | +110 Elo |
| 70% | +150 Elo |
| 75% | +200 Elo |

---

## Tips & Best Practices

### Performance
- **Fast testing:** Use `--depth1 3 --depth2 3 --time 0.1` for rapid iteration
- **Accurate testing:** Use `--depth1 5 --depth2 5 --time 0.5` for realistic results
- **GUI performance:** Higher speeds (50x, 100x) reduce rendering overhead

### Testing Strategy
1. **Always test one change at a time** - Makes it clear what works
2. **Start with quick tests** - 10 games catches obvious regressions
3. **Full validation before commit** - 100+ games for statistical confidence
4. **Use consistent settings** - Same depth/time for fair comparison

### GUI vs CLI
- **Use GUI** when you want to watch games and see what's happening
- **Use CLI** for batch testing, automation, and maximum speed
- **CLI is faster** when running many games (less rendering overhead)

### Debugging
If a tournament fails:
```bash
# Test engine loads
python -c "import engine_v4; print('OK')"

# Run single game manually
python main.py

# Check saved games
ls games/engine_v3_vs_engine_v4/
```

---

## Output Files

### PGN Files
Each game is saved with:
- Standard PGN headers (Event, Date, Players, Result)
- Time control information
- Performance statistics (avg nodes, avg time)
- Complete move notation
- Termination reason

### Match Summary JSON
Contains:
- Match configuration
- All game results
- Win/Draw/Loss statistics
- Performance averages
- Timestamps

**Example:**
```json
{
  "engine1": "engine_v3",
  "engine2": "engine_v4",
  "games_played": 100,
  "engine1_wins": 42,
  "engine1_draws": 18,
  "engine1_losses": 40,
  "avg_game_length": 38.5,
  "start_time": "2025-12-15T14:30:00",
  "end_time": "2025-12-15T15:45:00"
}
```

---

## Troubleshooting

### "Module not found" error
- Make sure engine files exist (e.g., `engine_v3.py`, `engine_v4.py`)
- Check spelling of module names (no `.py` extension needed)

### GUI pieces not visible
- The GUI now uses Segoe UI Symbol font (Windows)
- Should work automatically on Windows 10/11
- If issues persist, pieces render with thick outlines for visibility

### Tournament takes too long
- Reduce depth: `--depth1 3 --depth2 3`
- Reduce games: `--games 10` or `--quick`
- Add time limit: `--time 0.1` (very fast)
- Use CLI instead of GUI (faster)

### Out of memory
- Reduce number of parallel processes (if using parallel mode)
- Close other applications
- Reduce game count

---

## Advanced Usage

### Testing Multiple Depths
```bash
# Test if deeper search helps
python tournament.py --engine1 engine_v3 --engine2 engine_v3 \
    --depth1 5 --depth2 6 --games 50
```

### Same Engine Different Times
```bash
# Does more time help?
python tournament_gui.py --engine1 engine_v3 --engine2 engine_v3 \
    --depth1 5 --depth2 5 --time 1.0
```

### Batch Testing
```bash
# Test v4 against v3 at multiple depths
for depth in 3 4 5 6; do
    python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
        --depth1 $depth --depth2 $depth --games 50 --quiet
done
```

---

## Quick Reference

### Most Common Commands

```bash
# Quick 10-game test
python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4

# Standard 100-game test
python tournament.py --engine1 engine_v3 --engine2 engine_v4

# Visual tournament with GUI
python tournament_gui.py --games 10

# View results
python results_viewer.py games/engine_v3_vs_engine_v4/match_*/

# Export results
python results_viewer.py games/engine_v3_vs_engine_v4/match_*/ --export-all
```

---

## Related Files

- **IMPLEMENTATION_ROADMAP.md** - Future improvements and features
- **ENGINE_IMPROVEMENTS.md** - Log of engine changes and results
- **README.md** - Project overview

---

**Last Updated:** 2025-12-15
**Status:** Production Ready
**Version:** 1.0
