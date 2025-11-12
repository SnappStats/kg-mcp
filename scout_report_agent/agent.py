"""
Scout Report Agent - Main orchestration function for MCP
"""

from .research_agent import research_player
from .formatting_agent import format_to_schema


def generate_scout_report(player_query: str) -> dict:
    """
    Generate a scout report for a player.

    Args:
        player_query: Player name and disambiguating context

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
