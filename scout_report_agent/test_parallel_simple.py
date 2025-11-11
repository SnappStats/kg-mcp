#!/usr/bin/env python3
"""
Simple test of parallel scout agent
"""

import sys
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
sys.path.insert(0, str(Path(__file__).parent.parent))

from scout_report_agent.parallel_scout_v4 import generate_scout_report_parallel

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 test_parallel_simple.py \"Player Name\"")
        sys.exit(1)

    player_query = " ".join(sys.argv[1:])
    print(f"\nTesting parallel scout agent for: {player_query}\n")

    start = time.time()
    try:
        result = generate_scout_report_parallel(player_query)
        elapsed = time.time() - start

        print(f"\n{'='*80}")
        print(f"RESULT (completed in {elapsed:.2f}s)")
        print(f"{'='*80}\n")

        if "text" in result:
            print(f"Error/Feedback: {result['text']}")
        elif "player" in result:
            import json

            # Print summary
            print(f"✓ Success!")
            print(f"Player: {result.get('player', {}).get('name', 'N/A')}")
            print(f"Tags: {', '.join(result.get('tags', []))}")
            print(f"Analysis sections: {len(result.get('analysis', []))}")
            print(f"Stats: {len(result.get('stats', []))}")
            print(f"Citations: {len(result.get('citations', []))}")

            # Print full player info
            print(f"\n{'='*80}")
            print("PLAYER INFO")
            print(f"{'='*80}\n")
            player = result.get('player', {})
            print(f"Name: {player.get('name', 'N/A')}")
            print(f"Physicals: {json.dumps(player.get('physicals', {}), indent=2)}")
            print(f"Socials: {json.dumps(player.get('socials', {}), indent=2)}")

            # Print all stats
            print(f"\n{'='*80}")
            print("STATS")
            print(f"{'='*80}\n")
            for i, stat in enumerate(result.get('stats', []), 1):
                print(f"{i}. {stat}")

            # Print all analysis sections with FULL content
            print(f"\n{'='*80}")
            print("ANALYSIS SECTIONS (FULL)")
            print(f"{'='*80}\n")
            for i, section in enumerate(result.get('analysis', []), 1):
                print(f"\n{i}. {section.get('title', 'N/A')}")
                print("-" * 80)
                print(section.get('content', ''))
                print()

            # Print all citations
            print(f"\n{'='*80}")
            print("CITATIONS")
            print(f"{'='*80}\n")
            for i, citation in enumerate(result.get('citations', []), 1):
                print(f"{i}. {citation}")

            # Print full JSON at the end
            print(f"\n{'='*80}")
            print("FULL JSON OUTPUT")
            print(f"{'='*80}\n")
            print(json.dumps(result, indent=2))

        else:
            print(f"Unexpected format: {list(result.keys())}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
