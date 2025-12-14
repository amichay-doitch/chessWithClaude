"""
Chess Engine v3.0
A strong chess engine with comprehensive evaluation and advanced search.
Designed for competitive play.
"""

import chess
import time
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

    # Piece values in centipawns
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 335,
        chess.ROOK: 500,
        chess.QUEEN: 975,
        chess.KING: 20000,
    }

    # Mobility bonus per move for each piece type
    MOBILITY_BONUS = {
        chess.KNIGHT: 4,
        chess.BISHOP: 5,
        chess.ROOK: 2,
        chess.QUEEN: 1,
    }

    # Center squares
    CENTER = [chess.D4, chess.E4, chess.D5, chess.E5]
    EXTENDED_CENTER = [
        chess.C3, chess.D3, chess.E3, chess.F3,
        chess.C4, chess.D4, chess.E4, chess.F4,
        chess.C5, chess.D5, chess.E5, chess.F5,
        chess.C6, chess.D6, chess.E6, chess.F6,
    ]

    # Piece-square tables
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

    # Passed pawn bonus by rank
    PASSED_PAWN_BONUS = [0, 15, 25, 40, 60, 90, 130, 0]

    # Constants
    INFINITY = 999999
    MATE_SCORE = 100000
    TT_SIZE = 1 << 20

    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_searched = 0
        self.start_time = 0
        self.time_exceeded = False
        self.tt = {}
        self.killers = [[None, None] for _ in range(64)]
        self.history = defaultdict(int)

    def clear_tables(self):
        self.tt.clear()
        self.killers = [[None, None] for _ in range(64)]
        self.history.clear()

    def get_game_phase(self, board: chess.Board) -> float:
        """0.0 = opening/middlegame, 1.0 = endgame"""
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

    def get_pst_value(self, piece: chess.Piece, square: int, phase: float) -> int:
        """Get piece-square table value with phase interpolation."""
        sq = square if piece.color == chess.WHITE else chess.square_mirror(square)
        pt = piece.piece_type

        if pt == chess.PAWN:
            mg = self.PAWN_TABLE_MG[sq]
            eg = self.PAWN_TABLE_EG[sq]
            return int(mg * (1 - phase) + eg * phase)
        elif pt == chess.KNIGHT:
            return self.KNIGHT_TABLE[sq]
        elif pt == chess.BISHOP:
            return self.BISHOP_TABLE[sq]
        elif pt == chess.ROOK:
            return self.ROOK_TABLE[sq]
        elif pt == chess.QUEEN:
            return self.QUEEN_TABLE[sq]
        elif pt == chess.KING:
            mg = self.KING_TABLE_MG[sq]
            eg = self.KING_TABLE_EG[sq]
            return int(mg * (1 - phase) + eg * phase)
        return 0

    def evaluate_development(self, board: chess.Board, phase: float) -> int:
        """Evaluate piece development (important in opening/early middlegame)."""
        if phase > 0.5:
            return 0

        score = 0
        weight = 1.0 - phase * 2  # Fade out by middlegame

        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1
            back_rank = 0 if color == chess.WHITE else 7
            dev_score = 0

            # Penalty for knights on back rank
            for sq in board.pieces(chess.KNIGHT, color):
                if chess.square_rank(sq) == back_rank:
                    dev_score -= 25

            # Penalty for bishops on back rank
            for sq in board.pieces(chess.BISHOP, color):
                if chess.square_rank(sq) == back_rank:
                    dev_score -= 25

            # Bonus for castling done, penalty for lost castling rights
            if color == chess.WHITE:
                king_sq = board.king(chess.WHITE)
                if king_sq in [chess.G1, chess.C1]:  # Castled
                    dev_score += 40
                elif not board.has_kingside_castling_rights(chess.WHITE) and not board.has_queenside_castling_rights(chess.WHITE):
                    if king_sq == chess.E1:  # King stuck in center
                        dev_score -= 40
            else:
                king_sq = board.king(chess.BLACK)
                if king_sq in [chess.G8, chess.C8]:  # Castled
                    dev_score += 40
                elif not board.has_kingside_castling_rights(chess.BLACK) and not board.has_queenside_castling_rights(chess.BLACK):
                    if king_sq == chess.E8:
                        dev_score -= 40

            # Penalty for moving queen too early before minor pieces
            queen_sq = list(board.pieces(chess.QUEEN, color))
            if queen_sq:
                q_rank = chess.square_rank(queen_sq[0])
                if color == chess.WHITE and q_rank > 1:  # Queen moved out
                    # Count unmoved minor pieces
                    unmoved_minors = 0
                    for sq in board.pieces(chess.KNIGHT, color):
                        if chess.square_rank(sq) == back_rank:
                            unmoved_minors += 1
                    for sq in board.pieces(chess.BISHOP, color):
                        if chess.square_rank(sq) == back_rank:
                            unmoved_minors += 1
                    dev_score -= unmoved_minors * 15
                elif color == chess.BLACK and q_rank < 6:
                    unmoved_minors = 0
                    for sq in board.pieces(chess.KNIGHT, color):
                        if chess.square_rank(sq) == back_rank:
                            unmoved_minors += 1
                    for sq in board.pieces(chess.BISHOP, color):
                        if chess.square_rank(sq) == back_rank:
                            unmoved_minors += 1
                    dev_score -= unmoved_minors * 15

            # Penalty for blocked center pawns
            if color == chess.WHITE:
                # e2 pawn blocked
                if board.piece_at(chess.E2) == chess.Piece(chess.PAWN, chess.WHITE):
                    if board.piece_at(chess.E3):
                        dev_score -= 20
                # d2 pawn blocked
                if board.piece_at(chess.D2) == chess.Piece(chess.PAWN, chess.WHITE):
                    if board.piece_at(chess.D3):
                        dev_score -= 20
            else:
                if board.piece_at(chess.E7) == chess.Piece(chess.PAWN, chess.BLACK):
                    if board.piece_at(chess.E6):
                        dev_score -= 20
                if board.piece_at(chess.D7) == chess.Piece(chess.PAWN, chess.BLACK):
                    if board.piece_at(chess.D6):
                        dev_score -= 20

            score += sign * int(dev_score * weight)

        return score

    def evaluate_center_control(self, board: chess.Board) -> int:
        """Evaluate control of the center."""
        score = 0

        # Pawns in center
        for sq in self.CENTER:
            piece = board.piece_at(sq)
            if piece and piece.piece_type == chess.PAWN:
                bonus = 25 if piece.color == chess.WHITE else -25
                score += bonus

        # Pieces attacking center
        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1
            attacks_center = 0

            for sq in self.CENTER:
                attackers = board.attackers(color, sq)
                attacks_center += len(attackers) * 5

            for sq in self.EXTENDED_CENTER:
                if sq not in self.CENTER:
                    attackers = board.attackers(color, sq)
                    attacks_center += len(attackers) * 2

            score += sign * attacks_center

        return score

    def evaluate_mobility(self, board: chess.Board) -> int:
        """Evaluate piece mobility with per-piece bonuses."""
        score = 0

        # We need to calculate attacks for each piece
        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1

            for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                for sq in board.pieces(pt, color):
                    # Count squares this piece attacks
                    attacks = board.attacks(sq)
                    mobility = bin(attacks).count('1')
                    score += sign * mobility * self.MOBILITY_BONUS[pt]

        return score

    def evaluate_pawns(self, board: chess.Board, phase: float) -> int:
        """Evaluate pawn structure."""
        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1
            pawns = board.pieces(chess.PAWN, color)
            enemy_pawns = board.pieces(chess.PAWN, not color)

            pawns_per_file = [0] * 8
            for sq in pawns:
                pawns_per_file[chess.square_file(sq)] += 1

            for sq in pawns:
                file = chess.square_file(sq)
                rank = chess.square_rank(sq)

                # Doubled pawns
                if pawns_per_file[file] > 1:
                    score -= sign * 15

                # Isolated pawns
                has_neighbor = (file > 0 and pawns_per_file[file - 1] > 0) or \
                               (file < 7 and pawns_per_file[file + 1] > 0)
                if not has_neighbor:
                    score -= sign * 20

                # Backward pawns
                if has_neighbor:
                    is_backward = True
                    pawn_rank = rank if color == chess.WHITE else 7 - rank
                    for adj_file in [file - 1, file + 1]:
                        if 0 <= adj_file < 8 and pawns_per_file[adj_file] > 0:
                            for pawn_sq in pawns:
                                if chess.square_file(pawn_sq) == adj_file:
                                    adj_rank = chess.square_rank(pawn_sq)
                                    adj_pawn_rank = adj_rank if color == chess.WHITE else 7 - adj_rank
                                    if adj_pawn_rank <= pawn_rank:
                                        is_backward = False
                    if is_backward:
                        score -= sign * 10

                # Passed pawns
                is_passed = True
                if color == chess.WHITE:
                    for r in range(rank + 1, 8):
                        for f in range(max(0, file - 1), min(8, file + 2)):
                            test_sq = chess.square(f, r)
                            if test_sq in enemy_pawns:
                                is_passed = False
                                break
                        if not is_passed:
                            break
                else:
                    for r in range(rank - 1, -1, -1):
                        for f in range(max(0, file - 1), min(8, file + 2)):
                            test_sq = chess.square(f, r)
                            if test_sq in enemy_pawns:
                                is_passed = False
                                break
                        if not is_passed:
                            break

                if is_passed:
                    bonus_rank = rank if color == chess.WHITE else 7 - rank
                    base_bonus = self.PASSED_PAWN_BONUS[bonus_rank]
                    # Extra bonus in endgame
                    bonus = int(base_bonus * (1 + phase * 0.5))
                    score += sign * bonus

                    # Connected passed pawns
                    for adj_file in [file - 1, file + 1]:
                        if 0 <= adj_file < 8:
                            adj_sq = chess.square(adj_file, rank)
                            if adj_sq in pawns:
                                score += sign * 15

        return score

    def evaluate_king_safety(self, board: chess.Board, phase: float) -> int:
        """Evaluate king safety."""
        if phase > 0.7:
            return 0

        score = 0
        weight = 1.0 - phase

        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1
            king_sq = board.king(color)
            if king_sq is None:
                continue

            king_file = chess.square_file(king_sq)
            king_rank = chess.square_rank(king_sq)
            safety = 0

            # Pawn shield
            pawn_direction = 1 if color == chess.WHITE else -1
            shield_bonus = 0
            for f in range(max(0, king_file - 1), min(8, king_file + 2)):
                for r_offset in [1, 2]:
                    r = king_rank + pawn_direction * r_offset
                    if 0 <= r < 8:
                        sq = chess.square(f, r)
                        piece = board.piece_at(sq)
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            shield_bonus += 12 if r_offset == 1 else 6
                            break

            safety += shield_bonus

            # Penalty for open files near king
            for f in range(max(0, king_file - 1), min(8, king_file + 2)):
                has_own_pawn = False
                has_enemy_pawn = False
                for r in range(8):
                    sq = chess.square(f, r)
                    piece = board.piece_at(sq)
                    if piece and piece.piece_type == chess.PAWN:
                        if piece.color == color:
                            has_own_pawn = True
                        else:
                            has_enemy_pawn = True

                if not has_own_pawn and not has_enemy_pawn:
                    safety -= 25  # Open file
                elif not has_own_pawn:
                    safety -= 15  # Semi-open

            # Count attackers near king
            king_zone = []
            for f in range(max(0, king_file - 2), min(8, king_file + 3)):
                for r in range(max(0, king_rank - 2), min(8, king_rank + 3)):
                    king_zone.append(chess.square(f, r))

            enemy = not color
            attacker_count = 0
            for sq in king_zone:
                attackers = board.attackers(enemy, sq)
                for att_sq in attackers:
                    piece = board.piece_at(att_sq)
                    if piece and piece.piece_type != chess.PAWN:
                        attacker_count += 1

            safety -= attacker_count * 8

            score += sign * int(safety * weight)

        return score

    def evaluate_pieces(self, board: chess.Board, phase: float) -> int:
        """Evaluate individual piece features."""
        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1

            # Bishop pair
            if len(board.pieces(chess.BISHOP, color)) >= 2:
                score += sign * 45

            # Bad bishop (blocked by own pawns)
            own_pawns = board.pieces(chess.PAWN, color)
            for bishop_sq in board.pieces(chess.BISHOP, color):
                # Light or dark square bishop
                is_light = (chess.square_file(bishop_sq) + chess.square_rank(bishop_sq)) % 2 == 1
                blocking_pawns = 0
                for pawn_sq in own_pawns:
                    pawn_is_light = (chess.square_file(pawn_sq) + chess.square_rank(pawn_sq)) % 2 == 1
                    if pawn_is_light == is_light:
                        blocking_pawns += 1
                score -= sign * blocking_pawns * 5

            # Rook on open/semi-open file
            for rook_sq in board.pieces(chess.ROOK, color):
                file = chess.square_file(rook_sq)
                has_own_pawn = False
                has_enemy_pawn = False
                for r in range(8):
                    sq = chess.square(file, r)
                    piece = board.piece_at(sq)
                    if piece and piece.piece_type == chess.PAWN:
                        if piece.color == color:
                            has_own_pawn = True
                        else:
                            has_enemy_pawn = True

                if not has_own_pawn and not has_enemy_pawn:
                    score += sign * 25  # Open file
                elif not has_own_pawn:
                    score += sign * 12  # Semi-open file

            # Rook on 7th rank (2nd rank for black)
            seventh_rank = 6 if color == chess.WHITE else 1
            for rook_sq in board.pieces(chess.ROOK, color):
                if chess.square_rank(rook_sq) == seventh_rank:
                    score += sign * 20

            # Knight outposts (knight protected by pawn, can't be attacked by enemy pawn)
            for knight_sq in board.pieces(chess.KNIGHT, color):
                file = chess.square_file(knight_sq)
                rank = chess.square_rank(knight_sq)

                # Is it protected by own pawn?
                protected = False
                pawn_rank = rank - 1 if color == chess.WHITE else rank + 1
                if 0 <= pawn_rank < 8:
                    for pawn_file in [file - 1, file + 1]:
                        if 0 <= pawn_file < 8:
                            pawn_sq = chess.square(pawn_file, pawn_rank)
                            piece = board.piece_at(pawn_sq)
                            if piece and piece.piece_type == chess.PAWN and piece.color == color:
                                protected = True
                                break

                # Can it be attacked by enemy pawn?
                can_be_attacked = False
                enemy = not color
                enemy_pawns = board.pieces(chess.PAWN, enemy)
                for ep_sq in enemy_pawns:
                    ep_file = chess.square_file(ep_sq)
                    ep_rank = chess.square_rank(ep_sq)
                    if abs(ep_file - file) == 1:
                        if color == chess.WHITE and ep_rank > rank:
                            can_be_attacked = True
                        elif color == chess.BLACK and ep_rank < rank:
                            can_be_attacked = True

                if protected and not can_be_attacked:
                    # Outpost in enemy territory
                    outpost_rank = rank if color == chess.WHITE else 7 - rank
                    if outpost_rank >= 4:
                        score += sign * (15 + outpost_rank * 3)

        return score

    def evaluate_threats(self, board: chess.Board) -> int:
        """Evaluate threats and hanging pieces."""
        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            sign = 1 if color == chess.WHITE else -1
            enemy = not color

            # Check for hanging pieces (attacked but not defended)
            for pt in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
                for sq in board.pieces(pt, color):
                    attackers = board.attackers(enemy, sq)
                    defenders = board.attackers(color, sq)

                    if attackers and not defenders:
                        # Hanging piece!
                        score -= sign * (self.PIECE_VALUES[pt] // 4)
                    elif attackers:
                        # Attacked by lesser piece?
                        min_attacker_value = min(
                            self.PIECE_VALUES[board.piece_at(att_sq).piece_type]
                            for att_sq in attackers
                        )
                        if min_attacker_value < self.PIECE_VALUES[pt]:
                            score -= sign * ((self.PIECE_VALUES[pt] - min_attacker_value) // 8)

        return score

    def evaluate(self, board: chess.Board) -> int:
        """Full position evaluation."""
        if board.is_checkmate():
            return -self.MATE_SCORE

        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        if board.is_fifty_moves() or board.is_repetition(2):
            return 0

        phase = self.get_game_phase(board)
        score = 0

        # Material and piece-square tables
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.PIECE_VALUES[piece.piece_type]
                value += self.get_pst_value(piece, square, phase)
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value

        # Positional evaluation
        score += self.evaluate_development(board, phase)
        score += self.evaluate_center_control(board)
        score += self.evaluate_mobility(board)
        score += self.evaluate_pawns(board, phase)
        score += self.evaluate_king_safety(board, phase)
        score += self.evaluate_pieces(board, phase)
        score += self.evaluate_threats(board)

        # Tempo bonus for side to move
        score += 10 if board.turn == chess.WHITE else -10

        # Return from side to move's perspective
        if board.turn == chess.BLACK:
            score = -score

        return score

    def score_move(self, board: chess.Board, move: chess.Move, ply: int, tt_move: chess.Move = None) -> int:
        """Score move for ordering."""
        score = 0

        if tt_move and move == tt_move:
            return 10000000

        if board.is_capture(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim:
                score += 1000000 + self.PIECE_VALUES[victim.piece_type] * 10 - self.PIECE_VALUES[attacker.piece_type]
            else:
                score += 1000000 + 100

        if move.promotion:
            score += 900000 + self.PIECE_VALUES[move.promotion]

        if ply < 64:
            if move == self.killers[ply][0]:
                score += 800000
            elif move == self.killers[ply][1]:
                score += 700000

        score += self.history[(move.from_square, move.to_square)]

        return score

    def order_moves(self, board: chess.Board, moves: list, ply: int, tt_move: chess.Move = None) -> list:
        scored = [(self.score_move(board, m, ply, tt_move), m) for m in moves]
        scored.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored]

    def store_killer(self, move: chess.Move, ply: int):
        if ply >= 64:
            return
        if move != self.killers[ply][0]:
            self.killers[ply][1] = self.killers[ply][0]
            self.killers[ply][0] = move

    def quiescence(self, board: chess.Board, alpha: int, beta: int, ply: int) -> int:
        self.nodes_searched += 1

        if self.time_limit and time.time() - self.start_time > self.time_limit:
            self.time_exceeded = True
            return 0

        stand_pat = self.evaluate(board)

        if stand_pat >= beta:
            return beta

        if stand_pat + 1000 < alpha:
            return alpha

        if stand_pat > alpha:
            alpha = stand_pat

        captures = [m for m in board.legal_moves if board.is_capture(m) or m.promotion]
        captures = self.order_moves(board, captures, ply)

        for move in captures:
            if not move.promotion:
                victim = board.piece_at(move.to_square)
                if victim and stand_pat + self.PIECE_VALUES[victim.piece_type] + 200 < alpha:
                    continue

            board.push(move)
            score = -self.quiescence(board, -beta, -alpha, ply + 1)
            board.pop()

            if self.time_exceeded:
                return 0

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int, do_null: bool = True) -> int:
        self.nodes_searched += 1

        if self.time_limit and self.nodes_searched % 4096 == 0:
            if time.time() - self.start_time > self.time_limit:
                self.time_exceeded = True
                return 0

        if self.time_exceeded:
            return 0

        if board.is_repetition(2) or board.is_fifty_moves():
            return 0

        key = board._transposition_key()
        tt_entry = self.tt.get(key)
        tt_move = None

        if tt_entry and tt_entry.depth >= depth:
            tt_move = tt_entry.best_move
            if tt_entry.flag == TT_EXACT:
                return tt_entry.score
            elif tt_entry.flag == TT_ALPHA and tt_entry.score <= alpha:
                return alpha
            elif tt_entry.flag == TT_BETA and tt_entry.score >= beta:
                return beta
        elif tt_entry:
            tt_move = tt_entry.best_move

        if depth <= 0:
            return self.quiescence(board, alpha, beta, ply)

        in_check = board.is_check()

        # Null move pruning
        if do_null and depth >= 3 and not in_check and self.get_game_phase(board) < 0.8:
            has_pieces = any(board.pieces(pt, board.turn) for pt in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN])
            if has_pieces:
                board.push(chess.Move.null())
                R = 3 if depth >= 6 else 2
                score = -self.negamax(board, depth - 1 - R, -beta, -beta + 1, ply + 1, False)
                board.pop()
                if self.time_exceeded:
                    return 0
                if score >= beta:
                    return beta

        moves = list(board.legal_moves)
        if not moves:
            return -self.MATE_SCORE + ply if in_check else 0

        moves = self.order_moves(board, moves, ply, tt_move)

        best_move = moves[0]
        best_score = -self.INFINITY
        flag = TT_ALPHA

        for i, move in enumerate(moves):
            board.push(move)

            # LMR
            if i >= 4 and depth >= 3 and not in_check and not board.is_check() and not board.is_capture(move) and not move.promotion:
                score = -self.negamax(board, depth - 2, -alpha - 1, -alpha, ply + 1)
                if score > alpha:
                    score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
            else:
                if i == 0:
                    score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
                else:
                    score = -self.negamax(board, depth - 1, -alpha - 1, -alpha, ply + 1)
                    if score > alpha and score < beta:
                        score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)

            board.pop()

            if self.time_exceeded:
                return 0

            if score > best_score:
                best_score = score
                best_move = move

            if score > alpha:
                alpha = score
                flag = TT_EXACT
                if not board.is_capture(move):
                    self.history[(move.from_square, move.to_square)] += depth * depth

            if alpha >= beta:
                if not board.is_capture(move):
                    self.store_killer(move, ply)
                flag = TT_BETA
                break

        if len(self.tt) < self.TT_SIZE:
            self.tt[key] = TTEntry(key, depth, best_score, flag, best_move)
        elif key in self.tt and depth >= self.tt[key].depth:
            self.tt[key] = TTEntry(key, depth, best_score, flag, best_move)

        return best_score

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        if depth is None:
            depth = self.max_depth

        self.nodes_searched = 0
        self.start_time = time.time()
        self.time_exceeded = False

        moves = list(board.legal_moves)
        if not moves:
            return None

        best_move = moves[0]
        best_score = -self.INFINITY
        final_depth = 1

        for current_depth in range(1, depth + 1):
            if self.time_exceeded:
                break

            current_best_move = None
            current_best_score = -self.INFINITY
            alpha = -self.INFINITY
            beta = self.INFINITY

            tt_entry = self.tt.get(board._transposition_key())
            tt_move = tt_entry.best_move if tt_entry else None
            moves = self.order_moves(board, list(board.legal_moves), 0, tt_move)

            for i, move in enumerate(moves):
                board.push(move)

                if i == 0:
                    score = -self.negamax(board, current_depth - 1, -beta, -alpha, 1)
                else:
                    score = -self.negamax(board, current_depth - 1, -alpha - 1, -alpha, 1)
                    if score > alpha and score < beta:
                        score = -self.negamax(board, current_depth - 1, -beta, -alpha, 1)

                board.pop()

                if self.time_exceeded:
                    break

                if score > current_best_score:
                    current_best_score = score
                    current_best_move = move

                if score > alpha:
                    alpha = score

            if not self.time_exceeded and current_best_move:
                best_move = current_best_move
                best_score = current_best_score
                final_depth = current_depth

        return SearchResult(
            best_move=best_move,
            score=best_score,
            depth=final_depth,
            nodes_searched=self.nodes_searched,
            time_spent=time.time() - self.start_time
        )

    def get_best_move(self, board: chess.Board) -> chess.Move:
        result = self.search(board)
        return result.best_move if result else None


if __name__ == "__main__":
    board = chess.Board()
    engine = ChessEngine(max_depth=6, time_limit=5)

    print("Testing engine v3.0...")
    result = engine.search(board)
    print(f"Best move: {result.best_move}")
    print(f"Score: {result.score} cp")
    print(f"Depth: {result.depth}")
    print(f"Nodes: {result.nodes_searched}")
    print(f"Time: {result.time_spent:.2f}s")
    print(f"NPS: {result.nodes_searched / result.time_spent:.0f}")
