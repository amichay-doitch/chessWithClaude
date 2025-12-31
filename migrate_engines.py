"""
Script to migrate engine files to use shared engine_base and engine_pst modules.
"""

import re
import sys

def migrate_engine_file(filepath):
    """Migrate an engine file to use shared modules."""

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if already migrated
    if 'from engine_base import' in content:
        print(f"{filepath} already migrated, skipping...")
        return False

    # Replace imports
    old_imports = r'''import chess
import time
from typing import Optional
from dataclasses import dataclass
from collections import defaultdict


@dataclass
class SearchResult:
    """Result from engine search."""
    best_move: chess.Move
    score: int
    depth: int
    nodes_searched: int
    time_spent: float


# Transposition table entry types
TT_EXACT = 0
TT_ALPHA = 1
TT_BETA = 2


@dataclass
class TTEntry:
    """Transposition table entry."""
    key: int
    depth: int
    score: int
    flag: int
    best_move: Optional\[chess.Move\]'''

    new_imports = '''import chess
import time
from collections import defaultdict
from engine_base import (
    SearchResult, TTEntry, TT_EXACT, TT_ALPHA, TT_BETA,
    INFINITY, MATE_SCORE, TT_SIZE, CENTER, EXTENDED_CENTER,
    PASSED_PAWN_BONUS, get_game_phase
)
from engine_pst import get_pst_value'''

    content = re.sub(old_imports, new_imports, content, flags=re.DOTALL)

    # Remove duplicate constants and tables
    patterns_to_remove = [
        (r'    # Center squares\s+CENTER = \[.*?\]\s+EXTENDED_CENTER = \[.*?\]', ''),
        (r'    # Piece-square tables\s+PAWN_TABLE_MG = \[.*?\]', ''),
        (r'    PAWN_TABLE_EG = \[.*?\]', ''),
        (r'    KNIGHT_TABLE = \[.*?\]', ''),
        (r'    BISHOP_TABLE = \[.*?\]', ''),
        (r'    ROOK_TABLE = \[.*?\]', ''),
        (r'    QUEEN_TABLE = \[.*?\]', ''),
        (r'    KING_TABLE_MG = \[.*?\]', ''),
        (r'    KING_TABLE_EG = \[.*?\]', ''),
        (r'    # Passed pawn bonus by rank\s+PASSED_PAWN_BONUS = \[.*?\]', ''),
        (r'    # Constants\s+INFINITY = \d+\s+MATE_SCORE = \d+\s+TT_SIZE = .*', ''),
    ]

    for pattern, replacement in patterns_to_remove:
        content = re.sub(pattern, replacement, content, flags=re.DOTALL)

    # Remove duplicate methods
    # Remove get_game_phase method
    get_game_phase_pattern = r'    def get_game_phase\(self, board: chess\.Board\) -> float:.*?return 1\.0 - min\(phase / 24\.0, 1\.0\)'
    content = re.sub(get_game_phase_pattern, '', content, flags=re.DOTALL)

    # Remove get_pst_value method
    get_pst_value_pattern = r'    def get_pst_value\(self, piece: chess\.Piece, square: int, phase: float\) -> int:.*?return 0'
    content = re.sub(get_pst_value_pattern, '', content, flags=re.DOTALL)

    # Replace self.X with X for constants
    replacements = [
        (r'self\.CENTER\b', 'CENTER'),
        (r'self\.EXTENDED_CENTER\b', 'EXTENDED_CENTER'),
        (r'self\.PASSED_PAWN_BONUS\b', 'PASSED_PAWN_BONUS'),
        (r'self\.INFINITY\b', 'INFINITY'),
        (r'self\.MATE_SCORE\b', 'MATE_SCORE'),
        (r'self\.TT_SIZE\b', 'TT_SIZE'),
        (r'self\.get_game_phase\(', 'get_game_phase('),
        (r'self\.get_pst_value\(', 'get_pst_value('),
    ]

    for pattern, replacement in replacements:
        content = re.sub(pattern, replacement, content)

    # Write back
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"Migrated {filepath}")
    return True

if __name__ == '__main__':
    files = [
        'engine_pool/engine_v3.py',
        'engine_pool/engine_v4.py',
        'engine_pool/engine_fast.py',
        'engine_pool/engine_v5_fast.py',
        'engine_pool/engine_v5_optimized.py',
        'engine_pool/engine_v6.py',
        'engine_pool/engine_v6_fixed.py',
        'engine_pool/gemini.py',
    ]

    for filepath in files:
        try:
            migrate_engine_file(filepath)
        except Exception as e:
            print(f"Error migrating {filepath}: {e}")

    print("Migration complete!")
