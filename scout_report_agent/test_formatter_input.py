#!/usr/bin/env python3
"""
Simple test to see what the formatter agent receives from research agents
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types

load_dotenv()

# Simple research agent with google_search
research_agent = Agent(
    name="test_researcher",
    model="gemini-2.5-flash",
    description="Researches player info",
    instruction="Research Bryce Underwood, 2025 QB. Find his height and school. Use google_search.",
    tools=[google_search],
    output_key="research_output",
)

# Formatter agent that tells us what it sees
formatter_agent = Agent(
    name="test_formatter",
    model="gemini-2.5-flash",
    description="Reports what research it received",
    instruction="""
You received research in session state at key 'research_output'.

Your task: Tell me exactly what you see in {research_output}.

Specifically:
1. Does the text contain any citation markers like [0], [1], [0, 1], etc.?
2. If yes, show me 2 examples of statements with those citation markers
3. If no, just show me the first 2 sentences of what you received

Output your response as plain text.
""",
    tools=[],
)

# Sequential pipeline
pipeline = SequentialAgent(
    name="test_pipeline",
    sub_agents=[research_agent, formatter_agent],
)


async def test():
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="test_pipeline",
        user_id="test_user"
    )

    runner = Runner(
        agent=pipeline,
        app_name="test_pipeline",
        session_service=session_service
    )

    user_content = types.Content(
        role='user',
        parts=[types.Part(text="Test query")]
    )

    result_stream = runner.run_async(
        user_id="test_user",
        session_id=session.id,
        new_message=user_content
    )

    print("\n" + "="*80)
    print("WHAT THE FORMATTER SEES:")
    print("="*80)

    async for event in result_stream:
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        print(part.text)

    print("="*80 + "\n")


if __name__ == "__main__":
    asyncio.run(test())
