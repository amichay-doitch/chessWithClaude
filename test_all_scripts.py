"""
Comprehensive test script to verify all main scripts run correctly after refactoring.
"""

import chess
import sys

def test_engine(engine_module_path, engine_name):
    """Test an engine by running a quick search."""
    try:
        # Import the engine module dynamically
        if '.' in engine_module_path:
            parts = engine_module_path.split('.')
            module = __import__(engine_module_path, fromlist=[parts[-1]])
        else:
            module = __import__(engine_module_path)

        # Create engine instance
        engine = module.ChessEngine(max_depth=3, time_limit=0.1)

        # Test on starting position
        board = chess.Board()
        result = engine.search(board)

        if result and result.best_move:
            print(f"[PASS] {engine_name}: Found move {result.best_move} (depth {result.depth}, {result.nodes_searched} nodes)")
            return True
        else:
            print(f"[FAIL] {engine_name}: Failed to find a move")
            return False
    except Exception as e:
        print(f"[FAIL] {engine_name}: Error - {e}")
        return False

def main():
    print("=" * 70)
    print("COMPREHENSIVE SCRIPT TESTING")
    print("=" * 70)

    results = {}

    # Test main engine (engine_v5.py in root)
    print("\n--- Testing Root Engine ---")
    results['engine_v5'] = test_engine('engine_v5', 'engine_v5.py')

    # Test all engines in engine_pool
    print("\n--- Testing Engine Pool Engines ---")
    engine_pool_engines = [
        ('engine_pool.engine', 'engine_pool/engine.py'),
        ('engine_pool.engine_v3', 'engine_pool/engine_v3.py'),
        ('engine_pool.engine_v4', 'engine_pool/engine_v4.py'),
        ('engine_pool.engine_fast', 'engine_pool/engine_fast.py'),
        ('engine_pool.engine_v5_fast', 'engine_pool/engine_v5_fast.py'),
        ('engine_pool.engine_v5_optimized', 'engine_pool/engine_v5_optimized.py'),
        ('engine_pool.engine_v6', 'engine_pool/engine_v6.py'),
        ('engine_pool.engine_v6_fixed', 'engine_pool/engine_v6_fixed.py'),
    ]

    for module_path, name in engine_pool_engines:
        results[name] = test_engine(module_path, name)

    # Test module imports (scripts that can't be "run" but should import)
    print("\n--- Testing GUI and Utility Script Imports ---")
    test_imports = [
        ('gui', 'gui.py'),
        ('main', 'main.py'),
        ('tournament_gui', 'tournament_gui.py'),
        ('tournament_gui_config', 'tournament_gui_config.py'),
        ('pgn_viewer', 'pgn_viewer.py'),
        ('test_suite_interactive', 'test_suite_interactive.py'),
        ('benchmark_engines', 'benchmark_engines.py'),
        ('tournament', 'tournament.py'),
        ('test_suite', 'test_suite.py'),
        ('results_viewer', 'results_viewer.py'),
        ('stockfish_analyzer', 'stockfish_analyzer.py'),
    ]

    for module_name, display_name in test_imports:
        try:
            __import__(module_name)
            print(f"[PASS] {display_name}: Imports successfully")
            results[display_name] = True
        except Exception as e:
            print(f"[FAIL] {display_name}: Import error - {e}")
            results[display_name] = False

    # Test shared modules
    print("\n--- Testing Shared Modules ---")
    shared_modules = [
        ('engine_base', 'engine_base.py'),
        ('engine_pst', 'engine_pst.py'),
        ('gui_utils', 'gui_utils.py'),
    ]

    for module_name, display_name in shared_modules:
        try:
            __import__(module_name)
            print(f"[PASS] {display_name}: Imports successfully")
            results[display_name] = True
        except Exception as e:
            print(f"[FAIL] {display_name}: Import error - {e}")
            results[display_name] = False

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print(f"\nPassed: {passed}/{total}")

    if passed == total:
        print("\n*** ALL TESTS PASSED! Refactoring complete and verified. ***")
        return 0
    else:
        print(f"\n*** {total - passed} test(s) failed. See details above. ***")
        return 1

if __name__ == '__main__':
    sys.exit(main())
