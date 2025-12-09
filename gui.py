"""
Chess GUI - Graphical interface to play against the engine
"""

import pygame
import chess
import sys
import threading
from board import ChessBoard
from engine import ChessEngine, SearchResult

# Initialize pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
SELECTED = (246, 246, 105)
LAST_MOVE = (205, 210, 106)
CHECK_COLOR = (255, 80, 80)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 149, 237)
TEXT_COLOR = (50, 50, 50)

# Board settings
SQUARE_SIZE = 80
BOARD_SIZE = SQUARE_SIZE * 8
PANEL_WIDTH = 250
WINDOW_WIDTH = BOARD_SIZE + PANEL_WIDTH
WINDOW_HEIGHT = BOARD_SIZE

# Fonts
pygame.font.init()
FONT = pygame.font.SysFont('Arial', 20)
FONT_SMALL = pygame.font.SysFont('Arial', 16)
FONT_LARGE = pygame.font.SysFont('Arial', 28, bold=True)

# Unicode chess pieces
PIECE_UNICODE = {
    'P': '\u2659', 'N': '\u2658', 'B': '\u2657', 'R': '\u2656', 'Q': '\u2655', 'K': '\u2654',
    'p': '\u265F', 'n': '\u265E', 'b': '\u265D', 'r': '\u265C', 'q': '\u265B', 'k': '\u265A',
}

class Button:
    def __init__(self, x, y, width, height, text, callback):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.callback = callback
        self.hovered = False

    def draw(self, screen):
        color = BUTTON_HOVER if self.hovered else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=5)

        text_surface = FONT.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.callback()
                return True
        return False


class ChessGUI:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chess Engine - chessWithClaude")

        self.board = ChessBoard()
        self.engine = ChessEngine(max_depth=10, time_limit=1)

        self.selected_square = None
        self.legal_moves_for_selected = []
        self.last_move = None
        self.player_is_white = True
        self.flipped = False 

        self.engine_thinking = False
        self.engine_done = False
        self.engine_result = None
        self.status_message = "Your turn"

        # Create piece font (larger for rendering)
        self.piece_font = pygame.font.SysFont('Segoe UI Symbol', 64)

        # Buttons
        self.buttons = [
            Button(BOARD_SIZE + 20, 400, 100, 40, "New Game", self.new_game),
            Button(BOARD_SIZE + 130, 400, 100, 40, "Flip Board", self.flip_board),
            Button(BOARD_SIZE + 20, 450, 100, 40, "Undo", self.undo_move),
            Button(BOARD_SIZE + 130, 450, 100, 40, "Hint", self.get_hint),
        ]

        # Depth buttons
        self.depth_buttons = []
        for i, d in enumerate([3, 5, 7]):
            btn = Button(BOARD_SIZE + 20 + i * 75, 520, 65, 35, f"Depth {d}", lambda depth=d: self.set_depth(depth))
            self.depth_buttons.append(btn)

    def set_depth(self, depth):
        self.engine.max_depth = depth
        self.status_message = f"Engine depth set to {depth}"

    def new_game(self):
        self.board.reset()
        self.selected_square = None
        self.legal_moves_for_selected = []
        self.last_move = None
        self.engine_thinking = False
        self.engine_result = None
        self.status_message = "New game! Your turn"

    def flip_board(self):
        self.flipped = not self.flipped

    def undo_move(self):
        if len(self.board.board.move_stack) >= 2:
            self.board.undo_move()
            self.board.undo_move()
            self.last_move = self.board.board.peek() if self.board.board.move_stack else None
            self.status_message = "Undid last moves"
        elif len(self.board.board.move_stack) == 1:
            self.board.undo_move()
            self.last_move = None
            self.status_message = "Undid last move"
        self.selected_square = None
        self.legal_moves_for_selected = []

    def get_hint(self):
        if not self.engine_thinking and not self.board.is_game_over():
            self.status_message = "Calculating hint..."
            threading.Thread(target=self._calculate_hint, daemon=True).start()

    def _calculate_hint(self):
        result = self.engine.search(self.board.board)
        if result:
            self.status_message = f"Hint: {result.best_move}"

    def get_square_from_pos(self, pos):
        x, y = pos
        if x >= BOARD_SIZE:
            return None

        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE

        if self.flipped:
            col = 7 - col
            row = 7 - row
        else:
            row = 7 - row

        return chess.square(col, row)

    def get_pos_from_square(self, square):
        col = chess.square_file(square)
        row = chess.square_rank(square)

        if self.flipped:
            col = 7 - col
            row = 7 - row
        else:
            row = 7 - row

        return col * SQUARE_SIZE, row * SQUARE_SIZE

    def draw_board(self):
        # Draw squares
        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE

                # Determine actual square
                if self.flipped:
                    actual_col = 7 - col
                    actual_row = 7 - row
                else:
                    actual_col = col
                    actual_row = 7 - row

                square = chess.square(actual_col, actual_row)

                # Base color
                if (row + col) % 2 == 0:
                    color = LIGHT_SQUARE
                else:
                    color = DARK_SQUARE

                # Highlight last move
                if self.last_move:
                    if square == self.last_move.from_square or square == self.last_move.to_square:
                        color = LAST_MOVE

                # Highlight selected square
                if square == self.selected_square:
                    color = SELECTED

                # Highlight legal moves
                for move in self.legal_moves_for_selected:
                    if move.to_square == square:
                        color = HIGHLIGHT

                # Highlight king in check
                if self.board.is_check():
                    king_square = self.board.board.king(self.board.board.turn)
                    if square == king_square:
                        color = CHECK_COLOR

                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

                # Draw piece
                piece = self.board.board.piece_at(square)
                if piece:
                    piece_char = piece.symbol()
                    piece_unicode = PIECE_UNICODE[piece_char]

                    # Render piece
                    if piece.color == chess.WHITE:
                        text_surface = self.piece_font.render(piece_unicode, True, WHITE)
                        # Add black outline for white pieces
                        outline_surface = self.piece_font.render(piece_unicode, True, BLACK)
                        text_rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        # Draw outline
                        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                            self.screen.blit(outline_surface, (text_rect.x + dx, text_rect.y + dy))
                        self.screen.blit(text_surface, text_rect)
                    else:
                        text_surface = self.piece_font.render(piece_unicode, True, BLACK)
                        text_rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        self.screen.blit(text_surface, text_rect)

        # Draw coordinates
        for i in range(8):
            # Files (a-h)
            file_label = chr(ord('a') + (i if not self.flipped else 7 - i))
            text = FONT_SMALL.render(file_label, True, TEXT_COLOR)
            self.screen.blit(text, (i * SQUARE_SIZE + SQUARE_SIZE - 15, BOARD_SIZE - 18))

            # Ranks (1-8)
            rank_label = str((8 - i) if not self.flipped else (i + 1))
            text = FONT_SMALL.render(rank_label, True, TEXT_COLOR)
            self.screen.blit(text, (3, i * SQUARE_SIZE + 3))

    def draw_panel(self):
        # Panel background
        pygame.draw.rect(self.screen, (245, 245, 245), (BOARD_SIZE, 0, PANEL_WIDTH, WINDOW_HEIGHT))
        pygame.draw.line(self.screen, BLACK, (BOARD_SIZE, 0), (BOARD_SIZE, WINDOW_HEIGHT), 2)

        # Title
        title = FONT_LARGE.render("Chess Engine", True, TEXT_COLOR)
        self.screen.blit(title, (BOARD_SIZE + 20, 20))

        # Status
        status = FONT.render(self.status_message, True, TEXT_COLOR)
        self.screen.blit(status, (BOARD_SIZE + 20, 70))

        # Turn indicator
        turn_text = f"Turn: {self.board.get_turn()}"
        turn = FONT.render(turn_text, True, TEXT_COLOR)
        self.screen.blit(turn, (BOARD_SIZE + 20, 100))

        # Game state
        if self.board.is_game_over():
            result = FONT.render(self.board.get_result(), True, (200, 0, 0))
            self.screen.blit(result, (BOARD_SIZE + 20, 130))
        elif self.board.is_check():
            check = FONT.render("CHECK!", True, (200, 0, 0))
            self.screen.blit(check, (BOARD_SIZE + 20, 130))

        # Engine info
        info_y = 180
        self.screen.blit(FONT_SMALL.render(f"Engine Depth: {self.engine.max_depth}", True, TEXT_COLOR),
                        (BOARD_SIZE + 20, info_y))

        if self.engine_thinking:
            thinking = FONT.render("Engine thinking...", True, (0, 100, 200))
            self.screen.blit(thinking, (BOARD_SIZE + 20, info_y + 30))

        # Move history (last 10 moves)
        self.screen.blit(FONT.render("Recent moves:", True, TEXT_COLOR), (BOARD_SIZE + 20, 250))
        moves = list(self.board.board.move_stack)[-10:]
        for i, move in enumerate(moves):
            move_text = FONT_SMALL.render(f"{len(self.board.board.move_stack) - len(moves) + i + 1}. {move}", True, TEXT_COLOR)
            self.screen.blit(move_text, (BOARD_SIZE + 20, 280 + i * 20))

        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)

        # Depth label and buttons
        self.screen.blit(FONT_SMALL.render("Set Difficulty:", True, TEXT_COLOR), (BOARD_SIZE + 20, 495))
        for button in self.depth_buttons:
            button.draw(self.screen)

    def handle_click(self, pos):
        if self.engine_thinking or self.board.is_game_over():
            return

        # Check if it's player's turn
        is_player_turn = (self.board.board.turn == chess.WHITE) == self.player_is_white
        if not is_player_turn:
            return

        square = self.get_square_from_pos(pos)
        if square is None:
            return

        # If we have a selected piece, try to move
        if self.selected_square is not None:
            # Check if this is a legal move
            move = None
            for m in self.legal_moves_for_selected:
                if m.to_square == square:
                    move = m
                    break

            if move:
                # Handle pawn promotion
                if move.promotion:
                    # For simplicity, always promote to queen
                    # Could add a dialog later
                    pass

                self.board.make_move_object(move)
                self.last_move = move
                self.selected_square = None
                self.legal_moves_for_selected = []
                self.status_message = f"You played: {move}"

                # Check game over
                if self.board.is_game_over():
                    self.status_message = self.board.get_result()
                else:
                    # Engine's turn
                    self.engine_turn()
                return

            # Clicked on own piece - select it instead
            piece = self.board.board.piece_at(square)
            if piece and piece.color == self.board.board.turn:
                self.selected_square = square
                self.legal_moves_for_selected = [m for m in self.board.get_legal_moves() if m.from_square == square]
                return

            # Deselect
            self.selected_square = None
            self.legal_moves_for_selected = []
        else:
            # Select a piece
            piece = self.board.board.piece_at(square)
            if piece and piece.color == self.board.board.turn:
                self.selected_square = square
                self.legal_moves_for_selected = [m for m in self.board.get_legal_moves() if m.from_square == square]

    def engine_turn(self):
        if self.engine_thinking:
            return  # Already thinking, don't start again
        self.engine_thinking = True
        self.engine_done = False
        self.engine_result = None
        self.status_message = "Engine thinking..."
        threading.Thread(target=self._engine_move, daemon=True).start()

    def _engine_move(self):
        # Make a copy of the board for searching so GUI doesn't see intermediate states
        board_copy = self.board.board.copy()
        result = self.engine.search(board_copy)
        self.engine_result = result
        self.engine_done = True  # Signal that search is complete

    def process_engine_result(self):
        # Only process when engine is completely done
        if not self.engine_done:
            return
        if self.engine_result is None:
            return

        result = self.engine_result
        self.engine_result = None
        self.engine_thinking = False
        self.engine_done = False

        if result.best_move:
            self.board.make_move_object(result.best_move)
            self.last_move = result.best_move

            score_text = f"{result.score/100:+.2f}" if abs(result.score) < 90000 else "Mate"
            self.status_message = f"Engine: {result.best_move} ({score_text})"

            if self.board.is_game_over():
                self.status_message = self.board.get_result()

    def run(self):
        clock = pygame.time.Clock()
        running = True

        # If player is black, engine moves first
        if not self.player_is_white:
            self.flipped = True
            self.engine_turn()

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Handle button events
                for button in self.buttons + self.depth_buttons:
                    button.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:  # Left click
                        self.handle_click(event.pos)

                if event.type == pygame.MOUSEMOTION:
                    for button in self.buttons + self.depth_buttons:
                        button.hovered = button.rect.collidepoint(event.pos)

            # Process engine result
            self.process_engine_result()

            # Draw
            self.screen.fill(WHITE)
            self.draw_board()
            self.draw_panel()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


def main():
    gui = ChessGUI()
    gui.run()


if __name__ == "__main__":
    main()
