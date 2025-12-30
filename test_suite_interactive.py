"""
Interactive Chess Engine Test Suite
Visual GUI for testing engines on selected positions with step-by-step move comparison.
Uses Stockfish for dynamic scoring.
"""

import pygame
import chess
import threading
import importlib
import glob
import os
import json
import time
from typing import List, Dict
from collections import defaultdict
from test_suite import TestSuite, TestPosition
from stockfish_analyzer import StockfishAnalyzer

# Initialize pygame
pygame.init()

# Constants
WINDOW_WIDTH = 1200
WINDOW_HEIGHT = 800
BOARD_SIZE = 640
SQUARE_SIZE = 80
PANEL_WIDTH = WINDOW_WIDTH - BOARD_SIZE

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT_CORRECT = (130, 200, 105, 180)  # Green
HIGHLIGHT_WRONG = (231, 76, 60, 180)      # Red
HIGHLIGHT_PARTIAL = (255, 215, 0, 180)    # Yellow
HIGHLIGHT_EXPECTED = (100, 150, 255, 180) # Blue
BUTTON_COLOR = (52, 73, 94)
BUTTON_HOVER = (71, 101, 130)
DROPDOWN_BG = (45, 45, 45)
DROPDOWN_HOVER = (60, 60, 60)
DROPDOWN_SELECTED = (75, 110, 140)
PANEL_BG = (250, 250, 252)
TEXT_COLOR = (50, 50, 50)
HEADER_BG = (38, 38, 38)
HEADER_TEXT = (230, 230, 230)

# Fonts
FONT = pygame.font.SysFont('Arial', 18)
FONT_SMALL = pygame.font.SysFont('Arial', 16)
FONT_TINY = pygame.font.SysFont('Arial', 14)
FONT_TITLE = pygame.font.SysFont('Arial', 24, bold=True)
FONT_LARGE = pygame.font.SysFont('Arial', 32, bold=True)

# Unicode chess pieces
PIECE_UNICODE = {
    'P': '\u2659', 'N': '\u2658', 'B': '\u2657', 'R': '\u2656', 'Q': '\u2655', 'K': '\u2654',
    'p': '\u265F', 'n': '\u265E', 'b': '\u265D', 'r': '\u265C', 'q': '\u265B', 'k': '\u265A',
}


def find_all_engines():
    """Dynamically find all chess engines in the project."""
    engines = []

    # Search in current directory
    for file in glob.glob("engine*.py"):
        if file == "benchmark_engines.py":
            continue
        module_name = file[:-3]
        display_name = format_engine_name(module_name)
        engines.append((module_name, display_name, "local"))

    # Search in engine_pool directory
    if os.path.exists("engine_pool"):
        for file in glob.glob("engine_pool/*.py"):
            if file.endswith("__init__.py"):
                continue
            filename = os.path.basename(file)[:-3]
            module_name = f"engine_pool.{filename}"
            display_name = format_engine_name(filename)
            engines.append((module_name, display_name, "pool"))

    # Sort: prioritize optimized engines
    def sort_key(item):
        module_name, display_name, source = item
        if "optimized" in module_name:
            return (0, display_name)
        elif source == "local" and "v5" in module_name:
            return (1, display_name)
        elif source == "local":
            return (2, display_name)
        else:
            return (3, display_name)

    engines.sort(key=sort_key)
    return engines if engines else [("engine", "Basic Engine", "local")]


def format_engine_name(module_name):
    """Format engine module name for display."""
    name = module_name.replace("engine_pool.", "")

    if "engine_v5_optimized" in name:
        return "V5 Optimized"
    elif "engine_v5_fast" in name:
        return "V5 Fast"
    elif "engine_v5" in name:
        return "V5"
    elif "engine_v4" in name:
        return "V4"
    elif "engine_v3" in name:
        return "V3"
    elif name == "engine":
        return "Basic Engine"
    else:
        return name.replace("_", " ").title()


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


class Dropdown:
    def __init__(self, x, y, width, items, default_index=0, max_visible=10):
        self.rect = pygame.Rect(x, y, width, 40)
        self.items = items
        self.selected_index = default_index
        self.is_open = False
        self.hovered_index = -1
        self.scroll_offset = 0
        self.max_visible = max_visible

    def get_selected(self):
        return self.items[self.selected_index][0]

    def get_dropdown_rect(self):
        item_height = 35
        visible_items = min(len(self.items), self.max_visible)
        return pygame.Rect(self.rect.x, self.rect.y + self.rect.height,
                          self.rect.width, visible_items * item_height)

    def draw(self, screen):
        color = BUTTON_HOVER if self.is_open else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2, border_radius=5)

        _, display_name, source = self.items[self.selected_index]
        source_icon = "" if source == "local" else "P "
        text = FONT_SMALL.render(f"{source_icon}{display_name}", True, WHITE)
        text_rect = text.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        screen.blit(text, text_rect)

        arrow = "v" if not self.is_open else "^"
        arrow_text = FONT_SMALL.render(arrow, True, WHITE)
        arrow_rect = arrow_text.get_rect(midright=(self.rect.right - 10, self.rect.centery))
        screen.blit(arrow_text, arrow_rect)

        if self.is_open:
            dropdown_rect = self.get_dropdown_rect()
            pygame.draw.rect(screen, DROPDOWN_BG, dropdown_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), dropdown_rect, 2, border_radius=5)

            start_idx = self.scroll_offset
            end_idx = min(start_idx + self.max_visible, len(self.items))

            item_height = 35
            for i in range(start_idx, end_idx):
                display_idx = i - start_idx
                item_rect = pygame.Rect(dropdown_rect.x, dropdown_rect.y + display_idx * item_height,
                                       dropdown_rect.width, item_height)

                if i == self.selected_index:
                    pygame.draw.rect(screen, DROPDOWN_SELECTED, item_rect)
                elif i == self.hovered_index:
                    pygame.draw.rect(screen, DROPDOWN_HOVER, item_rect)

                _, display_name, source = self.items[i]
                source_icon = "" if source == "local" else "P "
                item_text = FONT_TINY.render(f"{source_icon}{display_name}", True, WHITE)
                item_text_rect = item_text.get_rect(midleft=(item_rect.x + 10, item_rect.centery))
                screen.blit(item_text, item_text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    self.is_open = not self.is_open
                    if self.is_open:
                        self.scroll_offset = 0
                    return True
                elif self.is_open:
                    dropdown_rect = self.get_dropdown_rect()
                    if dropdown_rect.collidepoint(event.pos):
                        item_height = 35
                        rel_y = event.pos[1] - dropdown_rect.y
                        clicked_idx = self.scroll_offset + (rel_y // item_height)
                        if 0 <= clicked_idx < len(self.items):
                            self.selected_index = clicked_idx
                            self.is_open = False
                            return True
                    else:
                        self.is_open = False
            elif event.button == 4 and self.is_open:
                dropdown_rect = self.get_dropdown_rect()
                if dropdown_rect.collidepoint(event.pos):
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                    return True
            elif event.button == 5 and self.is_open:
                dropdown_rect = self.get_dropdown_rect()
                if dropdown_rect.collidepoint(event.pos):
                    max_scroll = max(0, len(self.items) - self.max_visible)
                    self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                    return True
        elif event.type == pygame.MOUSEMOTION and self.is_open:
            dropdown_rect = self.get_dropdown_rect()
            if dropdown_rect.collidepoint(event.pos):
                item_height = 35
                rel_y = event.pos[1] - dropdown_rect.y
                self.hovered_index = self.scroll_offset + (rel_y // item_height)
            else:
                self.hovered_index = -1
        return False


class TextInput:
    def __init__(self, x, y, width, default_value="1.0", input_type="float"):
        self.rect = pygame.Rect(x, y, width, 40)
        self.text = default_value
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
        self.input_type = input_type

    def get_value(self):
        try:
            if self.input_type == "int":
                val = int(self.text)
                return max(1, min(99, val))
            else:
                val = float(self.text)
                return max(0.1, min(60.0, val))
        except ValueError:
            return 99 if self.input_type == "int" else 1.0

    def draw(self, screen):
        border_color = (100, 150, 255) if self.active else (150, 150, 150)
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, border_color, self.rect, 2)

        text_surface = FONT.render(self.text, True, BLACK)
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))

        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 10 + FONT.size(self.text)[0]
            pygame.draw.line(screen, BLACK,
                           (cursor_x, self.rect.y + 8),
                           (cursor_x, self.rect.y + 32), 2)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        elif event.type == pygame.KEYDOWN and self.active:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.key == pygame.K_RETURN:
                self.active = False
            elif event.unicode.isdigit() or (event.unicode == '.' and self.input_type == "float"):
                self.text += event.unicode


class CategoryCheckbox:
    def __init__(self, name, tests, y_pos):
        self.name = name
        self.tests = tests
        self.y = y_pos
        self.selected = False
        self.expanded = False
        self.test_checkboxes = {test.id: False for test in tests}
        self.rect = pygame.Rect(50, y_pos, 20, 20)
        self.expand_rect = pygame.Rect(950, y_pos, 20, 20)

    def get_selected_tests(self):
        return [t for t in self.tests if self.test_checkboxes[t.id]]

    def draw(self, screen):
        # Category checkbox
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        if self.selected or any(self.test_checkboxes.values()):
            pygame.draw.line(screen, BLACK, (self.rect.x + 3, self.rect.y + 10),
                           (self.rect.x + 8, self.rect.y + 15), 3)
            pygame.draw.line(screen, BLACK, (self.rect.x + 8, self.rect.y + 15),
                           (self.rect.x + 17, self.rect.y + 5), 3)

        # Category name
        name_text = FONT.render(f"{self.name} ({len(self.tests)} tests)", True, TEXT_COLOR)
        screen.blit(name_text, (self.rect.x + 30, self.rect.y))

        # Expand button
        arrow = "v" if not self.expanded else "^"
        arrow_text = FONT_SMALL.render(arrow, True, TEXT_COLOR)
        screen.blit(arrow_text, (self.expand_rect.x, self.expand_rect.y))

        # Draw individual tests if expanded
        if self.expanded:
            for i, test in enumerate(self.tests[:5]):  # Show max 5
                test_y = self.y + 30 + i * 25
                test_rect = pygame.Rect(70, test_y, 15, 15)
                pygame.draw.rect(screen, WHITE, test_rect)
                pygame.draw.rect(screen, BLACK, test_rect, 1)

                if self.test_checkboxes[test.id]:
                    pygame.draw.line(screen, BLACK, (test_rect.x + 2, test_rect.y + 7),
                                   (test_rect.x + 6, test_rect.y + 11), 2)
                    pygame.draw.line(screen, BLACK, (test_rect.x + 6, test_rect.y + 11),
                                   (test_rect.x + 13, test_rect.y + 3), 2)

                test_name = FONT_SMALL.render(test.name[:40], True, TEXT_COLOR)
                screen.blit(test_name, (test_rect.x + 20, test_rect.y))

            if len(self.tests) > 5:
                more_text = FONT_TINY.render(f"... and {len(self.tests) - 5} more", True, (100, 100, 100))
                screen.blit(more_text, (70, self.y + 30 + 5 * 25))

    def handle_event(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Category checkbox
            if self.rect.collidepoint(mouse_pos):
                self.selected = not self.selected
                # Toggle all tests
                for test_id in self.test_checkboxes:
                    self.test_checkboxes[test_id] = self.selected
                return True

            # Expand button
            if self.expand_rect.collidepoint(mouse_pos):
                self.expanded = not self.expanded
                return True

            # Individual test checkboxes
            if self.expanded:
                for i, test in enumerate(self.tests[:5]):
                    test_y = self.y + 30 + i * 25
                    test_rect = pygame.Rect(70, test_y, 15, 15)
                    if test_rect.collidepoint(mouse_pos):
                        self.test_checkboxes[test.id] = not self.test_checkboxes[test.id]
                        return True
        return False


class InteractiveTestSuite:
    def __init__(self):
        self.screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
        pygame.display.set_caption("Interactive Test Suite")

        # Load test suite
        self.test_suite = TestSuite()

        # Organize by category
        self.categories = {}
        y_pos = 200
        for cat_name in ['tactical', 'checkmate', 'endgame', 'positional']:
            tests = [p for p in self.test_suite.positions if p.category == cat_name]
            self.categories[cat_name] = CategoryCheckbox(cat_name.capitalize(), tests, y_pos)
            y_pos += 50

        # Config widgets
        self.engine_dropdown = Dropdown(100, 100, 400, find_all_engines())
        self.depth_input = TextInput(300, 450, 100, "99", "int")
        self.time_input = TextInput(300, 500, 100, "1.0", "float")
        self.run_button = Button(450, 600, 200, 50, "RUN TESTS", self.start_testing)

        # Test screen widgets
        self.next_test_button = Button(BOARD_SIZE + 100, 650, 200, 50, "NEXT TEST", self.advance_to_next_test)

        # Summary screen widgets
        self.save_button = Button(300, 600, 200, 50, "SAVE RESULTS", self.save_results)
        self.new_test_button = Button(520, 600, 200, 50, "NEW TEST", self.reset_to_config)

        # State
        self.current_screen = "config"  # config | testing | summary
        self.selected_tests = []
        self.current_test_index = 0
        self.current_result = None
        self.results = []
        self.display_state = "position"  # position | engine_move | both_moves

        # Load piece font
        self.piece_font = self.load_piece_font()

        # Clock
        self.clock = pygame.time.Clock()

    def load_piece_font(self):
        # Try chess font files
        chess_font_files = ['ChessMerida.ttf', 'ChessAlpha.ttf', 'chess_merida_unicode.ttf']
        for font_file in chess_font_files:
            try:
                font = pygame.font.Font(font_file, 65)
                print(f"Loaded chess font: {font_file}")
                return font
            except:
                continue

        # Try system fonts with chess unicode support
        piece_font_names = ['Segoe UI Symbol', 'Arial Unicode MS', 'DejaVu Sans', 'FreeSans']
        for font_name in piece_font_names:
            try:
                font = pygame.font.SysFont(font_name, 65)
                print(f"Using system font: {font_name}")
                return font
            except:
                continue

        # Final fallback
        print("Using default font - pieces may not display correctly")
        return pygame.font.SysFont(None, 65)

    def start_testing(self):
        # Collect selected tests
        self.selected_tests = []
        for category in self.categories.values():
            self.selected_tests.extend(category.get_selected_tests())

        if not self.selected_tests:
            return  # No tests selected

        # Get config
        self.max_depth = self.depth_input.get_value()
        self.time_limit = self.time_input.get_value()
        self.selected_engine = self.engine_dropdown.get_selected()

        self.current_test_index = 0
        self.results = []
        self.current_screen = "testing"
        self.start_current_test()

    def start_current_test(self):
        self.display_state = "position"
        self.current_result = None
        thread = threading.Thread(target=self.run_test_on_position, daemon=True)
        thread.start()

    def run_test_on_position(self):
        position = self.selected_tests[self.current_test_index]
        board = chess.Board(position.fen)

        try:
            # Initialize Stockfish for this position (auto-detects stockfish-windows-x86-64-avx2.exe)
            with StockfishAnalyzer(depth=20) as stockfish:
                # 1. Get Stockfish's top 3 moves and eval
                sf_analysis = stockfish.analyze(board, top_n=3, verbose=True)
                eval_before = sf_analysis.evaluation
                stockfish_move_uci = sf_analysis.best_move.uci()
                stockfish_move_san = board.san(sf_analysis.best_move)

                # 2. Run engine being tested
                engine_module = importlib.import_module(self.selected_engine)
                engine = engine_module.ChessEngine(max_depth=self.max_depth, time_limit=self.time_limit)

                result = engine.search(board)
                engine_move = result.best_move

                if not engine_move:
                    raise ValueError("Engine returned no move")

                engine_move_uci = engine_move.uci()
                engine_move_san = board.san(engine_move)

                # 3. Check if engine move is in top 3
                move_rank = None
                for move_analysis in sf_analysis.top_moves:
                    if engine_move == move_analysis.move:
                        move_rank = move_analysis.rank
                        break

                # 4. Calculate dynamic score based on move rank
                if move_rank == 1:
                    # Found #1 move - perfect!
                    score_pct = 0.0
                    eval_after = None
                elif move_rank == 2:
                    # Second best move - still very good
                    score_pct = 0.10  # 10% penalty
                    eval_after = None
                elif move_rank == 3:
                    # Third best - acceptable
                    score_pct = 0.15  # 15% penalty
                    eval_after = None
                else:
                    # Not in top 3 - use evaluation-based scoring
                    board_after = board.copy()
                    board_after.push(engine_move)
                    sf_after = stockfish.analyze(board_after)
                    eval_after = sf_after.evaluation

                    if abs(eval_before) < 0.01:
                        score_pct = 0.0 if abs(eval_after) < 0.01 else -100.0
                    else:
                        score_pct = (eval_after / eval_before) - 1

                # 5. Determine status
                abs_score = abs(score_pct)
                if abs_score <= 0.20:
                    status = "EXCELLENT"
                elif abs_score <= 0.50:
                    status = "OK"
                elif abs_score <= 1.00:
                    status = "POOR"
                else:
                    status = "TERRIBLE"

                self.current_result = {
                    'position': position,
                    'stockfish_move': stockfish_move_uci,
                    'stockfish_move_san': stockfish_move_san,
                    'stockfish_eval': eval_before,

                    # NEW: Top moves
                    'stockfish_top_moves': [
                        {
                            'rank': ma.rank,
                            'move_uci': ma.move_uci,
                            'move_san': board.san(ma.move),
                            'centipawn': ma.centipawn,
                            'mate': ma.mate
                        }
                        for ma in sf_analysis.top_moves
                    ] if sf_analysis.top_moves else None,

                    'engine_move': engine_move_uci,
                    'engine_move_san': engine_move_san,
                    'engine_move_rank': move_rank,  # NEW
                    'engine_eval': eval_after,
                    'score_pct': score_pct,
                    'status': status,
                    'time': result.time_spent,
                    'nodes': result.nodes_searched,
                    'depth_reached': result.depth,
                    'max_depth': self.max_depth,

                    # NEW: Verbose stats
                    'stockfish_nodes': sf_analysis.verbose_stats.nodes if sf_analysis.verbose_stats else None,
                    'stockfish_nps': sf_analysis.verbose_stats.nps if sf_analysis.verbose_stats else None,
                }
        except Exception as e:
            self.current_result = {
                'position': position,
                'error': str(e),
                'score_pct': -999.0,
                'status': 'ERROR'
            }

    def advance_to_next_test(self):
        if self.current_result:
            self.results.append(self.current_result)

        self.current_test_index += 1

        if self.current_test_index >= len(self.selected_tests):
            self.current_screen = "summary"
        else:
            self.start_current_test()

    def draw_config_screen(self):
        self.screen.fill(PANEL_BG)

        # Title
        title = FONT_LARGE.render("Interactive Test Suite", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 40))
        self.screen.blit(title, title_rect)

        # Engine selection
        label = FONT.render("Select Engine:", True, TEXT_COLOR)
        self.screen.blit(label, (100, 75))
        self.engine_dropdown.draw(self.screen)

        # Test selection
        label = FONT.render("Select Tests:", True, TEXT_COLOR)
        self.screen.blit(label, (50, 170))

        for category in self.categories.values():
            category.draw(self.screen)

        # Depth and time
        depth_label = FONT.render("Max depth:", True, TEXT_COLOR)
        self.screen.blit(depth_label, (150, 455))
        self.depth_input.draw(self.screen)

        time_label = FONT.render("Time per test:", True, TEXT_COLOR)
        self.screen.blit(time_label, (150, 505))
        self.time_input.draw(self.screen)

        seconds_label = FONT_SMALL.render("seconds", True, (100, 100, 100))
        self.screen.blit(seconds_label, (410, 510))

        # Run button
        self.run_button.draw(self.screen)

    def draw_test_screen(self):
        self.screen.fill(WHITE)

        # Draw board
        if self.current_test_index < len(self.selected_tests):
            position = self.selected_tests[self.current_test_index]
            board = chess.Board(position.fen)
            self.draw_board(board)

        # Draw info panel
        self.draw_test_info_panel()

    def draw_board(self, board):
        # Determine if board should be flipped (Black's perspective)
        flipped = board.turn == chess.BLACK

        # Draw squares
        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE

                if flipped:
                    actual_col = 7 - col
                    actual_row = row
                else:
                    actual_col = col
                    actual_row = 7 - row

                square = chess.square(actual_col, actual_row)

                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

        # Highlight moves
        if self.current_result and self.display_state != "position":
            try:
                engine_move = chess.Move.from_uci(self.current_result['engine_move'])
                status = self.current_result['status']

                if status == 'EXCELLENT':
                    engine_color = HIGHLIGHT_CORRECT
                elif status in ['POOR', 'TERRIBLE']:
                    engine_color = HIGHLIGHT_WRONG
                else:  # OK
                    engine_color = HIGHLIGHT_PARTIAL

                self.highlight_move(engine_move, engine_color, flipped)

                if self.display_state == "both_moves":
                    stockfish_move = chess.Move.from_uci(self.current_result['stockfish_move'])
                    if engine_move != stockfish_move:
                        self.highlight_move(stockfish_move, HIGHLIGHT_EXPECTED, flipped)
            except:
                pass

        # Draw pieces
        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE

                if flipped:
                    actual_col = 7 - col
                    actual_row = row
                else:
                    actual_col = col
                    actual_row = 7 - row

                square = chess.square(actual_col, actual_row)

                piece = board.piece_at(square)
                if piece:
                    piece_char = piece.symbol()
                    piece_unicode = PIECE_UNICODE.get(piece_char, piece_char)

                    if piece.color == chess.WHITE:
                        outline = self.piece_font.render(piece_unicode, True, (50, 50, 50))
                        text_rect = outline.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        for dx, dy in [(-1,-1), (-1,0), (-1,1), (0,-1), (0,1), (1,-1), (1,0), (1,1)]:
                            self.screen.blit(outline, (text_rect.x + dx, text_rect.y + dy))
                        text = self.piece_font.render(piece_unicode, True, (255, 255, 255))
                        self.screen.blit(text, text_rect)
                    else:
                        text = self.piece_font.render(piece_unicode, True, (30, 30, 30))
                        text_rect = text.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        self.screen.blit(text, text_rect)

        # Draw coordinates
        coord_font = pygame.font.SysFont('Arial', 14, bold=True)
        for i in range(8):
            if flipped:
                file_label = chr(ord('h') - i)
                rank_label = str(i + 1)
            else:
                file_label = chr(ord('a') + i)
                rank_label = str(8 - i)

            # Files (a-h) at bottom
            text = coord_font.render(file_label, True, (100, 100, 100))
            self.screen.blit(text, (i * SQUARE_SIZE + SQUARE_SIZE - 15, BOARD_SIZE - 15))

            # Ranks (1-8) on left
            text = coord_font.render(rank_label, True, (100, 100, 100))
            self.screen.blit(text, (5, i * SQUARE_SIZE + 5))

    def highlight_move(self, move, color, flipped=False):
        for square in [move.from_square, move.to_square]:
            file = chess.square_file(square)
            rank = chess.square_rank(square)

            if flipped:
                col = 7 - file
                row = rank
            else:
                col = file
                row = 7 - rank

            x = col * SQUARE_SIZE
            y = row * SQUARE_SIZE

            s = pygame.Surface((SQUARE_SIZE, SQUARE_SIZE))
            s.set_alpha(180)
            s.fill(color[:3])
            self.screen.blit(s, (x, y))

    def draw_test_info_panel(self):
        panel_x = BOARD_SIZE

        # Background
        pygame.draw.rect(self.screen, PANEL_BG, (panel_x, 0, PANEL_WIDTH, WINDOW_HEIGHT))

        # Header
        pygame.draw.rect(self.screen, HEADER_BG, (panel_x, 0, PANEL_WIDTH, 60))
        title = FONT_TITLE.render(f"Test {self.current_test_index + 1}/{len(self.selected_tests)}", True, HEADER_TEXT)
        self.screen.blit(title, (panel_x + 20, 20))

        y = 80

        if self.current_test_index < len(self.selected_tests):
            position = self.selected_tests[self.current_test_index]

            # Test name
            name = FONT.render(position.name, True, TEXT_COLOR)
            self.screen.blit(name, (panel_x + 20, y))
            y += 30

            # Category
            cat = FONT_SMALL.render(f"Category: {position.category.capitalize()}", True, TEXT_COLOR)
            self.screen.blit(cat, (panel_x + 20, y))
            y += 40

            # Results
            if self.current_result:
                if 'error' in self.current_result:
                    error = FONT_SMALL.render(f"Error: {self.current_result['error']}", True, (200, 0, 0))
                    self.screen.blit(error, (panel_x + 20, y))
                else:
                    # Stockfish best
                    sf_label = FONT_SMALL.render("Stockfish Best:", True, (100, 100, 100))
                    self.screen.blit(sf_label, (panel_x + 20, y))
                    y += 20

                    sf_move = FONT.render(f"{self.current_result['stockfish_move_san']} ({self.current_result['stockfish_eval']:+.2f})", True, (100, 150, 255))
                    self.screen.blit(sf_move, (panel_x + 30, y))
                    y += 30

                    # Engine move
                    eng_label = FONT_SMALL.render("Engine Move:", True, (100, 100, 100))
                    self.screen.blit(eng_label, (panel_x + 20, y))
                    y += 20

                    status = self.current_result['status']
                    status_colors = {
                        'EXCELLENT': (46, 125, 50),
                        'OK': (245, 127, 23),
                        'POOR': (183, 28, 28),
                        'TERRIBLE': (139, 0, 0),
                        'ERROR': (200, 0, 0)
                    }
                    color = status_colors.get(status, TEXT_COLOR)
                    symbols = {'EXCELLENT': '✓', 'OK': '~', 'POOR': '✗', 'TERRIBLE': '✗✗', 'ERROR': '!'}
                    symbol = symbols.get(status, '?')

                    # Display engine move with eval or rank
                    engine_eval = self.current_result.get('engine_eval')
                    move_rank = self.current_result.get('engine_move_rank')

                    if move_rank is not None and move_rank <= 3:
                        # In top 3, show rank instead of eval
                        eng_move_text = f"{self.current_result['engine_move_san']} (Rank #{move_rank})"
                    elif engine_eval is not None:
                        # Not in top 3, show eval after move
                        eng_move_text = f"{self.current_result['engine_move_san']} ({engine_eval:+.2f})"
                    else:
                        # Fallback
                        eng_move_text = f"{self.current_result['engine_move_san']}"

                    eng_move = FONT.render(eng_move_text, True, color)
                    self.screen.blit(eng_move, (panel_x + 30, y))
                    y += 30

                    # Score
                    score_pct = self.current_result.get('score_pct', 0)
                    score_text = FONT.render(f"Score: {score_pct:+.1%} {symbol} {status}", True, color)
                    self.screen.blit(score_text, (panel_x + 20, y))
                    y += 30

                    # Depth
                    depth = FONT_SMALL.render(f"Depth: {self.current_result['depth_reached']} (max: {self.current_result['max_depth']})", True, TEXT_COLOR)
                    self.screen.blit(depth, (panel_x + 20, y))
                    y += 22

                    # Time and nodes
                    time_nodes = FONT_SMALL.render(f"Time: {self.current_result['time']:.2f}s  Nodes: {self.current_result['nodes']:,}", True, TEXT_COLOR)
                    self.screen.blit(time_nodes, (panel_x + 20, y))
                    y += 40
            else:
                calc = FONT.render("Analyzing with Stockfish...", True, (100, 100, 100))
                self.screen.blit(calc, (panel_x + 20, y))
                y += 40

            # Navigation
            y = 550
            nav_label = FONT_SMALL.render("Navigation:", True, (100, 100, 100))
            self.screen.blit(nav_label, (panel_x + 20, y))
            y += 25

            help1 = FONT_SMALL.render("< > arrows: Navigate", True, TEXT_COLOR)
            help2 = FONT_SMALL.render("ESC: Next test", True, TEXT_COLOR)
            self.screen.blit(help1, (panel_x + 30, y))
            y += 20
            self.screen.blit(help2, (panel_x + 30, y))

            # Next button
            self.next_test_button.draw(self.screen)

    def draw_summary_screen(self):
        self.screen.fill(PANEL_BG)

        # Calculate stats - filter out errors and compute average
        valid_results = [r for r in self.results if 'error' not in r]
        error_count = len(self.results) - len(valid_results)

        if valid_results:
            avg_score_pct = sum(abs(r['score_pct']) for r in valid_results) / len(valid_results)
            # Convert to 0-100 scale (lower is better, capped at 100%)
            pct = max(0, 100 - (avg_score_pct * 100))
        else:
            pct = 0.0

        # Title
        title = FONT_LARGE.render("Test Suite Results", True, TEXT_COLOR)
        title_rect = title.get_rect(center=(WINDOW_WIDTH // 2, 60))
        self.screen.blit(title, title_rect)

        # Total score
        from collections import defaultdict
        status_counts = defaultdict(int)
        for r in self.results:
            status_counts[r['status']] += 1

        score_text = FONT_TITLE.render(f"Overall Score: {pct:.1f}%", True, TEXT_COLOR)
        score_rect = score_text.get_rect(center=(WINDOW_WIDTH // 2, 120))
        self.screen.blit(score_text, score_rect)

        # Show test counts by status
        counts_text = FONT.render(
            f"Excellent: {status_counts['EXCELLENT']}  OK: {status_counts['OK']}  "
            f"Poor: {status_counts['POOR']}  Terrible: {status_counts['TERRIBLE']}  "
            f"Errors: {status_counts['ERROR']}",
            True, (100, 100, 100)
        )
        counts_rect = counts_text.get_rect(center=(WINDOW_WIDTH // 2, 155))
        self.screen.blit(counts_text, counts_rect)

        # Category breakdown
        category_stats = defaultdict(lambda: {
            'valid_scores': [],
            'excellent': 0,
            'ok': 0,
            'poor': 0,
            'terrible': 0,
            'error': 0
        })

        for result in self.results:
            cat = result['position'].category
            status = result['status']

            # Track status counts
            if status == 'EXCELLENT':
                category_stats[cat]['excellent'] += 1
            elif status == 'OK':
                category_stats[cat]['ok'] += 1
            elif status == 'POOR':
                category_stats[cat]['poor'] += 1
            elif status == 'TERRIBLE':
                category_stats[cat]['terrible'] += 1
            elif status == 'ERROR':
                category_stats[cat]['error'] += 1

            # Collect valid scores for average
            if 'error' not in result:
                category_stats[cat]['valid_scores'].append(abs(result['score_pct']))

        y = 200
        label = FONT.render("Category Breakdown:", True, TEXT_COLOR)
        self.screen.blit(label, (200, y))
        y += 40

        for cat, stats in sorted(category_stats.items()):
            # Calculate category percentage
            if stats['valid_scores']:
                avg_score = sum(stats['valid_scores']) / len(stats['valid_scores'])
                cat_pct = max(0, 100 - (avg_score * 100))
            else:
                cat_pct = 0.0

            total_tests = (stats['excellent'] + stats['ok'] + stats['poor'] +
                          stats['terrible'] + stats['error'])
            good_tests = stats['excellent'] + stats['ok']

            icon = "✓" if cat_pct >= 70 else "~" if cat_pct >= 50 else "✗"

            cat_line = FONT.render(
                f"{icon} {cat.capitalize()}: {cat_pct:.1f}% ({good_tests}/{total_tests} good)",
                True, TEXT_COLOR
            )
            self.screen.blit(cat_line, (220, y))
            y += 25

            detail = FONT_SMALL.render(
                f"Excellent: {stats['excellent']}, OK: {stats['ok']}, "
                f"Poor: {stats['poor']}, Terrible: {stats['terrible']}, "
                f"Errors: {stats['error']}",
                True, (100, 100, 100)
            )
            self.screen.blit(detail, (240, y))
            y += 35

        # Buttons
        self.save_button.draw(self.screen)
        self.new_test_button.draw(self.screen)

    def save_results(self):
        filename = f"test_results_{self.selected_engine.replace('/', '_')}_{int(time.time())}.json"
        with open(filename, 'w') as f:
            json.dump({
                'engine': self.selected_engine,
                'max_depth': self.max_depth,
                'time_limit': self.time_limit,
                'results': [
                    {
                        'test_id': r['position'].id,
                        'test_name': r['position'].name,
                        'category': r['position'].category,
                        'score_pct': r['score_pct'],
                        'status': r['status'],
                        'engine_move': r.get('engine_move', 'none'),
                        'engine_move_san': r.get('engine_move_san', 'none'),
                        'stockfish_move': r.get('stockfish_move', 'none'),
                        'stockfish_move_san': r.get('stockfish_move_san', 'none'),
                        'stockfish_eval': r.get('stockfish_eval', 0.0),
                        'engine_eval': r.get('engine_eval', 0.0),
                        'time': r.get('time', 0),
                        'nodes': r.get('nodes', 0),
                        'depth': r.get('depth_reached', 0),
                        'error': r.get('error', None)
                    } for r in self.results
                ]
            }, f, indent=2)
        print(f"Results saved to {filename}")

    def reset_to_config(self):
        self.current_screen = "config"
        self.selected_tests = []
        self.current_test_index = 0
        self.results = []
        self.current_result = None

    def handle_event(self, event):
        if self.current_screen == "config":
            if self.engine_dropdown.handle_event(event):
                return
            if self.depth_input.handle_event(event):
                return
            if self.time_input.handle_event(event):
                return
            if self.run_button.handle_event(event):
                return

            mouse_pos = pygame.mouse.get_pos()
            for category in self.categories.values():
                if category.handle_event(event, mouse_pos):
                    return

        elif self.current_screen == "testing":
            # Handle button clicks
            if self.next_test_button.handle_event(event):
                return

            # Handle keyboard
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    if self.display_state == "position" and self.current_result:
                        self.display_state = "engine_move"
                    elif self.display_state == "engine_move":
                        self.display_state = "both_moves"
                elif event.key == pygame.K_LEFT:
                    if self.display_state == "both_moves":
                        self.display_state = "engine_move"
                    elif self.display_state == "engine_move":
                        self.display_state = "position"
                elif event.key == pygame.K_ESCAPE:
                    self.advance_to_next_test()

        elif self.current_screen == "summary":
            # Handle button clicks
            if self.save_button.handle_event(event):
                return
            if self.new_test_button.handle_event(event):
                return

    def run(self):
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                else:
                    self.handle_event(event)

            # Update cursor blink
            self.depth_input.cursor_timer += self.clock.get_time()
            if self.depth_input.cursor_timer > 500:
                self.depth_input.cursor_visible = not self.depth_input.cursor_visible
                self.depth_input.cursor_timer = 0

            self.time_input.cursor_timer += self.clock.get_time()
            if self.time_input.cursor_timer > 500:
                self.time_input.cursor_visible = not self.time_input.cursor_visible
                self.time_input.cursor_timer = 0

            # Draw current screen
            if self.current_screen == "config":
                self.draw_config_screen()
            elif self.current_screen == "testing":
                self.draw_test_screen()
            elif self.current_screen == "summary":
                self.draw_summary_screen()

            pygame.display.flip()
            self.clock.tick(30)

        pygame.quit()


if __name__ == "__main__":
    app = InteractiveTestSuite()
    app.run()
