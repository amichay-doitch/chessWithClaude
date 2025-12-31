"""
Chess Engine v4.0
A strong chess engine with comprehensive evaluation and advanced search.
Designed for competitive play.

Improvements over v3.0:
- Tuned piece values for better material evaluation
"""

import chess
import time
from collections import defaultdict
from engine_base import (
    SearchResult, TTEntry, TT_EXACT, TT_ALPHA, TT_BETA,
    INFINITY, MATE_SCORE, TT_SIZE, CENTER, EXTENDED_CENTER,
    PASSED_PAWN_BONUS, get_game_phase
)
from engine_pst import get_pst_value


class ChessEngine:
    """
    Strong chess engine with advanced evaluation.

    Evaluation features:
    - Material with tuned values
    - Piece-square tables (middlegame/endgame interpolation)
    - Development (piece activity, castling)
    - Center control (pawn center, piece attacks on center)
    - Per-piece mobility
    - Pawn structure (doubled, isolated, passed, connected)
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





















