"""
Fast Scout Report Service - Direct Gemini API call with KG context and grounding
"""
import os
import json
import requests
from typing import Dict, Any
from scout_report_agent.scout_report_schema import ScoutReport, Source
from scout_report_agent.gemini_rest_service import get_gemini_rest_service


def search_knowledge_graph(user_id: str, player_name: str) -> dict:
    """Search the knowledge graph for existing player information."""
    url = os.environ['KG_URL'] + '/search'
    response = requests.get(url, params={'graph_id': user_id, 'query': player_name})
    return response.json()


def extract_sources_from_grounding(response: Dict[str, Any]) -> list[Source]:
    """Extract citation sources from grounding metadata."""
    try:
        sources = []
        candidates = response.get('candidates', [])
        if not candidates:
            return sources

        grounding_metadata = candidates[0].get('groundingMetadata', {})
        chunks = grounding_metadata.get('groundingChunks', [])

        for idx, chunk in enumerate(chunks):
            web = chunk.get('web', {})
            title = web.get('title', 'Unknown Source')
            uri = web.get('uri', 'No URL')

            # Try to resolve redirects
            if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                try:
                    response = requests.head(uri, allow_redirects=True, timeout=3)
                    actual_url = response.url
                    if actual_url != uri:
                        uri = actual_url
                except Exception:
                    pass

            # Clean title
            clean_title = title[:100]
            if '.' in clean_title and len(clean_title.split()) == 1:
                clean_title = clean_title.lower().replace('www.', '')
            elif ' - ' in clean_title:
                parts = clean_title.split(' - ')
                clean_title = parts[-1].strip()
            elif ' | ' in clean_title:
                parts = clean_title.split(' | ')
                clean_title = parts[-1].strip()

            sources.append(Source(
                number=idx + 1,
                title=clean_title,
                url=uri
            ))

        return sources
    except Exception:
        return []


def generate_scout_report(user_id: str, player_name: str) -> ScoutReport:
    """
    Generate a comprehensive scout report using KG context + web search grounding.

    Args:
        user_id: User ID for KG lookup
        player_name: Name of the player

    Returns:
        ScoutReport object with all fields populated and citations
    """
    # 1. Get KG data
    kg_data = search_knowledge_graph(user_id, player_name)

    # 2. Build comprehensive prompt with KG context
    prompt = f"""
Generate a comprehensive scout report for {player_name}.

**Existing Knowledge Graph Data:**
{json.dumps(kg_data, indent=2)}

Use the knowledge graph data as a baseline reference, but perform web searches to validate, update, and fill in missing information.

**CRITICAL INSTRUCTIONS:**
* Use web search to find current information from credible sources
* **ALL data points MUST have sources** - if KG data lacks sources, validate via web search and cite the web source
* **VALIDATE** the player's current/final high school - some sources list training academies
* **CHECK FOR TRANSFERS** - search if the player changed high schools during varsity career
* Prioritize reputable sources (247Sports, On3, ESPN, Rivals, MaxPreps, official school sites, etc.)
* Include citation numbers [1], [2], etc. for ALL facts throughout the report

**DATA TO COLLECT (must match schema exactly):**

**QUICK ACCESS FIELDS (most recent from credible sources):**
- player_name: Full name
- position: Position(s) played (e.g., "QB", "WR")
- height: Most recent height from credible source (consider: major recruiting services like 247Sports/On3/ESPN/Rivals, official school athletics sites, verified combine/camp measurements). Use your judgment on source credibility. Format: "6'4\""
- weight: Most recent weight from credible source using same credibility criteria. Format: "219 lbs"
- school_name: Current/final high school in format "School Name (City, State)"
- location: City, State
- graduation_class: High school graduation year (e.g., "2025")
- gpa: Most recent GPA from credible source if available - FORMAT: just the number like "3.8" (or null if unavailable). Do NOT include school or other context here - that goes in intangibles.academic_profile
- twitter_handle: @username format (or null if not found)
- previous_schools: Previous high schools with years if transferred. FORMAT: "St. John's HS (2020-2021) | Transfer to IMG Academy (2022)". Empty string "" if no transfers

**executive_summary:** Brief summary of player profile, strengths, and potential

**physical_profile (historical tracking with ALL sources):**
- measurements: ALL height/weight measurements from ALL sources with dates. Example: "Height: 6'4\\" (Texas Athletics, 2025), 6'3.5\\" (On3, 2022), 6'3\\" (HS, 2021). Weight: 219 lbs (Texas, 2025), 215 lbs (247Sports, 2022)"
- athletic_testing: Weight room stats, track times, combine results, camp measurements with sources
- physical_development: Physical growth and development notes year-to-year

**recruiting_profile:**
- star_ratings: Star ratings from all services with rankings, formatted as single string. Example: "247Sports: 5-star, No. 1 QB | On3: 5-star | ESPN: 4-star, No. 2 QB"
- scholarship_offers: All known college offers as comma-separated string. Example: "Texas, Georgia, Alabama, LSU, Ohio State"
- latest_offer: Most recent offer with school and date if available
- visits: Official and unofficial visits with dates
- school_interest: Schools/programs showing reported interest
- self_reported_offers: Offers and commitments reported via player's social media

**team_profile:**
- high_school_team: Team name (or null)
- coach: Coach name (or null)
- conference: Conference/league (or null)
- recruitment_breakdown: Information about teammates recruited (division, star ratings, player names) (or null)

**statistics:**
- season_stats: Year-by-year breakdown with stats and citations. Example: "2022 Junior: 2,500 yards, 25 TDs [10] | 2023 Senior: 3,000 yards, 30 TDs [15]". If transferred, specify school for each year
- team_records: Team W-L records by year with citations. Example: "2022: 10-2, State Semifinals [10] | 2023: 12-1, State Champions [15]"
- competition_level: State classification, strength of region/schedule, notable opponents and teammates with citations
- key_games_outcomes: Key game performances with years and citations (or null). Example: "Championship Game (2023): 4 TDs, 300 yards, Win [12] | vs #1 Ranked Team (2023): 2 TDs, Loss [15]"

**intangibles:**
- character_leadership: Character traits, work ethic, leadership qualities from articles/interviews
- twitter_review: Analysis of X/Twitter activity - recruiting news, character indicators, engagement
- academic_profile: Full academic history with GPA over time, academic awards, AP/honors classes, school academic reputation. Example: "GPA: 3.8 (Senior, 2023), 3.6 (Junior, 2022). Honors: AP Scholar, National Honor Society. School: Top-ranked prep school."
- media_coverage: Key insights and narratives from local news, beat writers, media coverage

**rankings_accolades:**
- accolades: Accolades with years and citations. Example: "All-State (2023) [10] | All-American (2023) [12] | MaxPreps National Freshman of Year (2020) [5]"
- source_rankings: Rankings from all sources. Example: "247Sports: 5-star, No. 1 QB | On3: 5-star | ESPN: 4-star, No. 2 nationally"

**conference_awards:**
- Conference awards with years and citations. Example: "First Team All-Conference (2023) [10] | Conference Defensive Player of Year (2023) [12]"

**offers_commits:**
- Scholarship offers and commitments with dates and citations. Example: "Offer: USC (Jan 2023) [5] | Committed: Ohio State (June 2023) [8] | Offer: Alabama (March 2023) [6]"

**athlete_characteristics:**
- Athletic attributes with citations. Example: "Elite speed [10] | Strong arm [12] | High football IQ [15] | Natural leader [20]"

**perception:**
- articles_beat_writers: Article links/summaries with dates and citations (or null). Example: "ESPN recruitment article (June 2023) [10] | Local Times leadership feature (Sept 2023) [15]"
- highlight_reels: Note on where highlight reels can be found (e.g., Hudl link, YouTube channel) (or null)

**external_links:**
- hudl: URL link to Hudl profile (or null)
- social_media: Social media handle or URL (or null)
- red_flags: Any known behavioral, injury, or academic red flags or concerns (or null)

**OUTPUT RULES - READ CAREFULLY:**
- Return ONLY valid JSON that matches the schema exactly
- **CRITICAL**: ALL top-level and nested fields must be STRINGS or NESTED OBJECTS - NEVER dicts/arrays as field values!

**EXAMPLES OF COMMON MISTAKES TO AVOID:**
❌ WRONG: "conference_awards": {{"Conference awards": "..."}}  ← This is a dict object!
✅ CORRECT: "conference_awards": "ACC Offensive Player of Week (Aug 2025) [2] | First Team All-Conference (2024) [5]"

❌ WRONG: "offers_commits": {{"Scholarship offers": "..."}}  ← This is a dict object!
✅ CORRECT: "offers_commits": "Offer: USC (Jan 2023) [5] | Committed: Ohio State (June 2023) [8]"

❌ WRONG: "athlete_characteristics": {{"Athletic attributes": "..."}}  ← This is a dict object!
✅ CORRECT: "athlete_characteristics": "Elite speed [10] | Strong arm [12] | High IQ [15]"

❌ WRONG: "accolades": ["All-State", "All-American"]  ← This is an array!
✅ CORRECT: "accolades": "All-State (2023) [10] | All-American (2023) [12]"

**KEY RULES:**
- Use " | " to separate multiple items in a string
- **ALWAYS include citations [1], [2] and years (2023) where applicable**
- All string fields default to "" if empty (not null unless Optional)
- Do NOT use markdown code blocks (```json) - return raw JSON only
"""

    # 3. Make single grounded API call WITHOUT schema (so grounding works)
    gemini_rest = get_gemini_rest_service()

    response = gemini_rest.make_ai_call(
        prompt=prompt,
        model="gemini-2.5-flash",
        use_grounding=True,
        temperature=0.3
        # NO response_schema - it disables grounding!
    )

    # 4. Parse response
    response_text = gemini_rest.extract_text_from_response(response)

    # Strip markdown code blocks if present (```json ... ```)
    if response_text.startswith('```'):
        lines = response_text.split('\n')
        # Remove first line (```json) and last line (```)
        response_text = '\n'.join(lines[1:-1])

    # Manually parse JSON from response
    report_data = json.loads(response_text)

    # Flatten any incorrectly nested dicts and convert None to empty strings (LLM sometimes ignores instructions)
    def flatten_dicts(obj):
        if obj is None:
            return ""  # Convert None to empty string for string fields
        elif isinstance(obj, dict):
            # Check if this looks like a wrongly nested single-key dict
            if len(obj) == 1:
                key, value = list(obj.items())[0]
                # If the single value is a string, return it directly
                if isinstance(value, str):
                    return value
            # Otherwise recurse into nested structure
            return {k: flatten_dicts(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [flatten_dicts(item) for item in obj]
        return obj

    report_data = flatten_dicts(report_data)

    # 5. Extract sources from grounding metadata
    sources = extract_sources_from_grounding(response)
    report_data['sources'] = [s.model_dump() for s in sources]

    # 6. Create ScoutReport object
    report = ScoutReport(**report_data)

    return report
