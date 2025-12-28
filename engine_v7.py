"""
Chess Engine v7.0 - FAST ENGINE
Optimized for speed with advanced search techniques.

Key optimizations:
- Transposition table with proper usage
- Iterative deepening
- Move ordering (hash move, MVV-LVA, killers, history)
- Quiescence search
- Null move pruning
- Late move reductions
"""

import chess
import time
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

# Transposition table entry types
TT_EXACT = 0
TT_ALPHA = 1
TT_BETA = 2

@dataclass
class TTEntry:
    zobrist_key: int
    depth: int
    score: int
    flag: int
    best_move: Optional[chess.Move]

class ChessEngine:
    # Piece values
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000,
    }

    INFINITY = 999999
    MATE_SCORE = 100000
    TT_SIZE = 1 << 20  # 1 million entries

    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_searched = 0
        self.start_time = 0
        self.time_exceeded = False

        # Search tables
        self.tt = {}  # Transposition table
        self.killers = [[None, None] for _ in range(64)]  # Killer moves per ply
        self.history = defaultdict(int)  # History heuristic

    def clear_tables(self):
        """Clear search tables between games."""
        self.tt.clear()
        self.killers = [[None, None] for _ in range(64)]
        self.history.clear()

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        """Main search with iterative deepening."""
        if depth is None:
            depth = self.max_depth

        self.nodes_searched = 0
        self.start_time = time.time()
        self.time_exceeded = False

        best_move = None
        best_score = -self.INFINITY

        # Iterative deepening - search depth 1, 2, 3... up to max_depth
        for current_depth in range(1, depth + 1):
            if self.time_exceeded:
                break

            score = self.negamax(board, current_depth, -self.INFINITY, self.INFINITY, 0)

            # Get best move from transposition table
            zobrist_key = board._transposition_key()
            if zobrist_key in self.tt:
                entry = self.tt[zobrist_key]
                if entry.best_move:
                    best_move = entry.best_move
                    best_score = score

            # Check time
            if self.time_limit and (time.time() - self.start_time) >= self.time_limit:
                self.time_exceeded = True
                break

        time_spent = time.time() - self.start_time
        return SearchResult(
            best_move=best_move,
            score=best_score,
            depth=current_depth if self.time_exceeded else depth,
            nodes_searched=self.nodes_searched,
            time_spent=time_spent
        )

    def negamax(self, board: chess.Board, depth: int, alpha: int, beta: int, ply: int) -> int:
        """Negamax search with alpha-beta pruning."""
        self.nodes_searched += 1

        # Check time limit
        if self.time_limit and self.nodes_searched % 1024 == 0:
            if (time.time() - self.start_time) >= self.time_limit:
                self.time_exceeded = True
                return 0

        # Check for draw
        if board.is_repetition(2) or board.is_fifty_moves():
            return 0

        zobrist_key = board._transposition_key()

        # Probe transposition table
        hash_move = None
        if zobrist_key in self.tt:
            entry = self.tt[zobrist_key]
            if entry.depth >= depth:
                if entry.flag == TT_EXACT:
                    return entry.score
                elif entry.flag == TT_ALPHA and entry.score <= alpha:
                    return entry.score
                elif entry.flag == TT_BETA and entry.score >= beta:
                    return entry.score
            hash_move = entry.best_move

        # Terminal nodes
        if depth <= 0:
            return self.quiescence(board, alpha, beta)

        if board.is_game_over():
            if board.is_checkmate():
                return -self.MATE_SCORE + ply  # Prefer faster mates
            return 0  # Stalemate or insufficient material

        # Null move pruning
        if (depth >= 3 and not board.is_check() and
            self.has_non_pawn_material(board, board.turn)):
            board.push(chess.Move.null())
            score = -self.negamax(board, depth - 3, -beta, -beta + 1, ply + 1)
            board.pop()
            if score >= beta:
                return beta

        # Generate and order moves
        moves = self.order_moves(board, hash_move, ply)

        best_move = None
        best_score = -self.INFINITY
        flag = TT_ALPHA
        moves_searched = 0

        for move in moves:
            board.push(move)

            # Late move reductions (LMR)
            reduction = 0
            if (moves_searched >= 4 and depth >= 3 and
                not board.is_check() and not board.is_capture(move)):
                reduction = 1

            # Principal variation search (PVS)
            if moves_searched == 0:
                score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)
            else:
                # Search with null window
                score = -self.negamax(board, depth - 1 - reduction, -alpha - 1, -alpha, ply + 1)
                # Re-search if needed
                if score > alpha and score < beta:
                    score = -self.negamax(board, depth - 1, -beta, -alpha, ply + 1)

            board.pop()
            moves_searched += 1

            if score > best_score:
                best_score = score
                best_move = move

            if best_score > alpha:
                alpha = best_score
                flag = TT_EXACT

            if alpha >= beta:
                flag = TT_BETA
                # Store killer moves
                if not board.is_capture(move):
                    if self.killers[ply][0] != move:
                        self.killers[ply][1] = self.killers[ply][0]
                        self.killers[ply][0] = move
                    self.history[move] += depth * depth
                break

        # Store in transposition table
        if len(self.tt) < self.TT_SIZE:
            self.tt[zobrist_key] = TTEntry(
                zobrist_key=zobrist_key,
                depth=depth,
                score=best_score,
                flag=flag,
                best_move=best_move
            )

        return best_score

    def quiescence(self, board: chess.Board, alpha: int, beta: int) -> int:
        """Quiescence search - only search captures to avoid horizon effect."""
        self.nodes_searched += 1

        # Stand pat
        stand_pat = self.evaluate(board)
        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        # Only search captures
        for move in board.legal_moves:
            if not board.is_capture(move):
                continue

            board.push(move)
            score = -self.quiescence(board, -beta, -alpha)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def order_moves(self, board: chess.Board, hash_move: Optional[chess.Move], ply: int) -> list:
        """Order moves for better alpha-beta pruning."""
        moves = list(board.legal_moves)

        def move_score(move):
            score = 0

            # Hash move first (from TT)
            if move == hash_move:
                return 1000000

            # MVV-LVA for captures
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if victim and attacker:
                    victim_value = self.PIECE_VALUES[victim.piece_type]
                    attacker_value = self.PIECE_VALUES[attacker.piece_type]
                    score += 10000 + victim_value - attacker_value

            # Killer moves
            if move == self.killers[ply][0]:
                score += 9000
            elif move == self.killers[ply][1]:
                score += 8000

            # History heuristic
            score += self.history.get(move, 0)

            # Promotions
            if move.promotion:
                score += 5000

            return score

        moves.sort(key=move_score, reverse=True)
        return moves

    def has_non_pawn_material(self, board: chess.Board, color: chess.Color) -> bool:
        """Check if side has pieces other than pawns."""
        for piece_type in [chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
            if board.pieces(piece_type, color):
                return True
        return False

    def evaluate(self, board: chess.Board) -> int:
        """Fast evaluation function focused on material."""
        if board.is_checkmate():
            return -self.MATE_SCORE
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0

        # Material count
        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece:
                value = self.PIECE_VALUES[piece.piece_type]
                if piece.color == chess.WHITE:
                    score += value
                else:
                    score -= value

        # Simple bonuses
        # Mobility
        white_mobility = board.legal_moves.count() if board.turn == chess.WHITE else 0
        board.push(chess.Move.null())
        black_mobility = board.legal_moves.count() if board.turn == chess.BLACK else 0
        board.pop()
        score += (white_mobility - black_mobility) * 2

        # Bishop pair
        if len(list(board.pieces(chess.BISHOP, chess.WHITE))) >= 2:
            score += 30
        if len(list(board.pieces(chess.BISHOP, chess.BLACK))) >= 2:
            score -= 30

        # Perspective from side to move
        if board.turn == chess.BLACK:
            score = -score

        return score
