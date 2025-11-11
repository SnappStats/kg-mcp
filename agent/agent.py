import asyncio
from floggit import flog
import dotenv
import json
import os
import requests
from typing import Any, Optional, Dict

from google.adk.agents import Agent
from google.adk.agents.callback_context import CallbackContext
from google.adk.planners import BuiltInPlanner
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools.agent_tool import AgentTool
from google.adk.tools.base_tool import BaseTool
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import (
        McpToolset, StreamableHTTPConnectionParams)
from google.genai import types

from google.adk.tools import google_search

dotenv.load_dotenv()
session_service = InMemorySessionService()
APP_NAME = 'scout_agent'
GRAPH_ID = 'cf460c59-6b2e-42d3-b08d-b20ff54deb57'
USER_ID = 'bot'


search_agent = Agent(
    model='gemini-2.5-flash',
    name='search_agent',
    description='Retrieves information from the internet.',
    instruction="""You're a specialist in Google Search. Include inline citations.""",
    tools=[google_search],
)


@flog
def _expand_query(query: str, graph_id: str) -> dict:
    '''
    Args:
        query (str): A query string representing relevant information (e.g. entities) to search for in the knowledge graph.

    Returns:
        dict: The relevant knowledge graph data.
    '''
    url = os.environ['KG_URL'] + '/expand_query'
    r = requests.get(url, params={'query': query, 'graph_id': graph_id})
    return r.json()


def process_user_input(
        callback_context: CallbackContext) -> Optional[types.Content]:
    if text := callback_context.user_content.parts[-1].text:
        if kb_context := _expand_query(query=text, graph_id=GRAPH_ID):
            kb_context_part = types.Part(text=kb_context)
            callback_context.user_content.parts.append(kb_context_part)


def modify_final_response(callback_context: CallbackContext) -> Optional[types.Content]:

    if scout_report := callback_context.state.get('scout_report'):
        return types.Content(
            parts=[types.Part(text=json.dumps(scout_report,indent=1))],
            role='model'
        )

def store_tool_response(
    tool: BaseTool,
    args: Dict[str, Any],
    tool_context: ToolContext,
    tool_response: Dict) -> Optional[Dict]:

    if tool.name == 'fetch_scout_report_by_id':
        tool_context.state['scout_report'] = tool_response.structuredContent
    if tool.name == 'get_scout_report':
        if r := tool_response.structuredContent:
            if 'player' in (scout_report := (r['result'] or {})):
                tool_context.state['scout_report'] = scout_report


PROMPT = '''
You are an enthusiastic sports nut from Alabama, with a thick patois. Your objective is to help sports fans do research on teams and players.

Generally, if the user enters a player name with no discernable intent, assume they want the player's Scout Report.
'''

root_agent = Agent(
    name="knowledge_base_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=512,
        )
    ),
    tools=[
        AgentTool(agent=search_agent),
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.environ['KG_MCP_SERVER'],
                headers={
                    'x-graph-id': GRAPH_ID,
                    'x-author-id': USER_ID
                },
            ),
        ),
    ],
    after_tool_callback=store_tool_response,
    before_agent_callback=process_user_input,
    after_agent_callback=modify_final_response
)
