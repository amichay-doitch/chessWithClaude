"""
Game Recorder - PGN generation and storage for tournament games
"""

import chess.pgn
import chess.engine
import os
import json
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple


class GameRecorder:
    """Records tournament games in PGN format with metadata."""

    def __init__(self, output_dir: str = "games"):
        """
        Initialize game recorder.

        Args:
            output_dir: Base directory for saving games
        """
        self.output_dir = Path(output_dir)
        self.current_match_dir: Optional[Path] = None
        self.match_metadata: Dict[str, Any] = {}
        self.games_recorded = 0

    def start_match(self, engine1_name: str, engine2_name: str,
                   depth1: int, depth2: int, time_control: Optional[float] = None,
                   num_games: int = 100) -> Path:
        """
        Start a new match and create directory structure.

        Args:
            engine1_name: Name of first engine (e.g., "engine_v3")
            engine2_name: Name of second engine (e.g., "engine_v4")
            depth1: Search depth for engine 1
            depth2: Search depth for engine 2
            time_control: Time limit per move in seconds
            num_games: Total number of games in match

        Returns:
            Path to match directory
        """
        # Create match directory name
        match_name = f"{engine1_name}_vs_{engine2_name}"
        timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
        match_dir_name = f"match_{timestamp}"

        # Create directory structure
        self.current_match_dir = self.output_dir / match_name / match_dir_name
        self.current_match_dir.mkdir(parents=True, exist_ok=True)

        # Store match metadata
        self.match_metadata = {
            "engine1": engine1_name,
            "engine2": engine2_name,
            "depth1": depth1,
            "depth2": depth2,
            "time_control": time_control,
            "num_games": num_games,
            "start_time": datetime.now().isoformat(),
            "games": []
        }

        self.games_recorded = 0

        return self.current_match_dir

    def record_game(self, board: chess.Board, game_number: int,
                   white_engine: str, black_engine: str,
                   result: str, termination: str = "normal",
                   white_stats: Optional[Dict[str, Any]] = None,
                   black_stats: Optional[Dict[str, Any]] = None,
                   move_annotations: Optional[List[Tuple]] = None) -> Path:
        """
        Record a single game in PGN format.

        Args:
            board: Chess board with complete game
            game_number: Game number in the match
            white_engine: Name of engine playing white
            black_engine: Name of engine playing black
            result: Game result ("1-0", "0-1", "1/2-1/2")
            termination: How game ended (normal, timeout, error, etc.)
            white_stats: Statistics for white engine (avg nodes, time, etc.)
            black_stats: Statistics for black engine

        Returns:
            Path to saved PGN file
        """
        if not self.current_match_dir:
            raise ValueError("No active match. Call start_match() first.")

        # Create PGN game
        game = chess.pgn.Game()

        # Set standard headers
        game.headers["Event"] = f"Engine Match {self.match_metadata['engine1']} vs {self.match_metadata['engine2']}"
        game.headers["Site"] = "Local"
        game.headers["Date"] = datetime.now().strftime("%Y.%m.%d")
        game.headers["Round"] = str(game_number)
        game.headers["White"] = f"{white_engine} (depth={self.match_metadata['depth1'] if white_engine == self.match_metadata['engine1'] else self.match_metadata['depth2']})"
        game.headers["Black"] = f"{black_engine} (depth={self.match_metadata['depth2'] if black_engine == self.match_metadata['engine2'] else self.match_metadata['depth1']})"
        game.headers["Result"] = result

        # Add time control if specified
        if self.match_metadata['time_control']:
            game.headers["TimeControl"] = f"{self.match_metadata['time_control']}+0"

        # Add custom metadata for ML training
        game.headers["Termination"] = termination

        if white_stats:
            game.headers["WhiteAvgNodes"] = str(int(white_stats.get('avg_nodes', 0)))
            game.headers["WhiteAvgTime"] = f"{white_stats.get('avg_time', 0):.3f}"

        if black_stats:
            game.headers["BlackAvgNodes"] = str(int(black_stats.get('avg_nodes', 0)))
            game.headers["BlackAvgTime"] = f"{black_stats.get('avg_time', 0):.3f}"

        # Add moves with annotations
        node = game
        temp_board = chess.Board()
        time_control = self.match_metadata.get('time_control')
        white_time = time_control * 60 if time_control else 0
        black_time = time_control * 60 if time_control else 0

        for i, move in enumerate(board.move_stack):
            search_result = None
            if move_annotations and i < len(move_annotations):
                ann_move, search_result, color = move_annotations[i]
                if ann_move != move:
                    search_result = None

            comment_parts = []
            if search_result:
                comment_parts.append(f"d={search_result.depth}")
                comment_parts.append(f"n={search_result.nodes_searched:,}")
                comment_parts.append(f"t={search_result.time_spent:.2f}s")
                if search_result.time_spent > 0:
                    nps = int(search_result.nodes_searched / search_result.time_spent)
                    comment_parts.append(f"nps={nps:,}")

            comment = ", ".join(comment_parts) if comment_parts else None
            node = node.add_variation(move, comment=comment)

            if search_result:
                cp = search_result.score
                pov_score = chess.engine.PovScore(chess.engine.Cp(cp), temp_board.turn)
                node.set_eval(pov_score, depth=search_result.depth)

            if time_control and search_result:
                if temp_board.turn == chess.WHITE:
                    white_time = max(0, white_time - search_result.time_spent)
                    node.set_clock(white_time)
                else:
                    black_time = max(0, black_time - search_result.time_spent)
                    node.set_clock(black_time)

            temp_board.push(move)

        opening_name, eco = self._detect_opening(temp_board)
        if opening_name:
            game.headers["Opening"] = opening_name
        if eco:
            game.headers["ECO"] = eco

        # Save to file
        filename = f"game_{game_number:03d}.pgn"
        filepath = self.current_match_dir / filename

        with open(filepath, 'w') as f:
            print(game, file=f, end="\n\n")

        # Update match metadata
        game_data = {
            "game_number": game_number,
            "white": white_engine,
            "black": black_engine,
            "result": result,
            "moves": len(board.move_stack),
            "termination": termination
        }

        if white_stats:
            game_data["white_stats"] = white_stats
        if black_stats:
            game_data["black_stats"] = black_stats

        self.match_metadata["games"].append(game_data)
        self.games_recorded += 1

        return filepath

    def save_match_summary(self, results: Dict[str, Any]) -> Path:
        """
        Save match summary with statistics.

        Args:
            results: Dictionary containing match statistics

        Returns:
            Path to summary JSON file
        """
        if not self.current_match_dir:
            raise ValueError("No active match. Call start_match() first.")

        # Combine metadata with results
        summary = {
            **self.match_metadata,
            "end_time": datetime.now().isoformat(),
            "results": results
        }

        # Save to JSON
        summary_file = self.current_match_dir / "match_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        # Also save to global match_results directory
        results_dir = self.output_dir / "match_results"
        results_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        global_summary = results_dir / f"results_{timestamp}.json"
        with open(global_summary, 'w') as f:
            json.dump(summary, f, indent=2)

        return summary_file

    def get_match_dir(self) -> Optional[Path]:
        """Get current match directory."""
        return self.current_match_dir

    def get_games_recorded(self) -> int:
        """Get number of games recorded in current match."""
        return self.games_recorded

    def _detect_opening(self, board: chess.Board) -> Tuple[Optional[str], Optional[str]]:
        """Detect opening name and ECO code."""
        if len(board.move_stack) < 2:
            return None, None

        temp = chess.Board()
        moves = []
        for i, move in enumerate(board.move_stack[:8]):
            moves.append(temp.san(move))
            temp.push(move)
            if i >= 3:
                break

        patterns = {
            ("e4", "e5"): ("King's Pawn", "C20"),
            ("e4", "c5"): ("Sicilian", "B20"),
            ("e4", "e6"): ("French", "C00"),
            ("e4", "c6"): ("Caro-Kann", "B10"),
            ("d4", "d5"): ("Queen's Pawn", "D00"),
            ("d4", "Nf6"): ("Indian", "A45"),
            ("c4",): ("English", "A10"),
            ("Nf3",): ("Reti", "A04"),
        }

        for pattern, (name, eco) in patterns.items():
            if len(moves) >= len(pattern):
                if all(moves[i] == pattern[i] for i in range(len(pattern))):
                    return name, eco
        return None, None
