"""
Parallel Scout Report - Version 2
Uses asyncio directly instead of ADK ParallelAgent for better control
"""

import os
import asyncio
from google import genai
from google.genai import types
from .formatting_agent import format_to_schema


# Same prompts as v1 but adapted for direct genai calls
ROOT_PROMPT = """
You are a sports research coordinator. Your job is to quickly identify the player and store baseline info.

**CRITICAL: KEEP THIS FAST - 1-2 searches maximum!**

TASK:
1. Use grounded search to quickly find the player's basic information ONLY:
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


async def research_baseline(player_query: str, client: genai.Client) -> tuple[str, list[str]]:
    """Quick baseline player identification"""
    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=f"{ROOT_PROMPT}\n\n**PLAYER TO RESEARCH:** {player_query}",
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    text = response.text.strip()
    sources = extract_sources(response)
    return text, sources


async def research_physical(baseline_info: str, client: genai.Client) -> tuple[str, list[str]]:
    """Research physical profile"""
    prompt = f"""
You are researching the PHYSICAL PROFILE for a football player.

Context: {baseline_info}

Research and document:
- Height, weight, measurables (arm length, hand size, wingspan if available)
- Athletic testing (40-yard dash, shuttle, broad jump, vertical, etc.)
- Physical attributes (build, frame, body type)
- Growth/development notes

Use grounded search. Include [1][2] style citations.
Keep notes concise but comprehensive. Focus ONLY on physical attributes.
"""

    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text.strip(), extract_sources(response)


async def research_performance(baseline_info: str, client: genai.Client) -> tuple[str, list[str]]:
    """Research on-field performance"""
    prompt = f"""
You are researching ON-FIELD PERFORMANCE for a football player.

Context: {baseline_info}

Research and document:
- Latest season statistics (passing/rushing/receiving yards, TDs, completion %, etc.)
- Previous season stats if relevant
- Game highlights and notable performances
- Film evaluation notes (mechanics, technique, football IQ)
- Performance trends

Use grounded search. Include [1][2] style citations.
Keep notes concise but comprehensive. Focus ONLY on performance and stats.
"""

    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text.strip(), extract_sources(response)


async def research_recruiting(baseline_info: str, client: genai.Client) -> tuple[str, list[str]]:
    """Research recruiting profile"""
    prompt = f"""
You are researching the RECRUITING PROFILE for a football player.

Context: {baseline_info}

Research and document:
- Star rating (247Sports, ESPN, On3, Rivals)
- National/state/position rankings
- Scholarship offers received
- Recruitment timeline and commitment status
- Official/unofficial visits
- Recruiting analysts' evaluations

Use grounded search. Include [1][2] style citations.
Keep notes concise but comprehensive. Focus ONLY on recruiting information.
"""

    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text.strip(), extract_sources(response)


async def research_background(baseline_info: str, client: genai.Client) -> tuple[str, list[str]]:
    """Research background and context"""
    prompt = f"""
You are researching BACKGROUND AND CONTEXT for a football player.

Context: {baseline_info}

Research and document:
- High school program details and success
- Family background (parents, siblings who played sports)
- Academic information (GPA, academic honors if public)
- Multi-sport athlete status
- Early career development (youth leagues, camps)
- Geographic context (state football culture, competition level)

Use grounded search. Include [1][2] style citations.
Keep notes concise but comprehensive. Focus ONLY on background context.
"""

    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text.strip(), extract_sources(response)


async def research_intangibles(baseline_info: str, client: genai.Client) -> tuple[str, list[str]]:
    """Research intangibles and character"""
    prompt = f"""
You are researching INTANGIBLES AND CHARACTER for a football player.

Context: {baseline_info}

Research and document:
- Leadership qualities (team captain, vocal leader, etc.)
- Work ethic and dedication
- Coachability and attitude
- Character assessments from coaches/teammates
- Community involvement or off-field activities
- Mental makeup and competitiveness
- Any character concerns or red flags

Use grounded search. Include [1][2] style citations.
Keep notes concise but comprehensive. Focus ONLY on intangibles and character.
"""

    response = await client.aio.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text.strip(), extract_sources(response)


def extract_sources(response) -> list[str]:
    """Extract sources from grounding metadata"""
    import requests

    sources = []
    if hasattr(response, 'candidates') and response.candidates:
        candidate = response.candidates[0]
        if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
            for chunk in candidate.grounding_metadata.grounding_chunks:
                if hasattr(chunk, 'web') and chunk.web:
                    uri = chunk.web.uri
                    # Resolve grounding API redirect URLs
                    if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                        try:
                            resp = requests.head(uri, allow_redirects=True, timeout=3)
                            actual_url = resp.url
                            if actual_url != uri:
                                uri = actual_url
                        except Exception:
                            pass
                    sources.append(uri)
    return sources


def generate_scout_report_parallel(player_query: str) -> dict:
    """
    Generate scout report using parallel research.

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """

    async def run():
        # Create client
        client = genai.Client(
            vertexai=True,
            project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
            location=os.environ.get('GOOGLE_CLOUD_LOCATION')
        )

        # Step 1: Quick baseline research (serial - needed for context)
        print("Step 1: Baseline research...")
        baseline_info, baseline_sources = await research_baseline(player_query, client)

        # Check for AMBIGUOUS or NOT FOUND
        if baseline_info.startswith("AMBIGUOUS:") or baseline_info.startswith("NOT FOUND:"):
            return {"text": baseline_info}

        print(f"Baseline: {baseline_info[:100]}...")

        # Step 2: Parallel section research
        print("Step 2: Parallel section research...")
        results = await asyncio.gather(
            research_physical(baseline_info, client),
            research_performance(baseline_info, client),
            research_recruiting(baseline_info, client),
            research_background(baseline_info, client),
            research_intangibles(baseline_info, client),
        )

        physical_notes, physical_sources = results[0]
        performance_notes, performance_sources = results[1]
        recruiting_notes, recruiting_sources = results[2]
        background_notes, background_sources = results[3]
        intangibles_notes, intangibles_sources = results[4]

        print("Step 3: Combining results...")

        # Combine all notes
        combined_notes = f"""## Player Identity
{baseline_info}

## Physical Profile
{physical_notes}

## On-Field Performance
{performance_notes}

## Recruiting Profile
{recruiting_notes}

## Background & Context
{background_notes}

## Intangibles & Character
{intangibles_notes}
"""

        # Combine all sources (deduplicate)
        all_sources = list(dict.fromkeys(
            baseline_sources + physical_sources + performance_sources +
            recruiting_sources + background_sources + intangibles_sources
        ))

        print(f"Step 4: Formatting to schema ({len(all_sources)} sources)...")

        # Format to structured schema
        scout_report = format_to_schema(
            research_notes=combined_notes,
            sources=all_sources
        )

        return scout_report.model_dump()

    return asyncio.run(run())
