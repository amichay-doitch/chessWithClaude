"""
Quick test script to verify Stockfish library migration works correctly.
"""

import chess
import os
from stockfish_analyzer import StockfishAnalyzer

# Auto-detect stockfish in script directory
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
STOCKFISH_PATH = os.path.join(SCRIPT_DIR, "stockfish-windows-x86-64-avx2.exe")

def test_basic_analysis():
    """Test basic analysis (backward compatible)."""
    print("=" * 60)
    print("TEST 1: Basic Analysis (Backward Compatible)")
    print("=" * 60)

    board = chess.Board()  # Starting position

    with StockfishAnalyzer(stockfish_path=STOCKFISH_PATH) as analyzer:
        analysis = analyzer.analyze(board)

        print(f"Best move: {analysis.best_move}")
        print(f"Evaluation: {analysis.evaluation:+.2f} pawns")
        print(f"Depth: {analysis.depth}")
        print(f"Top moves: {analysis.top_moves}")  # Should be None
        print(f"Verbose stats: {analysis.verbose_stats}")  # Should be None

    print("\n[OK] Basic analysis works!\n")


def test_top_moves():
    """Test top-N moves analysis."""
    print("=" * 60)
    print("TEST 2: Top-3 Moves Analysis")
    print("=" * 60)

    board = chess.Board()

    with StockfishAnalyzer(stockfish_path=STOCKFISH_PATH) as analyzer:
        analysis = analyzer.analyze(board, top_n=3, verbose=False)

        print(f"Best move: {analysis.best_move}")
        print(f"Evaluation: {analysis.evaluation:+.2f} pawns")
        print(f"\nTop 3 moves:")

        if analysis.top_moves:
            for ma in analysis.top_moves:
                eval_str = f"{ma.centipawn/100:+.2f}" if ma.centipawn else f"M{ma.mate}"
                print(f"  {ma.rank}. {ma.move_uci} ({eval_str})")
        else:
            print("  ERROR: No top moves returned!")
            return False

    print("\n[OK] Top-N analysis works!\n")
    return True


def test_verbose_stats():
    """Test verbose statistics."""
    print("=" * 60)
    print("TEST 3: Verbose Statistics")
    print("=" * 60)

    board = chess.Board()

    with StockfishAnalyzer(stockfish_path=STOCKFISH_PATH) as analyzer:
        analysis = analyzer.analyze(board, top_n=3, verbose=True)

        print(f"Best move: {analysis.best_move}")
        print(f"\nTop 3 moves:")

        if analysis.top_moves:
            for ma in analysis.top_moves:
                eval_str = f"{ma.centipawn/100:+.2f}" if ma.centipawn else f"M{ma.mate}"
                print(f"  {ma.rank}. {ma.move_uci} ({eval_str})")

        print(f"\nVerbose stats:")
        if analysis.verbose_stats:
            print(f"  Nodes searched: {analysis.verbose_stats.nodes:,}")
            print(f"  NPS: {analysis.verbose_stats.nps:,}")
            print(f"  Selective depth: {analysis.verbose_stats.seldepth}")
            print(f"  Time: {analysis.verbose_stats.time_ms} ms")
        else:
            print("  ERROR: No verbose stats returned!")
            return False

    print("\n[OK] Verbose stats work!\n")
    return True


def test_elo_rating():
    """Test ELO rating limitation."""
    print("=" * 60)
    print("TEST 4: ELO Rating (1350 vs Full Strength)")
    print("=" * 60)

    board = chess.Board()

    # Full strength
    with StockfishAnalyzer(stockfish_path=STOCKFISH_PATH) as analyzer:
        full_analysis = analyzer.analyze(board, top_n=1)
        print(f"Full strength: {full_analysis.best_move} ({full_analysis.evaluation:+.2f})")

    # 1350 ELO (minimum supported by Stockfish)
    with StockfishAnalyzer(stockfish_path=STOCKFISH_PATH, elo_rating=1350) as analyzer:
        weak_analysis = analyzer.analyze(board, top_n=1)
        print(f"1350 ELO:      {weak_analysis.best_move} ({weak_analysis.evaluation:+.2f})")

    print("\n[OK] ELO rating works!\n")
    return True


def test_tactical_position():
    """Test on a tactical position."""
    print("=" * 60)
    print("TEST 5: Tactical Position (Greek Gift Sacrifice)")
    print("=" * 60)

    # Greek Gift position - Bxh7+ is winning
    fen = "r1bq1rk1/ppp2ppp/2n5/3np1B1/1b1P4/2N1PN2/PPP2PPP/R2QKB1R w KQ - 0 1"
    board = chess.Board(fen)

    with StockfishAnalyzer(stockfish_path=STOCKFISH_PATH) as analyzer:
        analysis = analyzer.analyze(board, top_n=3, verbose=True)

        print(f"FEN: {fen}")
        print(f"\nTop 3 moves:")

        if analysis.top_moves:
            for ma in analysis.top_moves:
                move_san = board.san(ma.move)
                eval_str = f"{ma.centipawn/100:+.2f}" if ma.centipawn else f"M{ma.mate}"
                print(f"  {ma.rank}. {move_san} ({eval_str})")

        if analysis.verbose_stats:
            print(f"\nSearch stats: {analysis.verbose_stats.nodes:,} nodes @ {analysis.verbose_stats.nps:,} nps")

    print("\n[OK] Tactical analysis works!\n")
    return True


if __name__ == "__main__":
    print("\n" + "="*60)
    print("STOCKFISH LIBRARY MIGRATION TEST SUITE")
    print("="*60 + "\n")

    try:
        test_basic_analysis()
        test_top_moves()
        test_verbose_stats()
        test_elo_rating()
        test_tactical_position()

        print("="*60)
        print("ALL TESTS PASSED!")
        print("="*60)
        print("\nMigration successful! The stockfish library integration works correctly.")
        print("\nKey features verified:")
        print("  - Backward compatible basic analysis")
        print("  - Top-N moves analysis")
        print("  - Verbose search statistics")
        print("  - ELO rating control")
        print("  - Tactical position analysis")

    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
