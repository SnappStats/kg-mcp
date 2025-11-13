"""
Scout Report Agent - Single Call with Brightdata
Uses Brightdata web search + function calling in ONE Gemini conversation

Advantage: Both tools are custom function declarations, so they CAN be combined!
"""

import os
import sys
import json
from typing import Dict, Any

# Add parent directory to path for imports
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from dotenv import load_dotenv
load_dotenv(os.path.join(parent_dir, '.env'))

from google import genai
from google.genai import types
from utils.logger import logger
from simple_scout_schema import SIMPLE_SCOUT_REPORT_FUNCTION, RESEARCH_PROMPT as SIMPLE_RESEARCH_PROMPT
from comprehensive_scout_schema import COMPREHENSIVE_SCOUT_REPORT_FUNCTION, COMPREHENSIVE_RESEARCH_PROMPT
from flexible_scout_schema import FLEXIBLE_SCOUT_REPORT_FUNCTION, FLEXIBLE_RESEARCH_PROMPT
from brightdata_tools import WEB_SEARCH_FUNCTION, execute_web_search
from finish_message_parser import parse_finish_message
from extract_citations import extract_urls_from_markdown
from citation_processor import process_inline_citations


# Toggle between schemas (flexible is recommended)
SCHEMA_TYPE = "flexible"  # Options: "simple", "comprehensive", "flexible"

if SCHEMA_TYPE == "flexible":
    RESEARCH_PROMPT = FLEXIBLE_RESEARCH_PROMPT
    SCOUT_REPORT_FUNCTION = FLEXIBLE_SCOUT_REPORT_FUNCTION
elif SCHEMA_TYPE == "comprehensive":
    RESEARCH_PROMPT = COMPREHENSIVE_RESEARCH_PROMPT
    SCOUT_REPORT_FUNCTION = COMPREHENSIVE_SCOUT_REPORT_FUNCTION
else:
    RESEARCH_PROMPT = SIMPLE_RESEARCH_PROMPT
    SCOUT_REPORT_FUNCTION = SIMPLE_SCOUT_REPORT_FUNCTION

RESEARCH_PROMPT_OLD = '''
You are a scout report researcher for coaching staff making recruiting decisions. Quality and credibility are CRITICAL.

**YOUR WORKFLOW:**
1. Use web_search_direct to search for information about the player
2. Make multiple searches to gather comprehensive information:
   - Player identity and basic info (name, school, position, grad year)
   - Recruiting rankings and offers (247Sports, On3, ESPN, Rivals)
   - Physical measurements and athletic testing
   - Statistics and performance
   - Character, academics, and intangibles
3. After gathering all information, call submit_scout_report with structured data

**CRITICAL INSTRUCTIONS:**
* Use web_search_direct multiple times with specific queries
* If you find MULTIPLE possible players → call submit_scout_report with status="ambiguous"
* If you CANNOT find the player → call submit_scout_report with status="not_found"
* If you find the exact player → call submit_scout_report with status="success" and all data

**SEARCH STRATEGY:**
* Start with player name + sport + position
* Search for "Player Name 247Sports" to find recruiting rankings
* Search for "Player Name MaxPreps stats" to find performance
* Search for "Player Name Twitter" or "Player Name Instagram" for social media
* Use specific, targeted queries rather than broad searches

**WHEN CALLING submit_scout_report:**
* Fill in ALL fields that you have information for
* Leave fields as null if no information was found
* For arrays, use empty arrays [] if nothing found
* Include all sources you found in the citations field
'''


@logger.catch(reraise=True)
def generate_scout_report(player_query: str) -> Dict[str, Any]:
    """
    Generate a scout report using Brightdata search + function calling in a single conversation.

    This uses an agentic loop where Gemini can:
    1. Call web_search_direct multiple times to research
    2. Call submit_scout_report when done to structure the data

    Returns:
        dict with the scout report data or feedback message
    """
    client = genai.Client(
        vertexai=True,
        project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        location=os.environ.get('GOOGLE_CLOUD_LOCATION')
    )

    # Provide both tools to Gemini
    tools = [
        types.Tool(function_declarations=[WEB_SEARCH_FUNCTION, SCOUT_REPORT_FUNCTION])
    ]

    # Start the conversation
    messages = [
        f"{RESEARCH_PROMPT}\n\n**PLAYER TO RESEARCH:** {player_query}"
    ]

    max_turns = 20  # Limit conversation turns to prevent infinite loops
    turn_count = 0
    all_search_results = []  # Track all search results for citation extraction

    while turn_count < max_turns:
        turn_count += 1
        logger.info(f"[scout_report] Turn {turn_count}/{max_turns}")

        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=messages,
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    tools=tools
                )
            )

            if not response.candidates:
                return {"status": "error", "message": "No response from model"}

            candidate = response.candidates[0]

            # Check if there are function calls to handle
            function_calls = []
            if hasattr(candidate.content, 'parts') and candidate.content.parts:
                for part in candidate.content.parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        function_calls.append(part.function_call)

            # Check for finish reasons - but DON'T treat malformed function calls as errors
            # Gemini sometimes puts valid data in finish_message even when it says "Malformed"
            if hasattr(candidate, 'finish_message') and candidate.finish_message:
                finish_msg = candidate.finish_message
                logger.info(f"[scout_report] Finish message present: {finish_msg[:200]}...")

                # If it's a "Malformed function call" message, the data might still be parseable
                # We'll continue processing if we have function_calls

            # If no function calls but there's a finish_message with data, try to parse it
            if not function_calls:
                if hasattr(candidate, 'finish_message') and candidate.finish_message:
                    finish_msg = candidate.finish_message

                    # Try to extract the function call from the message
                    # The message format is like: "Malformed function call: print(default_api.submit_scout_report(...data...))"
                    if "submit_scout_report(" in finish_msg:
                        logger.info("[scout_report] Attempting to parse data from finish_message")

                        # Use our parser to extract the data
                        parsed_result = parse_finish_message(finish_msg)

                        if parsed_result and parsed_result.get('status') == 'success':
                            logger.info("[scout_report] Successfully parsed malformed function call!")
                            # Add extracted citations (overwrite any provided)
                            if 'scout_report' in parsed_result:
                                citations = []
                                for search_result in all_search_results:
                                    citations.extend(extract_urls_from_markdown(search_result['result']))
                                parsed_result['scout_report']['citations'] = sorted(list(set(citations)))

                                # Process inline citations to numbered format
                                parsed_result['scout_report'] = process_inline_citations(parsed_result['scout_report'])
                            return parsed_result
                        else:
                            # If parsing failed, save for debugging
                            import tempfile
                            temp_file = os.path.join(tempfile.gettempdir(), "scout_report_finish_message.txt")
                            with open(temp_file, 'w') as f:
                                f.write(finish_msg)
                            logger.warning(f"[scout_report] Failed to parse finish_message, saved to: {temp_file}")
                            return {
                                "status": "error",
                                "message": f"Failed to parse finish_message. Data saved to: {temp_file}"
                            }

                # Check if there's text content
                if hasattr(candidate.content, 'parts') and candidate.content.parts:
                    for part in candidate.content.parts:
                        if hasattr(part, 'text') and part.text:
                            return {"status": "error", "message": f"Unexpected response: {part.text}"}
                return {"status": "error", "message": "No function calls found"}

            # Handle function calls
            function_responses = []
            for fc in function_calls:
                if fc.name == "web_search_direct":
                    # Execute the web search
                    query = fc.args.get('query', '')
                    engine = fc.args.get('engine', 'google')
                    cursor = fc.args.get('cursor')

                    logger.info(f"[web_search] Executing: {query}")
                    result = execute_web_search(query, engine, cursor)

                    # Store search results for citation extraction
                    if 'result' in result:
                        all_search_results.append(result)

                    function_responses.append({
                        "function_call": {
                            "name": "web_search_direct",
                            "args": fc.args
                        },
                        "function_response": {
                            "name": "web_search_direct",
                            "response": result
                        }
                    })

                elif fc.name == "submit_scout_report":
                    # Extract the structured scout report!
                    scout_report = dict(fc.args)

                    status = scout_report.get('status', 'error')
                    if status in ['ambiguous', 'not_found']:
                        return {
                            "status": "feedback",
                            "message": scout_report.get('feedback_message', f"{status.upper()}")
                        }

                    # Add extracted citations from search results (overwrite any provided)
                    citations = []
                    for search_result in all_search_results:
                        citations.extend(extract_urls_from_markdown(search_result['result']))
                    scout_report['citations'] = sorted(list(set(citations)))

                    # Process inline citations to numbered format
                    scout_report = process_inline_citations(scout_report)

                    logger.info(f"[scout_report] Successfully generated report")
                    return {"status": "success", "scout_report": scout_report}

            # Add function responses to conversation and continue
            if function_responses:
                # Gemini expects the conversation to include the function responses
                # We need to append them to the messages list
                messages.append({
                    "role": "model",
                    "parts": [{"function_call": fr["function_call"]} for fr in function_responses]
                })
                messages.append({
                    "role": "user",
                    "parts": [{"function_response": fr["function_response"]} for fr in function_responses]
                })

        except Exception as e:
            logger.exception("[scout_report] Error in conversation turn")
            return {"status": "error", "message": f"Error: {str(e)}"}

    return {"status": "error", "message": f"Exceeded maximum turns ({max_turns})"}


# Example usage
if __name__ == "__main__":
    import time
    start_time = time.time()

    result = generate_scout_report("Bryce Underwood")

    elapsed_time = time.time() - start_time

    if result['status'] == 'success':
        print("Scout Report Generated Successfully!")
        print(f"\n⏱️  Time taken: {elapsed_time:.2f} seconds")
        print("\nStructured Data:")
        print(json.dumps(result['scout_report'], indent=2))
    elif result['status'] == 'feedback':
        print("Feedback Message:")
        print(result['message'])
        print(f"\n⏱️  Time taken: {elapsed_time:.2f} seconds")
    else:
        print("Error:")
        print(result['message'])
        print(f"\n⏱️  Time taken: {elapsed_time:.2f} seconds")
