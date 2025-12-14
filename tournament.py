"""
Tournament Runner - CLI interface for running engine vs engine matches
"""

import argparse
import chess
import time
import importlib
from typing import Dict, Any, Optional, List
from pathlib import Path
from game_recorder import GameRecorder


class TournamentRunner:
    """Runs tournaments between two chess engines."""

    def __init__(self, engine1_module: str, engine2_module: str,
                 depth1: int = 5, depth2: int = 5,
                 time_limit: Optional[float] = None,
                 num_games: int = 100,
                 output_dir: str = "games",
                 quiet: bool = False):
        """
        Initialize tournament runner.

        Args:
            engine1_module: Module name for engine 1 (e.g., "engine_v3")
            engine2_module: Module name for engine 2 (e.g., "engine_v4")
            depth1: Search depth for engine 1
            depth2: Search depth for engine 2
            time_limit: Time limit per move in seconds
            num_games: Number of games to play
            output_dir: Directory for saving games
            quiet: Minimize output
        """
        self.engine1_module = engine1_module
        self.engine2_module = engine2_module
        self.depth1 = depth1
        self.depth2 = depth2
        self.time_limit = time_limit
        self.num_games = num_games
        self.quiet = quiet

        # Load engines
        print(f"Loading engines: {engine1_module} vs {engine2_module}...")
        mod1 = importlib.import_module(engine1_module)
        mod2 = importlib.import_module(engine2_module)

        self.engine1 = mod1.ChessEngine(max_depth=depth1, time_limit=time_limit)
        self.engine2 = mod2.ChessEngine(max_depth=depth2, time_limit=time_limit)

        # Initialize recorder
        self.recorder = GameRecorder(output_dir)

        # Statistics
        self.stats = {
            "engine1": {"name": engine1_module, "wins": 0, "draws": 0, "losses": 0,
                       "wins_as_white": 0, "wins_as_black": 0,
                       "total_time": 0, "total_nodes": 0, "total_moves": 0},
            "engine2": {"name": engine2_module, "wins": 0, "draws": 0, "losses": 0,
                       "wins_as_white": 0, "wins_as_black": 0,
                       "total_time": 0, "total_nodes": 0, "total_moves": 0},
            "games": [],
            "total_moves": 0,
            "longest_game": 0,
            "shortest_game": float('inf'),
            "timeouts": 0,
            "errors": 0
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
        white_name = self.engine1_module if engine1_is_white else self.engine2_module
        black_name = self.engine2_module if engine1_is_white else self.engine1_module

        # Game statistics
        white_times = []
        white_nodes_list = []
        black_times = []
        black_nodes_list = []

        move_count = 0
        max_moves = 500  # Prevent infinite games

        if not self.quiet:
            print(f"\nGame {game_number}/{self.num_games}: {white_name} (W) vs {black_name} (B)")

        try:
            while not board.is_game_over() and move_count < max_moves:
                # Get move from appropriate engine
                if board.turn == chess.WHITE:
                    result = white_engine.search(board)
                    if result and result.best_move:
                        board.push(result.best_move)
                        white_times.append(result.time_spent)
                        white_nodes_list.append(result.nodes_searched)
                    else:
                        # Engine failed to find move
                        return self._handle_error(game_number, board, white_name, black_name, "white_error")
                else:
                    result = black_engine.search(board)
                    if result and result.best_move:
                        board.push(result.best_move)
                        black_times.append(result.time_spent)
                        black_nodes_list.append(result.nodes_searched)
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
            result_str, termination, white_stats, black_stats
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

        # Determine winner
        if result == "1-0":
            winner = white_name
        elif result == "0-1":
            winner = white_name if white_name == self.engine2_module else self.engine1_module
            winner = self.engine2_module if white_name == self.engine1_module else self.engine1_module
        else:
            winner = None

        # Update engine statistics
        if result == "1-0":
            if white_name == self.engine1_module:
                self.stats["engine1"]["wins"] += 1
                self.stats["engine1"]["wins_as_white"] += 1
                self.stats["engine2"]["losses"] += 1
            else:
                self.stats["engine2"]["wins"] += 1
                self.stats["engine2"]["wins_as_white"] += 1
                self.stats["engine1"]["losses"] += 1
        elif result == "0-1":
            if white_name == self.engine1_module:
                self.stats["engine2"]["wins"] += 1
                self.stats["engine2"]["wins_as_black"] += 1
                self.stats["engine1"]["losses"] += 1
            else:
                self.stats["engine1"]["wins"] += 1
                self.stats["engine1"]["wins_as_black"] += 1
                self.stats["engine2"]["losses"] += 1
        else:
            self.stats["engine1"]["draws"] += 1
            self.stats["engine2"]["draws"] += 1

        # Update time/nodes if available
        if "white_stats" in game_result and game_result["white_stats"]:
            if white_name == self.engine1_module:
                self.stats["engine1"]["total_time"] += game_result["white_stats"]["avg_time"] * game_result["white_stats"]["total_moves"]
                self.stats["engine1"]["total_nodes"] += game_result["white_stats"]["avg_nodes"] * game_result["white_stats"]["total_moves"]
                self.stats["engine1"]["total_moves"] += game_result["white_stats"]["total_moves"]
            else:
                self.stats["engine2"]["total_time"] += game_result["white_stats"]["avg_time"] * game_result["white_stats"]["total_moves"]
                self.stats["engine2"]["total_nodes"] += game_result["white_stats"]["avg_nodes"] * game_result["white_stats"]["total_moves"]
                self.stats["engine2"]["total_moves"] += game_result["white_stats"]["total_moves"]

        if "black_stats" in game_result and game_result["black_stats"]:
            black_name = game_result["black_name"]
            if black_name == self.engine1_module:
                self.stats["engine1"]["total_time"] += game_result["black_stats"]["avg_time"] * game_result["black_stats"]["total_moves"]
                self.stats["engine1"]["total_nodes"] += game_result["black_stats"]["avg_nodes"] * game_result["black_stats"]["total_moves"]
                self.stats["engine1"]["total_moves"] += game_result["black_stats"]["total_moves"]
            else:
                self.stats["engine2"]["total_time"] += game_result["black_stats"]["avg_time"] * game_result["black_stats"]["total_moves"]
                self.stats["engine2"]["total_nodes"] += game_result["black_stats"]["avg_nodes"] * game_result["black_stats"]["total_moves"]
                self.stats["engine2"]["total_moves"] += game_result["black_stats"]["total_moves"]

        self.stats["games"].append(game_result)

    def run_tournament(self):
        """Run the complete tournament."""
        print("\n" + "=" * 70)
        print(f"TOURNAMENT: {self.engine1_module} vs {self.engine2_module}")
        print("=" * 70)
        print(f"Games: {self.num_games}")
        print(f"Depth: {self.depth1} vs {self.depth2}")
        if self.time_limit:
            print(f"Time limit: {self.time_limit}s per move")
        print("=" * 70 + "\n")

        # Start match recording
        self.recorder.start_match(
            self.engine1_module, self.engine2_module,
            self.depth1, self.depth2, self.time_limit, self.num_games
        )

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
        print("\n" + "╔" + "=" * 68 + "╗")
        print(f"║{'MATCH RESULTS':^68}║")
        print("╠" + "=" * 68 + "╣")
        print(f"║ Configuration:{' ' * 54}║")
        print(f"║   Games Played: {self.num_games:>6}{' ' * 45}║")
        print(f"║   Time Control: {f'{self.time_limit}s per move' if self.time_limit else 'depth-based':>20}{' ' * 31}║")
        print(f"║   Depth: {self.depth1} vs {self.depth2}{' ' * 51}║")
        print("╠" + "=" * 68 + "╣")
        print(f"║{'OVERALL RESULTS':^68}║")
        print("╠" + "=" * 68 + "╣")

        e1 = self.stats["engine1"]
        e2 = self.stats["engine2"]

        print(f"║ {e1['name']}: {e1['wins']:>3} wins | {e1['draws']:>3} draws | {e1['losses']:>3} losses{' ' * (33 - len(e1['name']))}║")
        print(f"║ {e2['name']}: {e2['wins']:>3} wins | {e2['draws']:>3} draws | {e2['losses']:>3} losses{' ' * (33 - len(e2['name']))}║")

        score1 = e1['wins'] + 0.5 * e1['draws']
        score2 = e2['wins'] + 0.5 * e2['draws']
        print(f"║{' ' * 68}║")
        print(f"║ Score: {score1:.1f} - {score2:.1f}{' ' * 54}║")

        print("╠" + "=" * 68 + "╣")
        print(f"║{'GAME STATISTICS':^68}║")
        print("╠" + "=" * 68 + "╣")
        print(f"║ Average Game Length: {self.stats['total_moves'] / self.num_games:>6.1f} moves{' ' * 34}║")
        print(f"║ Longest Game:  {self.stats['longest_game']:>6} moves{' ' * 40}║")
        print(f"║ Shortest Game: {self.stats['shortest_game']:>6} moves{' ' * 40}║")
        print(f"║ Decisive Games: {e1['wins'] + e2['wins']:>5}/{self.num_games} ({(e1['wins'] + e2['wins'])*100/self.num_games:.1f}%){' ' * 33}║")
        print(f"║ Draws:          {e1['draws']:>5}/{self.num_games} ({e1['draws']*100/self.num_games:.1f}%){' ' * 33}║")

        if self.stats["errors"] > 0:
            print(f"║ Errors:         {self.stats['errors']:>5}{' ' * 48}║")

        print("╠" + "=" * 68 + "╣")
        print(f"║{'PERFORMANCE METRICS':^68}║")
        print("╠" + "=" * 68 + "╣")

        if e1["total_moves"] > 0:
            avg_time1 = e1["total_time"] / e1["total_moves"]
            avg_nodes1 = e1["total_nodes"] / e1["total_moves"]
            print(f"║ {e1['name']} Avg Time/Move: {avg_time1:>6.2f}s{' ' * (38 - len(e1['name']))}║")
            print(f"║ {e1['name']} Avg Nodes/Move: {avg_nodes1:>10,.0f}{' ' * (33 - len(e1['name']))}║")

        if e2["total_moves"] > 0:
            avg_time2 = e2["total_time"] / e2["total_moves"]
            avg_nodes2 = e2["total_nodes"] / e2["total_moves"]
            print(f"║ {e2['name']} Avg Time/Move: {avg_time2:>6.2f}s{' ' * (38 - len(e2['name']))}║")
            print(f"║ {e2['name']} Avg Nodes/Move: {avg_nodes2:>10,.0f}{' ' * (33 - len(e2['name']))}║")

        print("╠" + "=" * 68 + "╣")
        print(f"║ Total Time: {total_time/60:.1f} minutes{' ' * 45}║")
        print(f"║ Games saved to: {str(self.recorder.get_match_dir())[:50]}{' ' * (17 - min(50, len(str(self.recorder.get_match_dir()))))}║")
        print("╚" + "=" * 68 + "╝\n")


def main():
    """Main entry point for CLI."""
    parser = argparse.ArgumentParser(description="Run chess engine tournament")

    parser.add_argument("--engine1", required=True, help="First engine module (e.g., engine_v3)")
    parser.add_argument("--engine2", required=True, help="Second engine module (e.g., engine_v4)")
    parser.add_argument("--games", type=int, default=100, help="Number of games to play")
    parser.add_argument("--depth1", type=int, default=5, help="Search depth for engine 1")
    parser.add_argument("--depth2", type=int, default=5, help="Search depth for engine 2")
    parser.add_argument("--time", type=float, default=None, help="Time limit per move (seconds)")
    parser.add_argument("--output-dir", default="games", help="Output directory for games")
    parser.add_argument("--quiet", action="store_true", help="Minimize output")
    parser.add_argument("--quick", action="store_true", help="Quick test (10 games)")

    args = parser.parse_args()

    # Override games for quick mode
    if args.quick:
        args.games = 10

    # Run tournament
    tournament = TournamentRunner(
        args.engine1, args.engine2,
        depth1=args.depth1, depth2=args.depth2,
        time_limit=args.time,
        num_games=args.games,
        output_dir=args.output_dir,
        quiet=args.quiet
    )

    tournament.run_tournament()


if __name__ == "__main__":
    main()
