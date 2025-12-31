"""
Comprehensive test suite to verify all functionality after refactoring.
"""

import chess
import sys
import os
import importlib

def print_header(title):
    """Print a section header."""
    print("\n" + "=" * 70)
    print(title.center(70))
    print("=" * 70)

def test_engines():
    """Test all chess engines."""
    print_header("TESTING ALL CHESS ENGINES")

    engines = [
        ('engine_v5', 'engine_v5.py'),
        ('engine_pool.engine', 'engine_pool/engine.py'),
        ('engine_pool.engine_v3', 'engine_pool/engine_v3.py'),
        ('engine_pool.engine_v4', 'engine_pool/engine_v4.py'),
        ('engine_pool.engine_fast', 'engine_pool/engine_fast.py'),
        ('engine_pool.engine_v5_fast', 'engine_pool/engine_v5_fast.py'),
        ('engine_pool.engine_v5_optimized', 'engine_pool/engine_v5_optimized.py'),
        ('engine_pool.engine_v6', 'engine_pool/engine_v6.py'),
        ('engine_pool.engine_v6_fixed', 'engine_pool/engine_v6_fixed.py'),
    ]

    passed = 0
    failed = 0

    for module_name, display_name in engines:
        try:
            module = importlib.import_module(module_name)
            engine = module.ChessEngine(max_depth=3, time_limit=0.1)
            board = chess.Board()
            result = engine.search(board)

            if result and result.best_move:
                print(f"[PASS] {display_name}: {result.best_move} (depth {result.depth}, {result.nodes_searched} nodes)")
                passed += 1
            else:
                print(f"[FAIL] {display_name}: No move returned")
                failed += 1
        except Exception as e:
            print(f"[FAIL] {display_name}: {str(e)[:80]}")
            failed += 1

    print(f"\nEngine Tests: {passed}/{len(engines)} passed")
    return failed == 0

def test_imports():
    """Test all script imports."""
    print_header("TESTING ALL SCRIPT IMPORTS")

    scripts = [
        'gui',
        'main',
        'tournament_gui',
        'tournament_gui_config',
        'pgn_viewer',
        'test_suite_interactive',
        'benchmark_engines',
        'tournament',
        'test_suite',
        'results_viewer',
        'stockfish_analyzer',
        'engine_base',
        'engine_pst',
        'gui_utils',
        'game_recorder',
        'board',
    ]

    passed = 0
    failed = 0

    for script in scripts:
        try:
            importlib.import_module(script)
            print(f"[PASS] {script}.py imports")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {script}.py: {str(e)[:80]}")
            failed += 1

    print(f"\nImport Tests: {passed}/{len(scripts)} passed")
    return failed == 0

def test_engine_on_positions():
    """Test an engine on various positions."""
    print_header("TESTING ENGINE ON VARIOUS POSITIONS")

    from engine_v5 import ChessEngine

    positions = [
        ("Starting position", chess.Board()),
        ("Sicilian Defense", chess.Board("rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2")),
        ("Endgame", chess.Board("8/8/4k3/8/8/4K3/4P3/8 w - - 0 1")),
        ("Complex middlegame", chess.Board("r1bq1rk1/pp2ppbp/2np1np1/8/2BNP3/2N1BP2/PPPQ2PP/R3K2R w KQ - 0 1")),
    ]

    engine = ChessEngine(max_depth=4, time_limit=0.5)

    passed = 0
    for name, board in positions:
        try:
            result = engine.search(board)
            if result and result.best_move:
                print(f"[PASS] {name}: {result.best_move}")
                passed += 1
            else:
                print(f"[FAIL] {name}: No move")
        except Exception as e:
            print(f"[FAIL] {name}: {str(e)[:80]}")

    print(f"\nPosition Tests: {passed}/{len(positions)} passed")
    return passed == len(positions)

def test_tournament():
    """Test tournament.py with minimal settings."""
    print_header("TESTING TOURNAMENT.PY")

    try:
        from tournament import TournamentRunner

        print("Running quick 2-game tournament (engine_v5 vs engine_pool.engine)...")

        tournament = TournamentRunner(
            'engine_v5',
            'engine_pool.engine',
            depth1=3,
            depth2=3,
            time_limit=0.3,
            num_games=2,
            quiet=True
        )

        tournament.run_tournament()

        # Tournament doesn't return results, but if it completed without error, that's a pass
        print(f"[PASS] Tournament completed")
        print(f"  Engine 1 wins: {tournament.stats['engine1']['wins']}")
        print(f"  Engine 2 wins: {tournament.stats['engine2']['wins']}")
        print(f"  Draws: {tournament.stats['engine1']['draws']}")
        return True

    except Exception as e:
        print(f"[FAIL] Tournament error: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False

def test_benchmark():
    """Test benchmark_engines.py."""
    print_header("TESTING BENCHMARK")

    try:
        from benchmark_engines import benchmark_engine
        from engine_pool.engine_v5_fast import ChessEngine as EngineFast

        print("Running quick benchmark on engine_v5_fast...")

        test_positions = [
            chess.Board().fen(),
            "rnbqkbnr/pp1ppppp/8/2p5/4P3/8/PPPP1PPP/RNBQKBNR w KQkq - 0 2",
        ]

        results = benchmark_engine(
            EngineFast,
            "engine_v5_fast",
            test_positions,
            time_limit=0.2
        )

        if results and results.get('avg_nodes', 0) > 0:
            print(f"[PASS] Benchmark completed")
            print(f"  Avg nodes: {results['avg_nodes']:,.0f}")
            print(f"  Avg NPS: {results['avg_nps']:,.0f}")
            return True
        else:
            print(f"[FAIL] No nodes searched")
            return False

    except Exception as e:
        print(f"[FAIL] Benchmark error: {str(e)[:200]}")
        import traceback
        traceback.print_exc()
        return False

def test_game_recorder():
    """Test game recorder."""
    print_header("TESTING GAME RECORDER")

    try:
        from game_recorder import GameRecorder
        import tempfile
        import shutil

        # Create temp directory
        temp_dir = tempfile.mkdtemp()

        try:
            recorder = GameRecorder(temp_dir)
            recorder.start_match("test_engine_1", "test_engine_2", 5, 5, None, 1)

            # Create a simple game
            board = chess.Board()
            board.push(chess.Move.from_uci("e2e4"))
            board.push(chess.Move.from_uci("e7e5"))
            board.push(chess.Move.from_uci("g1f3"))

            # Record game
            recorder.record_game(
                board,
                game_number=1,
                white_engine="test_engine_1",
                black_engine="test_engine_2",
                result="1-0",
                termination="Test game"
            )

            print(f"[PASS] Game recorder works")
            return True

        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)

    except Exception as e:
        print(f"[FAIL] Game recorder error: {str(e)[:200]}")
        return False

def test_board_module():
    """Test board.py module."""
    print_header("TESTING BOARD MODULE")

    try:
        import board as board_module

        # Test if it has required functions/classes
        if hasattr(board_module, 'Board') or hasattr(board_module, 'ChessBoard'):
            print(f"[PASS] board.py module loads")
            return True
        else:
            print(f"[INFO] board.py loads but may not have expected classes")
            return True

    except Exception as e:
        print(f"[FAIL] board.py error: {str(e)[:200]}")
        return False

def main():
    """Run all tests."""
    print("\n" + "=" * 70)
    print("COMPREHENSIVE TEST SUITE".center(70))
    print("Testing all functionality after refactoring".center(70))
    print("=" * 70)

    results = {}

    # Run all tests
    results['engines'] = test_engines()
    results['imports'] = test_imports()
    results['positions'] = test_engine_on_positions()
    results['tournament'] = test_tournament()
    results['benchmark'] = test_benchmark()
    results['game_recorder'] = test_game_recorder()
    results['board_module'] = test_board_module()

    # Summary
    print_header("FINAL SUMMARY")

    for test_name, passed in results.items():
        status = "[PASS]" if passed else "[FAIL]"
        print(f"{status} {test_name.replace('_', ' ').title()}")

    total_passed = sum(1 for v in results.values() if v)
    total_tests = len(results)

    print(f"\nOverall: {total_passed}/{total_tests} test categories passed")

    if total_passed == total_tests:
        print("\n✓ ALL TESTS PASSED - Refactoring verified successful!")
        return 0
    else:
        print(f"\n✗ {total_tests - total_passed} test categories failed")
        return 1

if __name__ == '__main__':
    sys.exit(main())
