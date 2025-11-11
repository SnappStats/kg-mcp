"""
Parallel Scout Report Agent - Optimized with concurrent section research

Architecture:
1. Root Agent: Quick baseline player research (name, position, school, grad year)
2. ParallelAgent: 5 concurrent section-specific research agents
3. Formatter: Combines results into structured schema with inline citations
"""

import os
import asyncio
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
from .formatting_agent import format_to_schema

# Load environment
load_dotenv()

# =============================================================================
# ROOT AGENT - Quick baseline player identification
# =============================================================================

ROOT_PROMPT = """
You are a sports research coordinator. Your job is to quickly identify the player and store baseline info.

**CRITICAL: KEEP THIS FAST - 1-2 searches maximum!**

TASK:
1. Use google_search to quickly find the player's basic information ONLY:
   - Full legal name
   - Sport and position
   - High school or college (current team)
   - Graduation year or class year
   - City, State/location

2. If player is ambiguous, return: "AMBIGUOUS: [brief explanation with candidates]"
3. If player not found, return: "NOT FOUND: [brief explanation]"

CRITICAL: Do NOT research:
- Stats or performance details
- Recruiting rankings or offers
- Physical measurables
- Background or character info

That will be handled by specialized agents. Just confirm WHO the player is.

Output exactly in this format:
[Name] is a [year] [position] from [School] in [City, State]. Currently [college commitment or status if applicable].
"""


# =============================================================================
# SECTION-SPECIFIC RESEARCH AGENTS
# =============================================================================

PHYSICAL_PROFILE_PROMPT = """
You are researching the PHYSICAL PROFILE for a football player.

Context: $state.baseline_info

Research and document:
- Height, weight, measurables (arm length, hand size, wingspan if available)
- Athletic testing (40-yard dash, shuttle, broad jump, vertical, etc.)
- Physical attributes (build, frame, body type)
- Growth/development notes

Use google_search to find reliable sources. Include [1][2] style citations.

Keep notes concise but comprehensive. Focus ONLY on physical attributes.
"""

PERFORMANCE_PROMPT = """
You are researching ON-FIELD PERFORMANCE for a football player.

Context: $state.baseline_info

Research and document:
- Latest season statistics (passing/rushing/receiving yards, TDs, completion %, etc.)
- Previous season stats if relevant
- Game highlights and notable performances
- Film evaluation notes (mechanics, technique, football IQ)
- Performance trends

Use google_search to find reliable sources. Include [1][2] style citations.

Keep notes concise but comprehensive. Focus ONLY on performance and stats.
"""

RECRUITING_PROMPT = """
You are researching the RECRUITING PROFILE for a football player.

Context: $state.baseline_info

Research and document:
- Star rating (247Sports, ESPN, On3, Rivals)
- National/state/position rankings
- Scholarship offers received
- Recruitment timeline and commitment status
- Official/unofficial visits
- Recruiting analysts' evaluations

Use google_search to find reliable sources. Include [1][2] style citations.

Keep notes concise but comprehensive. Focus ONLY on recruiting information.
"""

BACKGROUND_PROMPT = """
You are researching BACKGROUND AND CONTEXT for a football player.

Context: $state.baseline_info

Research and document:
- High school program details and success
- Family background (parents, siblings who played sports)
- Academic information (GPA, academic honors if public)
- Multi-sport athlete status
- Early career development (youth leagues, camps)
- Geographic context (state football culture, competition level)

Use google_search to find reliable sources. Include [1][2] style citations.

Keep notes concise but comprehensive. Focus ONLY on background context.
"""

INTANGIBLES_PROMPT = """
You are researching INTANGIBLES AND CHARACTER for a football player.

Context: $state.baseline_info

Research and document:
- Leadership qualities (team captain, vocal leader, etc.)
- Work ethic and dedication
- Coachability and attitude
- Character assessments from coaches/teammates
- Community involvement or off-field activities
- Mental makeup and competitiveness
- Any character concerns or red flags

Use google_search to find reliable sources. Include [1][2] style citations.

Keep notes concise but comprehensive. Focus ONLY on intangibles and character.
"""


# =============================================================================
# CREATE THE PARALLEL RESEARCH AGENTS
# =============================================================================

def create_parallel_scout_agent():
    """
    Creates a SequentialAgent that:
    1. Gets baseline info from root agent
    2. Runs 5 parallel section-specific research agents
    3. Combines and formats into structured output

    Returns:
        Agent: The configured parallel scout agent
    """
    # Root agent - quick player identification
    root_agent = Agent(
        name="baseline_researcher",
        model="gemini-2.5-flash",
        instruction=ROOT_PROMPT,
        tools=[google_search],
        output_key="baseline_info",  # Store result for subagents
    )

    # Section-specific parallel agents
    physical_agent = Agent(
        name="physical_researcher",
        model="gemini-2.5-flash",
        instruction=PHYSICAL_PROFILE_PROMPT,
        tools=[google_search],
        output_key="physical_notes",
    )

    performance_agent = Agent(
        name="performance_researcher",
        model="gemini-2.5-flash",
        instruction=PERFORMANCE_PROMPT,
        tools=[google_search],
        output_key="performance_notes",
    )

    recruiting_agent = Agent(
        name="recruiting_researcher",
        model="gemini-2.5-flash",
        instruction=RECRUITING_PROMPT,
        tools=[google_search],
        output_key="recruiting_notes",
    )

    background_agent = Agent(
        name="background_researcher",
        model="gemini-2.5-flash",
        instruction=BACKGROUND_PROMPT,
        tools=[google_search],
        output_key="background_notes",
    )

    intangibles_agent = Agent(
        name="intangibles_researcher",
        model="gemini-2.5-flash",
        instruction=INTANGIBLES_PROMPT,
        tools=[google_search],
        output_key="intangibles_notes",
    )

    # Parallel execution of all section researchers
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

    # Merger agent - combines all research notes
    merger_prompt = """
You are combining research notes from multiple specialized agents into a comprehensive scout report.

You have access to these research sections:
- Baseline Info: $state.baseline_info
- Physical Profile: $state.physical_notes
- Performance: $state.performance_notes
- Recruiting: $state.recruiting_notes
- Background: $state.background_notes
- Intangibles: $state.intangibles_notes

TASK:
1. Combine ALL sections into comprehensive research notes
2. Preserve ALL [1][2] style citations from each section
3. Organize into clear sections:
   - Player Identity (from baseline)
   - Physical Profile
   - On-Field Performance
   - Recruiting Profile
   - Background & Context
   - Intangibles & Character

4. Create a consolidated sources list with all unique URLs

Output format:
## Player Identity
[combined baseline info with citations]

## Physical Profile
[combined physical notes with citations]

## On-Field Performance
[combined performance notes with citations]

## Recruiting Profile
[combined recruiting notes with citations]

## Background & Context
[combined background notes with citations]

## Intangibles & Character
[combined intangibles notes with citations]

## Sources
[1] URL
[2] URL
...
"""

    merger_agent = Agent(
        name="research_merger",
        model="gemini-2.5-flash",
        instruction=merger_prompt,
        output_key="combined_notes",
    )

    # Sequential pipeline: root → parallel → merger
    pipeline = SequentialAgent(
        name="scout_report_pipeline",
        sub_agents=[
            root_agent,
            parallel_researchers,
            merger_agent,
        ],
    )

    return pipeline


# =============================================================================
# MAIN ENTRY POINT (compatible with existing MCP interface)
# =============================================================================

async def generate_scout_report_parallel_async(player_query: str) -> dict:
    """
    Generate a scout report using parallel research agents (async).

    Args:
        player_query: Player name and disambiguating context

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """
    # Create the agent pipeline
    agent = create_parallel_scout_agent()

    # Set up session
    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="parallel_scout_agent",
        user_id="system"
    )

    # Create runner
    runner = Runner(
        agent=agent,
        app_name="parallel_scout_agent",
        session_service=session_service
    )

    # Run the agent
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=f"Research: {player_query}")]
    )

    result_stream = runner.run_async(
        user_id="system",
        session_id=session.id,
        new_message=user_content
    )

    # Collect combined notes from merger agent output
    combined_notes = None
    all_text = []

    async for event in result_stream:
        print(f"Event: {type(event).__name__}")

        # Look for text content
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        all_text.append(part.text)
                        print(f"  Got text: {part.text[:100]}...")

    # Use the last substantial text output (should be from merger agent)
    for text in reversed(all_text):
        if len(text) > 200 and ('##' in text or 'Player' in text):
            combined_notes = text
            break

    if not combined_notes:
        return {
            "text": "Unable to complete research - no results from research agents"
        }

    print(f"\nCombined notes length: {len(combined_notes)}")
    print(f"First 200 chars: {combined_notes[:200]}")

    # Parse sources from the combined notes
    sources = []
    for line in combined_notes.split('\n'):
        if line.strip().startswith('[') and ']' in line and 'http' in line:
            # Extract URL from citation like "[1] URL"
            try:
                url = line.split(']', 1)[1].strip()
                if url.startswith('http'):
                    sources.append(url)
            except:
                pass

    print(f"Found {len(sources)} sources")

    # Format to structured schema
    scout_report = format_to_schema(
        research_notes=combined_notes,
        sources=sources
    )

    return scout_report.model_dump()


def generate_scout_report_parallel(player_query: str) -> dict:
    """
    Generate a scout report using parallel research agents (sync wrapper).

    Args:
        player_query: Player name and disambiguating context

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """
    return asyncio.run(generate_scout_report_parallel_async(player_query))


# For backward compatibility with existing agent.py
agent = None  # This will be created dynamically when needed
