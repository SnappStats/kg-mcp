#!/usr/bin/env python3
"""
Test script for Scout Report Agent (Two-Agent Approach)

Usage:
    python3 scout_report_agent/test_scout_agent.py "Player Name"

Example:
    python3 scout_report_agent/test_scout_agent.py "Arch Manning"
"""

import os
import sys
import json
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scout_report_agent import generate_scout_report


def test_scout_agent(player_name: str):
    """Test the scout report agent with a player name."""

    print(f"\n{'='*80}")
    print(f"Testing Scout Report Agent (Two-Agent Approach)")
    print(f"Player: {player_name}")
    print(f"{'='*80}\n")

    try:
        print(f"Generating scout report for {player_name}...\n")
        print("This may take 30-60 seconds as the agent researches...\n")

        # Call the generate_scout_report function
        result = generate_scout_report(player_name)

        # Print the result
        print(f"\n{'='*80}")
        print(f"RESULT")
        print(f"{'='*80}\n")

        # Check result type
        if result["type"] == "feedback":
            # Feedback message for clarification
            print("FEEDBACK MESSAGE (would be shown to root agent):")
            print(result["message"])
        elif result["type"] == "scout_report":
            # Success - got a scout report
            scout_report = result["data"]

            # Convert to JSON for display
            result_json = json.loads(scout_report.model_dump_json())
            print(json.dumps(result_json, indent=2))

            print(f"\n--- Summary ---")
            print(f"Player: {result_json.get('player', {}).get('name', 'N/A')}")
            print(f"Tags: {', '.join(result_json.get('tags', []))}")
            print(f"Analysis sections: {len(result_json.get('analysis', []))}")
            print(f"Stats: {len(result_json.get('stats', []))}")
            print(f"  {result_json.get('stats', [])}")
            print(f"Citations: {len(result_json.get('citations', []))}")

            # Show first analysis item as example
            if result_json.get('analysis'):
                first_analysis = result_json['analysis'][0]
                print(f"\nFirst Analysis Section: {first_analysis.get('title', 'N/A')}")
                content = first_analysis.get('content', '')
                print(f"Content preview ({len(content)} chars): {content[:300]}...")
        else:
            print(f"Unknown result type: {result}")

        print(f"\n{'='*80}")
        print(f"Test completed successfully!")
        print(f"{'='*80}\n")

        return result

    except Exception as e:
        print(f"\n{'='*80}")
        print(f"ERROR")
        print(f"{'='*80}\n")
        print(f"Error running scout agent: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scout_report_agent/test_scout_agent.py \"Player Name\"")
        print("Example: python3 scout_report_agent/test_scout_agent.py \"Arch Manning\"")
        sys.exit(1)

    player_name = " ".join(sys.argv[1:])
    test_scout_agent(player_name)
