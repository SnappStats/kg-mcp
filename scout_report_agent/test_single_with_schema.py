#!/usr/bin/env python3
"""
Test single ADK agent with google_search AND output_schema
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types
from pydantic import BaseModel

load_dotenv()


class PhysicalProfile(BaseModel):
    """Physical profile schema"""
    height: str
    weight: str
    notes: str


async def test_single_with_schema():
    """Test a single agent with both google_search and output_schema"""

    agent = Agent(
        name="test_researcher",
        model="gemini-2.5-flash",
        instruction="""
Research the player's physical profile using google_search.
Find height, weight, and athletic measurables.
""",
        tools=[google_search],
        output_schema=PhysicalProfile,  # Both google_search AND output_schema
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

    # Collect events
    grounding_found = False
    all_urls = []
    final_json = None

    async for event in result_stream:
        print(f"\nEvent: {type(event).__name__}")

        # Check for grounding metadata
        if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
            grounding_found = True
            gm = event.grounding_metadata
            print(f"  ✓ HAS GROUNDING_METADATA with {len(gm.grounding_chunks)} chunks")
            if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                for i, chunk in enumerate(gm.grounding_chunks):
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = chunk.web.uri
                        print(f"    [{i}] {uri[:80]}...")
                        all_urls.append(uri)

        # Check for structured output
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(f"  Text: {part.text[:150]}...")
                        try:
                            import json
                            final_json = json.loads(part.text)
                        except:
                            pass

    print(f"\n{'='*80}")
    print("SUMMARY:")
    print(f"{'='*80}")
    print(f"Grounding metadata found: {grounding_found}")
    print(f"Total URLs: {len(all_urls)}")
    print(f"Structured JSON received: {final_json is not None}")
    if final_json:
        import json
        print(f"\nJSON Output:\n{json.dumps(final_json, indent=2)}")


if __name__ == "__main__":
    asyncio.run(test_single_with_schema())
