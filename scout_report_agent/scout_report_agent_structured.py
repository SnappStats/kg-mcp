"""
Scout Report Agent - Two-Step Approach
Step 1: Research with grounded search
Step 2: Structure output with function calling

Note: Gemini does not allow combining search tools (google_search, url_context)
with function declarations in a single call. We use a two-step approach instead.
"""

import os
import json
import requests
from typing import Dict, Any
from google import genai
from google.genai import types
from utils.logger import logger
from scout_report_function_schema import SCOUT_REPORT_FUNCTION, RESEARCH_PROMPT


@logger.catch(reraise=True)
def generate_scout_report(player_query: str) -> Dict[str, Any]:
    """
    Generate a scout report using a two-step approach:
    1. Research with grounded search
    2. Structure with function calling

    Returns:
        dict with the scout report data or feedback message
    """
    client = genai.Client(
        vertexai=True,
        project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        location=os.environ.get('GOOGLE_CLOUD_LOCATION')
    )

    # ========================================
    # STEP 1: Research with grounded search
    # ========================================
    try:
        research_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=f"{RESEARCH_PROMPT}\n\n**PLAYER TO RESEARCH:** {player_query}",
            config=types.GenerateContentConfig(
                temperature=0.1,
                tools=[
                    types.Tool(google_search=types.GoogleSearch()),
                    types.Tool(url_context=types.UrlContext())
                ]
            )
        )

        research_notes = research_response.text

        # Extract sources from grounding metadata
        sources = []
        if hasattr(research_response, 'candidates') and research_response.candidates:
            candidate = research_response.candidates[0]
            if hasattr(candidate, 'grounding_metadata') and candidate.grounding_metadata:
                grounding_chunks = getattr(candidate.grounding_metadata, 'grounding_chunks', None)
                if grounding_chunks:
                    for chunk in grounding_chunks:
                        if hasattr(chunk, 'web') and chunk.web and chunk.web.uri:
                            uri = chunk.web.uri
                            # Resolve redirect URLs
                            if uri and 'vertexaisearch.cloud.google.com/grounding-api-redirect' in uri:
                                try:
                                    resp = requests.head(uri, allow_redirects=True, timeout=3)
                                    uri = resp.url
                                except Exception:
                                    pass
                            sources.append(uri)

    except Exception as e:
        logger.exception("Research step failed")
        return {"status": "error", "message": f"Research failed: {str(e)}"}

    # ========================================
    # STEP 2: Structure with function calling
    # ========================================
    structuring_prompt = f"""
Based on the following research notes, create a structured scout report.
Call the submit_scout_report function with the organized information.

RESEARCH NOTES:
{research_notes}

SOURCES FOUND:
{json.dumps(sources, indent=2)}

Instructions:
- Extract player identity, physical attributes, and social media handles
- Create smart searchable tags (sport, position, school, location, grad year, etc.)
- Organize analysis items (awards, strengths, weaknesses, quotes)
- List 3-6 key statistics with season/year
- Include all source URLs in citations

If the research indicates multiple players or no player found, still call the function
but put that information in the analysis section with appropriate status.
"""

    try:
        structure_response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=structuring_prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                tools=[types.Tool(function_declarations=[SCOUT_REPORT_FUNCTION])],
                tool_config=types.ToolConfig(
                    function_calling_config=types.FunctionCallingConfig(
                        mode="any",
                        allowed_function_names=["submit_scout_report"]
                    )
                )
            )
        )

        # Extract structured data from function call
        if hasattr(structure_response, 'candidates') and structure_response.candidates:
            candidate = structure_response.candidates[0]
            if hasattr(candidate.content, 'parts'):
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        if part.function_call.name == "submit_scout_report":
                            scout_report = dict(part.function_call.args)

                            # Handle status
                            status = scout_report.get('status', 'error')
                            if status in ['ambiguous', 'not_found']:
                                return {
                                    "status": "feedback",
                                    "message": scout_report.get('feedback_message', f"{status.upper()}")
                                }

                            return {"status": "success", "scout_report": scout_report}

        return {"status": "error", "message": "No structured output generated"}

    except Exception as e:
        logger.exception("Structuring step failed")
        return {"status": "error", "message": f"Structuring failed: {str(e)}"}


# Example usage
if __name__ == "__main__":
    result = generate_scout_report("Bryce Underwood")

    if result['status'] == 'success':
        print("Scout Report Generated Successfully!")
        print("\nStructured Data:")
        print(json.dumps(result['scout_report'], indent=2))
    elif result['status'] == 'feedback':
        print("Feedback Message:")
        print(result['message'])
    else:
        print("Error:")
        print(result['message'])
