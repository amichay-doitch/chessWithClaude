"""
Stockfish Son Chess Engine - Stockfish Wrapper for Tournament Play

This engine wraps Stockfish to enable tournament play with adjustable strength
and move randomness for generating diverse training data.

Features:
- Adjustable ELO rating (1320-3190)
- Time control support
- Move randomness for diverse training data (select 2nd/3rd best moves)
- Full tournament integration
- Self-play support: Run Stockfish vs Stockfish with different configs
- Training data generation: Create large datasets of varied games

Usage Examples:
    # Deterministic tournament play at 2400 ELO
    engine = ChessEngine(max_depth=22, elo_rating=2400)

    # Training data generation with randomness
    engine = ChessEngine(
        max_depth=18,
        elo_rating=1800,
        randomness_config={
            'enabled': True,
            'best_move_weight': 0.6,
            'second_move_weight': 0.3,
            'third_move_weight': 0.1
        }
    )

    # Time-controlled play
    engine = ChessEngine(max_depth=20, time_limit=3.0, elo_rating=2200)

    # Full strength Stockfish
    engine = ChessEngine(max_depth=25, threads=4, hash_size=128)

Tournament Self-Play:
    python tournament.py \\
      --engine1 engine_pool.stockfishSonChessEngine \\
      --engine2 engine_pool.stockfishSonChessEngine \\
      --games 100 \\
      --depth1 18 \\
      --depth2 22 \\
      --time 2.0
"""

import chess
import time
import random
import sys
import os
from typing import Optional
from dataclasses import dataclass

# Add parent directory to path to import stockfish_analyzer
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from stockfish_analyzer import StockfishAnalyzer


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
    Stockfish wrapper engine with ELO rating and randomness support.

    Wraps Stockfish for tournament play with the following capabilities:
    - Adjustable strength via ELO rating or skill level
    - Move randomness for generating diverse training games
    - Time control support
    - Full compatibility with tournament system

    The engine can be instantiated multiple times with different parameters
    to enable self-play scenarios for training data generation.
    """

    # ELO rating bounds supported by Stockfish
    MIN_ELO = 1320
    MAX_ELO = 3190

    def __init__(
        self,
        max_depth: int = 20,
        time_limit: Optional[float] = None,
        elo_rating: Optional[int] = None,
        skill_level: Optional[int] = None,
        threads: int = 1,
        hash_size: int = 16,
        randomness_config: Optional[dict] = None,
        stockfish_path: Optional[str] = None
    ):
        """
        Initialize Stockfish wrapper engine.

        Args:
            max_depth: Search depth (default: 20, good balance for Stockfish)
            time_limit: Time limit per move in seconds (measured but not strictly enforced by Stockfish)
            elo_rating: Limit Stockfish to specific ELO (1320-3190, None = full strength ~3190)
            skill_level: Alternative strength control 0-20 (None = full strength)
            threads: Number of CPU threads (default: 1)
            hash_size: Hash table size in MB (default: 16)
            randomness_config: Dictionary controlling move selection randomness:
                {
                    'enabled': bool,              # Enable randomness (default: False)
                    'best_move_weight': float,    # Probability for best move (default: 0.7)
                    'second_move_weight': float,  # Probability for 2nd best (default: 0.2)
                    'third_move_weight': float    # Probability for 3rd best (default: 0.1)
                }
            stockfish_path: Path to Stockfish binary (default: auto-detect)

        Raises:
            ValueError: If ELO rating is out of valid range or randomness weights invalid
        """
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.stockfish_path = stockfish_path
        self.threads = threads
        self.hash_size = hash_size

        # Validate and store ELO rating
        if elo_rating is not None:
            if elo_rating < self.MIN_ELO or elo_rating > self.MAX_ELO:
                raise ValueError(
                    f"ELO rating must be between {self.MIN_ELO} and {self.MAX_ELO}, "
                    f"got {elo_rating}"
                )
        self.elo_rating = elo_rating
        self.skill_level = skill_level

        # Parse randomness configuration
        self.randomness_enabled = False
        self.move_weights = [1.0, 0.0, 0.0]  # Default: always pick best move

        if randomness_config:
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
        Supports both depth-based and time-based control, with randomness for
        generating diverse training data.

        Args:
            board: Chess position to analyze
            depth: Search depth override (uses max_depth if None)

        Returns:
            SearchResult with best move and evaluation, or None if no legal moves
        """
        start_time = time.time()

        # Check for no legal moves (checkmate or stalemate)
        if not any(board.legal_moves):
            return None

        # Determine search depth
        if depth is None:
            depth = self.max_depth

        # Initialize Stockfish with configured parameters
        with StockfishAnalyzer(
            stockfish_path=self.stockfish_path,
            depth=depth,
            elo_rating=self.elo_rating,
            skill_level=self.skill_level,
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
                # (shouldn't happen if there are legal moves)
                selected_move = analysis.best_move
                # Rough score estimate from evaluation
                score = int(analysis.evaluation * 100)
                if board.turn == chess.BLACK:
                    score = -score

            # Extract statistics
            nodes = 0
            if analysis.verbose_stats:
                nodes = analysis.verbose_stats.nodes

        # Calculate actual time spent (including Stockfish overhead)
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

    board = chess.Board()

    # Test 1: Basic search
    print("\nTest 1: Basic search at starting position")
    engine = ChessEngine(max_depth=15, elo_rating=2000)
    result = engine.search(board)
    if result:
        print(f"  Best move: {result.best_move}")
        print(f"  Score: {result.score}")
        print(f"  Depth: {result.depth}")
        print(f"  Nodes: {result.nodes_searched:,}")
        print(f"  Time: {result.time_spent:.3f}s")

    # Test 2: With randomness
    print("\nTest 2: Search with randomness enabled")
    engine_random = ChessEngine(
        max_depth=15,
        elo_rating=1800,
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

    print("\nEngine tests complete!")
