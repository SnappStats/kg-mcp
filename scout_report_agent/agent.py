from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.adk.tools.agent_tool import AgentTool
from google.genai import types

from google.adk.tools import google_search

from .scout_report_schema import ScoutReport

search_agent = Agent(
    model='gemini-2.5-flash',
    name='search_agent',
    description='Retrieves information from the internet.',
    instruction="""You're a specialist in Google Search""",
    tools=[google_search],
)

PROMPT='''
Use the search tool to generate a well-researched, complete Scout Report for the given player.

Leave any sections blank if there is no reliable data.
'''

agent = Agent(
    name="generate_scout_report_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=512,
        )
    ),
    output_schema=ScoutReport,
    tools=[
        AgentTool(agent=search_agent)
    ],
)
