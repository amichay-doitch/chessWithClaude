"""
Chess GUI - Graphical interface to play against the engine
"""

import pygame
import chess
import sys
import threading
import importlib
from board import ChessBoard
from engine import ChessEngine, SearchResult
from gui_utils import (
    Button, Dropdown, ChessBoardRenderer,
    find_all_engines, format_engine_name,
    WHITE, BLACK, LIGHT_SQUARE, DARK_SQUARE, HIGHLIGHT, SELECTED,
    LAST_MOVE, CHECK_COLOR, BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR,
    PANEL_BG, PANEL_TEXT, MOVE_DOT, CAPTURE_RING,
    DROPDOWN_BG, DROPDOWN_HOVER, DROPDOWN_SELECTED, PIECE_UNICODE
)

# Initialize pygame
pygame.init()

# Board settings
SQUARE_SIZE = 80
BOARD_SIZE = SQUARE_SIZE * 8
PANEL_WIDTH = 250
WINDOW_WIDTH = BOARD_SIZE + PANEL_WIDTH
WINDOW_HEIGHT = 750  # Increased to fit all setup options

# Fonts
pygame.font.init()
FONT = pygame.font.SysFont('Arial', 20)
FONT_SMALL = pygame.font.SysFont('Arial', 16)
FONT_TINY = pygame.font.SysFont('Arial', 14)
FONT_LARGE = pygame.font.SysFont('Arial', 28, bold=True)


class SetupScreen:
    """Game setup screen to choose color, depth, and time limit"""
    def __init__(self, screen):
        self.screen = screen
        self.selected_color = chess.WHITE  # Default to white
        self.selected_depth = 6  # Default depth
        self.time_limit = 3  # 3 second limit is the default

        # Find all available engines
        all_engines = find_all_engines()

        # Setup buttons
        center_x = WINDOW_WIDTH // 2

        # Color selection buttons
        self.white_button = Button(center_x - 220, 180, 180, 50, "Play as White", lambda: self.set_color(chess.WHITE))
        self.black_button = Button(center_x + 40, 180, 180, 50, "Play as Black", lambda: self.set_color(chess.BLACK))

        # Engine dropdown - find index of engine_v5_optimized as default
        default_engine_idx = 0
        for i, (module_name, _, _) in enumerate(all_engines):
            if "engine_v5_optimized" in module_name:
                default_engine_idx = i
                break

        self.engine_dropdown = Dropdown(center_x - 200, 280, 400, all_engines, default_engine_idx)

        # Depth buttons (with No Limit option)
        self.depth_buttons = []
        depth_options = [("No Limit", None), ("D3", 3), ("D4", 4), ("D5", 5), ("D6", 6), ("D7", 7), ("D8", 8)]
        for i, (label, depth) in enumerate(depth_options):
            x = center_x - 240 + i * 70
            y = 390
            btn = Button(x, y, 65, 45, label, lambda d=depth: self.set_depth(d))
            self.depth_buttons.append((btn, depth))

        # Time limit dropdown - create time options
        time_options = [
            (None, "No Limit", "none"),
            (0.5, "0.5s", "time"),
            (1, "1s", "time"),
            (2, "2s", "time"),
            (3, "3s", "time"),
            (5, "5s", "time"),
            (10, "10s", "time"),
            (30, "30s", "time"),
            (60, "60s", "time"),
        ]
        # Format for Dropdown: (value, display, category)
        formatted_times = [(val, display, cat) for val, display, cat in time_options]
        default_time_idx = 4  # Default to 3s
        self.time_dropdown = Dropdown(center_x - 100, 490, 200, formatted_times, default_time_idx)

        # Start button
        self.start_button = Button(center_x - 100, 690, 200, 50, "START GAME", None)

    def set_color(self, color):
        self.selected_color = color

    def set_depth(self, depth):
        self.selected_depth = depth

    def draw(self):
        self.screen.fill(PANEL_BG)

        # Title
        title = pygame.font.SysFont('Arial', 48, bold=True).render("Chess Setup", True, PANEL_TEXT)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)

        # Info box
        info_text = FONT_SMALL.render("⚡ V5 Optimized = 3.8x faster!", True, (100, 255, 100))
        info_rect = info_text.get_rect(center=(WINDOW_WIDTH // 2, 110))
        self.screen.blit(info_text, info_rect)

        # Color selection label
        color_label = FONT_LARGE.render("Choose Your Color:", True, PANEL_TEXT)
        self.screen.blit(color_label, (WINDOW_WIDTH // 2 - 120, 130))

        # Draw color buttons with selection indicator
        for btn, color in [(self.white_button, chess.WHITE), (self.black_button, chess.BLACK)]:
            if self.selected_color == color:
                pygame.draw.rect(self.screen, HIGHLIGHT,
                               (btn.rect.x - 3, btn.rect.y - 3, btn.rect.width + 6, btn.rect.height + 6),
                               border_radius=7)
            btn.draw(self.screen)

        # Engine selection label
        engine_label = FONT_LARGE.render("Choose Engine:", True, PANEL_TEXT)
        self.screen.blit(engine_label, (WINDOW_WIDTH // 2 - 100, 240))

        # Depth selection label
        depth_label = FONT_LARGE.render("Choose Depth:", True, PANEL_TEXT)
        self.screen.blit(depth_label, (WINDOW_WIDTH // 2 - 90, 350))

        # Draw depth buttons with selection indicator
        for btn, depth in self.depth_buttons:
            if self.selected_depth == depth:
                pygame.draw.rect(self.screen, HIGHLIGHT,
                               (btn.rect.x - 3, btn.rect.y - 3, btn.rect.width + 6, btn.rect.height + 6),
                               border_radius=7)
            btn.draw(self.screen)

        # Time limit label
        time_label = FONT_LARGE.render("Time per Move:", True, PANEL_TEXT)
        self.screen.blit(time_label, (WINDOW_WIDTH // 2 - 100, 450))

        # Config summary
        summary_y = 560
        _, engine_display, source = self.engine_dropdown.items[self.engine_dropdown.selected_index]
        source_text = " (Engine Pool)" if source == "pool" else ""

        # Get time display from dropdown
        time_val, time_display, _ = self.time_dropdown.items[self.time_dropdown.selected_index]

        depth_text = f"Depth {self.selected_depth}" if self.selected_depth else "No depth limit"
        time_text = time_display

        summary_lines = [
            f"Ready: {engine_display}{source_text}",
            f"{depth_text} • {time_text}",
            f"Playing as {'White' if self.selected_color == chess.WHITE else 'Black'}"
        ]
        for i, line in enumerate(summary_lines):
            text = FONT_SMALL.render(line, True, (180, 180, 180))
            text_rect = text.get_rect(center=(WINDOW_WIDTH // 2, summary_y + i * 25))
            self.screen.blit(text, text_rect)

        # Draw start button
        self.start_button.draw(self.screen)

        # Help text
        help_text = FONT_TINY.render("📦 = Engine from engine_pool directory", True, (150, 150, 150))
        help_rect = help_text.get_rect(center=(WINDOW_WIDTH // 2, 650))
        self.screen.blit(help_text, help_rect)

        # IMPORTANT: Draw dropdowns LAST so they appear on top of everything
        self.engine_dropdown.draw(self.screen)
        self.time_dropdown.draw(self.screen)

    def handle_event(self, event):
        # Handle dropdowns first (they need priority and must be drawn on top)
        # Check if either dropdown handled the event
        if self.time_dropdown.handle_event(event):
            # Update time_limit when dropdown selection changes
            time_val, _, _ = self.time_dropdown.items[self.time_dropdown.selected_index]
            self.time_limit = time_val
            return False

        if self.engine_dropdown.handle_event(event):
            return False

        # Handle color buttons
        for btn in [self.white_button, self.black_button]:
            btn.handle_event(event)

        # Handle depth buttons
        for btn, _ in self.depth_buttons:
            btn.handle_event(event)

        # Handle start button
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.start_button.rect.collidepoint(event.pos):
                return True  # Signal to start game

        # Handle hover for all buttons
        if event.type == pygame.MOUSEMOTION:
            all_buttons = [self.white_button, self.black_button, self.start_button]
            all_buttons.extend([btn for btn, _ in self.depth_buttons])
            for btn in all_buttons:
                btn.hovered = btn.rect.collidepoint(event.pos)

        return False


class ChessGUI:
    def __init__(self, player_color=chess.WHITE, engine_depth=5, time_limit=None, engine_module="engine"):
        # Use board size for game window
        self.screen = pygame.display.set_mode((BOARD_SIZE + PANEL_WIDTH, BOARD_SIZE))
        pygame.display.set_caption("Chess Engine - chessWithClaude")

        self.board = ChessBoard()

        # Load engine dynamically
        try:
            engine_mod = importlib.import_module(engine_module)
            # Use depth 100 if None (essentially no limit)
            actual_depth = engine_depth if engine_depth is not None else 100
            self.engine = engine_mod.ChessEngine(max_depth=actual_depth, time_limit=time_limit)
            self.engine_name = engine_module
            self.engine_depth_display = engine_depth  # Store for display
        except Exception as e:
            print(f"Error loading engine {engine_module}: {e}")
            # Fallback to default engine
            from engine import ChessEngine
            actual_depth = engine_depth if engine_depth is not None else 100
            self.engine = ChessEngine(max_depth=actual_depth, time_limit=time_limit)
            self.engine_name = "engine"
            self.engine_depth_display = engine_depth

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
        self.hint_message = None  # Store hint message separately
        self.viewing_history = False  # True when viewing past positions
        self.current_move_index = None  # Index of move being viewed (None = current position)
        self.last_search_stats = None  # Store last search statistics for display

        # Create board renderer
        self.board_renderer = ChessBoardRenderer(SQUARE_SIZE)

        # Buttons
        self.buttons = [
            Button(BOARD_SIZE + 20, 400, 100, 40, "New Game", self.new_game),
            Button(BOARD_SIZE + 130, 400, 100, 40, "Flip Board", self.flip_board),
            Button(BOARD_SIZE + 20, 450, 100, 40, "Undo", self.undo_move),
            Button(BOARD_SIZE + 130, 450, 100, 40, "Hint", self.get_hint),
        ]

        # Scroll buttons for move history
        self.scroll_up_button = Button(BOARD_SIZE + 215, 178, 25, 25, "▲", self.scroll_history_up)
        self.scroll_down_button = Button(BOARD_SIZE + 215, 355, 25, 25, "▼", self.scroll_history_down)

        # Depth buttons
        self.depth_buttons = []
        for i, d in enumerate([3, 5, 7]):
            btn = Button(BOARD_SIZE + 20 + i * 75, 520, 65, 35, f"Depth {d}", lambda depth=d: self.set_depth(depth))
            self.depth_buttons.append(btn)

    def set_depth(self, depth):
        actual_depth = depth if depth is not None else 100
        self.engine.max_depth = actual_depth
        self.engine_depth_display = depth
        if depth:
            self.status_message = f"Engine depth set to {depth}"
        else:
            self.status_message = "Engine depth: No limit"

    def scroll_history_up(self):
        """Go back one move in history"""
        all_moves = list(self.board.board.move_stack)
        if len(all_moves) == 0:
            return

        if self.current_move_index is None:
            self.current_move_index = len(all_moves) - 1
            self.viewing_history = True
        elif self.current_move_index > 0:
            self.current_move_index -= 1

    def scroll_history_down(self):
        """Go forward one move in history"""
        all_moves = list(self.board.board.move_stack)
        if not self.viewing_history or self.current_move_index is None:
            return

        if self.current_move_index < len(all_moves) - 1:
            self.current_move_index += 1
        else:
            self.viewing_history = False
            self.current_move_index = None

    def new_game(self):
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
            self.hint_message = "Calculating hint..."
            self.hint_thinking = True
            threading.Thread(target=self._calculate_hint, daemon=True).start()

    def _calculate_hint(self):
        try:
            board_copy = self.board.board.copy()
            engine_mod = importlib.import_module(self.engine_name)
            hint_engine = engine_mod.ChessEngine(max_depth=3, time_limit=2.0)
            result = hint_engine.search(board_copy)

            if result and result.best_move:
                from_sq = chess.square_name(result.best_move.from_square)
                to_sq = chess.square_name(result.best_move.to_square)
                piece = board_copy.piece_at(result.best_move.from_square)
                piece_name = piece.symbol().upper() if piece else ""
                self.hint_message = f"Hint: {piece_name}{from_sq}->{to_sq}"
            else:
                self.hint_message = "No hint available"
        except Exception as e:
            self.hint_message = f"Hint error: {str(e)[:40]}"
        finally:
            self.hint_thinking = False

    def get_square_from_pos(self, pos):
        x, y = pos
        if x >= BOARD_SIZE:
            return None

        col = x // SQUARE_SIZE
        row = y // SQUARE_SIZE

        if self.flipped:
            col = 7 - col
            row = row
        else:
            row = 7 - row

        return chess.square(col, row)

    def get_pos_from_square(self, square):
        col = chess.square_file(square)
        row = chess.square_rank(square)

        if self.flipped:
            col = 7 - col
            row = row
        else:
            row = 7 - row

        return col * SQUARE_SIZE, row * SQUARE_SIZE

    def get_display_board(self):
        """Get the board position to display (current or historical)"""
        if self.viewing_history and self.current_move_index is not None:
            display_board = chess.Board()
            all_moves = list(self.board.board.move_stack)
            for i in range(self.current_move_index + 1):
                display_board.push(all_moves[i])
            return display_board
        else:
            return self.board.board

    def draw_board(self):
        display_board = self.get_display_board()

        # Use the board renderer to draw everything
        self.board_renderer.draw_board(
            screen=self.screen,
            board=display_board,
            x=0,
            y=0,
            flipped=self.flipped,
            last_move=self.last_move,
            selected_square=self.selected_square,
            legal_moves=self.legal_moves_for_selected,
            draw_coordinates=True
        )

    def draw_panel(self):
        # Panel background
        pygame.draw.rect(self.screen, PANEL_BG, (BOARD_SIZE, 0, PANEL_WIDTH, WINDOW_HEIGHT))
        pygame.draw.line(self.screen, (60, 60, 60), (BOARD_SIZE, 0), (BOARD_SIZE, WINDOW_HEIGHT), 1)

        # Title
        title = FONT_LARGE.render("Chess", True, PANEL_TEXT)
        self.screen.blit(title, (BOARD_SIZE + 20, 15))

        # Turn indicator
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

        # Engine status
        info_y = 120
        engine_display = format_engine_name(self.engine_name)
        depth_display = f"D{self.engine_depth_display}" if self.engine_depth_display else "No Depth Limit"
        depth_text = FONT_SMALL.render(f"{engine_display} {depth_display}", True, (180, 180, 180))
        self.screen.blit(depth_text, (BOARD_SIZE + 20, info_y))

        if self.engine_thinking:
            thinking = FONT_SMALL.render("● Thinking...", True, (100, 180, 255))
            self.screen.blit(thinking, (BOARD_SIZE + 20, info_y + 20))
        elif self.hint_thinking:
            hint_status = FONT_SMALL.render("Calculating hint...", True, (255, 200, 50))
            self.screen.blit(hint_status, (BOARD_SIZE + 20, info_y + 20))

        # Display search statistics
        if self.last_search_stats and not self.engine_thinking:
            stats = self.last_search_stats
            nps = int(stats.nodes_searched / stats.time_spent) if stats.time_spent > 0 else 0

            if nps >= 1000000:
                nps_text = f"{nps/1000000:.1f}M"
            elif nps >= 1000:
                nps_text = f"{nps/1000:.1f}K"
            else:
                nps_text = str(nps)

            stats_y = info_y + 20
            nodes_text = FONT_SMALL.render(f"Nodes: {stats.nodes_searched:,}", True, (150, 200, 150))
            self.screen.blit(nodes_text, (BOARD_SIZE + 20, stats_y))

            time_text = FONT_SMALL.render(f"Time: {stats.time_spent:.2f}s", True, (150, 200, 150))
            self.screen.blit(time_text, (BOARD_SIZE + 20, stats_y + 18))

            nps_color = (100, 255, 100) if nps >= 5000 else (150, 200, 150)
            nps_display = FONT_SMALL.render(f"Speed: {nps_text} NPS", True, nps_color)
            self.screen.blit(nps_display, (BOARD_SIZE + 20, stats_y + 36))

        # Hint message
        hint_y = info_y + 75 if self.last_search_stats else info_y + 40
        if self.hint_message and not self.hint_thinking:
            hint_text = FONT_SMALL.render(self.hint_message, True, (100, 220, 100))
            self.screen.blit(hint_text, (BOARD_SIZE + 20, hint_y))

        # History viewing indicator
        history_y = info_y + 100 if self.last_search_stats else info_y + 65
        if self.viewing_history:
            history_indicator = FONT.render("VIEWING HISTORY", True, (255, 150, 50))
            self.screen.blit(history_indicator, (BOARD_SIZE + 20, history_y))
            click_hint = FONT_SMALL.render("Click board to return", True, (200, 200, 200))
            self.screen.blit(click_hint, (BOARD_SIZE + 20, history_y + 23))

        # Move history
        history_y = 170
        pygame.draw.line(self.screen, (50, 50, 50),
                        (BOARD_SIZE + 15, history_y), (BOARD_SIZE + PANEL_WIDTH - 15, history_y), 1)

        self.screen.blit(FONT_SMALL.render("Move History", True, (140, 140, 140)),
                        (BOARD_SIZE + 20, history_y + 8))

        # Format moves
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

        # Show with scrolling
        max_visible = 9
        total_moves = len(move_pairs)
        end_idx = total_moves - self.move_scroll_offset
        start_idx = max(0, end_idx - max_visible)
        visible_moves = move_pairs[start_idx:end_idx]

        for i, move_text in enumerate(visible_moves):
            color = (190, 190, 190)
            if self.viewing_history and self.current_move_index is not None:
                move_pair_idx = start_idx + i
                first_move_idx = move_pair_idx * 2
                second_move_idx = first_move_idx + 1
                if first_move_idx == self.current_move_index or second_move_idx == self.current_move_index:
                    color = (255, 220, 100)

            text = FONT_SMALL.render(move_text, True, color)
            self.screen.blit(text, (BOARD_SIZE + 22, history_y + 35 + i * 18))

        self.scroll_up_button.draw(self.screen)
        self.scroll_down_button.draw(self.screen)

        # Buttons
        button_y = 385
        pygame.draw.line(self.screen, (50, 50, 50),
                        (BOARD_SIZE + 15, button_y - 5), (BOARD_SIZE + PANEL_WIDTH - 15, button_y - 5), 1)

        for button in self.buttons:
            button.draw(self.screen)

        # Difficulty
        pygame.draw.line(self.screen, (50, 50, 50),
                        (BOARD_SIZE + 15, 490), (BOARD_SIZE + PANEL_WIDTH - 15, 490), 1)
        self.screen.blit(FONT_SMALL.render("Difficulty", True, (140, 140, 140)),
                        (BOARD_SIZE + 20, 498))
        for button in self.depth_buttons:
            button.draw(self.screen)

    def handle_click(self, pos):
        if self.viewing_history:
            self.viewing_history = False
            self.current_move_index = None
            return

        if self.engine_thinking or self.board.is_game_over():
            return

        is_player_turn = (self.board.board.turn == chess.WHITE) == self.player_is_white
        if not is_player_turn:
            return

        square = self.get_square_from_pos(pos)
        if square is None:
            return

        if self.selected_square is not None:
            move = None
            for m in self.legal_moves_for_selected:
                if m.to_square == square:
                    move = m
                    break

            if move:
                self.board.make_move_object(move)
                self.last_move = move
                self.selected_square = None
                self.legal_moves_for_selected = []
                self.hint_message = None
                self.status_message = f"You played: {move}"

                if self.board.is_game_over():
                    self.status_message = self.board.get_result()
                else:
                    self.engine_turn()
                return

            piece = self.board.board.piece_at(square)
            if piece and piece.color == self.board.board.turn:
                self.selected_square = square
                self.legal_moves_for_selected = [m for m in self.board.get_legal_moves() if m.from_square == square]
                return

            self.selected_square = None
            self.legal_moves_for_selected = []
        else:
            piece = self.board.board.piece_at(square)
            if piece and piece.color == self.board.board.turn:
                self.selected_square = square
                self.legal_moves_for_selected = [m for m in self.board.get_legal_moves() if m.from_square == square]

    def engine_turn(self):
        if self.engine_thinking:
            return
        self.engine_thinking = True
        self.engine_done = False
        self.engine_result = None
        self.status_message = "Engine thinking..."
        threading.Thread(target=self._engine_move, daemon=True).start()

    def _engine_move(self):
        board_copy = self.board.board.copy()
        result = self.engine.search(board_copy)
        self.engine_result = result
        self.engine_done = True

    def process_engine_result(self):
        if not self.engine_done:
            return
        if self.engine_result is None:
            return

        result = self.engine_result
        self.engine_result = None
        self.engine_thinking = False
        self.engine_done = False

        self.last_search_stats = result

        if result.best_move:
            self.board.make_move_object(result.best_move)
            self.last_move = result.best_move

            score_text = f"{result.score/100:+.2f}" if abs(result.score) < 90000 else "Mate"
            self.status_message = f"Engine: {result.best_move} ({score_text})"

            nps = int(result.nodes_searched / result.time_spent) if result.time_spent > 0 else 0
            print(f"\n{self.engine_name} played: {result.best_move} (eval: {score_text})")
            print(f"  Depth: {result.depth} | Nodes: {result.nodes_searched:,} | Time: {result.time_spent:.2f}s | Speed: {nps:,} NPS")

            if self.board.is_game_over():
                self.status_message = self.board.get_result()

    def run(self):
        clock = pygame.time.Clock()
        running = True

        if not self.player_is_white:
            self.engine_turn()

        while running:
            if self.return_to_setup:
                return

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                all_buttons = self.buttons + self.depth_buttons + [self.scroll_up_button, self.scroll_down_button]
                button_handled = False
                for button in all_buttons:
                    if button.handle_event(event):
                        button_handled = True
                        break

                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1 and not button_handled:
                        self.handle_click(event.pos)
                    elif event.button == 4:
                        all_moves = list(self.board.board.move_stack)
                        move_pairs_count = (len(all_moves) + 1) // 2
                        if move_pairs_count > 9:
                            self.move_scroll_offset = min(self.move_scroll_offset + 1, move_pairs_count - 9)
                    elif event.button == 5:
                        self.move_scroll_offset = max(0, self.move_scroll_offset - 1)

                if event.type == pygame.MOUSEMOTION:
                    all_buttons = self.buttons + self.depth_buttons + [self.scroll_up_button, self.scroll_down_button]
                    for button in all_buttons:
                        button.hovered = button.rect.collidepoint(event.pos)

            self.process_engine_result()

            self.screen.fill(WHITE)
            self.draw_board()
            self.draw_panel()

            pygame.display.flip()
            clock.tick(60)

        pygame.quit()
        sys.exit()


def main():
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
                time_limit=setup.time_limit,
                engine_module=setup.engine_dropdown.get_selected()
            )
            gui.run()

            if not gui.return_to_setup:
                running = False

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
