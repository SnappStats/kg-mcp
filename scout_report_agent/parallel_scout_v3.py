"""
Parallel Scout Report - Version 3
Uses ThreadPoolExecutor for parallel execution with sync genai client
"""

import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from google import genai
from google.genai import types
from .formatting_agent import format_to_schema
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def create_client():
    """Create a genai client"""
    return genai.Client(
        vertexai=True,
        project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        location=os.environ.get('GOOGLE_CLOUD_LOCATION')
    )


def extract_sources(response) -> list[str]:
    """Extract sources from grounding metadata"""
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


def research_baseline(player_query: str) -> tuple[str, list[str]]:
    """Quick baseline player identification"""
    client = create_client()

    prompt = f"""
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

**PLAYER TO RESEARCH:** {player_query}
"""

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return response.text.strip(), extract_sources(response)


def research_physical(baseline_info: str) -> tuple[str, str, list[str]]:
    """Research physical profile"""
    client = create_client()

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

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return "physical", response.text.strip(), extract_sources(response)


def research_performance(baseline_info: str) -> tuple[str, str, list[str]]:
    """Research on-field performance"""
    client = create_client()

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

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return "performance", response.text.strip(), extract_sources(response)


def research_recruiting(baseline_info: str) -> tuple[str, str, list[str]]:
    """Research recruiting profile"""
    client = create_client()

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

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return "recruiting", response.text.strip(), extract_sources(response)


def research_background(baseline_info: str) -> tuple[str, str, list[str]]:
    """Research background and context"""
    client = create_client()

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

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return "background", response.text.strip(), extract_sources(response)


def research_intangibles(baseline_info: str) -> tuple[str, str, list[str]]:
    """Research intangibles and character"""
    client = create_client()

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

    response = client.models.generate_content(
        model='gemini-2.5-flash',
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.1,
            tools=[types.Tool(google_search=types.GoogleSearch())]
        )
    )

    return "intangibles", response.text.strip(), extract_sources(response)


def generate_scout_report_parallel(player_query: str) -> dict:
    """
    Generate scout report using parallel research with ThreadPoolExecutor.

    Returns:
        dict: Scout report with 'player' key or {'text': error_message}
    """
    import time

    start_time = time.time()

    # Step 1: Quick baseline research (serial - needed for context)
    print("Step 1: Baseline research...")
    baseline_info, baseline_sources = research_baseline(player_query)

    # Check for AMBIGUOUS or NOT FOUND
    if baseline_info.startswith("AMBIGUOUS:") or baseline_info.startswith("NOT FOUND:"):
        return {"text": baseline_info}

    print(f"  ✓ Baseline complete ({time.time() - start_time:.1f}s): {baseline_info[:80]}...")

    # Step 2: Parallel section research
    print("Step 2: Parallel section research (5 concurrent agents)...")
    parallel_start = time.time()

    research_functions = [
        research_physical,
        research_performance,
        research_recruiting,
        research_background,
        research_intangibles,
    ]

    results = {}
    all_sources = list(baseline_sources)

    # Execute in parallel
    with ThreadPoolExecutor(max_workers=5) as executor:
        # Submit all tasks
        futures = {
            executor.submit(func, baseline_info): func.__name__
            for func in research_functions
        }

        # Collect results as they complete
        for future in as_completed(futures):
            func_name = futures[future]
            try:
                section_name, notes, sources = future.result()
                results[section_name] = notes
                all_sources.extend(sources)
                print(f"  ✓ {section_name} complete")
            except Exception as e:
                print(f"  ✗ {func_name} failed: {e}")
                results[func_name] = f"[Research failed: {e}]"

    print(f"  ✓ All parallel research complete ({time.time() - parallel_start:.1f}s)")

    # Step 3: Combine all notes
    print("Step 3: Combining results...")
    combined_notes = f"""## Player Identity
{baseline_info}

## Physical Profile
{results.get('physical', '[No data]')}

## On-Field Performance
{results.get('performance', '[No data]')}

## Recruiting Profile
{results.get('recruiting', '[No data]')}

## Background & Context
{results.get('background', '[No data]')}

## Intangibles & Character
{results.get('intangibles', '[No data]')}
"""

    # Deduplicate sources
    unique_sources = list(dict.fromkeys(all_sources))

    print(f"Step 4: Formatting to schema ({len(unique_sources)} sources)...")
    format_start = time.time()

    # Format to structured schema
    scout_report = format_to_schema(
        research_notes=combined_notes,
        sources=unique_sources
    )

    print(f"  ✓ Formatting complete ({time.time() - format_start:.1f}s)")
    print(f"\nTOTAL TIME: {time.time() - start_time:.1f}s")

    return scout_report.model_dump()
