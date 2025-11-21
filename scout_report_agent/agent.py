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
        hudl_profile = await extract_hudl_profile_data(scout_report.player.hudl_profile)
        
        player_name = scout_report.player.name
        is_same_player = hudl_profile and hudl_profile.name and all(name_part.lower() in player_name.lower() for name_part in hudl_profile.name.split())
        
        if is_same_player:
            # NOTE: we take the first one since they are sorted at the source, this should be the latest one with most views
            if hudl_profile and hudl_profile.hudl_video_sources and len(hudl_profile.hudl_video_sources) > 0:
                scout_report.player.highlighted_reel = hudl_profile.hudl_video_sources[0].url
            
            if hudl_profile.avatar_url and scout_report.player.avatar_url is None:
                scout_report.player.avatar_url = hudl_profile.avatar_url
        else:
            scout_report.player.hudl_profile = None
            logger.warning(f"player name mismatch: the hudl profile scraped from the provided url '{hudl_profile.name if hudl_profile else 'None'}' does not match expected player '{player_name}'")
        
        

    # Return as dict - frontend expects nested player object
    # Format: {'player': {'name': str, 'physicals': {}, 'socials': {}}, 'tags': [], 'analysis': [], 'stats': []}
    return scout_report.model_dump()
