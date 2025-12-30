"""
FAST Chess Engine - C-like performance with Numba JIT compilation
Uses NumPy arrays and Numba @njit for maximum speed.

Speed optimizations:
- Numba JIT compilation (@njit) - compiles to native machine code
- NumPy arrays for piece-square tables (vectorized operations)
- Minimal Python object creation
- Tight loops optimized by Numba
- Fast bitboard-style evaluation
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
    best_move: chess.Move
    score: int
    depth: int
    nodes_searched: int
    time_spent: float

# Constants for Numba (must be compile-time constants)
PAWN_VALUE = 100
KNIGHT_VALUE = 320
BISHOP_VALUE = 330
ROOK_VALUE = 500
QUEEN_VALUE = 900
KING_VALUE = 20000

INFINITY = 999999
MATE_SCORE = 100000

# Piece-square tables as NumPy arrays (FAST lookup)
PST_PAWN = np.array([
    0,   0,   0,   0,   0,   0,   0,   0,
    50,  50,  50,  50,  50,  50,  50,  50,
    10,  10,  20,  30,  30,  20,  10,  10,
    5,   5,  10,  25,  25,  10,   5,   5,
    0,   0,   0,  20,  20,   0,   0,   0,
    5,  -5, -10,   0,   0, -10,  -5,   5,
    5,  10,  10, -20, -20,  10,  10,   5,
    0,   0,   0,   0,   0,   0,   0,   0
], dtype=np.int32)

PST_KNIGHT = np.array([
    -50, -40, -30, -30, -30, -30, -40, -50,
    -40, -20,   0,   0,   0,   0, -20, -40,
    -30,   0,  10,  15,  15,  10,   0, -30,
    -30,   5,  15,  20,  20,  15,   5, -30,
    -30,   0,  15,  20,  20,  15,   0, -30,
    -30,   5,  10,  15,  15,  10,   5, -30,
    -40, -20,   0,   5,   5,   0, -20, -40,
    -50, -40, -30, -30, -30, -30, -40, -50
], dtype=np.int32)

PST_BISHOP = np.array([
    -20, -10, -10, -10, -10, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,  10,  10,   5,   0, -10,
    -10,   5,   5,  10,  10,   5,   5, -10,
    -10,   0,  10,  10,  10,  10,   0, -10,
    -10,  10,  10,  10,  10,  10,  10, -10,
    -10,   5,   0,   0,   0,   0,   5, -10,
    -20, -10, -10, -10, -10, -10, -10, -20
], dtype=np.int32)

PST_ROOK = np.array([
    0,   0,   0,   0,   0,   0,   0,   0,
    5,  10,  10,  10,  10,  10,  10,   5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    -5,   0,   0,   0,   0,   0,   0,  -5,
    0,   0,   0,   5,   5,   0,   0,   0
], dtype=np.int32)

PST_QUEEN = np.array([
    -20, -10, -10,  -5,  -5, -10, -10, -20,
    -10,   0,   0,   0,   0,   0,   0, -10,
    -10,   0,   5,   5,   5,   5,   0, -10,
    -5,   0,   5,   5,   5,   5,   0,  -5,
    0,   0,   5,   5,   5,   5,   0,  -5,
    -10,   5,   5,   5,   5,   5,   0, -10,
    -10,   0,   5,   0,   0,   0,   0, -10,
    -20, -10, -10,  -5,  -5, -10, -10, -20
], dtype=np.int32)

PST_KING = np.array([
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -30, -40, -40, -50, -50, -40, -40, -30,
    -20, -30, -30, -40, -40, -30, -30, -20,
    -10, -20, -20, -20, -20, -20, -20, -10,
    20,  20,   0,   0,   0,   0,  20,  20,
    20,  30,  10,   0,   0,  10,  30,  20
], dtype=np.int32)

# JIT-compiled evaluation helper
@njit(cache=True)
def eval_position_fast(
    white_pawns, white_knights, white_bishops, white_rooks, white_queens, white_king,
    black_pawns, black_knights, black_bishops, black_rooks, black_queens, black_king
):
    """Ultra-fast position evaluation using NumPy arrays and Numba JIT.

    Takes piece positions as NumPy arrays of square indices.
    Returns evaluation score from white's perspective.
    """
    score = 0

    # White pieces
    for sq in white_pawns:
        if sq >= 0:  # -1 means no piece
            score += PAWN_VALUE + PST_PAWN[sq]
    for sq in white_knights:
        if sq >= 0:
            score += KNIGHT_VALUE + PST_KNIGHT[sq]
    for sq in white_bishops:
        if sq >= 0:
            score += BISHOP_VALUE + PST_BISHOP[sq]
    for sq in white_rooks:
        if sq >= 0:
            score += ROOK_VALUE + PST_ROOK[sq]
    for sq in white_queens:
        if sq >= 0:
            score += QUEEN_VALUE + PST_QUEEN[sq]
    if white_king >= 0:
        score += KING_VALUE + PST_KING[white_king]

    # Black pieces (mirror PST vertically)
    for sq in black_pawns:
        if sq >= 0:
            mirror_sq = sq ^ 56  # Flip rank (0->7, 1->6, ...)
            score -= PAWN_VALUE + PST_PAWN[mirror_sq]
    for sq in black_knights:
        if sq >= 0:
            mirror_sq = sq ^ 56
            score -= KNIGHT_VALUE + PST_KNIGHT[mirror_sq]
    for sq in black_bishops:
        if sq >= 0:
            mirror_sq = sq ^ 56
            score -= BISHOP_VALUE + PST_BISHOP[mirror_sq]
    for sq in black_rooks:
        if sq >= 0:
            mirror_sq = sq ^ 56
            score -= ROOK_VALUE + PST_ROOK[mirror_sq]
    for sq in black_queens:
        if sq >= 0:
            mirror_sq = sq ^ 56
            score -= QUEEN_VALUE + PST_QUEEN[mirror_sq]
    if black_king >= 0:
        mirror_sq = black_king ^ 56
        score -= KING_VALUE + PST_KING[mirror_sq]

    # Bishop pair bonus
    if len(white_bishops) >= 2:
        score += 30
    if len(black_bishops) >= 2:
        score -= 30

    return score


class ChessEngine:
    """Fast chess engine with Numba JIT-compiled evaluation."""

    PIECE_VALUES = {
        chess.PAWN: PAWN_VALUE,
        chess.KNIGHT: KNIGHT_VALUE,
        chess.BISHOP: BISHOP_VALUE,
        chess.ROOK: ROOK_VALUE,
        chess.QUEEN: QUEEN_VALUE,
        chess.KING: KING_VALUE,
    }

    INFINITY = INFINITY
    MATE_SCORE = MATE_SCORE

    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_searched = 0
        self.start_time = 0
        self.time_exceeded = False

        # Search tables
        self.tt = {}
        self.killers = [[None, None] for _ in range(64)]
        self.history = defaultdict(int)

    def clear_tables(self):
        self.tt.clear()
        self.killers = [[None, None] for _ in range(64)]
        self.history.clear()

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        """Iterative deepening search."""
        if depth is None:
            depth = self.max_depth

        self.nodes_searched = 0
        self.start_time = time.time()
        self.time_exceeded = False

        best_move = None
        best_score = -self.INFINITY

        # Iterative deepening
        for d in range(1, depth + 1):
            if self.time_exceeded:
                break

            alpha = -self.INFINITY
            beta = self.INFINITY

            # Search all moves
            moves = self.order_moves(board, None, 0)
            for move in moves:
                board.push(move)
                score = -self.negamax(board, d - 1, -beta, -alpha, 1)
                board.pop()

                if score > best_score:
                    best_score = score
                    best_move = move

                if self.time_limit and (time.time() - self.start_time) >= self.time_limit:
                    self.time_exceeded = True
                    break

        time_spent = time.time() - self.start_time
        return SearchResult(
            best_move=best_move,
            score=best_score,
            depth=d if self.time_exceeded else depth,
            nodes_searched=self.nodes_searched,
            time_spent=time_spent
        )

    def negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        """Alpha-beta search."""
        self.nodes_searched += 1

        # Check time every 1024 nodes
        if self.time_limit and self.nodes_searched % 1024 == 0:
            if (time.time() - self.start_time) >= self.time_limit:
                self.time_exceeded = True
                return 0

        # Terminal conditions
        if board.is_game_over():
            if board.is_checkmate():
                return -self.MATE_SCORE + ply
            return 0

        if depth <= 0:
            return self.evaluate(board)

        # Move ordering
        moves = self.order_moves(board, None, ply)

        for move in moves:
            board.push(move)
            score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()

            if score >= beta:
                # Beta cutoff - update killer moves
                if not board.is_capture(move):
                    if self.killers[ply][0] != move:
                        self.killers[ply][1] = self.killers[ply][0]
                        self.killers[ply][0] = move
                return beta

            if score > alpha:
                alpha = score

        return alpha

    def order_moves(self, board: chess.Board, hash_move, ply: int) -> list:
        """MVV-LVA move ordering."""
        moves = list(board.legal_moves)

        def score_move(move):
            score = 0

            if move == hash_move:
                return 1000000

            # Captures (MVV-LVA)
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if victim and attacker:
                    score += 10000 + self.PIECE_VALUES[victim.piece_type] - self.PIECE_VALUES[attacker.piece_type]

            # Killer moves
            if ply < 64:
                if move == self.killers[ply][0]:
                    score += 9000
                elif move == self.killers[ply][1]:
                    score += 8000

            # History
            score += self.history.get(move, 0)

            return score

        moves.sort(key=score_move, reverse=True)
        return moves

    def evaluate(self, board: chess.Board) -> int:
        """Enhanced evaluation - v5 strength with FAST speed."""
        if board.is_checkmate():
            return -self.MATE_SCORE
        if board.is_stalemate():
            return 0

        # Extract piece positions into NumPy arrays for JIT function
        white_pawns = np.array([sq for sq in board.pieces(chess.PAWN, chess.WHITE)] + [-1] * 8, dtype=np.int32)[:8]
        white_knights = np.array([sq for sq in board.pieces(chess.KNIGHT, chess.WHITE)] + [-1] * 2, dtype=np.int32)[:2]
        white_bishops = np.array([sq for sq in board.pieces(chess.BISHOP, chess.WHITE)] + [-1] * 2, dtype=np.int32)[:2]
        white_rooks = np.array([sq for sq in board.pieces(chess.ROOK, chess.WHITE)] + [-1] * 2, dtype=np.int32)[:2]
        white_queens = np.array([sq for sq in board.pieces(chess.QUEEN, chess.WHITE)] + [-1] * 1, dtype=np.int32)[:1]
        white_king = board.king(chess.WHITE) if board.king(chess.WHITE) is not None else -1

        black_pawns = np.array([sq for sq in board.pieces(chess.PAWN, chess.BLACK)] + [-1] * 8, dtype=np.int32)[:8]
        black_knights = np.array([sq for sq in board.pieces(chess.KNIGHT, chess.BLACK)] + [-1] * 2, dtype=np.int32)[:2]
        black_bishops = np.array([sq for sq in board.pieces(chess.BISHOP, chess.BLACK)] + [-1] * 2, dtype=np.int32)[:2]
        black_rooks = np.array([sq for sq in board.pieces(chess.ROOK, chess.BLACK)] + [-1] * 2, dtype=np.int32)[:2]
        black_queens = np.array([sq for sq in board.pieces(chess.QUEEN, chess.BLACK)] + [-1] * 1, dtype=np.int32)[:1]
        black_king = board.king(chess.BLACK) if board.king(chess.BLACK) is not None else -1

        # Call JIT-compiled evaluation function
        score = eval_position_fast(
            white_pawns, white_knights, white_bishops, white_rooks, white_queens, white_king,
            black_pawns, black_knights, black_bishops, black_rooks, black_queens, black_king
        )

        # Add non-JIT features for strength (v5 level)
        score += self.evaluate_pawn_structure(board)
        score += self.evaluate_king_safety(board)
        score += self.evaluate_piece_activity(board)
        score += self.evaluate_mobility(board)

        # Perspective
        if board.turn == chess.BLACK:
            score = -score

        return score

    def evaluate_pawn_structure(self, board: chess.Board) -> int:
        """Evaluate pawn structure: doubled, isolated, passed pawns."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1
            pawns = list(board.pieces(chess.PAWN, color))

            # File analysis
            files = [chess.square_file(sq) for sq in pawns]
            for sq in pawns:
                file = chess.square_file(sq)
                rank = chess.square_rank(sq)

                # Doubled pawns
                if files.count(file) > 1:
                    score -= sign * 12

                # Isolated pawns
                isolated = True
                for adj_file in [file - 1, file + 1]:
                    if 0 <= adj_file < 8 and any(chess.square_file(p) == adj_file for p in pawns):
                        isolated = False
                if isolated:
                    score -= sign * 15

                # Passed pawns
                passed = True
                for enemy_pawn in board.pieces(chess.PAWN, not color):
                    ef = chess.square_file(enemy_pawn)
                    er = chess.square_rank(enemy_pawn)
                    if abs(ef - file) <= 1:
                        if (color == chess.WHITE and er > rank) or (color == chess.BLACK and er < rank):
                            passed = False
                if passed:
                    bonus = 20 + (rank if color == chess.WHITE else 7 - rank) * 5
                    score += sign * bonus
        return score

    def evaluate_king_safety(self, board: chess.Board) -> int:
        """Evaluate king safety: pawn shield, attackers."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1
            king_sq = board.king(color)
            if king_sq is None:
                continue

            king_rank = chess.square_rank(king_sq)
            king_file = chess.square_file(king_sq)

            # Pawn shield
            shield_pawns = 0
            for df in [-1, 0, 1]:
                if 0 <= king_file + df < 8:
                    shield_rank = king_rank + (1 if color == chess.WHITE else -1)
                    if 0 <= shield_rank < 8:
                        shield_sq = chess.square(king_file + df, shield_rank)
                        piece = board.piece_at(shield_sq)
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            shield_pawns += 1
            score += sign * shield_pawns * 10

            # Attackers near king
            attackers = 0
            for dr in range(-1, 2):
                for df in range(-1, 2):
                    sq = chess.square(king_file + df, king_rank + dr) if 0 <= king_file + df < 8 and 0 <= king_rank + dr < 8 else None
                    if sq:
                        attackers += len(board.attackers(not color, sq))
            score -= sign * attackers * 5
        return score

    def evaluate_piece_activity(self, board: chess.Board) -> int:
        """Evaluate rooks on open files and knight outposts."""
        score = 0
        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1

            # Rooks on open/semi-open files
            for rook_sq in board.pieces(chess.ROOK, color):
                file = chess.square_file(rook_sq)
                own_pawns = any(chess.square_file(p) == file for p in board.pieces(chess.PAWN, color))
                enemy_pawns = any(chess.square_file(p) == file for p in board.pieces(chess.PAWN, not color))

                if not own_pawns and not enemy_pawns:
                    score += sign * 20  # Open file
                elif not own_pawns:
                    score += sign * 10  # Semi-open file

            # Knight outposts
            for knight_sq in board.pieces(chess.KNIGHT, color):
                rank = chess.square_rank(knight_sq)
                if (color == chess.WHITE and rank >= 4) or (color == chess.BLACK and rank <= 3):
                    score += sign * 10
        return score

    def evaluate_mobility(self, board: chess.Board) -> int:
        """Evaluate piece mobility."""
        if board.turn == chess.WHITE:
            white_mob = len(list(board.legal_moves))
            board.push(chess.Move.null())
            black_mob = len(list(board.legal_moves))
            board.pop()
            return (white_mob - black_mob) * 2
        else:
            black_mob = len(list(board.legal_moves))
            board.push(chess.Move.null())
            white_mob = len(list(board.legal_moves))
            board.pop()
            return (black_mob - white_mob) * 2
