"""
Benchmark script to compare engine performance.
"""

import chess
import time
from engine_pool.engine_v5_fast import ChessEngine as EngineFast
from engine_pool.engine_v5_optimized import ChessEngine as EngineOptimized


def benchmark_engine(engine_class, name, positions, time_limit=3):
    """Benchmark an engine on multiple positions."""
    print(f"\n{'=' * 60}")
    print(f"Testing {name}")
    print('=' * 60)

    total_nodes = 0
    total_time = 0
    total_depth = 0

    for i, fen in enumerate(positions, 1):
        board = chess.Board(fen)
        engine = engine_class(max_depth=20, time_limit=time_limit)

        result = engine.search(board)

        total_nodes += result.nodes_searched
        total_time += result.time_spent
        total_depth += result.depth

        print(f"Position {i}: depth={result.depth}, nodes={result.nodes_searched:,}, "
              f"time={result.time_spent:.2f}s, nps={result.nodes_searched/result.time_spent:,.0f}")

    avg_nodes = total_nodes / len(positions)
    avg_time = total_time / len(positions)
    avg_depth = total_depth / len(positions)
    avg_nps = total_nodes / total_time

    print(f"\n{name} AVERAGES:")
    print(f"  Avg Depth: {avg_depth:.1f}")
    print(f"  Avg Nodes: {avg_nodes:,.0f}")
    print(f"  Avg Time: {avg_time:.2f}s")
    print(f"  Avg NPS: {avg_nps:,.0f}")

    return {
        'name': name,
        'avg_depth': avg_depth,
        'avg_nodes': avg_nodes,
        'avg_time': avg_time,
        'avg_nps': avg_nps
    }


def main():
    # Test positions (diverse set)
    positions = [
        # Starting position
        "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        # Open position
        "r1bqkb1r/pppp1ppp/2n2n2/1B2p3/4P3/5N2/PPPP1PPP/RNBQK2R w KQkq - 4 4",
        # Tactical position
        "r1bq1rk1/ppp2ppp/2np1n2/2b1p3/2B1P3/2NP1N2/PPP2PPP/R1BQR1K1 w - - 0 8",
        # Endgame
        "8/5k2/3p4/1p1Pp2p/pP2Pp1P/P4P1K/8/8 b - - 99 50",
        # Complex middlegame
        "r2q1rk1/ppp2ppp/2n1bn2/2bpp3/4P3/2PP1N2/PPB2PPP/RNBQ1RK1 w - - 0 9",
    ]

    print("\n" + "=" * 60)
    print("CHESS ENGINE PERFORMANCE BENCHMARK")
    print("=" * 60)
    print(f"Positions: {len(positions)}")
    print(f"Time limit: 3s per position")
    print("=" * 60)

    # Benchmark both engines
    results = []
    results.append(benchmark_engine(EngineFast, "engine_v5_fast", positions))
    results.append(benchmark_engine(EngineOptimized, "engine_v5_optimized", positions))

    # Compare results
    print("\n" + "=" * 60)
    print("COMPARISON")
    print("=" * 60)

    fast_nps = results[0]['avg_nps']
    opt_nps = results[1]['avg_nps']
    speedup = opt_nps / fast_nps

    fast_depth = results[0]['avg_depth']
    opt_depth = results[1]['avg_depth']
    depth_gain = opt_depth - fast_depth

    print(f"Speed improvement: {speedup:.1f}x faster")
    print(f"  {results[0]['name']}: {fast_nps:,.0f} nps")
    print(f"  {results[1]['name']}: {opt_nps:,.0f} nps")
    print()
    print(f"Search depth improvement: +{depth_gain:.1f} ply")
    print(f"  {results[0]['name']}: {fast_depth:.1f} avg depth")
    print(f"  {results[1]['name']}: {opt_depth:.1f} avg depth")
    print("=" * 60)


if __name__ == "__main__":
    main()
