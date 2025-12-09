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

# Colors - Polished chess.com style
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)   # Warm cream
DARK_SQUARE = (181, 136, 99)     # Warm brown
HIGHLIGHT = (130, 151, 105)      # Soft green for legal moves
SELECTED = (246, 246, 105)       # Bright yellow for selected
LAST_MOVE = (170, 162, 58)       # Golden yellow for last move (both squares)
CHECK_COLOR = (231, 76, 60)      # Bright red for check
BUTTON_COLOR = (52, 73, 94)      # Dark blue-gray
BUTTON_HOVER = (71, 101, 130)    # Lighter blue on hover
TEXT_COLOR = (50, 50, 50)
PANEL_BG = (38, 38, 38)          # Darker panel background
PANEL_TEXT = (230, 230, 230)     # Light text on dark panel
MOVE_DOT = (80, 80, 80, 180)     # Semi-transparent dots for legal moves
CAPTURE_RING = (80, 80, 80, 200) # Semi-transparent ring for captures

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
        self.time_limit = 1  # 1 second limit is the default

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
        time_options = [("No Limit", None), ("1 sec", 1), ("5 sec", 5), ("10 sec", 10)]
        for i, (label, time_val) in enumerate(time_options):
            x = center_x - 270 + i * 100
            btn = Button(x, 500, 95, 45, label, lambda t=time_val: self.set_time(t))
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
        self.move_scroll_offset = 0  # For scrolling through move history
        self.hint_thinking = False  # Track hint calculation

        # Create piece font (larger for rendering) - try multiple fonts
        piece_font_names = ['Segoe UI Symbol', 'Arial Unicode MS', 'DejaVu Sans', 'FreeSans']
        self.piece_font = None
        for font_name in piece_font_names:
            try:
                self.piece_font = pygame.font.SysFont(font_name, 70)
                break
            except:
                continue
        if self.piece_font is None:
            self.piece_font = pygame.font.SysFont(None, 70)

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
            self.status_message = "💡 Calculating hint..."
            self.hint_thinking = True
            threading.Thread(target=self._calculate_hint, daemon=True).start()

    def _calculate_hint(self):
        try:
            board_copy = self.board.board.copy()
            # Use depth 3 with 2 second time limit for quick hints
            from engine import ChessEngine
            hint_engine = ChessEngine(max_depth=3, time_limit=2.0)
            result = hint_engine.search(board_copy)

            if result and result.best_move:
                # Convert to more readable format
                from_sq = chess.square_name(result.best_move.from_square)
                to_sq = chess.square_name(result.best_move.to_square)
                piece = board_copy.piece_at(result.best_move.from_square)
                piece_name = piece.symbol().upper() if piece else ""
                self.status_message = f"💡 Hint: {piece_name}{from_sq}→{to_sq}"
            else:
                self.status_message = "No hint available"
        except Exception as e:
            self.status_message = f"Hint error: {str(e)[:40]}"
        finally:
            self.hint_thinking = False

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

                    # Render piece with clean, sharp appearance
                    if piece.color == chess.WHITE:
                        # White pieces: bright white with strong dark outline
                        text_surface = self.piece_font.render(piece_unicode, True, (255, 255, 255))
                        outline_surface = self.piece_font.render(piece_unicode, True, (30, 30, 30))
                        text_rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        # Draw thick outline for clarity
                        for dx, dy in [(-2, -2), (-2, 2), (2, -2), (2, 2), (-2, 0), (2, 0), (0, -2), (0, 2),
                                      (-1, -1), (-1, 1), (1, -1), (1, 1), (-1, 0), (1, 0), (0, -1), (0, 1)]:
                            self.screen.blit(outline_surface, (text_rect.x + dx, text_rect.y + dy))
                        self.screen.blit(text_surface, text_rect)
                    else:
                        # Black pieces: solid black, no blur
                        text_surface = self.piece_font.render(piece_unicode, True, (0, 0, 0))
                        text_rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        self.screen.blit(text_surface, text_rect)

        # Draw legal move indicators (dots and rings) on top of pieces
        for move in self.legal_moves_for_selected:
            dest_square = move.to_square
            pos = self.get_pos_from_square(dest_square)
            center_x = pos[0] + SQUARE_SIZE // 2
            center_y = pos[1] + SQUARE_SIZE // 2

            # Check if destination has a piece (capture)
            if self.board.board.piece_at(dest_square):
                # Draw ring for capture
                pygame.draw.circle(self.screen, (60, 60, 60), (center_x, center_y), SQUARE_SIZE // 2 - 4, 5)
            else:
                # Draw dot for empty square
                pygame.draw.circle(self.screen, (80, 80, 80), (center_x, center_y), SQUARE_SIZE // 6)

        # Draw coordinates with better contrast
        coord_font = pygame.font.SysFont('Arial', 14, bold=True)
        for i in range(8):
            # Files (a-h) - flip when viewing from black's perspective
            if self.flipped:
                file_label = chr(ord('h') - i)  # h to a (right to left)
            else:
                file_label = chr(ord('a') + i)  # a to h (left to right)

            # Choose color based on square color (bottom right corner)
            square_is_light = (7 + i) % 2 == 0
            coord_color = DARK_SQUARE if square_is_light else LIGHT_SQUARE
            text = coord_font.render(file_label, True, coord_color)
            self.screen.blit(text, (i * SQUARE_SIZE + SQUARE_SIZE - 13, BOARD_SIZE - 16))

            # Ranks (1-8) - flip vertically when board is flipped
            if self.flipped:
                rank_label = str(i + 1)  # 1 at top, 8 at bottom when flipped
            else:
                rank_label = str(8 - i)  # 8 at top, 1 at bottom normally

            # Choose color based on square color (left column)
            square_is_light = i % 2 == 0
            coord_color = DARK_SQUARE if square_is_light else LIGHT_SQUARE
            text = coord_font.render(rank_label, True, coord_color)
            self.screen.blit(text, (5, i * SQUARE_SIZE + 5))

    def draw_panel(self):
        # Panel background - dark modern style
        pygame.draw.rect(self.screen, PANEL_BG, (BOARD_SIZE, 0, PANEL_WIDTH, WINDOW_HEIGHT))

        # Subtle separator line
        pygame.draw.line(self.screen, (60, 60, 60), (BOARD_SIZE, 0), (BOARD_SIZE, WINDOW_HEIGHT), 1)

        # Title - more compact
        title = FONT_LARGE.render("Chess", True, PANEL_TEXT)
        self.screen.blit(title, (BOARD_SIZE + 20, 15))

        # Turn indicator - compact, no redundant "Your turn"
        turn_color = (230, 230, 230) if self.board.board.turn == chess.WHITE else (180, 180, 180)
        turn_text = f"{'White' if self.board.board.turn == chess.WHITE else 'Black'} to move"
        turn = FONT.render(turn_text, True, turn_color)
        self.screen.blit(turn, (BOARD_SIZE + 20, 55))

        # Game state alerts
        if self.board.is_game_over():
            result = FONT_LARGE.render(self.board.get_result(), True, CHECK_COLOR)
            self.screen.blit(result, (BOARD_SIZE + 20, 85))
        elif self.board.is_check():
            check = FONT_LARGE.render("CHECK!", True, CHECK_COLOR)
            self.screen.blit(check, (BOARD_SIZE + 20, 85))

        # Engine status - compact
        info_y = 120
        depth_text = FONT_SMALL.render(f"Engine: Depth {self.engine.max_depth}", True, (180, 180, 180))
        self.screen.blit(depth_text, (BOARD_SIZE + 20, info_y))

        if self.engine_thinking:
            thinking = FONT_SMALL.render("● Thinking...", True, (100, 180, 255))
            self.screen.blit(thinking, (BOARD_SIZE + 20, info_y + 20))
        elif self.hint_thinking:
            hint_status = FONT_SMALL.render("💡 Calculating hint...", True, (255, 200, 50))
            self.screen.blit(hint_status, (BOARD_SIZE + 20, info_y + 20))

        # Move history - more compact with proper chess notation
        history_y = 170
        pygame.draw.line(self.screen, (50, 50, 50),
                        (BOARD_SIZE + 15, history_y), (BOARD_SIZE + PANEL_WIDTH - 15, history_y), 1)

        self.screen.blit(FONT_SMALL.render("Move History", True, (140, 140, 140)),
                        (BOARD_SIZE + 20, history_y + 8))

        # Format moves in chess notation (1. e4 e5, 2. d4 d5, etc.)
        all_moves = list(self.board.board.move_stack)
        move_pairs = []
        for i in range(0, len(all_moves), 2):
            move_num = (i // 2) + 1
            white_move = str(all_moves[i])
            black_move = str(all_moves[i + 1]) if i + 1 < len(all_moves) else ""
            if black_move:
                move_pairs.append(f"{move_num}. {white_move} {black_move}")
            else:
                move_pairs.append(f"{move_num}. {white_move}")

        # Show up to 9 lines with scrolling
        max_visible = 9
        total_moves = len(move_pairs)

        # When offset is 0, show the most recent moves
        # When offset increases, show older moves
        if total_moves <= max_visible:
            # Show all moves
            visible_moves = move_pairs
            start_idx = 0
        else:
            # Calculate which moves to show based on scroll offset
            end_idx = total_moves - self.move_scroll_offset
            start_idx = max(0, end_idx - max_visible)
            visible_moves = move_pairs[start_idx:end_idx]

        for i, move_text in enumerate(visible_moves):
            text = FONT_SMALL.render(move_text, True, (190, 190, 190))
            self.screen.blit(text, (BOARD_SIZE + 22, history_y + 35 + i * 18))

        # Show scroll indicators if needed
        if self.move_scroll_offset > 0:
            # Can scroll down to see newer moves
            down_arrow = FONT_SMALL.render("▼", True, (100, 180, 255))
            self.screen.blit(down_arrow, (BOARD_SIZE + 200, history_y + 35 + 8 * 18))
        if total_moves > max_visible and start_idx > 0:
            # Can scroll up to see older moves
            up_arrow = FONT_SMALL.render("▲", True, (100, 180, 255))
            self.screen.blit(up_arrow, (BOARD_SIZE + 200, history_y + 35))

        # Action buttons - more compact
        button_y = 385
        pygame.draw.line(self.screen, (50, 50, 50),
                        (BOARD_SIZE + 15, button_y - 5), (BOARD_SIZE + PANEL_WIDTH - 15, button_y - 5), 1)

        for button in self.buttons:
            button.draw(self.screen)

        # Difficulty section - compact
        pygame.draw.line(self.screen, (50, 50, 50),
                        (BOARD_SIZE + 15, 490), (BOARD_SIZE + PANEL_WIDTH - 15, 490), 1)
        self.screen.blit(FONT_SMALL.render("Difficulty", True, (140, 140, 140)),
                        (BOARD_SIZE + 20, 498))
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
                    elif event.button == 4:  # Mouse wheel up
                        # Scroll up in move history
                        all_moves = list(self.board.board.move_stack)
                        move_pairs_count = (len(all_moves) + 1) // 2
                        if move_pairs_count > 9:
                            self.move_scroll_offset = min(self.move_scroll_offset + 1, move_pairs_count - 9)
                    elif event.button == 5:  # Mouse wheel down
                        # Scroll down in move history
                        self.move_scroll_offset = max(0, self.move_scroll_offset - 1)

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
