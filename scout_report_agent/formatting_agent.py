"""
Formatting Agent - Converts research notes to structured ScoutReport with inline citations
"""

import os
from google import genai
from google.genai import types
from .scout_report_schema import ScoutReport
from utils.logger import logger

FORMATTING_PROMPT = '''
You are converting comprehensive research notes into a structured scout report.

**CRITICAL: JSON FORMATTING**
* Output MUST be valid JSON - properly escape all quotes, newlines, and special characters
* Use \\n for line breaks within strings, not literal newlines
* Escape all quotes within strings as \\"
* Do not truncate or cut off any JSON fields - complete all strings properly

**CRITICAL: INLINE CITATION FORMAT**
* Convert [1] [2] style citations to inline markdown format: ([Source Name](url))
* When multiple sources support one fact, group them: ([ESPN](url1), [247Sports](url2))
* Every factual claim must have inline citations
* Strip UTM parameters from URLs

**STATS FORMATTING:**
* Create 3-6 key statistics as complete, self-explanatory statements with season/year
* Format: "3,245 Passing Yards (2024/25)", "42 TD, 4 INT (2024/25)", "68.2% Completion (2024/25)"
* PRIORITIZE latest performance stats over athletic measurables

**OUTPUT STRUCTURE:**
* Create analysis items for each major section (Player Identity, Recruiting Profile, Physical Profile, On-Field Performance, Intangibles)
* Within each analysis item's content, use clear bullet points with inline citations
* Populate player fields (name, physicals dict, socials dict)
* Populate tags with smart, searchable information based on what's important for THIS player:
  - Sport, position, high school (prefix with "High School:"), location (City, ST format or City, Country for international)
  - Grad year, college (prefix with "College:", add "(committed)" if not enrolled yet)
  - Star rating with source in parentheses if applicable
  - Additional sports if multi-sport athlete
  - Other relevant tags that would be useful for searching/filtering
  Be smart - include what matters, skip what doesn't. More or fewer tags as makes sense.
* Populate stats list with 3-6 key performance stats with seasons
* Populate citations list with all URLs used

Convert the research notes below into a structured scout report.
'''


@logger.catch(reraise=True)
def format_to_schema(research_notes: str, sources: list[str]) -> ScoutReport:
    """
    Convert research notes to structured ScoutReport using Gemini.

    Args:
        research_notes: Raw research notes with [1][2] style citations
        sources: List of source URLs

    Returns:
        ScoutReport pydantic model
    """
    client = genai.Client(
        vertexai=True,
        project=os.environ.get('GOOGLE_CLOUD_PROJECT'),
        location=os.environ.get('GOOGLE_CLOUD_LOCATION')
    )

    # Create sources reference for the prompt
    sources_text = "\n".join([f"[{i+1}] {url}" for i, url in enumerate(sources)])

    prompt = f"""{FORMATTING_PROMPT}

**SOURCES:**
{sources_text}

**RESEARCH NOTES:**
{research_notes}
"""

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    temperature=0.1 if attempt == 0 else 0.0,  # Lower temp on retries
                    response_mime_type='application/json',
                    response_schema=ScoutReport
                )
            )
            
            # Parse the JSON response into ScoutReport
            import json

            def stringify_all(obj):
                """Recursively convert all values to strings, except None"""
                if obj is None:
                    return None
                elif isinstance(obj, dict):
                    return {k: stringify_all(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [stringify_all(item) for item in obj]
                else:
                    return str(obj)

            data = json.loads(response.text)
            data = stringify_all(data)

            return ScoutReport.model_validate(data)
            
        except json.JSONDecodeError as e:
            logger.error(
                f"JSON parsing failed on attempt {attempt + 1}/{max_retries}",
                error=str(e),
                response_preview=response.text[:500] if 'response' in locals() else None
            )
            if attempt == max_retries - 1:
                logger.exception(
                    "failed to parse formatting agent output after all retries",
                    response_text=response.text if 'response' in locals() else None
                )
                raise
            # Continue to next retry
            
        except Exception as e:
            logger.exception(f"formatting agent raised an exception on attempt {attempt + 1}")
            if attempt == max_retries - 1:
                raise
            # Continue to next retry
