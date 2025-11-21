"""
Research Agent - Uses Gemini with grounded search to gather scout report information
Returns either research notes or feedback messages for ambiguous/not found cases
"""

import os
import requests
from google import genai
from google.genai import types
from utils.logger import logger

RESEARCH_PROMPT = '''
**CONTEXT: This report is for a COACHING STAFF making recruiting decisions. Quality and credibility are CRITICAL.**

YOU MUST FOLLOW THIS FORMAT STRICTLY - coaches rely on accurate, well-sourced information.

**CRITICAL INSTRUCTIONS:**

* You must perform new, online searches for current information. Do not rely on training data.
* **IDENTIFY PLAYER FIRST:**
    - Determine the PRIMARY SPORT for this athlete based on your search
    - If you find an EXACT match for the player → proceed with full research
    - If you find MULTIPLE possible players with this name → Return: "AMBIGUOUS: I found multiple athletes named [name]. Please specify which one by providing additional details (sport, position, school, or location):\n[list all candidates with position, school, year, location, sport]"
    - If you CANNOT find this player → Return: "NOT FOUND: I couldn't find an athlete matching '[name]'. [explain what you searched and suggestions for the user]"
* **VALIDATION:** You must first **validate the player's current or final high school**. Some sources (like Hudl) may list a training academy.
* **CHECK FOR TRANSFERS:** You must also **actively search to see if the player has transferred** and played varsity at any other high school during their career.

**SPORT-SPECIFIC SOURCE REQUIREMENTS:**
* **CRITICAL:** Apply THE SAME LEVEL OF RIGOR regardless of sport - use authoritative, sport-specific recruiting and stats sources
* **WIKIPEDIA:** NEVER use Wikipedia as a primary source. If you find information on Wikipedia, find the actual sources cited in the Wikipedia article and cite those original sources instead.
* **HIGH SCHOOL STATS:** For high school statistics, prioritize in this order:
    1. The high school's official athletic website/page
    2. State-level sport governing body sites (e.g., state athletic associations, state-specific sport sites)
    3. Fall back to MaxPreps, On3, or other national aggregators only if the above aren't available
* Prioritize reputable sources. Use the "Source Guidance" in each section to find the right information FOR THE ATHLETE'S PRIMARY SPORT.
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

**REQUIRED INFORMATION TO COMPILE:**

1. **Player Identity & Basic Info**
   * **Source Guidance:** Use primary recruiting profiles (247Sports, On3, etc.) and team rosters (MaxPreps) to confirm. **Search hudl.com for the player's profile URL** - Hudl hosts game film and athlete profiles widely used by high school athletes and recruiters.
   * Full Name, **Current/Final High School (City, State)**, Team Name, Position(s), Graduation Class
   * List any previous high schools attended while playing varsity (if any are found)
   * **Hudl Profile URL (if found, provide the complete URL as it appears on Hudl, typically in format: https://www.hudl.com/profile/[ID] or https://www.hudl.com/profile/[ID]/[Name-Slug]. CRITICAL: You must VERIFY and VALIDATE that the profile page content matches the correct player being researched (verify name, school, position, graduation year match) before including the URL. Do not include URLs for different players with similar names.)**
   * **X/Twitter handle (if found, format as @username)**, Instagram handle

2. **Recruiting Profile**
   * **Source Guidance:** Search **247Sports, On3, ESPN, and Rivals** directly. **Also, cross-reference the player's X/Twitter feed (if found) for self-reported offers, commitments, or visit news.**
   * **Star Rating & Rankings:** Provide current star ratings and national, position, and state rankings from all four major services (247Sports, On3, ESPN, Rivals). Include 247Sports Composite score.
   * **Scholarship Offers:** List all known college scholarship offers (from services and self-reported on social media). Break down by tier: Elite/CFP contenders, Power 5, Group of 5, FCS.
   * **Latest Offer:** Identify the school that made the most recent offer and the date, if available.
   * **Visits:** Detail any official visits (NCAA-limited to 5) and unofficial visits with dates. Include scheduled future visits.
   * **School Interest:** Note top contending schools. Look for 247Sports Crystal Ball predictions and On3 RPM scores. Note pursuit level (leader, heavy pursuit, etc.).
   * **NIL Valuation:** Search for On3 NIL valuation and any known NIL deals or brand partnerships.
   * **Enrollment Plans:** Note if player plans early enrollment (January), summer enrollment, or fall enrollment.
   * **Family Connections:** Search for parents/siblings who played college or have coaching connections to programs.

3. **Physical & Athletic Profile**
   * **Source Guidance:** Look for combine/camp results (e.g., UCReport, Rivals Camp Series) for verified numbers. For track stats, search `athletic.net` or state athletic association results.
   * **Verified Measurements:** List **all publicly available** verified measurements (height, weight, wingspan, hand size). **If multiple are found from different sources, list each with its source/date (e.g., "Rivals Camp, Mar 2025: 6'2", 195lbs").**
   * **Athletic Testing:**
       * Search for *reported* weight room numbers (bench press, squat, power clean, etc.).
       * Search for track & field stats (40-yard dash, 100m/200m, shuttle, vertical jump, broad jump, shot put, etc.).
       * **If multiple results are found, list each with its source/date.**
   * **Physical Development:** Note any information about physical growth or changes from year to year.
   * **Camp Circuit:** Search for performances at elite camps (Elite 11 Finals, The Opening Finals, Under Armour All-American, Army All-American, Rivals Camp Series). Include camp name, date, performance highlights, rankings/awards won.
   * **Multi-Sport Athlete:** Note if player competed in other sports (basketball, track, baseball, etc.). Include sport, level (varsity/JV), years played, achievements, and whether they stopped to focus on primary sport.

4. **On-Field Performance & Context**
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

5. **Intangibles & Projection**
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
* Each point should be concise and factual. Use [numbered citations] for every fact.
* At the end, include a "SOURCES:" section listing all URLs with their numbers.

If player cannot be identified or is ambiguous, start your response with:
- "AMBIGUOUS: I found multiple athletes named [name]. Please specify which one by providing additional details (sport, position, school, or location):\n[bulleted list of candidates]" OR
- "NOT FOUND: I couldn't find an athlete matching '[name]'. [explanation and suggestions]"
'''

@logger.catch(reraise=True)
def research_player(player_query: str) -> dict:
    """
    Research a player using Gemini with grounded search.

    Returns:
        dict with either:
        - {"status": "success", "notes": str, "sources": [str]} - Research complete, ready to format
        - {"status": "feedback", "message": str} - Needs clarification (AMBIGUOUS, NOT FOUND, etc.)
    """
    client = genai.Client(
        vertexai=True,
        project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        location=os.environ.get('GOOGLE_CLOUD_LOCATION')
    )

    # Use grounded search
    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{RESEARCH_PROMPT}\n\n**PLAYER TO RESEARCH:** {player_query}",
            config=types.GenerateContentConfig(
                temperature=0.1,
                tools=[types.Tool(google_search=types.GoogleSearch()),types.Tool(url_context=types.UrlContext())]
            )
        )
    except Exception as e:
        logger.exception("research agent raised an exception")
        return {
            "status": "feedback",
            "message": f"Error during research: {str(e)}"
        }

    response_text = response.text.strip()

    # If not success (AMBIGUOUS or NOT FOUND), return feedback to root agent
    if response_text.startswith("AMBIGUOUS:") or response_text.startswith("NOT FOUND:"):
        return {
            "status": "feedback",
            "message": response_text
        }

    # Extract sources from grounding metadata and resolve redirects
    sources = []

    if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                grounding_chunks = getattr(candidate.grounding_metadata, 'grounding_chunks', None)
                if grounding_chunks and hasattr(grounding_chunks, '__iter__'):
                    for chunk in grounding_chunks:
                        if hasattr(chunk, 'web') and chunk.web:
                            uri = chunk.web.uri
                            # Resolve grounding API redirect URLs to actual URLs
                            if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                                try:
                                    resp = requests.head(uri, allow_redirects=True, timeout=3)
                                    actual_url = resp.url
                                    if actual_url != uri:
                                        uri = actual_url
                                except Exception:
                                    pass  # Keep the original URI if redirect fails
                            sources.append(uri)

    return {
        "status": "success",
        "notes": response_text,
        "sources": sources
    }
