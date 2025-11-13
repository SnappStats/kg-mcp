"""
Brightdata Tools for Python/Gemini
Provides web search via Brightdata SERP API
"""

import os
import sys
import requests
from google.genai import types
from urllib.parse import quote

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from utils.logger import logger


def search_url(engine: str, query: str, cursor: str = None) -> str:
    """Generate search URL for different engines"""
    encoded_query = quote(query)

    if engine == 'bing':
        return f"https://www.bing.com{cursor}" if cursor else f"https://www.bing.com/search?q={encoded_query}"
    elif engine == 'yandex':
        return f"https://yandex.com{cursor}" if cursor else f"https://yandex.com/search/?text={encoded_query}"
    else:  # google (default)
        return f"https://www.google.com/search?start={cursor}&q={encoded_query}" if cursor else f"https://www.google.com/search?q={encoded_query}"


# Define the web search function declaration
WEB_SEARCH_FUNCTION = types.FunctionDeclaration(
    name="web_search_direct",
    description="Search the web for information. Be specific and include relevant keywords, dates, names, etc. Returns markdown with titles, links, and snippets.",
    parameters={
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search query to execute. Be specific and include relevant keywords, dates, names, etc."
            },
            "engine": {
                "type": "string",
                "description": "Search engine: google (default), bing, or yandex.",
                "enum": ["google", "bing", "yandex"]
            },
            "cursor": {
                "type": "string",
                "description": "Pagination cursor for next page of results"
            }
        },
        "required": ["query"]
    }
)


def execute_web_search(query: str, engine: str = "google", cursor: str = None) -> dict:
    """
    Execute a web search using Brightdata SERP API

    Returns:
        dict with 'result' key containing markdown results, or 'error' key if failed
    """
    BRIGHTDATA_API_URL = 'https://api.brightdata.com/request'

    api_key = os.environ.get('BRIGHTDATA_API_KEY')
    serp_zone = os.environ.get('BRIGHTDATA_SERP_ZONE')

    if not api_key:
        return {"error": "BRIGHTDATA_API_KEY environment variable is not set"}

    if not serp_zone:
        return {"error": "BRIGHTDATA_SERP_ZONE environment variable is not set"}

    if not query or query.strip() == '':
        return {"error": "query parameter is required and cannot be empty"}

    try:
        url = search_url(engine, query, cursor)

        logger.info(f"[web_search_direct] Calling Brightdata API: {url[:100]}...")

        response = requests.post(
            BRIGHTDATA_API_URL,
            json={
                "zone": serp_zone,
                "url": url,
                "format": "raw",
                "data_format": "markdown"
            },
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            timeout=60
        )

        response.raise_for_status()

        result_text = response.text if isinstance(response.text, str) else str(response.content)
        logger.info(f"[web_search_direct] Success! Result size: {len(result_text)}")

        return {"result": result_text}

    except requests.exceptions.HTTPError as e:
        status_code = e.response.status_code if e.response else None

        if status_code == 429:
            error_msg = "Search rate limited by Bright Data API. Try again in a moment."
        elif status_code in [401, 403]:
            error_msg = "Authentication failed. Check BRIGHTDATA_API_KEY."
        else:
            error_msg = f"Search failed with status {status_code}"

        logger.error(f"[web_search_direct] HTTP Error: {error_msg}", exc_info=True)
        return {"error": f"{error_msg}: {str(e)}"}

    except Exception as e:
        logger.exception("[web_search_direct] Unexpected error")
        return {"error": f"Search failed: {str(e)}"}
