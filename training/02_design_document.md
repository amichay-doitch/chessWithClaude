# Chess ML Engine - Design Document

## 1. Overview
[Brief description of goal and approach]

---

## 2. Data

### 2.1 Data Structure
[What each record contains]

### 2.2 Data Collection
[How we generate games]

### 2.3 Data Volume
[How many games needed, when to generate more]

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

### 3.6 Threats & Attacks
- In check?
- Pieces under attack
- Pieces attacking enemy pieces
- **Tempo / Initiative** - who is attacking, who is defending

### 3.7 Tactics
- Forks (piece attacking 2+ enemy pieces)
- Skewers (attack through valuable piece to piece behind)
- Discovered attacks (moving piece reveals attack from another)
- Double check (two pieces giving check)
- Trapped pieces (no safe escape squares)
- Hanging pieces (undefended, can be captured for free)
- X-ray attacks (attacks through pieces along lines)
- **Battery attacks** - two rooks on same file, or queen+rook, queen+bishop on diagonal
- **Overloaded pieces** - piece defending too many things

### 3.8 Strategic Features

**For Model 1 (Classical ML) - clear, countable features:**
- Open vs closed position (number of open/semi-open files)
- Bishop pair advantage
- Rook on open file / 7th rank
- Space advantage (squares controlled beyond 4th rank)
- Pawn majority (kingside/queenside)
- Control of open/semi-open files
- **Color complex control** - control of light/dark squares

**For Model 2 (Neural Network) - more nuanced patterns:**
- Good bishop vs bad bishop (pawns blocking bishop's color)
- Piece coordination (pieces supporting each other)
- Weak squares (can't be defended by pawns)
- Blockade (piece blocking passed pawn)
- Knight vs Bishop (which is better in current position)

*Note: Neural network can learn subtle patterns from raw board representation. Classical ML needs explicit feature engineering.*

### 3.9 Dynamic Features
- Repetition count (approaching draw?)
- 50-move rule counter
- Last move was capture/check? (momentum)
- Who to move (tempo)

### 3.10 Board Representation

**For Model 1 (Classical ML):**
- Feature vector of all above (some binary, some numeric)
- Total ~50-100 features

**For Model 2 (Neural Network):**
- Input planes like AlphaZero (8x8x12 channels for pieces)
- History of positions (for repetition detection)
- **HalfKP features** (king position + piece positions relative to king) - used in Stockfish NNUE

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
