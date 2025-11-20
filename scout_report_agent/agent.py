from .research_agent import research_player
from .formatting_agent import format_to_schema
from utils.logger import logger
from .extract_hudl_data import extract_hudl_profile_data

@logger.catch(reraise=True)
async def generate_scout_report(player_query: str) -> dict:
    """
    Generate a scout report for a player.

    Args:
        player_query: Player name and disambiguating context

    Returns either:
    - Scout report dict with 'player' key (success) - save to GCS
    - {"text": str} - Needs clarification, return to root agent
    """
    research_result = research_player(player_query)

    if research_result["status"] != "success":
        return {
            "text": research_result.get("message", "Unable to complete research")
        }

    scout_report = format_to_schema(
        research_notes=research_result["notes"],
        sources=research_result["sources"]
    )
    
    if scout_report.player.hudl_profile is not None:
        hudl_profile = await extract_hudl_profile_data(scout_report.player.hudl_profile, scout_report.player.name)
        
        # NOTE: we take the first one since they are sorted at the source, this should be the latest one with most views
        if hudl_profile and hudl_profile.hudl_video_sources and len(hudl_profile.hudl_video_sources) > 0:
            scout_report.player.highlighted_reel = hudl_profile.hudl_video_sources[0].url

    # Return as dict - frontend expects nested player object
    # Format: {'player': {'name': str, 'physicals': {}, 'socials': {}}, 'tags': [], 'analysis': [], 'stats': []}
    return scout_report.model_dump()
