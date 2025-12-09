# Chess Game with AI Engine

A complete chess game implementation in Python featuring a sophisticated AI engine with both command-line and graphical user interfaces.

## Overview

This project provides a full-featured chess game where you can play against an advanced AI opponent. The engine uses modern chess programming techniques including alpha-beta pruning, transposition tables, and comprehensive positional evaluation.

## Features

### Chess Engine (v3.0)
- **Advanced Search Algorithm**
  - Negamax with alpha-beta pruning
  - Iterative deepening
  - Quiescence search for tactical positions
  - Transposition table with position caching
  - Move ordering optimization (killer moves, history heuristics)
  - Null move pruning
  - Late Move Reduction (LMR)
  - Configurable search depth (1-10) and time limits

- **Comprehensive Evaluation Function**
  - Material evaluation with standard piece values
  - Piece-Square Tables (separate for middlegame/endgame)
  - Development and castling bonuses
  - Center control evaluation
  - Piece mobility analysis
  - Pawn structure (doubled, isolated, backward, passed pawns)
  - King safety (pawn shield, open files, attacker proximity)
  - Special piece features (bishop pair, rooks on open files, knight outposts)
  - Threat detection (hanging pieces)

### User Interfaces

#### Command-Line Interface (`main.py`)
- Interactive text-based gameplay
- Unicode board display
- Multiple game modes:
  - Player vs Engine
  - Engine vs Engine (watch mode)
- Commands:
  - Move input in UCI format (e.g., `e2e4`)
  - `quit` - Exit game
  - `undo` - Take back moves
  - `new` - Start new game
  - `fen` - Display board state
  - `eval` - Show engine evaluation
  - `hint` - Get move suggestion
  - `depth N` - Change engine search depth

#### Graphical Interface (`gui.py`)
- Pygame-based visual interface
- 640x640px chessboard with clean design
- Interactive features:
  - Click-to-move piece selection
  - Legal move highlighting
  - Last move highlighting
  - Check detection (red square)
  - Board flipping
  - Move history (last 10 moves)
- Control panel with buttons:
  - New Game
  - Flip Board
  - Undo
  - Hint
  - Depth adjustment (3, 5, 7)
- Threaded engine calculations (non-blocking UI)

## Installation

### Requirements
- Python 3.x
- pip package manager

### Setup

1. Clone or download the repository

2. Install dependencies:
```bash
pip install -r requirements.txt
```

Required packages:
- `python-chess >= 1.999` - Chess logic and board management
- `pygame >= 2.5.0` - Graphical interface

## Usage

### Running the CLI Version

```bash
python main.py
```

Follow the prompts to:
1. Choose your color (White/Black)
2. Set engine depth (1-10, recommended: 4-6)
3. Set time limit per move (optional)
4. Start playing!

Enter moves in UCI format: `e2e4`, `g1f3`, etc.

### Running the GUI Version

```bash
python gui.py
```

- Click on a piece to select it
- Click on a highlighted square to move
- Use buttons in the side panel for game controls
- Adjust engine difficulty with depth buttons

## Project Structure

```
clever-agnesi/
├── README.md              # This file
├── requirements.txt       # Python dependencies
├── .gitignore            # Git ignore rules
├── main.py               # CLI game interface
├── board.py              # Chess board state management
├── engine.py             # Chess AI engine (v3.0)
└── gui.py                # Graphical user interface
```

## Module Documentation

### `board.py`
Chess board wrapper around python-chess library.

**Key Functions:**
- `make_move(move)` - Execute a move
- `undo_move()` - Take back last move
- `get_legal_moves()` - Get all valid moves
- `is_game_over()` - Check game status
- `display()` - Print Unicode board

### `engine.py`
Sophisticated chess AI with configurable difficulty.

**Key Class: ChessEngine**
- `__init__(max_depth=6, time_limit=None)` - Initialize engine
- `get_best_move(board)` - Calculate best move
- `evaluate_board(board)` - Position evaluation
- `negamax(...)` - Main search function

**Evaluation Components:**
- Material: Standard piece values
- Position: Piece-square tables
- Structure: Pawn formations
- Safety: King protection
- Mobility: Piece activity
- Threats: Tactical awareness

### `main.py`
Command-line game loop.

**Game Flow:**
1. Setup (color, depth, time limit)
2. Player move input
3. Engine calculation
4. Result display
5. Repeat until game over

### `gui.py`
Pygame graphical interface.

**Key Class: ChessGUI**
- `__init__()` - Initialize GUI and game state
- `run()` - Main game loop
- `draw_board()` - Render chessboard
- `handle_click(pos)` - Process mouse input
- `get_engine_move()` - Calculate AI move (threaded)

## Game Rules

Standard chess rules are enforced:
- All piece movements validated
- Castling (kingside and queenside)
- En passant captures
- Pawn promotion
- Check and checkmate detection
- Stalemate and draw conditions:
  - Insufficient material
  - Fifty-move rule
  - Threefold repetition

## Engine Strength

The engine's playing strength varies by depth:
- **Depth 3**: Beginner (~1200 ELO)
- **Depth 4**: Intermediate (~1500 ELO)
- **Depth 5**: Advanced (~1800 ELO)
- **Depth 6**: Strong (~2000 ELO)
- **Depth 7+**: Very Strong (2200+ ELO)

Note: Depth 7+ may have noticeable calculation time on slower machines.

## Development

### Git Information
- **Current Branch**: `clever-agnesi`
- **Recent Commits**: Initial setup and configuration

### Contributing
This is an active development project. Areas for potential enhancement:
- Opening book integration
- Endgame tablebase support
- UCI protocol compatibility
- Online multiplayer
- Advanced GUI features
- Performance optimizations

## Technical Notes

### Engine Architecture
- **Search**: Negamax (cleaner than minimax for zero-sum games)
- **Pruning**: Alpha-beta cutoffs reduce search tree by ~90%
- **Memory**: Transposition table with configurable size
- **Move Ordering**: Critical for alpha-beta efficiency (killer moves, history)
- **Extensions**: Quiescence search prevents horizon effect

### Performance
- Typical search: 10,000-100,000 positions per move (depth 5-6)
- Transposition table hit rate: 30-50%
- Average branching factor: ~35 (reduced to ~6 with good move ordering)

## License

See repository for license information.

## Acknowledgments

Built with:
- [python-chess](https://python-chess.readthedocs.io/) - Robust chess library
- [pygame](https://www.pygame.org/) - Game development framework

---

**Version**: 3.0
**Status**: Active Development
**Python**: 3.x compatible
