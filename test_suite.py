"""
Chess Engine Test Suite
Evaluates engines on tactical, positional, and endgame positions using Stockfish as reference.
"""

import chess
import yaml
import json
import argparse
import importlib
import time
import os
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict
from stockfish_analyzer import StockfishAnalyzer


@dataclass
class TestPosition:
    """A single test position."""
    id: str
    name: str
    category: str
    difficulty: str
    fen: str
    description: str


class TestSuite:
    """Test suite for chess engines."""

    def __init__(self, yaml_file: str = "test_positions.yaml", stockfish_path: str = None):
        self.yaml_file = yaml_file
        # Auto-detect stockfish in script directory
        if stockfish_path is None:
            script_dir = os.path.dirname(os.path.abspath(__file__))
            self.stockfish_path = os.path.join(script_dir, "stockfish-windows-x86-64-avx2.exe")
        else:
            self.stockfish_path = stockfish_path
        self.positions = self.load_positions()

    def load_positions(self) -> List[TestPosition]:
        """Load test positions from YAML file."""
        try:
            with open(self.yaml_file, 'r') as f:
                data = yaml.safe_load(f)

            positions = []
            for pos_data in data['test_positions']:
                positions.append(TestPosition(
                    id=pos_data['id'],
                    name=pos_data['name'],
                    category=pos_data['category'],
                    difficulty=pos_data['difficulty'],
                    fen=pos_data['fen'],
                    description=pos_data['description']
                ))

            print(f"Loaded {len(positions)} test positions from {self.yaml_file}")
            return positions

        except Exception as e:
            print(f"Error loading test positions: {e}")
            return []

    def run_engine_test(
        self,
        engine_module_name: str,
        depth: int = 6,
        time_limit: float = 2.0,
        verbose: bool = True,
        stockfish_depth: int = 20
    ) -> Dict[str, Any]:
        """
        Test an engine on all positions using Stockfish as reference.

        Args:
            engine_module_name: Name of engine module (e.g., 'engine_v5')
            depth: Search depth for engine being tested
            time_limit: Time limit per position
            verbose: Print detailed output
            stockfish_depth: Depth for Stockfish analysis (default: 20)

        Returns:
            Dictionary with test results
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"Testing {engine_module_name} (Stockfish-evaluated)")
            print(f"{'='*70}")
            print(f"Engine Depth: {depth} | Time Limit: {time_limit}s")
            print(f"Stockfish Depth: {stockfish_depth} | Positions: {len(self.positions)}")
            print(f"{'='*70}")

        # Import engine
        try:
            engine_module = importlib.import_module(engine_module_name)
            engine_class = engine_module.ChessEngine
        except Exception as e:
            print(f"Error importing {engine_module_name}: {e}")
            return None

        results = {
            'engine': engine_module_name,
            'depth': depth,
            'time_limit': time_limit,
            'stockfish_depth': stockfish_depth,
            'category_scores': defaultdict(lambda: {'scores': [], 'excellent': 0, 'ok': 0, 'poor': 0, 'terrible': 0}),
            'position_results': [],
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        # Initialize Stockfish
        with StockfishAnalyzer(self.stockfish_path, depth=stockfish_depth) as stockfish:

            for i, pos in enumerate(self.positions, 1):
                board = chess.Board(pos.fen)

                if verbose:
                    print(f"\n[{i}/{len(self.positions)}] {pos.id}: {pos.name}")
                    print(f"  Category: {pos.category} | Difficulty: {pos.difficulty}")

                # Search for best move
                start_time = time.time()
                try:
                    # 1. Get Stockfish's top 3 moves and eval
                    sf_analysis = stockfish.analyze(board, top_n=3, verbose=True)
                    eval_before = sf_analysis.evaluation

                    # 2. Run engine being tested
                    engine = engine_class(max_depth=depth, time_limit=time_limit)
                    result = engine.search(board)
                    engine_move = result.best_move
                    search_time = time.time() - start_time

                    if not engine_move:
                        raise ValueError("Engine returned no move")

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
                        eval_after = None  # Don't need to calculate
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

                        if abs(eval_before) < 0.01:  # Avoid division by zero for equal positions
                            score_pct = 0.0 if abs(eval_after) < 0.01 else -100.0
                        else:
                            score_pct = (eval_after / eval_before) - 1

                    # 5. Determine status
                    abs_score = abs(score_pct)
                    if abs_score <= 0.20:
                        status = "EXCELLENT"
                        symbol = "[OK]"
                        status_key = 'excellent'
                    elif abs_score <= 0.50:
                        status = "OK"
                        symbol = "~"
                        status_key = 'ok'
                    elif abs_score <= 1.00:
                        status = "POOR"
                        symbol = "[X]"
                        status_key = 'poor'
                    else:
                        status = "TERRIBLE"
                        symbol = "[XX]"
                        status_key = 'terrible'

                    # 6. Display results
                    if verbose:
                        engine_move_san = board.san(engine_move)

                        print(f"  Stockfish Top 3:")
                        for ma in sf_analysis.top_moves[:3]:
                            marker = " <- ENGINE" if engine_move == ma.move else ""
                            if ma.centipawn is not None:
                                eval_str = f"{ma.centipawn/100:+.2f}"
                            elif ma.mate is not None:
                                eval_str = f"M{ma.mate}"
                            else:
                                eval_str = "0.00"
                            print(f"    {ma.rank}. {board.san(ma.move)} ({eval_str}){marker}")

                        print(f"  Engine:    {engine_move_san} (rank: {move_rank or 'not in top 3'})")
                        if eval_after is not None:
                            print(f"             eval after move: {eval_after:+.2f}")
                        print(f"  Score:     {score_pct:+.1%} {symbol} {status}")
                        print(f"  Time:      {search_time:.2f}s | Nodes: {result.nodes_searched:,}")

                        if sf_analysis.verbose_stats:
                            print(f"  SF Stats:  {sf_analysis.verbose_stats.nodes:,} nodes @ {sf_analysis.verbose_stats.nps:,} nps")

                    # 7. Store results
                    cat = pos.category
                    results['category_scores'][cat]['scores'].append(score_pct)
                    results['category_scores'][cat][status_key] += 1

                    results['position_results'].append({
                        'id': pos.id,
                        'name': pos.name,
                        'category': pos.category,
                        'difficulty': pos.difficulty,
                        'fen': pos.fen,
                        'description': pos.description,

                        # Stockfish data
                        'stockfish_move': sf_analysis.best_move.uci(),
                        'stockfish_move_san': board.san(sf_analysis.best_move),
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

                        # Engine data
                        'engine_move': engine_move.uci(),
                        'engine_move_san': board.san(engine_move),
                        'engine_move_rank': move_rank,  # NEW: 1, 2, 3, or None
                        'engine_eval': eval_after,

                        # Scoring
                        'score_pct': score_pct,
                        'status': status,

                        # Performance stats
                        'time': search_time,
                        'nodes': result.nodes_searched,
                        'engine_internal_eval': result.score,
                        'depth_reached': result.depth,

                        # NEW: Verbose stats
                        'stockfish_nodes': sf_analysis.verbose_stats.nodes if sf_analysis.verbose_stats else None,
                        'stockfish_nps': sf_analysis.verbose_stats.nps if sf_analysis.verbose_stats else None,
                    })

                except Exception as e:
                    if verbose:
                        print(f"  ERROR: {e}")

                    results['position_results'].append({
                        'id': pos.id,
                        'name': pos.name,
                        'category': pos.category,
                        'difficulty': pos.difficulty,
                        'error': str(e),
                        'score_pct': -999.0,  # Mark as failed
                        'status': 'ERROR'
                    })
                    results['category_scores'][pos.category]['terrible'] += 1

        return results


def print_summary(results: Dict[str, Any]):
    """Print test results summary with Stockfish-based dynamic scoring."""
    if not results:
        return

    print(f"\n{'='*70}")
    print(f"{results['engine']} - TEST SUMMARY (Stockfish-evaluated)")
    print(f"{'='*70}")

    # Calculate overall statistics
    all_scores = []
    for cat_data in results['category_scores'].values():
        all_scores.extend(cat_data['scores'])

    if all_scores:
        avg_score = sum(all_scores) / len(all_scores)
        print(f"\nOverall Average Score: {avg_score:+.1%}")
        print(f"Total Positions: {len(all_scores)}")
    else:
        print(f"\nNo positions tested")

    print(f"\nCategory Breakdown:")
    print(f"{'-'*70}")
    for category, scores in sorted(results['category_scores'].items()):
        if not scores['scores']:
            continue

        avg = sum(scores['scores']) / len(scores['scores'])
        total = len(scores['scores'])
        excellent = scores['excellent']
        ok = scores['ok']
        poor = scores['poor']
        terrible = scores['terrible']

        # Determine status
        if excellent / total >= 0.7:
            status_icon = "[OK]"
            status_text = "STRONG"
        elif (excellent + ok) / total >= 0.5:
            status_icon = "~"
            status_text = "DECENT"
        else:
            status_icon = "[X]"
            status_text = "WEAK"

        print(f"  {status_icon} {category.capitalize():15s}: Avg: {avg:+.1%}")
        print(f"      [OK]{excellent} Excellent  ~{ok} OK  [X]{poor} Poor  [XX]{terrible} Terrible")

    print(f"\n{'='*70}")
    print(f"Recommendations:")
    print(f"{'-'*70}")

    weak_categories = []
    for cat, cat_data in results['category_scores'].items():
        if not cat_data['scores']:
            continue
        avg = sum(cat_data['scores']) / len(cat_data['scores'])
        total = len(cat_data['scores'])
        poor_rate = (cat_data['poor'] + cat_data['terrible']) / total
        if poor_rate >= 0.5:  # More than half are poor/terrible
            weak_categories.append((cat, avg, poor_rate))

    if weak_categories:
        for cat, avg, poor_rate in sorted(weak_categories, key=lambda x: x[1]):
            print(f"  * {cat.capitalize()}: {poor_rate:.0%} positions are poor/terrible (avg: {avg:+.1%})")
            if cat == 'tactical':
                print(f"    > Consider: deeper search, better move ordering, tactical pruning")
            elif cat == 'checkmate':
                print(f"    > Consider: check extensions, mate threat evaluation")
            elif cat == 'endgame':
                print(f"    > Consider: king activity, pawn advancement, opposition")
            elif cat == 'positional':
                print(f"    > Consider: piece mobility, pawn structure, weak squares")
    else:
        print(f"  ✓ Strong performance across all categories!")
        print(f"  > Continue refining search speed and depth")

    print(f"{'='*70}\n")


def compare_engines(results_list: List[Dict[str, Any]]):
    """Compare multiple engine results with Stockfish-based scoring."""
    if len(results_list) < 2:
        return

    print(f"\n{'='*70}")
    print(f"ENGINE COMPARISON (Stockfish-evaluated)")
    print(f"{'='*70}")

    # Calculate overall averages for sorting
    engine_averages = []
    for r in results_list:
        all_scores = []
        for cat_data in r['category_scores'].values():
            all_scores.extend(cat_data['scores'])
        avg = sum(all_scores) / len(all_scores) if all_scores else -999
        engine_averages.append((r['engine'], avg, len(all_scores)))

    # Overall comparison
    print(f"\nOverall Performance:")
    print(f"{'-'*70}")
    for engine, avg, total in sorted(engine_averages, key=lambda x: x[1], reverse=True):
        print(f"  {engine:25s}: {avg:+.1%} (avg across {total} positions)")

    # Category comparison
    all_categories = set()
    for r in results_list:
        all_categories.update(r['category_scores'].keys())

    print(f"\nCategory Comparison:")
    print(f"{'-'*70}")
    for cat in sorted(all_categories):
        print(f"\n  {cat.capitalize()}:")
        cat_results = []
        for r in results_list:
            if cat in r['category_scores']:
                cat_data = r['category_scores'][cat]
                if cat_data['scores']:
                    avg = sum(cat_data['scores']) / len(cat_data['scores'])
                    total = len(cat_data['scores'])
                    excellent = cat_data['excellent']
                    ok = cat_data['ok']
                    poor = cat_data['poor']
                    terrible = cat_data['terrible']
                    cat_results.append((r['engine'], avg, excellent, ok, poor, terrible, total))

        for engine, avg, exc, ok, pr, terr, total in sorted(cat_results, key=lambda x: x[1], reverse=True):
            print(f"    {engine:25s}: {avg:+.1%} | ✓{exc} ~{ok} ✗{pr} ✗✗{terr}")

    print(f"\n{'='*70}\n")


def main():
    parser = argparse.ArgumentParser(
        description='Test chess engines on tactical and strategic positions',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python test_suite.py --engine engine_v5
  python test_suite.py --engines engine_v5 engine_v6 --compare
  python test_suite.py --engine engine_v6 --depth 8 --time 5.0 --save results.json
        """
    )

    parser.add_argument('--engine', help='Single engine to test')
    parser.add_argument('--engines', nargs='+', help='Multiple engines to test and compare')
    parser.add_argument('--depth', type=int, default=6, help='Search depth (default: 6)')
    parser.add_argument('--time', type=float, default=2.0, help='Time limit per position in seconds (default: 2.0)')
    parser.add_argument('--yaml', default='test_positions.yaml', help='YAML file with test positions')
    parser.add_argument('--save', help='Save results to JSON file')
    parser.add_argument('--quiet', action='store_true', help='Suppress detailed output')
    parser.add_argument('--compare', action='store_true', help='Show comparison table (for multiple engines)')

    args = parser.parse_args()

    # Determine which engines to test
    engines_to_test = []
    if args.engine:
        engines_to_test = [args.engine]
    elif args.engines:
        engines_to_test = args.engines
    else:
        parser.error("Must specify --engine or --engines")

    # Load test suite
    test_suite = TestSuite(args.yaml)

    if not test_suite.positions:
        print("No test positions loaded. Exiting.")
        return

    # Run tests
    all_results = []
    for engine_name in engines_to_test:
        results = test_suite.run_engine_test(
            engine_name,
            depth=args.depth,
            time_limit=args.time,
            verbose=not args.quiet
        )

        if results:
            print_summary(results)
            all_results.append(results)

    # Compare if multiple engines
    if len(all_results) > 1 or args.compare:
        compare_engines(all_results)

    # Save results
    if args.save and all_results:
        with open(args.save, 'w') as f:
            json.dump(all_results, f, indent=2)
        print(f"Results saved to {args.save}")


if __name__ == "__main__":
    main()
