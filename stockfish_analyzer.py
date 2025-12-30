"""
Stockfish Chess Engine Analyzer
Provides interface to Stockfish for position analysis and evaluation.

NEW: Supports top-N moves, ELO testing, verbose search statistics
"""

from stockfish import Stockfish
import chess
from typing import Optional, List
from dataclasses import dataclass


@dataclass
class MoveAnalysis:
    """Single move with evaluation details."""
    move: chess.Move
    move_uci: str
    centipawn: Optional[int]
    mate: Optional[int]
    rank: int  # 1 = best, 2 = second best, etc.


@dataclass
class VerboseStats:
    """Detailed search statistics."""
    nodes: int
    nps: int  # Nodes per second
    seldepth: int  # Selective depth
    time_ms: int


@dataclass
class StockfishAnalysis:
    """Enhanced result from Stockfish analysis."""
    best_move: chess.Move
    evaluation: float  # in pawns (for backward compatibility)
    depth: int

    # NEW FIELDS:
    top_moves: Optional[List[MoveAnalysis]] = None
    verbose_stats: Optional[VerboseStats] = None
    wdl: Optional[dict] = None  # {'win': float, 'draw': float, 'loss': float}


class StockfishAnalyzer:
    """
    Wrapper for Stockfish chess engine analysis using stockfish library.

    NEW: Supports top-N moves, ELO testing, verbose stats

    Usage:
        # Basic (backward compatible)
        with StockfishAnalyzer() as analyzer:
            analysis = analyzer.analyze(board)
            print(f"Best move: {analysis.best_move}")

        # With top moves
        with StockfishAnalyzer() as analyzer:
            analysis = analyzer.analyze(board, top_n=3)
            for move_analysis in analysis.top_moves:
                print(f"{move_analysis.rank}. {move_analysis.move_uci}")

        # ELO testing
        with StockfishAnalyzer(elo_rating=1500) as analyzer:
            analysis = analyzer.analyze(board)
    """

    def __init__(
        self,
        stockfish_path: str = None,
        depth: int = 20,
        elo_rating: Optional[int] = None,
        skill_level: Optional[int] = None,
        threads: int = 1,
        hash_size: int = 16
    ):
        """
        Initialize Stockfish analyzer.

        Args:
            stockfish_path: Path to Stockfish binary (default: auto-detect in script directory)
            depth: Search depth (default: 20)
            elo_rating: Limit Stockfish to specific ELO (None = full strength)
            skill_level: Skill level 0-20 (None = full strength)
            threads: Number of threads for analysis
            hash_size: Hash table size in MB
        """
        # Auto-detect stockfish executable in script directory
        if stockfish_path is None:
            import os
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.stockfish_path = os.path.join(script_dir, "data/stockfish-windows-x86-64-avx2.exe")
        else:
            self.stockfish_path = stockfish_path
        self.depth = depth
        self.elo_rating = elo_rating
        self.skill_level = skill_level
        self.threads = threads
        self.hash_size = hash_size
        self.engine: Optional[Stockfish] = None

    def __enter__(self):
        """Start Stockfish engine."""
        try:
            # Initialize with parameters
            parameters = {
                "Threads": self.threads,
                "Hash": self.hash_size,
            }

            self.engine = Stockfish(
                path=self.stockfish_path,
                depth=self.depth,
                parameters=parameters
            )

            # Apply ELO/skill limits if specified
            if self.elo_rating is not None:
                self.engine.set_elo_rating(self.elo_rating)
            elif self.skill_level is not None:
                self.engine.set_skill_level(self.skill_level)

            return self

        except Exception as e:
            raise FileNotFoundError(
                f"Stockfish not found at '{self.stockfish_path}'. "
                f"Error: {e}. "
                "Please download from https://stockfishchess.org/download/ "
                "and ensure it's in your PATH or specify the full path."
            )

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop Stockfish engine."""
        if self.engine:
            # Stockfish library handles cleanup internally
            self.engine = None

    def analyze(
        self,
        board: chess.Board,
        top_n: int = 1,
        verbose: bool = False
    ) -> StockfishAnalysis:
        """
        Analyze position and return best move + evaluation.

        Args:
            board: Chess board position to analyze
            top_n: Number of top moves to return (default: 1)
            verbose: Include detailed search statistics (default: False)

        Returns:
            StockfishAnalysis with move(s) and evaluation

        Raises:
            RuntimeError: If engine is not initialized
        """
        if not self.engine:
            raise RuntimeError("Stockfish engine not initialized. Use with context manager.")

        # Set position using FEN
        fen = board.fen()
        self.engine.set_fen_position(fen)

        # Get top moves with verbose stats if requested
        top_moves_data = self.engine.get_top_moves(top_n, verbose=verbose)

        # Parse top moves into MoveAnalysis objects
        top_moves = []
        for rank, move_data in enumerate(top_moves_data, start=1):
            move_uci = move_data['Move']
            move_obj = chess.Move.from_uci(move_uci)

            top_moves.append(MoveAnalysis(
                move=move_obj,
                move_uci=move_uci,
                centipawn=move_data.get('Centipawn'),
                mate=move_data.get('Mate'),
                rank=rank
            ))

        # Extract best move (first in list)
        best_move = top_moves[0].move

        # Calculate evaluation in pawns (backward compatible)
        if top_moves[0].mate is not None:
            # Mate in N moves
            eval_pawns = 100.0 if top_moves[0].mate > 0 else -100.0
        elif top_moves[0].centipawn is not None:
            eval_pawns = top_moves[0].centipawn / 100.0
        else:
            eval_pawns = 0.0

        # Extract verbose stats if requested
        verbose_stats = None
        if verbose and len(top_moves_data) > 0:
            first_move = top_moves_data[0]
            # Check if all verbose keys are present
            verbose_keys = ['Nodes', 'NPS', 'SelectiveDepth', 'Time']
            if all(k in first_move for k in verbose_keys):
                verbose_stats = VerboseStats(
                    nodes=first_move['Nodes'],
                    nps=first_move['NPS'],
                    seldepth=first_move['SelectiveDepth'],
                    time_ms=first_move['Time']
                )

        return StockfishAnalysis(
            best_move=best_move,
            evaluation=eval_pawns,
            depth=self.depth,
            top_moves=top_moves if top_n > 1 else None,
            verbose_stats=verbose_stats
        )
