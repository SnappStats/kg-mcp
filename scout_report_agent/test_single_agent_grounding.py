#!/usr/bin/env python3
"""
Test single ADK agent with google_search to see grounding metadata
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()

async def test_single_agent():
    """Test a single agent with google_search and inspect grounding metadata"""

    agent = Agent(
        name="test_researcher",
        model="gemini-2.5-flash",
        description="Research assistant",
        instruction="""
Research the player's PHYSICAL PROFILE using google_search.

Find and document:
- Height, weight, measurables
- Athletic testing results
- Physical attributes

Focus ONLY on physical attributes.
""",
        tools=[google_search],
    )

    # Set up session
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="test_agent",
        user_id="system"
    )

    # Create runner
    runner = Runner(
        agent=agent,
        app_name="test_agent",
        session_service=session_service
    )

    # Run the agent
    user_content = types.Content(
        role='user',
        parts=[types.Part(text="Research Bryce Underwood's physical profile")]
    )

    result_stream = runner.run_async(
        user_id="system",
        session_id=session.id,
        new_message=user_content
    )

    # Collect all events and look for grounding metadata
    event_count = 0
    grounding_count = 0
    all_urls = []

    async for event in result_stream:
        event_count += 1
        print(f"\n{'='*80}")
        print(f"EVENT {event_count}: {type(event).__name__}")
        print(f"{'='*80}")

        # Check for grounding metadata
        if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
            grounding_count += 1
            gm = event.grounding_metadata
            print(f"✓ HAS GROUNDING METADATA!")
            print(f"  Type: {type(gm)}")
            print(f"  Dir: {[attr for attr in dir(gm) if not attr.startswith('_')]}")

            if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                print(f"  Grounding chunks: {len(gm.grounding_chunks)}")
                for i, chunk in enumerate(gm.grounding_chunks):
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = chunk.web.uri
                        title = chunk.web.title if hasattr(chunk.web, 'title') else 'N/A'
                        print(f"    [{i}] {title}")
                        print(f"        {uri}")
                        all_urls.append(uri)

            if hasattr(gm, 'grounding_supports') and gm.grounding_supports:
                print(f"  Grounding supports: {len(gm.grounding_supports)}")
        else:
            print("  No grounding metadata")

        # Check content
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"  Text content: {part.text[:200]}...")

    print(f"\n{'='*80}")
    print(f"SUMMARY")
    print(f"{'='*80}")
    print(f"Total events: {event_count}")
    print(f"Events with grounding metadata: {grounding_count}")
    print(f"Total URLs collected: {len(all_urls)}")
    if all_urls:
        print("\nAll URLs:")
        for i, url in enumerate(all_urls, 1):
            print(f"  {i}. {url}")

if __name__ == "__main__":
    asyncio.run(test_single_agent())
