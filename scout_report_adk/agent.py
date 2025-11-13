"""
ADK Agent for Football Recruiting Scout Reports
"""

from google.adk.agents import Agent
from google.genai import types
from .parallel_scout_v5 import generate_scout_report_parallel
import json


def generate_scout_report_tool(player_query: str) -> str:
    """
    Generate a comprehensive football recruiting scout report.

    Uses a multi-agent system that:
    1. Identifies the player (baseline research)
    2. Runs parallel specialized research (physical, performance, recruiting, background, intangibles)
    3. Formats results with inline citations

    Args:
        player_query: Player name and disambiguating context
                     Examples: "Bryce Johnson, IOL Redding High School"
                               "John Smith, QB, class of 2026, Texas"

    Returns:
        str: JSON scout report or clarification request if player is ambiguous
    """
    result = generate_scout_report_parallel(player_query)

    # If result contains 'text' key, it's a clarification request or error
    if isinstance(result, dict) and 'text' in result and 'player' not in result:
        return result['text']

    # Otherwise return formatted JSON
    return json.dumps(result, indent=2)


root_agent = Agent(
    model='gemini-2.5-flash',
    name='scout_report_agent',
    description="Generates comprehensive football recruiting scout reports with citations",
    instruction="""You are a football recruiting scout report assistant powered by a multi-agent research system.

**Your Capabilities:**
- Generate comprehensive scout reports for high school football recruits
- Research player physical profiles, performance stats, recruiting rankings, background, and intangibles
- Provide inline citations from 40+ sources including 247Sports, On3, Rivals, MaxPreps, local news
- Handle ambiguous player queries by requesting clarification

**How to Help Users:**

1. When a user asks for a scout report, use the `generate_scout_report_tool` with their player query.

2. The tool returns either:
   - A complete JSON scout report with player info, analysis sections, stats, and citations
   - A plain text clarification request if the player identification is ambiguous

3. If you receive a clarification request:
   - Present it clearly to the user
   - Ask for more specific details (graduation year, school, location, position)
   - Once they provide details, call the tool again with the updated query

4. If you receive a complete scout report:
   - Present the key highlights to the user
   - Mention that detailed analysis with citations is available in the full report
   - Offer to show specific sections (physical profile, stats, strengths/weaknesses, etc.)

**Example Interaction:**
User: "Scout report on Bryce Johnson"
Assistant: *calls tool*
Tool: "I found multiple players named Bryce Johnson. Did you mean..."
Assistant: "I found several players with that name. Could you provide more details like the high school, position, or graduation year?"

User: "Bryce Johnson, IOL, Redding High School"
Assistant: *calls tool*
Tool: *returns full scout report JSON*
Assistant: "I've generated a comprehensive scout report for Bryce Johnson (IOL, Redding High School, Class of 2026). Here are the key highlights..."

**Important:**
- Always use the tool to generate reports - don't make up player information
- Be concise when presenting reports - users can ask for more details
- If the tool returns JSON, parse and present it in a user-friendly format
""",
    tools=[generate_scout_report_tool],
    generate_content_config=types.GenerateContentConfig(temperature=0.2),
)
