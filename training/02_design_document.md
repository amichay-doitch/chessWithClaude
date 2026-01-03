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
[Algorithm - decision trees? gradient boosting?]

### 4.2 Policy (Move Selection)
[How model chooses a move]

### 4.3 Value (Position Evaluation)
[How model evaluates a position]

### 4.4 Training
[Training process]

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

### 6.1 Algorithm
[Which RL algorithm]

### 6.2 Reward
[What's the reward - only win? intermediate rewards?]

### 6.3 Self-play
[How model plays against itself]

### 6.4 Training Loop
[Full iteration process]

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
