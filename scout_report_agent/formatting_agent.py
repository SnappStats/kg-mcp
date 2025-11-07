"""
Formatting Agent - Converts research notes to structured ScoutReport with inline citations
"""

import os
from google import genai
from google.genai import types
from .scout_report_schema import ScoutReport

FORMATTING_PROMPT = '''
You are converting comprehensive research notes into a structured scout report.

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

    try:
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                response_mime_type='application/json',
                response_schema=ScoutReport
            )
        )
    except Exception as e:
        print(f"Error calling Gemini API: {e}")
        raise

    # Parse the JSON response into ScoutReport
    try:
        import json

        def stringify_all(obj):
            """Recursively convert all values to strings"""
            if isinstance(obj, dict):
                return {k: stringify_all(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [stringify_all(item) for item in obj]
            else:
                return str(obj)

        data = json.loads(response.text)
        data = stringify_all(data)

        return ScoutReport.model_validate(data)
    except Exception as e:
        # Debug: print the response text to see what went wrong
        print(f"Error parsing JSON response: {e}")
        print(f"Response text length: {len(response.text)}")
        print(f"Response text (first 500 chars): {response.text[:500]}")
        print(f"Response text (last 500 chars): {response.text[-500:]}")
        raise
