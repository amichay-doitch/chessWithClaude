import chess
import time
import random
from typing import Optional, Tuple
from dataclasses import dataclass


@dataclass
class SearchResult:
    best_move: chess.Move
    score: int
    depth: int
    nodes_searched: int
    time_spent: float


class ChessEngine:
    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.start_time = None
        self.nodes_searched = 0

        # Piece-square tables (from black's perspective, so we flip for white)
        self.pst_pawn = [
            0, 0, 0, 0, 0, 0, 0, 0,
            50, 50, 50, 50, 50, 50, 50, 50,
            10, 10, 20, 30, 30, 20, 10, 10,
            5, 5, 10, 25, 25, 10, 5, 5,
            0, 0, 0, 20, 20, 0, 0, 0,
            5, -5, -10, 0, 0, -10, -5, 5,
            5, 10, 10, -20, -20, 10, 10, 5,
            0, 0, 0, 0, 0, 0, 0, 0
        ]

        self.pst_knight = [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20, 0, 0, 0, 0, -20, -40,
            -30, 0, 10, 15, 15, 10, 0, -30,
            -30, 5, 15, 20, 20, 15, 5, -30,
            -30, 0, 15, 20, 20, 15, 0, -30,
            -30, 5, 10, 15, 15, 10, 5, -30,
            -40, -20, 0, 5, 5, 0, -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50
        ]

        self.pst_bishop = [
            -20, -10, -10, -10, -10, -10, -10, -20,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -10, 0, 5, 10, 10, 5, 0, -10,
            -10, 5, 5, 10, 10, 5, 5, -10,
            -10, 0, 10, 10, 10, 10, 0, -10,
            -10, 10, 10, 10, 10, 10, 10, -10,
            -10, 5, 0, 0, 0, 0, 5, -10,
            -20, -10, -10, -10, -10, -10, -10, -20
        ]

        self.pst_rook = [
            0, 0, 0, 0, 0, 0, 0, 0,
            5, 10, 10, 10, 10, 10, 10, 5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            -5, 0, 0, 0, 0, 0, 0, -5,
            0, 0, 0, 5, 5, 0, 0, 0
        ]

        self.pst_queen = [
            -20, -10, -10, -5, -5, -10, -10, -20,
            -10, 0, 0, 0, 0, 0, 0, -10,
            -10, 0, 5, 5, 5, 5, 0, -10,
            -5, 0, 5, 5, 5, 5, 0, -5,
            0, 0, 5, 5, 5, 5, 0, -5,
            -10, 5, 5, 5, 5, 5, 0, -10,
            -10, 0, 5, 0, 0, 0, 0, -10,
            -20, -10, -10, -5, -5, -10, -10, -20
        ]

        self.pst_king = [
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -20, -30, -30, -40, -40, -30, -30, -20,
            -10, -20, -20, -20, -20, -20, -20, -10,
            20, 20, 0, 0, 0, 0, 20, 20,
            20, 30, 10, 0, 0, 10, 30, 20
        ]

        self.piece_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 320,
            chess.BISHOP: 330,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 20000
        }

        self.piece_square_tables = {
            chess.PAWN: self.pst_pawn,
            chess.KNIGHT: self.pst_knight,
            chess.BISHOP: self.pst_bishop,
            chess.ROOK: self.pst_rook,
            chess.QUEEN: self.pst_queen,
            chess.KING: self.pst_king
        }

    def evaluate(self, board: chess.Board) -> int:
        """Evaluate the position from white's perspective"""
        if board.is_checkmate():
            return -20000 if board.turn else 20000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0
        # Material and piece-square evaluation
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece is not None:
                piece_value = self.piece_values[piece.piece_type]
                pst = self.piece_square_tables[piece.piece_type]
                pst_value = pst[square] if piece.color == chess.WHITE else pst[chess.square_mirror(square)]

                if piece.color == chess.WHITE:
                    score += piece_value + pst_value
                else:
                    score -= piece_value + pst_value

        # Bonus for mobility
        if board.turn == chess.WHITE:
            score += len(list(board.legal_moves)) * 1
        else:
            score -= len(list(board.legal_moves)) * 1

        return score

    def quiescence_search(self, board: chess.Board, alpha: int, beta: int) -> int:
        """Quiescence search to handle tactical instability"""
        self.nodes_searched += 1

        # Check time limit
        if self.time_limit and time.time() - self.start_time > self.time_limit:
            return 0

        stand_pat = self.evaluate(board)

        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        # Generate captures only
        captures = []
        for move in board.legal_moves:
            if board.is_capture(move):
                captures.append(move)

        # Move ordering for captures: MVV-LVA
        def mvv_lva(move):
            attacker = board.piece_at(move.from_square).piece_type
            victim = board.piece_at(move.to_square)
            if victim is None:
                return 0
            victim = victim.piece_type
            return self.piece_values[victim] - self.piece_values[attacker]

        captures.sort(key=mvv_lva, reverse=True)

        for move in captures:
            board.push(move)
            score = -self.quiescence_search(board, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def move_ordering(self, board: chess.Board, moves: list, ply: int) -> list:
        """Order moves to improve alpha-beta pruning"""

        def score_move(move):
            score = 0
            # PV move would go here, but we don't track it
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if victim and attacker:
                    score += self.piece_values[victim.piece_type] * 10 - self.piece_values[attacker.piece_type]
            # Killer moves would go here
            # History heuristic would go here
            # Check moves get bonus
            if board.gives_check(move):
                score += 50
            return score

        return sorted(moves, key=score_move, reverse=True)

    def negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        """Negamax with alpha-beta pruning"""
        self.nodes_searched += 1

        # Check time limit
        if self.time_limit and time.time() - self.start_time > self.time_limit:
            return 0

        # Quiescence search at leaf nodes
        if depth == 0:
            return self.quiescence_search(board, alpha, beta)

        # Check for game end
        if board.is_game_over():
            if board.is_checkmate():
                return -20000 + ply if board.turn else 20000 - ply
            return 0

        moves = list(board.legal_moves)
        if not moves:
            return self.evaluate(board)

        moves = self.move_ordering(board, moves, ply)

        best_score = -20000
        for move in moves:
            board.push(move)
            score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()

            if score > best_score:
                best_score = score

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def iterative_deepening(self, board: chess.Board, max_depth: int, time_limit: float) -> Tuple[chess.Move, int]:
        """Iterative deepening with time management"""
        best_move = None
        best_score = -20000 if board.turn else 20000

        for depth in range(1, max_depth + 1):
            self.nodes_searched = 0
            current_best_move = None
            alpha, beta = -20000, 20000

            moves = list(board.legal_moves)
            if not moves:
                break

            moves = self.move_ordering(board, moves, 0)

            for move in moves:
                board.push(move)
                score = -self.negamax(board, depth - 1, -beta, -alpha, 1)
                board.pop()

                if (board.turn and score > best_score) or (not board.turn and score < best_score):
                    best_score = score
                    best_move = move
                    current_best_move = move

                if score >= beta:
                    best_move = move
                    break
                if score > alpha:
                    alpha = score

            # Check time limit after each depth
            if time_limit and time.time() - self.start_time > time_limit:
                break

        return best_move, best_score

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        """Search and return SearchResult with best_move, score, depth, nodes_searched, time_spent"""
        self.start_time = time.time()
        self.nodes_searched = 0

        search_depth = depth if depth is not None else self.max_depth
        actual_time_limit = self.time_limit

        # If no time limit is set, use a reasonable default based on depth
        if actual_time_limit is None:
            actual_time_limit = 10.0  # 10 seconds max if no explicit limit

        best_move, score = self.iterative_deepening(board, search_depth, actual_time_limit)

        # If no best move found, pick a random legal move
        if best_move is None:
            legal_moves = list(board.legal_moves)
            if legal_moves:
                best_move = random.choice(legal_moves)
            else:
                best_move = None

        time_spent = time.time() - self.start_time

        # Determine actual depth searched
        actual_depth = search_depth
        if self.time_limit and time_spent >= self.time_limit:
            # We might not have completed the last depth
            actual_depth = min(search_depth, int(time_spent / 0.1) + 1)

        return SearchResult(
            best_move=best_move,
            score=score,
            depth=actual_depth,
            nodes_searched=self.nodes_searched,
            time_spent=time_spent
        )

    def get_best_move(self, board: chess.Board) -> chess.Move:
        """Return best move for current position"""
        result = self.search(board)
        return result.best_move