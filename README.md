# Chess Game with Advanced AI Engine

A comprehensive chess game implementation in Python featuring sophisticated AI engines, tournament systems, and multiple user interfaces for playing, testing, and analyzing chess games.

## Overview

This project provides a complete chess ecosystem where you can:
- Play against advanced AI opponents
- Run automated tournaments to test engine improvements
- Analyze games with a PGN viewer
- Watch engine battles in real-time with visual interfaces

The engine uses modern chess programming techniques including alpha-beta pruning, transposition tables, iterative deepening, and comprehensive positional evaluation.

## Features

### Chess Engines

#### Engine v4.0 (Latest - Recommended)
- **~150-200 Elo stronger than v3.0**
- Tuned piece values for better material evaluation
- All v3.0 features plus improved decision making
- 70% win rate against v3.0 in testing

#### Engine v3.0 (Baseline)
- **Advanced Search Algorithm**
  - Negamax with alpha-beta pruning
  - Iterative deepening
  - Quiescence search for tactical positions
  - Transposition table with position caching
  - Move ordering (killer moves, history heuristics)
  - Null move pruning
  - Late Move Reduction (LMR)
  - Configurable search depth and time limits

- **Comprehensive Evaluation**
  - Material evaluation with piece values
  - Piece-Square Tables (middlegame/endgame)
  - Development and castling bonuses
  - Center control evaluation
  - Piece mobility analysis
  - Pawn structure (doubled, isolated, passed)
  - King safety (pawn shield, attackers)
  - Special features (bishop pair, rooks on open files)
  - Threat detection

### Applications

#### 1. Player vs Engine (`gui.py`)
**Interactive chess game with visual interface**
- Clean, modern chess.com-style design
- Click-to-move piece selection with legal move highlighting
- Last move highlighting and check detection
- Adjustable engine difficulty (depth 3-7)
- Move history tracking
- Board flipping
- Undo and hint functions
- Threaded engine (non-blocking UI)

```bash
python gui.py
```

#### 2. Tournament System with Configuration (`tournament_gui_config.py`)
**Complete tournament GUI with pre-game setup**
- Interactive configuration screen
- Select engines, depths, time controls
- Choose number of games (10, 20, 50, 100)
- Set time limit per move (Depth-based, 0.1s, 1s, 2s, 5s, 10s)
- Choose output directory
- Live board display during matches
- Real-time statistics
- Speed controls (1x, 10x, 50x, 100x)
- Pause/Resume/Stop functionality

```bash
python tournament_gui_config.py
```

#### 3. CLI Tournament (`tournament.py`)
**Fast, headless tournament execution**
- Run batch tests without GUI overhead
- Progress tracking and ETA
- Comprehensive statistics
- Saves PGN files and JSON summaries
- Quiet mode for automation

```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --games 100
```

#### 4. Results Viewer (`results_viewer.py`)
**Analyze completed tournament results**
- Detailed match statistics
- Performance metrics (time/move, nodes/move, NPS)
- Win/Draw/Loss breakdown by color
- Elo difference estimates
- Game length analysis
- Export to JSON/CSV

```bash
python results_viewer.py games/engine_v3_vs_engine_v4/match_2025-12-15_214657/
```

#### 5. PGN Viewer (`pgn_viewer.py`)
**Load and explore saved chess games**
- Browse PGN files or load recent tournament games
- Navigate through moves with keyboard or buttons
- Display game information (players, event, result)
- Move list with current position highlighting
- Keyboard shortcuts for quick navigation

```bash
python pgn_viewer.py
```

#### 6. CLI Game (`main.py`)
**Command-line interface for playing**
- Text-based interactive gameplay
- Unicode board display
- Player vs Engine or Engine vs Engine modes
- Commands: move, undo, hint, eval, new, quit

```bash
python main.py
```

## Installation

### Requirements
- Python 3.8+
- pip package manager

### Setup

1. Clone or download the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `python-chess >= 1.999` - Chess logic and board management
- `pygame >= 2.5.0` - Graphical interfaces

## Quick Start

### Play Against the Engine
```bash
python gui.py
```
Click on pieces to move, adjust difficulty with depth buttons (3, 5, 7).

### Run a Tournament
```bash
python tournament_gui_config.py
```
Select your settings in the GUI, then watch engines battle it out!

### Explore a Saved Game
```bash
python pgn_viewer.py
```
Click "Recent Games" to load the latest tournament game, or browse for any PGN file.

## Project Structure

```
chessWithClaudeGit/
├── README.md                    # This file
├── requirements.txt             # Python dependencies
├── .gitignore                  # Git ignore rules
│
├── engine.py                   # Original engine
├── engine_v3.py                # Baseline engine (v3.0)
├── engine_v4.py                # Improved engine (v4.0) ⭐
│
├── gui.py                      # Play vs engine (GUI)
├── main.py                     # Play vs engine (CLI)
│
├── tournament.py               # CLI tournament runner
├── tournament_gui.py           # Visual tournament (old)
├── tournament_gui_config.py    # Visual tournament with config ⭐
│
├── pgn_viewer.py               # Game replay viewer ⭐
├── results_viewer.py           # Tournament analysis ⭐
│
├── board.py                    # Board wrapper
├── game_recorder.py            # PGN recording
│
├── ENGINE_IMPROVEMENTS.md      # Engine development log
├── TOURNAMENT_GUIDE.md         # Tournament system guide
└── IMPLEMENTATION_ROADMAP.md   # Future development plans
```

⭐ = New/Updated features

## Tournament System

### Quick Test Workflow

1. **Make a change** to engine_v4.py
2. **Quick test** (10 games, ~1 min):
   ```bash
   python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4 --depth1 3 --depth2 3 --time 0.1
   ```
3. **If promising** (>55% win rate), run full validation (100 games):
   ```bash
   python tournament.py --engine1 engine_v3 --engine2 engine_v4 --games 100 --depth1 3 --depth2 3 --time 0.1
   ```
4. **View results**:
   ```bash
   python results_viewer.py games/engine_v3_vs_engine_v4/match_*/
   ```

### Success Criteria
- Win rate > 55% (minimum improvement)
- Win rate > 60% (strong improvement)
- Win rate 70%+ (excellent improvement) ✅ v4.0 achieved this!

### Elo Estimates
| Win Rate | Elo Gain |
|----------|----------|
| 55% | +35 Elo |
| 60% | +70 Elo |
| 65% | +110 Elo |
| 70% | +150 Elo |
| 75% | +200 Elo |

## Engine Development

### Current Achievement
**Engine v4.0** achieved a **70% win rate** against v3.0 through piece value tuning:
- Queen: 975 → 900 centipawns
- Knight: 320 → 305 centipawns
- Result: +150-200 Elo improvement

See `ENGINE_IMPROVEMENTS.md` for detailed development log and future improvements.

### Planned Improvements
1. Move ordering (MVV-LVA) - Expected +50-100 Elo
2. Passed pawn evaluation - Expected +40-80 Elo
3. King safety improvements - Expected +30-70 Elo
4. Search extensions - Expected +100-200 Elo

See `IMPLEMENTATION_ROADMAP.md` for comprehensive development plan.

## Usage Examples

### Playing

**GUI Game:**
```bash
python gui.py
```
- Click pieces to move
- Use buttons: New Game, Flip Board, Undo, Hint
- Adjust depth for difficulty

**CLI Game:**
```bash
python main.py
```
- Enter moves in UCI format: `e2e4`, `g1f3`
- Commands: `undo`, `hint`, `eval`, `new`, `quit`

### Tournament Testing

**Interactive Tournament (Recommended):**
```bash
python tournament_gui_config.py
```
- Configure all settings in GUI
- Watch games in real-time
- Adjust speed as needed

**Fast CLI Tournament:**
```bash
# Quick 10-game test
python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4

# Full 100-game validation
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --games 100 --depth1 5 --depth2 5

# Deep test with time control
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --games 200 --depth1 5 --depth2 5 --time 0.5
```

### Analysis

**View Tournament Results:**
```bash
python results_viewer.py games/engine_v3_vs_engine_v4/match_2025-12-15_214657/
```

**Review Saved Games:**
```bash
python pgn_viewer.py
```
- Click "Recent Games" for latest tournament
- Or browse for any PGN file
- Use arrow keys or buttons to navigate

## Keyboard Shortcuts

### PGN Viewer
- **Left/Right Arrow** - Previous/Next move
- **Home/End** - Go to start/end
- **Q** - Quit

### Tournament GUI
- **SPACE** - Start/Pause
- **S** - Stop
- **Q** - Quit
- **1/2/3/4** - Speed (1x, 10x, 50x, 100x)

## Engine Strength

Estimated playing strength by depth:

| Engine | Depth 3 | Depth 5 | Depth 7 |
|--------|---------|---------|---------|
| v3.0 | ~1400 Elo | ~1800 Elo | ~2100 Elo |
| v4.0 | ~1550 Elo | ~1950 Elo | ~2250 Elo |

Note: Higher depths require more computation time.

## Game Recording

All games are automatically saved in PGN format with:
- Standard chess notation
- Player/engine information
- Time control details
- Performance statistics (nodes, time per move)
- Game result and termination reason

Games are organized by match in the `games/` directory.

## Development

### Git Workflow
- Work directly on `main` branch unless specified
- Commit successful improvements immediately
- Tag major versions (v4.0, v4.1, etc.)
- Keep clear commit messages

### Testing Protocol
1. Make ONE change at a time
2. Run quick test (10 games)
3. If promising, run full validation (100 games)
4. If successful (>55%), commit
5. Document in ENGINE_IMPROVEMENTS.md
6. Move to next improvement

### Contributing
Areas for enhancement:
- Engine evaluation improvements (see IMPLEMENTATION_ROADMAP.md)
- Opening book integration
- Endgame tablebase support
- UCI protocol compatibility
- Machine learning evaluation
- Web dashboard

## Technical Details

### Search Algorithm
- **Negamax** framework (cleaner than minimax)
- **Alpha-beta pruning** reduces tree by ~90%
- **Iterative deepening** for time management
- **Quiescence search** prevents horizon effect
- **Transposition table** caches positions (30-50% hit rate)

### Move Ordering
Critical for alpha-beta efficiency:
1. Hash move (from transposition table)
2. Captures (MVV - Most Valuable Victim)
3. Killer moves
4. History heuristic
5. Other moves

### Performance
- Typical search: 10K-100K positions/move at depth 5-6
- Average branching factor: ~35 (reduced to ~6 with move ordering)
- Search speed: 3,000-5,000 nodes/second

## License

See repository for license information.

## Acknowledgments

Built with:
- [python-chess](https://python-chess.readthedocs.io/) - Comprehensive chess library
- [pygame](https://www.pygame.org/) - Game development framework

## Documentation

- **ENGINE_IMPROVEMENTS.md** - Detailed log of engine development and testing
- **TOURNAMENT_GUIDE.md** - Complete guide to tournament system
- **IMPLEMENTATION_ROADMAP.md** - Future development plans

---

**Current Version:** 4.0
**Engine Strength:** v4.0 (~1950 Elo at depth 5)
**Status:** Active Development
**Python:** 3.8+ compatible

**Last Updated:** 2025-12-15
