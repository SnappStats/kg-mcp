#!/usr/bin/env python3
"""
Test script for parallel_scout_v5.py
"""

import sys
import json
import time
from parallel_scout_v5 import generate_scout_report_parallel

def main():
    player_query = "Bryce Johnson, IOL wedding high school"

    print(f"\nTesting parallel scout agent v5 for: {player_query}\n")
    print("="*80)

    start_time = time.time()
    result = generate_scout_report_parallel(player_query)
    end_time = time.time()

    elapsed_time = end_time - start_time

    print("\n" + "="*80)
    print("FINAL SCOUT REPORT:")
    print("="*80)
    print(json.dumps(result, indent=2))
    print("="*80)
    print(f"\n⏱️  Total execution time: {elapsed_time:.2f} seconds ({elapsed_time/60:.2f} minutes)\n")

if __name__ == "__main__":
    main()
