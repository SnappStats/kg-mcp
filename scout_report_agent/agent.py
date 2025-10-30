import os
import json
import re
import tempfile
import requests
from typing import Any, Dict
from dotenv import load_dotenv
from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.adk.tools import ToolContext
from google.genai import types
from scout_report_agent.scout_report_schema import ScoutReport, Source
from logger import logger

load_dotenv()

if 'API_GOOGLE_SERVICE_ACCOUNT_CREDENTIALS' in os.environ:
    creds_json = json.loads(os.environ['API_GOOGLE_SERVICE_ACCOUNT_CREDENTIALS'])
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(creds_json, f)
        os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = f.name

PROMPT = """
Generate a comprehensive scout report for the requested player.

**Existing Knowledge Graph Data:**
Use the `search_knowledge_graph` tool to retrieve baseline knowledge about the player from the knowledge graph.

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
* **CITATIONS**: You MUST add inline citation numbers using superscript format after EVERY factual statement
  - Use the format: "Statement here.[1]" or "Multiple facts here.[1,2,3]"
  - Citation numbers correspond to the grounded sources
  - Add citations immediately after each fact or claim
  - Do NOT skip citations for any factual information

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

**OUTPUT FORMAT REQUIREMENTS - READ CAREFULLY:**

YOU MUST RETURN ONLY RAW JSON. NO MARKDOWN, NO CODE BLOCKS, NO EXPLANATIONS.

CORRECT FORMAT:
{
  "player_name": "John Doe",
  "position": "QB",
  ...
}

INCORRECT FORMATS (DO NOT USE):
```json
{...}
```

```
{...}
```

Here is some text...

**STRICT RULES:**
1. Output MUST start with { and end with }
2. NO markdown code blocks (```)
3. NO explanatory text before or after JSON
4. ALL string fields must use double quotes
5. Empty fields should be "" (empty string), NOT null
6. Add citation superscripts [1], [2,3], etc. after every fact in the string values
7. Valid JSON only - check for trailing commas, proper escaping, matching brackets
8. Use natural language with inline citations in all string field values
9. Field names MUST be lowercase with underscores: executive_summary NOT EXECUTIVE_SUMMARY
10. Nested objects MUST use lowercase field names: physical_profile NOT PHYSICAL_PROFILE

REQUIRED FIELD NAMES (EXACT - DO NOT NEST incorrectly):
Root level fields:
- player_name, position, height, weight, school_name, location, graduation_class, gpa, twitter_handle, previous_schools
- executive_summary (string, NOT object)
- offers_commits (string, NOT object)
- athlete_characteristics (string, NOT object)
- hudl (string, NOT nested under external_links)
- social_media (string, NOT nested under external_links)
- red_flags (string, NOT nested under external_links)

Nested object fields:
- physical_profile: {measurements, athletic_testing, physical_development}
- recruiting_profile: {star_ratings, scholarship_offers, latest_offer, visits, school_interest, self_reported_offers}
- team_profile: {high_school_team, coach, conference, recruitment_breakdown}
- statistics: {season_stats, team_records, competition_level, key_games_outcomes}
- intangibles: {character_leadership, twitter_review, academic_profile, media_coverage}
- rankings_accolades: {accolades, source_rankings, conference_awards}
- perception: {articles_beat_writers, highlight_reels}

CITATION REQUIREMENT - MANDATORY:
EVERY fact MUST have inline citations like this: "fact here.[1]" or "multiple facts.[1,2,3]"
Example: "Height: 6'4\" (Texas, 2025).[1] Weight: 219 lbs (247Sports, 2024).[2,3]"
DO NOT write facts without citations!
"""


def search_knowledge_graph(query: str, tool_context: ToolContext) -> dict:
    graph_id = tool_context.metadata.get('graph_id', 'test_graph')
    url = os.environ['KG_URL'] + '/search'
    response = requests.get(url, params={'graph_id': graph_id, 'query': query})
    if response.status_code != 200:
        return {'entities': {}, 'relationships': []}
    if not response.text:
        return {'entities': {}, 'relationships': []}
    return response.json()


agent = Agent(
    name="scout_report_agent",
    model="gemini-2.5-flash",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=512,
        )
    ),
    instruction=PROMPT,
    tools=[search_knowledge_graph]
)


def extract_sources_from_grounding(response: Dict[str, Any]) -> list[Source]:
    try:
        sources = []
        candidates = response.get('candidates', [])
        if not candidates:
            return sources
        grounding_metadata = candidates[0].get('groundingMetadata', {})

        chunks = grounding_metadata.get('grounding_chunks', grounding_metadata.get('groundingChunks', []))
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

        search_entry_point = grounding_metadata.get('search_entry_point', grounding_metadata.get('searchEntryPoint', {}))
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


def generate_scout_report(graph_id: str, player_name: str, max_retries: int = 3) -> ScoutReport:
    from google.genai import Client

    url = os.environ['KG_URL'] + '/search'
    
    logger.info(f'requesting kg read action using url: {url}')
    
    response = requests.get(url, params={'graph_id': graph_id, 'query': player_name})
    if response.status_code != 200 or not response.text:
        logger.error(f'failed KG search request {response.text}')
        kg_data = {'entities': {}, 'relationships': []}
    else:
        logger.info('received response from KG search')
        kg_data = response.json()

    prompt = f"""
{PROMPT}

**Player Name:** {player_name}

**Knowledge Graph Data:**
{json.dumps(kg_data, indent=2)}
"""

    client = Client()

    for attempt in range(max_retries):
        try:
            
            logger.info(f'requesting gemini to generate scout report for player: {player_name}')
            
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            
            logger.info(f'received gemini response to generate scout report for player: {player_name}')

            response_text = response.text

            # Strip markdown code blocks
            if '```json' in response_text:
                start = response_text.find('```json') + 7
                end = response_text.find('```', start)
                if end != -1:
                    response_text = response_text[start:end]
            elif '```' in response_text:
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                if end != -1:
                    response_text = response_text[start:end]
            else:
                # Extract JSON if there's extra text before/after
                # Find the first { and last }
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}')

                if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                    response_text = response_text[start_idx:end_idx + 1]

            response_text = response_text.strip()

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
                report_data = json.loads(response_text)
            except json.JSONDecodeError as e:
                error_file = f'/tmp/gemini_json_error_attempt_{attempt}.json'
                with open(error_file, 'w') as f:
                    f.write(response_text)
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: failed to parse response")

                fixed_json = re.sub(r',(\s*[}\]])', r'\1', response_text)
                try:
                    report_data = json.loads(fixed_json)
                    logger.debug("successfully fixed JSON by removing trailing commas!")
                except json.JSONDecodeError as e2:
                    if attempt < max_retries - 1:
                        logger.warning(f"Attempt {attempt + 1}/{max_retries}: JSON parsing failed, retrying...")
                        continue
                    else:
                        logger.exception(f"All {max_retries} attempts failed to parse JSON")
                        raise e

            report_data = flatten_and_fix(report_data)

            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                    grounding_dict = json.loads(candidate.grounding_metadata.model_dump_json())
                    response_dict = {'candidates': [{'groundingMetadata': grounding_dict}]}
                    sources = extract_sources_from_grounding(response_dict)
                    report_data['sources'] = [s.model_dump() for s in sources]
                else:
                    report_data['sources'] = []
            else:
                report_data['sources'] = []

            report = ScoutReport(**report_data)
            
            logger.info(f'scout report completed for player: {player_name}')
            
            return report

        except Exception as e:
            if attempt < max_retries - 1:
                logger.warning(f"Attempt {attempt + 1}/{max_retries}: Error generating report: {e}, retrying...")
                continue
            else:
                logger.exception(f"All {max_retries} attempts failed")
                raise
