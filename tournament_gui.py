"""
Tournament GUI - Visual interface for watching engine vs engine matches
"""

import pygame
import chess
import sys
import argparse
import threading
import time
import importlib
from typing import Optional, Dict, Any, Tuple
from game_recorder import GameRecorder
from gui_utils import (
    Button, ChessBoardRenderer,
    WHITE, BLACK, LIGHT_SQUARE, DARK_SQUARE,
    BUTTON_COLOR, BUTTON_HOVER, TEXT_COLOR, PIECE_UNICODE
)

# Tournament-specific colors
HIGHLIGHT = (186, 202, 68)
BG_COLOR = (240, 240, 245)
PANEL_BG = (250, 250, 252)
BUTTON_DISABLED = (180, 180, 180)
GREEN = (76, 175, 80)
RED = (244, 67, 54)
ORANGE = (255, 152, 0)

# Screen dimensions
BOARD_SIZE = 640
PANEL_WIDTH = 460
SCREEN_WIDTH = BOARD_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = 720
SQUARE_SIZE = BOARD_SIZE // 8


class TournamentGUI:
    """GUI for watching chess engine tournaments."""

    def __init__(self, engine1_module: str, engine2_module: str,
                 depth1: int = 5, depth2: int = 5,
                 time_limit: Optional[float] = None,
                 num_games: int = 10):
        """Initialize tournament GUI."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("Chess Tournament Viewer")
        self.clock = pygame.time.Clock()

        # Fonts
        self.title_font = pygame.font.Font(None, 36)
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 20)
        self.tiny_font = pygame.font.Font(None, 16)

        # Tournament settings
        self.engine1_module = engine1_module
        self.engine2_module = engine2_module
        self.depth1 = depth1
        self.depth2 = depth2
        self.time_limit = time_limit
        self.num_games = num_games

        # Load engines
        print(f"Loading engines: {engine1_module} vs {engine2_module}...")
        mod1 = importlib.import_module(engine1_module)
        mod2 = importlib.import_module(engine2_module)
        self.engine1 = mod1.ChessEngine(max_depth=depth1, time_limit=time_limit)
        self.engine2 = mod2.ChessEngine(max_depth=depth2, time_limit=time_limit)

        # Game state
        self.board = chess.Board()
        self.current_game = 0
        self.running = False
        self.paused = False
        self.speed = 1

        # Statistics
        self.stats = {
            "engine1": {"wins": 0, "draws": 0, "losses": 0},
            "engine2": {"wins": 0, "draws": 0, "losses": 0},
            "games": [],
            "start_time": None
        }

        # Recorder
        self.recorder = GameRecorder("games")

        # Threading
        self.game_thread = None
        self.current_move_info = None

        # Create buttons
        self.create_buttons()

        # Create board renderer
        self.board_renderer = ChessBoardRenderer(SQUARE_SIZE)

    def create_buttons(self):
        """Create GUI buttons."""
        panel_x = BOARD_SIZE + 20
        button_y = SCREEN_HEIGHT - 200
        button_width = 130
        button_height = 45
        spacing = 10

        self.start_button = Button(panel_x, button_y, button_width, button_height, "Start", GREEN)
        self.pause_button = Button(panel_x + button_width + spacing, button_y, button_width, button_height, "Pause", ORANGE)
        self.stop_button = Button(panel_x + 2 * (button_width + spacing), button_y, button_width, button_height, "Stop", RED)

        # Speed buttons
        speed_y = button_y + button_height + spacing
        speed_width = 60
        self.speed_1x = Button(panel_x, speed_y, speed_width, 35, "1x", BUTTON_COLOR)
        self.speed_10x = Button(panel_x + speed_width + 5, speed_y, speed_width, 35, "10x", BUTTON_COLOR)
        self.speed_50x = Button(panel_x + 2 * (speed_width + 5), speed_y, speed_width, 35, "50x", BUTTON_COLOR)
        self.speed_100x = Button(panel_x + 3 * (speed_width + 5), speed_y, speed_width, 35, "100x", BUTTON_COLOR)

        self.buttons = [
            self.start_button, self.pause_button, self.stop_button,
            self.speed_1x, self.speed_10x, self.speed_50x, self.speed_100x
        ]

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
            draw_coordinates=False
        )

    def draw_panel(self):
        """Draw the statistics and control panel."""
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
            f"{self.engine1_module} vs {self.engine2_module}",
            f"Depth: {self.depth1} vs {self.depth2}",
            f"Time: {self.time_limit}s" if self.time_limit else "Depth-based",
            f"",
            f"Game: {self.current_game}/{self.num_games}",
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

        name1 = self.tiny_font.render(self.engine1_module, True, TEXT_COLOR)
        score1 = self.title_font.render(f"{e1_score}", True, TEXT_COLOR)
        wdl1 = self.tiny_font.render(f"W:{self.stats['engine1']['wins']} D:{self.stats['engine1']['draws']} L:{self.stats['engine1']['losses']}", True, TEXT_COLOR)

        self.screen.blit(name1, (score_box1.centerx - name1.get_width() // 2, score_box1.y + 10))
        self.screen.blit(score1, (score_box1.centerx - score1.get_width() // 2, score_box1.y + 35))
        self.screen.blit(wdl1, (score_box1.centerx - wdl1.get_width() // 2, score_box1.y + 75))

        # Engine 2 score
        score_box2 = pygame.Rect(panel_x + 15 + (PANEL_WIDTH - 40) // 2 + 5, y, (PANEL_WIDTH - 40) // 2 - 5, 100)
        pygame.draw.rect(self.screen, WHITE, score_box2, border_radius=8)
        pygame.draw.rect(self.screen, GREEN if e2_score > e1_score else (220, 220, 220), score_box2, 2, border_radius=8)

        name2 = self.tiny_font.render(self.engine2_module, True, TEXT_COLOR)
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
        for button in self.buttons:
            button.draw(self.screen, self.small_font)

    def play_game_threaded(self, game_number: int, engine1_is_white: bool):
        """Play a single game in a thread."""
        self.board = chess.Board()

        white_engine = self.engine1 if engine1_is_white else self.engine2
        black_engine = self.engine2 if engine1_is_white else self.engine1
        white_name = self.engine1_module if engine1_is_white else self.engine2_module
        black_name = self.engine2_module if engine1_is_white else self.engine1_module

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
                    result = white_engine.search(self.board)
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
                    result = black_engine.search(self.board)
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
            if white_name == self.engine1_module:
                self.stats["engine1"]["wins"] += 1
                self.stats["engine2"]["losses"] += 1
            else:
                self.stats["engine2"]["wins"] += 1
                self.stats["engine1"]["losses"] += 1
        elif result == "0-1":
            if white_name == self.engine1_module:
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
            self.engine1_module, self.engine2_module,
            self.depth1, self.depth2, self.time_limit, self.num_games
        )

        def run_tournament():
            for game_num in range(1, self.num_games + 1):
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

    def handle_events(self):
        """Handle pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            # Handle button events
            if self.start_button.handle_event(event):
                if not self.running:
                    self.start_tournament()

            if self.pause_button.handle_event(event):
                if self.running:
                    self.paused = not self.paused

            if self.stop_button.handle_event(event):
                self.running = False

            if self.speed_1x.handle_event(event):
                self.speed = 1
            if self.speed_10x.handle_event(event):
                self.speed = 10
            if self.speed_50x.handle_event(event):
                self.speed = 50
            if self.speed_100x.handle_event(event):
                self.speed = 100

            # Keyboard shortcuts
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False
                elif event.key == pygame.K_SPACE:
                    if not self.running:
                        self.start_tournament()
                    else:
                        self.paused = not self.paused
                elif event.key == pygame.K_s:
                    self.running = False

        return True

    def run(self):
        """Main GUI loop."""
        running = True

        while running:
            running = self.handle_events()

            # Update button states
            self.pause_button.enabled = self.running
            self.stop_button.enabled = self.running

            self.screen.fill(BG_COLOR)
            self.draw_board()
            self.draw_panel()

            pygame.display.flip()
            self.clock.tick(30)

        self.running = False
        pygame.quit()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Tournament GUI")

    parser.add_argument("--engine1", default="engine_pool.engine_v3", help="First engine module")
    parser.add_argument("--engine2", default="engine_pool.engine_v4", help="Second engine module")
    parser.add_argument("--games", type=int, default=10, help="Number of games")
    parser.add_argument("--depth1", type=int, default=5, help="Depth for engine 1")
    parser.add_argument("--depth2", type=int, default=5, help="Depth for engine 2")
    parser.add_argument("--time", type=float, default=None, help="Time limit per move")

    args = parser.parse_args()

    gui = TournamentGUI(
        args.engine1, args.engine2,
        depth1=args.depth1, depth2=args.depth2,
        time_limit=args.time,
        num_games=args.games
    )

    print("\nTournament GUI Controls:")
    print("  Click 'Start' or press SPACE - Start tournament")
    print("  Click 'Pause' or press SPACE - Pause/Resume")
    print("  Click 'Stop' or press S - Stop tournament")
    print("  Speed buttons - Change playback speed")
    print("  Q - Quit\n")

    gui.run()


if __name__ == "__main__":
    main()
