# Repository Summary

This repository is a comprehensive Python-based platform for developing, testing, and playing against chess engines.

## Project Structure Overview

The project is organized into several key areas:

- **Chess Engines**: Multiple versions of the chess engine exist (`engine.py`, `engine_v3.py`, `engine_v4.py`, `engine_v5.py`). The development process encourages creating new, improved engine versions.
- **Core Logic**: `board.py` acts as a wrapper around the `python-chess` library, managing the game state and board operations.
- **User Interfaces**:
    - `main.py`: A command-line interface (CLI) for playing against the engine. It supports features like choosing sides, setting engine depth, and getting hints.
    - `gui.py`: A graphical user interface (GUI) built with `pygame` for a more visual gameplay experience.
    - `pgn_viewer.py`: A tool for replaying and analyzing games saved in PGN format.
    - `results_viewer.py`: A utility for viewing and analyzing tournament results.
- **Tournament and Testing**:
    - `tournament.py`: A headless script to run automated tournaments between different engine versions.
    - `game_recorder.py`: Saves tournament games as PGN files and match results in JSON format.
- **Game Data**: The `games/` directory stores the history of tournament matches, including PGN files and match summaries.
- **Configuration and Documentation**:
    - `CODEBASE_OVERVIEW.md`: Provides a high-level overview of the project components.
    - `requirements.txt`: Lists the necessary Python dependencies.

## How It Works

The application can be run in several modes:

1. **Player vs. Engine (CLI)**: Executing `main.py` starts a game in the console. The user can play against the default engine (`engine.py`).
2. **Player vs. Engine (GUI)**: Running `gui.py` launches a `pygame` window for graphical gameplay.
3. **Engine vs. Engine (Self-Play)**: Running `main.py --self` pits the engine against itself.
4. **Tournaments**: The `tournament.py` script is used to systematically test different engines against each other to evaluate performance improvements.

## Development Workflow

The intended development cycle is as follows:

1. **Improve an Engine**: Create a new engine file (e.g., `engine_v6.py`) with enhanced AI logic, evaluation functions, or search algorithms.
2. **Test in a Tournament**: Use `tournament.py` to run a series of games between the new engine and existing ones.
3. **Analyze Results**: Use `results_viewer.py` and `pgn_viewer.py` to analyze the outcomes and determine if the changes led to a stronger engine.

This structured approach allows for iterative and data-driven improvements to the chess-playing AI.
# Repository Summary

This repository is a comprehensive Python-based platform for developing, testing, and playing against chess engines.

## Project Structure Overview

The project is organized into several key areas:

- **Chess Engines**: Multiple versions of the chess engine exist (`engine.py`, `engine_v3.py`, `engine_v4.py`, `engine_v5.py`). The development process encourages creating new, improved engine versions.
- **Core Logic**: `board.py` acts as a wrapper around the `python-chess` library, managing the game state and board operations.
- **User Interfaces**:
    - `main.py`: A command-line interface (CLI) for playing against the engine. It supports features like choosing sides, setting engine depth, and getting hints.
    - `gui.py`: A graphical user interface (GUI) built with `pygame` for a more visual gameplay experience.
    - `pgn_viewer.py`: A tool for replaying and analyzing games saved in PGN format.
    - `results_viewer.py`: A utility for viewing and analyzing tournament results.
- **Tournament and Testing**:
    - `tournament.py`: A headless script to run automated tournaments between different engine versions.
    - `game_recorder.py`: Saves tournament games as PGN files and match results in JSON format.
- **Game Data**: The `games/` directory stores the history of tournament matches, including PGN files and match summaries.
- **Configuration and Documentation**:
    - `CODEBASE_OVERVIEW.md`: Provides a high-level overview of the project components.
    - `requirements.txt`: Lists the necessary Python dependencies.

## How It Works

The application can be run in several modes:

1. **Player vs. Engine (CLI)**: Executing `main.py` starts a game in the console. The user can play against the default engine (`engine.py`).
2. **Player vs. Engine (GUI)**: Running `gui.py` launches a `pygame` window for graphical gameplay.
3. **Engine vs. Engine (Self-Play)**: Running `main.py --self` pits the engine against itself.
4. **Tournaments**: The `tournament.py` script is used to systematically test different engines against each other to evaluate performance improvements.

## Development Workflow

The intended development cycle is as follows:

1. **Improve an Engine**: Create a new engine file (e.g., `engine_v6.py`) with enhanced AI logic, evaluation functions, or search algorithms.
2. **Test in a Tournament**: Use `tournament.py` to run a series of games between the new engine and existing ones.
3. **Analyze Results**: Use `results_viewer.py` and `pgn_viewer.py` to analyze the outcomes and determine if the changes led to a stronger engine.

This structured approach allows for iterative and data-driven improvements to the chess-playing AI.
# Codebase Overview

This project is a Python-based platform for developing and testing chess engines.

## Key Components

*   **Chess Engines:**
    *   `engine.py`: The baseline chess engine (v3.0) with core AI logic, including static evaluation and alpha-beta search.
    *   `engine_v4.py`: An improved version of the engine with tuned piece values.

*   **Core Logic:**
    *   `board.py`: A wrapper around the `python-chess` library for managing the game state.

*   **Testing & Analysis:**
    *   `tournament.py`: A headless tournament runner for automated engine vs. engine testing.
    *   `game_recorder.py`: Saves tournament games (PGN) and results (JSON) for analysis.

*   **User Interfaces:**
    *   `gui.py`: A `pygame`-based graphical interface for playing against the chess engine. **Note:** It currently uses the baseline `engine.py`.
    *   `main.py`: A simple command-line interface for playing against the engine.
    *   `pgn_viewer.py`: A tool for replaying and analyzing saved PGN files.
    *   `results_viewer.py`: A tool for viewing and analyzing tournament results.

## Development Workflow

The typical workflow involves:
1.  Making improvements to a chess engine (e.g., creating a new `engine_v5.py`).
2.  Running tournaments to test the new engine against existing ones.
3.  Analyzing the results to validate the improvements.
