import json
import requests
import re
from ddgs import DDGS
from utils.logger import logger

def _search_hudl_api(player_name: str) -> list:
    api_url = 'https://www.hudl.com/api/v3/community-search/feed-users/search'
    payload = {
        'count': 20,
        'query': player_name,
        'skip': 0
    }
    
    response = requests.post(api_url, json=payload, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    results = data.get('results', [])
    
    hudl_urls = []
    seen_profile_ids = set()
    
    for result in results:
        feed_user_id = result.get('feedUserId', {})
        profile_id = feed_user_id.get('relatedId')
        result_name = result.get('name', '')
        
        if profile_id and profile_id not in seen_profile_ids:
            seen_profile_ids.add(profile_id)
            
            name_slug = result_name.replace(' ', '-')
            full_url = f"https://www.hudl.com/profile/{profile_id}/{name_slug}"
            hudl_urls.append(full_url)
            
            base_url = f"https://www.hudl.com/profile/{profile_id}"
            hudl_urls.append(base_url)
    
    return hudl_urls

def _search_hudl_web(player_name: str) -> list:
    search_query = f'site:hudl.com/profile {player_name}'
    
    hudl_urls = []
    seen_profile_ids = set()
    
    with DDGS() as ddgs:
        results = ddgs.text(search_query, max_results=20)
        
        for result in results:
            url = result.get('href') or result.get('link', '')
            
            if url and 'hudl.com/profile/' in url:
                if not url.startswith('http'):
                    url = 'https://' + url
                
                clean_url = url.split('?')[0].split('#')[0]
                
                profile_match = re.search(r'/profile/(\d+)', clean_url)
                if profile_match:
                    profile_id = profile_match.group(1)
                    
                    if profile_id not in seen_profile_ids:
                        seen_profile_ids.add(profile_id)
                        hudl_urls.append(clean_url)
                        
                        base_url = f"https://www.hudl.com/profile/{profile_id}"
                        if base_url != clean_url:
                            hudl_urls.append(base_url)
                        
                        if len(seen_profile_ids) >= 10:
                            break
    
    return hudl_urls

def search_hudl_player(player_name: str) -> str:
    try:
        # Try Hudl API first
        try:
            hudl_urls = _search_hudl_api(player_name)
            if hudl_urls:
                return json.dumps({
                    "status": "success",
                    "message": f"Found {len(hudl_urls) // 2} Hudl profile(s) for {player_name}",
                    "urls": hudl_urls
                })
        except Exception as api_error:
            logger.warning(f"Hudl API search failed for {player_name}: {api_error}. Falling back to web search.")
            
            # Fallback to web search
            hudl_urls = _search_hudl_web(player_name)
            if hudl_urls:
                return json.dumps({
                    "status": "success",
                    "message": f"Found {len(hudl_urls) // 2} Hudl profile(s) for {player_name} (via web search)",
                    "urls": hudl_urls
                })
        
        return json.dumps({
            "status": "not_found",
            "message": f"No Hudl profiles found for {player_name}",
            "urls": []
        })

    except Exception as e:
        logger.exception(f"Error searching Hudl for player: {player_name}")
        return json.dumps({
            "status": "error",
            "message": f"Error searching Hudl: {str(e)}",
            "urls": []
        })