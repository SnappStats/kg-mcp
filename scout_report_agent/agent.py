"""
Scout Report Agent - Main orchestration function for MCP
"""

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from .research_agent import research_player
from .formatting_agent import format_to_schema


PROMPT = """
You are a scout report generator. When given a player query, you must call the set_model_response tool with the complete scout report data.

Your job is to orchestrate the scout report generation by:
1. Understanding the player query
2. Calling set_model_response with the final scout report structure

The tool will handle all research and formatting internally.
"""


def set_model_response(player_query: str, tool_context: ToolContext) -> dict:
    """
    Generate a scout report for a player.

    Args:
        player_query: Player name and disambiguating context
        tool_context: ADK tool context

    Returns either:
    - Scout report dict with 'player' key (success) - save to GCS
    - {"text": str} - Needs clarification, return to root agent
    """
    # Step 1: Research the player with grounded search
    research_result = research_player(player_query)

    # Step 2: If not success, return feedback to root agent
    if research_result["status"] != "success":
        return {
            "text": research_result.get("message", "Unable to complete research")
        }

    # Step 3: Research succeeded - format to structured schema
    scout_report = format_to_schema(
        research_notes=research_result["notes"],
        sources=research_result["sources"]
    )

    # Return as dict - frontend expects nested player object
    # Format: {'player': {'name': str, 'physicals': {}, 'socials': {}}, 'tags': [], 'analysis': [], 'stats': []}
    return scout_report.model_dump()


# Create the ADK agent
agent = Agent(
    name="scout_report_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    tools=[set_model_response]
)
