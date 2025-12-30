"""
Piece-Square Tables (PSTs) for chess engines.

PSTs provide positional bonuses/penalties for pieces based on their square.
These tables are used to encourage pieces to occupy strong squares.

The values are from the perspective of White; they are automatically
mirrored for Black pieces.
"""

import chess


# Pawn tables with middlegame/endgame variants
# Pawns should advance and control center in MG, push passed pawns in EG
PAWN_TABLE_MG = [
     0,  0,  0,  0,  0,  0,  0,  0,
    60, 60, 60, 65, 65, 60, 60, 60,
    20, 25, 35, 45, 45, 35, 25, 20,
    10, 12, 22, 35, 35, 22, 12, 10,
     5,  8, 15, 28, 28, 15,  8,  5,
     3,  5,  5, 15, 15,  5,  5,  3,
     5, 10,  0,-15,-15,  0, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
]

PAWN_TABLE_EG = [
     0,  0,  0,  0,  0,  0,  0,  0,
    80, 80, 80, 80, 80, 80, 80, 80,
    50, 50, 50, 50, 50, 50, 50, 50,
    30, 30, 30, 30, 30, 30, 30, 30,
    15, 15, 15, 15, 15, 15, 15, 15,
     5,  5,  5,  5,  5,  5,  5,  5,
     0,  0,  0,  0,  0,  0,  0,  0,
     0,  0,  0,  0,  0,  0,  0,  0,
]


# Knights should be centralized and avoid the rim
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30, 10, 20, 25, 25, 20, 10,-30,
    -30, 10, 20, 25, 25, 20, 10,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50,
]


# Bishops should control diagonals and avoid the rim
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  0, 15, 15, 15, 15,  0,-10,
    -10,  5, 15, 15, 15, 15,  5,-10,
    -10,  0, 10, 15, 15, 10,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10,-10,-10,-10,-10,-20,
]


# Rooks should be on the 7th rank and back rank
ROOK_TABLE = [
    10, 10, 10, 10, 10, 10, 10, 10,
    15, 20, 20, 20, 20, 20, 20, 15,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  5, 10, 10,  5,  0,  0,
]


# Queens should be centralized but not exposed early
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
     -5,  0,  5,  5,  5,  5,  0, -5,
    -10,  0,  5,  5,  5,  5,  0,-10,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20,
]


# King should castle and stay safe in middlegame, centralize in endgame
KING_TABLE_MG = [
    -40,-40,-40,-50,-50,-40,-40,-40,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-30,-30,-20,-20,-10,
    -10,-15,-15,-20,-20,-15,-15,-10,
      0,  0, -5,-10,-10, -5,  0,  0,
     15, 15,  0, -5, -5,  0, 15, 15,
     20, 35, 15,  0,  0, 15, 35, 20,
]

KING_TABLE_EG = [
    -50,-30,-20,-10,-10,-20,-30,-50,
    -30,-10,  0, 10, 10,  0,-10,-30,
    -20,  0, 20, 30, 30, 20,  0,-20,
    -10, 10, 30, 40, 40, 30, 10,-10,
    -10, 10, 30, 40, 40, 30, 10,-10,
    -20,  0, 20, 30, 30, 20,  0,-20,
    -30,-10,  0, 10, 10,  0,-10,-30,
    -50,-30,-20,-10,-10,-20,-30,-50,
]


def get_pst_value(piece: chess.Piece, square: int, phase: float = 0.0) -> int:
    """
    Get piece-square table value for a piece on a square.

    For pawns and kings, interpolates between middlegame and endgame tables
    based on game phase. Other pieces use single tables.

    Args:
        piece: The chess piece
        square: The square index (0-63)
        phase: Game phase (0.0 = opening/MG, 1.0 = endgame)

    Returns:
        int: Positional bonus/penalty in centipawns
    """
    # Mirror square for Black pieces (PSTs are from White's perspective)
    sq = square if piece.color == chess.WHITE else chess.square_mirror(square)
    pt = piece.piece_type

    if pt == chess.PAWN:
        mg = PAWN_TABLE_MG[sq]
        eg = PAWN_TABLE_EG[sq]
        return int(mg * (1 - phase) + eg * phase)
    elif pt == chess.KNIGHT:
        return KNIGHT_TABLE[sq]
    elif pt == chess.BISHOP:
        return BISHOP_TABLE[sq]
    elif pt == chess.ROOK:
        return ROOK_TABLE[sq]
    elif pt == chess.QUEEN:
        return QUEEN_TABLE[sq]
    elif pt == chess.KING:
        mg = KING_TABLE_MG[sq]
        eg = KING_TABLE_EG[sq]
        return int(mg * (1 - phase) + eg * phase)
    return 0
