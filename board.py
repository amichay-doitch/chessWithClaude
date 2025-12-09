"""
Chess Board Manager
Wrapper around python-chess for game state management.
"""

import chess


class ChessBoard:
    """Manages the chess game state."""

    def __init__(self, fen: str = None):
        """Initialize board, optionally from FEN string."""
        if fen:
            self.board = chess.Board(fen)
        else:
            self.board = chess.Board()

    def reset(self):
        """Reset to starting position."""
        self.board.reset()

    def make_move(self, move_str: str) -> bool:
        """
        Make a move from string (e.g., 'e2e4', 'e7e8q' for promotion).
        Returns True if move was legal and made, False otherwise.
        """
        try:
            move = chess.Move.from_uci(move_str)
            if move in self.board.legal_moves:
                self.board.push(move)
                return True
            return False
        except ValueError:
            return False

    def make_move_object(self, move: chess.Move) -> bool:
        """Make a move from a chess.Move object."""
        if move in self.board.legal_moves:
            self.board.push(move)
            return True
        return False

    def undo_move(self):
        """Undo the last move."""
        if self.board.move_stack:
            self.board.pop()

    def get_legal_moves(self) -> list:
        """Get all legal moves in current position."""
        return list(self.board.legal_moves)

    def is_game_over(self) -> bool:
        """Check if game is over."""
        return self.board.is_game_over()

    def get_result(self) -> str:
        """Get game result string."""
        if self.board.is_checkmate():
            if self.board.turn == chess.WHITE:
                return "Black wins by checkmate!"
            else:
                return "White wins by checkmate!"
        elif self.board.is_stalemate():
            return "Draw by stalemate"
        elif self.board.is_insufficient_material():
            return "Draw by insufficient material"
        elif self.board.is_fifty_moves():
            return "Draw by fifty-move rule"
        elif self.board.is_repetition():
            return "Draw by repetition"
        elif self.board.is_game_over():
            return "Game over"
        return "Game in progress"

    def is_check(self) -> bool:
        """Check if current side is in check."""
        return self.board.is_check()

    def get_turn(self) -> str:
        """Get current turn as string."""
        return "White" if self.board.turn == chess.WHITE else "Black"

    def get_fen(self) -> str:
        """Get FEN string of current position."""
        return self.board.fen()

    def display(self) -> str:
        """Get string representation of board."""
        return str(self.board)

    def display_flipped(self) -> str:
        """Get string representation from black's perspective."""
        return self.board.unicode(invert_color=True, borders=True)

    def display_unicode(self, flip: bool = False) -> str:
        """Get nice unicode representation."""
        return self.board.unicode(borders=True, invert_color=flip)


if __name__ == "__main__":
    # Quick test
    board = ChessBoard()
    print("Starting position:")
    print(board.display_unicode())
    print(f"\nTurn: {board.get_turn()}")
    print(f"Legal moves: {len(board.get_legal_moves())}")
