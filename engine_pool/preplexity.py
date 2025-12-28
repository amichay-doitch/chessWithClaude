import time
import math
from dataclasses import dataclass
from typing import Optional, Tuple, Dict, List

import chess


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
        self.time_limit = time_limit  # seconds
        self.start_time: float = 0.0
        self.nodes: int = 0
        self.stop: bool = False

        # Transposition table: zobrist key -> (depth, score, flag, best_move)
        # flag: 0=exact, -1=alpha, 1=beta
        self.tt: Dict[int, Tuple[int, int, int, Optional[chess.Move]]] = {}

        # Killer moves: killer_moves[depth] = [move1, move2]
        self.killer_moves: Dict[int, List[chess.Move]] = {}

        # History heuristic: history[(color, from_sq, to_sq)] = score
        self.history: Dict[Tuple[bool, int, int], int] = {}

        # Evaluation constants (centipawns)
        self.PAWN = 100
        self.KNIGHT = 320
        self.BISHOP = 330
        self.ROOK = 500
        self.QUEEN = 900

        # Piece-square tables (simplified, from white perspective)
        # Values adapted from common PSTs [web:24]
        self.pawn_table = [
              0,   0,   0,   0,   0,   0,   0,   0,
             50,  50,  50,  50,  50,  50,  50,  50,
             10,  10,  20,  30,  30,  20,  10,  10,
              5,   5,  10,  25,  25,  10,   5,   5,
              0,   0,   0,  20,  20,   0,   0,   0,
              5,  -5, -10,   0,   0, -10,  -5,   5,
              5,  10,  10, -20, -20,  10,  10,   5,
              0,   0,   0,   0,   0,   0,   0,   0,
        ]

        self.knight_table = [
            -50, -40, -30, -30, -30, -30, -40, -50,
            -40, -20,   0,   5,   5,   0, -20, -40,
            -30,   5,  10,  15,  15,  10,   5, -30,
            -30,   0,  15,  20,  20,  15,   0, -30,
            -30,   5,  15,  20,  20,  15,   5, -30,
            -30,   0,  10,  15,  15,  10,   0, -30,
            -40, -20,   0,   0,   0,   0, -20, -40,
            -50, -40, -30, -30, -30, -30, -40, -50,
        ]

        self.bishop_table = [
            -20, -10, -10, -10, -10, -10, -10, -20,
            -10,   5,   0,   0,   0,   0,   5, -10,
            -10,  10,  10,  10,  10,  10,  10, -10,
            -10,   0,  10,  10,  10,  10,   0, -10,
            -10,   5,   5,  10,  10,   5,   5, -10,
            -10,   0,   5,  10,  10,   5,   0, -10,
            -10,   0,   0,   0,   0,   0,   0, -10,
            -20, -10, -10, -10, -10, -10, -10, -20,
        ]

        self.rook_table = [
              0,   0,   5,  10,  10,   5,   0,   0,
            - 5,   0,   0,   0,   0,   0,   0,  -5,
            - 5,   0,   0,   0,   0,   0,   0,  -5,
            - 5,   0,   0,   0,   0,   0,   0,  -5,
            - 5,   0,   0,   0,   0,   0,   0,  -5,
            - 5,   0,   0,   0,   0,   0,   0,  -5,
              5,  10,  10,  10,  10,  10,  10,   5,
              0,   0,   0,   0,   0,   0,   0,   0,
        ]

        self.queen_table = [
            -20, -10, -10, - 5, - 5, -10, -10, -20,
            -10,   0,   5,   0,   0,   0,   0, -10,
            -10,   5,   5,   5,   5,   5,   0, -10,
             -5,   0,   5,   5,   5,   5,   0,  -5,
              0,   0,   5,   5,   5,   5,   0,  -5,
            -10,   5,   5,   5,   5,   5,   0, -10,
            -10,   0,   5,   0,   0,   0,   0, -10,
            -20, -10, -10, - 5, - 5, -10, -10, -20,
        ]

        self.king_table_mid = [
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -30, -40, -40, -50, -50, -40, -40, -30,
            -20, -30, -30, -40, -40, -30, -30, -20,
            -10, -20, -20, -20, -20, -20, -20, -10,
             20,  20,   0,   0,   0,   0,  20,  20,
             20,  30,  10,   0,   0,  10,  30,  20,
        ]

        self.king_table_end = [
            -50, -40, -30, -20, -20, -30, -40, -50,
            -30, -20, -10,   0,   0, -10, -20, -30,
            -30, -10,  20,  30,  30,  20, -10, -30,
            -30, -10,  30,  40,  40,  30, -10, -30,
            -30, -10,  30,  40,  40,  30, -10, -30,
            -30, -10,  20,  30,  30,  20, -10, -30,
            -30, -30,   0,   0,   0,   0, -30, -30,
            -50, -30, -30, -30, -30, -30, -30, -50,
        ]

        # For mate scores
        self.MATE_SCORE = 100000
        self.MATE_THRESHOLD = self.MATE_SCORE - 1000

    def _time_up(self) -> bool:
        if self.time_limit is None:
            return False
        return (time.time() - self.start_time) >= self.time_limit

    # -------------------- Public API --------------------

    def get_best_move(self, board: chess.Board) -> chess.Move:
        result = self.search(board)
        return result.best_move

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        search_depth = depth if depth is not None else self.max_depth
        self.start_time = time.time()
        self.nodes = 0
        self.stop = False

        best_move: Optional[chess.Move] = None
        best_score = -math.inf
        last_completed_depth = 0

        # Clear helpers but keep TT to reuse info
        self.killer_moves.clear()
        self.history.clear()

        # Iterative deepening [web:24]
        for current_depth in range(1, search_depth + 1):
            if self._time_up():
                break

            alpha = -self.MATE_SCORE
            beta = self.MATE_SCORE
            pv_move = best_move  # Use previous best as PV move ordering

            score, move = self._negamax(
                board,
                depth=current_depth,
                alpha=alpha,
                beta=beta,
                ply=0,
                pv_move=pv_move,
            )

            if self.stop:
                break

            if move is not None:
                best_move = move
                best_score = score
            last_completed_depth = current_depth

        elapsed = time.time() - self.start_time
        if best_move is None:
            # Fallback: make any legal move
            moves = list(board.legal_moves)
            if moves:
                best_move = moves[0]
                best_score = 0
            else:
                best_score = self._evaluate(board)

        return SearchResult(
            best_move=best_move,
            score=int(best_score),
            depth=last_completed_depth,
            nodes_searched=self.nodes,
            time_spent=elapsed,
        )

    # -------------------- Search core --------------------

    def _negamax(
        self,
        board: chess.Board,
        depth: int,
        alpha: int,
        beta: int,
        ply: int,
        pv_move: Optional[chess.Move] = None,
    ) -> Tuple[int, Optional[chess.Move]]:
        if self._time_up():
            self.stop = True
            return 0, None

        self.nodes += 1
        alpha_orig = alpha

        # Transposition table lookup
        key = board.zobrist_hash()
        if key in self.tt:
            tt_depth, tt_score, tt_flag, tt_move = self.tt[key]
            if tt_depth >= depth:
                if tt_flag == 0:
                    return tt_score, tt_move
                elif tt_flag == -1:
                    alpha = max(alpha, tt_score)
                elif tt_flag == 1:
                    beta = min(beta, tt_score)
                if alpha >= beta:
                    return tt_score, tt_move
            # Use tt_move as pv candidate if provided
            if pv_move is None and tt_move is not None:
                pv_move = tt_move

        # Terminal node
        if depth <= 0:
            score = self._quiescence(board, alpha, beta, ply)
            return score, None

        if board.is_game_over():
            score = self._evaluate_terminal(board, ply)
            return score, None

        best_move: Optional[chess.Move] = None
        legal_moves = list(board.legal_moves)
        if not legal_moves:
            score = self._evaluate_terminal(board, ply)
            return score, None

        moves_ordered = self._order_moves(board, legal_moves, pv_move, ply)

        best_score = -self.MATE_SCORE
        for move in moves_ordered:
            if self._time_up():
                self.stop = True
                break

            board.push(move)
            score, _ = self._negamax(
                board,
                depth=depth - 1,
                alpha=-beta,
                beta=-alpha,
                ply=ply + 1,
                pv_move=None,
            )
            score = -score
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            if best_score > alpha:
                alpha = best_score
                # Update history heuristic
                if not board.is_capture(move):
                    key_hist = (board.turn, move.from_square, move.to_square)
                    self.history[key_hist] = self.history.get(key_hist, 0) + depth * depth

            if alpha >= beta:
                # Beta cutoff: killer move heuristic
                if not board.is_capture(move):
                    killers = self.killer_moves.get(ply, [])
                    if move not in killers:
                        if len(killers) < 2:
                            killers.append(move)
                        else:
                            killers[1] = killers[0]
                            killers[0] = move
                        self.killer_moves[ply] = killers
                break

        # Store in TT
        flag = 0
        if best_score <= alpha_orig:
            flag = -1  # alpha
        elif best_score >= beta:
            flag = 1   # beta

        self.tt[key] = (depth, int(best_score), flag, best_move)

        return best_score, best_move

    def _quiescence(self, board: chess.Board, alpha: int, beta: int, ply: int) -> int:
        if self._time_up():
            self.stop = True
            return 0

        self.nodes += 1

        stand_pat = self._evaluate(board)
        if stand_pat >= beta:
            return beta
        if stand_pat > alpha:
            alpha = stand_pat

        # Only consider captures (and promotions) in quiescence [web:18][web:22]
        for move in self._order_moves(board, list(board.legal_moves), None, ply, quiescence=True):
            if not board.is_capture(move) and not move.promotion:
                continue

            board.push(move)
            score = -self._quiescence(board, -beta, -alpha, ply + 1)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    # -------------------- Move ordering --------------------

    def _order_moves(
        self,
        board: chess.Board,
        moves: List[chess.Move],
        pv_move: Optional[chess.Move],
        ply: int,
        quiescence: bool = False,
    ) -> List[chess.Move]:
        # MVV-LVA scores for captures
        mvv_lva_values = {
            chess.PAWN: 100,
            chess.KNIGHT: 300,
            chess.BISHOP: 300,
            chess.ROOK: 500,
            chess.QUEEN: 900,
            chess.KING: 10000,
        }

        def move_score(m: chess.Move) -> int:
            score = 0
            # Principal variation move
            if pv_move is not None and m == pv_move:
                score += 1_000_000
            # Captures
            if board.is_capture(m):
                captured_piece_type = board.piece_type_at(m.to_square)
                mover_piece_type = board.piece_type_at(m.from_square)
                cap_val = mvv_lva_values.get(captured_piece_type, 0)
                mov_val = mvv_lva_values.get(mover_piece_type, 1)
                score += 500_000 + (cap_val * 10 - mov_val)
            else:
                # Killer moves
                killers = self.killer_moves.get(ply, [])
                if m in killers:
                    score += 300_000
                # History heuristic
                key_hist = (board.turn, m.from_square, m.to_square)
                score += self.history.get(key_hist, 0)
            return score

        scored_moves = [(move_score(m), m) for m in moves]
        scored_moves.sort(key=lambda x: x[0], reverse=True)
        return [m for _, m in scored_moves]

    # -------------------- Evaluation --------------------

    def _evaluate_terminal(self, board: chess.Board, ply: int) -> int:
        if board.is_checkmate():
            # Mate is bad for side to move
            return - (self.MATE_SCORE - ply)
        # Stalemate or other draws
        return 0

    def _evaluate(self, board: chess.Board) -> int:
        if board.is_game_over():
            return self._evaluate_terminal(board, 0)

        # Material + piece-square evaluation [web:24]
        score = 0

        # Phase: decide mid vs endgame for king PST
        total_material = 0
        for piece_type in [chess.QUEEN, chess.ROOK, chess.BISHOP, chess.KNIGHT]:
            total_material += len(board.pieces(piece_type, chess.WHITE)) * self._piece_value(piece_type)
            total_material += len(board.pieces(piece_type, chess.BLACK)) * self._piece_value(piece_type)

        endgame = total_material < 2 * (self.ROOK + self.BISHOP + self.KNIGHT)

        for piece_type in chess.PIECE_TYPES:
            for sq in board.pieces(piece_type, chess.WHITE):
                score += self._piece_value(piece_type)
                score += self._piece_square_value(piece_type, sq, True, endgame)
            for sq in board.pieces(piece_type, chess.BLACK):
                score -= self._piece_value(piece_type)
                score -= self._piece_square_value(piece_type, sq, False, endgame)

        # Simple mobility bonus
        score += 5 * (board.legal_moves.count())
        board.push(chess.Move.null())
        opp_mobility = board.legal_moves.count()
        board.pop()
        score -= 5 * opp_mobility

        # From side to move perspective
        return score if board.turn == chess.WHITE else -score

    def _piece_value(self, piece_type: int) -> int:
        if piece_type == chess.PAWN:
            return self.PAWN
        if piece_type == chess.KNIGHT:
            return self.KNIGHT
        if piece_type == chess.BISHOP:
            return self.BISHOP
        if piece_type == chess.ROOK:
            return self.ROOK
        if piece_type == chess.QUEEN:
            return self.QUEEN
        return 0  # king has no fixed material value

    def _piece_square_value(
        self,
        piece_type: int,
        square: int,
        white: bool,
        endgame: bool,
    ) -> int:
        rank = chess.square_rank(square)
        file = chess.square_file(square)
        idx = rank * 8 + file
        if not white:
            # Mirror vertically for black
            idx = (7 - rank) * 8 + file

        if piece_type == chess.PAWN:
            return self.pawn_table[idx]
        if piece_type == chess.KNIGHT:
            return self.knight_table[idx]
        if piece_type == chess.BISHOP:
            return self.bishop_table[idx]
        if piece_type == chess.ROOK:
            return self.rook_table[idx]
        if piece_type == chess.QUEEN:
            return self.queen_table[idx]
        if piece_type == chess.KING:
            return (self.king_table_end[idx] if endgame else self.king_table_mid[idx])
        return 0


# -------------------- Example usage --------------------
if __name__ == "__main__":
    # Simple test: find a move from starting position with 2 seconds limit
    board = chess.Board()
    engine = ChessEngine(max_depth=6, time_limit=2.0)
    result = engine.search(board)
    print("Best move:", result.best_move)
    print("Score:", result.score)
    print("Depth reached:", result.depth)
    print("Nodes searched:", result.nodes_searched)
    print("Time spent:", result.time_spent)
