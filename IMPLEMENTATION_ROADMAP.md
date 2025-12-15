# Chess Engine - Complete Implementation Roadmap

**Last Updated:** 2025-12-15
**Current Status:** Tournament system complete, v4.0 showing 70% win rate over v3.0
**Next Phase:** Continue engine improvements through systematic testing

---

## 🎯 Current Achievement

✅ **Iteration 1 Complete: Piece Value Tuning** (+150-200 Elo gain!)
- Queen: 975 → 900 centipawns
- Knight: 320 → 305 centipawns
- Result: 70% win rate in quick test (target was >55%)
- Status: Validating with 100-game tournament

---

## 📋 Immediate Priorities (Next 1-2 Sessions)

### Priority 1: Complete Current Validation
**Estimated Time:** Check status only (5 mins)

- [ ] Check if 100-game v3 vs v4 validation tournament completed
- [ ] Review full results with `results_viewer.py`
- [ ] If successful (>55%), commit v4.0 improvements
- [ ] Update ENGINE_IMPROVEMENTS.md with final results

**Commands:**
```bash
# Check games completed
find games -name "*.pgn" | wc -l

# View results
python results_viewer.py games/engine_v3_vs_engine_v4/match_2025-12-15_*/
```

---

### Priority 2: Iteration 2 - Move Ordering (MVV-LVA)
**Estimated Time:** 30-60 minutes
**Difficulty:** Medium
**Expected Impact:** +50 to +100 Elo

#### Implementation Tasks:
- [ ] Add `_mvv_lva_score()` method to `engine_v4.py`
  - Calculate victim value * 10 - attacker value
  - Prioritize capturing high-value pieces with low-value pieces
- [ ] Update `_order_moves()` to use MVV-LVA for capture ordering
- [ ] Test implementation doesn't break existing functionality
- [ ] Run quick test (10 games)
- [ ] If promising, run 100-game validation
- [ ] Document results in ENGINE_IMPROVEMENTS.md

**Code Location:** `engine_v4.py`, around line 900-1000 (`_order_moves()` method)

**Implementation Details:**
```python
def _mvv_lva_score(self, move: chess.Move, board: chess.Board) -> int:
    """
    Score captures using MVV-LVA.
    Returns: (victim_value * 10) - attacker_value
    """
    if not board.is_capture(move):
        return 0

    victim = board.piece_at(move.to_square)
    attacker = board.piece_at(move.from_square)

    if victim is None:
        return 0

    victim_value = self.PIECE_VALUES[victim.piece_type]
    attacker_value = self.PIECE_VALUES[attacker.piece_type]

    return (victim_value * 10) - attacker_value
```

---

### Priority 3: Iteration 3 - Passed Pawn Evaluation
**Estimated Time:** 30-45 minutes
**Difficulty:** Easy
**Expected Impact:** +40 to +80 Elo

#### Implementation Tasks:
- [ ] Add distance-based passed pawn bonus (exponential increase near promotion)
- [ ] Add connected passed pawn bonus
- [ ] Reduce bonus for blocked passed pawns
- [ ] Test with 10-game quick test
- [ ] Run 100-game validation if successful
- [ ] Document results

**Code Location:** `engine_v4.py`, around line 600-650 (pawn structure evaluation)

**Key Changes:**
```python
# Current: Fixed 50 point bonus
# New: Distance-based exponential bonus
rank = chess.square_rank(square)
distance_to_promotion = 7 - rank if color == chess.WHITE else rank
bonus = 50 * (7 - distance_to_promotion) ** 1.5

# Add connected passed pawn bonus
if has_connected_passed_pawn(square, color, board):
    bonus += 30

# Reduce if blocked
if is_blocked(square, color, board):
    bonus *= 0.5
```

---

### Priority 4: Iteration 4 - King Safety Improvements
**Estimated Time:** 45-60 minutes
**Difficulty:** Medium
**Expected Impact:** +30 to +70 Elo

#### Implementation Tasks:
- [ ] Add castling bonus (encourage early castling)
- [ ] Add penalty for not castling when available
- [ ] Implement pawn storm detection (opponent pawns advancing near king)
- [ ] Add penalty for open files near king
- [ ] Test with 10-game quick test
- [ ] Run 100-game validation
- [ ] Document results

**Code Location:** `engine_v4.py`, king safety section in `evaluate()` method

**Improvements:**
1. **Castling Bonus:**
   ```python
   if board.has_kingside_castling_rights(color) or board.has_queenside_castling_rights(color):
       score -= 30  # Penalty for not having castled yet

   if has_castled(board, color):
       score += 40  # Bonus for having castled
   ```

2. **Pawn Storm Detection:**
   ```python
   # Detect advancing enemy pawns on files near king
   king_file = chess.square_file(king_square)
   for file in [king_file - 1, king_file, king_file + 1]:
       # Check for enemy pawns advancing toward our king
       # Penalty increases as pawns get closer
   ```

3. **Open File Detection:**
   ```python
   if is_open_file_near_king(king_square, board):
       score -= 25  # Vulnerable to rook attacks
   ```

---

## 🚀 Medium-Term Goals (Next 2-4 Sessions)

### Enhancement 1: Search Extensions (ADVANCED)
**Estimated Time:** 2-3 hours
**Difficulty:** Hard
**Expected Impact:** +100 to +200 Elo (high risk/reward)
**Priority:** Medium (after simpler improvements)

#### Implementation Tasks:
- [ ] **Phase 1: Check Extensions**
  - [ ] Extend search depth by 1 when in check
  - [ ] Test carefully (can cause search explosion)
  - [ ] Validate performance impact

- [ ] **Phase 2: Pawn Push to 7th Rank**
  - [ ] Extend when pawn moves to 7th rank (about to promote)
  - [ ] Test with pawn endgames

- [ ] **Phase 3: Recapture Extensions**
  - [ ] Extend on recaptures (tactical sequences)
  - [ ] Requires tracking previous move

- [ ] **Phase 4: One-Reply Extensions**
  - [ ] Extend when only one legal move (forced)
  - [ ] Monitor for search explosion

**Notes:**
- Start with check extensions only
- Consider fractional extensions (0.5 plies) to prevent explosion
- Monitor nodes/time carefully
- Be prepared to revert if performance degrades
- This is high-impact but risky

---

### Enhancement 2: Opening Book Integration
**Estimated Time:** 1-2 hours
**Difficulty:** Easy
**Expected Impact:** Better testing variety, not direct Elo gain

#### Implementation Tasks:
- [ ] Update `tournament.py` to use `openings.fen` file
- [ ] Add `--use-openings` flag to tournament CLI
- [ ] Randomly select opening position for each game
- [ ] Ensure both engines get equal distribution of openings
- [ ] Test that opening positions load correctly
- [ ] Update documentation

**Files Involved:**
- `tournament.py` - Add opening book support
- `openings.fen` - Already created with 20 positions

---

### Enhancement 3: Adjudication Rules
**Estimated Time:** 1-2 hours
**Difficulty:** Medium
**Expected Impact:** Faster tournaments, clearer results

#### Implementation Tasks:
- [ ] **Tablebase Adjudication**
  - [ ] Declare draw when material insufficient for mate
  - [ ] Declare win in known won endgames

- [ ] **Score-based Adjudication**
  - [ ] Declare win if eval > +10.0 for 10 consecutive moves
  - [ ] Saves time on clearly won positions

- [ ] **Draw Adjudication**
  - [ ] Auto-adjudicate threefold repetition
  - [ ] Auto-adjudicate 50-move rule
  - [ ] Declare draw if eval stays within [-0.5, +0.5] for 40 moves

- [ ] Add `--adjudicate` flag to enable/disable
- [ ] Test with long games
- [ ] Ensure accuracy (no false positives)

---

### Enhancement 4: Parallel Game Execution
**Estimated Time:** 2-3 hours
**Difficulty:** Hard
**Expected Impact:** 2-4x faster tournaments (using multiple CPU cores)

#### Implementation Tasks:
- [ ] Implement multiprocessing for game execution
- [ ] Run 4-8 games simultaneously (based on CPU cores)
- [ ] Ensure thread-safe game recording
- [ ] Maintain progress tracking across parallel games
- [ ] Add `--parallel N` flag to specify number of parallel games
- [ ] Test with 100-game tournament
- [ ] Verify PGN files are saved correctly
- [ ] Update progress bar to show all games

**Technical Considerations:**
- Use Python's `multiprocessing` module
- Each game runs in separate process
- Need process-safe file writing
- Progress updates need synchronization

---

## 📊 Advanced Features (Future Sessions)

### Feature 1: Real-time Evaluation Graph (GUI)
**Estimated Time:** 2-3 hours
**Difficulty:** Medium
**Expected Impact:** Better analysis and debugging

#### Implementation Tasks:
- [ ] Add evaluation history tracking to games
- [ ] Plot evaluation graph in tournament_gui.py
- [ ] Show critical moments (evaluation swings)
- [ ] Add to replay mode
- [ ] Export graph images

---

### Feature 2: Position Test Suite
**Estimated Time:** 2-3 hours
**Difficulty:** Medium
**Expected Impact:** Tactical strength measurement

#### Implementation Tasks:
- [ ] Create database of tactical positions (mate in N, win material, etc.)
- [ ] Create test runner: `python test_tactics.py`
- [ ] Measure success rate on each position
- [ ] Compare engine versions
- [ ] Include famous positions (e.g., Lucena, Philidor endgames)
- [ ] Track improvement over time

**File Structure:**
```
test_positions/
├── tactics/
│   ├── mate_in_2.fen
│   ├── mate_in_3.fen
│   └── win_material.fen
├── endgames/
│   ├── rook_endgames.fen
│   └── pawn_endgames.fen
└── test_runner.py
```

---

### Feature 3: Analysis Mode
**Estimated Time:** 3-4 hours
**Difficulty:** Hard
**Expected Impact:** Identify weaknesses for targeted improvements

#### Implementation Tasks:
- [ ] After tournament, auto-analyze games with deeper search
- [ ] Compare moves played vs. best move at higher depth
- [ ] Identify blunders (moves with eval drop > 2.0)
- [ ] Generate improvement report
- [ ] Categorize errors (tactical, positional, endgame)
- [ ] Create `analysis_report.py`

**Output Example:**
```
Analysis Report: v3 vs v4 (100 games)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

v3.0 Blunders: 47
  - Tactical: 28 (60%)
  - Positional: 12 (26%)
  - Endgame: 7 (14%)

v4.0 Blunders: 23 (-51% improvement!)
  - Tactical: 12 (52%)
  - Positional: 7 (30%)
  - Endgame: 4 (18%)

Most Common v3 Errors:
1. Overvaluing queen trades (12 occurrences)
2. Weak king safety (8 occurrences)
3. Passed pawn underestimation (6 occurrences)
```

---

### Feature 4: Web Dashboard
**Estimated Time:** 6-10 hours
**Difficulty:** Very Hard
**Expected Impact:** Professional presentation and long-term tracking

#### Implementation Tasks:
- [ ] Create Flask/FastAPI web server
- [ ] Real-time tournament viewing in browser
- [ ] Historical results database
- [ ] Graph engine improvement over time
- [ ] Compare multiple engine versions
- [ ] Interactive game replay
- [ ] Export capabilities

**Technology Stack:**
- Backend: Flask or FastAPI
- Frontend: HTML/CSS/JavaScript
- Charting: Chart.js or Plotly
- Chess board: chess.js + chessboard.js

---

### Feature 5: Machine Learning Integration
**Estimated Time:** 10+ hours
**Difficulty:** Very Hard
**Expected Impact:** Potential massive Elo gain (speculative)

#### Phase 1: Dataset Preparation
- [ ] Parse all saved PGN files
- [ ] Extract position-evaluation pairs
- [ ] Convert boards to neural network input format
- [ ] Create training/validation split
- [ ] Export to ML-friendly format (CSV, numpy arrays)

#### Phase 2: Neural Network Training
- [ ] Design network architecture (CNN or transformer)
- [ ] Implement in PyTorch or TensorFlow
- [ ] Train on position dataset
- [ ] Validate against test positions
- [ ] Compare vs. hand-crafted evaluation

#### Phase 3: Hybrid Engine
- [ ] Integrate NN evaluation into engine
- [ ] Use NN for position evaluation
- [ ] Keep alpha-beta search
- [ ] Test hybrid vs. traditional engine
- [ ] Tune balance between NN and heuristics

**Notes:**
- Very long-term project
- Requires significant ML expertise
- Large dataset needed (10,000+ games)
- Computational resources for training

---

## 🔧 Code Quality & Maintenance

### Refactoring Tasks
- [ ] Add comprehensive docstrings to all engine methods
- [ ] Add type hints throughout codebase
- [ ] Create unit tests for evaluation functions
- [ ] Add integration tests for tournament system
- [ ] Optimize hot paths (profiling + optimization)
- [ ] Code style consistency (run Black formatter)

### Documentation Updates
- [ ] Update README.md with v4.0 achievements
- [ ] Document all engine improvements
- [ ] Create CONTRIBUTING.md guide
- [ ] Add architecture diagrams
- [ ] Create tutorial for adding new evaluation terms

---

## 📈 Testing & Validation Strategy

### Quick Test (10 games, depth 3, 0.1s/move)
**Use for:** Initial validation of changes
```bash
python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4 --depth1 3 --depth2 3 --time 0.1
```

### Standard Test (100 games, depth 3, 0.1s/move)
**Use for:** Statistical validation before commit
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --games 100 --depth1 3 --depth2 3 --time 0.1
```

### Deep Test (200 games, depth 5, 0.5s/move)
**Use for:** Final validation before production promotion
```bash
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --games 200 --depth1 5 --depth2 5 --time 0.5
```

### Success Criteria:
- ✅ Win rate > 55% (minimum)
- ✅ Win rate > 60% (ideal)
- ✅ No speed regression > 20%
- ✅ No obvious tactical blunders
- ✅ Qualitatively better play

---

## 🎯 Milestones & Goals

### Milestone 1: v4.0 Release (CURRENT)
- [x] Piece value tuning (+150-200 Elo)
- [ ] 100-game validation complete
- [ ] Commit and tag v4.0

### Milestone 2: v4.1 Release (NEXT)
- [ ] Move ordering (MVV-LVA) (+50-100 Elo)
- [ ] Passed pawn evaluation (+40-80 Elo)
- [ ] Total expected: +240-380 Elo over v3.0

### Milestone 3: v4.2 Release
- [ ] King safety improvements (+30-70 Elo)
- [ ] Opening book integration
- [ ] Adjudication rules
- [ ] Total expected: +270-450 Elo over v3.0

### Milestone 4: v5.0 Release
- [ ] Search extensions (+100-200 Elo)
- [ ] Parallel tournaments
- [ ] Position test suite
- [ ] Total expected: +370-650 Elo over v3.0

### Long-term Vision: v6.0+ (Neural Network Hybrid)
- [ ] ML integration
- [ ] Web dashboard
- [ ] Advanced analysis tools
- [ ] Expected: Potentially +500-1000 Elo

---

## 📊 Elo Progression Tracking

| Version | Changes | Expected Elo | Actual Elo | Status |
|---------|---------|--------------|------------|--------|
| v3.0 | Baseline | 0 | 0 | ✅ Complete |
| v4.0 | Piece values | +150-200 | +150-200 (70% win rate) | ⏳ Validating |
| v4.1 | +MVV-LVA, Passed pawns | +240-380 | TBD | 📋 Planned |
| v4.2 | +King safety, Openings | +270-450 | TBD | 📋 Planned |
| v5.0 | +Search extensions | +370-650 | TBD | 📋 Planned |

---

## 🛠️ Implementation Best Practices

### One Change at a Time
- Make ONE improvement per iteration
- Test immediately
- Document results
- Keep if win rate > 55%, revert otherwise

### Version Control
- Commit each successful improvement
- Tag major versions (v4.0, v4.1, etc.)
- Keep baseline versions for comparison
- Write clear commit messages

### Testing Protocol
1. Make change to `engine_v4.py`
2. Run quick test (10 games)
3. If promising (>55%), run 100-game validation
4. If successful, commit
5. Update ENGINE_IMPROVEMENTS.md
6. Move to next improvement

### Documentation
- Update ENGINE_IMPROVEMENTS.md after each iteration
- Document failed experiments (what NOT to do)
- Track Elo estimates
- Note observations and insights

---

## 🔍 Debugging & Troubleshooting

### If Tournament Fails:
```bash
# Test engine loads correctly
python -c "import engine_v4; e = engine_v4.ChessEngine(); print('OK')"

# Run single game manually
python main.py

# Check for syntax errors
python -m py_compile engine_v4.py
```

### If Results Unclear:
```bash
# List all matches
ls -ltr games/engine_v3_vs_engine_v4/

# View specific game
cat games/engine_v3_vs_engine_v4/match_*/game_001.pgn

# Check JSON summary
cat games/engine_v3_vs_engine_v4/match_*/match_summary.json
```

### If Performance Regresses:
- Revert last change
- Profile code to find bottleneck
- Consider different approach
- Test with simpler version first

---

## 📚 Resources & References

### Chess Programming Wiki
- Piece-Square Tables
- Move Ordering
- Search Extensions
- Evaluation Function Design

### Recommended Reading
- "Chess Programming" by François Dominic Laramée
- Stockfish source code (for inspiration)
- Chessprogramming Wiki (extensive resource)

### Tools
- `python-chess` documentation
- Lichess analysis board (test positions)
- Arena Chess GUI (if UCI support added)

---

## ✅ Quick Reference Commands

### Run Tests
```bash
# Quick 10-game test
python tournament.py --quick --engine1 engine_v3 --engine2 engine_v4

# Full 100-game test
python tournament.py --engine1 engine_v3 --engine2 engine_v4 --games 100 --depth1 3 --depth2 3 --time 0.1

# Visual tournament
python tournament_gui.py
```

### View Results
```bash
# Latest match
python results_viewer.py games/engine_v3_vs_engine_v4/match_*/ | tail -n 50

# Export to JSON and CSV
python results_viewer.py games/engine_v3_vs_engine_v4/match_*/ --export-all
```

### Git Workflow
```bash
# Check status
git status

# Commit improvement
git add engine_v4.py ENGINE_IMPROVEMENTS.md
git commit -m "feat: improve engine v4 with [DESCRIPTION]"

# Tag version
git tag v4.1
git push origin main --tags
```

---

## 📝 Notes

### Key Insights from v4.0:
- Piece value tuning is VERY impactful (70% win rate!)
- Queen was significantly overvalued at 975
- Small changes can have large effects
- Fast testing (0.1s/move, depth 3) works well for validation
- 100 games provides good statistical confidence

### Lessons Learned:
- Always test one change at a time
- Start with simple, high-impact changes
- Don't skip quick tests (saves time)
- Document everything (easy to forget what worked)
- Be willing to revert unsuccessful changes

---

**Last Updated:** 2025-12-15
**Status:** Ready for Iteration 2 (MVV-LVA)
**Current Engine Strength:** v4.0 (~+150-200 Elo over v3.0)
**Target:** v5.0 (~+400-600 Elo over v3.0)

---

*This roadmap will be updated as improvements are implemented and new ideas emerge.*
