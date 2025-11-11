#!/usr/bin/env python3
"""
Speed test: Parallel vs Serial Scout Report Generation

Compares:
1. Current serial approach (research_agent.py)
2. New parallel approach (parallel_scout_agent.py)
"""

import time
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment
load_dotenv()

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scout_report_agent.research_agent import research_player
from scout_report_agent.formatting_agent import format_to_schema
from scout_report_agent.parallel_scout_agent import generate_scout_report_parallel


def test_serial(player_query: str):
    """Test the current serial approach"""
    print(f"\n{'='*80}")
    print(f"SERIAL APPROACH (Current)")
    print(f"{'='*80}\n")

    start = time.time()

    try:
        # Step 1: Research
        print("Step 1: Research player...")
        research_start = time.time()
        research_result = research_player(player_query)
        research_time = time.time() - research_start
        print(f"  ✓ Research completed in {research_time:.2f}s")

        if research_result["status"] != "success":
            print(f"  ✗ Research failed: {research_result.get('message')}")
            return None, time.time() - start

        # Step 2: Format
        print("Step 2: Format to schema...")
        format_start = time.time()
        scout_report = format_to_schema(
            research_notes=research_result["notes"],
            sources=research_result["sources"]
        )
        format_time = time.time() - format_start
        print(f"  ✓ Formatting completed in {format_time:.2f}s")

        total_time = time.time() - start

        print(f"\n{'='*80}")
        print(f"SERIAL RESULTS")
        print(f"{'='*80}")
        print(f"Research time: {research_time:.2f}s")
        print(f"Format time:   {format_time:.2f}s")
        print(f"TOTAL TIME:    {total_time:.2f}s")
        print(f"{'='*80}\n")

        result = scout_report.model_dump()
        print(f"Player: {result.get('player', {}).get('name', 'N/A')}")
        print(f"Tags: {len(result.get('tags', []))} tags")
        print(f"Analysis sections: {len(result.get('analysis', []))}")
        print(f"Stats: {len(result.get('stats', []))}")
        print(f"Citations: {len(result.get('citations', []))}")

        return result, total_time

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, time.time() - start


def test_parallel(player_query: str):
    """Test the new parallel approach"""
    print(f"\n{'='*80}")
    print(f"PARALLEL APPROACH (New)")
    print(f"{'='*80}\n")

    start = time.time()

    try:
        print("Running parallel scout report generation...")
        result = generate_scout_report_parallel(player_query)

        total_time = time.time() - start

        print(f"\n{'='*80}")
        print(f"PARALLEL RESULTS")
        print(f"{'='*80}")
        print(f"TOTAL TIME:    {total_time:.2f}s")
        print(f"{'='*80}\n")

        if "text" in result:
            print(f"Error: {result['text']}")
            return None, total_time

        print(f"Player: {result.get('player', {}).get('name', 'N/A')}")
        print(f"Tags: {len(result.get('tags', []))} tags")
        print(f"Analysis sections: {len(result.get('analysis', []))}")
        print(f"Stats: {len(result.get('stats', []))}")
        print(f"Citations: {len(result.get('citations', []))}")

        return result, total_time

    except Exception as e:
        print(f"  ✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return None, time.time() - start


def compare_results(serial_result, parallel_result):
    """Compare quality of results"""
    print(f"\n{'='*80}")
    print(f"QUALITY COMPARISON")
    print(f"{'='*80}\n")

    if not serial_result or not parallel_result:
        print("Cannot compare - one or both failed")
        return

    print("Serial:")
    print(f"  - Tags: {len(serial_result.get('tags', []))}")
    print(f"  - Analysis sections: {len(serial_result.get('analysis', []))}")
    print(f"  - Stats: {len(serial_result.get('stats', []))}")
    print(f"  - Citations: {len(serial_result.get('citations', []))}")

    print("\nParallel:")
    print(f"  - Tags: {len(parallel_result.get('tags', []))}")
    print(f"  - Analysis sections: {len(parallel_result.get('analysis', []))}")
    print(f"  - Stats: {len(parallel_result.get('stats', []))}")
    print(f"  - Citations: {len(parallel_result.get('citations', []))}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_parallel_vs_serial.py \"Player Name\"")
        print("Example: python3 test_parallel_vs_serial.py \"Bryce Underwood\"")
        sys.exit(1)

    player_query = " ".join(sys.argv[1:])

    print(f"\n{'#'*80}")
    print(f"SPEED TEST: Serial vs Parallel Scout Report")
    print(f"Player: {player_query}")
    print(f"{'#'*80}")

    # Test serial
    serial_result, serial_time = test_serial(player_query)

    # Wait a bit between tests
    print("\n\nWaiting 3 seconds before parallel test...\n")
    time.sleep(3)

    # Test parallel
    parallel_result, parallel_time = test_parallel(player_query)

    # Compare
    compare_results(serial_result, parallel_result)

    # Final summary
    print(f"\n{'='*80}")
    print(f"FINAL COMPARISON")
    print(f"{'='*80}")
    print(f"Serial:   {serial_time:.2f}s")
    print(f"Parallel: {parallel_time:.2f}s")

    if serial_time > 0 and parallel_time > 0:
        speedup = serial_time / parallel_time
        if speedup > 1:
            print(f"Speedup:  {speedup:.2f}x FASTER")
        else:
            print(f"Speedup:  {1/speedup:.2f}x SLOWER")

    print(f"{'='*80}\n")
