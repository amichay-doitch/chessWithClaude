# Chess Engine Test Suite - User Guide

## Overview

The test suite system helps you evaluate chess engines on tactical, positional, checkmate, and endgame positions. It provides both **CLI** and **GUI** interfaces.

## Quick Start

### GUI Viewer (Recommended)

**Visual interface showing positions on a chess board:**

```bash
python test_suite_viewer.py engine_v5 --depth 5 --time 1.5
```

**GUI Controls:**
- **SPACE**: Pause/Resume auto-run
- **LEFT/RIGHT arrows**: Navigate between test positions
- **R**: Restart tests from beginning
- **S**: Save results to JSON file
- **ESC**: Exit

**What you'll see:**
1. Chess board with current test position
2. Info panel showing:
   - Test name and category
   - Expected moves vs engine's move
   - Pass/Fail status (✓ green, ✗ red, ~ yellow)
   - Progress counter (e.g., "5/40")
   - Overall score
   - Keyboard controls

3. Auto-run flow:
   - Tests run automatically on startup
   - Each position shows for 2 seconds
   - Final summary screen at end

### CLI Runner

**Text-based output for automation:**

```bash
# Test single engine
python test_suite.py --engine engine_v5 --depth 5 --time 1.5

# Compare multiple engines
python test_suite.py --engines engine_v5 engine_v6 --compare

# Save results to JSON
python test_suite.py --engine engine_v6 --save results.json

# Quiet mode (less output)
python test_suite.py --engine engine_v5 --quiet
```

## Test Positions

The test suite includes **40 curated positions** across 4 categories:

### Tactical (10 positions)
- Greek Gift Sacrifice
- Pin - Win Material
- Fork - Knight Fork
- Discovered Attack
- Skewer
- Removing Defender
- Deflection
- Desperado
- Zwischenzug
- Overloaded Piece

### Checkmate (10 positions)
- Back Rank Mate
- Smothered Mate
- Queen and Rook Mate
- Anastasia's Mate
- Arabian Mate
- Epaulette Mate
- Mate in 2 - Sacrifice
- Mate in 2 - Queen Sac
- Philidor's Legacy
- Boden's Mate

### Endgame (10 positions)
- King and Pawn - Opposition
- Queen vs King
- Rook Endgame - Lucena
- Rook Endgame - Philidor
- Pawn Endgame - Square Rule
- Bishop and Pawn vs King
- Rook vs Pawn - Drawn
- Queen vs Rook
- Opposite Bishops
- Rook and Pawn on 7th

### Positional (10 positions)
- Control the Center
- Complete Development - Castle
- Weak Square Exploitation
- Doubled Pawns Problem
- Open File for Rook
- Knight Outpost
- Bishop Pair Advantage
- Pawn Structure - Isolani
- King Safety - Don't Move Pawns
- Space Advantage

## Scoring System

- **Correct move**: Full points (5-15 per position)
- **Acceptable move**: Half points (move not in expected, but not terrible)
- **Wrong move**: 0 points (move in avoid list)

**Total possible**: 385 points

## Interpreting Results

### Category Breakdown

- **70%+**: ✓ GOOD - Engine performs well
- **50-69%**: ~ OK - Room for improvement
- **<50%**: ✗ WEAK - Needs work

### Recommendations

The test suite provides specific suggestions based on weak categories:

- **Tactical < 60%**: "Improve tactical vision"
  → Consider: deeper search, better move ordering, tactical pruning

- **Checkmate < 60%**: "Strengthen checkmate detection"
  → Consider: check extensions, mate threat evaluation

- **Endgame < 60%**: "Enhance endgame play"
  → Consider: king activity, pawn advancement, opposition

- **Positional < 60%**: "Improve positional understanding"
  → Consider: piece mobility, pawn structure, weak squares

## Example Results

```
======================================================================
engine_v5 - TEST SUMMARY
======================================================================

Overall Score: 194/385 (50.4%)

Category Breakdown:
----------------------------------------------------------------------
  ~ Checkmate      :  55/ 94 ( 58.5%) - OK
  ~ Endgame        :  61/ 98 ( 62.2%) - OK
  X Positional     :  40/ 86 ( 46.5%) - WEAK
  X Tactical       :  38/107 ( 35.5%) - WEAK

======================================================================
Recommendations:
----------------------------------------------------------------------
  * Improve tactical vision - only 36% on tactical positions
    > Consider: deeper search, better move ordering, tactical pruning
  * Improve positional understanding - only 46% on positional positions
    > Consider: piece mobility, pawn structure, weak squares
```

## Adding New Test Positions

Edit `test_positions.yaml`:

```yaml
test_positions:
  - id: tactical_011
    name: "Double Attack"
    category: tactical
    difficulty: medium
    fen: "r1bqkbnr/pppp1ppp/2n5/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    best_moves:
      - b1c3
      - d2d4
    avoid_moves:
      - c4f7
    description: "Develop pieces and control center"
    points: 8
```

**Fields:**
- `id`: Unique identifier
- `name`: Display name
- `category`: tactical, checkmate, endgame, or positional
- `difficulty`: easy, medium, or hard
- `fen`: Position in FEN notation
- `best_moves`: List of acceptable moves (UCI format: e2e4, g1f3, etc.)
- `avoid_moves`: List of bad moves (UCI format)
- `description`: Brief explanation
- `points`: Score value (typically 5-15)

## Files

- **`test_positions.yaml`** - Test position database (edit to add positions)
- **`test_suite.py`** - CLI test runner
- **`test_suite_viewer.py`** - GUI test viewer
- **`TEST_SUITE_GUIDE.md`** - This file

## Tips

1. **Baseline Testing**: Run tests on all engine versions to track progress
2. **Depth Testing**: Try different depths (4, 5, 6, 7) to see scaling
3. **Time Testing**: Test with different time limits (1s, 2s, 5s)
4. **Compare Versions**: Use `--engines` and `--compare` to see improvements
5. **Save Results**: Use `--save` to track historical performance
6. **Focus Weak Areas**: Add more positions in categories where engines fail

## Troubleshooting

**GUI doesn't show:**
- Ensure pygame is installed: `pip install pygame`
- Check if chess fonts exist (ChessMerida.ttf)
- GUI falls back to unicode pieces if fonts missing

**Unicode errors in CLI:**
- This is a Windows console limitation
- Results still save correctly to JSON
- Use GUI for better visualization

**Slow tests:**
- Reduce depth: `--depth 4` instead of 6
- Reduce time limit: `--time 1.0` instead of 2.0
- Test fewer positions (edit YAML to comment out positions)

## Development Workflow

1. **Make engine changes** (improve evaluation, search, etc.)
2. **Run test suite**: `python test_suite_viewer.py engine_vX`
3. **Check which categories improved/declined**
4. **Iterate based on recommendations**
5. **Compare with previous version**: `python test_suite.py --engines engine_v5 engine_v6 --compare`
6. **Save results for tracking**: `--save results_vX.json`

## Future Enhancements

- [ ] Add more test positions (WAC, Arasan suites)
- [ ] Difficulty-weighted scoring
- [ ] Historical tracking graphs
- [ ] Opening test positions
- [ ] Perft/speed tests
- [ ] Tablebase validation



> /compact keep with test_suite_interactive
  ⎿  Compacted (ctrl+o to see full summary)
  ⎿  Referenced file test_suite_interactive.py
  ⎿  Read ..\..\..\..\..\AMICHA~1\AppData\Local\Temp\claude\C--Users-AmichayDeutsch-OneDrive---Start-io-Documents-Python-Scripts-chessWithClaudeGit\tasks\ba8b6af.output (6 lines)
  ⎿  Referenced file test_suite_viewer.py
  ⎿  Read TEST_SUITE_GUIDE.md (247 lines)
  ⎿  Read test_suite.py (369 lines)
  ⎿  Plan file referenced (~\.claude\plans\jazzy-leaping-finch.md)