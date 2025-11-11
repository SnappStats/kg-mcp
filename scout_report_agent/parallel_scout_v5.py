"""
Parallel Scout Report Agent - V5 with ADK Sequential + Parallel
Architecture:
1. Baseline research agent (output_key="baseline_info")
2. ParallelAgent with 5 research agents (each with output_key)
3. Formatter agent (output_schema=ScoutReport) - produces final structured JSON

This properly uses ADK's workflow agents and grounding metadata with citations.
"""

import os
import asyncio
import json
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent, ParallelAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai import types
from scout_report_schema import ScoutReport

# Load environment
load_dotenv()

# =============================================================================
# 1. BASELINE RESEARCH AGENT
# =============================================================================

baseline_agent = Agent(
    name="baseline_researcher",
    model="gemini-2.5-flash",
    description="Performs initial baseline research on the player",
    instruction="""
You are the baseline researcher for a football recruiting scout report.

Your task: Perform broad initial research on the player to establish:
- Full name and position
- Current team/school and grad year
- Basic physical stats (height, weight)
- Recruiting status (committed, ranking)
- Any major awards or achievements

This baseline info will guide the specialized research agents.

Use google_search to gather this information efficiently.
""",
    tools=[google_search],
    output_key="baseline_info",
)

# =============================================================================
# 2. SECTION-SPECIFIC RESEARCH AGENTS (run in parallel)
# =============================================================================

physical_agent = Agent(
    name="physical_researcher",
    model="gemini-2.5-flash",
    description="Researches player physical profile and measurables",
    instruction="""
Research the player's PHYSICAL PROFILE using google_search.

Based on the baseline info in session state, find detailed information about:
- Height, weight, measurables (arm length, hand size, wingspan)
- Athletic testing results (40-yard dash, shuttle, broad jump, vertical)
- Physical attributes (build, frame, body type, athleticism)
- Growth trajectory and development notes

Focus ONLY on physical attributes and testing data.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="physical_research",
)

performance_agent = Agent(
    name="performance_researcher",
    model="gemini-2.5-flash",
    description="Researches player on-field performance and statistics",
    instruction="""
Research the player's ON-FIELD PERFORMANCE using google_search.

Based on the baseline info in session state, find:
- Career statistics (passing/rushing/receiving yards, TDs, etc.)
- Season-by-season performance trends
- Game film analysis and performance grades
- Championship/playoff performances
- Performance against top competition

Focus ONLY on on-field performance and statistics.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="performance_research",
)

recruiting_agent = Agent(
    name="recruiting_researcher",
    model="gemini-2.5-flash",
    description="Researches player recruiting profile and rankings",
    instruction="""
Research the player's RECRUITING PROFILE using google_search.

Based on the baseline info in session state, find:
- Current recruiting rankings (247, Rivals, On3, ESPN)
- Star rating and position ranking
- Recruiting interest (offers, visits, commitment status)
- Recruiting timeline and decision factors
- Comparisons to other recruits

Focus ONLY on recruiting rankings and recruitment process.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="recruiting_research",
)

background_agent = Agent(
    name="background_researcher",
    model="gemini-2.5-flash",
    description="Researches player background and personal story",
    instruction="""
Research the player's BACKGROUND AND STORY using google_search.

Based on the baseline info in session state, find:
- Family background and support system
- High school/college program and coaching
- Personal story, challenges overcome, motivations
- Academic performance and interests
- Community involvement and character

Focus ONLY on background, personal story, and character.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="background_research",
)

intangibles_agent = Agent(
    name="intangibles_researcher",
    model="gemini-2.5-flash",
    description="Researches player intangibles and leadership",
    instruction="""
Research the player's INTANGIBLES AND LEADERSHIP using google_search.

Based on the baseline info in session state, find:
- Leadership qualities and team captain roles
- Work ethic and coachability
- Mental toughness and competitiveness
- Football IQ and learning ability
- Character and off-field reputation
- Coach and teammate quotes about intangibles

Focus ONLY on intangibles, leadership, and character traits.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="intangibles_research",
)

# =============================================================================
# 3. PARALLEL RESEARCH COORDINATOR
# =============================================================================

parallel_research_agent = ParallelAgent(
    name="parallel_research_coordinator",
    sub_agents=[
        physical_agent,
        performance_agent,
        recruiting_agent,
        background_agent,
        intangibles_agent,
    ],
    description="Runs specialized research agents in parallel for speed",
)

# =============================================================================
# 4. FORMATTER AGENT (with output_schema)
# =============================================================================

formatter_agent = Agent(
    name="scout_report_formatter",
    model="gemini-2.5-flash",
    description="Formats all research into structured ScoutReport JSON",
    instruction="""
You are the final formatter for a football recruiting scout report.

Your task: Synthesize ALL the research from session state into a comprehensive,
structured scout report following the ScoutReport schema.

**Available Research in Session State:**
- {baseline_info} - Basic player info
- {physical_research} - Physical profile and measurables
- {performance_research} - On-field performance and stats
- {recruiting_research} - Recruiting rankings and profile
- {background_research} - Background and personal story
- {intangibles_research} - Leadership and intangibles

**CRITICAL: INLINE CITATIONS**
The research text from each agent contains statements with grounding citations in the format:
"Statement text [0, 1, 2]" where the numbers refer to source indices.

You MUST preserve these citations in your analysis content fields by converting them to markdown links:
- Find statements with citation patterns like [0, 1] or [2]
- Convert to markdown format: "Statement text [^1][^2]" or "Statement text [^3]"
- The citation numbers from research become footnote-style references
- Keep all citations inline with the content they support

**Output Requirements:**

1. **player.name**: Full name from baseline info
2. **player.physicals**: Extract key physical stats (Height, Weight, etc.) as dict
3. **player.socials**: Extract any social media handles found (Twitter, Instagram, etc.) as dict
4. **tags**: Smart, searchable tags - include sport, position, high school (prefix "High School:"),
   location, grad year, college status (prefix "College:", add "(committed)" if applicable),
   star rating with source, additional sports played
5. **analysis**: Create AnalysisItem entries for:
   - Awards and Accolades (title="Awards")
   - Strengths (title="Strengths")
   - Weaknesses (title="Weaknesses")
   - Notable Quotes (title="Quotes")
   **IMPORTANT**: Preserve inline citations from research in markdown format within content
6. **stats**: List 3-6 key performance statistics with season/year
   Format: "3,245 Passing Yards (2024/25)", "42 TD, 4 INT (2024/25)"
   Include inline citations if present in research
7. **citations**: Leave empty - will be populated from grounding metadata

**Critical Instructions:**
- Be comprehensive - synthesize ALL research provided
- **PRESERVE ALL INLINE CITATIONS** from research text in markdown format
- Use markdown formatting for analysis content
- Ensure stats are specific with seasons
- Make tags useful for searching/filtering
- Focus on facts from the research, not speculation

Output ONLY valid JSON matching the ScoutReport schema.
""",
    tools=[],  # No tools - just formats existing research
    output_schema=ScoutReport,
)

# =============================================================================
# 5. MAIN SEQUENTIAL PIPELINE
# =============================================================================

scout_report_pipeline = SequentialAgent(
    name="scout_report_pipeline",
    sub_agents=[
        baseline_agent,           # Step 1: Get baseline info
        parallel_research_agent,  # Step 2: Parallel deep research
        formatter_agent,          # Step 3: Format into structured output
    ],
    description="Complete scout report generation pipeline with parallel research",
)

# =============================================================================
# EXECUTION FUNCTION
# =============================================================================

async def generate_scout_report_parallel_async(player_query: str) -> dict:
    """
    Generate a scout report using the parallel research pipeline.

    Args:
        player_query: Player name and disambiguating context

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """
    print(f"\nGenerating scout report for: {player_query}\n")

    session_service = InMemorySessionService()
    session = await session_service.create_session(
        app_name="scout_report_pipeline",
        user_id="scout_user"
    )

    runner = Runner(
        agent=scout_report_pipeline,
        app_name="scout_report_pipeline",
        session_service=session_service
    )

    user_content = types.Content(
        role='user',
        parts=[types.Part(text=player_query)]
    )

    result_stream = runner.run_async(
        user_id="scout_user",
        session_id=session.id,
        new_message=user_content
    )

    # Collect grounding metadata and final response
    all_grounding_chunks = []
    final_response = None

    async for event in result_stream:
        # Collect grounding metadata from all agents
        if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
            gm = event.grounding_metadata
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

                        all_grounding_chunks.append(uri)

        # Capture final response (from formatter agent)
        if hasattr(event, 'content') and event.content:
            final_response = event.content

    # Parse the structured output from formatter agent
    scout_report = None
    if final_response and hasattr(final_response, 'parts'):
        for part in final_response.parts:
            if hasattr(part, 'text') and part.text:
                try:
                    scout_report = json.loads(part.text)
                    print("✓ Successfully parsed structured scout report from formatter agent")
                except Exception as e:
                    print(f"✗ Failed to parse JSON from formatter: {e}")
                    print(f"Raw text: {part.text[:200]}...")

    if not scout_report:
        return {
            "text": "Unable to complete scout report - no structured output received"
        }

    # Add deduplicated citations from grounding metadata
    unique_citations = list(dict.fromkeys(all_grounding_chunks))
    if unique_citations:
        scout_report.setdefault('citations', []).extend(unique_citations)
        # Deduplicate final list
        scout_report['citations'] = list(dict.fromkeys(scout_report['citations']))
        print(f"✓ Added {len(unique_citations)} unique citations from grounding metadata")

    return scout_report


def generate_scout_report_parallel(player_query: str) -> dict:
    """
    Synchronous wrapper for the async scout report generation.

    Args:
        player_query: Player name and disambiguating context

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """
    return asyncio.run(generate_scout_report_parallel_async(player_query))
