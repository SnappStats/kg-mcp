import os
import requests
from floggit import flog

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search
from google.adk.planners import BuiltInPlanner
from google.genai import types

from scout_report_schema import ScoutReport


search_agent = Agent(
    model='gemini-2.5-flash',
    name='search_agent',
    description='Retrieves information from the internet.',
    instruction="""You're a specialist in Google Search""",
    tools=[google_search],
)


@flog
def search_knowledge_graph(player_name: str, tool_context: ToolContext) -> dict:
    """Function to search knowledge graph."""
    user_id = tool_context._invocation_context.user_id
    url = os.environ['KG_URL'] + '/search'
    return requests.get(url, params={'graph_id': user_id, 'query': player_name}).json()


PROMPT = """Generate a Scout Report based on the provided information. First consult the knowledge graph. If there is insufficient information, use the search agent to gather more data. Ensure the report is comprehensive and well-structured (formatted as markdown) according to these notes:

==============================
Scout Report (player profile)

- Player Name
- executive summary/TLDR
- most recent player info
    - height/weight/other physical characteristics
    - GPA
    - Team: High school team, coach, conference /number of players recruited by division and star rating on his team and who
    - athlete attributes/characteristics
- accolades
    - 247sports, espn, prep redzone, maxpreps rankings
    - offers/commits from colleges
    - conference awards
- stats
    - season stats in high school
    - key games and outcomes
- public perception
    - articles/beat writers
- highlight reels (user most likely has to upload themselves?)
- external links
    - hudl
    - social media (twitter/X)
        - Any red flags
    - school

"""

agent = Agent(
    name="scout_report_agent",
    model="gemini-2.5-flash",
    description="Generates a Scout Report for a given player.",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=512,
        )
    ),
    tools=[
        search_knowledge_graph,
        AgentTool(agent=search_agent),
    ],
    #output_schema=ScoutReport,
    instruction=PROMPT,
)
