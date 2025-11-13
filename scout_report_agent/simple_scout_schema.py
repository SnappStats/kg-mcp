"""
Simple Scout Report Function Schema - Using the original simpler design
"""

from google.genai import types

# Much simpler schema based on scout_report_schema.py
SIMPLE_SCOUT_REPORT_FUNCTION = types.FunctionDeclaration(
    name="submit_scout_report",
    description="Submit the completed scout report with all researched information",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The full name of the player being scouted"
                    },
                    "physicals": {
                        "type": "object",
                        "description": "Physical attributes as key-value pairs (e.g., Height: '6ft 4in', Weight: '228lbs')",
                        "additionalProperties": {"type": "string"}
                    },
                    "socials": {
                        "type": "object",
                        "description": "Social media handles as key-value pairs (e.g., Twitter: '@handle', Instagram: '@handle')",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["name"]
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Smart, searchable tags. Examples: sport, position, 'High School: Name', 'City, ST', grad year, 'College: Name (committed)', '5-star (247Sports)', additional sports"
            },
            "analysis": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Category title (e.g., 'Awards', 'Strengths', 'Weaknesses', 'Recruiting Rankings', 'Coach Quotes')"
                        },
                        "content": {
                            "type": "string",
                            "description": "Detailed content in markdown format"
                        }
                    },
                    "required": ["title", "content"]
                },
                "description": "List of analysis items such as awards, rankings, strengths, weaknesses, quotes"
            },
            "stats": {
                "type": "array",
                "items": {"type": "string"},
                "description": "3-6 key statistics with season/year. Format: '2,888 Passing Yards (2023)', '39 TD, 4 INT (2023)', '50-4 Career Record'"
            }
        },
        "required": ["player", "tags", "analysis", "stats"]
    }
)

RESEARCH_PROMPT = '''
You are a scout report researcher for coaching staff making recruiting decisions. Quality and credibility are CRITICAL.

**YOUR WORKFLOW:**
1. Use web_search_direct to search for information about the player
2. Make multiple targeted searches to gather comprehensive information
3. After gathering all information, call submit_scout_report with structured data

**SEARCH STRATEGY:**
* Start with player name + sport + position
* Search for recruiting rankings: "Player Name 247Sports", "Player Name On3", "Player Name ESPN", "Player Name Rivals"
* Search for stats: "Player Name MaxPreps stats", "Player Name high school stats"
* Search for physical attributes and testing results
* Search for character and academics
* Search for social media handles

**CRITICAL CITATION REQUIREMENT:**
**YOU MUST CITE EVERY SINGLE FACT, STAT, QUOTE, AND CLAIM WITH INLINE CITATIONS**
- Use source names in brackets: [247Sports], [On3], [ESPN], [MaxPreps], [Rivals], [Gatorade], etc.
- Place citations immediately after the fact or quote they support
- Example: "He is ranked as the #1 QB prospect [247Sports, On3] with a perfect 100 rating [On3]"
- Example: "Posted 3,329 passing yards and 41 TDs in 2023 [MaxPreps]"
- Example: "Coach Moore said 'He's a generational talent' [ESPN]"
- We will automatically extract full URLs from your searches and convert your source names to numbered citations
- NEVER write a fact without a citation. If you can't cite it from your searches, don't include it.

**WHEN CALLING submit_scout_report:**
* player.name: Full name
* player.physicals: Dict like {"Height": "6ft 4in", "Weight": "228lbs", "Wingspan": "4ft 11in"}
* player.socials: Dict like {"Twitter": "@handle", "Instagram": "@handle"}
* tags: Array of smart tags like ["Football", "Quarterback", "High School: Belleville", "Belleville, MI", "Class of 2025", "College: Michigan (committed)", "5-star (247Sports)"]
* analysis: Array of {title, content} items WITH INLINE CITATIONS:
  - "Recruiting Rankings": "No. 1 overall recruit [247Sports, On3] and consensus 5-star [247Sports, On3, ESPN, Rivals]..."
  - "Awards": "Gatorade Michigan Player of the Year (2023) [Gatorade.com]..."
  - "Strengths": "Elite arm talent [247Sports scouting report] and excellent accuracy [ESPN analysis]..."
  - "Weaknesses": "Needs to improve footwork under pressure [On3 scouting report]..."
  - "Coach Quotes": "Coach Smith said 'He's special' [ESPN interview]..."
* stats: Array like ["2,888 Passing Yards (2023)", "39 TD, 4 INT (2023)", "50-4 Career Record"]
'''
