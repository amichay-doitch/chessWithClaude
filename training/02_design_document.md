# Chess ML Engine - Design Document

## 1. Overview
[Brief description of goal and approach]

---

## 2. Data

### 2.1 Data Structure

Training data consists of **game trajectories** (sequences of positions) rather than isolated positions. This is essential for:
- **TD learning** (Temporal Difference) - updating V(s) based on V(s')
- **Advantage calculation** - V(new_position) - V(old_position)
- **Credit assignment** - propagating game result backward through moves

#### Game Record Schema

```python
TrainingGame:
  # Game-level metadata
  - game_id: str                    # Unique identifier (e.g., "20260107_selfplay_00042")
  - result: float                   # {1.0, 0.5, 0.0} from white's perspective
  - termination: str                # "checkmate" | "stalemate" | "insufficient_material" |
                                    # "fifty_move_rule" | "threefold_repetition"
  - total_plies: int                # Game length (half-moves)
  - source: str                     # "self-play" | "engine-match" | "external"
  - model_version: str              # Which model/engine generated this (e.g., "v1.0", "engine_v5")
  - timestamp: str                  # ISO format (e.g., "2026-01-07T14:30:00Z")
  - opening_name: str? (optional)   # ECO code if available (e.g., "Sicilian Defense")

  # Position sequence
  - positions: [
      {
        fen: str,                   # Full position (includes side to move, castling, en passant)
        move_played: str,           # UCI format (e.g., "e2e4", "e7e8q")
        ply: int,                   # Move number (0-indexed half-moves)

        # Optional metadata (if available from engine):
        search_depth: int?,         # Search depth used
        time_spent_ms: float?,      # Thinking time in milliseconds
        nodes_searched: int?,       # Number of nodes searched
      },
      ...
    ]
```

#### What Each Model Needs

**Critic (Position Evaluator):**
- Input: FEN → extract features
- Target: Game result (from side-to-move's perspective)
- Per position: `(fen, side_to_move, game_result)`

**Actor (Move Selector):**
- Input: FEN → extract features, generate legal moves
- Target: Move played + quality signal (from Critic)
- Per position: `(fen, move_played, advantage)`

#### Design Decisions

**Store raw FEN, compute features on-the-fly:**
- ✅ Small storage footprint
- ✅ Flexibility to change feature extraction
- ✅ Can experiment with different feature sets
- ⚠️ Slightly slower training (mitigated by caching)

**Alternative:** Pre-compute and store feature vectors
- Only if profiling shows feature extraction is a bottleneck
- Locks you into a specific feature set

**Do NOT store legal_moves per position:**
- Computed from FEN on-demand: `board = chess.Board(fen); legal_moves = list(board.legal_moves)`
- Saves ~30-50 moves × 4 bytes × 1M positions = 120-200 MB

### 2.2 Data Collection

#### Phase 1: Initial Validation (1,000 games)
**Goal:** Verify Critic can learn basic patterns (material advantage, checkmate vs stalemate)

**Method:**
- **Random move games** (fastest generation)
- Or **engine_v3 vs random** (slightly better quality)
- Games will be short (~20-50 moves), many decisive

**Why:** Quick sanity check before investing in large-scale data collection

#### Phase 2: First Real Training (10,000 games)
**Goal:** Train Critic to evaluate middlegame positions, train Actor for basic move selection

**Method:**
- **engine_v5 self-play** with reduced depth (depth=3)
- Or **mixed sources:** 50% engine_v5, 50% random
- Opening diversity: Use opening book or start from positions after 5 random moves

**Why:** Higher quality games than random, diverse positions

#### Phase 3: Production Training (100,000+ games)
**Goal:** Achieve competitive playing strength

**Method:**
- **Self-play with current best model** (RL iteration loop)
- Exploration: ε-greedy (ε=0.1-0.2) or softmax sampling
- Opening diversity: Opening book with 50+ variations

**Why:** RL learns from its own mistakes, progressively harder opponents

#### Data Generation Pipeline

```
1. Game Generator
   ├─ Initialize engines/models (white, black)
   ├─ Play game with exploration
   ├─ Record: (fen, move_played, ply) for each position
   └─ Save game result and metadata

2. Data Storage
   ├─ Format: JSON Lines (.jsonl) - one game per line
   ├─ Location: training/data/games_YYYYMMDD.jsonl
   └─ Append-only (no need to reload all data)

3. Data Loading (during training)
   ├─ Stream games from .jsonl (memory efficient)
   ├─ Extract features on-the-fly from FEN
   └─ Create training batches
```

#### Opening Diversity Strategy

**Problem:** Starting from standard position every game → deterministic engines play identical games

**Solutions:**
1. **Opening book** - Start from ~50 book positions (after 3-6 moves)
2. **Random starting moves** - Play 5-8 random legal moves before using engine
3. **Fischer Random Chess (Chess960)** - Randomized back rank

**Recommendation for Phase 1-2:** Random starting moves (simplest)
**Recommendation for Phase 3:** Opening book (more realistic)

### 2.3 Data Volume

#### Storage Requirements

**Per game estimate:**
- Average game length: 40 moves (80 plies)
- Per position: ~150 bytes (FEN + move + metadata)
- Per game: 80 × 150 bytes = 12 KB
- 1,000 games = 12 MB
- 10,000 games = 120 MB
- 100,000 games = 1.2 GB
- 1,000,000 games = 12 GB

**Conclusion:** Storage is NOT a constraint. Use raw FEN format.

#### Training Data Requirements

**For Gradient Boosting (Model 1):**

| Phase | Games | Positions | Storage | Purpose |
|-------|-------|-----------|---------|---------|
| Validation | 1,000 | ~40,000 | 12 MB | Verify learning works |
| Initial Training | 10,000 | ~400,000 | 120 MB | First real model |
| Production | 100,000 | ~4,000,000 | 1.2 GB | Competitive strength |
| Advanced | 1,000,000 | ~40,000,000 | 12 GB | Grandmaster level (aspirational) |

**Why RL is data-hungry:**
- Sparse reward (only game result, no intermediate feedback)
- High variance (same position can lead to win or loss)
- Need diverse positions (opening, middlegame, endgame)
- Need diverse tactics (forks, pins, sacrifices, etc.)

#### When to Generate More Data

**Triggers for collecting more games:**

1. **Model plateaus** - Win rate stops improving against baseline
2. **Overfitting** - Training accuracy high, validation accuracy low
3. **Narrow repertoire** - Model plays same openings/plans repeatedly
4. **Weak in specific phases** - Poor endgame play → need more endgame positions

**RL Training Loop:**
- Don't pre-generate all data!
- Generate data **iteratively** as model improves
- Each iteration: Play 1,000-10,000 games with current model
- Discard old data or weight recent games higher (curriculum learning)

#### Data Quality vs Quantity

**Better 10,000 high-quality games than 100,000 random games:**
- High quality = diverse, non-trivial, from competent play
- Random games are short, lack strategic depth
- Phase 1 uses random for quick validation only
- Phase 2+ uses engine/model-generated games

#### Data Augmentation

**Symmetry augmentation (8x data for free):**
- Flip board horizontally (a1 ↔ h1)
- Rotate 180° (swap colors, flip board)
- Works because chess board is symmetric

**Implementation:**
- Apply during feature extraction, not storage
- Each position becomes 8 training samples
- Effective data volume: Multiply by 8x

---

## 3. Features (Feature Engineering)

### 3.1 Material Features
- Piece count per type (pawn, knight, bishop, rook, queen) per side
- Total material advantage
- **Piece-Square Tables (PSQT)** - piece value based on position (knight in center > corner, rook on open file, etc.)
- Imbalances (bishop pair vs knight+pawns, queen vs 2 rooks, etc.)

### 3.2 Pawn Structure
- Doubled pawns (two pawns on same file)
- Isolated pawns (no friendly pawns on adjacent files)
- Connected pawns (pawns defending each other)
- Passed pawns (no enemy pawns blocking or attacking)
- **Backward pawns** - pawns behind others that can't advance safely (static weakness)
- **Pawn islands** - number of disconnected pawn groups (fewer = stronger structure)
- Promotion potential (distance to 8th rank)
- **Rule of the square** - can king catch passed pawn? (endgame)

### 3.3 Piece Activity
- Center control (central squares attacked)
- Piece mobility (legal moves per piece)
- Outposts (pieces on squares that can't be attacked by enemy pawns)
- Pinned pieces (can't move without exposing more valuable piece)
- **Connected rooks** (rooks defending each other on same rank/file)
- **Bishop on long diagonal** - control of key diagonals
- **Fianchettoed bishop** - bishop developed to b2/g2/b7/g7
- Knights/bishops on central vs corner squares
- Pieces developed from back rank
- **Queen activity** - centralized vs edge

### 3.4 King Safety
- Castling rights (can still castle kingside/queenside)
- King position (cornered and protected vs exposed in center)
- Pieces defending king zone
- Enemy pieces attacking king zone
- **Pawn shield** - pawns in front of castled king (how many, structure)
- **Pawn storm** - enemy pawns advancing toward king
- **Open files/diagonals toward king** - attack vectors
- **King escape squares** - safe squares for king to flee

### 3.5 Game Phase
- Opening / middlegame / endgame (based on material)
- Move number
- **King activity** (in endgame, active king is crucial)
- **Opposition** - king positions in pawn endgames

### 3.6 Endgame-Specific Features
- **King centralization score** - distance of king from center (active king is critical in endgames)
- **Pawn race calculation** - who promotes first if both sides push passed pawns
- **Key squares control** - control of squares on promotion path (e.g., for king to stop/support pawn)
- **Rook behind passed pawn** - rook supporting own passed pawn from behind (huge advantage), or rook behind enemy passed pawn (restrains it)
- **Wrong bishop + rook pawn** - bishop can't control promotion square (drawing pattern)
- **Fortress indicators** - defensive setup that holds despite material deficit
- **Zugzwang indicators** - positions where having to move is a disadvantage
- **Tablebase-like patterns** - known theoretical positions (KQvK, KRvK, etc.)

### 3.7 King Attack Features
- **King tropism** - sum of distances of attacking pieces to enemy king (closer = more dangerous)
- **Attacker count vs defender count** - ratio of pieces attacking king zone vs defending it
- **Back rank weakness** - vulnerability to back rank mate (no escape squares, no defenders)
- **Mating net indicators** - is king being cornered/trapped with few escape squares
- **Queen proximity to king** - queen near enemy king is dangerous
- **Safe checks available** - number of checking moves that don't lose the piece

### 3.8 Threats & Attacks
- In check?
- Pieces under attack
- Pieces attacking enemy pieces
- **Tempo / Initiative** - who is attacking, who is defending

### 3.9 Tactics
- Forks (piece attacking 2+ enemy pieces)
- Skewers (attack through valuable piece to piece behind)
- Discovered attacks (moving piece reveals attack from another)
- Double check (two pieces giving check)
- Trapped pieces (no safe escape squares)
- Hanging pieces (undefended, can be captured for free)
- X-ray attacks (attacks through pieces along lines)
- **Battery attacks** - two rooks on same file, or queen+rook, queen+bishop on diagonal
- **Overloaded pieces** - piece defending too many things
- **Deflection potential** - can a defender be lured away from its duty
- **Interference patterns** - can we block a defensive piece's line
- **Decoy opportunities** - can we lure a piece to a bad square
- **Clearance sacrifices** - clearing a square or line for another piece
- **Zwischenzug potential** - intermediate move opportunities before expected recapture

### 3.10 Piece Coordination
- **Development count** - number of pieces moved from starting squares
- **Undeveloped pieces** - pieces still on back rank (penalty)
- **Piece harmony** - pieces supporting each other vs blocking each other
- **Minor piece coordination** - bishop+knight working together (e.g., knight controls squares bishop can't)
- **Rooks connected** - both rooks on same rank/file with no pieces between
- **Rooks doubled** - both rooks on same file (powerful)
- **Queen-rook battery** - queen and rook aligned on file/rank
- **Queen-bishop battery** - queen and bishop aligned on diagonal
- **Knight on rim** - "knight on the rim is dim" (penalty for edge knights)
- **Centralized pieces** - pieces controlling center squares

### 3.11 Strategic Features

**For Model 1 (Classical ML) - clear, countable features:**
- Open vs closed position (number of open/semi-open files)
- Bishop pair advantage
- Rook on open file / 7th rank
- Space advantage (squares controlled beyond 4th rank)
- Pawn majority (kingside/queenside)
- Control of open/semi-open files
- **Color complex control** - control of light/dark squares
- **Blockade** - piece blocking passed pawn (knight is best blocker)
- **Minority attack** - fewer pawns attacking pawn majority (creates weaknesses)
- **Weak color complex** - holes on one color (often due to bishop trade)
- **Outpost squares** - squares that can't be attacked by enemy pawns
- **Good knight vs bad bishop** - knight better in closed positions, bishop in open

**For Model 2 (Neural Network) - more nuanced patterns:**
- Good bishop vs bad bishop (pawns blocking bishop's color)
- Piece coordination (pieces supporting each other)
- Weak squares (can't be defended by pawns)
- Blockade (piece blocking passed pawn)
- Knight vs Bishop (which is better in current position)
- Prophylactic moves (preventing opponent's plans)
- Piece exchanges when ahead/behind

*Note: Neural network can learn subtle patterns from raw board representation. Classical ML needs explicit feature engineering.*

### 3.12 Dynamic Features
- Repetition count (approaching draw?)
- 50-move rule counter
- Last move was capture/check? (momentum)
- Who to move (tempo)
- **Recent captures** - sequence of captures (exchanges happening)
- **Tension in position** - pieces attacking each other but not capturing yet

### 3.13 Board Representation

**For Model 1 (Classical ML):**
- Feature vector of all above (some binary, some numeric)
- Total ~100-150 features (expanded from original estimate)
- Features should be normalized (0-1 range or standardized)

**For Model 2 (Neural Network):**
- Input planes like AlphaZero (8x8x12 channels for pieces)
- History of positions (for repetition detection)
- **HalfKP features** (king position + piece positions relative to king) - used in Stockfish NNUE
- Attack/defense maps as additional planes

---

## 4. Model 1 - Classical ML

### 4.1 Architecture

Two separate **Gradient Boosting** models (Actor-Critic pattern):
- **Actor model** - for move selection (Policy)
- **Critic model** - for position evaluation (Value)

Why Gradient Boosting:
- Works well with hand-crafted features
- Fast inference (important for real-time play)
- Easy to interpret and debug
- No GPU required

### 4.2 Policy (Move Selection) - Actor

**Input:** Feature vector of current position + candidate move
**Output:** Score for how good this move is

**How it works:**
1. Generate all legal moves
2. For each move, create features of resulting position
3. Actor scores each (position, move) pair
4. Choose move with highest score (or sample probabilistically for exploration)

**Training:**
- Moves from winning games get positive signal
- Moves from losing games get negative signal
- Critic's evaluation helps refine the signal

### 4.3 Value (Position Evaluation) - Critic

**Input:** Feature vector of position
**Output:** Number between 0-1 (expected game result from this position)

**How it works:**
1. Extract features from current position
2. Critic outputs evaluation (0 = losing, 0.5 = equal, 1 = winning)

**Training:**
- TD(λ) learning - update based on difference between predicted value and actual outcome
- Learn from game results, propagate backwards through positions

### 4.4 Training

**Training Loop:**
1. Play games using current Actor (with exploration)
2. Collect (position, move, result) tuples
3. Update Critic using TD learning on position values
4. Update Actor using Critic's feedback on move quality
5. Repeat

---

## 5. Model 2 - Neural Network

### 5.1 Architecture
[Network structure]

### 5.2 Policy Network
[Network for move selection]

### 5.3 Value Network
[Network for position evaluation]

### 5.4 Training
[Training process]

---

## 6. Reinforcement Learning

### 6.1 Algorithm: Actor-Critic

We use **Actor-Critic** - two models working together:

**Actor (Policy):**
- Chooses moves
- "What's the best move?"

**Critic (Value):**
- Evaluates positions
- "How good is this position?"

**How they work together:**
1. Actor chooses a move
2. We reach a new position
3. Critic evaluates: "new position is better/worse than expected"
4. Actor learns: "the move I chose was good/bad" (based on Critic's feedback)
5. Critic learns: "my evaluation was accurate/inaccurate" (based on game result)

**Why Actor-Critic:**
- Actor doesn't need to wait until game end to learn
- Critic gives immediate feedback on each move
- Solves the credit assignment problem - if Critic says "position got worse", Actor knows last move was bad

### 6.2 Reward

**Sparse reward (game result only):**
- Win = 1, Loss = 0, Draw = 0.5
- No intermediate rewards

**The Credit Assignment Problem:**
- Game ends after 40 moves in a loss
- Move 5 was excellent, move 35 was the blunder
- Both get "labeled" as loss

**Solution:** The Critic solves this by learning position values over many games. Good moves will appear in winning positions more often, bad moves in losing positions.

### 6.3 Self-play

The model improves by playing against itself:

1. **Current best model** plays as both white and black
2. Games are played with some **exploration** (not always choosing the "best" move)
3. All positions and moves are recorded
4. After batch of games, models are updated
5. New model becomes "current best" if it's stronger

**Exploration strategies:**
- ε-greedy: with probability ε, choose random move instead of best
- Softmax: sample moves proportionally to their scores
- Add noise to evaluations

### 6.4 Training Loop

**Full training iteration:**

```
1. PLAY PHASE
   - Play N games (self-play)
   - Record: (position, move, game_result) for each move

2. LEARN PHASE
   - Update Critic:
     * For each position, target = actual game result
     * Minimize prediction error using TD(λ)
   - Update Actor:
     * For each (position, move), compute advantage = Critic(new_pos) - Critic(old_pos)
     * If advantage > 0: reinforce this move
     * If advantage < 0: discourage this move

3. EVALUATE PHASE
   - New model plays against old model
   - If win rate > threshold: accept new model
   - Otherwise: keep old model

4. REPEAT
```

**Key hyperparameters:**
- Games per iteration
- Learning rate
- Exploration rate (decay over time)
- TD(λ) lambda value

---

## 7. System Integration

### 7.1 Engine Interface
[How new engine integrates with engine pool]

### 7.2 Model Persistence
[How to save and load models]

---

## 8. Evaluation

### 8.1 Metrics
[How we measure success]

### 8.2 Tournaments
[Games against other engines]

---

## 9. Development Phases

### Phase 1: [Description]
### Phase 2: [Description]
### Phase 3: [Description]

---

## 10. Open Questions
[Things to decide]
