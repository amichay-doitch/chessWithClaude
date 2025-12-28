import chess
import time
from dataclasses import dataclass
from typing import Optional


@dataclass
class SearchResult:
    best_move: Optional[chess.Move]
    score: int
    depth: int
    nodes_searched: int
    time_spent: float


class ChessEngine:
    PIECE_VALUES = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                    chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 20000}

    PST_PAWN = [0, 0, 0, 0, 0, 0, 0, 0, 50, 50, 50, 50, 50, 50, 50, 50, 10, 10, 20, 30, 30, 20, 10, 10,
                5, 5, 10, 25, 25, 10, 5, 5, 0, 0, 0, 20, 20, 0, 0, 0, 5, -5, -10, 0, 0, -10, -5, 5,
                5, 10, 10, -20, -20, 10, 10, 5, 0, 0, 0, 0, 0, 0, 0, 0]
    PST_KNIGHT = [-50, -40, -30, -30, -30, -30, -40, -50, -40, -20, 0, 0, 0, 0, -20, -40,
                  -30, 0, 10, 15, 15, 10, 0, -30, -30, 5, 15, 20, 20, 15, 5, -30, -30, 0, 15, 20, 20, 15, 0, -30,
                  -30, 5, 10, 15, 15, 10, 5, -30, -40, -20, 0, 5, 5, 0, -20, -40, -50, -40, -30, -30, -30, -30, -40,
                  -50]
    PST_BISHOP = [-20, -10, -10, -10, -10, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 10, 10, 5, 0, -10,
                  -10, 5, 5, 10, 10, 5, 5, -10, -10, 0, 10, 10, 10, 10, 0, -10, -10, 10, 10, 10, 10, 10, 10, -10,
                  -10, 5, 0, 0, 0, 0, 5, -10, -20, -10, -10, -10, -10, -10, -10, -20]
    PST_ROOK = [0, 0, 0, 0, 0, 0, 0, 0, 5, 10, 10, 10, 10, 10, 10, 5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0,
                -5,
                -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, -5, 0, 0, 0, 0, 0, 0, -5, 0, 0, 0, 5, 5, 0, 0, 0]
    PST_QUEEN = [-20, -10, -10, -5, -5, -10, -10, -20, -10, 0, 0, 0, 0, 0, 0, -10, -10, 0, 5, 5, 5, 5, 0, -10,
                 -5, 0, 5, 5, 5, 5, 0, -5, 0, 0, 5, 5, 5, 5, 0, -5, -10, 5, 5, 5, 5, 5, 0, -10, -10, 0, 5, 0, 0, 0, 0,
                 -10, -20, -10, -10, -5, -5, -10, -10, -20]
    PST_KING_MG = [-30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30,
                   -30, -40, -40, -50, -50, -40, -40, -30, -30, -40, -40, -50, -50, -40, -40, -30,
                   -20, -30, -30, -40, -40, -30, -30, -20, -10, -20, -20, -20, -20, -20, -20, -10,
                   20, 20, 0, 0, 0, 0, 20, 20, 20, 30, 10, 0, 0, 10, 30, 20]

    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes = 0
        self.start_time = 0
        self.tt = {}

    def get_best_move(self, board: chess.Board) -> chess.Move:
        return self.search(board).best_move

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        self.nodes = 0
        self.start_time = time.time()
        self.tt.clear()
        depth = depth or self.max_depth
        best_move, score = None, -999999

        for d in range(1, depth + 1):
            if self.time_limit and time.time() - self.start_time > self.time_limit * 0.8:
                break
            move, s = self._search_root(board, d)
            if move:
                best_move, score = move, s

        return SearchResult(best_move, score, d, self.nodes, time.time() - self.start_time)

    def _search_root(self, board, depth):
        best_move, alpha, beta = None, -999999, 999999
        for move in self._order_moves(board, board.legal_moves):
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha)
            board.pop()
            if score > alpha:
                alpha, best_move = score, move
        return best_move, alpha

    def _negamax(self, board, depth, alpha, beta):
        self.nodes += 1
        if self.time_limit and self.nodes % 4096 == 0:
            if time.time() - self.start_time > self.time_limit:
                return alpha

        if board.is_checkmate():
            return -99999 - depth
        if board.is_stalemate() or board.is_insufficient_material():
            return 0
        if depth <= 0:
            return self._quiesce(board, alpha, beta)

        for move in self._order_moves(board, board.legal_moves):
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha)
            board.pop()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha

    def _quiesce(self, board, alpha, beta):
        self.nodes += 1
        stand_pat = self._evaluate(board)
        if stand_pat >= beta:
            return beta
        alpha = max(alpha, stand_pat)

        for move in self._order_moves(board, board.legal_moves):
            if not board.is_capture(move):
                continue
            board.push(move)
            score = -self._quiesce(board, -beta, -alpha)
            board.pop()
            if score >= beta:
                return beta
            alpha = max(alpha, score)
        return alpha

    def _order_moves(self, board, moves):
        scored = []
        for m in moves:
            score = 0
            if board.is_capture(m):
                victim = board.piece_type_at(m.to_square)
                attacker = board.piece_type_at(m.from_square)
                if victim:
                    score = 10 * self.PIECE_VALUES.get(victim, 0) - self.PIECE_VALUES.get(attacker, 0)
            if m.promotion:
                score += self.PIECE_VALUES[m.promotion]
            scored.append((score, m))
        return [m for _, m in sorted(scored, reverse=True)]

    def _evaluate(self, board):
        if board.is_checkmate():
            return -99999 if board.turn else 99999

        score = 0
        for sq in chess.SQUARES:
            piece = board.piece_at(sq)
            if not piece:
                continue
            val = self.PIECE_VALUES[piece.piece_type]
            pst = self._get_pst(piece.piece_type)
            idx = sq if piece.color else chess.square_mirror(sq)
            val += pst[idx] if pst else 0
            score += val if piece.color else -val

        score += 10 * (bin(board.attacks_mask(chess.E4) | board.attacks_mask(chess.D4) |
                           board.attacks_mask(chess.E5) | board.attacks_mask(chess.D5)).count('1'))
        return score if board.turn else -score

    def _get_pst(self, pt):
        return {chess.PAWN: self.PST_PAWN, chess.KNIGHT: self.PST_KNIGHT,
                chess.BISHOP: self.PST_BISHOP, chess.ROOK: self.PST_ROOK,
                chess.QUEEN: self.PST_QUEEN, chess.KING: self.PST_KING_MG}.get(pt)
