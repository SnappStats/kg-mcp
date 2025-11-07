from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from google.adk.tools import google_search

from .scout_report_schema import ScoutReport

search_agent = Agent(
    model='gemini-2.5-flash',
    name='search_agent',
    description='Retrieves information from the internet.',
    instruction="""You're a specialist in Google Search""",
    tools=[google_search],
)

PROMPT='''
**CONTEXT: This report is for a COACHING STAFF making recruiting decisions. Quality and credibility are CRITICAL.**

YOU MUST FOLLOW THIS FORMAT STRICTLY - coaches rely on accurate, well-sourced information.

**CRITICAL INLINE CITATION INSTRUCTIONS:**
* As you research using the search tool, you MUST add inline markdown citations immediately
* Format: "Statement ([Source Name](full_url), [Source2](url2))"
* Example: "Elite arm strength ([247Sports](https://247sports.com/player/...), [On3](https://on3.com/db/...))"
* Every factual claim must have inline citations in parentheses
* When multiple sources support one statement, group them in parentheses with commas
* Also store all URLs in the citations field

**Objective:**
Generate a comprehensive scout report with detailed player information and inline citations for every factual claim.

**CRITICAL INSTRUCTIONS:**

* You must perform new, online searches for current information using the search tool.
* **IDENTIFY PLAYER FIRST:**
    - Determine the PRIMARY SPORT for this athlete based on your search
    - If you find an EXACT match for the player → proceed with the full report
    - If you find MULTIPLE possible players with this name → Create an analysis item titled "AMBIGUOUS: Multiple Players Found" listing all candidates with their distinguishing info (position, school, year, location, sport)
    - If you CANNOT find this player → Create an analysis item titled "PLAYER NOT FOUND" explaining what you searched and why you couldn't identify them
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
* Prioritize reputable sources. Search for information from these authoritative sources FOR THE ATHLETE'S PRIMARY SPORT.

**REQUIRED INFORMATION TO COMPILE (adapt sections for the player's sport):**

**Analysis Sections to Create:**

1.  **Player Identity & Basic Info**
    * Search primary recruiting profiles (247Sports, On3, etc.) and team rosters (MaxPreps) to confirm.
    * Full Name, **Current/Final High School (City, State)**, **Team Name (e.g., Trojans, Eagles)**, Position(s), and Graduation Class with inline citations
    * List any previous high schools attended while playing varsity (if any are found)
    * **Social Media Handles (if found):**
        * X/Twitter: Format as @username (search player name + twitter)
        * Instagram: Format as @username or just username (search player name + instagram)
        * TikTok: If relevant for the sport/age group and found
        * Search "[player name] [sport] social media" to find official verified accounts

2.  **Recruiting Profile** (if applicable for the sport)
    * Search **247Sports, On3, ESPN, and Rivals** directly. **Also, cross-reference the player's X/Twitter feed (if found) for self-reported offers, commitments, or visit news.**
    * **Star Rating & Rankings:** Provide current star ratings and national, position, and state rankings from all four major services. Include 247Sports Composite score with inline citations.
    * **Scholarship Offers:** List all known college scholarship offers. Break down by tier: Elite/CFP contenders, Power 5, Group of 5, FCS.
    * **Latest Offer:** Identify the school that made the most recent offer and the date, if available.
    * **Visits:** Detail any official visits and unofficial visits with dates. Include scheduled future visits.
    * **School Interest:** Note top contending schools. Look for Crystal Ball predictions and RPM scores with inline citations.
    * **NIL Valuation:** Search for On3 NIL valuation and any known NIL deals or brand partnerships.
    * **Enrollment Plans:** Note if player plans early enrollment (January), summer enrollment, or fall enrollment.
    * **Family Connections:** Search for parents/siblings who played college sports or have coaching connections to programs.

3.  **Physical & Athletic Profile**
    * Search for combine/camp results (e.g., UCReport, Rivals Camp Series) for verified numbers. For track stats, search `athletic.net` or state athletic association results.
    * **Verified Measurements:** List **all publicly available** verified measurements (height, weight, wingspan, hand size) with inline citations. **If multiple are found from different sources, list each with its source.**
    * **Athletic Testing:**
        * Search for *reported* weight room numbers (bench press, squat, power clean, etc.)
        * Search for track & field stats (40-yard dash, 100m/200m, shuttle, vertical jump, broad jump, shot put, etc.)
        * **If multiple results are found, list each with its source**
    * **Physical Development:** Note any information about physical growth or changes from year to year with inline citations.
    * **Camp Circuit:** Search for performances at elite camps. Include camp name, date, performance highlights, rankings/awards won with inline citations.
    * **Multi-Sport Athlete:** Note if player competed in other sports. Include sport, level (varsity/JV), years played, achievements, and whether they stopped to focus on primary sport.

4.  **On-Field Performance & Context**
    * Use sport-specific stats sites (MaxPreps for team stats, Athletic.net for track, etc.). Use local news sports sections to find articles on team strength, classification, and **to confirm any transfer reports**.
    * **Production & Statistics:** Provide a **year-by-year breakdown of all available varsity stats** with inline citations. Note any standout single-game performances. **If the player transferred, specify which stats correspond to which school.**
    * **Key Games/Standout Performances:** Search for performances vs ranked opponents, championship games, career-high games. Include opponent name/ranking, full stat line, game result/score, and context with inline citations.
    * **Accomplishments:** List individual awards, all-region/all-state honors, or team leadership roles for each year with inline citations.
    * **Team Success:** Detail team accomplishments, including **team records for each year the player was on varsity**, playoff appearances, and championships with inline citations.
    * **Level of Competition:** For each school attended, describe the type of competition faced and note any **notable opponents or highly-recruited teammates** with inline citations.

5.  **Intangibles & Projection**
    * Search local news outlets for human-interest stories, player interviews, or scholar-athlete awards. The player's X/Twitter feed is also a primary source. Look for recruiting analyst quotes and scouting reports.
    * **Character & Leadership:** Synthesize information from news articles or interviews that speaks to the player's character, work ethic, or leadership qualities with inline citations.
    * **Academic Profile:**
        * Search local news for "scholar-athlete" awards, school honor rolls
        * **Individual Standing:** Search for any **publicly available** GPA, academic awards (e.g., Honor Roll, Scholar-Athlete), or mentions of AP/honors courses with inline citations.
    * **Scout Projection:** Search for analyst projections on college readiness, development timeline, ceiling/floor analysis with inline citations.
    * **Player Comparisons:** Look for pro/college player comparisons from recruiting analysts. Search for phrases like "reminds of", "similar to", "plays like" with inline citations. Include why the comparison fits.
    * **Media Coverage:** Mention key insights from local news or beat writer articles not already covered with inline citations.

**OUTPUT FORMAT:**

* Create analysis items for each major section above (Player Identity, Recruiting Profile, Physical & Athletic Profile, On-Field Performance, Intangibles & Projection)
* Within each analysis item's content, use clear bullet points to present the factual information
* Add inline markdown citations in parentheses for EVERY factual claim: ([Source](url), [Source2](url2))
* Also populate the player fields (name, physicals dict, socials dict)
* Also populate the tags list with sport, school, team, position
* Also populate the stats list with key measurables (e.g., "Height: 6'2\"", "40 Yard: 4.5s", "PPG: 20.1")
* Also populate the citations list with all URLs used
* Leave any sections blank if there is no reliable data
'''

agent = Agent(
    name="generate_scout_report_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=2048,  # Increased for complex research
        )
    ),
    output_schema=ScoutReport,
    tools=[
        AgentTool(agent=search_agent)
    ],
)
