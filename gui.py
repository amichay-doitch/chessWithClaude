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

# Colors - Chess.com style
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (238, 238, 210)  # Chess.com light squares
DARK_SQUARE = (118, 150, 86)     # Chess.com dark squares
HIGHLIGHT = (186, 202, 68)       # Yellow-green for legal moves
SELECTED = (246, 246, 130)       # Bright yellow for selected
LAST_MOVE = (205, 210, 106)      # Muted yellow for last move
CHECK_COLOR = (235, 97, 80)      # Red for check
BUTTON_COLOR = (130, 151, 105)   # Green matching dark squares
BUTTON_HOVER = (150, 171, 125)   # Lighter green on hover
TEXT_COLOR = (50, 50, 50)
PANEL_BG = (49, 46, 43)          # Dark panel background
PANEL_TEXT = (220, 220, 220)     # Light text on dark panel

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


class SetupScreen:
    """Game setup screen to choose color, depth, and time limit"""
    def __init__(self, screen):
        self.screen = screen
        self.selected_color = chess.WHITE  # Default to white
        self.selected_depth = 5  # Default depth
        self.time_limit = None  # No time limit by default

        # Setup buttons
        center_x = WINDOW_WIDTH // 2

        # Color selection buttons
        self.white_button = Button(center_x - 220, 200, 180, 50, "Play as White", lambda: self.set_color(chess.WHITE))
        self.black_button = Button(center_x + 40, 200, 180, 50, "Play as Black", lambda: self.set_color(chess.BLACK))

        # Depth buttons
        self.depth_buttons = []
        depths = [3, 4, 5, 6, 7, 8]
        for i, depth in enumerate(depths):
            x = center_x - 270 + (i % 3) * 90
            y = 320 if i < 3 else 380
            btn = Button(x, y, 80, 45, f"Depth {depth}", lambda d=depth: self.set_depth(d))
            self.depth_buttons.append((btn, depth))

        # Time limit buttons
        self.time_buttons = []
        time_options = [("No Limit", None), ("1 sec", 1), ("5 sec", 5), ("10 sec", 10), ("30 sec", 30)]
        for i, (label, time_val) in enumerate(time_options):
            x = center_x - 270 + i * 135
            btn = Button(x, 500, 125, 45, label, lambda t=time_val: self.set_time(t))
            self.time_buttons.append((btn, time_val))

        # Start button
        self.start_button = Button(center_x - 100, 580, 200, 60, "START GAME", None)

    def set_color(self, color):
        self.selected_color = color

    def set_depth(self, depth):
        self.selected_depth = depth

    def set_time(self, time_limit):
        self.time_limit = time_limit

    def draw(self):
        self.screen.fill(PANEL_BG)

        # Title
        title = pygame.font.SysFont('Arial', 48, bold=True).render("Chess Setup", True, PANEL_TEXT)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)

        # Color selection label
        color_label = FONT_LARGE.render("Choose Your Color:", True, PANEL_TEXT)
        self.screen.blit(color_label, (WINDOW_WIDTH // 2 - 120, 150))

        # Draw color buttons with selection indicator
        for btn, color in [(self.white_button, chess.WHITE), (self.black_button, chess.BLACK)]:
            if self.selected_color == color:
                # Draw selection border
                pygame.draw.rect(self.screen, HIGHLIGHT,
                               (btn.rect.x - 3, btn.rect.y - 3, btn.rect.width + 6, btn.rect.height + 6),
                               border_radius=7)
            btn.draw(self.screen)

        # Depth selection label
        depth_label = FONT_LARGE.render("Choose Difficulty:", True, PANEL_TEXT)
        self.screen.blit(depth_label, (WINDOW_WIDTH // 2 - 120, 270))

        # Draw depth buttons with selection indicator
        for btn, depth in self.depth_buttons:
            if self.selected_depth == depth:
                pygame.draw.rect(self.screen, HIGHLIGHT,
                               (btn.rect.x - 3, btn.rect.y - 3, btn.rect.width + 6, btn.rect.height + 6),
                               border_radius=7)
            btn.draw(self.screen)

        # Time limit label
        time_label = FONT_LARGE.render("Time per Move:", True, PANEL_TEXT)
        self.screen.blit(time_label, (WINDOW_WIDTH // 2 - 120, 450))

        # Draw time buttons with selection indicator
        for btn, time_val in self.time_buttons:
            if self.time_limit == time_val:
                pygame.draw.rect(self.screen, HIGHLIGHT,
                               (btn.rect.x - 3, btn.rect.y - 3, btn.rect.width + 6, btn.rect.height + 6),
                               border_radius=7)
            btn.draw(self.screen)

        # Draw start button
        self.start_button.draw(self.screen)

    def handle_event(self, event):
        # Handle color buttons
        for btn in [self.white_button, self.black_button]:
            btn.handle_event(event)

        # Handle depth buttons
        for btn, _ in self.depth_buttons:
            btn.handle_event(event)

        # Handle time buttons
        for btn, _ in self.time_buttons:
            btn.handle_event(event)

        # Handle start button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button.rect.collidepoint(event.pos):
                return True  # Signal to start game

        # Handle hover for all buttons
        if event.type == pygame.MOUSEMOTION:
            all_buttons = [self.white_button, self.black_button, self.start_button]
            all_buttons.extend([btn for btn, _ in self.depth_buttons])
            all_buttons.extend([btn for btn, _ in self.time_buttons])
            for btn in all_buttons:
                btn.hovered = btn.rect.collidepoint(event.pos)

        return False


class ChessGUI:
    def __init__(self, player_color=chess.WHITE, engine_depth=5, time_limit=None):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Chess Engine - chessWithClaude")

        self.board = ChessBoard()
        self.engine = ChessEngine(max_depth=engine_depth, time_limit=time_limit)

        self.selected_square = None
        self.legal_moves_for_selected = []
        self.last_move = None
        self.player_is_white = (player_color == chess.WHITE)
        self.flipped = not self.player_is_white  # Flip board if playing black

        self.engine_thinking = False
        self.engine_done = False
        self.engine_result = None
        self.status_message = "Your turn"
        self.return_to_setup = False  # Flag to return to setup screen

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
        # Signal to return to setup screen
        self.return_to_setup = True

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
            # When flipped, reverse both rows and columns (180 degree rotation)
            col = 7 - col
            row = row  # Keep row as-is (0 at top = rank 8 for black)
        else:
            row = 7 - row  # Normal orientation (0 at top = rank 8)

        return chess.square(col, row)

    def get_pos_from_square(self, square):
        col = chess.square_file(square)
        row = chess.square_rank(square)

        if self.flipped:
            # When flipped, reverse both rows and columns (180 degree rotation)
            col = 7 - col
            row = row  # Keep row as-is for flipped view
        else:
            row = 7 - row  # Normal orientation

        return col * SQUARE_SIZE, row * SQUARE_SIZE

    def draw_board(self):
        # Draw squares
        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE

                # Determine actual square
                if self.flipped:
                    # When flipped, reverse both rows and columns (180 degree rotation)
                    actual_col = 7 - col
                    actual_row = row  # Keep row as-is for flipped view
                else:
                    actual_col = col
                    actual_row = 7 - row  # Normal orientation

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
            # Files (a-h) - flip when viewing from black's perspective
            if self.flipped:
                file_label = chr(ord('h') - i)  # h to a (right to left)
            else:
                file_label = chr(ord('a') + i)  # a to h (left to right)
            text = FONT_SMALL.render(file_label, True, TEXT_COLOR)
            self.screen.blit(text, (i * SQUARE_SIZE + SQUARE_SIZE - 15, BOARD_SIZE - 18))

            # Ranks (1-8) - flip vertically when board is flipped
            if self.flipped:
                rank_label = str(i + 1)  # 1 at top, 8 at bottom when flipped
            else:
                rank_label = str(8 - i)  # 8 at top, 1 at bottom normally
            text = FONT_SMALL.render(rank_label, True, TEXT_COLOR)
            self.screen.blit(text, (3, i * SQUARE_SIZE + 3))

    def draw_panel(self):
        # Panel background - dark chess.com style
        pygame.draw.rect(self.screen, PANEL_BG, (BOARD_SIZE, 0, PANEL_WIDTH, WINDOW_HEIGHT))
        pygame.draw.line(self.screen, DARK_SQUARE, (BOARD_SIZE, 0), (BOARD_SIZE, WINDOW_HEIGHT), 2)

        # Title
        title = FONT_LARGE.render("Chess Engine", True, PANEL_TEXT)
        self.screen.blit(title, (BOARD_SIZE + 20, 20))

        # Status
        status = FONT.render(self.status_message, True, PANEL_TEXT)
        self.screen.blit(status, (BOARD_SIZE + 20, 70))

        # Turn indicator
        turn_text = f"Turn: {self.board.get_turn()}"
        turn = FONT.render(turn_text, True, PANEL_TEXT)
        self.screen.blit(turn, (BOARD_SIZE + 20, 100))

        # Game state
        if self.board.is_game_over():
            result = FONT.render(self.board.get_result(), True, CHECK_COLOR)
            self.screen.blit(result, (BOARD_SIZE + 20, 130))
        elif self.board.is_check():
            check = FONT.render("CHECK!", True, CHECK_COLOR)
            self.screen.blit(check, (BOARD_SIZE + 20, 130))

        # Engine info
        info_y = 180
        self.screen.blit(FONT_SMALL.render(f"Engine Depth: {self.engine.max_depth}", True, PANEL_TEXT),
                        (BOARD_SIZE + 20, info_y))

        if self.engine_thinking:
            thinking = FONT.render("Engine thinking...", True, (100, 180, 255))
            self.screen.blit(thinking, (BOARD_SIZE + 20, info_y + 30))

        # Move history (last 10 moves)
        self.screen.blit(FONT.render("Recent moves:", True, PANEL_TEXT), (BOARD_SIZE + 20, 250))
        moves = list(self.board.board.move_stack)[-10:]
        for i, move in enumerate(moves):
            move_text = FONT_SMALL.render(f"{len(self.board.board.move_stack) - len(moves) + i + 1}. {move}", True, PANEL_TEXT)
            self.screen.blit(move_text, (BOARD_SIZE + 20, 280 + i * 20))

        # Draw buttons
        for button in self.buttons:
            button.draw(self.screen)

        # Depth label and buttons
        self.screen.blit(FONT_SMALL.render("Set Difficulty:", True, PANEL_TEXT), (BOARD_SIZE + 20, 495))
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
            self.engine_turn()

        while running:
            # Check if we should return to setup
            if self.return_to_setup:
                return  # Exit run loop to go back to setup

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
    # Initialize pygame and create window
    screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
    pygame.display.set_caption("Chess Engine - chessWithClaude")
    clock = pygame.time.Clock()

    running = True

    while running:
        # Show setup screen
        setup = SetupScreen(screen)
        game_started = False

        while running and not game_started:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                    break

                if setup.handle_event(event):
                    game_started = True

            if not running:
                break

            setup.draw()
            pygame.display.flip()
            clock.tick(60)

        if game_started:
            # Start game with selected settings
            gui = ChessGUI(
                player_color=setup.selected_color,
                engine_depth=setup.selected_depth,
                time_limit=setup.time_limit
            )
            gui.run()

            # Check if user wants to return to setup or quit
            if not gui.return_to_setup:
                running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
