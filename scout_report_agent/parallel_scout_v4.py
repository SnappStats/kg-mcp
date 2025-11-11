"""
Parallel Scout Report Agent - V4 with ADK
Uses ADK ParallelAgent with output_schema on root orchestrator
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool
from google.genai import types
from .scout_report_schema import ScoutReport

# Load environment
load_dotenv()

# =============================================================================
# SECTION-SPECIFIC RESEARCH AGENTS (Parallel)
# =============================================================================

# Physical Profile Agent
physical_agent = Agent(
    name="physical_researcher",
    model="gemini-2.5-flash",
    description="Researches player physical profile and measurables",
    instruction="""
Research the player's PHYSICAL PROFILE using google_search.

Find and document:
- Height, weight, measurables (arm length, hand size, wingspan)
- Athletic testing (40-yard dash, shuttle, broad jump, vertical)
- Physical attributes (build, frame, body type)
- Growth/development notes

Focus ONLY on physical attributes.
""",
    tools=[google_search],
    output_key="physical_notes",
)

# Performance Agent
performance_agent = Agent(
    name="performance_researcher",
    model="gemini-2.5-flash",
    description="Researches player on-field performance and statistics",
    instruction="""
Research the player's ON-FIELD PERFORMANCE using google_search.

Find and document:
- Latest season statistics (passing/rushing/receiving yards, TDs, completion %)
- Previous season stats if relevant
- Game highlights and notable performances
- Film evaluation notes (mechanics, technique, football IQ)
- Performance trends

Focus ONLY on performance and stats.
""",
    tools=[google_search],
    output_key="performance_notes",
)

# Recruiting Agent
recruiting_agent = Agent(
    name="recruiting_researcher",
    model="gemini-2.5-flash",
    description="Researches player recruiting profile and rankings",
    instruction="""
Research the player's RECRUITING PROFILE using google_search.

Find and document:
- Star rating (247Sports, ESPN, On3, Rivals)
- National/state/position rankings
- Scholarship offers received
- Recruitment timeline and commitment status
- Official/unofficial visits
- Recruiting analysts' evaluations

Focus ONLY on recruiting information.
""",
    tools=[google_search],
    output_key="recruiting_notes",
)

# Background Agent
background_agent = Agent(
    name="background_researcher",
    model="gemini-2.5-flash",
    description="Researches player background and context",
    instruction="""
Research the player's BACKGROUND AND CONTEXT using google_search.

Find and document:
- High school program details and success
- Family background (parents, siblings who played sports)
- Academic information (GPA, academic honors if public)
- Multi-sport athlete status
- Early career development (youth leagues, camps)
- Geographic context (state football culture, competition level)

Focus ONLY on background context.
""",
    tools=[google_search],
    output_key="background_notes",
)

# Intangibles Agent
intangibles_agent = Agent(
    name="intangibles_researcher",
    model="gemini-2.5-flash",
    description="Researches player intangibles and character",
    instruction="""
Research the player's INTANGIBLES AND CHARACTER using google_search.

Find and document:
- Leadership qualities (team captain, vocal leader)
- Work ethic and dedication
- Coachability and attitude
- Character assessments from coaches/teammates
- Community involvement or off-field activities
- Mental makeup and competitiveness
- Any character concerns or red flags

Focus ONLY on intangibles and character.
""",
    tools=[google_search],
    output_key="intangibles_notes",
)

# Parallel execution of all research agents
parallel_researchers = ParallelAgent(
    name="parallel_section_researchers",
    sub_agents=[
        physical_agent,
        performance_agent,
        recruiting_agent,
        background_agent,
        intangibles_agent,
    ],
)

# =============================================================================
# ROOT ORCHESTRATOR AGENT (with output_schema)
# =============================================================================

ROOT_PROMPT = """
You are a scout report generator. Your job is to create a comprehensive, structured scout report.

WORKFLOW:
1. Use the `physical_researcher` agent tool to research physical profile
2. Use the `performance_researcher` agent tool to research performance
3. Use the `recruiting_researcher` agent tool to research recruiting
4. Use the `background_researcher` agent tool to research background
5. Use the `intangibles_researcher` agent tool to research intangibles

After collecting all research, synthesize it into the structured ScoutReport format:

**CRITICAL OUTPUT REQUIREMENTS:**
* Create 3-6 key statistics as complete statements with season/year
* Create analysis items for each major section (Physical Profile, Performance, Recruiting, Background, Intangibles)
  - Analysis content should include inline citations in markdown format: ([Source Name](url))
  - Extract source names from domains (e.g., "247Sports", "ESPN", "On3")
* Populate player fields (name, physicals dict with height/weight/etc, socials dict if available)
* Populate tags with searchable info (sport, position, school, location, grad year, college, star rating, etc.)
* Populate stats list with 3-6 key performance stats
* Populate citations list with all source URLs used

The output will automatically be formatted according to the ScoutReport schema.
"""

# Create root orchestrator with output schema
root_agent = Agent(
    name="scout_report_orchestrator",
    model="gemini-2.5-flash",
    instruction=ROOT_PROMPT,
    tools=[
        AgentTool(agent=physical_agent),
        AgentTool(agent=performance_agent),
        AgentTool(agent=recruiting_agent),
        AgentTool(agent=background_agent),
        AgentTool(agent=intangibles_agent),
        # Can't mix AgentTool and google_search - subagents have google_search
    ],
    output_schema=ScoutReport,  # Forced structured output!
)

# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

async def generate_scout_report_parallel_async(player_query: str) -> dict:
    """
    Generate a scout report using parallel research agents with ADK.

    Args:
        player_query: Player name and disambiguating context

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """
    # Set up session
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="parallel_scout_agent",
        user_id="system"
    )

    # Create runner
    runner = Runner(
        agent=root_agent,
        app_name="parallel_scout_agent",
        session_service=session_service
    )

    # Run the agent
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=f"Generate a comprehensive scout report for: {player_query}")]
    )

    result_stream = runner.run_async(
        user_id="system",
        session_id=session.id,
        new_message=user_content
    )

    # Collect the structured output and grounding metadata
    scout_report = None
    final_response = None
    all_citations = []

    async for event in result_stream:
        # Capture the final response (only from root agent, not subagents)
        if hasattr(event, 'content') and event.content:
            final_response = event.content

        # Extract grounding metadata from all events (subagents and root)
        if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
            gm = event.grounding_metadata
            print(f"  ✓ Found grounding_metadata with {len(gm.grounding_chunks) if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks else 0} chunks")
            if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                for chunk in gm.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = chunk.web.uri
                        # Resolve Vertex AI redirect URLs
                        if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                            try:
                                import requests
                                resp = requests.head(uri, allow_redirects=True, timeout=3)
                                actual_url = resp.url
                                if actual_url != uri:
                                    uri = actual_url
                                    print(f"    Resolved: {uri}")
                            except Exception as e:
                                print(f"    Failed to resolve: {e}")
                        if uri:
                            all_citations.append(uri)

    # Print only the final root agent response
    print("\n" + "="*80)
    print("FINAL RESPONSE FROM ROOT AGENT:")
    print("="*80)
    print(final_response)
    print("="*80 + "\n")

    if final_response and hasattr(final_response, 'parts'):
        for part in final_response.parts:
            if hasattr(part, 'text') and part.text:
                # With output_schema, this should be JSON
                try:
                    import json
                    scout_report = json.loads(part.text)
                    print("✓ Successfully parsed structured output from root agent")
                except Exception as e:
                    print(f"✗ Failed to parse JSON: {e}")

    if not scout_report:
        return {
            "text": "Unable to complete research - no structured output received"
        }

    # Deduplicate citations and add any that weren't in the structured output
    unique_citations = list(dict.fromkeys(all_citations))
    if unique_citations:
        # Merge with citations from structured output
        existing_citations = set(scout_report.get('citations', []))
        for citation in unique_citations:
            if citation not in existing_citations:
                scout_report.setdefault('citations', []).append(citation)
        print(f"✓ Added {len(unique_citations)} citations from grounding metadata")

    return scout_report


def generate_scout_report_parallel(player_query: str) -> dict:
    """
    Generate a scout report using parallel research agents (sync wrapper).

    Args:
        player_query: Player name and disambiguating context

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """
    return asyncio.run(generate_scout_report_parallel_async(player_query))
