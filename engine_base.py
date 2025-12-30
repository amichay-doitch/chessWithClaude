"""
Shared base code for chess engines.

This module contains data structures, constants, and utility functions
that are common across all chess engine implementations.
"""

import chess
from typing import Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Result from engine search."""
    best_move: chess.Move
    score: int
    depth: int
    nodes_searched: int
    time_spent: float


# Transposition table entry types
TT_EXACT = 0
TT_ALPHA = 1
TT_BETA = 2


@dataclass
class TTEntry:
    """Transposition table entry."""
    key: int
    depth: int
    score: int
    flag: int
    best_move: Optional[chess.Move]
    age: int = 0  # Optional field for engines that use age-based replacement


# Universal constants
INFINITY = 999999
MATE_SCORE = 100000
TT_SIZE = 1 << 20  # 1 million entries


# Center squares
CENTER = [chess.D4, chess.E4, chess.D5, chess.E5]
EXTENDED_CENTER = [
    chess.C3, chess.D3, chess.E3, chess.F3,
    chess.C4, chess.D4, chess.E4, chess.F4,
    chess.C5, chess.D5, chess.E5, chess.F5,
    chess.C6, chess.D6, chess.E6, chess.F6,
]


# Passed pawn bonus by rank
PASSED_PAWN_BONUS = [0, 15, 25, 40, 60, 90, 130, 0]


def get_game_phase(board: chess.Board) -> float:
    """
    Calculate game phase (0.0 = opening/middlegame, 1.0 = endgame).

    Phase is based on material count: knights and bishops worth 1 point,
    rooks worth 2 points, queens worth 4 points. Total 24 points.
    As material is traded, phase increases toward 1.0 (endgame).

    Args:
        board: The chess board to evaluate

    Returns:
        float: 0.0 in opening, gradually increases to 1.0 in endgame
    """
    phase = 0
    phase += len(board.pieces(chess.KNIGHT, chess.WHITE)) * 1
    phase += len(board.pieces(chess.KNIGHT, chess.BLACK)) * 1
    phase += len(board.pieces(chess.BISHOP, chess.WHITE)) * 1
    phase += len(board.pieces(chess.BISHOP, chess.BLACK)) * 1
    phase += len(board.pieces(chess.ROOK, chess.WHITE)) * 2
    phase += len(board.pieces(chess.ROOK, chess.BLACK)) * 2
    phase += len(board.pieces(chess.QUEEN, chess.WHITE)) * 4
    phase += len(board.pieces(chess.QUEEN, chess.BLACK)) * 4
    return 1.0 - min(phase / 24.0, 1.0)
