import json
import os
import re
from typing import Any, Dict
from logger import logger
from floggit import flog

import requests

from scout_report_agent.gemini_rest_service import get_gemini_rest_service
from scout_report_agent.scout_report_schema import ScoutReport, Source


def search_knowledge_graph(graph_id: str, player_name: str) -> dict:
    url = os.environ['KG_MCP_SERVER_URL'] + '/search'
    response = requests.get(url, params={'graph_id': graph_id, 'query': player_name})
    if response.status_code != 200:
        return {'entities': {}, 'relationships': []}
    if not response.text:
        return {'entities': {}, 'relationships': []}
    return response.json()

@flog
def parse_labeled_text(text: str) -> Dict[str, Any]:
    result = {}
    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or ':' not in line:
            continue
        field_path, value = line.split(':', 1)
        field_path = field_path.strip()
        value = value.strip()
        if not value or value.lower() in ['<value or leave blank>', '<value or empty string>', '<value>']:
            value = ""
        if '.' in field_path:
            parts = field_path.split('.')
            current = result
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = value
        else:
            result[field_path] = value
    return result


@flog
def auto_insert_citations(response_text: str, response: Dict[str, Any]) -> str:
    try:
        candidates = response.get('candidates', [])
        if not candidates:
            return response_text
        grounding_metadata = candidates[0].get('groundingMetadata', {})
        grounding_supports = grounding_metadata.get('groundingSupports', [])
        if not grounding_supports:
            return response_text
        sorted_supports = sorted(grounding_supports, key=lambda x: x['segment']['startIndex'], reverse=True)
        result = response_text
        for support in sorted_supports:
            segment = support['segment']
            chunk_indices = support.get('groundingChunkIndices', [])
            if not chunk_indices:
                continue
            citation_numbers = [str(idx + 1) for idx in chunk_indices]
            citation = f" [{','.join(citation_numbers)}]"
            end_index = segment['endIndex']
            result = result[:end_index] + citation + result[end_index:]
        return result
    except Exception as e:
        logger.exception(f"Warning: Failed to auto-insert citations")
        return response_text


@flog
def extract_sources_from_grounding(response: Dict[str, Any]) -> list[Source]:
    try:
        import re
        sources = []
        candidates = response.get('candidates', [])
        if not candidates:
            return sources
        grounding_metadata = candidates[0].get('groundingMetadata', {})

        # Try old format first (groundingChunks)
        chunks = grounding_metadata.get('groundingChunks', [])
        if chunks:
            for idx, chunk in enumerate(chunks):
                web = chunk.get('web', {})
                title = web.get('title', 'Unknown Source')
                uri = web.get('uri', 'No URL')
                if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                    try:
                        resp = requests.head(uri, allow_redirects=True, timeout=3)
                        actual_url = resp.url
                        if actual_url != uri:
                            uri = actual_url
                    except Exception:
                        pass
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

        # Try new format (searchEntryPoint with embedded HTML)
        search_entry_point = grounding_metadata.get('searchEntryPoint', {})
        rendered_content = search_entry_point.get('renderedContent', '')
        if rendered_content:
            pattern = r'<a\s+class="chip"\s+href="([^"]+)">([^<]+)</a>'
            matches = re.findall(pattern, rendered_content)
            for idx, (url, title) in enumerate(matches):
                if url and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in url:
                    try:
                        resp = requests.head(url, allow_redirects=True, timeout=3)
                        actual_url = resp.url
                        if actual_url != url:
                            url = actual_url
                    except Exception:
                        pass
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
                    url=url
                ))

        return sources
    except Exception as e:
        print(f"Warning: Failed to extract sources: {e}")
        return []


@flog
def generate_scout_report(graph_id: str, player_name: str) -> ScoutReport:
    kg_data = search_knowledge_graph(graph_id, player_name)
    prompt = f"""
    Generate a comprehensive scout report for {player_name}.

    **Existing Knowledge Graph Data:**
    {json.dumps(kg_data, indent=2)}

    Use the knowledge graph data as baseline reference. Validate and fill gaps with targeted web searches.

    **SEARCH STRATEGY:**
    1. Start with 247Sports/On3 player profile pages (most comprehensive single sources)
    2. Cross-reference MaxPreps for stats
    3. Check player's Twitter/Instagram for self-reported info
    4. Use local news only for unique stories/quotes

    **CRITICAL INSTRUCTIONS:**
    * Be COMPREHENSIVE but EFFICIENT - prioritize high-signal sources
    * **VALIDATE** current/final high school (watch for IMG Academy, Bishop Gorman transfers)
    * **CHECK FOR TRANSFERS** if you see conflicting school information
    * **CITATIONS**: Auto-added from grounding - just write facts naturally

    ---

    ## QUICK ACCESS FIELDS

    **Sources: 247Sports, On3, ESPN Recruiting, Rivals (pick best 1-2)**

    - player_name: Full name
    - position: Position(s) - e.g., "QB", "WR/DB"
    - height: Most recent from major recruiting service. Format: "6'4\""
    - weight: Most recent from major recruiting service. Format: "219 lbs"
    - school_name: "School Name (City, State)"
    - location: "City, State"
    - graduation_class: "2025"
    - gpa: Just number "3.8" or null (detail goes in academic_profile)
    - twitter_handle: "@username" or null
    - previous_schools: "St. John's HS (2020-2021), IMG Academy (2022)" or ""

    ---

    ## EXECUTIVE SUMMARY
    Brief overview of player profile, strengths, potential (2-3 sentences)

    ---

    ## PHYSICAL PROFILE

    **measurements**
    *Sources: 247Sports Composite, On3, official college roster (if committed), 1-2 camp measurements*

    Track growth over time. Example format:
    "Height: 6'4\" (Texas Athletics, 2025), 6'3.5\" (247Sports, 2024), 6'3\" (HS, 2022). Weight: 219 lbs (Texas, 2025), 215 lbs (247Sports, 2024), 205 lbs (HS, 2022)"

    **athletic_testing**
    *Sources: The Opening Finals, All-American Bowl measurements, 247Sports/On3 profiles, player Twitter*

    Include: 40-yard dash, shuttle, vertical, broad jump, bench, squat, track times (if applicable). Example:
    "40-yard dash: 4.48s (The Opening, 2024), Bench: 315 lbs, Squat: 450 lbs, Vertical: 38\""

    **physical_development**
    *Sources: Year-over-year comparison from above sources*

    Note: weight gain/loss, growth spurts, strength progression, injury history. Example:
    "Added 15 lbs muscle junior to senior year. Grew 2\" sophomore to junior season."

    ---

    ## RECRUITING PROFILE

    **star_ratings**
    *Sources: 247Sports Composite (primary), On3, ESPN, Rivals*

    Get composite + individual ratings. Example:
    "247Sports: 5-star, No. 1 QB, No. 1 overall | On3: 5-star, No. 2 QB | ESPN: 4-star, No. 2 QB | Rivals: 5-star | 247 Composite: 5-star, 0.9985"

    **scholarship_offers**
    *Sources: 247Sports Crystal Ball page, On3 Recruiting Profile, player Twitter*

    List ALL offers as comma-separated. Don't need dates here.
    "Texas, Georgia, Alabama, LSU, Ohio State, Michigan, USC, Oregon..."

    **latest_offer**
    *Source: 247Sports "Recent Activity" or On3 Timeline*

    Most recent with date: "USC (October 15, 2024)" or "Alabama (October 2024)"

    **visits**
    *Source: 247Sports Visit Tracker, On3 Visits section*

    "Official: Texas (June 14-16, 2024), Georgia (June 7-9, 2024) | Unofficial: Alabama (March 2024), LSU (Spring Game, April 2024)"

    **school_interest**
    *Source: 247Sports Crystal Ball, On3 Recruiting Prediction Machine (RPM)*

    Top contenders and their pursuit level: "Texas (leader, 85% CB), Georgia (heavy pursuit), Alabama (consistent contact)"

    **self_reported_offers**
    *Source: Player's Twitter/Instagram*

    Check for commitment announcements, offer graphics: "Announced commitment to Texas via Twitter (July 4, 2024). Posted Georgia offer graphic (May 2024)"

    ---

    ## TEAM PROFILE

    **high_school_team**
    *Source: MaxPreps team page, school athletics site*

    Full team name: "Lake Travis Cavaliers"

    **coach**
    *Source: MaxPreps roster page, school athletics site*

    "Head Coach Mike Smith"

    **conference**
    *Source: MaxPreps standings/schedule*

    "District 25-6A" or "Trinity League"

    **recruitment_breakdown**
    *Source: 247Sports Team Commits page for that high school*

    Search: "[high school name] 247sports". Note D1 teammates:
    "5 teammates signed D1 (2024): RB John Doe (3-star, Texas Tech), OL Mike Jones (4-star, Oklahoma). Strong D1 pipeline."

    ---

    ## STATISTICS

    **season_stats**
    *Source: MaxPreps player profile (primary), school athletics site*

    Year-by-year stats with grade level:
    "2024 Senior: 3,845 pass yds, 42 TDs, 4 INTs, 68% comp | 2023 Junior: 2,912 yds, 28 TDs, 6 INTs | 2022 Soph: 1,856 yds, 18 TDs"

    **team_records**
    *Source: MaxPreps team page*

    "2024: 13-1, State Champions | 2023: 11-2, State Semifinals | 2022: 9-3"

    **competition_level**
    *Source: MaxPreps (classification), state rankings site*

    State classification, region strength: "Texas 6A Division I (highest). Faced 3 top-25 ranked teams. Trinity League (nation's toughest conference)."

    **key_games_outcomes**
    *Source: MaxPreps game logs*

    Big performances: "State Championship (2024): 425 yds, 5 TDs, Win 45-42 | vs No. 1 Duncanville: 380 yds, 3 TDs, Loss 31-28"

    ---

    ## INTANGIBLES

    **character_leadership**
    *Source: 247Sports/On3/ESPN scouting reports and interviews, local news feature story*

    Coach quotes, leadership roles, work ethic: "Described as 'exceptional leader' by coach. Team captain senior year. Known for film study habits. Volunteers at youth camps."

    **twitter_review**
    *Source: Player's Twitter/X directly*

    Analyze: commitment post, offer graphics, training videos, character indicators:
    "Active @PlayerHandle - posts workouts regularly. Announced commitment July 4 with family. Shares motivational content and faith posts."

    **academic_profile**
    *Source: 247Sports/On3 profile (GPA often listed), local news mentions, school honor roll*

    GPA progression, honors: "GPA: 3.9 (247Sports, 2024), 3.8 (2023). Academic All-State (2024). National Honor Society. AP Scholar."

    **media_coverage**
    *Source: Google News search "[player_name] [city]", check 1-2 feature articles*

    Key narratives: "Dallas Morning News profile highlighted leadership (Sept 2024). Local writer: 'most polished QB in state'. Praised for championship poise."

    ---

    ## RANKINGS & ACCOLADES

    **accolades**
    *Sources: 247Sports profile, MaxPreps awards section, state athletic association site*

    ALL major honors:
    "Under Armour All-American (2024), MaxPreps Junior All-American (2023), Gatorade State POY (2024), First Team All-State (2024, 2023), USA Today All-USA (2024), Mr. Football Texas (2024)"

    **source_rankings**
    *Sources: 247Sports Composite page, On3, ESPN, Rivals*

    All major service rankings:
    "247Sports: 5-star, 0.9998, No. 1 QB, No. 1 overall | On3: 5-star, 98.50, No. 2 QB | ESPN: 4-star, No. 2 QB | Rivals: 5-star, No. 1 QB | 247 Composite: 0.9987, No. 1 overall"

    **conference_awards**
    *Source: MaxPreps awards, local news*

    "District 25-6A Offensive MVP (2024, 2023), First Team All-District (2024, 2023, 2022), Trinity League Offensive POY (2024)"

    ---

    ## OFFERS & COMMITS

    **offers_commits**
    *Sources: 247Sports Crystal Ball/Offers page, player Twitter timeline*

    All offers with dates (when available) + commitment:
    "Committed: Texas (July 4, 2024) | Offers: Georgia (June 2024), Alabama (May 2024), Ohio State (April 2024), LSU (March 2024) | Decommitted: Oklahoma (June 2024)"

    ---

    ## ATHLETE CHARACTERISTICS

    **athlete_characteristics**
    *Sources: 247Sports scouting report, On3 evaluation, ESPN/Rivals analysis*

    Playing style, strengths, areas for improvement:
    "Elite arm strength 60+ yard range. Exceptional pocket presence. High football IQ, advanced reads. Dual-threat, 4.6 forty. Natural leader. Quick release. Needs to improve deep ball accuracy."

    ---

    ## PERCEPTION

    **articles_beat_writers**
    *Source: Google News "[player_name] feature" - pick 2-3 best articles*

    Key media coverage:
    "ESPN feature on recruitment (Aug 2024): Family decision process. Dallas Morning News: 'Best QB prospect since Vince Young' (Sept 2024). 247Sports: Comparison to Patrick Mahomes (July 2024)."

    **highlight_reels**
    *Source: Search "[player_name] Hudl" or check MaxPreps media tab*

    "Hudl profile: hudl.com/profile/12345678. MaxPreps highlights available. YouTube game film: youtube.com/@playerhandle"

    ---

    ## EXTERNAL LINKS

    **hudl**: Search "[player_name] Hudl" → "https://www.hudl.com/profile/12345678" or null

    **social_media**: "Twitter: @PlayerHandle, Instagram: @playerhandle" or null

    **red_flags**: Be objective about injuries, discipline, academic concerns:
    "Minor ankle injury (2 games missed junior year). No behavioral/academic concerns." or "No known red flags"

    ---

    **OUTPUT FORMAT:**
    - Return valid JSON matching schema exactly
    - Use natural language - clear, comprehensive facts
    - Separate items with commas or bullets in strings
    - Do NOT add citation numbers manually - auto-inserted by grounding
    - Empty string fields: "" (not null unless Optional type)
    - Do NOT use markdown code blocks - raw JSON only
    """

    gemini_rest = get_gemini_rest_service()
    response = gemini_rest.make_ai_call(
        prompt=prompt,
        model="gemini-2.5-flash",
        use_grounding=True,
        temperature=0.1
    )

    response_text = gemini_rest.extract_text_from_response(response)
    response_text_with_citations = auto_insert_citations(response_text, response)

    if response_text_with_citations.startswith('```'):
        lines = response_text_with_citations.split('\n')
        response_text_with_citations = '\n'.join(lines[1:-1])

    def flatten_and_fix(obj):
        if obj is None:
            return ""
        elif isinstance(obj, dict):
            if len(obj) == 1:
                _, value = list(obj.items())[0]
                if isinstance(value, str):
                    return value
            return {k: flatten_and_fix(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [flatten_and_fix(item) for item in obj]
        return obj

    try:
        report_data = json.loads(response_text_with_citations)
    except json.JSONDecodeError as e:
        error_file = '/tmp/gemini_pro_json_error.json'
        with open(error_file, 'w') as f:
            f.write(response_text_with_citations)
        logger.exception(f"failed to parse response with citations")
        lines = response_text_with_citations.split('\n')
        start = max(0, e.lineno - 3)
        end = min(len(lines), e.lineno + 2)
        for i in range(start, end):
            marker = ">>> " if i == e.lineno - 1 else "    "
            logger.debug(f"{marker}{i+1}: {lines[i]}")
        logger.debug("attempting to fix common JSON errors...")
        fixed_json = re.sub(r',(\s*[}\]])', r'\1', response_text_with_citations)
        try:
            report_data = json.loads(fixed_json)
            logger.debug("successfully fixed JSON by removing trailing commas!")
        except json.JSONDecodeError as e2:
            logger.exception(f"failed to parse json after attempt to fixe line errors")
            raise e

    report_data = flatten_and_fix(report_data)
    sources = extract_sources_from_grounding(response)
    report_data['sources'] = [s.model_dump() for s in sources]
    report = ScoutReport(**report_data)
    return report
