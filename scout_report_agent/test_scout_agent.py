"""
Test script for Scout Report Agent

Usage:
    doppler run -- python3 scout_report_agent/test_scout_agent.py "Player Name"

Example:
    doppler run -- python3 scout_report_agent/test_scout_agent.py "Arch Manning"
"""

import os
import sys
import json
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from scout_report_agent.agent import agent
from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.genai import types


def test_scout_agent(player_name: str):
    """Test the scout report agent with a player name."""

    print(f"\n{'='*80}")
    print(f"Testing Scout Report Agent")
    print(f"Player: {player_name}")
    print(f"{'='*80}\n")

    try:
        # Get SESSION_SERVICE_URI from environment
        session_service_uri = os.environ.get('SESSION_SERVICE_URI')
        if not session_service_uri:
            print("ERROR: SESSION_SERVICE_URI not found in environment")
            print("Make sure you're running with doppler: doppler run -- python3 ...")
            return None

        agent_engine_id = session_service_uri.split('/')[-1]

        # Create session service
        session_service = VertexAiSessionService(agent_engine_id=agent_engine_id)

        # Create a runner for the agent
        runner = Runner(
            agent=agent,
            app_name=agent_engine_id,
            session_service=session_service
        )

        print(f"Generating scout report for {player_name}...\n")
        print("This may take 30-60 seconds as the agent researches...\n")

        # Create user message
        user_content = types.Content(
            role='user',
            parts=[types.Part(text=player_name)]
        )

        # Run the agent synchronously
        result = runner.run(new_message=user_content)

        # Print the result
        print(f"\n{'='*80}")
        print(f"RESULT")
        print(f"{'='*80}\n")

        # The result should be a ScoutReport object
        if hasattr(result, 'model_dump_json'):
            # Pydantic model - ScoutReport
            result_json = json.loads(result.model_dump_json())
            print(json.dumps(result_json, indent=2))

            print(f"\n--- Summary ---")
            print(f"Player: {result_json.get('player', {}).get('name', 'N/A')}")
            print(f"Tags: {', '.join(result_json.get('tags', []))}")
            print(f"Analysis sections: {len(result_json.get('analysis', []))}")
            print(f"Stats: {len(result_json.get('stats', []))}")
            print(f"Citations: {len(result_json.get('citations', []))}")

            # Show first analysis item as example
            if result_json.get('analysis'):
                first_analysis = result_json['analysis'][0]
                print(f"\nFirst Analysis Section: {first_analysis.get('title', 'N/A')}")
                content = first_analysis.get('content', '')
                print(f"Content preview ({len(content)} chars): {content[:300]}...")
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
        print("Usage: doppler run -- python3 scout_report_agent/test_scout_agent.py \"Player Name\"")
        print("Example: doppler run -- python3 scout_report_agent/test_scout_agent.py \"Arch Manning\"")
        sys.exit(1)

    player_name = " ".join(sys.argv[1:])
    test_scout_agent(player_name)
