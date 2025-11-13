"""
Parallel Scout Report Agent - V5 with ADK LLM Router + Parallel
Architecture:
1. LlmAgent coordinator with conditional routing
2. Baseline research agent (output_key="baseline_info")
3. ParallelAgent with 5 research agents (each with output_key)
4. Formatter agent (output_schema=ScoutReport) - produces final structured JSON

The coordinator can decide to:
- Ask for clarification if player identification is ambiguous
- Proceed with full research pipeline if player is clearly identified

This properly uses ADK's workflow agents and grounding metadata with citations.
"""

import os
import asyncio
import json
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from dotenv import load_dotenv
from google.adk.agents import Agent, SequentialAgent, ParallelAgent, LlmAgent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search, AgentTool
from google.genai import types
from .scout_report_schema import ScoutReport

# Load environment
load_dotenv()

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def strip_utm_params(url: str) -> str:
    """Remove UTM tracking parameters from URLs."""
    if not url:
        return url

    parsed = urlparse(url)
    if parsed.query:
        # Parse query string and filter out UTM parameters
        params = parse_qs(parsed.query, keep_blank_values=True)
        filtered_params = {k: v for k, v in params.items()
                          if not k.lower().startswith('utm_')}

        # Reconstruct URL without UTM params
        new_query = urlencode(filtered_params, doseq=True) if filtered_params else ''
        return urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path,
            parsed.params,
            new_query,
            parsed.fragment
        ))
    return url

def resolve_redirect_url(url: str, timeout: int = 3) -> str:
    """Resolve redirect URLs to their final destination."""
    if not url:
        return url

    # Check if it's a Vertex AI redirect URL
    if 'vertexaisearch.cloud.google.com/grounding-api-redirect' in url:
        try:
            import requests
            resp = requests.head(url, allow_redirects=True, timeout=timeout)
            return resp.url if resp.url != url else url
        except Exception:
            return url
    return url

def extract_source_name(url: str, title: str = None) -> str:
    """Extract a clean source name from URL or title."""
    if title:
        return title

    # Extract domain name as fallback
    parsed = urlparse(url)
    domain = parsed.netloc.replace('www.', '')

    # Common sports sites - return clean names
    domain_map = {
        '247sports.com': '247Sports',
        'on3.com': 'On3',
        'rivals.com': 'Rivals',
        'espn.com': 'ESPN',
        'maxpreps.com': 'MaxPreps',
        'hudl.com': 'Hudl',
        'si.com': 'Sports Illustrated',
        'athletic.com': 'The Athletic',
        'usatodayhss.com': 'USA Today',
    }

    return domain_map.get(domain, domain)

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
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

# =============================================================================
# 2. SECTION-SPECIFIC RESEARCH AGENTS (run in parallel)
# =============================================================================

physical_agent = Agent(
    name="physical_researcher",
    model="gemini-2.5-flash",
    description="Researches player physical profile and measurables",
    instruction="""
Research the player's PHYSICAL & ATHLETIC PROFILE using google_search.

**IMPORTANT: Use the {baseline_info} from session state to identify the specific player you're researching.**
The baseline info contains the player's name, position, school, and grad year - use this to target your searches.

**SOURCE GUIDANCE:**
- Look for combine/camp results (UCReport, Rivals Camp Series) for verified numbers
- For track stats, search athletic.net or state athletic association results
- Search sport-specific camp/combine events

**REQUIRED INFORMATION:**

1. **Verified Measurements:**
   - List ALL publicly available verified measurements (height, weight, wingspan, hand size)
   - If multiple measurements found from different sources, list EACH with its source/date
   - Example: "Rivals Camp, Mar 2025: 6'2\", 195lbs"
   - Prioritize verified measurements over basic profile stats

2. **Athletic Testing:**
   - Search for reported weight room numbers (bench press, squat, power clean, etc.)
   - Search for track & field stats (40-yard dash, 100m/200m, shuttle, vertical jump, broad jump, shot put, etc.)
   - If multiple results found, list EACH with its source/date

3. **Physical Development:**
   - Note any information about physical growth or changes year to year
   - Document weight/height changes between recruiting services updates

4. **Camp Circuit:**
   - Search for performances at elite camps (Elite 11 Finals, The Opening Finals, Under Armour All-American, Army All-American, Rivals Camp Series, etc.)
   - Include: camp name, date, performance highlights, rankings/awards won
   - Look for position-specific drills and rankings

5. **Multi-Sport Athlete:**
   - Note if player competed in other sports (basketball, track, baseball, etc.)
   - Include: sport, level (varsity/JV), years played, achievements
   - Note whether they stopped to focus on primary sport

Focus ONLY on physical attributes and testing data.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="physical_research",
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

performance_agent = Agent(
    name="performance_researcher",
    model="gemini-2.5-flash",
    description="Researches player on-field performance and statistics",
    instruction="""
Research the player's ON-FIELD PERFORMANCE & CONTEXT using google_search.

**IMPORTANT: Use the {baseline_info} from session state to identify the specific player you're researching.**
The baseline info contains the player's name, position, school, and grad year - use this to target your searches.

**SOURCE GUIDANCE:**
- Use MaxPreps for stats and team records
- Use local news sports sections for team strength, classification, and transfer reports
- For high school stats, prioritize: (1) high school's official athletic site, (2) state-level sport governing body sites, (3) MaxPreps/On3 as fallback
- CHECK FOR TRANSFERS: Search to see if player transferred and played varsity at other high schools

**REQUIRED INFORMATION:**

1. **Production & Statistics:**
   - Provide YEAR-BY-YEAR (Sophomore, Junior, Senior) breakdown of all available varsity stats
   - Note any standout single-game performances
   - If player transferred, specify which stats correspond to which high school

2. **Key Games/Standout Performances:**
   - Search for performances vs ranked opponents, championship games, career-high games
   - Include: opponent name/ranking, full stat line, game result/score, context

3. **Accomplishments:**
   - List individual awards, all-region/all-state honors, team leadership roles for EACH year
   - Include conference/district awards (POY, All-Conference teams)

4. **Team Success:**
   - Detail team accomplishments including TEAM RECORDS for each year player was on varsity (at each school if transferred)
   - Playoff appearances and championships

5. **Level of Competition:**
   - For each school attended, describe competition faced (state classification/division, strength of region)
   - Note notable opponents or highly-recruited teammates

6. **Team Context:**
   - Conference Strength: Total D1 signees from conference schools, nationally ranked teams in conference
   - School Recruiting History: Historical D1 pipeline - signee counts for last 3-5 years with P5 vs G5 breakdown
   - Teammate Recruits: Other D1 prospects on roster with positions, ratings, offer counts
   - Opponent Quality: Record vs ranked opponents, record vs teams with 5+ D1 recruits
   - Strength of Schedule: Number of nationally ranked opponents faced, combined opponent record, playoff teams faced

Focus ONLY on on-field performance and statistics.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="performance_research",
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

recruiting_agent = Agent(
    name="recruiting_researcher",
    model="gemini-2.5-flash",
    description="Researches player recruiting profile and rankings",
    instruction="""
Research the player's RECRUITING PROFILE using google_search.

**IMPORTANT: Use the {baseline_info} from session state to identify the specific player you're researching.**
The baseline info contains the player's name, position, school, and grad year - use this to target your searches.

**SOURCE GUIDANCE:**
- Search 247Sports, On3, ESPN, and Rivals directly
- Cross-reference player's X/Twitter feed (if found) for self-reported offers, commitments, or visit news
- Use sport-specific recruiting sites (e.g., PrepHoops for basketball, Perfect Game for baseball)

**REQUIRED INFORMATION:**

1. **Star Rating & Rankings:**
   - Provide current star ratings and national, position, and state rankings from ALL FOUR major services (247Sports, On3, ESPN, Rivals)
   - Include 247Sports Composite score
   - Note any ranking changes over time

2. **Scholarship Offers:**
   - List ALL known college scholarship offers (from services and self-reported on social media)
   - Break down by tier: Elite/CFP contenders, Power 5, Group of 5, FCS
   - Note offer dates if available

3. **Latest Offer:**
   - Identify the school that made the most recent offer and the date, if available

4. **Visits:**
   - Detail any official visits (NCAA-limited to 5) and unofficial visits with dates
   - Include scheduled future visits

5. **School Interest:**
   - Note top contending schools
   - Look for 247Sports Crystal Ball predictions and On3 RPM scores
   - Note pursuit level (leader, heavy pursuit, etc.)

6. **NIL Valuation:**
   - Search for On3 NIL valuation
   - Any known NIL deals or brand partnerships

7. **Enrollment Plans:**
   - Note if player plans early enrollment (January), summer enrollment, or fall enrollment

8. **Family Connections:**
   - Search for parents/siblings who played college or have coaching connections to programs

Focus ONLY on recruiting rankings and recruitment process.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="recruiting_research",
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

background_agent = Agent(
    name="background_researcher",
    model="gemini-2.5-flash",
    description="Researches player background and personal story",
    instruction="""
Research the player's BACKGROUND, IDENTITY, AND STORY using google_search.

**IMPORTANT: Use the {baseline_info} from session state to identify the specific player you're researching.**
The baseline info contains the player's name, position, school, and grad year - use this to target your searches.

**SOURCE GUIDANCE:**
- Use primary recruiting profiles (247Sports, On3) and team rosters (MaxPreps) to confirm identity
- Search local news for "scholar-athlete" awards, school honor rolls
- Use Niche/GreatSchools for high school academic reputation
- VALIDATE the player's current or final high school (some sources like Hudl may list training academies)

**REQUIRED INFORMATION:**

1. **Player Identity & Basic Info:**
   - Full Name, Current/Final High School (City, State), Team Name, Position(s), Graduation Class
   - List any previous high schools attended while playing varsity (if any are found)
   - X/Twitter handle (if found, format as @username), Instagram handle

2. **Family Background:**
   - Family background and support system
   - Parents/siblings who played college or pro sports
   - Family connections to coaching or programs

3. **High School Program:**
   - High school/program and coaching information
   - School's athletic reputation and facilities
   - Notable alumni from the program

4. **Personal Story:**
   - Personal story, challenges overcome, motivations
   - Community involvement and character
   - Human-interest stories from local news

5. **Academic Profile:**
   - Individual Standing: Search for publicly available GPA, academic awards (Honor Roll, Scholar-Athlete), mentions of AP/honors courses
   - School Academic Context: Briefly assess academic reputation of their high school(s) (e.g., "highly-rated public school," "well-regarded private prep school")

6. **Media Coverage:**
   - Key insights from local news or beat writer articles
   - Feature stories or interviews

Focus ONLY on background, personal story, and character.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="background_research",
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

intangibles_agent = Agent(
    name="intangibles_researcher",
    model="gemini-2.5-flash",
    description="Researches player intangibles and leadership",
    instruction="""
Research the player's INTANGIBLES, LEADERSHIP, AND PROJECTION using google_search.

**IMPORTANT: Use the {baseline_info} from session state to identify the specific player you're researching.**
The baseline info contains the player's name, position, school, and grad year - use this to target your searches.

**SOURCE GUIDANCE:**
- Search local news outlets for human-interest stories, player interviews, or scholar-athlete awards
- Player's X/Twitter feed is a primary source for character assessment
- Look for recruiting analyst quotes and scouting reports from 247Sports, On3, ESPN, Rivals analysts

**REQUIRED INFORMATION:**

1. **Character & Leadership:**
   - Synthesize information from news articles or interviews about player's character, work ethic, or leadership qualities
   - Note team captain roles, leadership positions
   - Coach and teammate quotes about intangibles

2. **X/Twitter Review (If Handle Found):**
   - CRUCIAL: Review the player's public X/Twitter feed
   - Recruiting: Identify any self-reported offers, commitments, or de-commitments not found on main sites (cite specific tweet/date if possible)
   - Character: Objectively note any publicly visible posts related to off-field concerns, problematic/hateful language, or extreme negativity, as well as positive examples of leadership or character

3. **Mental & Competitive Traits:**
   - Mental toughness and competitiveness
   - Football IQ and learning ability
   - Work ethic and coachability
   - Off-field reputation

4. **Scout Projection:**
   - Search for analyst projections on college readiness (Day 1 starter vs redshirt)
   - Development timeline
   - Ceiling/floor analysis
   - Potential NFL draft projection (if mentioned)

5. **Player Comparisons:**
   - Look for pro/college player comparisons from recruiting analysts (247Sports, On3, ESPN, Rivals)
   - Search for phrases like "reminds of", "similar to", "plays like"
   - Include why the comparison fits

Focus ONLY on intangibles, leadership, and character traits.
The grounding system will automatically attribute your findings to sources.
""",
    tools=[google_search],
    output_key="intangibles_research",
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
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

**IMPORTANT: Citations**
When synthesizing content from the research, manually add citation placeholders using [^N] format.
Start with [^0] for the first unique source, [^1] for the second, etc.
Use these when stating facts from the research. Example:
"Johnson is a fierce, physical blocker [^0] who plays with a relentless motor [^1]."

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
6. **stats**: List 3-6 key performance statistics with season/year
   Format: "3,245 Passing Yards (2024/25)", "42 TD, 4 INT (2024/25)"
7. **citations**: Leave empty - will be populated from grounding metadata

**Critical Instructions:**
- Be comprehensive - synthesize ALL research provided
- Use markdown formatting for analysis content
- Ensure stats are specific with seasons
- Make tags useful for searching/filtering
- Focus on facts from the research, not speculation

Output ONLY valid JSON matching the ScoutReport schema.
""",
    tools=[],  # No tools - just formats existing research
    # NOTE: Removed output_schema to allow grounding citations to be injected
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

# =============================================================================
# 5. LLM COORDINATOR WITH CONDITIONAL ROUTING
# =============================================================================

# Wrap agents as tools for the coordinator
baseline_tool = AgentTool(baseline_agent)
research_tool = AgentTool(parallel_research_agent)
formatter_tool = AgentTool(formatter_agent)

scout_report_coordinator = LlmAgent(
    name="scout_report_coordinator",
    model="gemini-2.5-flash",
    description="Coordinates the scout report generation process with conditional routing",
    instruction="""
You are the coordinator for a football recruiting scout report generation system.

**Your Process:**

1. **ALWAYS START** by calling `baseline_researcher` to gather basic player identification info.

2. **Evaluate the baseline research results:**
   - If the player identification is CLEAR and UNAMBIGUOUS (you have ONE specific player with name, position, school, grad year), proceed to step 3.
   - If the player identification is AMBIGUOUS, UNCLEAR, or you found NO clear match:
     * **STOP IMMEDIATELY**
     * **DO NOT call any more tools**
     * Ask the user for clarification with specific questions like:
       - "I found multiple players named [name]. Did you mean [Player A from School X] or [Player B from School Y]?"
       - "Could you specify the graduation year and/or school for [name]?"
       - "I couldn't find a player matching [query]. Could you provide more details?"

3. **ONLY if player identification is 100% clear and unambiguous**, call `parallel_research_coordinator` to gather detailed research.

4. **After research completes**, call `scout_report_formatter` to structure all the research into final JSON.

5. **Return the final scout report** to the user.

**CRITICAL:**
- If you need clarification, STOP and ask the user - DO NOT call research or formatter tools
- Only proceed through all steps if you have clear, unambiguous player identification
- When asking for clarification, respond ONLY with plain text questions - DO NOT format as JSON or code blocks

Begin by calling the baseline_researcher with the user's player query.
""",
    tools=[baseline_tool, research_tool, formatter_tool],
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)

# =============================================================================
# EXECUTION FUNCTION
# =============================================================================

async def generate_scout_report_parallel_async(player_query: str) -> dict:
    """
    Generate a scout report using two-phase execution to preserve grounding metadata.

    Phase 1: Run baseline agent to identify player
    Phase 2: If clear, run parallel research + formatter

    This approach preserves grounding metadata by running agents directly instead of through AgentTool.

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

    grounding_sources = []  # Collect from all phases

    # =========================================================================
    # PHASE 1: Run baseline agent to identify player
    # =========================================================================
    print("Phase 1: Running baseline research...")
    baseline_runner = Runner(
        agent=baseline_agent,
        app_name="scout_report_pipeline",  # Must match session app_name
        session_service=session_service
    )

    user_content = types.Content(
        role='user',
        parts=[types.Part(text=player_query)]
    )

    baseline_stream = baseline_runner.run_async(
        user_id="scout_user",
        session_id=session.id,
        new_message=user_content
    )

    baseline_text = None
    async for event in baseline_stream:
        # Collect grounding from baseline
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

                        # Strip UTM params from URL
                        uri = strip_utm_params(uri)

                        # Extract source name from title or URL
                        source_name = extract_source_name(uri, title)

                        grounding_sources.append((uri, source_name))

        # Capture baseline response text
        if hasattr(event, 'content') and event.content:
            if hasattr(event.content, 'parts'):
                for part in event.content.parts:
                    if hasattr(part, 'text') and part.text:
                        baseline_text = part.text.strip()

    print(f"✓ Baseline research complete")

    # Check if baseline indicates ambiguity or inability to identify player
    if not baseline_text or len(baseline_text) < 50:
        return {"text": "Unable to identify player - baseline research returned no results"}

    ambiguity_indicators = [
        "multiple players",
        "could not find",
        "unclear which",
        "need more information",
        "can you clarify",
        "which player",
        "more details needed"
    ]
    is_ambiguous = any(indicator in baseline_text.lower() for indicator in ambiguity_indicators)

    if is_ambiguous:
        print("✓ Player identification is ambiguous - requesting clarification")
        return {"text": baseline_text}

    # =========================================================================
    # PHASE 2: Player is clear - run parallel research + formatter
    # =========================================================================
    print("\nPhase 2: Running parallel research...")

    # Create a pipeline with just parallel research and formatter
    research_pipeline = SequentialAgent(
        name="research_and_format",
        sub_agents=[parallel_research_agent, formatter_agent]
    )

    pipeline_runner = Runner(
        agent=research_pipeline,
        app_name="scout_report_pipeline",  # Must match session app_name
        session_service=session_service
    )

    # Continue with same session so formatter can access {baseline_info}
    pipeline_stream = pipeline_runner.run_async(
        user_id="scout_user",
        session_id=session.id,
        new_message=types.Content(
            role='user',
            parts=[types.Part(text="Generate the full scout report based on baseline research.")]
        )
    )

    # Debug: Check what's in session state
    print(f"DEBUG: Checking session state after research...")
    try:
        state = await session_service.get_state(session.id, "scout_user")
        if state and 'physical_research' in state:
            sample = state['physical_research'][:500] if len(state['physical_research']) > 500 else state['physical_research']
            print(f"DEBUG: Sample of physical_research from state: {sample}...")
            import re
            citations_in_research = re.findall(r'\[\^\d+\]', state['physical_research'])
            print(f"DEBUG: Citations found in physical_research: {len(citations_in_research)}")
    except Exception as e:
        print(f"DEBUG: Could not check session state: {e}")

    final_response = None
    async for event in pipeline_stream:
        # Collect grounding from parallel research agents
        if hasattr(event, 'grounding_metadata') and event.grounding_metadata:
            gm = event.grounding_metadata
            if hasattr(gm, 'grounding_chunks') and gm.grounding_chunks:
                for chunk in gm.grounding_chunks:
                    if hasattr(chunk, 'web') and chunk.web:
                        uri = chunk.web.uri
                        title = chunk.web.title if hasattr(chunk.web, 'title') else None

                        # Resolve redirects
                        if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                            try:
                                import requests
                                resp = requests.head(uri, allow_redirects=True, timeout=3)
                                if resp.url != uri:
                                    uri = resp.url
                            except Exception:
                                pass

                        uri = strip_utm_params(uri)
                        source_name = extract_source_name(uri, title)
                        grounding_sources.append((uri, source_name))

        # Capture final formatter response
        if hasattr(event, 'content') and event.content:
            final_response = event.content

    print(f"✓ Parallel research complete - collected {len(grounding_sources)} total grounding sources")

    # Parse formatter output
    scout_report = None
    if final_response and hasattr(final_response, 'parts'):
        for part in final_response.parts:
            if hasattr(part, 'text') and part.text:
                text = part.text.strip()

                # Debug: Check raw formatter output for citations
                import re
                raw_citations = re.findall(r'\[\^\d+\]', text)
                if raw_citations:
                    print(f"DEBUG: Raw formatter text contains {len(raw_citations)} citations")
                    print(f"DEBUG: First 200 chars of raw text: {text[:200]}...")

                # Strip markdown code blocks
                if text.startswith('```'):
                    lines = text.split('\n')
                    if lines[0].startswith('```'):
                        lines = lines[1:]
                    if lines and lines[-1].strip() == '```':
                        lines = lines[:-1]
                    text = '\n'.join(lines).strip()

                try:
                    scout_report = json.loads(text)
                    print("✓ Successfully parsed structured scout report")
                    # Debug: Check if there are any [^N] citations in the raw text
                    import re
                    citations_found = re.findall(r'\[\^\d+\]', text)
                    print(f"DEBUG: Found {len(citations_found)} citation markers in formatter output: {citations_found[:5] if citations_found else 'None'}")
                except json.JSONDecodeError:
                    return {"text": "Unable to parse scout report from formatter"}

    if not scout_report:
        return {"text": "Unable to complete scout report - no response from formatter"}

    # Process citations
    if scout_report:
        # Convert [^0] [^1] style citations to inline markdown format: ([Source Name](url))
        import re

        def replace_citation(match):
            """Replace [^N] or [^N, ^M, ...] with inline citations"""
            citation_text = match.group(0)
            # Extract all numbers from the citation
            numbers = re.findall(r'\d+', citation_text)

            citations = []
            for num_str in numbers:
                index = int(num_str)
                if index < len(grounding_sources):
                    url, source_name = grounding_sources[index]
                    citations.append(f"([{source_name}]({url}))")

            return ' '.join(citations) if citations else match.group(0)

        # Process analysis items to replace citations
        if 'analysis' in scout_report:
            for item in scout_report['analysis']:
                if 'content' in item:
                    # Replace [^N] or [^N, ^M, ...] patterns with inline markdown citations
                    item['content'] = re.sub(r'\[\^[\d,\s\^]+\]', replace_citation, item['content'])

        # Process stats to replace citations
        if 'stats' in scout_report:
            scout_report['stats'] = [
                re.sub(r'\[\^[\d,\s\^]+\]', replace_citation, stat)
                for stat in scout_report['stats']
            ]

        # Add unique URLs to citations array
        unique_urls = list(dict.fromkeys([url for url, _ in grounding_sources]))
        if unique_urls:
            scout_report.setdefault('citations', []).extend(unique_urls)
            # Deduplicate final list
            scout_report['citations'] = list(dict.fromkeys(scout_report['citations']))
            print(f"✓ Converted {len(grounding_sources)} citations to inline markdown format")
            print(f"✓ Added {len(unique_urls)} unique citation URLs to citations array")

        return scout_report

    # Fallback if neither case worked
    return {
        "text": "Unable to complete scout report - no response received"
    }


def generate_scout_report_parallel(player_query: str) -> dict:
    """
    Synchronous wrapper for the async scout report generation.

    Args:
        player_query: Player name and disambiguating context

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """
    return asyncio.run(generate_scout_report_parallel_async(player_query))
