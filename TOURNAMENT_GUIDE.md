# Chess Engine Tournament System - Complete Guide

Guide for running tournaments, viewing results, and analyzing games.

---

## Overview

The tournament system provides three ways to test and compare chess engines:

1. **GUI Tournament with Config** (`tournament_gui_config.py`) - **Recommended** - Interactive setup + visual playback
2. **CLI Tournament** (`tournament.py`) - Fast, headless execution for batch testing
3. **Legacy GUI Tournament** (`tournament_gui.py`) - Visual interface with command-line config

Plus analysis tools:
- **Results Viewer** (`results_viewer.py`) - Analyze completed tournaments
- **PGN Viewer** (`pgn_viewer.py`) - Replay and explore individual games

---

## 1. GUI Tournament with Configuration (Recommended)

**File:** `tournament_gui_config.py`

### Features
- **Interactive configuration screen** - Set all parameters before starting
- **Live board visualization** - Watch games as they play
- **Real-time statistics** - See scores and progress
- **Speed controls** - 1x, 10x, 50x, 100x playback
- **Pause/Resume/Stop** - Full control during execution

### Usage

```bash
python tournament_gui_config.py
```

### Configuration Options

**On the config screen, you can select:**

#### Engine Selection
- Choose Engine 1 from available engines
- Choose Engine 2 from available engines
- Automatically detects all `engine*.py` files

#### Search Depth
- Depth 3, 4, 5, 6, or 7 for each engine
- Higher depth = stronger play but slower

#### Number of Games
- 10, 20, 50, or 100 games
- Alternates colors each game

#### Time Control
- **Depth-based** (no time limit)
- **0.1s** per move (very fast)
- **1s** per move (fast)
- **2s** per move (normal)
- **5s** per move (strong)
- **10s** per move (very strong)

#### Output Directory
- `games` (default)
- `results`
- `matches`
- `tournaments`

### During Tournament

**Buttons:**
- **Start** - Begin the tournament
- **Pause** - Pause/Resume
- **Stop** - End tournament early
- **1x/10x/50x/100x** - Speed controls

**Keyboard Shortcuts:**
- **SPACE** - Start/Pause
- **S** - Stop
- **Q** - Quit
- **1/2/3/4** - Speed selection

**Display Shows:**
- Live chess board with current position
- Current game number (e.g., "Game 5/10")
- Real-time score (W-D-L for each engine)
- Last move details (move, time, nodes)
- Match configuration
- Status (Running/Paused/Ready)

---

## 2. CLI Tournament

**File:** `tournament.py`

### Features
- **Fast execution** - No GUI overhead
- **Progress tracking** - Real-time updates and ETA
- **Quiet mode** - For automation
- **Comprehensive stats** - Detailed results at end

### Basic Usage

```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4
```

### All Arguments

| Argument | Type | Default | Required | Description |
|----------|------|---------|----------|-------------|
| `--engine1` | string | - | **Yes** | First engine module (e.g., `engine_v3`) |
| `--engine2` | string | - | **Yes** | Second engine module (e.g., `engine_v4`) |
| `--games` | int | `100` | No | Number of games |
| `--depth1` | int | `5` | No | Search depth for engine 1 |
| `--depth2` | int | `5` | No | Search depth for engine 2 |
| `--time` | float | `None` | No | Time limit per move (seconds) |
| `--output-dir` | string | `"games"` | No | Output directory |
| `--quiet` | flag | `False` | No | Minimal output |
| `--quick` | flag | `False` | No | Quick test (10 games) |

### Examples

```bash
# Quick 10-game test
python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4

# Standard 100-game match
python tournament.py --engine1 engine_v3 --engine2 engine_v4

# Custom configuration
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --games 200 --depth1 6 --depth2 5 --time 2.0

# Fast testing
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --games 50 --depth1 3 --depth2 3 --time 0.1

# Quiet mode
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --quiet
```

### Output

Displays:
- Progress bar with game count
- Current score (W-D-L)
- ETA and elapsed time
- Comprehensive final statistics

Saves:
- PGN files for each game
- JSON match summary
- Performance metrics

---

## 3. Results Viewer

**File:** `results_viewer.py`

### Features
- Analyze completed tournament results
- Detailed statistics and performance metrics
- Elo difference estimates
- Export to JSON/CSV

### Usage

```bash
python results_viewer.py games/engine_v3_vs_engine_v4/match_2025-12-15_214657/
```

### What It Shows

**Match Overview:**
- Engines tested
- Total games played
- Match directory

**Overall Results:**
- Wins-Draws-Losses for each engine
- Total score
- Win percentage

**Detailed Breakdown:**
- Performance as White
- Performance as Black
- Win rates by color

**Game Statistics:**
- Average game length
- Longest/shortest games
- Decisive game percentage
- Draw percentage

**Performance Metrics:**
- Average time per move
- Average nodes searched per move
- Nodes per second (NPS)

**Elo Estimate:**
- Estimated Elo difference
- Interpretation of strength difference

### Export Options

```bash
# Export to JSON
python results_viewer.py path/to/match/ --json

# Export to CSV
python results_viewer.py path/to/match/ --csv

# Export both
python results_viewer.py path/to/match/ --export-all
```

---

## 4. PGN Viewer

**File:** `pgn_viewer.py`

### Features
- Load and explore chess games from PGN files
- Navigate through moves step by step
- Display game information
- Keyboard shortcuts for quick navigation

### Usage

```bash
python pgn_viewer.py
```

### File Selection Screen

**Options:**
- **Browse PGN File** - Select any PGN file from your computer
- **Recent Games** - Automatically loads the most recent tournament game

### Game Viewer

**Display:**
- Chess board with current position
- Game information (players, event, date, result)
- Current move number
- Large display of current move in algebraic notation
- Scrolling move list with current position highlighted

**Navigation Buttons:**
- **|<** - Go to start
- **<** - Previous move
- **>** - Next move
- **>|** - Go to end
- **Back to File Selection** - Load another game

**Keyboard Shortcuts:**
- **Left Arrow** - Previous move
- **Right Arrow** - Next move
- **Home** - Go to start of game
- **End** - Go to end of game
- **Q** - Quit application

### Typical Workflow

1. Run `python pgn_viewer.py`
2. Click "Recent Games" to load latest tournament game
3. Use arrow keys to navigate through moves
4. Observe position and move list
5. Press Q to quit or load another game

---

## Recommended Testing Workflow

### Step 1: Quick Test (10 games, ~1 minute)
```bash
python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4 \
    --depth1 3 --depth2 3 --time 0.1
```
**Purpose:** Fast validation of changes

### Step 2: Standard Test (100 games, ~10-15 minutes)
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --games 100 --depth1 3 --depth2 3 --time 0.1
```
**Purpose:** Statistical validation

### Step 3: View Results
```bash
python results_viewer.py games/engine_v3_vs_engine_v4/match_*/
```
**Purpose:** Analyze performance

### Step 4: Review Games
```bash
python pgn_viewer.py
```
Click "Recent Games" to explore individual games
**Purpose:** Understand what happened

### Step 5: Deep Validation (if needed, 200 games, ~2-3 hours)
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 \
    --games 200 --depth1 5 --depth2 5 --time 0.5
```
**Purpose:** Final confirmation before production

---

## Success Criteria

An engine improvement is successful if:
- **Win rate > 55%** over 100+ games (minimum)
- **Win rate > 60%** is strong
- **Win rate 70%+** is excellent ✅ (v4.0 achieved this!)
- No significant performance regression
- Passes visual inspection (no obvious blunders)

### Elo Estimates from Win Rate

| Win Rate | Elo Difference | Quality |
|----------|----------------|---------|
| 50% | +0 Elo | No improvement |
| 55% | +35 Elo | Modest improvement |
| 60% | +70 Elo | Good improvement |
| 65% | +110 Elo | Strong improvement |
| 70% | +150 Elo | Excellent improvement ⭐ |
| 75% | +200 Elo | Outstanding improvement |

---

## Output Files

### Directory Structure
```
games/
└── engine_v3_vs_engine_v4/
    └── match_2025-12-15_214657/
        ├── game_001.pgn
        ├── game_002.pgn
        ├── ...
        ├── game_100.pgn
        └── match_summary.json
```

### PGN Files
Each game includes:
- Standard PGN headers (Event, Date, White, Black, Result)
- Engine depths and time control
- Performance stats (avg time/move, avg nodes/move)
- Complete move notation
- Termination reason

### Match Summary JSON
Contains:
- Match configuration
- All game results
- Win/Draw/Loss statistics
- Performance averages
- Timestamps

---

## Tips & Best Practices

### Performance
- **Fast testing:** Use `--depth1 3 --depth2 3 --time 0.1`
- **Accurate testing:** Use `--depth1 5 --depth2 5 --time 0.5`
- **GUI performance:** Higher speeds (50x, 100x) reduce overhead

### Testing Strategy
1. **Test one change at a time** - Clear cause and effect
2. **Start with quick tests** - Catch obvious regressions
3. **Full validation before commit** - Statistical confidence
4. **Use consistent settings** - Fair comparison

### GUI vs CLI
- **Use GUI** when watching games and understanding play
- **Use CLI** for batch testing and maximum speed
- **CLI is faster** with less rendering overhead

### Debugging
If tournament fails:
```bash
# Test engine loads correctly
python -c "import engine_v4; e = engine_v4.ChessEngine(); print('OK')"

# Run single game
python main.py

# Check saved games
ls -ltr games/engine_v3_vs_engine_v4/
```

---

## Troubleshooting

### "Module not found" error
- Ensure engine files exist (e.g., `engine_v3.py`)
- Check spelling (no `.py` extension in arguments)

### GUI pieces not rendering
- Uses Segoe UI Symbol (Windows) or system fonts
- Piece rendering with outlines for visibility
- Should work on Windows 10/11 automatically

### Tournament takes too long
- Reduce depth: `--depth1 3 --depth2 3`
- Reduce games: `--games 10` or `--quick`
- Add time limit: `--time 0.1`
- Use CLI instead of GUI

### Out of memory
- Close other applications
- Reduce game count
- Clear old tournament results

---

## Quick Reference

### Common Commands

```bash
# Quick test (GUI with config)
python tournament_gui_config.py

# Quick test (CLI)
python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4

# Standard test (CLI)
python tournament.py --engine1 engine_v3 --engine2 engine_v4

# View results
python results_viewer.py games/engine_v3_vs_engine_v4/match_*/

# Review games
python pgn_viewer.py

# Export results
python results_viewer.py games/engine_v3_vs_engine_v4/match_*/ --export-all
```

---

## Related Documentation

- **ENGINE_IMPROVEMENTS.md** - Log of engine development and testing results
- **IMPLEMENTATION_ROADMAP.md** - Future improvements and development plans
- **README.md** - Project overview and features

---

**Last Updated:** 2025-12-15
**Status:** Production Ready
**Version:** 2.0 (Added GUI config and PGN viewer)
