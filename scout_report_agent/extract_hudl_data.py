import re
from utils.logger import logger, _log_fields
from sources.hudl.scrape_hudl_profile_data import scrape_hudl_profile_data
from sources.hudl.hudl_types import HudlPlayerData

async def extract_hudl_profile_data(profile_url: str) -> HudlPlayerData | None:
  try:
    logger.info('received request to scrape hudl profile', **_log_fields(url=profile_url))
    
    if not re.match(r'https://www\.hudl\.com/profile/\d+(?:/[\w-]+)?$', profile_url):
      logger.error('invalid hudl profile URL format', **_log_fields(profile_url=profile_url))
      return None

    player_data = await scrape_hudl_profile_data(profile_url)
    
    logger.info("finished scraping hudl profile data", **_log_fields(data=player_data))
    
    return player_data
  except Exception as error:
    logger.exception("failed to scrape player data from hudl profile", **_log_fields(profile_url=profile_url))
    
    return None