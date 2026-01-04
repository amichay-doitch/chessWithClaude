"""
Stockfish Son Chess Engine - Stockfish Wrapper for Tournament Play

This engine wraps Stockfish to enable tournament play with two modes:
1. TIME-BASED: Uses get_best_move_time() for strict time control (no randomness)
2. DEPTH-BASED: Uses get_top_moves() with optional randomness for training data

Features:
- Time control support (strict enforcement via get_best_move_time)
- Move randomness for diverse training data (select 2nd/3rd best moves)
- Full tournament integration
- Self-play support: Run Stockfish vs Stockfish with different configs
- Training data generation: Create large datasets of varied games

Usage Examples:
    # Time-based mode (0.5 seconds per move, no randomness)
    engine = ChessEngine(time_limit=0.5)

    # Depth-based with randomness (for training data)
    engine = ChessEngine(
        max_depth=10,
        randomness_config={
            'enabled': True,
            'best_move_weight': 0.6,
            'second_move_weight': 0.3,
            'third_move_weight': 0.1
        }
    )

    # Depth-based without randomness (deterministic)
    engine = ChessEngine(max_depth=15)

Tournament Self-Play:
    # Time-based engine vs depth-based with randomness
    python tournament.py \\
      --engine1 engine_pool.stockfishSonChessEngine \\
      --engine2 engine_pool.stockfishSonChessEngine \\
      --time1 0.5 \\
      --depth2 10 --random_level2 0.7 \\
      --games 100
"""

import chess
import time
import random
import sys
import os
from typing import Optional
from dataclasses import dataclass

# Add parent directory to path to import stockfish_analyzer and stockfish
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stockfish_analyzer import StockfishAnalyzer
from stockfish import Stockfish


@dataclass
class SearchResult:
    """Result from engine search."""
    best_move: chess.Move
    score: int           # Centipawns from current player perspective
    depth: int
    nodes_searched: int
    time_spent: float


class ChessEngine:
    """
    Stockfish wrapper engine with two modes:

    1. TIME-BASED MODE (when time_limit is set):
       - Uses get_best_move_time() for strict time control
       - Returns best move within the time limit
       - No randomness (always best move)

    2. DEPTH-BASED MODE (when time_limit is None):
       - Uses get_top_moves() with specified depth
       - Optional randomness to select from top 3 moves
       - Good for generating diverse training data

    The engine can be instantiated multiple times with different parameters
    to enable self-play scenarios for training data generation.
    """

    def __init__(
        self,
        max_depth: int = 20,
        time_limit: Optional[float] = None,
        threads: int = 1,
        hash_size: int = 16,
        randomness_config: Optional[dict] = None,
        stockfish_path: Optional[str] = None
    ):
        """
        Initialize Stockfish wrapper engine.

        Args:
            max_depth: Search depth for depth-based mode (default: 20)
            time_limit: Time per move in seconds. If set, uses TIME-BASED mode.
                        If None, uses DEPTH-BASED mode with max_depth.
            threads: Number of CPU threads (default: 1)
            hash_size: Hash table size in MB (default: 16)
            randomness_config: Dictionary controlling move selection randomness
                               (only used in DEPTH-BASED mode):
                {
                    'enabled': bool,              # Enable randomness (default: False)
                    'best_move_weight': float,    # Probability for best move (default: 0.7)
                    'second_move_weight': float,  # Probability for 2nd best (default: 0.2)
                    'third_move_weight': float    # Probability for 3rd best (default: 0.1)
                }
            stockfish_path: Path to Stockfish binary (default: auto-detect)

        Raises:
            ValueError: If randomness weights don't sum to 1.0
        """
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.threads = threads
        self.hash_size = hash_size

        # Auto-detect stockfish path
        if stockfish_path is None:
            script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            self.stockfish_path = os.path.join(script_dir, "data/stockfish-windows-x86-64-avx2.exe")
        else:
            self.stockfish_path = stockfish_path

        # Persistent Stockfish instance for time-based mode (avoid re-initialization overhead)
        self._stockfish_instance = None
        if self.time_limit is not None:
            self._stockfish_instance = Stockfish(
                path=self.stockfish_path,
                parameters={"Threads": self.threads, "Hash": self.hash_size}
            )

        # Parse randomness configuration (only for depth-based mode)
        self.randomness_enabled = False
        self.move_weights = [1.0, 0.0, 0.0]  # Default: always pick best move

        if randomness_config and time_limit is None:  # Randomness only in depth-based mode
            self.randomness_enabled = randomness_config.get('enabled', False)
            if self.randomness_enabled:
                weights = [
                    randomness_config.get('best_move_weight', 0.7),
                    randomness_config.get('second_move_weight', 0.2),
                    randomness_config.get('third_move_weight', 0.1)
                ]

                # Validate weights sum to ~1.0
                total = sum(weights)
                if not (0.99 <= total <= 1.01):  # Allow small floating point error
                    raise ValueError(
                        f"Move weights must sum to 1.0, got {total}. "
                        f"Weights: best={weights[0]}, second={weights[1]}, third={weights[2]}"
                    )

                self.move_weights = weights

    def _convert_score_to_centipawns(self, move_analysis, board: chess.Board) -> int:
        """
        Convert MoveAnalysis score to centipawns from current player's perspective.

        Stockfish returns scores from white's perspective. This method converts
        mate scores to high centipawn values and adjusts perspective for black.

        Args:
            move_analysis: MoveAnalysis object from Stockfish
            board: Current board position (for perspective)

        Returns:
            Score in centipawns (positive = good for current player)
        """
        # Get score from white perspective
        if move_analysis.mate is not None:
            # Mate score
            if move_analysis.mate > 0:
                # White is giving mate in N moves
                score_white = 100000 - move_analysis.mate
            else:
                # Black is giving mate in N moves (mate value is negative)
                score_white = -100000 - move_analysis.mate
        elif move_analysis.centipawn is not None:
            score_white = move_analysis.centipawn
        else:
            # No score available (shouldn't happen with Stockfish)
            score_white = 0

        # Convert to current player perspective
        if board.turn == chess.BLACK:
            return -score_white
        return score_white

    def _select_move_with_randomness(self, top_moves: list, board: chess.Board) -> tuple:
        """
        Select move from top candidates using weighted random selection.

        If randomness is disabled or only one move is available, returns the best move.
        Otherwise, uses weighted random selection from top 1-3 moves.
        Automatically handles positions with fewer than 3 legal moves.

        Args:
            top_moves: List of MoveAnalysis objects (up to 3)
            board: Current board position

        Returns:
            Tuple of (selected_move, score_in_centipawns)
        """
        if not self.randomness_enabled or len(top_moves) == 1:
            # No randomness or only one move available
            move_analysis = top_moves[0]
            score = self._convert_score_to_centipawns(move_analysis, board)
            return move_analysis.move, score

        # Adjust weights based on available moves
        num_moves = min(len(top_moves), 3)
        weights = self.move_weights[:num_moves]

        # Renormalize if we have fewer than 3 moves
        if num_moves < 3:
            weights_sum = sum(weights)
            weights = [w / weights_sum for w in weights]

        # Weighted random selection
        selected_index = random.choices(
            range(num_moves),
            weights=weights,
            k=1
        )[0]

        move_analysis = top_moves[selected_index]
        score = self._convert_score_to_centipawns(move_analysis, board)

        return move_analysis.move, score

    def search(self, board: chess.Board, depth: Optional[int] = None) -> Optional[SearchResult]:
        """
        Search for best move in position using Stockfish.

        This is the main interface method called by the tournament system.

        Two modes:
        - TIME-BASED: If time_limit is set, uses get_best_move_time() for strict time control
        - DEPTH-BASED: If time_limit is None, uses get_top_moves() with optional randomness

        Args:
            board: Chess position to analyze
            depth: Search depth override (uses max_depth if None, only for depth-based mode)

        Returns:
            SearchResult with best move and evaluation, or None if no legal moves
        """
        start_time = time.time()

        # Check for no legal moves (checkmate or stalemate)
        if not any(board.legal_moves):
            return None

        # TIME-BASED MODE: Use get_best_move_time() for strict time control
        if self.time_limit is not None:
            return self._search_time_based(board, start_time)

        # DEPTH-BASED MODE: Use get_top_moves() with optional randomness
        return self._search_depth_based(board, depth, start_time)

    def _search_time_based(self, board: chess.Board, start_time: float) -> SearchResult:
        """
        Time-based search using get_best_move_time().
        Returns best move within the specified time limit.
        Uses persistent Stockfish instance for speed.
        """
        # Convert seconds to milliseconds
        time_ms = int(self.time_limit * 1000)

        # Use persistent Stockfish instance
        sf = self._stockfish_instance

        # Set depth limit (search stops at whichever limit is hit first: time or depth)
        sf.set_depth(self.max_depth)

        # Set position
        sf.set_fen_position(board.fen())

        # Get best move with time limit
        best_move_uci = sf.get_best_move_time(time_ms)

        if best_move_uci is None:
            # Fallback to any legal move
            best_move = list(board.legal_moves)[0]
            score = 0
        else:
            best_move = chess.Move.from_uci(best_move_uci)

            # Get evaluation
            eval_info = sf.get_evaluation()
            if eval_info['type'] == 'cp':
                score = eval_info['value']
            elif eval_info['type'] == 'mate':
                score = 100000 - abs(eval_info['value']) if eval_info['value'] > 0 else -100000 + abs(eval_info['value'])
            else:
                score = 0

            # Adjust score for black's perspective
            if board.turn == chess.BLACK:
                score = -score

        time_spent = time.time() - start_time

        return SearchResult(
            best_move=best_move,
            score=score,
            depth=self.max_depth,  # Max depth limit used
            nodes_searched=0,  # Nodes not tracked in time-based mode
            time_spent=time_spent
        )

    def _search_depth_based(self, board: chess.Board, depth: Optional[int], start_time: float) -> SearchResult:
        """
        Depth-based search using get_top_moves() with optional randomness.
        Good for generating diverse training data.
        """
        # Determine search depth
        if depth is None:
            depth = self.max_depth

        # Initialize Stockfish with configured parameters
        with StockfishAnalyzer(
            stockfish_path=self.stockfish_path,
            depth=depth,
            threads=self.threads,
            hash_size=self.hash_size
        ) as analyzer:
            # Get top 3 moves if randomness enabled, else just 1
            num_moves_to_fetch = 3 if self.randomness_enabled else 1

            # Analyze position with verbose statistics
            analysis = analyzer.analyze(
                board,
                top_n=num_moves_to_fetch,
                verbose=True
            )

            # Select move (with or without randomness)
            if analysis.top_moves:
                selected_move, score = self._select_move_with_randomness(
                    analysis.top_moves,
                    board
                )
            else:
                # Fallback: use best_move from analysis
                selected_move = analysis.best_move
                score = int(analysis.evaluation * 100)
                if board.turn == chess.BLACK:
                    score = -score

            # Extract statistics
            nodes = 0
            if analysis.verbose_stats:
                nodes = analysis.verbose_stats.nodes

        time_spent = time.time() - start_time

        return SearchResult(
            best_move=selected_move,
            score=score,
            depth=depth,
            nodes_searched=nodes,
            time_spent=time_spent
        )

    def get_best_move(self, board: chess.Board) -> Optional[chess.Move]:
        """
        Get best move for position (convenience method).

        Args:
            board: Chess position

        Returns:
            Best move, or None if no legal moves
        """
        result = self.search(board)
        return result.best_move if result else None


if __name__ == "__main__":
    # Basic test
    print("Testing Stockfish Son Chess Engine...")
    print("=" * 50)

    board = chess.Board()

    # Test 1: Time-based mode
    print("\nTest 1: TIME-BASED mode (0.1 seconds per move)")
    engine_time = ChessEngine(time_limit=0.1)
    result = engine_time.search(board)
    if result:
        print(f"  Best move: {result.best_move}")
        print(f"  Score: {result.score}")
        print(f"  Time: {result.time_spent:.3f}s (target: 0.1s)")

    # Test 2: Depth-based without randomness
    print("\nTest 2: DEPTH-BASED mode (depth=10, no randomness)")
    engine_depth = ChessEngine(max_depth=10)
    result = engine_depth.search(board)
    if result:
        print(f"  Best move: {result.best_move}")
        print(f"  Score: {result.score}")
        print(f"  Depth: {result.depth}")
        print(f"  Time: {result.time_spent:.3f}s")

    # Test 3: Depth-based with randomness
    print("\nTest 3: DEPTH-BASED mode (depth=10, WITH randomness)")
    engine_random = ChessEngine(
        max_depth=10,
        randomness_config={
            'enabled': True,
            'best_move_weight': 0.6,
            'second_move_weight': 0.3,
            'third_move_weight': 0.1
        }
    )

    # Run multiple times to see randomness
    moves = []
    for i in range(5):
        result = engine_random.search(board)
        if result:
            moves.append(result.best_move.uci())
    print(f"  Moves from 5 searches: {moves}")
    print(f"  Unique moves: {len(set(moves))}/5")

    print("\n" + "=" * 50)
    print("Engine tests complete!")
