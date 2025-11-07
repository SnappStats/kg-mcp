"""
Scout Report Agent - Main orchestration function for MCP
"""

from .research_agent import research_player
from .formatting_agent import format_to_schema


def generate_scout_report(player_query: str) -> dict:
    """
    Generate a scout report for a player.

    This is called by the MCP tool from the root agent.

    Returns either:
    - {"type": "scout_report", "data": ScoutReport} - Success, save to GCS
    - {"type": "feedback", "message": str} - Needs clarification, return to root agent

    The MCP should check the type:
    - If "scout_report" → save to GCS, show report card to user
    - If "feedback" → return message to root agent so it can call again with more details
    """
    # Step 1: Research the player with grounded search
    research_result = research_player(player_query)

    # Step 2: If not success, return feedback to root agent
    if research_result["status"] != "success":
        return {
            "type": "feedback",
            "message": research_result.get("message", "Unable to complete research")
        }

    # Step 3: Research succeeded - format to structured schema
    scout_report = format_to_schema(
        research_notes=research_result["notes"],
        sources=research_result["sources"]
    )

    return {
        "type": "scout_report",
        "data": scout_report
    }
