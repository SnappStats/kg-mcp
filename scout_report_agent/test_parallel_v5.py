#!/usr/bin/env python3
"""
Test script for parallel_scout_v5.py
"""

import sys
import json
from parallel_scout_v5 import generate_scout_report_parallel

def main():
    player_query = "Bryce Underwood, 2025 QB recruit"

    print(f"\nTesting parallel scout agent v5 for: {player_query}\n")
    print("="*80)

    result = generate_scout_report_parallel(player_query)

    print("\n" + "="*80)
    print("FINAL SCOUT REPORT:")
    print("="*80)
    print(json.dumps(result, indent=2))
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
