import chess
import time
import math
from dataclasses import dataclass
from typing import Optional, Dict, Tuple

INF = 10**9
MATE = 100_000

@dataclass
class SearchResult:
    best_move: Optional[chess.Move]
    score: int
    depth: int
    nodes_searched: int
    time_spent: float


class TTEntry:
    __slots__ = ("depth", "score", "flag", "move")
    def __init__(self, depth, score, flag, move):
        self.depth = depth
        self.score = score
        self.flag = flag
        self.move = move


class ChessEngine:
    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit

        self.nodes = 0
        self.start_time = 0.0
        self.stop = False

        self.tt: Dict[int, TTEntry] = {}
        self.killer = [[None, None] for _ in range(128)]
        self.history: Dict[chess.Move, int] = {}

    # =====================
    # Public API
    # =====================

    def get_best_move(self, board: chess.Board) -> chess.Move:
        return self.search(board).best_move

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        self.nodes = 0
        self.stop = False
        self.start_time = time.time()

        max_depth = depth or self.max_depth
        best_move = None
        best_score = -INF

        alpha, beta = -INF, INF

        for d in range(1, max_depth + 1):
            score, move = self._negamax(board, d, alpha, beta, True)
            if self.stop:
                break

            best_score = score
            best_move = move

            # Aspiration window
            alpha = score - 50
            beta = score + 50

        return SearchResult(
            best_move=best_move,
            score=best_score,
            depth=d,
            nodes_searched=self.nodes,
            time_spent=time.time() - self.start_time
        )

    # =====================
    # Negamax
    # =====================

    def _negamax(self, board, depth, alpha, beta, root=False):
        if self._time_up():
            self.stop = True
            return 0, None

        self.nodes += 1
        alpha_orig = alpha

        if board.is_checkmate():
            return -MATE + board.fullmove_number, None
        if board.is_stalemate() or board.is_insufficient_material():
            return 0, None

        key = hash(board)
        entry = self.tt.get(key)
        if entry and entry.depth >= depth:
            if entry.flag == "EXACT":
                return entry.score, entry.move
            if entry.flag == "LOWER":
                alpha = max(alpha, entry.score)
            elif entry.flag == "UPPER":
                beta = min(beta, entry.score)
            if alpha >= beta:
                return entry.score, entry.move

        if depth == 0:
            return self._quiescence(board, alpha, beta), None

        # Null move pruning
        if depth >= 3 and not board.is_check():
            board.push(chess.Move.null())
            score, _ = self._negamax(board, depth - 1 - 2, -beta, -beta + 1)
            board.pop()
            score = -score
            if score >= beta:
                return beta, None

        best_score = -INF
        best_move = None

        moves = list(board.legal_moves)
        self._order_moves(board, moves, entry.move if entry else None, depth)

        for i, move in enumerate(moves):
            board.push(move)

            reduction = 1 if i > 3 and depth >= 3 and not board.is_check() and not board.is_capture(move) else 0
            score, _ = self._negamax(board, depth - 1 - reduction, -beta, -alpha)
            score = -score

            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)
            if alpha >= beta:
                if not board.is_capture(move):
                    self._store_killer(move, depth)
                break

        flag = "EXACT"
        if best_score <= alpha_orig:
            flag = "UPPER"
        elif best_score >= beta:
            flag = "LOWER"

        self.tt[key] = TTEntry(depth, best_score, flag, best_move)
        return best_score, best_move

    # =====================
    # Quiescence
    # =====================

    def _quiescence(self, board, alpha, beta):
        stand = self._evaluate(board)
        if stand >= beta:
            return beta
        alpha = max(alpha, stand)

        for move in board.legal_moves:
            if not board.is_capture(move):
                continue
            board.push(move)
            score = -self._quiescence(board, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            alpha = max(alpha, score)

        return alpha

    # =====================
    # Evaluation
    # =====================

    PIECE = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 0
    }

    PST = {
        chess.PAWN: [0,5,10,20,20,10,5,0]*8,
        chess.KNIGHT: [-50,-40,-30,-30,-30,-30,-40,-50]*8,
        chess.BISHOP: [-20,-10,-10,-10,-10,-10,-10,-20]*8,
        chess.ROOK: [0,0,5,10,10,5,0,0]*8,
        chess.QUEEN: [-20,-10,-10,-5,-5,-10,-10,-20]*8,
        chess.KING: [-30,-40,-40,-50,-50,-40,-40,-30]*8,
    }

    def _evaluate(self, board):
        score = 0
        bishops = [0, 0]

        for piece in chess.PIECE_TYPES:
            for sq in board.pieces(piece, chess.WHITE):
                score += self.PIECE[piece] + self.PST[piece][sq]
                if piece == chess.BISHOP:
                    bishops[0] += 1
            for sq in board.pieces(piece, chess.BLACK):
                score -= self.PIECE[piece] + self.PST[piece][chess.square_mirror(sq)]
                if piece == chess.BISHOP:
                    bishops[1] += 1

        if bishops[0] >= 2:
            score += 30
        if bishops[1] >= 2:
            score -= 30

        score += len(list(board.legal_moves)) * (5 if board.turn else -5)
        return score if board.turn else -score

    # =====================
    # Move Ordering
    # =====================

    def _order_moves(self, board, moves, tt_move, depth):
        def score(m):
            if m == tt_move:
                return 10_000_000
            if board.is_capture(m):
                v = board.piece_at(m.to_square)
                a = board.piece_at(m.from_square)
                return 1_000_000 + self.PIECE[v.piece_type] - self.PIECE[a.piece_type]
            if m == self.killer[depth][0]:
                return 900_000
            if m == self.killer[depth][1]:
                return 800_000
            return self.history.get(m, 0)

        moves.sort(key=score, reverse=True)

    def _store_killer(self, move, depth):
        if self.killer[depth][0] != move:
            self.killer[depth][1] = self.killer[depth][0]
            self.killer[depth][0] = move
        self.history[move] = self.history.get(move, 0) + depth * depth

    # =====================
    # Time
    # =====================

    def _time_up(self):
        return self.time_limit is not None and (time.time() - self.start_time) >= self.time_limit
