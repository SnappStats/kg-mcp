#!/usr/bin/env python3
"""
Test script for Scout Report Agent via MCP Server

Usage:
    python3 scout_report_agent/test_scout_agent.py "Player Name"

Example:
    python3 scout_report_agent/test_scout_agent.py "Arch Manning"

Prerequisites:
    - MCP server must be running: uv run fastmcp run server.py --transport http --port 8001
    - Set KG_MCP_SERVER in .env (e.g., http://localhost:8001)
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.mcp_tool.mcp_toolset import (
    McpToolset, StreamableHTTPConnectionParams
)
from google.genai import types


GRAPH_ID = os.environ.get('TEST_GRAPH_ID', 'test-graph-id')
USER_ID = 'test-user'


async def test_scout_agent(player_name: str):
    """Test the scout report agent via MCP server."""

    print(f"\n{'='*80}")
    print(f"Testing Scout Report Agent via MCP Server")
    print(f"Player: {player_name}")
    print(f"MCP Server: {os.environ.get('KG_MCP_SERVER', 'NOT SET')}")
    print(f"{'='*80}\n")

    try:
        print(f"Generating scout report for {player_name}...\n")
        print("This may take 30-60 seconds as the agent researches...\n")

        # Create a simple agent that calls the MCP tool
        session_service = InMemorySessionService()

        test_agent = Agent(
            name="test_scout_agent",
            model="gemini-2.5-flash",
            instruction=f"Call the generate_scout_report tool with the player query: {player_name}",
            tools=[
                McpToolset(
                    connection_params=StreamableHTTPConnectionParams(
                        url=os.environ['KG_MCP_SERVER'],
                        headers={'x-graph-id': GRAPH_ID},
                    ),
                    tool_filter=['generate_scout_report'],
                ),
            ],
        )

        session = await session_service.create_session(
            app_name="test_scout_agent",
            user_id=USER_ID
        )

        runner = Runner(
            agent=test_agent,
            app_name="test_scout_agent",
            session_service=session_service
        )

        user_content = types.Content(
            role='user',
            parts=[types.Part(text=f"Generate a scout report for {player_name}")]
        )

        result_stream = runner.run_async(
            user_id=USER_ID,
            session_id=session.id,
            new_message=user_content
        )

        # Collect the result
        result = None
        async for event in result_stream:
            print(f"Event: {event}")
            if hasattr(event, 'content') and event.content:
                if hasattr(event.content, 'parts') and event.content.parts:
                    for part in event.content.parts:
                        if hasattr(part, 'function_response') and part.function_response:
                            if part.function_response.name == 'generate_scout_report':
                                # Response might be dict or JSON string
                                response = part.function_response.response
                                if isinstance(response, str):
                                    result = json.loads(response)
                                else:
                                    result = response
                        elif hasattr(part, 'text') and part.text:
                            print(f"Agent response: {part.text}")

        if not result:
            print("\n⚠️  No result received from MCP tool")
            return None

        # Print the result
        print(f"\n{'='*80}")
        print(f"RESULT")
        print(f"{'='*80}\n")

        # Check result format
        if "text" in result:
            # Feedback message for clarification
            print("FEEDBACK MESSAGE (needs clarification):")
            print(result["text"])
        elif "player" in result:
            # Success - got a scout report
            print(json.dumps(result, indent=2))

            print(f"\n--- Summary ---")
            print(f"Player: {result.get('player', {}).get('name', 'N/A')}")
            print(f"Tags: {', '.join(result.get('tags', []))}")
            print(f"Analysis sections: {len(result.get('analysis', []))}")
            print(f"Stats: {len(result.get('stats', []))}")
            print(f"  {result.get('stats', [])}")
            print(f"Citations: {len(result.get('citations', []))}")

            # Show first analysis item as example
            if result.get('analysis'):
                first_analysis = result['analysis'][0]
                print(f"\nFirst Analysis Section: {first_analysis.get('title', 'N/A')}")
                content = first_analysis.get('content', '')
                print(f"Content preview ({len(content)} chars): {content[:300]}...")

            # Show report ID if stored
            if 'id' in result:
                print(f"\n✓ Scout report stored with ID: {result['id']}")
        else:
            print(f"Unknown result format: {result}")

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
        print("\nTroubleshooting:")
        print("1. Make sure MCP server is running: uv run fastmcp run server.py --transport http --port 8001")
        print("2. Check KG_MCP_SERVER in .env is set correctly")
        print("3. Verify Google Cloud credentials are configured")
        return None


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 scout_report_agent/test_scout_agent.py \"Player Name\"")
        print("Example: python3 scout_report_agent/test_scout_agent.py \"Arch Manning\"")
        print("\nPrerequisites:")
        print("1. Start MCP server: uv run fastmcp run server.py --transport http --port 8001")
        print("2. Set KG_MCP_SERVER in .env (e.g., http://localhost:8001)")
        sys.exit(1)

    player_name = " ".join(sys.argv[1:])
    asyncio.run(test_scout_agent(player_name))
