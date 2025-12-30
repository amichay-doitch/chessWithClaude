# Chess Engine Test Suite - User Guide

## Overview

The test suite system evaluates chess engines on tactical, positional, checkmate, and endgame positions using **Stockfish as the reference engine** for objective scoring. It provides both **CLI** and **Interactive GUI** interfaces.

## Key Features

- **Stockfish-Based Evaluation**: Uses Stockfish (world's strongest engine) to objectively evaluate engine performance
- **Dynamic Scoring**: Measures how much evaluation is lost compared to optimal play (formula: `(eval_after / eval_before) - 1`)
- **40 Curated Positions**: Across 4 categories (Tactical, Checkmate, Endgame, Positional)
- **Multiple Interfaces**: Interactive GUI, CLI batch runner, and auto-viewer

## Quick Start

### Interactive GUI (Recommended)

**Visual interface with step-by-step move comparison:**

```bash
python test_suite_interactive.py
```

**Features:**
1. Select engine from dropdown
2. Choose tests by category (collapsible checkboxes)
3. Set max depth and time limit
4. View each position on visual board
5. See Stockfish's best move vs engine's move
6. Navigate with arrow keys
7. Get detailed score breakdown

**Navigation:**
- **RIGHT arrow**: Show engine's move, then both moves
- **LEFT arrow**: Go back
- **ESC**: Advance to next test
- **Next Test** button: Skip to next

### CLI Runner

**Text-based output for automation and comparison:**

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

## Stockfish Integration

### Library Migration (December 2025)

**Migrated from:** python-chess direct UCI → `stockfish` Python library v4.0.3

The test suite now uses the powerful `stockfish` Python library for enhanced analysis capabilities including top-N moves, ELO testing, and verbose statistics.

### How It Works

For each test position:

1. **Load FEN** from test_positions.yaml
2. **Run Stockfish** on the position → get **top 3 moves** + evaluations
3. **Run your engine** → `engine_move`
4. **Check if engine move is in top 3:**
   - **Rank #1**: Score = 0% (perfect!)
   - **Rank #2**: Score = 10% penalty (very good)
   - **Rank #3**: Score = 15% penalty (acceptable)
   - **Not in top 3**: Use evaluation-based scoring
5. If not in top 3:
   - Apply engine's move to the board
   - Run Stockfish again → `eval_after`
   - Calculate score: `(eval_after / eval_before) - 1`
6. **Determine status**: EXCELLENT / OK / POOR / TERRIBLE

### Enhanced Scoring System

**Top-3 Move Recognition:**
```
If engine_move == Stockfish's #1 move: score = 0%   (EXCELLENT)
If engine_move == Stockfish's #2 move: score = 10%  (EXCELLENT)
If engine_move == Stockfish's #3 move: score = 15%  (EXCELLENT)
Otherwise: score = (eval_after / eval_before) - 1
```

**Examples:**

| Engine Move | Stockfish Ranking | Score | Status    | Meaning |
|-------------|-------------------|-------|-----------|---------|
| e2e4        | Rank #1           | 0%    | EXCELLENT | Found best move! |
| d2d4        | Rank #2           | 10%   | EXCELLENT | Second best move |
| g1f3        | Rank #3           | 15%   | EXCELLENT | Third best move |
| a2a3        | Not in top 3, +5.0 → +4.0 | -20% | EXCELLENT | Lost 20% eval |
| h2h3        | Not in top 3, +5.0 → +2.5 | -50% | OK | Lost half advantage |
| a2a4        | Not in top 3, +5.0 → 0.0  | -100% | POOR | Lost all advantage |

**Status Thresholds:**
- **EXCELLENT** (✓): 0% to -20% (minimal eval loss OR in top 3)
- **OK** (~): -20% to -50% (some advantage lost)
- **POOR** (✗): -50% to -100% (major advantage lost)
- **TERRIBLE** (✗✗): < -100% (position flipped or worse)

**Key Improvement:** Engines are no longer harshly penalized for finding 2nd or 3rd best moves!

### Installing Stockfish

**Required:**
- Download Stockfish from: https://stockfishchess.org/download/
- Place `stockfish.exe` (Windows) or `stockfish` (Linux/Mac) in your PATH or project directory
- Install stockfish library: `pip install stockfish` (already in requirements.txt)

**Verify installation:**
```bash
stockfish
# Should show Stockfish version and wait for commands
# Type "quit" to exit
```

### Advanced Features

#### ELO Rating Testing
Test your engine against different Stockfish strengths:

```python
# In code (ready to use, UI not yet built):
with StockfishAnalyzer(stockfish_path="stockfish.exe", elo_rating=1500) as analyzer:
    analysis = analyzer.analyze(board, top_n=3)
```

**Supported ELO range:** 1320-2850 (Stockfish minimum is 1320)

**Use cases:**
- Test against 1350 ELO: Should score 80%+
- Test against 1800 ELO: Should score 50-60%
- Test against 2400 ELO: Should score 30-40%
- Full strength (default): Current behavior

#### Top-N Moves Analysis
See what Stockfish considers the best moves:

```python
analysis = analyzer.analyze(board, top_n=3, verbose=True)
for move_analysis in analysis.top_moves:
    print(f"{move_analysis.rank}. {move_analysis.move_uci} ({move_analysis.centipawn/100:+.2f})")
```

**Output example:**
```
1. e2e4 (+0.40)
2. d2d4 (+0.26)
3. g1f3 (+0.20)
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

## Interpreting Results

### CLI Output Example

```
======================================================================
engine_v5 - TEST SUMMARY (Stockfish-evaluated)
======================================================================

Overall Average Score: -42.3%
Total Positions: 40

Position Details:
----------------------------------------------------------------------
Position 1/40: Greek Gift Sacrifice
  Category: tactical | Difficulty: medium

  Stockfish Top 3:
    1. Bxh7+ (+4.50)
    2. Nxe5 (+0.85)
    3. Bd3 (+0.30)

  Engine:    Bxh7+ (rank: 1)
  Score:     +0.0% ✓ EXCELLENT
  Time:      0.35s | Nodes: 45,231
  SF Stats:  1,250,000 nodes @ 850,000 nps

======================================================================
Category Breakdown:
----------------------------------------------------------------------
  ✓ Tactical      : Avg: -12.5%
      ✓18 Excellent  ~2 OK  ✗0 Poor  ✗✗0 Terrible
  ~ Checkmate     : Avg: -38.2%
      ✓8 Excellent  ~6 OK  ✗4 Poor  ✗✗2 Terrible
  ✗ Endgame       : Avg: -67.1%
      ✓2 Excellent  ~3 OK  ✗8 Poor  ✗✗7 Terrible
  ~ Positional    : Avg: -28.5%
      ✓12 Excellent  ~4 OK  ✗3 Poor  ✗✗1 Terrible

======================================================================
Recommendations:
----------------------------------------------------------------------
  * Endgame: 75% positions are poor/terrible (avg: -67.1%)
    > Consider: king activity, pawn advancement, opposition
```

**Notice:** With top-3 scoring, tactical scores improved from -18.2% to -12.5% because the system now recognizes 2nd/3rd best moves!

### Category Performance Guidelines

- **70%+ EXCELLENT**: Strong category
- **50-70% OK/EXCELLENT**: Decent, room for improvement
- **50%+ POOR/TERRIBLE**: Weak category, needs work

### Recommendations

Based on weak categories, the suite suggests:

- **Tactical**: Deeper search, better move ordering, tactical pruning
- **Checkmate**: Check extensions, mate threat evaluation
- **Endgame**: King activity, pawn advancement, opposition awareness
- **Positional**: Piece mobility, pawn structure, weak squares

## Adding New Test Positions

Edit `test_positions.yaml`:

```yaml
test_positions:
  - id: tactical_041
    name: "Trapped Piece"
    category: tactical
    difficulty: medium
    fen: "r1bqkb1r/pppp1ppp/2n2n2/4p3/2B1P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4"
    description: "Win the trapped knight"
```

**Fields:**
- `id`: Unique identifier (category_number)
- `name`: Display name
- `category`: tactical, checkmate, endgame, or positional
- `difficulty`: easy, medium, or hard
- `fen`: Position in FEN notation
- `description`: Brief explanation of the tactic

**Note:** No need to specify best_moves or points - Stockfish determines optimal play!

## Files

- **`test_suite_interactive.py`** - Interactive GUI for step-by-step testing
- **`test_suite.py`** - CLI test runner for batch testing
- **`test_positions.yaml`** - Test position database (40 positions)
- **`stockfish_analyzer.py`** - Stockfish library wrapper with top-N moves, ELO testing
- **`test_stockfish_migration.py`** - Migration verification test suite
- **`requirements.txt`** - Dependencies (includes stockfish==4.0.3)
- **`TEST_SUITE_GUIDE.md`** - This file

## Tips

1. **Baseline Testing**: Run tests on all engine versions to track progress
2. **Depth Testing**: Try different depths (4, 5, 6, 7) to see scaling
3. **Time Testing**: Test with different time limits (1s, 2s, 5s)
4. **Compare Versions**: Use `--engines` and `--compare` to see improvements
5. **Save Results**: Use `--save` to track historical performance
6. **Focus Weak Areas**: Add more positions in categories where engines fail
7. **Stockfish Depth**: Default is depth 20 - adjust in code if needed

## Troubleshooting

**"Stockfish not found" error:**
- Download from https://stockfishchess.org/download/
- Ensure `stockfish` is in your PATH
- Or specify full path: `StockfishAnalyzer("C:/path/to/stockfish.exe")`

**GUI doesn't show:**
- Ensure pygame is installed: `pip install pygame`
- Check if chess fonts exist (optional, unicode fallback works)

**Slow tests:**
- Reduce engine depth: `--depth 4` instead of 6
- Reduce time limit: `--time 1.0` instead of 2.0
- Reduce Stockfish depth in code (default: 20)

**Interactive GUI freezes:**
- Engine calculation runs in background thread
- Board updates once Stockfish finishes analyzing
- Be patient - deep Stockfish analysis takes time

## Development Workflow

1. **Make engine changes** (improve evaluation, search, etc.)
2. **Run interactive test suite**: `python test_suite_interactive.py`
3. **Check which categories improved/declined**
4. **Identify specific weak positions**
5. **Iterate based on Stockfish comparisons**
6. **Compare with previous version**: `python test_suite.py --engines engine_v5 engine_v6 --compare`
7. **Save results for tracking**: `--save results_vX.json`

## Understanding the Scoring

**Old System (removed):**
- Hardcoded best_moves and avoid_moves
- Fixed points (5-15 per position)
- Subjective and required manual verification

**New System (Stockfish-based):**
- Objective evaluation using world's strongest engine
- Dynamic scoring shows exactly how much eval was lost
- No manual verification needed
- More accurate measure of engine strength

**Why percentage instead of points?**
- Losing +5 to +4 (-20%) is different than losing +1 to +0.8 (-20%)
- Percentage shows relative quality, not absolute
- Flipping winning to losing is severe (-200%+)
- Easy to compare across positions of different complexity

## Migration Details (December 2025)

### What Changed

**Migrated from:** `python-chess` direct UCI communication
**Migrated to:** `stockfish` Python library v4.0.3

### Key Improvements

1. **Top-3 Move Recognition**
   - Engines get credit for finding 2nd or 3rd best moves
   - Rank #1: 0%, Rank #2: 10%, Rank #3: 15%
   - Less harsh, more nuanced scoring

2. **ELO Testing Ready**
   - Test against different Stockfish strengths (1320-2850)
   - Progressive difficulty assessment
   - Code ready, GUI integration pending

3. **Richer Analysis Data**
   - Top moves with evaluations and centipawn scores
   - Verbose search statistics (nodes, NPS, selective depth)
   - Better debugging and performance insights

4. **Cleaner API**
   - Direct FEN position loading (leveraging existing YAML data)
   - More Pythonic interface
   - Maintained 100% backward compatibility

### Technical Changes

**stockfish_analyzer.py** - Complete refactor (94 → 211 lines)
- New dataclasses: `MoveAnalysis`, `VerboseStats`
- Extended `StockfishAnalysis` with optional fields
- New parameters: `elo_rating`, `skill_level`, `threads`, `hash_size`
- New analyze() parameters: `top_n`, `verbose`

**test_suite.py** - Enhanced scoring (lines 121-258)
- Top-3 scoring logic with smart penalties
- Enhanced verbose output showing all top moves
- Extended results with `stockfish_top_moves`, `engine_move_rank`, etc.

**test_suite_interactive.py** - GUI updates (lines 479-829)
- Same top-3 scoring as CLI
- Display fix: Shows "Rank #1/2/3" instead of eval for top moves
- Extended result structure with new fields

**All changes tested and verified with test_stockfish_migration.py**

### Known Limitations

1. **ELO Minimum:** Stockfish's UCI_Elo minimum is 1320 (not 1200)
2. **Verbose Stats:** Library doesn't consistently return verbose keys (not critical)
3. **Top Moves with ELO:** When using ELO limiting, `get_top_moves()` still returns full-strength moves (expected behavior)

### Backward Compatibility

✅ **100% Maintained**
- `StockfishAnalyzer()` works without parameters
- `analyze(board)` works with defaults (top_n=1, verbose=False)
- All existing code continues to work unchanged

## Future Enhancements

**Ready to Implement:**
- [ ] ELO dropdown in GUI config screen
- [ ] Top moves display in GUI info panel
- [ ] Win/Draw/Loss (WDL) statistics from Stockfish

**Nice to Have:**
- [ ] Add more test positions (WAC, Arasan tactical suites)
- [ ] Difficulty-weighted scoring (hard positions count more)
- [ ] Historical tracking graphs (compare versions over time)
- [ ] Opening test positions
- [ ] Time-based scoring (faster = bonus)
- [ ] Static eval mode (quick position assessment)

## Credits

Test positions curated from classic tactical and endgame studies. Evaluation powered by Stockfish - the world's strongest open-source chess engine.
