"""
Chess Game - Play against the engine
"""

import chess
from board import ChessBoard
from engine_v5 import ChessEngine


def print_header():
    print("\n" + "=" * 50)
    print("       CHESS ENGINE - chessWithClaude")
    print("=" * 50)
    print("Commands:")
    print("  - Enter moves in UCI format (e.g., e2e4, g1f3)")
    print("  - 'quit' to exit")
    print("  - 'undo' to take back last move")
    print("  - 'new' to start new game")
    print("  - 'fen' to show current FEN")
    print("  - 'eval' to show engine evaluation")
    print("  - 'hint' to get a move suggestion")
    print("  - 'depth N' to set engine depth (e.g., 'depth 6')")
    print("=" * 50 + "\n")


def format_score(score: int) -> str:
    """Format score for display."""
    if abs(score) >= 90000:  # Mate score
        if score > 0:
            return f"Mate in {(100000 - abs(score)) // 2 + 1} for White"
        else:
            return f"Mate in {(100000 - abs(score)) // 2 + 1} for Black"
    else:
        # Convert centipawns to pawns
        pawns = score / 100
        if pawns > 0:
            return f"+{pawns:.2f} (White advantage)"
        elif pawns < 0:
            return f"{pawns:.2f} (Black advantage)"
        else:
            return "0.00 (Equal)"


def play_game():
    """Main game loop."""
    print_header()

    # Configuration
    player_color = None
    while player_color not in ['w', 'b']:
        player_color = input("Play as White or Black? (w/b): ").strip().lower()

    player_is_white = player_color == 'w'

    depth = 5
    try:
        depth_input = input(f"Engine search depth (default={depth}, higher=stronger): ").strip()
        if depth_input:
            depth = int(depth_input)
            depth = max(1, min(depth, 10))  # Clamp between 1 and 10
    except ValueError:
        pass

    time_limit = None
    try:
        time_input = input("Time limit per move in seconds (default=none): ").strip()
        if time_input:
            time_limit = float(time_input)
    except ValueError:
        pass

    board = ChessBoard()
    engine = ChessEngine(max_depth=depth, time_limit=time_limit)

    print(f"\nEngine depth: {depth}")
    if time_limit:
        print(f"Time limit: {time_limit}s per move")
    print("\nGame started! Good luck!\n")

    while not board.is_game_over():
        # Display board
        print("\n" + board.display_unicode(flip=not player_is_white))
        print(f"\n{board.get_turn()} to move")

        if board.is_check():
            print("CHECK!")

        # Determine if it's player's turn
        is_player_turn = (board.board.turn == chess.WHITE) == player_is_white

        if is_player_turn:
            # Player's turn
            while True:
                move_input = input("\nYour move: ").strip().lower()

                if move_input == 'quit':
                    print("Thanks for playing!")
                    return

                elif move_input == 'undo':
                    # Undo both moves (player and engine)
                    if len(board.board.move_stack) >= 2:
                        board.undo_move()
                        board.undo_move()
                        print("Undid last two moves.")
                    elif len(board.board.move_stack) == 1:
                        board.undo_move()
                        print("Undid last move.")
                    else:
                        print("No moves to undo.")
                    break

                elif move_input == 'new':
                    board.reset()
                    print("New game started.")
                    break

                elif move_input == 'fen':
                    print(f"FEN: {board.get_fen()}")
                    continue

                elif move_input == 'eval':
                    score = engine.evaluate(board.board)
                    print(f"Evaluation: {format_score(score)}")
                    continue

                elif move_input == 'hint':
                    print("Thinking...")
                    result = engine.search(board.board)
                    if result:
                        print(f"Suggestion: {result.best_move} ({format_score(result.score)})")
                    continue

                elif move_input.startswith('depth'):
                    try:
                        new_depth = int(move_input.split()[1])
                        engine.max_depth = max(1, min(new_depth, 10))
                        print(f"Depth set to {engine.max_depth}")
                    except (IndexError, ValueError):
                        print("Usage: depth N (e.g., 'depth 6')")
                    continue

                else:
                    # Try to make the move
                    if board.make_move(move_input):
                        break
                    else:
                        print("Illegal move. Try again.")
                        print("Legal moves:", ' '.join(m.uci() for m in board.get_legal_moves()[:20]))
                        if len(board.get_legal_moves()) > 20:
                            print(f"... and {len(board.get_legal_moves()) - 20} more")

        else:
            # Engine's turn
            print("\nEngine is thinking...")
            result = engine.search(board.board)

            if result and result.best_move:
                board.make_move_object(result.best_move)
                print(f"\nEngine plays: {result.best_move}")
                print(f"Evaluation: {format_score(result.score)}")
                print(f"(Depth {result.depth}, {result.nodes_searched} nodes, {result.time_spent:.2f}s)")
            else:
                print("Engine error - no move found")
                break

    # Game over
    print("\n" + board.display_unicode(flip=not player_is_white))
    print("\n" + "=" * 50)
    print(f"GAME OVER: {board.get_result()}")
    print("=" * 50)


def engine_vs_engine():
    """Watch two engines play each other."""
    print("\n=== Engine vs Engine ===\n")

    board = ChessBoard()
    engine = ChessEngine(max_depth=4, time_limit=5)

    move_count = 0
    max_moves = 200  # Prevent infinite games

    while not board.is_game_over() and move_count < max_moves:
        print(f"\nMove {move_count // 2 + 1}")
        print(board.display_unicode())
        print(f"\n{board.get_turn()} to move")

        result = engine.search(board.board)
        if result and result.best_move:
            board.make_move_object(result.best_move)
            print(f"Plays: {result.best_move} ({format_score(result.score)})")
        else:
            break

        move_count += 1

    print("\n" + board.display_unicode())
    print(f"\nGame over: {board.get_result()}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == '--self':
        engine_vs_engine()
    else:
        play_game()
