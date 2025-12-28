import chess
import chess.polyglot
import time
from dataclasses import dataclass
from typing import Optional, Dict, List
import random


# -----------------------------------------------------------------------------
# Data Structures
# -----------------------------------------------------------------------------

@dataclass
class SearchResult:
    """Container for search results"""
    best_move: chess.Move
    score: float
    depth: int
    nodes_searched: int
    time_spent: float


class TranspositionTable:
    """Compact transposition table with replacement strategy"""

    def __init__(self, size_mb: int = 256):
        self.size = (size_mb * 1024 * 1024) // 32
        self.mask = self.size - 1
        self.table: List[Optional['TTEntry']] = [None] * self.size

    def _index(self, key: int) -> int:
        return (key >> 1) & self.mask

    def store(self, key: int, depth: int, score: float, flag: int, move: chess.Move, age: int):
        idx = self._index(key)
        # Replace if deeper or newer
        existing = self.table[idx]
        if not existing or depth > existing.depth or age > existing.age:
            self.table[idx] = TTEntry(key, depth, score, flag, move, age)

    def probe(self, key: int) -> Optional['TTEntry']:
        idx = self._index(key)
        entry = self.table[idx]
        if entry and entry.key == key:
            return entry
        return None


class TTEntry:
    __slots__ = ['key', 'depth', 'score', 'flag', 'move', 'age']

    def __init__(self, key: int, depth: int, score: float, flag: int, move: chess.Move, age: int):
        self.key = key
        self.depth = depth
        self.score = score
        self.flag = flag
        self.move = move
        self.age = age


# -----------------------------------------------------------------------------
# Main Engine
# -----------------------------------------------------------------------------

class ChessEngine:
    # Exact interface as requested
    PIECE_VALUES = {
        chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
        chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000
    }

    # Piece-square tables (tapered, from strong open-source engines)
    PAWN_TABLE = [
        0, 0, 0, 0, 0, 0, 0, 0,
        98, 134, 61, 95, 68, 126, 234, -49,
        -6, 7, -2, -15, 31, -2, 7, -5,
        -14, 13, -6, -21, -1, -16, 10, -21,
        -14, 9, -6, -14, -2, -5, -1, -20,
        -12, -7, 6, -1, 3, -9, -4, -19,
        11, 14, 20, 21, 26, 25, 17, 23,
        0, 0, 0, 0, 0, 0, 0, 0
    ]

    KNIGHT_TABLE = [
        -167, -89, -34, -49, 61, -97, -15, -107,
        -73, -41, 72, 36, 23, 62, 7, -17,
        -47, 60, 37, 65, 84, 129, 73, 44,
        -9, 17, 19, 53, 37, 69, 18, 22,
        -13, 4, 16, 13, 28, 19, 21, -8,
        -23, -9, 12, 10, 19, 17, 25, -16,
        -29, -53, -12, -3, -1, 18, -14, -19,
        -105, -21, -58, -33, -17, -28, -19, -23
    ]

    BISHOP_TABLE = [
        -29, 4, -82, -37, -25, -42, 7, -8,
        -26, 16, -18, -13, 30, 59, 18, -47,
        -16, 37, 43, 40, 35, 25, 22, -2,
        -4, 5, 19, 50, 37, 37, 7, -2,
        -6, 13, 13, 26, 34, 12, 10, 4,
        0, 15, 15, 15, 14, 27, 18, 10,
        4, 15, 16, 0, 0, -7, 21, -8,
        -33, -3, -14, -21, -13, -12, -39, -21
    ]

    ROOK_TABLE = [
        32, 42, 32, 51, 63, 9, 31, 43,
        27, 32, 58, 62, 80, 67, 26, 44,
        -5, 19, 26, 36, 17, 45, 61, 16,
        -24, -11, 7, 26, 24, 35, -8, -20,
        -36, -26, -12, -1, 9, -7, 6, -23,
        -45, -25, -16, -17, 3, 0, -5, -33,
        -44, -16, -20, -9, -1, 11, -6, -71,
        -19, -13, 1, 17, 16, 7, -37, -26
    ]

    QUEEN_TABLE = [
        -28, 0, 29, 12, 59, 44, 43, 45,
        -24, -39, -5, 1, -16, 57, 28, 54,
        -13, -17, 7, 8, 29, 56, 47, 57,
        -27, -27, -16, -16, -1, 17, -2, 1,
        -9, -26, -9, -10, -2, -4, 3, -3,
        -14, 2, -11, -2, 5, 14, 12, 5,
        -35, -8, 11, 2, 8, 15, -3, 1,
        -1, -18, -9, 10, -15, -25, -31, -50
    ]

    KING_TABLE_MIDGAME = [
        -65, 23, 16, -15, -56, -34, 2, 13,
        29, -1, -20, -7, -8, -4, -38, -29,
        -9, 24, 2, -16, -20, 6, 22, -22,
        -17, -20, -12, -27, -30, -25, -14, -36,
        -49, -1, -27, -39, -46, -44, -33, -51,
        -14, -14, -22, -46, -44, -30, -15, -27,
        1, 7, -8, -64, -43, -16, 9, 8,
        -15, 36, 12, -54, 8, -28, 24, 14
    ]

    KING_TABLE_ENDGAME = [
        -74, -35, -18, -18, -11, 15, 4, -17,
        -12, 17, 14, 17, 17, 38, 23, 11,
        6, 19, 23, 15, 20, 45, 31, 13,
        -10, 25, 27, 26, 33, 42, 28, 16,
        -12, 15, 23, 24, 30, 27, 32, 20,
        -19, 6, 2, 9, 20, 19, 13, 3,
        -26, -7, -7, -2, -2, 5, 9, -12,
        -44, -25, -17, -12, -22, -24, -16, -50
    ]

    # TT flags
    EXACT = 0
    LOWERBOUND = 1
    UPPERBOUND = 2

    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.tt = TranspositionTable(256)
        self.nodes_searched = 0
        self.start_time = 0.0
        self.age = 0
        self.killers = [[None, None] for _ in range(max_depth + 10)]
        self.history = [[0] * 64 for _ in range(64)]
        self.pv_table = {}
        self.best_move = None

    def get_best_move(self, board: chess.Board) -> chess.Move:
        """Return best move for current position"""
        result = self.search(board)
        return result.best_move

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        """Main search with iterative deepening and time management"""
        self.nodes_searched = 0
        self.start_time = time.time()
        self.age += 1
        self.best_move = None

        if depth is None:
            depth = self.max_depth

        best_result = None
        alpha, beta = -float('inf'), float('inf')

        # Iterative deepening
        for current_depth in range(1, depth + 1):
            self.killers = [[None, None] for _ in range(depth + 10)]

            try:
                # Aspiration windows for deeper searches
                if current_depth > 5 and best_result:
                    alpha = best_result.score - 30
                    beta = best_result.score + 30

                score = self._pvs(board, current_depth, alpha, beta, True)

                # Failed aspiration - research with full window
                if score <= alpha or score >= beta:
                    alpha, beta = -float('inf'), float('inf')
                    score = self._pvs(board, current_depth, alpha, beta, True)

                # Extract best move
                pv_key = chess.polyglot.zobrist_hash(board)
                self.best_move = self.pv_table.get(pv_key) or self.best_move or self._random_move(board)

                time_spent = time.time() - self.start_time
                best_result = SearchResult(
                    best_move=self.best_move,
                    score=score,
                    depth=current_depth,
                    nodes_searched=self.nodes_searched,
                    time_spent=time_spent
                )

                # Time limit check
                if self.time_limit and time_spent >= self.time_limit * 0.95:
                    break

            except TimeLimitException:
                break

        if best_result is None:
            time_spent = time.time() - self.start_time
            best_result = SearchResult(
                best_move=self.best_move or self._random_move(board),
                score=0, depth=0, nodes_searched=self.nodes_searched, time_spent=time_spent
            )

        return best_result

    def _random_move(self, board: chess.Board) -> chess.Move:
        """Fallback for emergencies"""
        return random.choice(list(board.legal_moves))

    def _pvs(self, board: chess.Board, depth: int, alpha: float, beta: float, is_root: bool) -> float:
        """Principal Variation Search with extensions/reductions"""
        self.nodes_searched += 1

        # Hard time limit
        if self.time_limit and (time.time() - self.start_time) > self.time_limit:
            raise TimeLimitException()

        # Quiescence at leaf nodes
        if depth <= 0:
            return self._qsearch(board, alpha, beta, 0)

        # Probe transposition table
        key = chess.polyglot.zobrist_hash(board)
        tt_entry = self.tt.probe(key)
        pv_move = None
        if tt_entry and tt_entry.depth >= depth:
            if tt_entry.flag == self.EXACT:
                return tt_entry.score
            elif tt_entry.flag == self.LOWERBOUND:
                alpha = max(alpha, tt_entry.score)
            else:  # UPPERBOUND
                beta = min(beta, tt_entry.score)
            if alpha >= beta:
                return tt_entry.score
        if tt_entry:
            pv_move = tt_entry.move

        # Draw detection
        if board.is_repetition(2) or board.is_insufficient_material() or board.is_fifty_moves():
            return 0

        # Null move pruning
        if not is_root and not board.is_check() and depth >= 3 and self._has_material(board, board.turn):
            R = 3 if depth >= 6 else 2
            board.push(chess.Move.null())
            null_score = -self._pvs(board, depth - R - 1, -beta, -beta + 1, False)
            board.pop()
            if null_score >= beta:
                return beta

        # Generate and order moves
        moves = self._order_moves(board, pv_move, self.killers[depth])
        if not moves:
            return -float('inf') if board.is_check() else 0

        best_score = -float('inf')
        best_move = None
        original_alpha = alpha

        # Extensions
        extension = 1 if board.is_check() else 0

        # Search loop
        for i, move in enumerate(moves):
            board.push(move)

            # Late move reduction
            reduction = 0
            if depth >= 3 and i >= 4 and not extension and not move.promotion and not board.is_capture(move):
                reduction = 1

            if i == 0:
                score = -self._pvs(board, depth - 1 + extension, -beta, -alpha, False)
            else:
                score = -self._pvs(board, depth - 1 + extension - reduction, -alpha - 1, -alpha, False)
                if reduction and score > alpha:
                    score = -self._pvs(board, depth - 1 + extension, -alpha - 1, -alpha, False)
                if score > alpha and score < beta:
                    score = -self._pvs(board, depth - 1 + extension, -beta, -score, False)

            board.pop()

            if score > best_score:
                best_score, best_move = score, move
                if is_root:
                    self.best_move = move
                    self.pv_table[key] = move

            alpha = max(alpha, score)
            if alpha >= beta:
                # Update history/killers
                if not board.is_capture(move):
                    self.killers[depth][1] = self.killers[depth][0]
                    self.killers[depth][0] = move
                    self.history[move.from_square][move.to_square] += depth * depth
                break

        # Store in TT
        if best_score <= original_alpha:
            flag = self.UPPERBOUND
        elif best_score >= beta:
            flag = self.LOWERBOUND
        else:
            flag = self.EXACT
        self.tt.store(key, depth, best_score, flag, best_move, self.age)

        return best_score

    def _qsearch(self, board: chess.Board, alpha: float, beta: float, depth: int) -> float:
        """Quiescence search - only captures and checks"""
        self.nodes_searched += 1

        if self.time_limit and (time.time() - self.start_time) > self.time_limit:
            raise TimeLimitException()

        # Stand pat
        stand_pat = self._evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        # Delta pruning
        if depth > 4:
            return alpha

        # Generate captures only (best ordered)
        moves = []
        for i, move in enumerate(board.legal_moves):
            if board.is_capture(move):
                victim = board.piece_type_at(move.to_square) or chess.PAWN
                attacker = board.piece_type_at(move.from_square) or chess.PAWN
                value = self.PIECE_VALUES[victim] - self.PIECE_VALUES[attacker]
                moves.append((-value, i, move))
        moves.sort()

        for _, _, move in moves:
            board.push(move)
            score = -self._qsearch(board, -beta, -alpha, depth + 1)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def _order_moves(self, board: chess.Board, pv_move: chess.Move, killers: List[chess.Move]) -> List[chess.Move]:
        """High-quality move ordering"""
        scored = []

        for i, move in enumerate(board.legal_moves):
            score = 0

            # PV move first
            if move == pv_move:
                score += 10000000

            # Captures (MVV-LVA)
            if board.is_capture(move):
                victim = board.piece_type_at(move.to_square) or chess.PAWN
                attacker = board.piece_type_at(move.from_square) or chess.PAWN
                score += 100000 + self.PIECE_VALUES[victim] - self.PIECE_VALUES[attacker]

            # Promotions
            if move.promotion:
                score += 90000 + self.PIECE_VALUES[move.promotion]

            # Killers
            if move == killers[0]:
                score += 5000
            elif move == killers[1]:
                score += 4000
            else:
                score += min(self.history[move.from_square][move.to_square], 2000)

            # Checks
            if board.gives_check(move):
                score += 1000

            scored.append((-score, i, move))

        scored.sort()
        return [m for _, _, m in scored]

    def _evaluate(self, board: chess.Board) -> float:
        """Advanced evaluation with tapered piece-square tables"""
        # Terminal states
        if board.is_checkmate():
            return -float('inf') if board.turn else float('inf')
        if board.is_stalemate() or board.is_insufficient_material() or board.is_repetition(3):
            return 0

        score = 0

        # Phase calculation for tapered eval
        phase = self._game_phase(board)

        # Evaluate each piece
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if not piece:
                continue

            value = self.PIECE_VALUES[piece.piece_type]
            psq = self._psq_score(piece.piece_type, square, piece.color, phase)
            total = value + psq

            if piece.color == chess.WHITE:
                score += total
            else:
                score -= total

        # Side to move bonus
        score += 10 if board.turn == chess.WHITE else -10

        return score / 100.0  # Return in pawn units

    def _psq_score(self, piece_type: int, square: int, color: bool, phase: float) -> int:
        """Piece-square score with phase-based interpolation"""
        sq = square if color == chess.WHITE else chess.square_mirror(square)

        if piece_type == chess.PAWN:
            return self.PAWN_TABLE[sq]
        elif piece_type == chess.KNIGHT:
            return self.KNIGHT_TABLE[sq]
        elif piece_type == chess.BISHOP:
            return self.BISHOP_TABLE[sq]
        elif piece_type == chess.ROOK:
            return self.ROOK_TABLE[sq]
        elif piece_type == chess.QUEEN:
            return self.QUEEN_TABLE[sq]
        else:  # King
            mg = self.KING_TABLE_MIDGAME[sq]
            eg = self.KING_TABLE_ENDGAME[sq]
            return int(mg * phase + eg * (1 - phase))

    def _game_phase(self, board: chess.Board) -> float:
        """Calculate game phase 0(endgame)-1(middlegame)"""
        material = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.piece_type != chess.KING:
                material += self.PIECE_VALUES[piece.piece_type]
        max_material = 2 * (900 + 500 + 330 + 320 + 100)
        return min(1.0, material / max_material)

    def _has_material(self, board: chess.Board, color: bool) -> bool:
        """Material requirement for null move pruning"""
        pieces = board.pieces(chess.ROOK, color) | board.pieces(chess.QUEEN, color) | board.pieces(chess.PAWN, color)
        return len(pieces) > 0


class TimeLimitException(Exception):
    pass