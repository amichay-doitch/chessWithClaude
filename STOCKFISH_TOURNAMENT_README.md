# Stockfish Tournament Runner - How to Run Guide

## Overview

The tournament system uses a Stockfish-based engine (`stockfishSonChessEngine`) that supports two modes:
- **TIME-BASED**: Engine gets a fixed time per move (no randomness)
- **DEPTH-BASED**: Engine searches to a fixed depth (supports randomness)

## Quick Start Examples

### 1. Time-Based Self-Play (Fast Games)
```bash
python tournament.py --engine1 engine_pool.stockfishSonChessEngine --engine2 engine_pool.stockfishSonChessEngine --games 100 --time1 0.1 --time2 0.1
```
Both engines get 100ms per move. Best for generating lots of games quickly.

### 2. Different Time Limits (Asymmetric)
```bash
python tournament.py --engine1 engine_pool.stockfishSonChessEngine --engine2 engine_pool.stockfishSonChessEngine --games 50 --time1 0.5 --time2 0.1
```
Engine 1 gets 500ms, Engine 2 gets 100ms per move.

### 3. Depth-Based with Randomness (Diverse Training Data)
```bash
python tournament.py --engine1 engine_pool.stockfishSonChessEngine --engine2 engine_pool.stockfishSonChessEngine --games 100 --depth1 15 --depth2 15 --random_level1 0.5 --random_level2 0.7
```
Both engines search to depth 15, but select from top 3 moves with different randomness levels.

### 4. Mixed: Time vs Depth
```bash
python tournament.py --engine1 engine_pool.stockfishSonChessEngine --engine2 engine_pool.stockfishSonChessEngine --games 50 --time1 0.2 --depth2 12 --random_level2 0.3
```
Engine 1 uses time-based (200ms), Engine 2 uses depth-based (depth 12 with randomness).

## CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--engine1` | string | required | Engine module for player 1 |
| `--engine2` | string | required | Engine module for player 2 |
| `--games` | int | 100 | Number of games to play |
| `--depth1` | int | 5 | Search depth for engine 1 (depth-based mode) |
| `--depth2` | int | 5 | Search depth for engine 2 (depth-based mode) |
| `--time1` | float | None | Time per move for engine 1 in seconds |
| `--time2` | float | None | Time per move for engine 2 in seconds |
| `--random_level1` | float | None | Randomness for engine 1 (0.0-1.0) |
| `--random_level2` | float | None | Randomness for engine 2 (0.0-1.0) |
| `--output-dir` | string | "games" | Directory for saving PGN files |
| `--quiet` | flag | False | Minimize console output |
| `--quick` | flag | False | Quick test (10 games only) |

## Mode Selection Logic

**For each engine independently:**

| time set? | random_level set? | Result |
|-----------|-------------------|--------|
| YES | ignored | TIME-BASED mode (uses `get_best_move_time()`) |
| NO | NO | DEPTH-BASED, deterministic (always best move) |
| NO | YES (>0) | DEPTH-BASED with randomness (selects from top 3) |

## Randomness Levels Explained

The `random_level` parameter (0.0 to 1.0) controls move selection probability:

| Level | Best Move | 2nd Best | 3rd Best | Description |
|-------|-----------|----------|----------|-------------|
| 0.0 | 100% | 0% | 0% | Always best move |
| 0.3 | 82% | 12% | 6% | Low randomness |
| 0.5 | 70% | 20% | 10% | Moderate randomness |
| 0.7 | 58% | 27% | 15% | Medium-high randomness |
| 1.0 | 40% | 35% | 25% | High randomness |

## Output Files

Games are saved to `games/<match_folder>/`:
- Individual PGN files: `game_001.pgn`, `game_002.pgn`, etc.
- Match summary: `match_summary.json`

Engine names in PGN include configuration:
- `stockfishSonChessEngine_T100ms` - Time-based, 100ms per move
- `stockfishSonChessEngine_D15_R50` - Depth 15, 50% randomness

## Training Data Generation Strategies

### High Volume (Speed Priority)
```bash
# Generate 1000 fast games
python tournament.py --engine1 engine_pool.stockfishSonChessEngine --engine2 engine_pool.stockfishSonChessEngine --games 1000 --time1 0.05 --time2 0.05
```

### High Diversity (Quality Priority)
```bash
# Different randomness levels for diverse game trees
python tournament.py --engine1 engine_pool.stockfishSonChessEngine --engine2 engine_pool.stockfishSonChessEngine --games 200 --depth1 12 --depth2 12 --random_level1 0.3 --random_level2 0.8
```

### Skill Gradient
```bash
# Stronger vs weaker (deeper search vs more randomness)
python tournament.py --engine1 engine_pool.stockfishSonChessEngine --engine2 engine_pool.stockfishSonChessEngine --games 100 --depth1 18 --random_level1 0.1 --depth2 10 --random_level2 0.6
```

## Common Mistakes

1. **Wrong**: `--time1 0.1 --time1 0.05` (second --time1 overwrites first)
   **Right**: `--time1 0.1 --time2 0.05`

2. **Wrong**: Using both `--time1` and `--random_level1` expecting randomness
   **Right**: Time-based mode ignores randomness. Use depth-based for randomness.

3. **Wrong**: Forgetting the `engine_pool.` prefix
   **Right**: `--engine1 engine_pool.stockfishSonChessEngine`
