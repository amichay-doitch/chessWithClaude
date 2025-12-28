import chess
import time
from dataclasses import dataclass
from typing import Optional, List, Tuple
import random


@dataclass
class SearchResult:
    best_move: chess.Move
    score: float
    depth: int
    nodes_searched: int
    time_spent: float


class ChessEngine:
    # Piece values
    PIECE_VALUES = {
        chess.PAWN: 100,
        chess.KNIGHT: 320,
        chess.BISHOP: 330,
        chess.ROOK: 500,
        chess.QUEEN: 900,
        chess.KING: 20000
    }

    # Piece-square tables for positional evaluation
    PAWN_TABLE = [
        0, 0, 0, 0, 0, 0, 0, 0,
        50, 50, 50, 50, 50, 50, 50, 50,
        10, 10, 20, 30, 30, 20, 10, 10,
        5, 5, 10, 25, 25, 10, 5, 5,
        0, 0, 0, 20, 20, 0, 0, 0,
        5, -5, -10, 0, 0, -10, -5, 5,
        5, 10, 10, -20, -20, 10, 10, 5,
        0, 0, 0, 0, 0, 0, 0, 0
    ]

    KNIGHT_TABLE = [
        -50, -40, -30, -30, -30, -30, -40, -50,
        -40, -20, 0, 0, 0, 0, -20, -40,
        -30, 0, 10, 15, 15, 10, 0, -30,
        -30, 5, 15, 20, 20, 15, 5, -30,
        -30, 0, 15, 20, 20, 15, 0, -30,
        -30, 5, 10, 15, 15, 10, 5, -30,
        -40, -20, 0, 5, 5, 0, -20, -40,
        -50, -40, -30, -30, -30, -30, -40, -50
    ]

    BISHOP_TABLE = [
        -20, -10, -10, -10, -10, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 10, 10, 5, 0, -10,
        -10, 5, 5, 10, 10, 5, 5, -10,
        -10, 0, 10, 10, 10, 10, 0, -10,
        -10, 10, 10, 10, 10, 10, 10, -10,
        -10, 5, 0, 0, 0, 0, 5, -10,
        -20, -10, -10, -10, -10, -10, -10, -20
    ]

    ROOK_TABLE = [
        0, 0, 0, 0, 0, 0, 0, 0,
        5, 10, 10, 10, 10, 10, 10, 5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        -5, 0, 0, 0, 0, 0, 0, -5,
        0, 0, 0, 5, 5, 0, 0, 0
    ]

    QUEEN_TABLE = [
        -20, -10, -10, -5, -5, -10, -10, -20,
        -10, 0, 0, 0, 0, 0, 0, -10,
        -10, 0, 5, 5, 5, 5, 0, -10,
        -5, 0, 5, 5, 5, 5, 0, -5,
        0, 0, 5, 5, 5, 5, 0, -5,
        -10, 5, 5, 5, 5, 5, 0, -10,
        -10, 0, 5, 0, 0, 0, 0, -10,
        -20, -10, -10, -5, -5, -10, -10, -20
    ]

    KING_MIDDLE_GAME = [
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -30, -40, -40, -50, -50, -40, -40, -30,
        -20, -30, -30, -40, -40, -30, -30, -20,
        -10, -20, -20, -20, -20, -20, -20, -10,
        20, 20, 0, 0, 0, 0, 20, 20,
        20, 30, 10, 0, 0, 10, 30, 20
    ]

    KING_END_GAME = [
        -50, -40, -30, -20, -20, -30, -40, -50,
        -30, -20, -10, 0, 0, -10, -20, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 30, 40, 40, 30, -10, -30,
        -30, -10, 20, 30, 30, 20, -10, -30,
        -30, -30, 0, 0, 0, 0, -30, -30,
        -50, -30, -30, -30, -30, -30, -30, -50
    ]

    def __init__(self, max_depth: int = 6, time_limit: float = None):
        self.max_depth = max_depth
        self.time_limit = time_limit
        self.nodes_searched = 0
        self.start_time = 0
        self.should_stop = False

        # Transposition table
        self.transposition_table = {}
        self.EXACT = 0
        self.LOWER_BOUND = 1
        self.UPPER_BOUND = 2

        # Killer moves (two per depth)
        self.killer_moves = [[None, None] for _ in range(100)]

        # History heuristic
        self.history_table = {}

    def get_best_move(self, board: chess.Board) -> chess.Move:
        """Return best move for current position"""
        result = self.search(board)
        return result.best_move

    def search(self, board: chess.Board, depth: int = None) -> SearchResult:
        """Search and return SearchResult with best_move, score, depth, nodes_searched, time_spent"""
        self.start_time = time.time()
        self.nodes_searched = 0
        self.should_stop = False
        search_depth = depth if depth is not None else self.max_depth

        # Clear tables for new search
        self.transposition_table.clear()
        self.killer_moves = [[None, None] for _ in range(100)]
        self.history_table.clear()

        best_move = None
        best_score = float('-inf')

        # Iterative deepening
        for current_depth in range(1, search_depth + 1):
            if self.should_stop:
                break

            score, move = self.iterative_deepening_search(board, current_depth)

            if move is not None:
                best_move = move
                best_score = score

            # Check time
            if self.time_limit and (time.time() - self.start_time) >= self.time_limit:
                break

        time_spent = time.time() - self.start_time

        # Fallback to random legal move if no move found
        if best_move is None:
            legal_moves = list(board.legal_moves)
            if legal_moves:
                best_move = random.choice(legal_moves)
                best_score = self.evaluate_board(board)

        return SearchResult(
            best_move=best_move,
            score=best_score,
            depth=search_depth,
            nodes_searched=self.nodes_searched,
            time_spent=time_spent
        )

    def iterative_deepening_search(self, board: chess.Board, depth: int) -> Tuple[float, Optional[chess.Move]]:
        """Perform alpha-beta search at a specific depth"""
        alpha = float('-inf')
        beta = float('inf')
        best_move = None
        best_score = float('-inf')

        moves = self.order_moves(board, None, 0)

        for move in moves:
            if self.should_stop:
                break

            board.push(move)
            score = -self.alpha_beta(board, depth - 1, -beta, -alpha, 1)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

        return best_score, best_move

    def alpha_beta(self, board: chess.Board, depth: int, alpha: float, beta: float, ply: int) -> float:
        """Alpha-beta pruning search"""
        # Check time limit
        if self.time_limit and (time.time() - self.start_time) >= self.time_limit:
            self.should_stop = True
            return 0

        self.nodes_searched += 1

        # Check transposition table
        board_hash = hash(board.fen())
        if board_hash in self.transposition_table:
            tt_entry = self.transposition_table[board_hash]
            if tt_entry['depth'] >= depth:
                if tt_entry['flag'] == self.EXACT:
                    return tt_entry['score']
                elif tt_entry['flag'] == self.LOWER_BOUND:
                    alpha = max(alpha, tt_entry['score'])
                elif tt_entry['flag'] == self.UPPER_BOUND:
                    beta = min(beta, tt_entry['score'])

                if alpha >= beta:
                    return tt_entry['score']

        # Check for terminal positions
        if board.is_checkmate():
            return -20000 + ply
        if board.is_stalemate() or board.is_insufficient_material() or board.is_seventyfive_moves() or board.is_fivefold_repetition():
            return 0

        # Quiescence search at leaf nodes
        if depth <= 0:
            return self.quiescence_search(board, alpha, beta)

        best_score = float('-inf')
        best_move = None
        flag = self.UPPER_BOUND

        moves = self.order_moves(board, board_hash, ply)

        for move in moves:
            board.push(move)
            score = -self.alpha_beta(board, depth - 1, -beta, -alpha, ply + 1)
            board.pop()

            if score > best_score:
                best_score = score
                best_move = move

            alpha = max(alpha, score)

            if alpha >= beta:
                # Beta cutoff - update killer moves and history
                if not board.is_capture(move):
                    self.update_killer_moves(move, ply)
                    self.update_history(move, depth)
                flag = self.LOWER_BOUND
                break

        if best_score > alpha:
            flag = self.EXACT

        # Store in transposition table
        self.transposition_table[board_hash] = {
            'score': best_score,
            'depth': depth,
            'flag': flag,
            'move': best_move
        }

        return best_score

    def quiescence_search(self, board: chess.Board, alpha: float, beta: float, depth: int = 0) -> float:
        """Quiescence search to avoid horizon effect"""
        if depth > 10:  # Limit quiescence depth
            return self.evaluate_board(board)

        self.nodes_searched += 1

        stand_pat = self.evaluate_board(board)

        if stand_pat >= beta:
            return beta
        if alpha < stand_pat:
            alpha = stand_pat

        # Only consider captures and checks
        moves = [m for m in board.legal_moves if board.is_capture(m) or board.gives_check(m)]
        moves = self.order_captures(board, moves)

        for move in moves:
            board.push(move)
            score = -self.quiescence_search(board, -beta, -alpha, depth + 1)
            board.pop()

            if score >= beta:
                return beta
            if score > alpha:
                alpha = score

        return alpha

    def order_moves(self, board: chess.Board, board_hash: Optional[int], ply: int) -> List[chess.Move]:
        """Order moves for better alpha-beta pruning"""
        moves = list(board.legal_moves)

        def move_priority(move):
            score = 0

            # Transposition table move
            if board_hash and board_hash in self.transposition_table:
                if self.transposition_table[board_hash].get('move') == move:
                    return 10000000

            # MVV-LVA for captures
            if board.is_capture(move):
                victim = board.piece_at(move.to_square)
                attacker = board.piece_at(move.from_square)
                if victim and attacker:
                    score += 1000000 + self.PIECE_VALUES[victim.piece_type] - self.PIECE_VALUES[
                        attacker.piece_type] // 10

            # Killer moves
            if ply < len(self.killer_moves):
                if move == self.killer_moves[ply][0]:
                    score += 900000
                elif move == self.killer_moves[ply][1]:
                    score += 800000

            # History heuristic
            move_key = (move.from_square, move.to_square)
            if move_key in self.history_table:
                score += self.history_table[move_key]

            # Promotions
            if move.promotion:
                score += 500000

            # Checks
            board.push(move)
            if board.is_check():
                score += 100000
            board.pop()

            return score

        moves.sort(key=move_priority, reverse=True)
        return moves

    def order_captures(self, board: chess.Board, moves: List[chess.Move]) -> List[chess.Move]:
        """Order captures using MVV-LVA"""

        def capture_priority(move):
            victim = board.piece_at(move.to_square)
            attacker = board.piece_at(move.from_square)
            if victim and attacker:
                return self.PIECE_VALUES[victim.piece_type] - self.PIECE_VALUES[attacker.piece_type] // 10
            return 0

        moves.sort(key=capture_priority, reverse=True)
        return moves

    def update_killer_moves(self, move: chess.Move, ply: int):
        """Update killer moves table"""
        if ply < len(self.killer_moves):
            if move != self.killer_moves[ply][0]:
                self.killer_moves[ply][1] = self.killer_moves[ply][0]
                self.killer_moves[ply][0] = move

    def update_history(self, move: chess.Move, depth: int):
        """Update history heuristic table"""
        move_key = (move.from_square, move.to_square)
        if move_key not in self.history_table:
            self.history_table[move_key] = 0
        self.history_table[move_key] += depth * depth

    def evaluate_board(self, board: chess.Board) -> float:
        """Evaluate the board position"""
        if board.is_checkmate():
            return -20000
        if board.is_stalemate() or board.is_insufficient_material():
            return 0

        score = 0

        # Material and positional evaluation
        score += self.evaluate_material_and_position(board, chess.WHITE)
        score -= self.evaluate_material_and_position(board, chess.BLACK)

        # Mobility bonus
        score += self.evaluate_mobility(board)

        # Pawn structure
        score += self.evaluate_pawn_structure(board)

        # King safety
        score += self.evaluate_king_safety(board)

        # Return score from perspective of side to move
        return score if board.turn == chess.WHITE else -score

    def evaluate_material_and_position(self, board: chess.Board, color: chess.Color) -> float:
        """Evaluate material and piece positions"""
        score = 0

        for square in chess.SQUARES:
            piece = board.piece_at(square)
            if piece and piece.color == color:
                # Material value
                score += self.PIECE_VALUES[piece.piece_type]

                # Positional value
                sq_index = square if color == chess.WHITE else chess.square_mirror(square)

                if piece.piece_type == chess.PAWN:
                    score += self.PAWN_TABLE[sq_index]
                elif piece.piece_type == chess.KNIGHT:
                    score += self.KNIGHT_TABLE[sq_index]
                elif piece.piece_type == chess.BISHOP:
                    score += self.BISHOP_TABLE[sq_index]
                elif piece.piece_type == chess.ROOK:
                    score += self.ROOK_TABLE[sq_index]
                elif piece.piece_type == chess.QUEEN:
                    score += self.QUEEN_TABLE[sq_index]
                elif piece.piece_type == chess.KING:
                    # Use endgame or middlegame table
                    if self.is_endgame(board):
                        score += self.KING_END_GAME[sq_index]
                    else:
                        score += self.KING_MIDDLE_GAME[sq_index]

        return score

    def evaluate_mobility(self, board: chess.Board) -> float:
        """Evaluate mobility (number of legal moves)"""
        current_turn = board.turn

        white_mobility = 0
        black_mobility = 0

        if board.turn == chess.WHITE:
            white_mobility = board.legal_moves.count()
            board.push(chess.Move.null())
            black_mobility = board.legal_moves.count()
            board.pop()
        else:
            black_mobility = board.legal_moves.count()
            board.push(chess.Move.null())
            white_mobility = board.legal_moves.count()
            board.pop()

        return (white_mobility - black_mobility) * 0.1

    def evaluate_pawn_structure(self, board: chess.Board) -> float:
        """Evaluate pawn structure (doubled, isolated, passed pawns)"""
        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1

            pawns = board.pieces(chess.PAWN, color)

            for square in pawns:
                file = chess.square_file(square)
                rank = chess.square_rank(square)

                # Passed pawns
                is_passed = True
                if color == chess.WHITE:
                    for r in range(rank + 1, 8):
                        for f in [file - 1, file, file + 1]:
                            if 0 <= f < 8:
                                sq = chess.square(f, r)
                                if board.piece_at(sq) == chess.Piece(chess.PAWN, chess.BLACK):
                                    is_passed = False
                                    break
                        if not is_passed:
                            break
                else:
                    for r in range(0, rank):
                        for f in [file - 1, file, file + 1]:
                            if 0 <= f < 8:
                                sq = chess.square(f, r)
                                if board.piece_at(sq) == chess.Piece(chess.PAWN, chess.WHITE):
                                    is_passed = False
                                    break
                        if not is_passed:
                            break

                if is_passed:
                    bonus = 20 * (rank if color == chess.WHITE else 7 - rank)
                    score += multiplier * bonus

                # Doubled pawns (penalty)
                same_file_pawns = sum(1 for sq in pawns if chess.square_file(sq) == file)
                if same_file_pawns > 1:
                    score -= multiplier * 15

                # Isolated pawns (penalty)
                has_neighbor = False
                for f in [file - 1, file + 1]:
                    if 0 <= f < 8:
                        if any(chess.square_file(sq) == f for sq in pawns):
                            has_neighbor = True
                            break
                if not has_neighbor:
                    score -= multiplier * 10

        return score

    def evaluate_king_safety(self, board: chess.Board) -> float:
        """Evaluate king safety"""
        if self.is_endgame(board):
            return 0

        score = 0

        for color in [chess.WHITE, chess.BLACK]:
            multiplier = 1 if color == chess.WHITE else -1
            king_square = board.king(color)

            if king_square is None:
                continue

            # Pawn shield
            king_file = chess.square_file(king_square)
            king_rank = chess.square_rank(king_square)

            shield_bonus = 0
            if color == chess.WHITE and king_rank <= 1:
                for f in range(max(0, king_file - 1), min(8, king_file + 2)):
                    for r in range(king_rank + 1, min(8, king_rank + 3)):
                        sq = chess.square(f, r)
                        piece = board.piece_at(sq)
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            shield_bonus += 10
            elif color == chess.BLACK and king_rank >= 6:
                for f in range(max(0, king_file - 1), min(8, king_file + 2)):
                    for r in range(max(0, king_rank - 2), king_rank):
                        sq = chess.square(f, r)
                        piece = board.piece_at(sq)
                        if piece and piece.piece_type == chess.PAWN and piece.color == color:
                            shield_bonus += 10

            score += multiplier * shield_bonus

        return score

    def is_endgame(self, board: chess.Board) -> bool:
        """Determine if we're in endgame"""
        queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
        minors = (len(board.pieces(chess.KNIGHT, chess.WHITE)) + len(board.pieces(chess.BISHOP, chess.WHITE)) +
                  len(board.pieces(chess.KNIGHT, chess.BLACK)) + len(board.pieces(chess.BISHOP, chess.BLACK)))

        return queens == 0 or (queens == 2 and minors <= 2)


# Example usage and testing
if __name__ == "__main__":
    import chess

    # Create engine
    engine = ChessEngine(max_depth=6, time_limit=5.0)

    # Test position
    board = chess.Board()

    print("Starting position:")
    print(board)
    print()

    # Get best move
    result = engine.search(board)

    print(f"Best move: {result.best_move}")
    print(f"Score: {result.score}")
    print(f"Depth: {result.depth}")
    print(f"Nodes searched: {result.nodes_searched}")
    print(f"Time spent: {result.time_spent:.3f}s")
    print(f"Nodes/sec: {result.nodes_searched / result.time_spent:.0f}")

    # Make the move
    board.push(result.best_move)
    print(f"\nPosition after {result.best_move}:")
    print(board)