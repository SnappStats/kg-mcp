import os
import requests
from floggit import flog

from google.adk.agents import Agent
from google.adk.tools import ToolContext
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools import google_search
from google.adk.tools.mcp_tool.mcp_toolset import (
        McpToolset, StreamableHTTPConnectionParams)
from google.adk.planners import BuiltInPlanner
from google.genai import types


internet_search_agent = Agent(
    model='gemini-2.5-flash',
    name='internet_search_agent',
    description='Retrieves information from the internet.',
    instruction="""You're a specialist in Google Search""",
    tools=[google_search],
)

@flog
def search_knowledge_graph(query: str, tool_context: ToolContext) -> dict:
    """Retrieves information from the knowledge graph."""
    user_id = tool_context._invocation_context.user_id
    url = os.environ['KG_URL'] + '/search'
    return requests.get(url, params={'graph_id': user_id, 'query': query}).json()


PROMPT = """Your task is to provide additional context/knowledge that will help form a well-founded response. Use the `internet_search_agent` tool only if the `search_knowledge_graph` tool returned insufficient context/knowledge.

"""
#Finally, before responding, use the `curate_knowledge` tool to record any relevant knowledge not already found in the knowledge graph.
#"""

agent = Agent(
    name="scout_report_agent",
    model="gemini-2.5-flash",
    description="Retrieves additional context/knowledge in order to form a well-founded response.",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=512,
        )
    ),
    tools=[
        search_knowledge_graph,
        AgentTool(agent=internet_search_agent),
        #McpToolset(
        #    connection_params=StreamableHTTPConnectionParams(
        #        url="https://kg-mcp-785636189485.us-central1.run.app/mcp"
        #    ),
        #    tool_filter=['curate_knowledge'],
        ),
    ],
    instruction=PROMPT,
)
