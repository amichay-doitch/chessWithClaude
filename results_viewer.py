"""
Results Viewer - Display and analyze tournament match results

This script analyzes completed tournament matches and displays comprehensive statistics.
"""

import json
import os
import sys
import chess.pgn
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse

# Fix Windows terminal encoding for Unicode box characters
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ResultsViewer:
    """Analyzes and displays tournament results."""

    def __init__(self, match_dir: str):
        """Initialize with path to match directory."""
        self.match_dir = Path(match_dir)
        if not self.match_dir.exists():
            raise FileNotFoundError(f"Match directory not found: {match_dir}")

        self.games = []
        self.stats = {
            'total_games': 0,
            'engine1_wins': 0,
            'engine2_wins': 0,
            'draws': 0,
            'engine1_white_wins': 0,
            'engine1_white_draws': 0,
            'engine1_white_losses': 0,
            'engine1_black_wins': 0,
            'engine1_black_draws': 0,
            'engine1_black_losses': 0,
            'total_moves': 0,
            'longest_game': 0,
            'shortest_game': float('inf'),
            'longest_game_num': 0,
            'shortest_game_num': 0,
            'engine1_total_time': 0,
            'engine2_total_time': 0,
            'engine1_total_nodes': 0,
            'engine2_total_nodes': 0,
            'engine1_name': '',
            'engine2_name': '',
        }

    def load_games(self):
        """Load all PGN files from match directory."""
        pgn_files = sorted(self.match_dir.glob('*.pgn'))

        if not pgn_files:
            print(f"No PGN files found in {self.match_dir}")
            return

        print(f"Loading {len(pgn_files)} games...")

        for pgn_file in pgn_files:
            try:
                with open(pgn_file) as f:
                    game = chess.pgn.read_game(f)
                    if game:
                        self.games.append(game)
                        self._analyze_game(game, len(self.games))
            except Exception as e:
                print(f"Error loading {pgn_file}: {e}")

        print(f"Loaded {len(self.games)} games successfully.\n")

    def _analyze_game(self, game, game_num: int):
        """Analyze a single game and update statistics."""
        # Get game info
        white = game.headers.get('White', '')
        black = game.headers.get('Black', '')
        result = game.headers.get('Result', '*')

        # Extract engine names (first occurrence sets them)
        if not self.stats['engine1_name']:
            self.stats['engine1_name'] = white.split('(')[0].strip()
        if not self.stats['engine2_name']:
            self.stats['engine2_name'] = black.split('(')[0].strip() if black.split('(')[0].strip() != self.stats['engine1_name'] else black.split('(')[0].strip()

        # Determine which engine is which
        engine1_is_white = self.stats['engine1_name'] in white

        # Count moves
        moves = 0
        node = game
        while node.variations:
            moves += 1
            node = node.variations[0]

        self.stats['total_games'] += 1
        self.stats['total_moves'] += moves

        # Track longest/shortest
        if moves > self.stats['longest_game']:
            self.stats['longest_game'] = moves
            self.stats['longest_game_num'] = game_num
        if moves < self.stats['shortest_game']:
            self.stats['shortest_game'] = moves
            self.stats['shortest_game_num'] = game_num

        # Parse performance data from headers
        try:
            white_time = float(game.headers.get('WhiteAvgTime', '0'))
            black_time = float(game.headers.get('BlackAvgTime', '0'))
            white_nodes = int(game.headers.get('WhiteAvgNodes', '0'))
            black_nodes = int(game.headers.get('BlackAvgNodes', '0'))

            if engine1_is_white:
                self.stats['engine1_total_time'] += white_time * moves
                self.stats['engine2_total_time'] += black_time * moves
                self.stats['engine1_total_nodes'] += white_nodes * moves
                self.stats['engine2_total_nodes'] += black_nodes * moves
            else:
                self.stats['engine1_total_time'] += black_time * moves
                self.stats['engine2_total_time'] += white_time * moves
                self.stats['engine1_total_nodes'] += black_nodes * moves
                self.stats['engine2_total_nodes'] += white_nodes * moves
        except (ValueError, TypeError):
            pass

        # Count results
        if result == '1-0':
            if engine1_is_white:
                self.stats['engine1_wins'] += 1
                self.stats['engine1_white_wins'] += 1
            else:
                self.stats['engine2_wins'] += 1
                self.stats['engine1_black_losses'] += 1
        elif result == '0-1':
            if engine1_is_white:
                self.stats['engine2_wins'] += 1
                self.stats['engine1_white_losses'] += 1
            else:
                self.stats['engine1_wins'] += 1
                self.stats['engine1_black_wins'] += 1
        elif result == '1/2-1/2':
            self.stats['draws'] += 1
            if engine1_is_white:
                self.stats['engine1_white_draws'] += 1
            else:
                self.stats['engine1_black_draws'] += 1

    def display_results(self):
        """Display comprehensive results in formatted output."""
        if not self.games:
            print("No games to analyze!")
            return

        s = self.stats

        # Calculate percentages
        total = s['total_games']
        e1_score = s['engine1_wins'] + (s['draws'] * 0.5)
        e2_score = s['engine2_wins'] + (s['draws'] * 0.5)
        e1_percentage = (e1_score / total * 100) if total > 0 else 0
        e2_percentage = (e2_score / total * 100) if total > 0 else 0

        decisive_games = s['engine1_wins'] + s['engine2_wins']
        decisive_pct = (decisive_games / total * 100) if total > 0 else 0

        # White/Black stats for engine1
        e1_white_games = s['engine1_white_wins'] + s['engine1_white_draws'] + s['engine1_white_losses']
        e1_black_games = s['engine1_black_wins'] + s['engine1_black_draws'] + s['engine1_black_losses']
        e1_white_score = s['engine1_white_wins'] + (s['engine1_white_draws'] * 0.5)
        e1_black_score = s['engine1_black_wins'] + (s['engine1_black_draws'] * 0.5)
        e1_white_pct = (e1_white_score / e1_white_games * 100) if e1_white_games > 0 else 0
        e1_black_pct = (e1_black_score / e1_black_games * 100) if e1_black_games > 0 else 0

        # White/Black stats for engine2
        e2_white_games = e1_black_games  # Engine2 plays white when engine1 plays black
        e2_black_games = e1_white_games
        e2_white_wins = s['engine1_black_losses']
        e2_white_draws = s['engine1_black_draws']
        e2_white_losses = s['engine1_black_wins']
        e2_black_wins = s['engine1_white_losses']
        e2_black_draws = s['engine1_white_draws']
        e2_black_losses = s['engine1_white_wins']
        e2_white_score = e2_white_wins + (e2_white_draws * 0.5)
        e2_black_score = e2_black_wins + (e2_black_draws * 0.5)
        e2_white_pct = (e2_white_score / e2_white_games * 100) if e2_white_games > 0 else 0
        e2_black_pct = (e2_black_score / e2_black_games * 100) if e2_black_games > 0 else 0

        # Performance metrics
        avg_game_length = s['total_moves'] / total if total > 0 else 0
        e1_avg_time = (s['engine1_total_time'] / s['total_moves']) if s['total_moves'] > 0 else 0
        e2_avg_time = (s['engine2_total_time'] / s['total_moves']) if s['total_moves'] > 0 else 0
        e1_avg_nodes = (s['engine1_total_nodes'] / s['total_moves']) if s['total_moves'] > 0 else 0
        e2_avg_nodes = (s['engine2_total_nodes'] / s['total_moves']) if s['total_moves'] > 0 else 0
        e1_nps = (e1_avg_nodes / e1_avg_time) if e1_avg_time > 0 else 0
        e2_nps = (e2_avg_nodes / e2_avg_time) if e2_avg_time > 0 else 0

        # Elo estimate
        elo_diff = self._estimate_elo(e1_percentage)

        # Print formatted results
        width = 62
        print("╔" + "═" * width + "╗")
        print(f"║ {'MATCH RESULTS':^{width}} ║")
        print(f"║ {s['engine1_name']} vs {s['engine2_name']:^{width-len(s['engine1_name'])-4}} ║")
        print("╠" + "═" * width + "╣")

        print(f"║ {'Configuration:':<{width}} ║")
        print(f"║   Games Played:     {total:<{width-20}} ║")
        print(f"║   Match Directory:  {self.match_dir.name:<{width-20}} ║")
        print("╠" + "═" * width + "╣")

        print(f"║ {' OVERALL RESULTS':^{width}} ║")
        print("╠" + "═" * width + "╣")
        print(f"║ {s['engine1_name'] + ':':<20} {s['engine1_wins']:>3} wins  |  {s['draws']:>3} draws  |  {s['engine2_wins']:>3} losses{' ':<{width-52}} ║")
        print(f"║ {s['engine2_name'] + ':':<20} {s['engine2_wins']:>3} wins  |  {s['draws']:>3} draws  |  {s['engine1_wins']:>3} losses{' ':<{width-52}} ║")
        print(f"║ {'':<{width}} ║")
        print(f"║ Score: {s['engine1_name']} {e1_score:.1f} - {e2_score:.1f} {s['engine2_name']}{' ':<{width-len(s['engine1_name'])-len(s['engine2_name'])-len(f'Score:  {e1_score:.1f} - {e2_score:.1f} ')}} ║")
        print("╠" + "═" * width + "╣")

        print(f"║ {' DETAILED BREAKDOWN':^{width}} ║")
        print("╠" + "═" * width + "╣")
        print(f"║ {s['engine1_name']} as White:{' ':<{width-len(s['engine1_name'])-11}} ║")
        print(f"║   W: {s['engine1_white_wins']:<3} D: {s['engine1_white_draws']:<3} L: {s['engine1_white_losses']:<3} ({e1_white_pct:.1f}%){' ':<{width-30}} ║")
        print(f"║ {'':<{width}} ║")
        print(f"║ {s['engine1_name']} as Black:{' ':<{width-len(s['engine1_name'])-11}} ║")
        print(f"║   W: {s['engine1_black_wins']:<3} D: {s['engine1_black_draws']:<3} L: {s['engine1_black_losses']:<3} ({e1_black_pct:.1f}%){' ':<{width-30}} ║")
        print("╠" + "═" * width + "╣")

        print(f"║ {s['engine2_name']} as White:{' ':<{width-len(s['engine2_name'])-11}} ║")
        print(f"║   W: {e2_white_wins:<3} D: {e2_white_draws:<3} L: {e2_white_losses:<3} ({e2_white_pct:.1f}%){' ':<{width-30}} ║")
        print(f"║ {'':<{width}} ║")
        print(f"║ {s['engine2_name']} as Black:{' ':<{width-len(s['engine2_name'])-11}} ║")
        print(f"║   W: {e2_black_wins:<3} D: {e2_black_draws:<3} L: {e2_black_losses:<3} ({e2_black_pct:.1f}%){' ':<{width-30}} ║")
        print("╠" + "═" * width + "╣")

        print(f"║ {' GAME STATISTICS':^{width}} ║")
        print("╠" + "═" * width + "╣")
        print(f"║ Average Game Length:     {avg_game_length:.1f} moves{' ':<{width-37}} ║")
        print(f"║ Longest Game:           {s['longest_game']:>3} moves (game #{s['longest_game_num']}){' ':<{width-47}} ║")
        print(f"║ Shortest Game:          {s['shortest_game']:>3} moves (game #{s['shortest_game_num']}){' ':<{width-48}} ║")
        print(f"║ Decisive Games:          {decisive_games}/{total} ({decisive_pct:.1f}%){' ':<{width-38}} ║")
        print(f"║ Draws:                   {s['draws']}/{total} ({(s['draws']/total*100):.1f}%){' ':<{width-35}} ║")
        print("╠" + "═" * width + "╣")

        if e1_avg_time > 0 and e2_avg_time > 0:
            print(f"║ {' PERFORMANCE METRICS':^{width}} ║")
            print("╠" + "═" * width + "╣")
            print(f"║ {s['engine1_name']} Avg Time/Move:      {e1_avg_time:.2f}s{' ':<{width-len(s['engine1_name'])-27}} ║")
            print(f"║ {s['engine1_name']} Avg Nodes/Move:     {e1_avg_nodes:>,.0f}{' ':<{width-len(s['engine1_name'])-28}} ║")
            print(f"║ {s['engine1_name']} Avg NPS:            {e1_nps:>,.0f}{' ':<{width-len(s['engine1_name'])-23}} ║")
            print(f"║ {'':<{width}} ║")
            print(f"║ {s['engine2_name']} Avg Time/Move:      {e2_avg_time:.2f}s{' ':<{width-len(s['engine2_name'])-27}} ║")
            print(f"║ {s['engine2_name']} Avg Nodes/Move:     {e2_avg_nodes:>,.0f}{' ':<{width-len(s['engine2_name'])-28}} ║")
            print(f"║ {s['engine2_name']} Avg NPS:            {e2_nps:>,.0f}{' ':<{width-len(s['engine2_name'])-23}} ║")
            print("╠" + "═" * width + "╣")

        print(f"║ {' ELO ESTIMATE':^{width}} ║")
        print("╠" + "═" * width + "╣")
        if elo_diff > 0:
            print(f"║ Estimated Elo Difference:  +{elo_diff:.0f} for {s['engine1_name']}{' ':<{width-len(s['engine1_name'])-36}} ║")
        elif elo_diff < 0:
            print(f"║ Estimated Elo Difference:  {elo_diff:.0f} for {s['engine1_name']}{' ':<{width-len(s['engine1_name'])-36}} ║")
        else:
            print(f"║ Estimated Elo Difference:  0 (equal strength){' ':<{width-47}} ║")
        print(f"║ {'':<{width}} ║")

        if abs(elo_diff) < 20:
            interpretation = "Engines appear equal in strength"
        elif elo_diff > 0:
            interpretation = f"{s['engine1_name']} appears ~{abs(elo_diff):.0f} Elo stronger"
        else:
            interpretation = f"{s['engine2_name']} appears ~{abs(elo_diff):.0f} Elo stronger"
        print(f"║ Interpretation: {interpretation}{' ':<{width-len(interpretation)-17}} ║")
        print("╚" + "═" * width + "╝")

        print(f"\nGames saved to: {self.match_dir}")

    def _estimate_elo(self, win_percentage: float) -> float:
        """
        Estimate Elo difference from win percentage.
        Formula: Elo_diff = -400 * log10(1/win_rate - 1)
        """
        if win_percentage >= 99.9:
            return 600  # Cap at reasonable max
        if win_percentage <= 0.1:
            return -600

        win_rate = win_percentage / 100
        if win_rate == 0.5:
            return 0

        import math
        elo_diff = -400 * math.log10(1/win_rate - 1)
        return elo_diff

    def export_json(self, output_file: Optional[str] = None):
        """Export results to JSON file."""
        if output_file is None:
            output_file = self.match_dir / "results_summary.json"

        data = {
            'match_directory': str(self.match_dir),
            'statistics': self.stats,
            'games': []
        }

        for i, game in enumerate(self.games, 1):
            game_data = {
                'number': i,
                'white': game.headers.get('White', ''),
                'black': game.headers.get('Black', ''),
                'result': game.headers.get('Result', '*'),
                'date': game.headers.get('Date', ''),
                'moves': sum(1 for _ in game.mainline_moves())
            }
            data['games'].append(game_data)

        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2)

        print(f"\nResults exported to: {output_file}")

    def export_csv(self, output_file: Optional[str] = None):
        """Export game list to CSV file."""
        if output_file is None:
            output_file = self.match_dir / "games_list.csv"

        with open(output_file, 'w') as f:
            f.write("Game,White,Black,Result,Moves,Date\n")
            for i, game in enumerate(self.games, 1):
                white = game.headers.get('White', '').replace(',', ';')
                black = game.headers.get('Black', '').replace(',', ';')
                result = game.headers.get('Result', '*')
                date = game.headers.get('Date', '')
                moves = sum(1 for _ in game.mainline_moves())
                f.write(f"{i},{white},{black},{result},{moves},{date}\n")

        print(f"Game list exported to: {output_file}")


def main():
    parser = argparse.ArgumentParser(description='View and analyze tournament results')
    parser.add_argument('match_dir', help='Path to match directory containing PGN files')
    parser.add_argument('--json', action='store_true', help='Export results to JSON')
    parser.add_argument('--csv', action='store_true', help='Export game list to CSV')
    parser.add_argument('--export-all', action='store_true', help='Export both JSON and CSV')

    args = parser.parse_args()

    try:
        viewer = ResultsViewer(args.match_dir)
        viewer.load_games()
        viewer.display_results()

        if args.json or args.export_all:
            viewer.export_json()

        if args.csv or args.export_all:
            viewer.export_csv()

    except FileNotFoundError as e:
        print(f"Error: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
