# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project: Chess Engine Development with ML Training

A chess ecosystem with two parallel development tracks:
1. **Traditional engines** (v3-v6) - Hand-crafted evaluation functions
2. **ML engines** (in development) - Reinforcement Learning with Actor-Critic architecture

## Architecture Overview

### Engine Pool Structure
All engines inherit from a common interface and are located in `engine_pool/`:
- **engine_v3.py** - Baseline engine (negamax + alpha-beta)
- **engine_v4.py** - Tuned piece values (+150 Elo over v3)
- **engine_v5_fast.py** - v5 with Numba JIT optimization (2-3x faster)
- **engine_v5_optimized.py, engine_v6*.py** - Experimental variants
- **stockfishSonChessEngine.py** - Stockfish wrapper with dual time+depth limits
- **gemini.py** - Experimental Gemini integration

**Key shared code:**
- `engine_base.py` - Common data structures (SearchResult, TTEntry), constants, utilities
- All engines implement: `get_move(board, depth=5, time_limit=None)`

### Tournament System
Three tournament interfaces share the same backend (`tournament.py`):
1. **tournament_gui_config.py** - Interactive GUI with pre-game setup (recommended)
2. **tournament.py** - CLI for batch testing
3. **tournament_gui.py** - Legacy GUI

**Game recording:** `game_recorder.py` saves all games as PGN with metadata

### Test Infrastructure
- **test_suite_interactive.py** - Visual GUI for testing engines on tactical positions
- **test_suite.py** - Core test suite logic with position database
- **stockfish_analyzer.py** - Stockfish integration for position analysis

## Common Development Commands

**Python path for this project:**
```
C:/Users/AmichayDeutsch/miniconda3/envs/chessWithClaude/python.exe
```

### Running Tournaments

**Quick test (10 games, ~1 min):**
```bash
python tournament.py --engine1 engine_pool.engine_v3 --engine2 engine_pool.engine_v5_fast --games 10 --depth1 3 --depth2 3 --time1 0.1 --time2 0.1
```

**Full validation (100 games):**
```bash
python tournament.py --engine1 engine_pool.engine_v3 --engine2 engine_pool.engine_v5_fast --games 100 --depth1 5 --depth2 5 --time1 0.5 --time2 0.5
```

**GUI tournament with configuration:**
```bash
python tournament_gui_config.py
```

**Stockfish benchmarking:**
```bash
python tournament.py --engine1 engine_pool.stockfishSonChessEngine --engine2 engine_pool.engine_v5_fast --games 2 --time1 0.01 --time2 0.5 --depth1 1 --depth2 10
```

### Testing Engines

**Interactive test suite (recommended):**
```bash
python test_suite_interactive.py
```
Visual GUI for testing engines on curated tactical positions with Stockfish comparison.

**View results:**
```bash
python results_viewer.py games/engine_v3_vs_engine_v5_fast/match_*/
```

### Playing Games

**GUI (player vs engine):**
```bash
python gui.py
```

**PGN viewer (replay games):**
```bash
python pgn_viewer.py
```

## Engine Development Workflow

### For Traditional Engines (v3-v6)

1. **Make ONE change at a time** to evaluation or search
2. Run quick test (10 games): `python tournament.py --quick --engine1 ... --engine2 ...`
3. If win rate > 55%, run full validation (100 games)
4. If successful, commit with clear message
5. Document in `md_files/ENGINE_IMPROVEMENTS.md`

**Success criteria:**
- 55% win rate = +35 Elo (minimum improvement)
- 60% = +70 Elo (strong)
- 70% = +150 Elo (excellent - v4 achieved this)

### For ML Engines (Actor-Critic RL)

**Current Status:** Design phase - implementing Model 1 (Classical ML with Gradient Boosting)

**Key Design Documents:**
- `training/02_design_document.md` - Full design (English)
- `training/02_design_document_hebrew.md` - Full design (Hebrew)
- `training/03_next_session_plan.md` - Next steps and current status
- `docs/ml_engine_overview.md` - High-level overview

**Architecture Decisions:**
- **Model 1 (Classical ML):** Two Gradient Boosting models (Actor + Critic)
- **Model 2 (Neural Network):** To be implemented after Model 1
- **RL Approach:** Actor-Critic with sparse rewards (game result only)
- **Features:** Extracted from engine5's evaluation, no Stockfish (pure RL)
- **Actor (Policy):** Scores moves, chooses best action
- **Critic (Value):** Evaluates positions (0=loss, 0.5=draw, 1=win)

**Planned Code Structure:**
```
training/
  data/              # game data storage
  models/            # saved models
  src/
    feature_extractor.py   # Extract features from chess.Board
    data_collector.py      # Generate training data
    critic_model.py        # Position evaluation model
    actor_model.py         # Move selection model
    trainer.py             # RL training loop
```

**Next Implementation Steps (from 03_next_session_plan.md):**
1. Create feature extractor (material, mobility, king safety, pawn structure)
2. Build data collection pipeline
3. Train simple Critic model on sample data
4. Create ML engine that uses Critic for evaluation
5. Verify it beats random engine >80%

## Critical Integration Points

### Adding New Engines to Pool

1. Create engine in `engine_pool/` with class `ChessEngine`
2. Implement: `__init__(self, max_depth=5, time_limit=None, **kwargs)`
3. Implement: `get_move(self, board) -> chess.Move`
4. Optionally return `SearchResult` with metadata
5. Test with: `python tournament.py --engine1 engine_pool.your_engine --engine2 engine_pool.engine_v3 --games 10`

### Stockfish Integration

**Special handling:** `stockfishSonChessEngine.py` enforces BOTH depth AND time limits
- Uses custom `go` command: UCI doesn't natively support dual limits
- Implementation: `tournament.py:64-77` for parameter setup
- Critical for fair comparisons with time-constrained engines

### ML Engine Integration

ML engines will:
- Use feature extractor to convert `chess.Board` → feature vector
- Call Critic model for position evaluation
- Call Actor model to score legal moves
- Plug into tournament system like traditional engines

## Session End Protocol

Before ending any session:
1. Update design docs if architectural decisions were made
2. Update `training/03_next_session_plan.md` with:
   - What was completed
   - Current state
   - Next steps
   - Open questions
3. Commit and push all changes with descriptive messages

## Language Preference

- **Code and technical docs:** English
- **Discussion:** Hebrew or English (user preference)
- **Design docs:** Both languages, keep synchronized (`02_design_document.md` + `02_design_document_hebrew.md`)

## Dependencies

From `requirements.txt`:
- `python-chess>=1.999` - Chess logic and board management
- `pygame>=2.5.0` - GUI interfaces
- `pyyaml>=6.0` - Configuration
- `stockfish==4.0.3` - Stockfish engine integration

**For ML development (to be added):**
- scikit-learn (Gradient Boosting)
- numpy (feature vectors)

## Key Files for Context

**When working on traditional engines:**
- `engine_base.py` - Shared constants and utilities
- `md_files/ENGINE_IMPROVEMENTS.md` - Development history
- `md_files/TOURNAMENT_GUIDE.md` - Tournament system details

**When working on ML engines:**
- `training/02_design_document.md` - Complete architecture
- `training/03_next_session_plan.md` - Current status and next steps
- `engine_v5.py` or `engine_v5_fast.py` - Reference for features to extract

**When debugging:**
- `test_suite_interactive.py` - Visual testing on tactical positions
- `results_viewer.py` - Analyze tournament performance
