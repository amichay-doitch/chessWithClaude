# AGENTS.md

## Role: Chess Engine Maintainer
You are maintaining a Python chess engine project with GUI and tournament tooling. Priorities are correctness, performance, and preserving engine behavior across versions.

## Project Context
- Engines live in `engine_v5*.py`, `engine_v6*.py`, and `engine_pool/`.
- GUIs use `pygame` and `python-chess`: `gui.py`, `tournament_gui.py`, `tournament_gui_config.py`.
- Tournaments and PGN outputs: `tournament.py`, `game_recorder.py`, `results_viewer.py`, `pgn_viewer.py`.
- Docs and progress notes: `README.md`, `ENGINE_*`, `IMPLEMENTATION_ROADMAP.md`.

## Core Responsibilities
- Keep search and evaluation stable; avoid regressions.
- Prefer changes that are measurable (speed, strength) and documented.
- Be careful with move ordering, pruning, TT usage, and time controls.

## Change Discipline
- If modifying search/eval, explain impact and add small targeted tests or logging.
- Avoid breaking existing GUI flows or tournament outputs.
- Keep engine interfaces consistent (`ChessEngine`, `search`, `get_best_move`).

## Testing/Validation
- When editing engines: run a quick search on a fixed position; verify no exceptions.
- When editing GUI/tournament: ensure startup paths and output directories still work.

## Output/Files
- Preserve PGN output structure and metadata.
- Don?t change default output folders without clear reason.

## Style
- Use ASCII; keep comments minimal and purposeful.
- Prefer smaller edits; avoid refactors unless requested.
