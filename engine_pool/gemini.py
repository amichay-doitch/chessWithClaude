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
    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_count = 0
        self.start_time = 0

        # Piece values for material evaluation
        self.values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        # Piece-Square Tables (PST) to encourage better positioning
        # Higher values mean the piece is better placed on that square
        self.pst = {
            chess.PAWN: [
                0, 0, 0, 0, 0, 0, 0, 0,
                50, 50, 50, 50, 50, 50, 50, 50,
                10, 10, 20, 30, 30, 20, 10, 10,
                5, 5, 10, 25, 25, 10, 5, 5,
                0, 0, 0, 20, 20, 0, 0, 0,
                5, -5, -10, 0, 0, -10, -5, 5,
                5, 10, 10, -20, -20, 10, 10, 5,
                0, 0, 0, 0, 0, 0, 0, 0
            ],
            chess.KNIGHT: [
                -50, -40, -30, -30, -30, -30, -40, -50,
                -40, -20, 0, 0, 0, 0, -20, -40,
                -30, 0, 10, 15, 15, 10, 0, -30,
                -30, 5, 15, 20, 20, 15, 5, -30,
                -30, 0, 15, 20, 20, 15, 0, -30,
                -30, 5, 10, 15, 15, 10, 5, -30,
                -40, -20, 0, 5, 5, 0, -20, -40,
                -50, -40, -30, -30, -30, -30, -40, -50
            ],
            # (Simplified for brevity, but usually includes all pieces)
        }

    def _evaluate(self, board: chess.Board) -> int:
        if board.is_checkmate():
            return -99999 if board.turn == chess.WHITE else 99999

        score = 0
        for piece_type in self.values:
            # Material score
            score += len(board.pieces(piece_type, chess.WHITE)) * self.values[piece_type]
            score -= len(board.pieces(piece_type, chess.BLACK)) * self.values[piece_type]

            # Positional score (PST)
            if piece_type in self.pst:
                for sq in board.pieces(piece_type, chess.WHITE):
                    score += self.pst[piece_type][chess.square_mirror(sq)]
                for sq in board.pieces(piece_type, chess.BLACK):
                    score -= self.pst[piece_type][sq]

        return score if board.turn == chess.WHITE else -score

    def _order_moves(self, board: chess.Board, moves):
        """MVV-LVA (Most Valuable Victim - Least Valuable Aggressor) heuristic"""

        def score_move(move):
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                aggressor = board.piece_at(move.from_square)
                if victim and aggressor:
                    return 10 * self.values[victim.piece_type] - self.values[aggressor.piece_type]
            return 0

        return sorted(moves, key=score_move, reverse=True)

    def _quiescence(self, board: chess.Board, alpha: int, beta: int) -> int:
        """Prevents 'horizon effect' by searching until captures stabilize."""
        stand_pat = self._evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        for move in self._order_moves(board, board.generate_legal_captures()):
            board.push(move)
            score = -self._quiescence(board, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
        return alpha

    def _negamax(self, board: chess.Board, depth: int, alpha: int, beta: int) -> int:
        self.nodes_count += 1

        # Check time limit
        if self.time_limit and (time.time() - self.start_time) > self.time_limit:
            raise TimeoutError()

        if depth == 0:
            return self._quiescence(board, alpha, beta)

        moves = self._order_moves(board, board.legal_moves)
        if not moves:
            return self._evaluate(board)

        best_score = -float('inf')
        for move in moves:
            board.push(move)
            score = -self._negamax(board, depth - 1, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score
            best_score = max(best_score, score)

        return alpha

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        self.start_time = time.time()
        self.nodes_count = 0
        target_depth = depth or self.max_depth
        best_move = None
        current_best_score = -float('inf')

        # Iterative Deepening
        try:
            for d in range(1, target_depth + 1):
                alpha = -float('inf')
                beta = float('inf')
                moves = self._order_moves(board, board.legal_moves)

                temp_best_move = None
                for move in moves:
                    board.push(move)
                    score = -self._negamax(board, d - 1, -beta, -alpha)
                    board.pop()

                    if score > alpha:
                        alpha = score
                        temp_best_move = move

                best_move = temp_best_move
                current_best_score = alpha
        except TimeoutError:
            pass  # Return the result from the last completed depth

        return SearchResult(
            best_move=best_move or list(board.legal_moves)[0],
            score=current_best_score,
            depth=d if 'd' in locals() else 0,
            nodes_searched=self.nodes_count,
            time_spent=time.time() - self.start_time
        )

    def get_best_move(self, board: chess.Board) -> chess.Move:
        result = self.search(board)
        return result.best_move