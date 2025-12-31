"""
Chess Engine v5 FAST
V5's exact brain with Numba JIT for 2-3x speed boost.

Same evaluation and search as V5, just faster execution.
"""

import chess
import time
import numpy as np
from numba import njit
from typing import Optional
from dataclasses import dataclass
from collections import defaultdict


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


# JIT-compiled fast material counter
@njit(cache=True)
def count_material_fast(
    white_pawns, white_knights, white_bishops, white_rooks, white_queens, white_king,
    black_pawns, black_knights, black_bishops, black_rooks, black_queens, black_king,
    pawn_table, knight_table, bishop_table, rook_table, queen_table, king_table
):
    """Fast material + PST calculation using Numba JIT."""
    score = 0

    # White pieces
    for sq in white_pawns:
        if sq >= 0:
            score += 100 + pawn_table[sq]
    for sq in white_knights:
        if sq >= 0:
            score += 305 + knight_table[sq]
    for sq in white_bishops:
        if sq >= 0:
            score += 333 + bishop_table[sq]
    for sq in white_rooks:
        if sq >= 0:
            score += 500 + rook_table[sq]
    for sq in white_queens:
        if sq >= 0:
            score += 900 + queen_table[sq]
    if white_king >= 0:
        score += 20000 + king_table[white_king]

    # Black pieces (mirror PST vertically)
    for sq in black_pawns:
        if sq >= 0:
            mirror_sq = sq ^ 56  # XOR with 56 flips rank
            score -= 100 + pawn_table[mirror_sq]
    for sq in black_knights:
        if sq >= 0:
            mirror_sq = sq ^ 56
            score -= 305 + knight_table[mirror_sq]
    for sq in black_bishops:
        if sq >= 0:
            mirror_sq = sq ^ 56
            score -= 333 + bishop_table[mirror_sq]
    for sq in black_rooks:
        if sq >= 0:
            mirror_sq = sq ^ 56
            score -= 500 + rook_table[mirror_sq]
    for sq in black_queens:
        if sq >= 0:
            mirror_sq = sq ^ 56
            score -= 900 + queen_table[mirror_sq]
    if black_king >= 0:
        mirror_sq = black_king ^ 56
        score -= 20000 + king_table[mirror_sq]

    return score


# NumPy PST arrays for JIT (initialized from class tables later)
# These will be set in __init__ from the class-level PST tables
PST_PAWN_MG_NP = None
PST_PAWN_EG_NP = None
PST_KNIGHT_NP = None
PST_BISHOP_NP = None
PST_ROOK_NP = None
PST_QUEEN_NP = None
PST_KING_MG_NP = None
PST_KING_EG_NP = None


class ChessEngine:
    """
    Strong chess engine with advanced evaluation.

    Evaluation features:
    - Material with tuned values
    - Piece-square tables (middlegame/endgame interpolation)
    - Development (piece activity, castling)
    - Center control (pawn center, piece attacks on center)
    - Per-piece mobility
    - Pawn structure (doubled, isolated, passed, connected, chains)
    - King safety (pawn shield, attackers near king)
    - Bishop pair, bad bishops
    - Rook on open/semi-open files
    - Knight outposts
    - Threats and hanging pieces
    """

    # Piece values in centipawns (v4.0: tuned for better evaluation)
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 305,      # Reduced: knights slightly less valuable
        chess.BISHOP: 333,      # Slightly reduced but still > knight
        chess.ROOK: 500,        # Unchanged
        chess.QUEEN: 900,       # Reduced: queen often overvalued
        chess.KING: 20000,      # Unchanged
    }

    # Mobility bonus per move for each piece type
    MOBILITY_BONUS = {
        chess.KNIGHT: 4,
        chess.BISHOP: 5,
        chess.ROOK: 2,
        chess.QUEEN: 1,
    }





















