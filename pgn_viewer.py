"""
PGN Viewer - Load and explore chess games from PGN files
"""

import pygame
import chess
import chess.pgn
import sys
import os
from typing import Optional, List, Tuple
from pathlib import Path
from tkinter import Tk, filedialog


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
LAST_MOVE = (170, 162, 58)
BG_COLOR = (240, 240, 245)
PANEL_BG = (250, 250, 252)
BUTTON_COLOR = (70, 130, 180)
BUTTON_HOVER = (100, 160, 210)
BUTTON_DISABLED = (180, 180, 180)
TEXT_COLOR = (40, 40, 50)
GREEN = (76, 175, 80)
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
        self.enabled = True
        self.hovered = False

    def draw(self, screen, font):
        """Draw the button."""
        if not self.enabled:
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


class PGNViewer:
    """GUI for viewing chess games from PGN files."""

    def __init__(self):
        """Initialize PGN viewer."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("PGN Viewer")
        self.clock = pygame.time.Clock()

        # Fonts
        self.title_font = pygame.font.Font(None, 48)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 16)

        # State
        self.mode = "select"  # "select" or "viewer"
        self.game = None
        self.board = None
        self.moves = []
        self.move_sans = []  # SAN notation for each move
        self.current_move_index = -1  # -1 means starting position
        self.last_move = None

        # Game info
        self.game_info = {}

        # Load piece font
        self.load_pieces()

        # Create UI
        self.create_select_ui()

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

    def create_select_ui(self):
        """Create file selection UI."""
        panel_x = SCREEN_WIDTH // 2 - 150
        y = SCREEN_HEIGHT // 2 - 50

        self.browse_button = Button(panel_x, y, 300, 60, "Browse PGN File", BUTTON_COLOR)
        self.recent_button = Button(panel_x, y + 80, 300, 60, "Recent Games", BUTTON_COLOR)

    def create_viewer_ui(self):
        """Create viewer control buttons."""
        panel_x = BOARD_SIZE + 20
        button_y = SCREEN_HEIGHT - 200
        button_width = 100
        button_height = 45
        spacing = 10

        self.start_btn = Button(panel_x, button_y, button_width, button_height, "|<", BUTTON_COLOR)
        self.prev_btn = Button(panel_x + button_width + spacing, button_y, button_width, button_height, "<", BUTTON_COLOR)
        self.next_btn = Button(panel_x + 2 * (button_width + spacing), button_y, button_width, button_height, ">", BUTTON_COLOR)
        self.end_btn = Button(panel_x + 3 * (button_width + spacing), button_y, button_width, button_height, ">|", BUTTON_COLOR)

        self.back_btn = Button(panel_x, button_y + button_height + spacing,
                              4 * button_width + 3 * spacing, 40, "Back to File Selection", ORANGE)

    def browse_file(self):
        """Open file dialog to select PGN file."""
        # Create Tkinter root (hidden)
        root = Tk()
        root.withdraw()
        root.attributes('-topmost', True)

        # Open file dialog
        filename = filedialog.askopenfilename(
            title="Select PGN File",
            filetypes=[("PGN files", "*.pgn"), ("All files", "*.*")]
        )

        root.destroy()

        # Bring pygame window back to front
        if filename:
            self.load_pgn(filename)

    def load_pgn(self, filepath: str):
        """Load a PGN file."""
        try:
            with open(filepath) as pgn_file:
                self.game = chess.pgn.read_game(pgn_file)

                if self.game is None:
                    print(f"No valid game found in {filepath}")
                    return

                # Extract game info
                self.game_info = {
                    "White": self.game.headers.get("White", "Unknown"),
                    "Black": self.game.headers.get("Black", "Unknown"),
                    "Result": self.game.headers.get("Result", "*"),
                    "Date": self.game.headers.get("Date", "Unknown"),
                    "Event": self.game.headers.get("Event", "Unknown"),
                    "Site": self.game.headers.get("Site", "Unknown"),
                }

                # Build move list and SAN notation
                self.moves = []
                self.move_sans = []
                temp_board = chess.Board()
                node = self.game
                while node.variations:
                    next_node = node.variation(0)
                    move = next_node.move
                    self.moves.append(move)
                    self.move_sans.append(temp_board.san(move))
                    temp_board.push(move)
                    node = next_node

                # Initialize board to starting position
                self.board = chess.Board()
                self.current_move_index = -1
                self.last_move = None

                # Create viewer UI
                self.create_viewer_ui()

                # Switch to viewer mode
                self.mode = "viewer"
                pygame.display.set_caption(f"PGN Viewer - {self.game_info['White']} vs {self.game_info['Black']}")

                print(f"Loaded game: {self.game_info['White']} vs {self.game_info['Black']}")
                print(f"Total moves: {len(self.moves)}")

        except Exception as e:
            print(f"Error loading PGN: {e}")
            import traceback
            traceback.print_exc()

    def show_recent_games(self):
        """Show recent games from the games directory."""
        # Find all PGN files in the games directory
        games_dir = Path("games")
        if not games_dir.exists():
            print("No games directory found")
            return

        pgn_files = list(games_dir.rglob("*.pgn"))

        if not pgn_files:
            print("No PGN files found")
            return

        # Load the most recent one
        pgn_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)
        self.load_pgn(str(pgn_files[0]))

    def go_to_start(self):
        """Go to starting position."""
        self.board = chess.Board()
        self.current_move_index = -1
        self.last_move = None

    def go_to_end(self):
        """Go to end of game."""
        self.board = chess.Board()
        self.last_move = None
        for i, move in enumerate(self.moves):
            self.board.push(move)
            self.last_move = move
        self.current_move_index = len(self.moves) - 1

    def previous_move(self):
        """Go to previous move."""
        if self.current_move_index >= 0:
            self.board.pop()
            self.current_move_index -= 1
            self.last_move = self.moves[self.current_move_index] if self.current_move_index >= 0 else None

    def next_move(self):
        """Go to next move."""
        if self.current_move_index < len(self.moves) - 1:
            self.current_move_index += 1
            move = self.moves[self.current_move_index]
            self.board.push(move)
            self.last_move = move

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

                # Highlight last move
                square = chess.square(col, 7 - row)
                if self.last_move and (square == self.last_move.from_square or square == self.last_move.to_square):
                    color = LAST_MOVE

                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

                # Draw piece
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

    def draw_select_screen(self):
        """Draw file selection screen."""
        self.screen.fill(BG_COLOR)

        # Title
        title = self.title_font.render("PGN Viewer", True, TEXT_COLOR)
        self.screen.blit(title, (SCREEN_WIDTH // 2 - title.get_width() // 2, 150))

        # Instructions
        instructions = [
            "Load a chess game from a PGN file",
            "and explore it move by move",
            "",
            "Use arrow keys or buttons to navigate"
        ]
        y = 250
        for line in instructions:
            text = self.small_font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (SCREEN_WIDTH // 2 - text.get_width() // 2, y))
            y += 30

        # Buttons
        self.browse_button.draw(self.screen, self.font)
        self.recent_button.draw(self.screen, self.font)

    def draw_viewer_screen(self):
        """Draw viewer screen."""
        self.screen.fill(BG_COLOR)

        # Draw board
        self.draw_board()

        # Draw panel
        self.draw_panel()

        # Draw buttons
        self.start_btn.draw(self.screen, self.font)
        self.prev_btn.draw(self.screen, self.font)
        self.next_btn.draw(self.screen, self.font)
        self.end_btn.draw(self.screen, self.font)
        self.back_btn.draw(self.screen, self.small_font)

    def draw_panel(self):
        """Draw information panel."""
        panel_x = BOARD_SIZE

        # Panel background
        panel_rect = pygame.Rect(panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_BG, panel_rect)
        pygame.draw.line(self.screen, (220, 220, 220), (panel_x, 0), (panel_x, SCREEN_HEIGHT), 2)

        y = 20

        # Title
        title = self.title_font.render("Game Info", True, TEXT_COLOR)
        self.screen.blit(title, (panel_x + 20, y))
        y += 60

        # Game info box
        info_box = pygame.Rect(panel_x + 15, y, PANEL_WIDTH - 30, 180)
        pygame.draw.rect(self.screen, WHITE, info_box, border_radius=8)
        pygame.draw.rect(self.screen, (220, 220, 220), info_box, 2, border_radius=8)

        info_y = y + 15
        info_lines = [
            f"White: {self.game_info['White']}",
            f"Black: {self.game_info['Black']}",
            f"Result: {self.game_info['Result']}",
            f"",
            f"Event: {self.game_info['Event'][:30]}",
            f"Date: {self.game_info['Date']}",
        ]

        for line in info_lines:
            text = self.tiny_font.render(line, True, TEXT_COLOR)
            self.screen.blit(text, (panel_x + 25, info_y))
            info_y += 24

        y += 200

        # Move counter
        move_num = self.current_move_index + 1
        total_moves = len(self.moves)
        counter_text = f"Move {move_num} of {total_moves}" if move_num > 0 else f"Starting position ({total_moves} moves)"
        counter = self.font.render(counter_text, True, TEXT_COLOR)
        self.screen.blit(counter, (panel_x + 20, y))
        y += 40

        # Current move
        if self.current_move_index >= 0:
            move_text = self.move_sans[self.current_move_index]
            move_display = self.title_font.render(move_text, True, TEXT_COLOR)
            self.screen.blit(move_display, (panel_x + 20, y))
            y += 60

        # Move list
        y += 20
        list_title = self.font.render("Move List:", True, TEXT_COLOR)
        self.screen.blit(list_title, (panel_x + 20, y))
        y += 30

        # Display moves around current position
        start_idx = max(0, self.current_move_index - 5)
        end_idx = min(len(self.moves), self.current_move_index + 10)

        for i in range(start_idx, end_idx):
            if i < len(self.moves):
                san = self.move_sans[i]

                # Highlight current move
                color = GREEN if i == self.current_move_index else TEXT_COLOR
                move_num_text = f"{i // 2 + 1}." if i % 2 == 0 else "   "
                move_text = f"{move_num_text} {san}"

                text = self.small_font.render(move_text, True, color)
                self.screen.blit(text, (panel_x + 25, y))
                y += 22

                if y > SCREEN_HEIGHT - 250:
                    break

    def handle_select_events(self, event):
        """Handle events in select mode."""
        if self.browse_button.handle_event(event):
            self.browse_file()

        if self.recent_button.handle_event(event):
            self.show_recent_games()

    def handle_viewer_events(self, event):
        """Handle events in viewer mode."""
        if self.start_btn.handle_event(event):
            self.go_to_start()

        if self.prev_btn.handle_event(event):
            self.previous_move()

        if self.next_btn.handle_event(event):
            self.next_move()

        if self.end_btn.handle_event(event):
            self.go_to_end()

        if self.back_btn.handle_event(event):
            self.mode = "select"
            self.game = None
            self.board = None
            pygame.display.set_caption("PGN Viewer")

        # Keyboard shortcuts
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                self.previous_move()
            elif event.key == pygame.K_RIGHT:
                self.next_move()
            elif event.key == pygame.K_HOME:
                self.go_to_start()
            elif event.key == pygame.K_END:
                self.go_to_end()

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False

            if self.mode == "select":
                self.handle_select_events(event)
            else:  # viewer mode
                self.handle_viewer_events(event)

        return True

    def run(self):
        """Main GUI loop."""
        running = True

        while running:
            running = self.handle_events()

            if self.mode == "select":
                self.draw_select_screen()
            else:  # viewer mode
                self.draw_viewer_screen()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


def main():
    """Main entry point."""
    print("\nPGN Viewer")
    print("=" * 50)
    print("\nLoad a chess game from a PGN file")
    print("Navigate with arrow keys or buttons\n")

    viewer = PGNViewer()
    viewer.run()


if __name__ == "__main__":
    main()
