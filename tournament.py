"""
Tournament Runner - CLI interface for running engine vs engine matches
"""

import argparse
import chess
import time
import importlib
import os
from typing import Dict, Any, Optional, List
from pathlib import Path
from game_recorder import GameRecorder


# Enable ANSI colors on Windows
if os.name == 'nt':
    os.system('')  # Enables ANSI escape sequences in Windows terminal


# ANSI color codes
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    # Piece colors
    WHITE_PIECE = '\033[97m'  # Bright white
    BLACK_PIECE = '\033[33m'  # Yellow/gold for black pieces
    # Square colors (background)
    LIGHT_SQUARE = '\033[48;5;180m'  # Light tan background
    DARK_SQUARE = '\033[48;5;94m'    # Brown background
    # Move info colors
    WHITE_MOVE = '\033[96m'   # Cyan for white's move
    BLACK_MOVE = '\033[93m'   # Yellow for black's move


def print_colored_board(board: chess.Board) -> None:
    """Print the chess board with colored pieces and squares."""
    piece_symbols = {
        'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
        'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟',
    }

    print()
    for rank in range(7, -1, -1):
        row = f" {rank + 1} "
        for file in range(8):
            square = chess.square(file, rank)
            piece = board.piece_at(square)

            # Determine square color
            is_light = (rank + file) % 2 == 1
            bg_color = Colors.LIGHT_SQUARE if is_light else Colors.DARK_SQUARE

            if piece:
                # Determine piece color
                piece_color = Colors.WHITE_PIECE if piece.color == chess.WHITE else Colors.BLACK_PIECE
                symbol = piece_symbols.get(piece.symbol(), piece.symbol())
                row += f"{bg_color}{piece_color}{Colors.BOLD} {symbol} {Colors.RESET}"
            else:
                row += f"{bg_color}   {Colors.RESET}"

        print(row)

    print("    a  b  c  d  e  f  g  h")


class TournamentRunner:
    """Runs tournaments between two chess engines."""

    def __init__(self, engine1_module: str, engine2_module: str,
                 depth1: int = 5, depth2: int = 5,
                 time1: Optional[float] = None,
                 time2: Optional[float] = None,
                 num_games: int = 100,
                 output_dir: str = "games",
                 quiet: bool = False,
                 random_level1: Optional[float] = None,
                 random_level2: Optional[float] = None,
                 present: bool = False):
        """
        Initialize tournament runner.

        Args:
            engine1_module: Module name for engine 1 (e.g., "engine_v3")
            engine2_module: Module name for engine 2 (e.g., "engine_v4")
            depth1: Search depth for engine 1 (used with randomness mode)
            depth2: Search depth for engine 2 (used with randomness mode)
            time1: Time per move for engine 1 in seconds (time-based mode)
            time2: Time per move for engine 2 in seconds (time-based mode)
            num_games: Number of games to play
            output_dir: Directory for saving games
            quiet: Minimize output
            random_level1: Randomness level for engine 1 (0-1, uses depth-based search)
            random_level2: Randomness level for engine 2 (0-1, uses depth-based search)
            present: Show board after every move with move number and engine name
        """
        self.engine1_module = engine1_module
        self.engine2_module = engine2_module
        self.depth1 = depth1
        self.depth2 = depth2
        self.time1 = time1
        self.time2 = time2
        self.random_level1 = random_level1
        self.random_level2 = random_level2
        self.num_games = num_games
        self.quiet = quiet
        self.present = present

        # Create descriptive names for engines (include time/randomness if specified)
        self.engine1_display_name = self._create_engine_name(engine1_module, time1, random_level1, depth1)
        self.engine2_display_name = self._create_engine_name(engine2_module, time2, random_level2, depth2)

        # Load engines
        print(f"Loading engines: {self.engine1_display_name} vs {self.engine2_display_name}...")
        mod1 = importlib.import_module(engine1_module)
        mod2 = importlib.import_module(engine2_module)

        # Prepare engine 1 kwargs
        engine1_kwargs = {'max_depth': depth1}
        if time1 is not None:
            engine1_kwargs['time_limit'] = time1
        if random_level1 is not None:
            engine1_kwargs['randomness_config'] = self._random_level_to_config(random_level1)

        # Prepare engine 2 kwargs
        engine2_kwargs = {'max_depth': depth2}
        if time2 is not None:
            engine2_kwargs['time_limit'] = time2
        if random_level2 is not None:
            engine2_kwargs['randomness_config'] = self._random_level_to_config(random_level2)

        self.engine1 = mod1.ChessEngine(**engine1_kwargs)
        self.engine2 = mod2.ChessEngine(**engine2_kwargs)

        # Initialize recorder
        self.recorder = GameRecorder(output_dir)

        # Statistics
        self.stats = {
            "engine1": {"name": self.engine1_display_name, "wins": 0, "draws": 0, "losses": 0,
                       "wins_as_white": 0, "wins_as_black": 0,
                       "total_time": 0, "total_nodes": 0, "total_moves": 0},
            "engine2": {"name": self.engine2_display_name, "wins": 0, "draws": 0, "losses": 0,
                       "wins_as_white": 0, "wins_as_black": 0,
                       "total_time": 0, "total_nodes": 0, "total_moves": 0},
            "games": [],
            "total_moves": 0,
            "longest_game": 0,
            "shortest_game": float('inf'),
            "timeouts": 0,
            "errors": 0
        }

    @staticmethod
    def _create_engine_name(module_name: str, time_limit: Optional[float], random_level: Optional[float], depth: int) -> str:
        """
        Create descriptive engine name including time/randomness/depth.

        Args:
            module_name: Engine module name
            time_limit: Time per move in seconds (or None)
            random_level: Randomness level (or None)
            depth: Search depth

        Returns:
            Descriptive name like "stockfishSonChessEngine_T100ms_D15" or "stockfishSonChessEngine_D10_R50"
        """
        # Start with base module name (strip 'engine_pool.' prefix if present)
        base_name = module_name.replace('engine_pool.', '')

        # Add time if specified (time-based mode) - use milliseconds to avoid decimal points in filenames
        if time_limit is not None:
            time_ms = int(time_limit * 1000)
            base_name += f"_T{time_ms}ms"

        # Always add depth (both time and depth are enforced now)
        base_name += f"_D{depth}"

        # Add randomness if specified - use integer percentage to avoid decimal points
        if random_level is not None and random_level > 0:
            random_pct = int(random_level * 100)
            base_name += f"_R{random_pct}"

        return base_name

    @staticmethod
    def _random_level_to_config(random_level: float) -> dict:
        """
        Convert random_level (0-1) to randomness_config dict.

        Args:
            random_level: Randomness level (0 = deterministic, 1 = high randomness)

        Returns:
            Dictionary with randomness configuration

        Examples:
            0.0 -> disabled
            0.5 -> (0.7, 0.2, 0.1) - moderate randomness
            1.0 -> (0.4, 0.35, 0.25) - high randomness
        """
        if random_level <= 0:
            return {'enabled': False}

        # Linear interpolation for randomness weights
        # Low random (0-0.5): gradually increase from deterministic to moderate
        # High random (0.5-1.0): transition from moderate to high randomness
        if random_level <= 0.5:
            # Scale from (1.0, 0, 0) at 0 to (0.7, 0.2, 0.1) at 0.5
            t = random_level / 0.5
            best_weight = 1.0 - (0.3 * t)
            second_weight = 0.2 * t
            third_weight = 0.1 * t
        else:
            # Scale from (0.7, 0.2, 0.1) at 0.5 to (0.4, 0.35, 0.25) at 1.0
            t = (random_level - 0.5) / 0.5
            best_weight = 0.7 - (0.3 * t)
            second_weight = 0.2 + (0.15 * t)
            third_weight = 0.1 + (0.15 * t)

        return {
            'enabled': True,
            'best_move_weight': round(best_weight, 2),
            'second_move_weight': round(second_weight, 2),
            'third_move_weight': round(third_weight, 2)
        }

    def play_game(self, game_number: int, engine1_is_white: bool) -> Dict[str, Any]:
        """
        Play a single game.

        Args:
            game_number: Game number in match
            engine1_is_white: True if engine1 plays white

        Returns:
            Dictionary with game results
        """
        board = chess.Board()

        # Determine which engine plays which color
        white_engine = self.engine1 if engine1_is_white else self.engine2
        black_engine = self.engine2 if engine1_is_white else self.engine1
        white_name = self.engine1_display_name if engine1_is_white else self.engine2_display_name
        black_name = self.engine2_display_name if engine1_is_white else self.engine1_display_name

        # Game statistics
        white_times = []
        white_nodes_list = []
        black_times = []
        black_nodes_list = []
        move_annotations = []  # Track per-move data for PGN

        move_count = 0
        max_moves = 500  # Prevent infinite games

        if not self.quiet:
            print(f"\nGame {game_number}/{self.num_games}: {white_name} (W) vs {black_name} (B)")

        try:
            while not board.is_game_over() and move_count < max_moves:
                # Get move from appropriate engine
                if board.turn == chess.WHITE:
                    result = white_engine.search(board.copy())
                    if result and result.best_move:
                        move_annotations.append((result.best_move, result, chess.WHITE))
                        move_san = board.san(result.best_move)
                        board.push(result.best_move)
                        white_times.append(result.time_spent)
                        white_nodes_list.append(result.nodes_searched)
                        if self.present:
                            move_number = (move_count // 2) + 1
                            print(f"\n{Colors.WHITE_MOVE}{Colors.BOLD}{move_number}. {move_san}{Colors.RESET} - {white_name}")
                            print_colored_board(board)
                    else:
                        # Engine failed to find move
                        return self._handle_error(game_number, board, white_name, black_name, "white_error")
                else:
                    result = black_engine.search(board.copy())
                    if result and result.best_move:
                        move_annotations.append((result.best_move, result, chess.BLACK))
                        move_san = board.san(result.best_move)
                        board.push(result.best_move)
                        black_times.append(result.time_spent)
                        black_nodes_list.append(result.nodes_searched)
                        if self.present:
                            move_number = (move_count // 2) + 1
                            print(f"\n{Colors.BLACK_MOVE}{Colors.BOLD}{move_number}... {move_san}{Colors.RESET} - {black_name}")
                            print_colored_board(board)
                    else:
                        # Engine failed to find move
                        return self._handle_error(game_number, board, white_name, black_name, "black_error")

                move_count += 1

            # Determine result
            if move_count >= max_moves:
                result_str = "1/2-1/2"
                termination = "adjudication_move_limit"
            elif board.is_checkmate():
                result_str = "1-0" if board.turn == chess.BLACK else "0-1"
                termination = "checkmate"
            elif board.is_stalemate():
                result_str = "1/2-1/2"
                termination = "stalemate"
            elif board.is_insufficient_material():
                result_str = "1/2-1/2"
                termination = "insufficient_material"
            elif board.is_fifty_moves():
                result_str = "1/2-1/2"
                termination = "fifty_move_rule"
            elif board.is_repetition():
                result_str = "1/2-1/2"
                termination = "threefold_repetition"
            else:
                result_str = "1/2-1/2"
                termination = "unknown"

        except Exception as e:
            print(f"Error during game {game_number}: {e}")
            return self._handle_error(game_number, board, white_name, black_name, "exception")

        # Calculate statistics
        white_stats = {
            "avg_time": sum(white_times) / len(white_times) if white_times else 0,
            "avg_nodes": sum(white_nodes_list) / len(white_nodes_list) if white_nodes_list else 0,
            "total_moves": len(white_times)
        }

        black_stats = {
            "avg_time": sum(black_times) / len(black_times) if black_times else 0,
            "avg_nodes": sum(black_nodes_list) / len(black_nodes_list) if black_nodes_list else 0,
            "total_moves": len(black_times)
        }

        # Record game
        pgn_path = self.recorder.record_game(
            board, game_number, white_name, black_name,
            result_str, termination, white_stats, black_stats,
            move_annotations=move_annotations
        )

        if not self.quiet:
            print(f"Result: {result_str} ({termination}) - {move_count} moves")

        return {
            "game_number": game_number,
            "result": result_str,
            "termination": termination,
            "moves": move_count,
            "white_name": white_name,
            "black_name": black_name,
            "white_stats": white_stats,
            "black_stats": black_stats,
            "pgn_path": str(pgn_path)
        }

    def _handle_error(self, game_number: int, board: chess.Board,
                     white_name: str, black_name: str, error_type: str) -> Dict[str, Any]:
        """Handle game errors."""
        self.stats["errors"] += 1

        # Award win to opponent
        if "white" in error_type:
            result_str = "0-1"
        elif "black" in error_type:
            result_str = "1-0"
        else:
            result_str = "1/2-1/2"

        # Record game
        pgn_path = self.recorder.record_game(
            board, game_number, white_name, black_name,
            result_str, error_type, None, None
        )

        print(f"Game {game_number} ended with error: {error_type} -> {result_str}")

        return {
            "game_number": game_number,
            "result": result_str,
            "termination": error_type,
            "moves": len(board.move_stack),
            "white_name": white_name,
            "black_name": black_name,
            "pgn_path": str(pgn_path)
        }

    def update_stats(self, game_result: Dict[str, Any]):
        """Update tournament statistics."""
        result = game_result["result"]
        white_name = game_result["white_name"]
        moves = game_result["moves"]

        # Update move statistics
        self.stats["total_moves"] += moves
        self.stats["longest_game"] = max(self.stats["longest_game"], moves)
        self.stats["shortest_game"] = min(self.stats["shortest_game"], moves)

        # Determine if engine1 is white (compare display names)
        engine1_is_white = (white_name == self.engine1_display_name)

        # Update engine statistics
        if result == "1-0":
            # White won
            if engine1_is_white:
                self.stats["engine1"]["wins"] += 1
                self.stats["engine1"]["wins_as_white"] += 1
                self.stats["engine2"]["losses"] += 1
            else:
                self.stats["engine2"]["wins"] += 1
                self.stats["engine2"]["wins_as_white"] += 1
                self.stats["engine1"]["losses"] += 1
        elif result == "0-1":
            # Black won
            if engine1_is_white:
                # Engine1 is white, so engine2 (black) won
                self.stats["engine2"]["wins"] += 1
                self.stats["engine2"]["wins_as_black"] += 1
                self.stats["engine1"]["losses"] += 1
            else:
                # Engine2 is white, so engine1 (black) won
                self.stats["engine1"]["wins"] += 1
                self.stats["engine1"]["wins_as_black"] += 1
                self.stats["engine2"]["losses"] += 1
        else:
            self.stats["engine1"]["draws"] += 1
            self.stats["engine2"]["draws"] += 1

        # Update time/nodes if available
        if "white_stats" in game_result and game_result["white_stats"]:
            if engine1_is_white:
                self.stats["engine1"]["total_time"] += game_result["white_stats"]["avg_time"] * game_result["white_stats"]["total_moves"]
                self.stats["engine1"]["total_nodes"] += game_result["white_stats"]["avg_nodes"] * game_result["white_stats"]["total_moves"]
                self.stats["engine1"]["total_moves"] += game_result["white_stats"]["total_moves"]
            else:
                self.stats["engine2"]["total_time"] += game_result["white_stats"]["avg_time"] * game_result["white_stats"]["total_moves"]
                self.stats["engine2"]["total_nodes"] += game_result["white_stats"]["avg_nodes"] * game_result["white_stats"]["total_moves"]
                self.stats["engine2"]["total_moves"] += game_result["white_stats"]["total_moves"]

        if "black_stats" in game_result and game_result["black_stats"]:
            if not engine1_is_white:
                # Engine1 is black
                self.stats["engine1"]["total_time"] += game_result["black_stats"]["avg_time"] * game_result["black_stats"]["total_moves"]
                self.stats["engine1"]["total_nodes"] += game_result["black_stats"]["avg_nodes"] * game_result["black_stats"]["total_moves"]
                self.stats["engine1"]["total_moves"] += game_result["black_stats"]["total_moves"]
            else:
                # Engine2 is black
                self.stats["engine2"]["total_time"] += game_result["black_stats"]["avg_time"] * game_result["black_stats"]["total_moves"]
                self.stats["engine2"]["total_nodes"] += game_result["black_stats"]["avg_nodes"] * game_result["black_stats"]["total_moves"]
                self.stats["engine2"]["total_moves"] += game_result["black_stats"]["total_moves"]

        self.stats["games"].append(game_result)

    def run_tournament(self):
        """Run the complete tournament."""
        print("\n" + "=" * 70)
        print(f"TOURNAMENT: {self.engine1_display_name} vs {self.engine2_display_name}")
        print("=" * 70)
        print(f"Games: {self.num_games}")
        print("-" * 70)

        # Engine 1 details
        print(f"Engine 1: {self.engine1_display_name}")
        if self.time1:
            print(f"  Mode: TIME-BASED ({self.time1}s per move)")
            print(f"  Behavior: Returns best move within time limit (no randomness)")
        else:
            print(f"  Mode: DEPTH-BASED (depth={self.depth1})")
            if self.random_level1 and self.random_level1 > 0:
                print(f"  Randomness: ENABLED (level={self.random_level1}, selects from top 3 moves)")
            else:
                print(f"  Randomness: DISABLED (always best move)")

        print("-" * 70)

        # Engine 2 details
        print(f"Engine 2: {self.engine2_display_name}")
        if self.time2:
            print(f"  Mode: TIME-BASED ({self.time2}s per move)")
            print(f"  Behavior: Returns best move within time limit (no randomness)")
        else:
            print(f"  Mode: DEPTH-BASED (depth={self.depth2})")
            if self.random_level2 and self.random_level2 > 0:
                print(f"  Randomness: ENABLED (level={self.random_level2}, selects from top 3 moves)")
            else:
                print(f"  Randomness: DISABLED (always best move)")

        print("=" * 70 + "\n")

        # Start match recording
        time_for_recorder = self.time1 or self.time2  # Use either time for recording
        self.recorder.start_match(
            self.engine1_display_name, self.engine2_display_name,
            self.depth1, self.depth2, time_for_recorder, self.num_games
        )

        # Show output directory
        print(f"Output: {self.recorder.get_match_dir()}\n")

        start_time = time.time()

        # Play games (alternating colors)
        for game_num in range(1, self.num_games + 1):
            engine1_is_white = (game_num % 2 == 1)
            game_result = self.play_game(game_num, engine1_is_white)
            self.update_stats(game_result)

            # Show progress
            if not self.quiet and game_num % 10 == 0:
                elapsed = time.time() - start_time
                games_per_sec = game_num / elapsed
                eta = (self.num_games - game_num) / games_per_sec if games_per_sec > 0 else 0
                print(f"\nProgress: {game_num}/{self.num_games} ({game_num*100//self.num_games}%) - ETA: {eta/60:.1f}min")
                print(f"Current score: {self.stats['engine1']['name']}: {self.stats['engine1']['wins']}-{self.stats['engine1']['draws']}-{self.stats['engine1']['losses']}")

        total_time = time.time() - start_time

        # Save match summary
        self.recorder.save_match_summary(self.stats)

        # Display results
        self.display_results(total_time)

    def display_results(self, total_time: float):
        """Display tournament results."""
        print("\n" + "+" + "=" * 68 + "+")
        print(f"|{'MATCH RESULTS':^68}|")
        print("+" + "=" * 68 + "+")
        print(f"| Configuration:{' ' * 54}|")
        print(f"|   Games Played: {self.num_games:>6}{' ' * 45}|")
        time_str = f"E1:{self.time1}s E2:{self.time2}s" if (self.time1 or self.time2) else "depth-based"
        print(f"|   Time Control: {time_str:>20}{' ' * 31}|")
        print(f"|   Depth: {self.depth1} vs {self.depth2}{' ' * 51}|")
        print("+" + "=" * 68 + "+")
        print(f"|{'OVERALL RESULTS':^68}|")
        print("+" + "=" * 68 + "+")

        e1 = self.stats["engine1"]
        e2 = self.stats["engine2"]

        print(f"| {e1['name']}: {e1['wins']:>3} wins | {e1['draws']:>3} draws | {e1['losses']:>3} losses{' ' * (33 - len(e1['name']))}|")
        print(f"| {e2['name']}: {e2['wins']:>3} wins | {e2['draws']:>3} draws | {e2['losses']:>3} losses{' ' * (33 - len(e2['name']))}|")

        score1 = e1['wins'] + 0.5 * e1['draws']
        score2 = e2['wins'] + 0.5 * e2['draws']
        print(f"|{' ' * 68}|")
        print(f"| Score: {score1:.1f} - {score2:.1f}{' ' * 54}|")

        print("+" + "=" * 68 + "+")
        print(f"|{'GAME STATISTICS':^68}|")
        print("+" + "=" * 68 + "+")
        print(f"| Average Game Length: {self.stats['total_moves'] / self.num_games:>6.1f} moves{' ' * 34}|")
        print(f"| Longest Game:  {self.stats['longest_game']:>6} moves{' ' * 40}|")
        print(f"| Shortest Game: {self.stats['shortest_game']:>6} moves{' ' * 40}|")
        print(f"| Decisive Games: {e1['wins'] + e2['wins']:>5}/{self.num_games} ({(e1['wins'] + e2['wins'])*100/self.num_games:.1f}%){' ' * 33}|")
        print(f"| Draws:          {e1['draws']:>5}/{self.num_games} ({e1['draws']*100/self.num_games:.1f}%){' ' * 33}|")

        if self.stats["errors"] > 0:
            print(f"| Errors:         {self.stats['errors']:>5}{' ' * 48}|")

        print("+" + "=" * 68 + "+")
        print(f"|{'PERFORMANCE METRICS':^68}|")
        print("+" + "=" * 68 + "+")

        if e1["total_moves"] > 0:
            avg_time1 = e1["total_time"] / e1["total_moves"]
            avg_nodes1 = e1["total_nodes"] / e1["total_moves"]
            print(f"| {e1['name']} Avg Time/Move: {avg_time1:>6.2f}s{' ' * (38 - len(e1['name']))}|")
            print(f"| {e1['name']} Avg Nodes/Move: {avg_nodes1:>10,.0f}{' ' * (33 - len(e1['name']))}|")

        if e2["total_moves"] > 0:
            avg_time2 = e2["total_time"] / e2["total_moves"]
            avg_nodes2 = e2["total_nodes"] / e2["total_moves"]
            print(f"| {e2['name']} Avg Time/Move: {avg_time2:>6.2f}s{' ' * (38 - len(e2['name']))}|")
            print(f"| {e2['name']} Avg Nodes/Move: {avg_nodes2:>10,.0f}{' ' * (33 - len(e2['name']))}|")

        print("+" + "=" * 68 + "+")
        print(f"| Total Time: {total_time/60:.1f} minutes{' ' * 45}|")
        print(f"| Games saved to: {str(self.recorder.get_match_dir())[:50]}{' ' * (17 - min(50, len(str(self.recorder.get_match_dir()))))}|")
        print("+" + "=" * 68 + "+\n")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Run chess engine tournament")

    parser.add_argument("--engine1", required=True, help="First engine module (e.g., engine_v3)")
    parser.add_argument("--engine2", required=True, help="Second engine module (e.g., engine_v4)")
    parser.add_argument("--games", type=int, default=100, help="Number of games to play")
    parser.add_argument("--depth1", type=int, default=5, help="Search depth for engine 1 (used with randomness)")
    parser.add_argument("--depth2", type=int, default=5, help="Search depth for engine 2 (used with randomness)")
    parser.add_argument("--time1", type=float, default=None, help="Time per move for engine 1 (seconds)")
    parser.add_argument("--time2", type=float, default=None, help="Time per move for engine 2 (seconds)")
    parser.add_argument("--random_level1", type=float, default=None, help="Randomness for engine 1 (0-1, uses depth-based search)")
    parser.add_argument("--random_level2", type=float, default=None, help="Randomness for engine 2 (0-1, uses depth-based search)")
    parser.add_argument("--output-dir", default="games", help="Output directory for games")
    parser.add_argument("--quiet", action="store_true", help="Minimize output")
    parser.add_argument("--quick", action="store_true", help="Quick test (10 games)")
    parser.add_argument("--present", action="store_true", help="Show board after every move with move number and engine name")

    args = parser.parse_args()

    # Override games for quick mode
    if args.quick:
        args.games = 10

    # Run tournament
    tournament = TournamentRunner(
        args.engine1, args.engine2,
        depth1=args.depth1, depth2=args.depth2,
        time1=args.time1, time2=args.time2,
        num_games=args.games,
        output_dir=args.output_dir,
        quiet=args.quiet,
        random_level1=args.random_level1, random_level2=args.random_level2,
        present=args.present
    )

    tournament.run_tournament()


if __name__ == "__main__":
    main()
    # run with --engine1 engine_v3 --engine2 engine_v4 --games 10 --time 5 --depth1 8 --depth2 8
    # --engine1 engine_v5 --engine2 engine --games 2 --depth1 20 --depth2 20 --time 1.5
