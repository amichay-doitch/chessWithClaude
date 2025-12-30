"""
Chess Engine Test Suite
Evaluates engines on tactical, positional, and endgame positions.
"""

import chess
import yaml
import json
import argparse
import importlib
import time
from typing import List, Dict, Any
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class TestPosition:
    """A single test position."""
    id: str
    name: str
    category: str
    difficulty: str
    fen: str
    best_moves: List[str]
    avoid_moves: List[str]
    description: str
    points: int


class TestSuite:
    """Test suite for chess engines."""

    def __init__(self, yaml_file: str = "test_positions.yaml"):
        self.yaml_file = yaml_file
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
                    best_moves=pos_data['best_moves'],
                    avoid_moves=pos_data.get('avoid_moves', []),
                    description=pos_data['description'],
                    points=pos_data['points']
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
        verbose: bool = True
    ) -> Dict[str, Any]:
        """
        Test an engine on all positions.

        Args:
            engine_module_name: Name of engine module (e.g., 'engine_v5')
            depth: Search depth
            time_limit: Time limit per position
            verbose: Print detailed output

        Returns:
            Dictionary with test results
        """
        if verbose:
            print(f"\n{'='*70}")
            print(f"Testing {engine_module_name}")
            print(f"{'='*70}")
            print(f"Depth: {depth} | Time Limit: {time_limit}s | Positions: {len(self.positions)}")
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
            'total_score': 0,
            'max_score': 0,
            'category_scores': defaultdict(lambda: {'score': 0, 'max': 0, 'passed': 0, 'failed': 0}),
            'position_results': [],
            'test_date': time.strftime('%Y-%m-%d %H:%M:%S')
        }

        for i, pos in enumerate(self.positions, 1):
            board = chess.Board(pos.fen)
            engine = engine_class(max_depth=depth, time_limit=time_limit)

            if verbose:
                print(f"\n[{i}/{len(self.positions)}] {pos.id}: {pos.name}")
                print(f"  Category: {pos.category} | Difficulty: {pos.difficulty} | Points: {pos.points}")

            # Search for best move
            start_time = time.time()
            try:
                result = engine.search(board)
                move = result.best_move
                search_time = time.time() - start_time

                move_uci = move.uci() if move else "none"

                # Convert move to SAN for display
                try:
                    move_san = board.san(move) if move else "none"
                except:
                    move_san = move_uci

                # Check if move is good
                is_correct = move_uci in pos.best_moves
                is_bad = move_uci in pos.avoid_moves

                if is_correct:
                    score = pos.points
                    status = "PASS"
                    symbol = "✓"
                elif is_bad:
                    score = 0
                    status = "FAIL"
                    symbol = "✗"
                else:
                    score = pos.points // 2  # Partial credit
                    status = "PARTIAL"
                    symbol = "~"

                if verbose:
                    # Convert expected moves to SAN
                    expected_san = []
                    for best_uci in pos.best_moves:
                        try:
                            best_move = chess.Move.from_uci(best_uci)
                            expected_san.append(board.san(best_move))
                        except:
                            expected_san.append(best_uci)

                    print(f"  Expected: {', '.join(expected_san)}")
                    print(f"  Engine:   {move_san} ({move_uci}) {symbol} {status}")
                    print(f"  Score:    {score}/{pos.points}")
                    print(f"  Time:     {search_time:.2f}s | Nodes: {result.nodes_searched:,} | Eval: {result.score}")

                # Update results
                results['total_score'] += score
                results['max_score'] += pos.points

                # Category scores
                cat = pos.category
                results['category_scores'][cat]['score'] += score
                results['category_scores'][cat]['max'] += pos.points
                if is_correct:
                    results['category_scores'][cat]['passed'] += 1
                else:
                    results['category_scores'][cat]['failed'] += 1

                # Position result
                results['position_results'].append({
                    'id': pos.id,
                    'name': pos.name,
                    'category': pos.category,
                    'difficulty': pos.difficulty,
                    'fen': pos.fen,
                    'expected_moves': pos.best_moves,
                    'engine_move': move_uci,
                    'engine_move_san': move_san,
                    'correct': is_correct,
                    'status': status,
                    'score': score,
                    'max': pos.points,
                    'time': search_time,
                    'nodes': result.nodes_searched,
                    'eval': result.score,
                    'depth_reached': result.depth
                })

            except Exception as e:
                if verbose:
                    print(f"  ERROR: {e}")
                results['position_results'].append({
                    'id': pos.id,
                    'name': pos.name,
                    'category': pos.category,
                    'error': str(e),
                    'score': 0,
                    'max': pos.points
                })
                results['max_score'] += pos.points
                results['category_scores'][pos.category]['max'] += pos.points
                results['category_scores'][pos.category]['failed'] += 1

        return results


def print_summary(results: Dict[str, Any]):
    """Print test results summary."""
    if not results:
        return

    print(f"\n{'='*70}")
    print(f"{results['engine']} - TEST SUMMARY")
    print(f"{'='*70}")

    total_pct = (results['total_score'] / results['max_score'] * 100) if results['max_score'] > 0 else 0
    print(f"\nOverall Score: {results['total_score']}/{results['max_score']} ({total_pct:.1f}%)")

    print(f"\nCategory Breakdown:")
    print(f"{'-'*70}")
    for category, scores in sorted(results['category_scores'].items()):
        cat_pct = (scores['score'] / scores['max'] * 100) if scores['max'] > 0 else 0
        status_icon = "+" if cat_pct >= 70 else "~" if cat_pct >= 50 else "X"
        status_text = "GOOD" if cat_pct >= 70 else "OK" if cat_pct >= 50 else "WEAK"

        print(f"  {status_icon} {category.capitalize():15s}: {scores['score']:3d}/{scores['max']:3d} ({cat_pct:5.1f}%) - {status_text}")
        print(f"    Passed: {scores['passed']}, Failed: {scores['failed']}")

    print(f"\n{'='*70}")
    print(f"Recommendations:")
    print(f"{'-'*70}")

    weak_categories = []
    for cat, scores in results['category_scores'].items():
        pct = (scores['score'] / scores['max'] * 100) if scores['max'] > 0 else 0
        if pct < 60:
            weak_categories.append((cat, pct))

    if weak_categories:
        for cat, pct in sorted(weak_categories, key=lambda x: x[1]):
            if cat == 'tactical':
                print(f"  * Improve tactical vision - only {pct:.0f}% on {cat} positions")
                print(f"    > Consider: deeper search, better move ordering, tactical pruning")
            elif cat == 'checkmate':
                print(f"  * Strengthen checkmate detection - only {pct:.0f}% on {cat} positions")
                print(f"    > Consider: check extensions, mate threat evaluation")
            elif cat == 'endgame':
                print(f"  * Enhance endgame play - only {pct:.0f}% on {cat} positions")
                print(f"    > Consider: king activity, pawn advancement, opposition")
            elif cat == 'positional':
                print(f"  * Improve positional understanding - only {pct:.0f}% on {cat} positions")
                print(f"    > Consider: piece mobility, pawn structure, weak squares")
    else:
        print(f"  + Strong performance across all categories!")
        print(f"  > Continue refining search speed and depth")

    print(f"{'='*70}\n")


def compare_engines(results_list: List[Dict[str, Any]]):
    """Compare multiple engine results."""
    if len(results_list) < 2:
        return

    print(f"\n{'='*70}")
    print(f"ENGINE COMPARISON")
    print(f"{'='*70}")

    # Overall comparison
    print(f"\nOverall Scores:")
    print(f"{'-'*70}")
    for r in sorted(results_list, key=lambda x: x['total_score'], reverse=True):
        pct = (r['total_score'] / r['max_score'] * 100) if r['max_score'] > 0 else 0
        print(f"  {r['engine']:25s}: {r['total_score']:3d}/{r['max_score']:3d} ({pct:5.1f}%)")

    # Category comparison
    all_categories = set()
    for r in results_list:
        all_categories.update(r['category_scores'].keys())

    print(f"\nCategory Comparison:")
    print(f"{'-'*70}")
    for cat in sorted(all_categories):
        print(f"\n  {cat.capitalize()}:")
        for r in results_list:
            if cat in r['category_scores']:
                scores = r['category_scores'][cat]
                pct = (scores['score'] / scores['max'] * 100) if scores['max'] > 0 else 0
                print(f"    {r['engine']:25s}: {scores['score']:3d}/{scores['max']:3d} ({pct:5.1f}%) | Pass: {scores['passed']}, Fail: {scores['failed']}")

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
