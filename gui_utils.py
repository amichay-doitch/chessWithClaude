"""
Shared GUI utilities for chess applications.

This module consolidates widgets, rendering logic, and common UI code
used across all chess GUI applications.
"""

import pygame
import chess
import glob
import os
from typing import List, Tuple, Optional


# ============================================================================
# COLOR CONSTANTS
# ============================================================================

# Board colors - Polished chess.com style
LIGHT_SQUARE = (240, 217, 181)   # Warm cream
DARK_SQUARE = (181, 136, 99)     # Warm brown
HIGHLIGHT = (130, 151, 105)      # Soft green for legal moves
SELECTED = (246, 246, 105)       # Bright yellow for selected
LAST_MOVE = (170, 162, 58)       # Golden yellow for last move
CHECK_COLOR = (231, 76, 60)      # Bright red for check

# UI colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
TEXT_COLOR = (50, 50, 50)
PANEL_BG = (38, 38, 38)          # Darker panel background
PANEL_TEXT = (230, 230, 230)     # Light text on dark panel

# Button colors
BUTTON_COLOR = (52, 73, 94)      # Dark blue-gray
BUTTON_HOVER = (71, 101, 130)    # Lighter blue on hover

# Dropdown colors
DROPDOWN_BG = (45, 45, 45)
DROPDOWN_HOVER = (60, 60, 60)
DROPDOWN_SELECTED = (75, 110, 140)

# Move indicators
MOVE_DOT = (80, 80, 80, 180)     # Semi-transparent dots for legal moves
CAPTURE_RING = (80, 80, 80, 200) # Semi-transparent ring for captures


# ============================================================================
# PIECE UNICODE
# ============================================================================

PIECE_UNICODE = {
    'P': '\u2659', 'N': '\u2658', 'B': '\u2657',
    'R': '\u2656', 'Q': '\u2655', 'K': '\u2654',
    'p': '\u265F', 'n': '\u265E', 'b': '\u265D',
    'r': '\u265C', 'q': '\u265B', 'k': '\u265A',
}


# ============================================================================
# ENGINE DISCOVERY UTILITIES
# ============================================================================

def find_all_engines() -> List[Tuple[str, str, str]]:
    """
    Dynamically find all chess engines in the project.

    Returns:
        List of tuples (module_name, display_name, source)
        where source is either "local" or "pool"
    """
    engines = []

    # Search in current directory
    for file in glob.glob("engine*.py"):
        if file == "benchmark_engines.py":  # Skip utility files
            continue
        module_name = file[:-3]
        display_name = format_engine_name(module_name)
        engines.append((module_name, display_name, "local"))

    # Search in engine_pool directory
    if os.path.exists("engine_pool"):
        for file in glob.glob("engine_pool/*.py"):
            if file.endswith("__init__.py"):
                continue
            # Get just the filename without path
            filename = os.path.basename(file)[:-3]
            module_name = f"engine_pool.{filename}"
            display_name = format_engine_name(filename)
            engines.append((module_name, display_name, "pool"))

    # Sort: prioritize optimized local engines, then others
    def sort_key(item):
        module_name, display_name, source = item
        if "optimized" in module_name:
            return (0, display_name)
        elif source == "local" and "v5" in module_name:
            return (1, display_name)
        elif source == "local":
            return (2, display_name)
        else:  # pool engines
            return (3, display_name)

    engines.sort(key=sort_key)
    return engines if engines else [("engine", "Basic Engine", "local")]


def format_engine_name(module_name: str) -> str:
    """
    Format engine module name for display.

    Args:
        module_name: Engine module name (e.g., "engine_v5", "engine_pool.engine_v4")

    Returns:
        Formatted display name
    """
    # Remove engine_pool prefix if present
    name = module_name.replace("engine_pool.", "")

    # Special formatting for known engines
    if "engine_v5_optimized" in name:
        return "⚡ V5 Optimized (FASTEST)"
    elif "engine_v5_fast" in name:
        return "V5 Fast"
    elif "engine_v5" in name:
        return "V5 (Best)"
    elif "engine_v4" in name:
        return "V4"
    elif "engine_v3" in name:
        return "V3"
    elif "engine_fast" in name:
        return "Fast Engine"
    elif name == "engine":
        return "Basic Engine"
    else:
        # Capitalize pool engines
        return name.replace("_", " ").title()


# ============================================================================
# WIDGETS
# ============================================================================

class Button:
    """Reusable button widget."""

    def __init__(self, x: int, y: int, width: int, height: int, text: str, color_or_callback=None):
        """
        Create a button.

        Args:
            x, y: Position
            width, height: Size
            text: Button label
            color_or_callback: Either a color tuple (R,G,B) or a callback function (optional)
        """
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.hovered = False
        self.enabled = True

        # Determine if color_or_callback is a color or callback
        if color_or_callback is None:
            self.color = BUTTON_COLOR
            self.callback = None
        elif callable(color_or_callback):
            self.color = BUTTON_COLOR
            self.callback = color_or_callback
        else:
            # It's a color tuple
            self.color = color_or_callback
            self.callback = None

    def draw(self, screen: pygame.Surface, font: pygame.font.Font = None):
        """Draw the button."""
        if font is None:
            font = pygame.font.SysFont('Arial', 20)

        if not self.enabled:
            color = (180, 180, 180)  # Gray for disabled
        elif self.hovered:
            color = BUTTON_HOVER
        else:
            color = self.color

        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, BLACK, self.rect, 2, border_radius=5)

        text_surface = font.render(self.text, True, WHITE)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame event.

        Returns:
            True if event was consumed (button clicked)
        """
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.enabled and self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()
                return True
        return False


class Dropdown:
    """Scrollable dropdown menu widget."""

    def __init__(self, x: int, y: int, width: int, items: List[Tuple], default_index: int = 0, max_visible: int = None):
        """
        Create a dropdown menu.

        Args:
            x, y: Position
            width: Width of dropdown
            items: List of (module_name, display_name, source) tuples
            default_index: Initially selected index
            max_visible: Maximum visible items before scrolling
        """
        self.rect = pygame.Rect(x, y, width, 40)
        self.items = items
        self.selected_index = default_index
        self.is_open = False
        self.hovered_index = -1
        self.scroll_offset = 0
        self.max_visible = max_visible if max_visible else 10

    def get_selected(self) -> str:
        """Get the selected item's module name."""
        return self.items[self.selected_index][0]

    def get_dropdown_rect(self) -> pygame.Rect:
        """Get the rect for the dropped down menu."""
        item_height = 35
        visible_items = min(len(self.items), self.max_visible)
        return pygame.Rect(self.rect.x, self.rect.y + self.rect.height,
                          self.rect.width, visible_items * item_height)

    def draw(self, screen: pygame.Surface):
        """Draw the dropdown."""
        font_small = pygame.font.SysFont('Arial', 16)
        font_tiny = pygame.font.SysFont('Arial', 14)

        # Draw main button
        color = BUTTON_HOVER if self.is_open else BUTTON_COLOR
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (100, 100, 100), self.rect, 2, border_radius=5)

        # Draw selected item text
        _, display_name, source = self.items[self.selected_index]
        source_icon = "" if source == "local" else "📦 "
        count_text = f" ({len(self.items)} engines)" if len(self.items) > 10 else ""
        display_text = f"{source_icon}{display_name}{count_text if not self.is_open else ''}"
        text = font_small.render(display_text, True, WHITE)
        text_rect = text.get_rect(midleft=(self.rect.x + 10, self.rect.centery))
        # Truncate if too long
        max_width = self.rect.width - 40
        if text.get_width() > max_width:
            display_text = f"{source_icon}{display_name}"
            text = font_small.render(display_text, True, WHITE)
        screen.blit(text, text_rect)

        # Draw dropdown arrow
        arrow = "▼" if not self.is_open else "▲"
        arrow_text = font_small.render(arrow, True, WHITE)
        arrow_rect = arrow_text.get_rect(midright=(self.rect.right - 10, self.rect.centery))
        screen.blit(arrow_text, arrow_rect)

        # Draw dropdown list if open
        if self.is_open:
            dropdown_rect = self.get_dropdown_rect()
            # Background
            pygame.draw.rect(screen, DROPDOWN_BG, dropdown_rect, border_radius=5)
            pygame.draw.rect(screen, (100, 100, 100), dropdown_rect, 2, border_radius=5)

            # Calculate visible range based on scroll
            total_items = len(self.items)
            start_idx = self.scroll_offset
            end_idx = min(start_idx + self.max_visible, total_items)

            # Draw items
            item_height = 35
            for i in range(start_idx, end_idx):
                display_idx = i - start_idx
                item_rect = pygame.Rect(dropdown_rect.x, dropdown_rect.y + display_idx * item_height,
                                       dropdown_rect.width, item_height)

                # Highlight selected or hovered
                if i == self.selected_index:
                    pygame.draw.rect(screen, DROPDOWN_SELECTED, item_rect)
                elif i == self.hovered_index:
                    pygame.draw.rect(screen, DROPDOWN_HOVER, item_rect)

                # Draw text
                _, display_name, source = self.items[i]
                source_icon = "" if source == "local" else "📦 "
                item_text = font_tiny.render(f"{source_icon}{display_name}", True, WHITE)
                item_text_rect = item_text.get_rect(midleft=(item_rect.x + 10, item_rect.centery))
                screen.blit(item_text, item_text_rect)

            # Draw scroll indicator if needed
            if total_items > self.max_visible:
                scrollbar_x = dropdown_rect.right - 8
                scrollbar_height = dropdown_rect.height
                scroll_ratio = self.scroll_offset / max(1, total_items - self.max_visible)
                thumb_height = max(20, scrollbar_height * self.max_visible / total_items)
                thumb_y = dropdown_rect.y + scroll_ratio * (scrollbar_height - thumb_height)

                pygame.draw.rect(screen, (80, 80, 80),
                               (scrollbar_x, thumb_y, 6, thumb_height), border_radius=3)

                # Show scroll hint text
                showing_text = f"Showing {start_idx+1}-{end_idx} of {total_items}"
                hint_surface = font_tiny.render(showing_text, True, (150, 150, 150))
                hint_rect = hint_surface.get_rect(center=(dropdown_rect.centerx, dropdown_rect.bottom + 12))
                screen.blit(hint_surface, hint_rect)

    def handle_event(self, event: pygame.event.Event) -> bool:
        """
        Handle pygame event.

        Returns:
            True if event was consumed
        """
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:  # Left click
                if self.rect.collidepoint(event.pos):
                    # Toggle dropdown
                    self.is_open = not self.is_open
                    if self.is_open:
                        self.scroll_offset = 0
                    return True
                elif self.is_open:
                    # Check if clicked on dropdown item
                    dropdown_rect = self.get_dropdown_rect()
                    if dropdown_rect.collidepoint(event.pos):
                        # Calculate which item was clicked
                        item_height = 35
                        rel_y = event.pos[1] - dropdown_rect.y
                        clicked_display_idx = rel_y // item_height
                        clicked_actual_idx = self.scroll_offset + clicked_display_idx
                        if 0 <= clicked_actual_idx < len(self.items):
                            self.selected_index = clicked_actual_idx
                            self.is_open = False
                            return True
                    else:
                        # Clicked outside, close dropdown
                        self.is_open = False

            # Mouse wheel scrolling
            elif event.button == 4 and self.is_open:  # Scroll up
                dropdown_rect = self.get_dropdown_rect()
                if dropdown_rect.collidepoint(event.pos):
                    self.scroll_offset = max(0, self.scroll_offset - 1)
                    return True

            elif event.button == 5 and self.is_open:  # Scroll down
                dropdown_rect = self.get_dropdown_rect()
                if dropdown_rect.collidepoint(event.pos):
                    max_scroll = max(0, len(self.items) - self.max_visible)
                    self.scroll_offset = min(max_scroll, self.scroll_offset + 1)
                    return True

        elif event.type == pygame.MOUSEMOTION and self.is_open:
            dropdown_rect = self.get_dropdown_rect()
            if dropdown_rect.collidepoint(event.pos):
                # Calculate which item is hovered
                item_height = 35
                rel_y = event.pos[1] - dropdown_rect.y
                hovered_display_idx = rel_y // item_height
                self.hovered_index = self.scroll_offset + hovered_display_idx
            else:
                self.hovered_index = -1

        return False


# ============================================================================
# CHESS BOARD RENDERER
# ============================================================================

class ChessBoardRenderer:
    """Handles chess board rendering with pieces and highlighting."""

    def __init__(self, square_size: int = 80):
        """
        Create a chess board renderer.

        Args:
            square_size: Size of each square in pixels
        """
        self.square_size = square_size
        self.piece_font = self.load_piece_font()

    def load_piece_font(self, size: int = 65) -> pygame.font.Font:
        """
        Load chess piece font with fallbacks.

        Tries chess-specific fonts first, then falls back to system fonts
        that support chess unicode characters.

        Args:
            size: Font size in pixels

        Returns:
            pygame Font object
        """
        # Try loading chess font files
        chess_font_files = ['ChessMerida.ttf', 'ChessAlpha.ttf', 'chess_merida_unicode.ttf']
        for font_file in chess_font_files:
            try:
                return pygame.font.Font(font_file, size)
            except:
                continue

        # Fall back to system fonts
        piece_font_names = ['Segoe UI Symbol', 'Arial Unicode MS', 'DejaVu Sans', 'FreeSans']
        for font_name in piece_font_names:
            try:
                return pygame.font.SysFont(font_name, size)
            except:
                continue

        # Final fallback
        return pygame.font.SysFont(None, size)

    def draw_board(
        self,
        screen: pygame.Surface,
        board: chess.Board,
        x: int = 0,
        y: int = 0,
        flipped: bool = False,
        highlight_squares: Optional[List[int]] = None,
        last_move: Optional[chess.Move] = None,
        selected_square: Optional[int] = None,
        legal_moves: Optional[List[chess.Move]] = None,
        draw_coordinates: bool = True
    ):
        """
        Draw a chess board with pieces and highlighting.

        Args:
            screen: Pygame surface to draw on
            board: Chess board state
            x, y: Top-left position to draw board
            flipped: Whether to flip board (Black's perspective)
            highlight_squares: List of squares to highlight
            last_move: Last move to highlight
            selected_square: Currently selected square
            legal_moves: Legal moves from selected square (for indicators)
            draw_coordinates: Whether to draw file/rank labels
        """
        highlight_squares = highlight_squares or []

        # Draw squares
        for row in range(8):
            for col in range(8):
                sq_x = x + col * self.square_size
                sq_y = y + row * self.square_size

                if flipped:
                    actual_col = 7 - col
                    actual_row = row
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
                if last_move and (square == last_move.from_square or square == last_move.to_square):
                    color = LAST_MOVE

                # Highlight selected square
                if square == selected_square:
                    color = SELECTED

                # Custom highlights
                if square in highlight_squares:
                    color = HIGHLIGHT

                # Highlight king in check
                if board.is_check():
                    king_square = board.king(board.turn)
                    if square == king_square:
                        color = CHECK_COLOR

                pygame.draw.rect(screen, color, (sq_x, sq_y, self.square_size, self.square_size))

                # Draw piece
                piece = board.piece_at(square)
                if piece:
                    piece_char = piece.symbol()
                    piece_unicode = PIECE_UNICODE[piece_char]

                    # White pieces with outline
                    if piece.color == chess.WHITE:
                        outline_surface = self.piece_font.render(piece_unicode, True, (50, 50, 50))
                        text_rect = outline_surface.get_rect(center=(sq_x + self.square_size // 2, sq_y + self.square_size // 2))
                        # 8-direction outline
                        for dx, dy in [(-1, -1), (-1, 0), (-1, 1), (0, -1), (0, 1), (1, -1), (1, 0), (1, 1)]:
                            screen.blit(outline_surface, (text_rect.x + dx, text_rect.y + dy))
                        text_surface = self.piece_font.render(piece_unicode, True, (255, 255, 255))
                        screen.blit(text_surface, text_rect)
                    # Black pieces solid
                    else:
                        text_surface = self.piece_font.render(piece_unicode, True, (30, 30, 30))
                        text_rect = text_surface.get_rect(center=(sq_x + self.square_size // 2, sq_y + self.square_size // 2))
                        screen.blit(text_surface, text_rect)

        # Draw legal move indicators
        if legal_moves:
            for move in legal_moves:
                dest_square = move.to_square
                if flipped:
                    col = 7 - chess.square_file(dest_square)
                    row = chess.square_rank(dest_square)
                else:
                    col = chess.square_file(dest_square)
                    row = 7 - chess.square_rank(dest_square)

                center_x = x + col * self.square_size + self.square_size // 2
                center_y = y + row * self.square_size + self.square_size // 2

                # Capture indicator (ring) vs move indicator (dot)
                if board.piece_at(dest_square):
                    pygame.draw.circle(screen, (60, 60, 60), (center_x, center_y), self.square_size // 2 - 4, 5)
                else:
                    pygame.draw.circle(screen, (80, 80, 80), (center_x, center_y), self.square_size // 6)

        # Draw coordinates
        if draw_coordinates:
            coord_font = pygame.font.SysFont('Arial', 14, bold=True)
            board_size = self.square_size * 8

            for i in range(8):
                # File labels (a-h)
                if flipped:
                    file_label = chr(ord('h') - i)
                else:
                    file_label = chr(ord('a') + i)

                square_is_light = (7 + i) % 2 == 0
                coord_color = DARK_SQUARE if square_is_light else LIGHT_SQUARE
                text = coord_font.render(file_label, True, coord_color)
                screen.blit(text, (x + i * self.square_size + self.square_size - 13, y + board_size - 16))

                # Rank labels (1-8)
                if flipped:
                    rank_label = str(i + 1)
                else:
                    rank_label = str(8 - i)

                square_is_light = i % 2 == 0
                coord_color = DARK_SQUARE if square_is_light else LIGHT_SQUARE
                text = coord_font.render(rank_label, True, coord_color)
                screen.blit(text, (x + 5, y + i * self.square_size + 5))
