import os
import requests
import json
import re
from google import genai
from google.genai import types
from utils.logger import logger, _log_fields
from .prompts.research_prompt import RESEARCH_PROMPT
from .tools.search_hudl_player import search_hudl_player as search_hudl_player_impl

@logger.catch(reraise=True)
def research_player(query: str, athlete_name: str) -> dict:
    """
    Research a player using Gemini with grounded search.

    Returns:
        dict with either:
        - {"status": "success", "notes": str, "sources": [str]} - Research complete, ready to format
        - {"status": "feedback", "message": str} - Needs clarification (AMBIGUOUS, NOT FOUND, etc.)
    """
    client = genai.Client(
        vertexai=True,
        project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        location=os.environ.get('GOOGLE_CLOUD_LOCATION')
    )

    hudl_search_result = None
    try:
        hudl_result_json = search_hudl_player_impl(athlete_name)
        hudl_search_result = json.loads(hudl_result_json)
        logger.info("hudl pre-search completed", *_log_fields(query=query, result=hudl_search_result))
    except Exception as e:
        logger.warning(f"hudl pre-search failed for '{query}': {e}")

    prompt_with_context = f"{RESEARCH_PROMPT}\n\n**PLAYER TO RESEARCH:** {query}"
    
    if hudl_search_result and hudl_search_result.get('status') == 'success':
        urls = hudl_search_result.get('urls', [])
        if urls:
            prompt_with_context += f"\n\n**HUDL SEARCH RESULTS:**\nFound {len(urls)} Hudl profile(s). Candidate URLs:\n"
            seen_ids = set()
            for url in urls:
                profile_match = re.search(r'/profile/(\d+)', url)
                if profile_match:
                    profile_id = profile_match.group(1)
                    if profile_id not in seen_ids:
                        seen_ids.add(profile_id)
                        prompt_with_context += f"- {url}\n"
            prompt_with_context += "\nVerify which profile matches the player by checking the profile content (name, school, position, graduation year)."

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt_with_context,
            config=types.GenerateContentConfig(
                temperature=0.1,
                tools=[
                    types.Tool(google_search=types.GoogleSearch()),
                    types.Tool(url_context=types.UrlContext())
                ]
            )
        )
    except Exception as e:
        logger.exception("research agent raised an exception")
        return {
            "status": "feedback",
            "message": f"Error during research: {str(e)}"
        }

    response_text = response.text.strip()

    if response_text.startswith("AMBIGUOUS:") or response_text.startswith("NOT FOUND:"):
        return {
            "status": "feedback",
            "message": response_text
        }

    sources = []

    if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                grounding_chunks = getattr(candidate.grounding_metadata, 'grounding_chunks', None)
                if grounding_chunks and hasattr(grounding_chunks, '__iter__'):
                    for chunk in grounding_chunks:
                        if hasattr(chunk, 'web') and chunk.web:
                            uri = chunk.web.uri
                            # Resolve grounding API redirect URLs to actual URLs
                            if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                                try:
                                    resp = requests.head(uri, allow_redirects=True, timeout=3)
                                    actual_url = resp.url
                                    if actual_url != uri:
                                        uri = actual_url
                                except Exception:
                                    pass  # Keep the original URI if redirect fails
                            sources.append(uri)

    return {
        "status": "success",
        "notes": response_text,
        "sources": sources
    }
