"""
Tournament GUI with Interactive Configuration Screen
"""

import pygame
import chess
import sys
import os
import glob
import importlib
import threading
import time
from typing import Optional, Dict, Any, Tuple, List
from game_recorder import GameRecorder


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
BG_COLOR = (240, 240, 245)
PANEL_BG = (250, 250, 252)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
BUTTON_DISABLED = (180, 180, 180)
BUTTON_SELECTED = (50, 180, 100)
TEXT_COLOR = (40, 40, 50)
GREEN = (76, 175, 80)
RED = (244, 67, 54)
ORANGE = (255, 152, 0)

# Screen dimensions
BOARD_SIZE = 640
PANEL_WIDTH = 460
SCREEN_WIDTH = BOARD_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = 720
SQUARE_SIZE = BOARD_SIZE // 8


class Button:
    """Simple button class for GUI."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str, color: Tuple[int, int, int]):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.hover_color = tuple(min(c + 30, 255) for c in color)
        self.disabled_color = BUTTON_DISABLED
        self.selected_color = BUTTON_SELECTED
        self.enabled = True
        self.hovered = False
        self.selected = False

    def draw(self, screen, font):
        """Draw the button."""
        if self.selected:
            color = self.selected_color
        elif not self.enabled:
            color = self.disabled_color
        elif self.hovered:
            color = self.hover_color
        else:
            color = self.color

        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (200, 200, 200), self.rect, 2, border_radius=5)

        text_surf = font.render(self.text, True, WHITE)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def handle_event(self, event) -> bool:
        """Handle mouse events."""
        if not self.enabled:
            return False

        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False


class TournamentGUI:
    """GUI for watching chess engine tournaments with configuration screen."""

    def __init__(self):
        """Initialize tournament GUI."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Chess Tournament - Configuration")
        self.clock = pygame.time.Clock()

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 16)

        # State
        self.mode = "config"  # "config" or "tournament"

        # Find available engines
        self.available_engines = self.find_engines()

        # Configuration settings (defaults)
        self.config = {
            "engine1": "engine_v3" if "engine_v3" in self.available_engines else self.available_engines[0],
            "engine2": "engine_v4" if "engine_v4" in self.available_engines else self.available_engines[0],
            "depth1": 5,
            "depth2": 5,
            "num_games": 10,
            "time_limit": None,
            "output_dir": "games"
        }

        # Tournament state (initialized when tournament starts)
        self.engine1 = None
        self.engine2 = None
        self.board = None
        self.current_game = 0
        self.running = False
        self.paused = False
        self.speed = 1
        self.stats = None
        self.recorder = None
        self.game_thread = None
        self.current_move_info = None

        # Create config UI
        self.create_config_ui()

        # Load piece font
        self.load_pieces()

    def find_engines(self) -> List[str]:
        """Find available engine modules."""
        engines = []
        for file in glob.glob("engine*.py"):
            module_name = file[:-3]  # Remove .py
            engines.append(module_name)
        engines.sort()
        return engines if engines else ["engine"]

    def create_config_ui(self):
        """Create configuration UI elements."""
        panel_x = BOARD_SIZE + 30
        y_start = 100
        button_width = 120
        button_height = 40
        spacing = 10

        # Engine 1 buttons
        self.engine1_buttons = []
        y = y_start
        for i, engine in enumerate(self.available_engines):
            btn = Button(panel_x, y + i * (button_height + spacing), 180, button_height,
                        engine, BUTTON_COLOR)
            btn.selected = (engine == self.config["engine1"])
            self.engine1_buttons.append((btn, engine))

        # Engine 2 buttons
        self.engine2_buttons = []
        y = y_start
        for i, engine in enumerate(self.available_engines):
            btn = Button(panel_x + 220, y + i * (button_height + spacing), 180, button_height,
                        engine, BUTTON_COLOR)
            btn.selected = (engine == self.config["engine2"])
            self.engine2_buttons.append((btn, engine))

        # Depth buttons
        y = y_start + len(self.available_engines) * (button_height + spacing) + 40
        self.depth1_buttons = []
        for i, depth in enumerate([3, 4, 5, 6, 7]):
            btn = Button(panel_x + i * 45, y, 40, 35, str(depth), BUTTON_COLOR)
            btn.selected = (depth == self.config["depth1"])
            self.depth1_buttons.append((btn, depth))

        self.depth2_buttons = []
        y += 60
        for i, depth in enumerate([3, 4, 5, 6, 7]):
            btn = Button(panel_x + i * 45, y, 40, 35, str(depth), BUTTON_COLOR)
            btn.selected = (depth == self.config["depth2"])
            self.depth2_buttons.append((btn, depth))

        # Games buttons
        y += 80
        self.games_buttons = []
        for i, games in enumerate([10, 20, 50, 100]):
            btn = Button(panel_x + i * 60, y, 55, 35, str(games), BUTTON_COLOR)
            btn.selected = (games == self.config["num_games"])
            self.games_buttons.append((btn, games))

        # Time limit buttons
        y += 80
        self.time_limit_buttons = []
        time_options = [("Depth", None), ("0.1s", 0.1), ("1s", 1.0), ("2s", 2.0), ("5s", 5.0), ("10s", 10.0)]
        for i, (label, time_val) in enumerate(time_options):
            btn = Button(panel_x + i * 50, y, 45, 35, label, BUTTON_COLOR)
            btn.selected = (time_val == self.config["time_limit"])
            self.time_limit_buttons.append((btn, time_val, label))

        # Output directory buttons
        y += 80
        self.output_dir_buttons = []
        output_dirs = ["games", "results", "matches", "tournaments"]
        for i, dir_name in enumerate(output_dirs):
            btn = Button(panel_x + i * 75, y, 70, 35, dir_name, BUTTON_COLOR)
            btn.selected = (dir_name == self.config["output_dir"])
            self.output_dir_buttons.append((btn, dir_name))

        # Start button
        self.config_start_button = Button(panel_x + 50, SCREEN_HEIGHT - 100, 300, 60,
                                         "START TOURNAMENT", GREEN)

        # Tournament control buttons (created when tournament starts)
        self.tournament_buttons = []

    def load_pieces(self):
        """Load chess piece images."""
        self.piece_font = None

        # Try loading chess font files first
        chess_font_files = ['ChessMerida.ttf', 'ChessAlpha.ttf', 'chess_merida_unicode.ttf']
        for font_file in chess_font_files:
            try:
                self.piece_font = pygame.font.Font(font_file, 65)
                print(f"Loaded chess font: {font_file}")
                break
            except:
                continue

        # Fall back to system fonts if no chess font found
        if self.piece_font is None:
            font_names = ['Segoe UI Symbol', 'Arial Unicode MS', 'DejaVu Sans', 'FreeSans']
            for font_name in font_names:
                try:
                    self.piece_font = pygame.font.SysFont(font_name, 65)
                    print(f"Loaded font: {font_name}")
                    break
                except:
                    continue

        if self.piece_font is None:
            self.piece_font = pygame.font.Font(None, 65)

        self.piece_chars = {
            'P': '\u2659', 'N': '\u2658', 'B': '\u2657',
            'R': '\u2656', 'Q': '\u2655', 'K': '\u2654',
            'p': '\u265F', 'n': '\u265E', 'b': '\u265D',
            'r': '\u265C', 'q': '\u265B', 'k': '\u265A'
        }

    def draw_config_screen(self):
        """Draw configuration screen."""
        self.screen.fill(BG_COLOR)

        # Title
        title = self.title_font.render("Tournament Setup", True, TEXT_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 30))

        panel_x = BOARD_SIZE + 30
        y = 100

        # Engine 1 label
        label1 = self.font.render("Engine 1:", True, TEXT_COLOR)
        self.screen.blit(label1, (panel_x, y - 30))

        # Engine 2 label
        label2 = self.font.render("Engine 2:", True, TEXT_COLOR)
        self.screen.blit(label2, (panel_x + 220, y - 30))

        # Draw engine buttons
        for btn, engine in self.engine1_buttons:
            btn.draw(self.screen, self.tiny_font)

        for btn, engine in self.engine2_buttons:
            btn.draw(self.screen, self.tiny_font)

        # Depth labels and buttons
        y = y + len(self.available_engines) * 50 + 40
        depth1_label = self.font.render(f"Engine 1 Depth:", True, TEXT_COLOR)
        self.screen.blit(depth1_label, (panel_x, y - 30))

        for btn, depth in self.depth1_buttons:
            btn.draw(self.screen, self.small_font)

        y += 60
        depth2_label = self.font.render(f"Engine 2 Depth:", True, TEXT_COLOR)
        self.screen.blit(depth2_label, (panel_x, y - 30))

        for btn, depth in self.depth2_buttons:
            btn.draw(self.screen, self.small_font)

        # Games label and buttons
        y += 80
        games_label = self.font.render("Number of Games:", True, TEXT_COLOR)
        self.screen.blit(games_label, (panel_x, y - 30))

        for btn, games in self.games_buttons:
            btn.draw(self.screen, self.small_font)

        # Time limit label and buttons
        y += 80
        time_label = self.font.render("Time per Move:", True, TEXT_COLOR)
        self.screen.blit(time_label, (panel_x, y - 30))

        for btn, time_val, label in self.time_limit_buttons:
            btn.draw(self.screen, self.tiny_font)

        # Output directory label and buttons
        y += 80
        output_label = self.font.render("Output Directory:", True, TEXT_COLOR)
        self.screen.blit(output_label, (panel_x, y - 30))

        for btn, dir_name in self.output_dir_buttons:
            btn.draw(self.screen, self.tiny_font)

        # Current config display
        y += 80
        time_display = f"{self.config['time_limit']}s per move" if self.config['time_limit'] else "Depth-based"
        config_text = [
            f"Ready to start:",
            f"{self.config['engine1']} (depth {self.config['depth1']}) vs",
            f"{self.config['engine2']} (depth {self.config['depth2']})",
            f"{self.config['num_games']} games",
            f"Time: {time_display}",
            f"Output: {self.config['output_dir']}"
        ]
        for i, line in enumerate(config_text):
            text = self.small_font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (panel_x, y + i * 22))

        # Start button
        self.config_start_button.draw(self.screen, self.font)

        # Instructions on left side
        instructions = [
            "Select engines and settings,",
            "then click START TOURNAMENT",
            "",
            "Controls during tournament:",
            "SPACE - Start/Pause",
            "S - Stop",
            "Q - Quit",
            "1/2/3/4 - Speed control"
        ]
        for i, line in enumerate(instructions):
            text = self.small_font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (30, 150 + i * 30))

    def handle_config_events(self, event):
        """Handle events in config mode."""
        # Engine 1 selection
        for btn, engine in self.engine1_buttons:
            if btn.handle_event(event):
                self.config["engine1"] = engine
                # Update selected states
                for b, e in self.engine1_buttons:
                    b.selected = (e == engine)

        # Engine 2 selection
        for btn, engine in self.engine2_buttons:
            if btn.handle_event(event):
                self.config["engine2"] = engine
                # Update selected states
                for b, e in self.engine2_buttons:
                    b.selected = (e == engine)

        # Depth 1 selection
        for btn, depth in self.depth1_buttons:
            if btn.handle_event(event):
                self.config["depth1"] = depth
                for b, d in self.depth1_buttons:
                    b.selected = (d == depth)

        # Depth 2 selection
        for btn, depth in self.depth2_buttons:
            if btn.handle_event(event):
                self.config["depth2"] = depth
                for b, d in self.depth2_buttons:
                    b.selected = (d == depth)

        # Games selection
        for btn, games in self.games_buttons:
            if btn.handle_event(event):
                self.config["num_games"] = games
                for b, g in self.games_buttons:
                    b.selected = (g == games)

        # Time limit selection
        for btn, time_val, label in self.time_limit_buttons:
            if btn.handle_event(event):
                self.config["time_limit"] = time_val
                for b, t, l in self.time_limit_buttons:
                    b.selected = (t == time_val)

        # Output directory selection
        for btn, dir_name in self.output_dir_buttons:
            if btn.handle_event(event):
                self.config["output_dir"] = dir_name
                for b, d in self.output_dir_buttons:
                    b.selected = (d == dir_name)

        # Start button
        if self.config_start_button.handle_event(event):
            self.start_tournament_setup()

    def start_tournament_setup(self):
        """Initialize tournament with configured settings."""
        print(f"\nLoading engines: {self.config['engine1']} vs {self.config['engine2']}...")

        try:
            # Load engines
            mod1 = importlib.import_module(self.config['engine1'])
            mod2 = importlib.import_module(self.config['engine2'])
            self.engine1 = mod1.ChessEngine(max_depth=self.config['depth1'],
                                           time_limit=self.config['time_limit'])
            self.engine2 = mod2.ChessEngine(max_depth=self.config['depth2'],
                                           time_limit=self.config['time_limit'])

            # Initialize tournament state
            self.board = chess.Board()
            self.current_game = 0
            self.running = False
            self.paused = False
            self.speed = 1

            self.stats = {
                "engine1": {"wins": 0, "draws": 0, "losses": 0},
                "engine2": {"wins": 0, "draws": 0, "losses": 0},
                "games": [],
                "start_time": None
            }

            self.recorder = GameRecorder(self.config['output_dir'])

            # Create tournament buttons
            self.create_tournament_buttons()

            # Switch to tournament mode
            self.mode = "tournament"
            pygame.display.set_caption("Chess Tournament Viewer")
            print("Tournament ready! Press SPACE or click Start to begin.")

        except Exception as e:
            print(f"Error loading engines: {e}")
            import traceback
            traceback.print_exc()

    def create_tournament_buttons(self):
        """Create tournament control buttons."""
        panel_x = BOARD_SIZE + 20
        button_y = SCREEN_HEIGHT - 200
        button_width = 130
        button_height = 45
        spacing = 10

        start_btn = Button(panel_x, button_y, button_width, button_height, "Start", GREEN)
        pause_btn = Button(panel_x + button_width + spacing, button_y, button_width, button_height, "Pause", ORANGE)
        stop_btn = Button(panel_x + 2 * (button_width + spacing), button_y, button_width, button_height, "Stop", RED)

        # Speed buttons
        speed_y = button_y + button_height + spacing
        speed_width = 60
        speed_1x = Button(panel_x, speed_y, speed_width, 35, "1x", BUTTON_COLOR)
        speed_10x = Button(panel_x + speed_width + 5, speed_y, speed_width, 35, "10x", BUTTON_COLOR)
        speed_50x = Button(panel_x + 2 * (speed_width + 5), speed_y, speed_width, 35, "50x", BUTTON_COLOR)
        speed_100x = Button(panel_x + 3 * (speed_width + 5), speed_y, speed_width, 35, "100x", BUTTON_COLOR)

        self.tournament_buttons = {
            "start": start_btn,
            "pause": pause_btn,
            "stop": stop_btn,
            "1x": speed_1x,
            "10x": speed_10x,
            "50x": speed_50x,
            "100x": speed_100x
        }

    def draw_board(self):
        """Draw the chess board."""
        board_rect = pygame.Rect(0, (SCREEN_HEIGHT - BOARD_SIZE) // 2, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(self.screen, (100, 100, 100), board_rect.inflate(4, 4))

        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE + (SCREEN_HEIGHT - BOARD_SIZE) // 2

                # Draw square
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

                # Draw piece
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)

                if piece:
                    piece_char = piece.symbol()
                    piece_unicode = self.piece_chars.get(piece_char)
                    if piece_unicode:
                        if piece.color == chess.WHITE:
                            # White pieces: dark outline with white fill
                            outline_surface = self.piece_font.render(piece_unicode, True, (50, 50, 50))
                            text_rect = outline_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                            # Draw outline in 8 directions for thickness
                            for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                                self.screen.blit(outline_surface, (text_rect.x + dx, text_rect.y + dy))
                            # Draw white piece on top
                            text_surface = self.piece_font.render(piece_unicode, True, (255, 255, 255))
                            self.screen.blit(text_surface, text_rect)
                        else:
                            # Black pieces: solid black with antialiasing
                            text_surface = self.piece_font.render(piece_unicode, True, (30, 30, 30))
                            text_rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                            self.screen.blit(text_surface, text_rect)

    def draw_tournament_panel(self):
        """Draw tournament statistics and control panel."""
        panel_x = BOARD_SIZE

        # Panel background
        panel_rect = pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, (220, 220, 220), (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)

        y = 20

        # Title
        title = self.title_font.render("Tournament", True, TEXT_COLOR)
        self.screen.blit(title, (panel_x + 20, y))
        y += 50

        # Match info box
        info_box = pygame.Rect(panel_x + 15, y, PANEL_WIDTH - 30, 140)
        pygame.draw.rect(self.screen, WHITE, info_box, border_radius=8)
        pygame.draw.rect(self.screen, (220, 220, 220), info_box, 2, border_radius=8)

        info_y = y + 15
        info_lines = [
            f"{self.config['engine1']} vs {self.config['engine2']}",
            f"Depth: {self.config['depth1']} vs {self.config['depth2']}",
            f"Time: {self.config['time_limit']}s" if self.config['time_limit'] else "Depth-based",
            f"",
            f"Game: {self.current_game}/{self.config['num_games']}",
        ]

        for line in info_lines:
            text = self.small_font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (panel_x + 25, info_y))
            info_y += 24

        y += 160

        # Score section
        score_title = self.font.render("Score", True, TEXT_COLOR)
        self.screen.blit(score_title, (panel_x + 20, y))
        y += 35

        # Score boxes
        e1_score = self.stats["engine1"]["wins"] + 0.5 * self.stats["engine1"]["draws"]
        e2_score = self.stats["engine2"]["wins"] + 0.5 * self.stats["engine2"]["draws"]

        # Engine 1 score
        score_box1 = pygame.Rect(panel_x + 15, y, (PANEL_WIDTH - 40) // 2 - 5, 100)
        pygame.draw.rect(self.screen, WHITE, score_box1, border_radius=8)
        pygame.draw.rect(self.screen, GREEN if e1_score > e2_score else (220, 220, 220), score_box1, 2, border_radius=8)

        name1 = self.tiny_font.render(self.config['engine1'], True, TEXT_COLOR)
        score1 = self.title_font.render(f"{e1_score}", True, TEXT_COLOR)
        wdl1 = self.tiny_font.render(f"W:{self.stats['engine1']['wins']} D:{self.stats['engine1']['draws']} L:{self.stats['engine1']['losses']}", True, TEXT_COLOR)

        self.screen.blit(name1, (score_box1.centerx - name1.get_width() // 2, score_box1.y + 10))
        self.screen.blit(score1, (score_box1.centerx - score1.get_width() // 2, score_box1.y + 35))
        self.screen.blit(wdl1, (score_box1.centerx - wdl1.get_width() // 2, score_box1.y + 75))

        # Engine 2 score
        score_box2 = pygame.Rect(panel_x + 15 + (PANEL_WIDTH - 40) // 2 + 5, y, (PANEL_WIDTH - 40) // 2 - 5, 100)
        pygame.draw.rect(self.screen, WHITE, score_box2, border_radius=8)
        pygame.draw.rect(self.screen, GREEN if e2_score > e1_score else (220, 220, 220), score_box2, 2, border_radius=8)

        name2 = self.tiny_font.render(self.config['engine2'], True, TEXT_COLOR)
        score2 = self.title_font.render(f"{e2_score}", True, TEXT_COLOR)
        wdl2 = self.tiny_font.render(f"W:{self.stats['engine2']['wins']} D:{self.stats['engine2']['draws']} L:{self.stats['engine2']['losses']}", True, TEXT_COLOR)

        self.screen.blit(name2, (score_box2.centerx - name2.get_width() // 2, score_box2.y + 10))
        self.screen.blit(score2, (score_box2.centerx - score2.get_width() // 2, score_box2.y + 35))
        self.screen.blit(wdl2, (score_box2.centerx - wdl2.get_width() // 2, score_box2.y + 75))

        y += 120

        # Current move info
        if self.current_move_info:
            move_box = pygame.Rect(panel_x + 15, y, PANEL_WIDTH - 30, 90)
            pygame.draw.rect(self.screen, WHITE, move_box, border_radius=8)
            pygame.draw.rect(self.screen, (220, 220, 220), move_box, 2, border_radius=8)

            move_y = y + 12
            move_title = self.small_font.render("Last Move", True, TEXT_COLOR)
            self.screen.blit(move_title, (panel_x + 25, move_y))
            move_y += 28

            move_text = self.font.render(f"Move: {self.current_move_info.get('move', 'N/A')}", True, TEXT_COLOR)
            time_text = self.small_font.render(f"Time: {self.current_move_info.get('time', 0):.2f}s", True, TEXT_COLOR)
            nodes_text = self.small_font.render(f"Nodes: {self.current_move_info.get('nodes', 0):,}", True, TEXT_COLOR)

            self.screen.blit(move_text, (panel_x + 25, move_y))
            self.screen.blit(time_text, (panel_x + 200, move_y))
            self.screen.blit(nodes_text, (panel_x + 25, move_y + 26))

            y += 100

        # Status
        y = SCREEN_HEIGHT - 280
        status_text = "Running..." if self.running and not self.paused else "Paused" if self.paused else "Ready"
        status_color = GREEN if status_text == "Running..." else ORANGE if status_text == "Paused" else TEXT_COLOR
        status = self.font.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status, (panel_x + 20, y))

        speed_text = self.small_font.render(f"Speed: {self.speed}x", True, TEXT_COLOR)
        self.screen.blit(speed_text, (panel_x + 250, y + 5))

        # Draw buttons
        for button in self.tournament_buttons.values():
            button.draw(self.screen, self.small_font)

    def play_game_threaded(self, game_number: int, engine1_is_white: bool):
        """Play a single game in a thread."""
        self.board = chess.Board()

        white_engine = self.engine1 if engine1_is_white else self.engine2
        black_engine = self.engine2 if engine1_is_white else self.engine1
        white_name = self.config['engine1'] if engine1_is_white else self.config['engine2']
        black_name = self.config['engine2'] if engine1_is_white else self.config['engine1']

        white_times = []
        white_nodes = []
        black_times = []
        black_nodes = []

        move_count = 0
        max_moves = 500

        try:
            while not self.board.is_game_over() and move_count < max_moves and self.running:
                while self.paused and self.running:
                    time.sleep(0.1)

                if not self.running:
                    break

                if self.board.turn == chess.WHITE:
                    result = white_engine.search(self.board.copy())
                    if result and result.best_move:
                        self.current_move_info = {
                            'move': result.best_move.uci(),
                            'time': result.time_spent,
                            'nodes': result.nodes_searched
                        }
                        self.board.push(result.best_move)
                        white_times.append(result.time_spent)
                        white_nodes.append(result.nodes_searched)
                    else:
                        break
                else:
                    result = black_engine.search(self.board.copy())
                    if result and result.best_move:
                        self.current_move_info = {
                            'move': result.best_move.uci(),
                            'time': result.time_spent,
                            'nodes': result.nodes_searched
                        }
                        self.board.push(result.best_move)
                        black_times.append(result.time_spent)
                        black_nodes.append(result.nodes_searched)
                    else:
                        break

                move_count += 1

                if self.speed < 10:
                    time.sleep(0.05 / self.speed)

            if not self.running:
                return

            # Determine result
            if move_count >= max_moves:
                result_str = "1/2-1/2"
                termination = "adjudication"
            elif self.board.is_checkmate():
                result_str = "1-0" if self.board.turn == chess.BLACK else "0-1"
                termination = "checkmate"
            elif self.board.is_stalemate():
                result_str = "1/2-1/2"
                termination = "stalemate"
            else:
                result_str = "1/2-1/2"
                termination = "draw"

            # Record game
            white_stats = {
                "avg_time": sum(white_times) / len(white_times) if white_times else 0,
                "avg_nodes": sum(white_nodes) / len(white_nodes) if white_nodes else 0,
                "total_moves": len(white_times)
            }

            black_stats = {
                "avg_time": sum(black_times) / len(black_times) if black_times else 0,
                "avg_nodes": sum(black_nodes) / len(black_nodes) if black_nodes else 0,
                "total_moves": len(black_times)
            }

            self.recorder.record_game(
                self.board, game_number, white_name, black_name,
                result_str, termination, white_stats, black_stats
            )

            self.update_stats(result_str, white_name)

            self.stats["games"].append({
                "game": game_number,
                "result": result_str,
                "moves": move_count
            })

        except Exception as e:
            print(f"Error in game {game_number}: {e}")

    def update_stats(self, result: str, white_name: str):
        """Update tournament statistics."""
        if result == "1-0":
            if white_name == self.config['engine1']:
                self.stats["engine1"]["wins"] += 1
                self.stats["engine2"]["losses"] += 1
            else:
                self.stats["engine2"]["wins"] += 1
                self.stats["engine1"]["losses"] += 1
        elif result == "0-1":
            if white_name == self.config['engine1']:
                self.stats["engine2"]["wins"] += 1
                self.stats["engine1"]["losses"] += 1
            else:
                self.stats["engine1"]["wins"] += 1
                self.stats["engine2"]["losses"] += 1
        else:
            self.stats["engine1"]["draws"] += 1
            self.stats["engine2"]["draws"] += 1

    def start_tournament(self):
        """Start the tournament."""
        if self.running:
            return

        self.running = True
        self.stats["start_time"] = time.time()

        self.recorder.start_match(
            self.config['engine1'], self.config['engine2'],
            self.config['depth1'], self.config['depth2'],
            self.config['time_limit'], self.config['num_games']
        )

        def run_tournament():
            for game_num in range(1, self.config['num_games'] + 1):
                if not self.running:
                    break

                self.current_game = game_num
                engine1_is_white = (game_num % 2 == 1)
                self.play_game_threaded(game_num, engine1_is_white)

            if self.running:
                self.recorder.save_match_summary(self.stats)
                print("Tournament complete!")
                self.running = False

        self.game_thread = threading.Thread(target=run_tournament, daemon=True)
        self.game_thread.start()

    def handle_tournament_events(self, event):
        """Handle events in tournament mode."""
        if self.tournament_buttons["start"].handle_event(event):
            if not self.running:
                self.start_tournament()

        if self.tournament_buttons["pause"].handle_event(event):
            if self.running:
                self.paused = not self.paused

        if self.tournament_buttons["stop"].handle_event(event):
            self.running = False

        if self.tournament_buttons["1x"].handle_event(event):
            self.speed = 1
        if self.tournament_buttons["10x"].handle_event(event):
            self.speed = 10
        if self.tournament_buttons["50x"].handle_event(event):
            self.speed = 50
        if self.tournament_buttons["100x"].handle_event(event):
            self.speed = 100

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if not self.running:
                    self.start_tournament()
                else:
                    self.paused = not self.paused
            elif event.key == pygame.K_s:
                self.running = False

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False

            if self.mode == "config":
                self.handle_config_events(event)
            else:  # tournament mode
                self.handle_tournament_events(event)

        return True

    def run(self):
        """Main GUI loop."""
        running = True

        while running:
            running = self.handle_events()

            if self.mode == "config":
                self.draw_config_screen()
            else:  # tournament mode
                # Update button states
                self.tournament_buttons["pause"].enabled = self.running
                self.tournament_buttons["stop"].enabled = self.running

                self.screen.fill(BG_COLOR)
                self.draw_board()
                self.draw_tournament_panel()

            pygame.display.flip()
            self.clock.tick(30)

        self.running = False
        pygame.quit()


def main():
    """Main entry point."""
    print("\nTournament GUI with Interactive Configuration")
    print("=" * 50)
    print("\nStarting configuration screen...")
    print("Select your engines and settings, then click START TOURNAMENT\n")

    gui = TournamentGUI()
    gui.run()


if __name__ == "__main__":
    main()
