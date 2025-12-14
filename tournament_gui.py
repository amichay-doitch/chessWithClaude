"""
Tournament GUI - Visual interface for watching engine vs engine matches
"""

import pygame
import chess
import chess.svg
import sys
import argparse
import threading
import time
import importlib
from typing import Optional, Dict, Any, List
from game_recorder import GameRecorder


# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_SQUARE = (240, 217, 181)
DARK_SQUARE = (181, 136, 99)
HIGHLIGHT = (186, 202, 68)
CHECK_COLOR = (255, 100, 100)
GRAY = (128, 128, 128)
LIGHT_GRAY = (200, 200, 200)
DARK_GRAY = (80, 80, 80)
GREEN = (100, 200, 100)
RED = (200, 100, 100)
BLUE = (100, 100, 200)

# Screen dimensions
BOARD_SIZE = 640
PANEL_WIDTH = 400
SCREEN_WIDTH = BOARD_SIZE + PANEL_WIDTH
SCREEN_HEIGHT = BOARD_SIZE
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
        pygame.display.set_caption("Tournament Viewer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.small_font = pygame.font.Font(None, 18)
        self.large_font = pygame.font.Font(None, 32)

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
        self.speed = 1  # 1x speed

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

        # Load piece images
        self.load_pieces()

    def load_pieces(self):
        """Load chess piece images."""
        self.pieces = {}
        piece_chars = {
            'P': '\u2659', 'N': '\u2658', 'B': '\u2657',
            'R': '\u2656', 'Q': '\u2655', 'K': '\u2654',
            'p': '\u265F', 'n': '\u265E', 'b': '\u265D',
            'r': '\u265C', 'q': '\u265B', 'k': '\u265A'
        }

        piece_font = pygame.font.Font(None, int(SQUARE_SIZE * 0.8))

        for piece, unicode_char in piece_chars.items():
            color = WHITE if piece.isupper() else BLACK
            text = piece_font.render(unicode_char, True, color)
            self.pieces[piece] = text

    def draw_board(self):
        """Draw the chess board."""
        for row in range(8):
            for col in range(8):
                x = col * SQUARE_SIZE
                y = row * SQUARE_SIZE

                # Draw square
                color = LIGHT_SQUARE if (row + col) % 2 == 0 else DARK_SQUARE
                pygame.draw.rect(self.screen, color, (x, y, SQUARE_SIZE, SQUARE_SIZE))

                # Draw piece
                square = chess.square(col, 7 - row)
                piece = self.board.piece_at(square)

                if piece:
                    piece_char = piece.symbol()
                    piece_img = self.pieces.get(piece_char)
                    if piece_img:
                        piece_rect = piece_img.get_rect(center=(x + SQUARE_SIZE // 2, y + SQUARE_SIZE // 2))
                        self.screen.blit(piece_img, piece_rect)

    def draw_panel(self):
        """Draw the statistics and control panel."""
        panel_x = BOARD_SIZE

        # Background
        pygame.draw.rect(self.screen, LIGHT_GRAY, (panel_x, 0, PANEL_WIDTH, SCREEN_HEIGHT))

        y_offset = 20

        # Title
        title = self.font.render("Tournament Viewer", True, BLACK)
        self.screen.blit(title, (panel_x + 10, y_offset))
        y_offset += 40

        # Match info
        info_lines = [
            f"{self.engine1_module} vs {self.engine2_module}",
            f"Depth: {self.depth1} vs {self.depth2}",
            f"Games: {self.current_game}/{self.num_games}",
            ""
        ]

        for line in info_lines:
            text = self.small_font.render(line, True, BLACK)
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 25

        # Score
        score_title = self.font.render("Score:", True, BLACK)
        self.screen.blit(score_title, (panel_x + 10, y_offset))
        y_offset += 30

        e1_score = self.stats["engine1"]["wins"] + 0.5 * self.stats["engine1"]["draws"]
        e2_score = self.stats["engine2"]["wins"] + 0.5 * self.stats["engine2"]["draws"]

        score_lines = [
            f"{self.engine1_module}: {e1_score}",
            f"  W:{self.stats['engine1']['wins']} D:{self.stats['engine1']['draws']} L:{self.stats['engine1']['losses']}",
            f"{self.engine2_module}: {e2_score}",
            f"  W:{self.stats['engine2']['wins']} D:{self.stats['engine2']['draws']} L:{self.stats['engine2']['losses']}",
        ]

        for line in score_lines:
            text = self.small_font.render(line, True, BLACK)
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 25

        y_offset += 20

        # Current move info
        if self.current_move_info:
            info_title = self.font.render("Current Move:", True, BLACK)
            self.screen.blit(info_title, (panel_x + 10, y_offset))
            y_offset += 30

            move_text = self.small_font.render(f"Move: {self.current_move_info.get('move', 'N/A')}", True, BLACK)
            self.screen.blit(move_text, (panel_x + 10, y_offset))
            y_offset += 25

            time_text = self.small_font.render(f"Time: {self.current_move_info.get('time', 0):.2f}s", True, BLACK)
            self.screen.blit(time_text, (panel_x + 10, y_offset))
            y_offset += 25

            nodes_text = self.small_font.render(f"Nodes: {self.current_move_info.get('nodes', 0):,}", True, BLACK)
            self.screen.blit(nodes_text, (panel_x + 10, y_offset))
            y_offset += 25

        y_offset += 20

        # Status
        status_text = "Running" if self.running and not self.paused else "Paused" if self.paused else "Stopped"
        status_color = GREEN if status_text == "Running" else BLUE if status_text == "Paused" else RED
        status = self.font.render(f"Status: {status_text}", True, status_color)
        self.screen.blit(status, (panel_x + 10, y_offset))
        y_offset += 40

        # Controls
        controls_title = self.font.render("Controls:", True, BLACK)
        self.screen.blit(controls_title, (panel_x + 10, y_offset))
        y_offset += 30

        controls = [
            "SPACE - Start/Pause",
            "S - Stop",
            "Q - Quit",
            f"Speed: {self.speed}x"
        ]

        for control in controls:
            text = self.small_font.render(control, True, DARK_GRAY)
            self.screen.blit(text, (panel_x + 10, y_offset))
            y_offset += 25

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
                # Wait if paused
                while self.paused and self.running:
                    time.sleep(0.1)

                if not self.running:
                    break

                # Get move
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

                # Speed control
                if self.speed < 10:
                    time.sleep(0.1 / self.speed)

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

            # Update stats
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

        # Start match recording
        self.recorder.start_match(
            self.engine1_module, self.engine2_module,
            self.depth1, self.depth2, self.time_limit, self.num_games
        )

        # Run games
        def run_tournament():
            for game_num in range(1, self.num_games + 1):
                if not self.running:
                    break

                self.current_game = game_num
                engine1_is_white = (game_num % 2 == 1)
                self.play_game_threaded(game_num, engine1_is_white)

            if self.running:
                # Save final results
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

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q:
                    return False

                elif event.key == pygame.K_SPACE:
                    if not self.running:
                        self.start_tournament()
                    else:
                        self.paused = not self.paused

                elif event.key == pygame.K_s:
                    self.running = False

                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.speed = min(self.speed * 2, 100)

                elif event.key == pygame.K_MINUS:
                    self.speed = max(self.speed // 2, 1)

        return True

    def run(self):
        """Main GUI loop."""
        running = True

        while running:
            running = self.handle_events()

            self.screen.fill(WHITE)
            self.draw_board()
            self.draw_panel()

            pygame.display.flip()
            self.clock.tick(30)

        self.running = False
        pygame.quit()


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Tournament GUI")

    parser.add_argument("--engine1", default="engine_v3", help="First engine module")
    parser.add_argument("--engine2", default="engine_v4", help="Second engine module")
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
    print("  SPACE - Start/Pause tournament")
    print("  S - Stop tournament")
    print("  +/- - Increase/Decrease speed")
    print("  Q - Quit\n")

    gui.run()


if __name__ == "__main__":
    main()
