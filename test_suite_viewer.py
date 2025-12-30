"""
Chess Engine Test Suite Viewer
Visual interface to see test positions and engine results on a chess board.
"""

import pygame
import chess
import sys
import argparse
import time
import threading
from test_suite import TestSuite

# Initialize pygame
pygame.init()

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_CORRECT = (130, 200, 105)  # Green for correct
HIGHLIGHT_WRONG = (231, 76, 60)     # Red for wrong
HIGHLIGHT_PARTIAL = (255, 215, 0)   # Yellow for partial
PANEL_BG = (250, 250, 252)
TEXT_COLOR = (50, 50, 50)
HEADER_BG = (38, 38, 38)
HEADER_TEXT = (230, 230, 230)

# Board settings
SQUARE_SIZE = 80
BOARD_SIZE = SQUARE_SIZE * 8
PANEL_WIDTH = 460
WINDOW_WIDTH = BOARD_SIZE + PANEL_WIDTH
WINDOW_HEIGHT = 720

# Fonts
pygame.font.init()
FONT = pygame.font.SysFont('Arial', 18)
FONT_SMALL = pygame.font.SysFont('Arial', 16)
FONT_TITLE = pygame.font.SysFont('Arial', 24, bold=True)
FONT_LARGE = pygame.font.SysFont('Arial', 32, bold=True)
FONT_HEADER = pygame.font.SysFont('Arial', 20, bold=True)

# Unicode chess pieces
PIECE_UNICODE = {
    'P': '\u2659', 'N': '\u2658', 'B': '\u2657', 'R': '\u2656', 'Q': '\u2655', 'K': '\u2654',
    'p': '\u265F', 'n': '\u265E', 'b': '\u265D', 'r': '\u265C', 'q': '\u265B', 'k': '\u265A',
}


def load_piece_font():
    """Load chess piece font."""
    # Try loading chess font files
    chess_font_files = ['ChessMerida.ttf', 'ChessAlpha.ttf', 'chess_merida_unicode.ttf']
    for font_file in chess_font_files:
        try:
            font = pygame.font.Font(font_file, 65)
            print(f"Loaded chess font: {font_file}")
            return font
        except:
            continue

    # Fall back to system fonts
    piece_font_names = ['Segoe UI Symbol', 'Arial Unicode MS', 'DejaVu Sans', 'FreeSans']
    for font_name in piece_font_names:
        try:
            return pygame.font.SysFont(font_name, 65)
        except:
            continue

    return pygame.font.SysFont(None, 65)


class TestSuiteViewer:
    """Visual test suite viewer."""

    def __init__(self, engine_name, depth=6, time_limit=2.0):
        self.engine_name = engine_name
        self.depth = depth
        self.time_limit = time_limit

        # Setup display - center on screen
        import os
        os.environ['SDL_VIDEO_CENTERED'] = '1'
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption(f"Test Suite - {engine_name}")
        print(f"\n{'='*60}")
        print(f"GUI WINDOW OPENED - Look for 'Test Suite - {engine_name}'")
        print(f"Window size: {WINDOW_WIDTH}x{WINDOW_HEIGHT}")
        print(f"{'='*60}\n")

        # Load piece font
        self.piece_font = load_piece_font()

        # Load test suite
        self.test_suite = TestSuite()
        self.positions = self.test_suite.positions

        # State
        self.current_index = 0
        self.results = None
        self.test_results = []
        self.is_running = False
        self.is_paused = False
        self.show_summary = False
        self.test_thread = None

        # Clock
        self.clock = pygame.time.Clock()

    def draw_board(self, board: chess.Board, highlight_squares=None, highlight_color=None):
        """Draw chess board with pieces."""
        # Draw squares
        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE

                actual_col = col
                actual_row = 7 - row
                square = chess.square(actual_col, actual_row)

                # Base color
                if (row + col) % 2 == 0:
                    color = LIGHT_SQUARE
                else:
                    color = DARK_SQUARE

                # Highlight squares
                if highlight_squares and square in highlight_squares and highlight_color:
                    color = highlight_color

                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # Draw pieces
        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE

                actual_col = col
                actual_row = 7 - row
                square = chess.square(actual_col, actual_row)

                piece = board.piece_at(square)
                if piece:
                    piece_symbol = piece.symbol()
                    piece_unicode = PIECE_UNICODE.get(piece_symbol, piece_symbol)

                    # White pieces: outline + white fill
                    if piece.color == chess.WHITE:
                        outline_surface = self.piece_font.render(piece_unicode, True, (50, 50, 50))
                        text_rect = outline_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                            self.screen.blit(outline_surface, (text_rect.x + dx, text_rect.y + dy))
                        text_surface = self.piece_font.render(piece_unicode, True, (255, 255, 255))
                        self.screen.blit(text_surface, text_rect)
                    else:
                        text_surface = self.piece_font.render(piece_unicode, True, (30, 30, 30))
                        text_rect = text_surface.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        self.screen.blit(text_surface, text_rect)

        # Draw coordinates
        coord_font = pygame.font.SysFont('Arial', 14, bold=True)
        for i in range(8):
            file_label = chr(ord('a') + i)
            rank_label = str(8 - i)

            # Files (a-h)
            text = coord_font.render(file_label, True, TEXT_COLOR)
            self.screen.blit(text, (i * SQUARE_SIZE + SQUARE_SIZE - 15, BOARD_SIZE - 15))

            # Ranks (1-8)
            text = coord_font.render(rank_label, True, TEXT_COLOR)
            self.screen.blit(text, (5, i * SQUARE_SIZE + 5))

    def draw_info_panel(self):
        """Draw information panel."""
        panel_x = BOARD_SIZE
        panel_width = PANEL_WIDTH

        # Panel background
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, 0, panel_width, WINDOW_HEIGHT))

        # Header
        pygame.draw.rect(self.screen, HEADER_BG, (panel_x, 0, panel_width, 60))
        title = FONT_HEADER.render(f"Test Suite", True, HEADER_TEXT)
        engine = FONT_SMALL.render(f"{self.engine_name}", True, (150, 150, 150))
        self.screen.blit(title, (panel_x + 20, 12))
        self.screen.blit(engine, (panel_x + 20, 38))

        # Status indicator
        if self.is_running:
            if self.is_paused:
                status = FONT_SMALL.render("PAUSED", True, (255, 193, 7))
                pygame.draw.circle(self.screen, (255, 193, 7), (panel_x + panel_width - 40, 30), 5)
            else:
                status = FONT_SMALL.render("RUNNING", True, (76, 175, 80))
                pygame.draw.circle(self.screen, (76, 175, 80), (panel_x + panel_width - 40, 30), 5)
            status_rect = status.get_rect(right=panel_x + panel_width - 50, centery=30)
            self.screen.blit(status, status_rect)

        y = 80

        if self.show_summary:
            self.draw_summary(panel_x, y)
        elif self.current_index < len(self.positions):
            pos = self.positions[self.current_index]
            result = self.test_results[self.current_index] if self.current_index < len(self.test_results) else None

            # Test info
            test_id = FONT_TITLE.render(f"{pos.name}", True, TEXT_COLOR)
            self.screen.blit(test_id, (panel_x + 20, y))
            y += 35

            # Category and difficulty
            cat_text = FONT_SMALL.render(f"Category: {pos.category.capitalize()}", True, TEXT_COLOR)
            diff_text = FONT_SMALL.render(f"Difficulty: {pos.difficulty.capitalize()}", True, TEXT_COLOR)
            pts_text = FONT_SMALL.render(f"Points: {pos.points}", True, TEXT_COLOR)
            self.screen.blit(cat_text, (panel_x + 20, y))
            self.screen.blit(diff_text, (panel_x + 20, y + 22))
            self.screen.blit(pts_text, (panel_x + 20, y + 44))
            y += 80

            # Separator
            pygame.draw.line(self.screen, (200, 200, 200), (panel_x + 20, y), (panel_x + panel_width - 20, y), 1)
            y += 15

            # Expected moves
            expected_label = FONT_SMALL.render("Expected:", True, (100, 100, 100))
            self.screen.blit(expected_label, (panel_x + 20, y))
            y += 25

            # Convert UCI to SAN
            board = chess.Board(pos.fen)
            for i, move_uci in enumerate(pos.best_moves[:3]):  # Show max 3
                try:
                    move = chess.Move.from_uci(move_uci)
                    move_san = board.san(move)
                except:
                    move_san = move_uci
                move_text = FONT.render(f"• {move_san}", True, TEXT_COLOR)
                self.screen.blit(move_text, (panel_x + 30, y))
                y += 25

            y += 10

            # Engine's move (if tested)
            if result:
                engine_label = FONT_SMALL.render("Engine chose:", True, (100, 100, 100))
                self.screen.blit(engine_label, (panel_x + 20, y))
                y += 25

                move_san = result.get('engine_move_san', result.get('engine_move', 'N/A'))
                status = result.get('status', 'UNKNOWN')
                status_colors = {'PASS': (46, 125, 50), 'FAIL': (183, 28, 28), 'PARTIAL': (245, 127, 23)}
                status_color = status_colors.get(status, TEXT_COLOR)

                move_text = FONT.render(f"{move_san}", True, status_color)
                self.screen.blit(move_text, (panel_x + 30, y))
                y += 30

                # Status
                status_symbols = {'PASS': '✓', 'FAIL': '✗', 'PARTIAL': '~'}
                symbol = status_symbols.get(status, '?')
                status_text = FONT_TITLE.render(f"{symbol} {status}", True, status_color)
                self.screen.blit(status_text, (panel_x + 30, y))
                y += 40

                # Score
                score_text = FONT.render(f"Score: {result['score']}/{result['max']}", True, TEXT_COLOR)
                self.screen.blit(score_text, (panel_x + 30, y))
                y += 30

            y += 20

            # Separator
            pygame.draw.line(self.screen, (200, 200, 200), (panel_x + 20, y), (panel_x + panel_width - 20, y), 1)
            y += 15

            # Description (wrapped)
            desc_label = FONT_SMALL.render("Description:", True, (100, 100, 100))
            self.screen.blit(desc_label, (panel_x + 20, y))
            y += 25

            # Wrap description text
            desc_words = pos.description.split()
            line = ""
            for word in desc_words:
                test_line = line + word + " "
                if FONT_SMALL.size(test_line)[0] > panel_width - 60:
                    text = FONT_SMALL.render(line, True, TEXT_COLOR)
                    self.screen.blit(text, (panel_x + 30, y))
                    y += 20
                    line = word + " "
                else:
                    line = test_line
            if line:
                text = FONT_SMALL.render(line, True, TEXT_COLOR)
                self.screen.blit(text, (panel_x + 30, y))
                y += 30

            # Progress
            y = WINDOW_HEIGHT - 120
            progress_label = FONT_SMALL.render("Progress:", True, (100, 100, 100))
            self.screen.blit(progress_label, (panel_x + 20, y))
            y += 25

            progress_text = FONT.render(f"{self.current_index + 1} / {len(self.positions)}", True, TEXT_COLOR)
            self.screen.blit(progress_text, (panel_x + 30, y))
            y += 30

            # Overall score (if available)
            if self.test_results:
                total_score = sum(r.get('score', 0) for r in self.test_results)
                max_score = sum(r.get('max', 0) for r in self.test_results)
                pct = (total_score / max_score * 100) if max_score > 0 else 0
                overall_text = FONT_SMALL.render(f"Overall: {total_score}/{max_score} ({pct:.0f}%)", True, TEXT_COLOR)
                self.screen.blit(overall_text, (panel_x + 30, y))

            # Controls help text at bottom
            y = WINDOW_HEIGHT - 80
            pygame.draw.line(self.screen, (200, 200, 200), (panel_x + 20, y), (panel_x + panel_width - 20, y), 1)
            y += 10
            help_label = FONT_SMALL.render("Controls:", True, (100, 100, 100))
            self.screen.blit(help_label, (panel_x + 20, y))
            y += 22
            help1 = FONT_SMALL.render("SPACE: Pause/Resume", True, TEXT_COLOR)
            help2 = FONT_SMALL.render("LEFT/RIGHT: Navigate", True, TEXT_COLOR)
            help3 = FONT_SMALL.render("R: Restart  ESC: Exit", True, TEXT_COLOR)
            self.screen.blit(help1, (panel_x + 30, y))
            y += 18
            self.screen.blit(help2, (panel_x + 30, y))
            y += 18
            self.screen.blit(help3, (panel_x + 30, y))

    def draw_summary(self, panel_x, y):
        """Draw final summary screen."""
        if not self.results:
            return

        # Title
        summary_title = FONT_LARGE.render("Final Results", True, TEXT_COLOR)
        self.screen.blit(summary_title, (panel_x + 80, y))
        y += 60

        # Overall score
        total_pct = (self.results['total_score'] / self.results['max_score'] * 100) if self.results['max_score'] > 0 else 0
        score_color = (46, 125, 50) if total_pct >= 70 else (245, 127, 23) if total_pct >= 50 else (183, 28, 28)

        overall_text = FONT_TITLE.render(f"{self.results['total_score']}/{self.results['max_score']}", True, score_color)
        pct_text = FONT_LARGE.render(f"{total_pct:.0f}%", True, score_color)
        self.screen.blit(overall_text, (panel_x + 160, y))
        self.screen.blit(pct_text, (panel_x + 170, y + 35))
        y += 90

        # Category breakdown
        cat_label = FONT_SMALL.render("Category Breakdown:", True, (100, 100, 100))
        self.screen.blit(cat_label, (panel_x + 20, y))
        y += 30

        for category, scores in sorted(self.results['category_scores'].items()):
            cat_pct = (scores['score'] / scores['max'] * 100) if scores['max'] > 0 else 0
            status_icon = "✓" if cat_pct >= 70 else "~" if cat_pct >= 50 else "✗"
            cat_color = (46, 125, 50) if cat_pct >= 70 else (245, 127, 23) if cat_pct >= 50 else (183, 28, 28)

            cat_text = FONT_SMALL.render(f"{status_icon} {category.capitalize()}", True, cat_color)
            score_text = FONT_SMALL.render(f"{scores['score']}/{scores['max']} ({cat_pct:.0f}%)", True, cat_color)

            self.screen.blit(cat_text, (panel_x + 30, y))
            self.screen.blit(score_text, (panel_x + 200, y))
            y += 25

        y += 30

        # Instructions
        inst_text = FONT_SMALL.render("Press 'R' to restart", True, (100, 100, 100))
        inst_text2 = FONT_SMALL.render("Press 'S' to save results", True, (100, 100, 100))
        inst_text3 = FONT_SMALL.render("Press 'ESC' to exit", True, (100, 100, 100))
        self.screen.blit(inst_text, (panel_x + 30, y))
        self.screen.blit(inst_text2, (panel_x + 30, y + 25))
        self.screen.blit(inst_text3, (panel_x + 30, y + 50))

    def run_tests_thread(self):
        """Run tests in background thread."""
        self.is_running = True
        self.results = self.test_suite.run_engine_test(
            self.engine_name,
            depth=self.depth,
            time_limit=self.time_limit,
            verbose=True
        )

        if self.results:
            self.test_results = self.results['position_results']

        self.is_running = False
        self.show_summary = True

    def start_tests(self):
        """Start test suite."""
        self.current_index = 0
        self.test_results = []
        self.show_summary = False

        # Start thread
        self.test_thread = threading.Thread(target=self.run_tests_thread, daemon=True)
        self.test_thread.start()

    def run(self):
        """Main loop."""
        # Start tests automatically
        self.start_tests()

        running = True
        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    elif event.key == pygame.K_SPACE:
                        self.is_paused = not self.is_paused
                    elif event.key == pygame.K_LEFT and not self.is_running:
                        self.current_index = max(0, self.current_index - 1)
                    elif event.key == pygame.K_RIGHT and not self.is_running:
                        self.current_index = min(len(self.positions) - 1, self.current_index + 1)
                    elif event.key == pygame.K_r:
                        self.start_tests()
                    elif event.key == pygame.K_s and self.results:
                        # Save results
                        import json
                        filename = f"test_results_{self.engine_name}_{int(time.time())}.json"
                        with open(filename, 'w') as f:
                            json.dump(self.results, f, indent=2)
                        print(f"Results saved to {filename}")

            # Update current index during test run
            if self.is_running and not self.is_paused:
                if len(self.test_results) > self.current_index:
                    # Update current index immediately when new results available
                    self.current_index = len(self.test_results) - 1
            elif not self.is_running and len(self.test_results) > 0:
                # Tests finished, show last position
                if self.current_index < len(self.test_results) - 1:
                    self.current_index = len(self.test_results) - 1

            # Draw everything
            self.screen.fill(WHITE)

            # Draw board
            if self.current_index < len(self.positions):
                pos = self.positions[self.current_index]
                board = chess.Board(pos.fen)

                # Highlight squares if result is available
                highlight_squares = None
                highlight_color = None
                if self.current_index < len(self.test_results):
                    result = self.test_results[self.current_index]
                    status = result.get('status', 'UNKNOWN')
                    if status == 'PASS':
                        highlight_color = HIGHLIGHT_CORRECT
                    elif status == 'FAIL':
                        highlight_color = HIGHLIGHT_WRONG
                    else:
                        highlight_color = HIGHLIGHT_PARTIAL

                    # Highlight the move
                    try:
                        move = chess.Move.from_uci(result['engine_move'])
                        highlight_squares = [move.from_square, move.to_square]
                    except:
                        pass

                self.draw_board(board, highlight_squares, highlight_color)

            # Draw info panel
            self.draw_info_panel()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description='Visual test suite for chess engines')
    parser.add_argument('engine', help='Engine module name (e.g., engine_v5)')
    parser.add_argument('--depth', type=int, default=6, help='Search depth (default: 6)')
    parser.add_argument('--time', type=float, default=2.0, help='Time limit per position (default: 2.0s)')

    args = parser.parse_args()

    viewer = TestSuiteViewer(args.engine, args.depth, args.time)
    viewer.run()


if __name__ == "__main__":
    main()
