"""
Scout Report Agent - Generates comprehensive scout reports for athletes
Uses direct Gemini REST API calls with Google Search grounding
"""
from floggit import flog
import os
import time
import requests
from typing import Dict, Any, List
from dotenv import load_dotenv
from logger import logger

load_dotenv()


def _add_citations(response: Dict[str, Any], text: str) -> str:
    """Add simple [1], [2] citations to text based on grounding supports"""
    try:
        if not isinstance(response, dict) or not response.get('candidates'):
            return text

        candidates = response.get('candidates', [])
        if not candidates:
            return text

        candidate = candidates[0]
        grounding_metadata = candidate.get('groundingMetadata')
        if not grounding_metadata:
            return text

        supports = grounding_metadata.get('groundingSupports', [])
        chunks = grounding_metadata.get('groundingChunks', [])

        if not supports or not chunks:
            return text

        sorted_supports = sorted(supports, key=lambda s: s.get('segment', {}).get('endIndex', 0), reverse=True)

        for support in sorted_supports:
            segment = support.get('segment', {})
            end_index = segment.get('endIndex', 0)
            grounding_chunk_indices = support.get('groundingChunkIndices', [])

            if grounding_chunk_indices:
                citation_numbers = []
                for i in grounding_chunk_indices:
                    if i < len(chunks):
                        citation_numbers.append(f"[{i + 1}]")

                citation_string = "".join(citation_numbers)
                text = text[:end_index] + citation_string + text[end_index:]

        return text
    except Exception:
        return text


def _extract_sources(response: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract citation sources from grounding metadata in response"""
    try:
        citation_sources = []

        if not isinstance(response, dict):
            return citation_sources

        candidates = response.get('candidates', [])
        if not candidates:
            return citation_sources

        grounding_metadata = candidates[0].get('groundingMetadata', {})
        chunks = grounding_metadata.get('groundingChunks', [])

        for chunk in chunks:
            web = chunk.get('web', {})
            title = web.get('title', 'Unknown Source')
            uri = web.get('uri', 'No URL')

            # Resolve redirect URLs
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

            citation_sources.append({
                'number': len(citation_sources) + 1,
                'title': clean_title,
                'url': uri
            })

        return citation_sources

    except Exception:
        return []


@flog
def generate_scout_report(graph_id: str, player_name: str, max_retries: int = 3, ctx=None) -> Dict[str, Any]:
    """
    Generate comprehensive scout report using Gemini with Google Search grounding.
    Returns text with citations and sources.

    Args:
        graph_id: Knowledge graph ID
        player_name: Player name to scout
        max_retries: Max retries for API calls
        ctx: Optional context

    Returns:
        Dict with 'notes' (text with citations) and 'sources' (list of citation dicts)
    """
    try:
        # Get KG data for context
        url = os.environ['KG_URL'] + '/search'
        logger.info(f'requesting kg read action using url: {url}')

        response = requests.get(url, params={'graph_id': graph_id, 'query': player_name})
        if response.status_code != 200 or not response.text:
            logger.error(f'failed KG search request {response.text}')
            kg_data = {'entities': {}, 'relationships': []}
        else:
            logger.info('received response from KG search')
            kg_data = response.json()

        # Build search info from KG data if available
        search_info = player_name
        kg_context = ""

        if kg_data and kg_data.get('entities'):
            # Extract relevant info from KG entities
            entities = kg_data.get('entities', {})

            # Look for player entity
            for entity in entities.values():
                entity_type = entity.get('type', '').lower()
                if 'player' in entity_type or 'athlete' in entity_type:
                    # Extract known info
                    props = entity.get('properties', {})
                    if props.get('position'):
                        search_info += f" {props['position']}"
                    if props.get('school'):
                        search_info += f" {props['school']}"
                    if props.get('graduation_class'):
                        search_info += f" class {props['graduation_class']}"
                    if props.get('location'):
                        search_info += f" {props['location']}"

                    # Build KG context string
                    if props:
                        kg_context = "\n**Existing Knowledge Graph Data:**\n"
                        kg_context += "Use this as baseline reference to validate and supplement with current web searches:\n"
                        for key, value in props.items():
                            if value:
                                kg_context += f"- {key}: {value}\n"
                    break

        if not kg_context:
            kg_context = "\n**No existing knowledge graph data available.** Start from scratch with web searches.\n"

        # Get current date for search queries
        from datetime import datetime
        current_date = datetime.now().strftime('%Y-%m-%d')

        # Build comprehensive prompt
        prompt = f"""
**CONTEXT: This report is for a COACHING STAFF making recruiting decisions. Quality and credibility are CRITICAL.**

YOU MUST FOLLOW THIS FORMAT STRICTLY - coaches rely on accurate, well-sourced information.

**Current Date: {current_date}** - Use this in your search queries to get the most recent information (e.g., "player name 2024 stats", "player name 2025 recruiting"). This is especially important for high school players to get their current season stats and recruiting status.

**Objective:**
Collect and summarize all available verified, up-to-date information and scouting context for the athlete: {search_info}.
Here is the knowledge graph result, use what you can from it to inform the search: {kg_context}

**CRITICAL INSTRUCTIONS:**

* You must perform new, online searches for current information. Do not rely on training data.
* **IDENTIFY PLAYER FIRST:**
    - Determine the PRIMARY SPORT for this athlete based on your search
    - If you find an EXACT match for the player → proceed with the full report
    - If you find MULTIPLE possible players with this name → List all candidates you found with their distinguishing info (position, school, year, location, sport) and state "AMBIGUOUS - Multiple players found" at the top
    - If you CANNOT find this player → State "PLAYER NOT FOUND" at the top and explain what you searched and why you couldn't identify them
* **VALIDATION:** You must first **validate the player's current or final high school**. Some sources (like Hudl) may list a training academy.
* **CHECK FOR TRANSFERS:** You must also **actively search to see if the player has transferred** and played varsity at any other high school during their career.

**SPORT-SPECIFIC SOURCE REQUIREMENTS:**
* **CRITICAL:** Apply THE SAME LEVEL OF RIGOR regardless of sport - use authoritative, sport-specific recruiting and stats sources
* DO NOT rely on Wikipedia as a primary source - use actual sports recruiting sites with real scouting data, stats, and recruiting information
* **FOOTBALL:** 247Sports, On3, ESPN, Rivals, MaxPreps, The Athletic, Pro Football Focus (PFF)
* **BASKETBALL:** 247Sports Basketball, Rivals Hoops, ESPN Basketball, On3 Basketball, PrepHoops, VerbalCommits, Prep Circuit, Grassroots Hoops, Ballislife, EYB (EvalYouthBasketball), KenPom (college analytics), Synergy Sports (video/analytics)
* **TRACK & FIELD:** Athletic.net, MileSplit, DyeStat, FloTrack, TFRRS (Track & Field Results Reporting System), state athletic association results, USTFCCCA rankings
* **BASEBALL:** Perfect Game (PG), Prep Baseball Report (PBR), Baseball America, D1Baseball, MaxPreps Baseball, Extra Innings Elite, Prospects1500
* **SOCCER:** TopDrawerSoccer, United Soccer Coaches, IMG Academy Soccer, College Soccer News, SoccerWire, YouthSoccerRankings
* **VOLLEYBALL:** PrepVolleyball (PrepDig), MaxPreps Volleyball, VolleyballMag, PrepVolleyball.com recruiting rankings
* **LACROSSE:** Inside Lacrosse (IL), Lacrosse Bucket, USA Lacrosse Magazine, NXT Level Lacrosse
* **WRESTLING:** FloWrestling, MatScouts, The Open Mat (TOM), WrestlingStat, TrackWrestling
* **SWIMMING:** SwimSwam, USA Swimming Times Database, CollegeSwimming.com
* **OTHER SPORTS:** Find and use the equivalent authoritative recruiting/stats sites for that sport (national governing body, recruiting-focused sites, verified stats databases)
* Prioritize reputable sources. Use the "Source Guidance" in each section to find the right information FOR THE ATHLETE'S PRIMARY SPORT.

**REQUIRED INFORMATION TO COMPILE (FOOTBALL EXAMPLE):**

1.  **Player Identity & Basic Info**
    * **Source Guidance:** Use primary recruiting profiles (247Sports, On3, etc.) and team rosters (MaxPreps) to confirm.
    * Full Name, **Current/Final High School (City, State)**, Position(s), and Graduation Class.
    * List any previous high schools attended while playing varsity (if any are found).
    * **X/Twitter handle (if found, format as @username)**.

2.  **Recruiting Profile**
    * **Source Guidance:** Search **247Sports, On3, ESPN, and Rivals** directly. **Also, cross-reference the player's X/Twitter feed (if found) for self-reported offers, commitments, or visit news.**
    * **Star Rating & Rankings:** Provide current star ratings and national, position, and state rankings from all four major services (247Sports, On3, ESPN, Rivals). Include 247Sports Composite score.
    * **Scholarship Offers:** List all known college scholarship offers (from services and self-reported on social media). Break down by tier: Elite/CFP contenders, Power 5, Group of 5, FCS.
    * **Latest Offer:** Identify the school that made the most recent offer and the date, if available.
    * **Visits:** Detail any official visits (NCAA-limited to 5) and unofficial visits with dates. Include scheduled future visits.
    * **School Interest:** Note top contending schools. Look for 247Sports Crystal Ball predictions and On3 RPM scores. Note pursuit level (leader, heavy pursuit, etc.).
    * **NIL Valuation:** Search for On3 NIL valuation and any known NIL deals or brand partnerships.
    * **Enrollment Plans:** Note if player plans early enrollment (January), summer enrollment, or fall enrollment.
    * **Family Connections:** Search for parents/siblings who played college football or have coaching connections to programs.

3.  **Physical & Athletic Profile**
    * **Source Guidance:** Look for combine/camp results (e.g., UCReport, Rivals Camp Series) for verified numbers. For track stats, search `athletic.net` or state athletic association results.
    * **Verified Measurements:** List **all publicly available** verified measurements (height, weight, wingspan, hand size). **If multiple are found from different sources, list each with its source/date (e.g., "Rivals Camp, Mar 2025: 6'2", 195lbs").**
    * **Athletic Testing:**
        * Search for *reported* weight room numbers (bench press, squat, power clean, etc.).
        * Search for track & field stats (40-yard dash, 100m/200m, shuttle, vertical jump, broad jump, shot put, etc.).
        * **If multiple results are found, list each with its source/date.**
    * **Physical Development:** Note any information about physical growth or changes from year to year.
    * **Camp Circuit:** Search for performances at elite camps (Elite 11 Finals, The Opening Finals, Under Armour All-American, Army All-American, Rivals Camp Series). Include camp name, date, performance highlights, rankings/awards won.
    * **Multi-Sport Athlete:** Note if player competed in other sports (basketball, track, baseball, etc.). Include sport, level (varsity/JV), years played, achievements, and whether they stopped to focus on football.

4.  **On-Field Performance & Context**
    * **Source Guidance:** Use `MaxPreps` for stats and team records. Use local news sports sections to find articles on team strength, classification, and **to confirm any transfer reports**.
    * **Production & Statistics:** Provide a **year-by-year (e.g., Sophomore, Junior, Senior) breakdown of all available varsity stats.** Note any standout single-game performances. **If the player transferred, specify which stats correspond to which high school.**
    * **Key Games/Standout Performances:** Search for performances vs ranked opponents, championship games, career-high games. Include opponent name/ranking, full stat line, game result/score, and context.
    * **Accomplishments:** List individual awards, all-region/all-state honors, or team leadership roles for each year. Include conference/district awards (POY, All-Conference teams).
    * **Team Success:** Detail team accomplishments, including **team records for each year the player was on varsity (at each school, if they transferred)**, playoff appearances, and championships.
    * **Level of Competition:** For each school attended, describe the type of competition faced (e.g., state classification/division, strength of region) and note any **notable opponents or highly-recruited teammates**.
    * **Team Context:**
        * **Conference Strength:** Total D1 signees from conference schools, nationally ranked teams in conference.
        * **School Recruiting History:** Historical D1 pipeline - signee counts for last 3-5 years with P5 vs G5 breakdown.
        * **Teammate Recruits:** Other D1 prospects on the roster with their positions, ratings, and offer counts.
        * **Opponent Quality:** Record vs ranked opponents, record vs teams with 5+ D1 recruits.
        * **Strength of Schedule:** Number of nationally ranked opponents faced, combined opponent record, playoff teams faced.

5.  **Intangibles & Projection**
    * **Source Guidance:** Search local news outlets for human-interest stories, player interviews, or scholar-athlete awards. The player's X/Twitter feed is also a primary source. Look for recruiting analyst quotes and scouting reports.
    * **Character & Leadership:** Synthesize information from news articles or interviews that speaks to the player's character, work ethic, or leadership qualities.
    * **X/Twitter Review (If Handle Found):**
        * **Crucial:** Review the player's public X/Twitter feed (e.g., using search operators or third-party viewers).
        * **Recruiting:** Identify any self-reported offers, commitments, or de-commitments not found on main sites. **Cite the specific tweet/date if possible.**
        * **Character:** **Objectively note** any publicly visible posts related to off-field concerns, use of problematic/hateful language, or extreme negativity, as well as positive examples of leadership or character.
    * **Academic Profile:**
        * **Source Guidance:** Search local news for "scholar-athlete" awards, school honor rolls, or Niche/GreatSchools for high school academic reputation.
        * **Individual Standing:** Search for any **publicly available** GPA, academic awards (e.g., Honor Roll, Scholar-Athlete), or mentions of AP/honors courses.
        * **School Academic Context:** Briefly assess the academic reputation of their high school(s) (e.g., "Attends a highly-rated public school," "well-regarded private prep school," etc.).
    * **Scout Projection:** Search for analyst projections on college readiness (Day 1 starter vs redshirt), development timeline, ceiling/floor analysis, potential NFL draft projection.
    * **Player Comparisons:** Look for pro/college player comparisons from recruiting analysts (247Sports, On3, ESPN, Rivals). Search for phrases like "reminds of", "similar to", "plays like". Include why the comparison fits.
    * **Media Coverage:** Mention key insights from local news or beat writer articles not already covered.

**OUTPUT FORMAT:**

* Provide a concise, structured summary using labeled sections for each category above (e.g., "Recruiting Profile," "Physical & Athletic Profile," etc.).
* Within each section, use clear bullet points to present the factual information.
* Prioritize verified measurements over basic profile stats.
* Each point should be concise and factual. Citations will be automatically added to link to sources.
* Do not use italics at all. Do not use markedown formatting at all.  You can bold and use bullets. Thats it.
"""

        # Make Gemini REST API call with retries
        api_key = os.environ.get('GOOGLE_API_KEY')
        if not api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set")

        base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        model = "gemini-2.5-flash"

        response = None
        for attempt in range(max_retries):
            try:
                api_url = f"{base_url}/{model}:generateContent?key={api_key}"

                payload = {
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.1},
                    "tools": [{"googleSearch": {}}]
                }

                logger.info(f"Making Gemini REST API call to {model} (grounding=True)")

                api_response = requests.post(
                    api_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=120
                )
                api_response.raise_for_status()
                response = api_response.json()

                logger.info(f"Received Gemini response")
                break
            except Exception as api_error:
                error_msg = str(api_error)
                if attempt < max_retries - 1 and ('500' in error_msg or 'INTERNAL' in error_msg or 'internal error' in error_msg.lower()):
                    time.sleep(1.5 * (attempt + 1))
                    continue
                else:
                    raise api_error

        if not response:
            raise ValueError('No response from Gemini API')

        # Extract raw notes
        raw_notes = response.get('candidates', [{}])[0].get('content', {}).get('parts', [{}])[0].get('text', '') if isinstance(response, dict) and response.get('candidates') else ''

        # Add citations
        notes_with_citations = _add_citations(response, raw_notes)

        # Extract sources
        citation_sources = _extract_sources(response)

        if notes_with_citations and len(notes_with_citations) > 50:
            logger.info(f"Generated scout report for {player_name}: {len(citation_sources)} sources")
            return {
                'notes': notes_with_citations,
                'sources': citation_sources
            }
        else:
            return {
                'notes': f"Limited information available for {player_name}.",
                'sources': []
            }

    except Exception as e:
        logger.error(f"Error generating scout report: {e}")
        raise
