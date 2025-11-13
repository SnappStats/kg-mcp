"""
Flexible Scout Report Schema - Organized for coaching staff review
Each section supports markdown with bullets, numbered lists, etc.
"""

from google.genai import types

FLEXIBLE_SCOUT_REPORT_FUNCTION = types.FunctionDeclaration(
    name="submit_scout_report",
    description="Submit the completed scout report with comprehensive player analysis",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "position": {"type": "string"},
                    "school": {"type": "string"},
                    "grad_year": {"type": "string"},
                    "physicals": {
                        "type": "object",
                        "description": "Height, weight, wingspan, etc as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    },
                    "socials": {
                        "type": "object",
                        "description": "Social media handles",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["name", "position", "school", "grad_year"]
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Searchable tags (sport, position, location, rankings)"
            },
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {"type": "string"},
                        "content": {"type": "string", "description": "Markdown content with bullets, citations"}
                    },
                    "required": ["title", "content"]
                },
                "description": "Report sections in order"
            },
            "stats": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key statistics with time periods"
            }
        },
        "required": ["player", "tags", "sections", "stats"]
    }
)

FLEXIBLE_RESEARCH_PROMPT = '''
**CONTEXT: Scout report for COACHING STAFF making recruiting decisions.**

**YOUR TASK:**
Use web_search_direct to research the player thoroughly, then submit a comprehensive scout report.

**INTELLIGENT SEARCH STRATEGY:**
Execute 15-25 highly specific searches. Start broad, then get specific based on what you find:

**Phase 1 - Identify & Verify (3-4 searches):**
- "[Full Name]" AND (football OR basketball OR baseball) AND "high school"
- "[Full Name]" AND "[School Name if found]" AND stats
- site:247sports.com "[Full Name]"
- site:maxpreps.com "[Full Name]"

**Phase 2 - Deep Recruiting Intel (5-6 searches):**
- site:247sports.com/Player "[Full Name]" recruiting profile
- site:on3.com "[Full Name]" scouting report analysis
- "[Full Name]" "official visit" OR "unofficial visit" OR "OV"
- "[Full Name]" "committed" OR "decommit" OR "flip" recruiting
- "[Full Name]" "crystal ball" OR "RPM" prediction
- "[Full Name]" NIL valuation OR "name image likeness"

**Phase 3 - Performance & Stats (4-5 searches):**
- "[Full Name]" "[School Name]" "vs" box score recent
- "[Full Name]" intitle:"game recap" OR intitle:"game story" 2024
- site:hudl.com "[Full Name]" highlights
- "[Full Name]" "state championship" OR "playoffs" performance
- "[Full Name]" "career high" OR "school record"

**Phase 4 - Physical & Athletic Testing (3-4 searches):**
- "[Full Name]" "40 time" OR "forty yard" OR "40-yard dash"
- "[Full Name]" combine OR "sparq rating" OR "verified testing"
- "[Full Name]" "wingspan" OR "hand size" OR "arm length" measurements
- site:athletic.net "[Full Name]" track field results

**Phase 5 - Character & Background (3-4 searches):**
- "[Full Name]" "team captain" OR "leadership award"
- "[Full Name]" "GPA" OR "academic" OR "honor roll" OR "valedictorian"
- "[Full Name]" parents OR father OR mother "played college"
- "[Full Name]" twitter.com OR x.com (to find social media)
- "[Full Name]" "arrested" OR "suspended" OR "violation" OR "incident"

**Phase 6 - Expert Analysis (3-4 searches):**
- "[Full Name]" "film study" OR "tape breakdown" analyst
- "[Full Name]" "reminds me of" OR "comparison" OR "pro comp"
- "[Full Name]" "ceiling" OR "floor" OR "projection" draft
- "[Full Name]" coach quote OR "what coaches say"

**CRITICAL CITATION REQUIREMENT:**
**YOU MUST CITE EVERY SINGLE FACT, STAT, QUOTE, AND CLAIM WITH INLINE CITATIONS**
- Use source names in brackets: [247Sports], [On3], [ESPN], [MaxPreps], [Rivals], [Gatorade], etc.
- NEVER write a fact without a citation. If you can't cite it from your searches, don't include it.
- We will automatically extract full URLs from your searches and convert your source names to numbered citations
- Just focus on citing EVERYTHING with the source name where you found it

**REQUIRED SECTIONS (in this order):**

1. **Recruiting Profile & Rankings**
   - Star ratings from all services [cite each]
   - National/position/state rankings
   - Composite score
   - Scholarship offers by tier (Elite/P5/G5/FCS)
   - Official & unofficial visits
   - Top schools, Crystal Ball predictions
   - NIL valuation

2. **Physical & Athletic Profile**
   - All verified measurements with source/date
   - Combine/camp testing results
   - 40-yard, vertical, bench press, etc
   - Elite camp performances
   - Multi-sport background

3. **Recent Performance (Last 3 Games)**
   - Game-by-game stats
   - Opponents faced
   - Key plays/moments

4. **Season Performance (Current/Most Recent)**
   - Season totals and averages
   - Conference stats
   - Best games
   - Consistency/trends

5. **Career Statistics**
   - Year-by-year breakdown (Freshman/Sophomore/Junior/Senior)
   - Progression over time
   - Career highs
   - Records set

6. **Key Games & Moments**
   - Performances vs ranked opponents
   - Playoff/championship games
   - Clutch performances
   - Head-to-head vs other top recruits

7. **Strengths**
   - Technical skills with examples
   - Physical advantages
   - Mental attributes
   - What separates them

8. **Areas for Development**
   - Technical weaknesses per scouts
   - Physical limitations
   - Areas needing college coaching
   - Consistency issues

9. **Awards & Recognition**
   - All-State/All-American
   - Conference honors by year
   - National awards
   - Camp MVPs

10. **Team Context & Competition Level**
    - School's football tradition
    - Conference strength
    - Notable teammates
    - Quality of opposition faced

11. **Character & Leadership**
    - Captain/leadership roles
    - Work ethic examples
    - Community involvement
    - Teammate testimonials

12. **Academic Profile**
    - GPA if available
    - Honor roll/AP courses
    - Academic awards
    - School reputation

13. **Coach & Scout Quotes**
    - Direct quotes with attribution
    - Scouting reports
    - What coaches say
    - Media coverage

14. **Player Comparisons**
    - NFL player comparisons from analysts
    - Style of play similarities
    - Ceiling/floor projections

15. **Injury History & Durability**
    - Past injuries if any
    - Games missed
    - Recovery timeline
    - Current health status

16. **Projection & Outlook**
    - College readiness (Day 1 starter vs developmental)
    - Position versatility
    - NFL draft potential
    - Development timeline

17. **Family & Background**
    - Athletic family members
    - Coaching connections
    - Geographic ties to schools
    - Early enrollment plans

**FORMAT EACH SECTION:**
Use markdown with bullets for easy scanning:
- Key fact one [Source]
- Key fact two [Source]

**stats array:** Include 8-10 most important statistics

Remember: Coaches need accurate, well-sourced information for million-dollar decisions.
'''