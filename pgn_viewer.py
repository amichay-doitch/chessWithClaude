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
from gui_utils import (
    Button, ChessBoardRenderer,
    WHITE, BLACK, LIGHT_SQUARE, DARK_SQUARE, LAST_MOVE,
    BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR, PIECE_UNICODE
)

# PGN Viewer specific colors
HIGHLIGHT = (186, 202, 68)
BG_COLOR = (240, 240, 245)
PANEL_BG = (250, 250, 252)
BUTTON_DISABLED = (180, 180, 180)
GREEN = (76, 175, 80)
ORANGE = (255, 152, 0)

# Screen dimensions
BOARD_SIZE = 640
PANEL_WIDTH = 460
SCREEN_WIDTH = BOARD_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = 720
SQUARE_SIZE = BOARD_SIZE // 8


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
        self.evaluations = []  # Evaluation scores for each move
        self.current_move_index = -1  # -1 means starting position
        self.last_move = None

        # Game info
        self.game_info = {}

        # Create board renderer
        self.board_renderer = ChessBoardRenderer(SQUARE_SIZE)

        # Create UI
        self.create_select_ui()

    def create_select_ui(self):
        """Create file selection UI."""
        panel_x = SCREEN_WIDTH // 2 - 150
        y = SCREEN_HEIGHT // 2 - 50

        self.browse_button = Button(panel_x, y, 300, 60, "Browse PGN File", BUTTON_COLOR)
        self.recent_button = Button(panel_x, y + 80, 300, 60, "Recent Games", BUTTON_COLOR)

    def create_viewer_ui(self):
        """Create viewer control buttons."""
        panel_x = BOARD_SIZE + 50  # Match panel position
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

                # Build move list, SAN notation, and evaluations
                self.moves = []
                self.move_sans = []
                self.evaluations = []
                temp_board = chess.Board()
                node = self.game
                while node.variations:
                    next_node = node.variation(0)
                    move = next_node.move
                    self.moves.append(move)
                    self.move_sans.append(temp_board.san(move))

                    # Extract evaluation if available
                    eval_score = None
                    if next_node.eval():
                        try:
                            pov_score = next_node.eval()
                            # Convert to centipawns from white's perspective
                            if pov_score.is_mate():
                                # Mate score
                                mate_in = pov_score.relative.moves
                                eval_score = 10000 if mate_in > 0 else -10000
                            else:
                                # Centipawn score
                                eval_score = pov_score.white().score()
                        except:
                            eval_score = None

                    self.evaluations.append(eval_score)
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
        board_y = (SCREEN_HEIGHT - BOARD_SIZE) // 2

        # Draw board border
        board_rect = pygame.Rect(0, board_y, BOARD_SIZE, BOARD_SIZE)
        pygame.draw.rect(self.screen, (100, 100, 100), board_rect.inflate(4, 4))

        # Use board renderer to draw board and pieces
        self.board_renderer.draw_board(
            screen=self.screen,
            board=self.board,
            x=0,
            y=board_y,
            flipped=False,
            last_move=self.last_move,
            draw_coordinates=False
        )

    def draw_eval_bar(self):
        """Draw evaluation bar showing position evaluation."""
        if self.current_move_index < 0 or self.current_move_index >= len(self.evaluations):
            eval_score = 0  # Starting position
        else:
            eval_score = self.evaluations[self.current_move_index]

        if eval_score is None:
            return  # No evaluation available

        # Bar dimensions
        bar_width = 30
        bar_height = BOARD_SIZE
        bar_x = BOARD_SIZE + 10
        bar_y = (SCREEN_HEIGHT - BOARD_SIZE) // 2

        # Clamp evaluation to reasonable range for display
        clamped_eval = max(-1000, min(1000, eval_score))

        # Calculate height ratio (0.5 = equal, 1.0 = white winning, 0.0 = black winning)
        # Use tanh-like scaling for better visual
        ratio = 0.5 + (clamped_eval / 2000.0)
        ratio = max(0.0, min(1.0, ratio))

        white_height = int(bar_height * ratio)
        black_height = bar_height - white_height

        # Draw bar background
        pygame.draw.rect(self.screen, (60, 60, 60), (bar_x, bar_y, bar_width, bar_height))

        # Draw black portion (top)
        if black_height > 0:
            pygame.draw.rect(self.screen, (40, 40, 40), (bar_x, bar_y, bar_width, black_height))

        # Draw white portion (bottom)
        if white_height > 0:
            pygame.draw.rect(self.screen, (240, 240, 240), (bar_x, bar_y + black_height, bar_width, white_height))

        # Draw border
        pygame.draw.rect(self.screen, (20, 20, 20), (bar_x, bar_y, bar_width, bar_height), 2)

        # Draw evaluation text
        if abs(eval_score) >= 9000:
            eval_text = "M" + str(abs(eval_score) // 100)
        else:
            eval_text = f"{eval_score / 100:.1f}"

        font = self.tiny_font
        text_color = (255, 200, 0)  # Orange/gold color - visible on both dark and light
        text_surface = font.render(eval_text, True, text_color)
        text_rect = text_surface.get_rect(center=(bar_x + bar_width // 2, bar_y + bar_height // 2))
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

        # Draw evaluation bar (after panel so it's on top)
        self.draw_eval_bar()

        # Draw buttons
        self.start_btn.draw(self.screen, self.font)
        self.prev_btn.draw(self.screen, self.font)
        self.next_btn.draw(self.screen, self.font)
        self.end_btn.draw(self.screen, self.font)
        self.back_btn.draw(self.screen, self.small_font)

    def draw_panel(self):
        """Draw information panel."""
        panel_x = BOARD_SIZE + 50  # Leave space for eval bar

        # Panel background
        panel_rect = pygame.Rect(panel_x, 0, PANEL_WIDTH - 50, SCREEN_HEIGHT)
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
