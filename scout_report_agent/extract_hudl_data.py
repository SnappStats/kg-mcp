import re
from utils.logger import logger, _log_fields
from sources.hudl.scrape_hudl_profile_data import scrape_hudl_profile_data
from sources.hudl.hudl_types import HudlPlayerData

async def extract_hudl_profile_data(profile_url: str, player_name: str) -> HudlPlayerData | None:
  try:
    logger.info('received request to scrape hudl profile', **_log_fields(url=profile_url))
    
    if not re.match(r'https://www\.hudl\.com/profile/\d+(?:/[\w-]+)?$', profile_url):
      logger.error('invalid hudl profile URL format', **_log_fields(profile_url=profile_url))
      return None

    player_data = await scrape_hudl_profile_data(profile_url)
    
    logger.info("finished scraping hudl profile data", **_log_fields(data=player_data))
    
    is_same_player = player_data and player_data.name and all(name_part.lower() in player_name.lower() for name_part in player_data.name.split())
    
    if not is_same_player:
      raise Exception(f"player name mismatch: the hudl profile scraped from the provided url '{player_data.name if player_data else 'None'}' does not match expected player '{player_name}'")
    
    return player_data
  except Exception as error:
    logger.exception("failed to scrape player data from hudl profile", **_log_fields(profile_url=profile_url))
    
    return None