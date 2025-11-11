#!/usr/bin/env python3
"""
Test if ADK Agent can get grounded results with sources in metadata
"""

import os
import asyncio
import json
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.tools import google_search
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

load_dotenv()


PROMPT = """
You are a football recruiting researcher.

Use google_search to research the player and return a text summary with:
- Full name
- Position
- High school or college
- Height and weight

The grounding system will automatically provide citations for you.
"""


async def test_grounding():
    """Test if we can get research text AND grounding metadata with citations"""

    agent = Agent(
        name="test_agent",
        model="gemini-2.5-flash",
        instruction=PROMPT,
        tools=[google_search],
    )

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="test_agent",
        user_id="test_user"
    )

    runner = Runner(
        agent=agent,
        app_name="test_agent",
        session_service=session_service
    )

    user_content = types.Content(
        role='user',
        parts=[types.Part(text="Research Bryce Underwood, 2025 QB recruit")]
    )

    result_stream = runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=user_content
    )

    # Collect grounding data
    grounding_chunks = []
    grounding_supports = []

    async for event in result_stream:
        if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
            gm = event.grounding_metadata

            # Collect grounding chunks (sources)
            if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                for chunk in gm.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = chunk.web.uri
                        title = chunk.web.title if hasattr(chunk.web, 'title') else None
                        # Resolve Vertex AI redirect URLs
                        if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                            try:
                                import requests
                                resp = requests.head(uri, allow_redirects=True, timeout=3)
                                actual_url = resp.url
                                if actual_url != uri:
                                    uri = actual_url
                            except Exception:
                                pass
                        grounding_chunks.append({
                            'url': uri,
                            'title': title
                        })

            # Collect grounding supports (text segments with source attribution)
            if hasattr(gm, 'grounding_supports') and gm.grounding_supports:
                for support in gm.grounding_supports:
                    if hasattr(support, 'segment') and support.segment:
                        text = support.segment.text if hasattr(support.segment, 'text') else None
                        indices = list(support.grounding_chunk_indices) if hasattr(support, 'grounding_chunk_indices') else []
                        if text:
                            grounding_supports.append({
                                'text': text,
                                'source_indices': indices
                            })

    # Build the response structure
    response = {
        'claims': [],
        'sources': {}
    }

    # Add claims with citations
    for support in grounding_supports:
        text = support['text']
        indices = support['source_indices']
        if indices:
            claim_with_citation = f"{text} [{', '.join(map(str, indices))}]"
        else:
            claim_with_citation = text
        response['claims'].append(claim_with_citation)

    # Add sources
    for i, source in enumerate(grounding_chunks):
        response['sources'][str(i)] = source

    # Print the response
    print("\n" + "="*80)
    print("STRUCTURED RESPONSE:")
    print("="*80)
    print(json.dumps(response, indent=2))
    print("="*80)

    # Also print as plain text for readability
    print("\n" + "="*80)
    print("PLAIN TEXT WITH CITATIONS:")
    print("="*80)
    for claim in response['claims']:
        print(claim)
    print("\n" + "-"*80)
    print("SOURCES:")
    print("-"*80)
    for idx, source in response['sources'].items():
        print(f"[{idx}] {source['title']} - {source['url']}")
    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test_grounding())
