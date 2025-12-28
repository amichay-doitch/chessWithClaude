import chess
import chess.polyglot
import time
import math
from typing import Optional, Tuple, Dict, List

# --- Constants ---
PAWN_VALUE = 100
KNIGHT_VALUE = 320
BISHOP_VALUE = 330
ROOK_VALUE = 500
QUEEN_VALUE = 900
KING_VALUE = 20000

# Piece-square tables (simplified for brevity)
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
     5,  5, 10, 25, 25, 10,  5,  5,
     0,  0,  0, 20, 20,  0,  0,  0,
     5, -5,-10,  0,  0,-10, -5,  5,
     5, 10, 10,-20,-20, 10, 10,  5,
     0,  0,  0,  0,  0,  0,  0,  0
]
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]
ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]
KING_MIDDLEGAME_TABLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]
KING_ENDGAME_TABLE = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]

# --- SearchResult ---
class SearchResult:
    def __init__(self, best_move: chess.Move, score: int, depth: int, nodes_searched: int, time_spent: float):
        self.best_move = best_move
        self.score = score
        self.depth = depth
        self.nodes_searched = nodes_searched
        self.time_spent = time_spent

# --- ChessEngine ---
class ChessEngine:
    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_searched = 0
        self.start_time = 0
        self.stop_search = False
        self.transposition_table = {}
        self.killer_moves = [[] for _ in range(100)]
        self.history_heuristic = {}
        try:
            self.book = chess.polyglot.open_reader("book.bin")
        except:
            self.book = None

    def get_best_move(self, board: chess.Board) -> chess.Move:
        """Return best move for current position"""
        if self.book and not board.move_stack:
            try:
                move = self.book.weighted_choice(board).move()
                return move
            except:
                pass
        result = self.search(board)
        return result.best_move

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        """Search and return SearchResult with best_move, score, depth, nodes_searched, time_spent"""
        self.nodes_searched = 0
        self.stop_search = False
        self.start_time = time.time()
        best_move = None
        best_score = -math.inf
        depth = depth or self.max_depth
        for d in range(1, depth + 1):
            score = self._alpha_beta(board, d, -math.inf, math.inf, True)
            if self.stop_search:
                break
            best_score = score
        time_spent = time.time() - self.start_time
        return SearchResult(best_move, best_score, d, self.nodes_searched, time_spent)

    def _alpha_beta(self, board: chess.Board, depth: int, alpha: int, beta: int, maximizing_player: bool) -> int:
        if self.time_limit and time.time() - self.start_time > self.time_limit:
            self.stop_search = True
            return 0

        self.nodes_searched += 1
        hash_key = board.fen()
        if hash_key in self.transposition_table and self.transposition_table[hash_key]['depth'] >= depth:
            return self.transposition_table[hash_key]['score']

        if board.is_game_over():
            result = board.result()
            if result == "1-0":
                return 10000
            elif result == "0-1":
                return -10000
            else:
                return 0

        if depth == 0:
            return self._quiescence_search(board, alpha, beta)

        moves = self._order_moves(board, depth)
        if maximizing_player:
            max_eval = -math.inf
            for move in moves:
                board.push(move)
                eval = self._alpha_beta(board, depth - 1, alpha, beta, False)
                board.pop()
                if eval > max_eval:
                    max_eval = eval
                    if depth == self.max_depth:
                        best_move = move
                alpha = max(alpha, eval)
                if beta <= alpha:
                    break
            self.transposition_table[hash_key] = {'score': max_eval, 'depth': depth}
            return max_eval
        else:
            min_eval = math.inf
            for move in moves:
                board.push(move)
                eval = self._alpha_beta(board, depth - 1, alpha, beta, True)
                board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    break
            self.transposition_table[hash_key] = {'score': min_eval, 'depth': depth}
            return min_eval

    def _quiescence_search(self, board: chess.Board, alpha: int, beta: int) -> int:
        stand_pat = self._evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        for move in board.legal_moves:
            if board.is_capture(move):
                board.push(move)
                score = -self._quiescence_search(board, -beta, -alpha)
                board.pop()
                if score >= beta:
                    return beta
                if score > alpha:
                    alpha = score
        return alpha

    def _order_moves(self, board: chess.Board, depth: int) -> List[chess.Move]:
        moves = list(board.legal_moves)
        move_scores = []
        for move in moves:
            if move in self.killer_moves[depth]:
                move_scores.append((move, 1000000))
            elif board.is_capture(move):
                captured_piece = board.piece_at(move.to_square)
                capturing_piece = board.piece_at(move.from_square)
                see = self._see(board, move, capturing_piece, captured_piece)
                move_scores.append((move, see if see > 0 else 0))
            else:
                move_scores.append((move, self.history_heuristic.get(move, 0)))
        moves = [move for move, _ in sorted(move_scores, key=lambda x: x[1], reverse=True)]
        return moves

    def _see(self, board: chess.Board, move: chess.Move, attacker: chess.Piece, victim: chess.Piece) -> int:
        if attacker is None or victim is None:
            return 0
        attacker_value = self._piece_value(attacker)
        victim_value = self._piece_value(victim)
        if attacker_value <= victim_value:
            return victim_value - attacker_value
        return 0

    def _evaluate(self, board: chess.Board) -> int:
        if board.is_game_over():
            result = board.result()
            if result == "1-0":
                return 10000
            elif result == "0-1":
                return -10000
            else:
                return 0

        material = 0
        positional = 0
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self._piece_value(piece)
                material += value if piece.color == chess.WHITE else -value
                positional += self._positional_value(piece, square, board)

        return material + positional

    def _piece_value(self, piece: chess.Piece) -> int:
        if piece.piece_type == chess.PAWN:
            return PAWN_VALUE
        elif piece.piece_type == chess.KNIGHT:
            return KNIGHT_VALUE
        elif piece.piece_type == chess.BISHOP:
            return BISHOP_VALUE
        elif piece.piece_type == chess.ROOK:
            return ROOK_VALUE
        elif piece.piece_type == chess.QUEEN:
            return QUEEN_VALUE
        elif piece.piece_type == chess.KING:
            return KING_VALUE
        return 0

    def _positional_value(self, piece: chess.Piece, square: chess.Square, board: chess.Board) -> int:
        file = chess.square_file(square)
        rank = chess.square_rank(square)
        index = rank * 8 + file
        if piece.piece_type == chess.PAWN:
            table = PAWN_TABLE
        elif piece.piece_type == chess.KNIGHT:
            table = KNIGHT_TABLE
        elif piece.piece_type == chess.BISHOP:
            table = BISHOP_TABLE
        elif piece.piece_type == chess.ROOK:
            table = ROOK_TABLE
        elif piece.piece_type == chess.QUEEN:
            table = QUEEN_TABLE
        elif piece.piece_type == chess.KING:
            if self._is_endgame(board):
                table = KING_ENDGAME_TABLE
            else:
                table = KING_MIDDLEGAME_TABLE
        else:
            return 0
        value = table[index]
        return value if piece.color == chess.WHITE else -value

    def _is_endgame(self, board: chess.Board) -> bool:
        queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
        return queens == 0
