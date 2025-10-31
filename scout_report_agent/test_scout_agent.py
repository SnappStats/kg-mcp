"""
Test script for Scout Report Agent

Usage:
    python scout_report_agent/test_scout_agent.py "Player Name"

Example:
    python scout_report_agent/test_scout_agent.py "Arch Manning"
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scout_report_agent.agent import generate_scout_report


def test_scout_agent(player_name: str):
    """Test the scout report agent with a player name."""

    print(f"\n{'='*80}")
    print(f"Testing Scout Report Agent")
    print(f"Player: {player_name}")
    print(f"{'='*80}\n")

    try:
        # Run the agent (need to pass graph_id)
        print(f"Generating scout report for {player_name}...\n")
        graph_id = os.getenv('GRAPH_ID', 'test_graph')
        result = generate_scout_report(graph_id, player_name)

        # Print the result
        print(f"\n{'='*80}")
        print(f"RESULT")
        print(f"{'='*80}\n")

        if isinstance(result, dict):
            # Pretty print the dict result
            print(json.dumps(result, indent=2))
            print(f"\n--- Summary ---")
            print(f"Notes length: {len(result.get('notes', ''))} characters")
            print(f"Number of sources: {len(result.get('sources', []))}")
        elif hasattr(result, 'model_dump_json'):
            # Legacy Pydantic model support
            print(json.dumps(json.loads(result.model_dump_json()), indent=2))
        else:
            print(result)

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
        print("Usage: python scout_report_agent/test_scout_agent.py \"Player Name\"")
        print("Example: python scout_report_agent/test_scout_agent.py \"Arch Manning\"")
        sys.exit(1)

    player_name = " ".join(sys.argv[1:])
    test_scout_agent(player_name)
