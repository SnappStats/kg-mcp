import asyncio
from floggit import flog
import dotenv
import os
import requests

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import (
        McpToolset, StreamableHTTPConnectionParams)
from google.genai import types

from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

dotenv.load_dotenv()
session_service = InMemorySessionService()
APP_NAME = 'kaybee_agent'
GRAPH_ID = 'cf460c59-6b2e-42d3-b08d-b20ff54deb57'
USER_ID = 'bot'

@flog
def get_random_entity(tool_context: ToolContext) -> dict:
    user_id = tool_context._invocation_context.user_id
    url = os.environ['KG_READ_URL'] + '/random_neighborhood'
    r = requests.get(url, params={'graph_id': GRAPH_ID})
    return r.json()


search_agent = Agent(
    model='gemini-2.5-flash',
    name='search_agent',
    description='Retrieves information from the internet.',
    instruction="""You're a specialist in Google Search""",
    tools=[google_search],
)

PROMPT = '''
You are helping to expand a knowledge graph about football players, to help scouts and analysts find talent.

Simply perform these three steps:
    1. Use `get_random_entity` to retrieve an existing entity (and its neighborhood) from the knowledge graph.
    2. Use the `search_agent` tool, multiple times if necessary, to do an internet search for more/updated knowledge about the entity and its relationships.
    3. Use `curate_knowledge` tool to record any new or updated knowledge.
'''

agent = Agent(
    name="knowledge_base_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    tools=[
        get_random_entity,
        AgentTool(agent=search_agent),
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.environ['KG_MCP_SERVER']
            ),
            tool_filter=['curate_knowledge'],
        ),
    ],
)

async def call_agent():
    session = await session_service.create_session(
            app_name=APP_NAME, user_id=USER_ID)

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    user_content = types.Content(role='user', parts=[types.Part(text=f'Expand the knowledge graph.')])
    result = runner.run_async(
            user_id=USER_ID, session_id=session.id, new_message=user_content)

    # Need this line.... Is there a good replacement?
    async for event in result:
        print(event)
        #pass


# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
if __name__ == "__main__":
    import time
    while True:
        asyncio.run(call_agent())
        time.sleep(90)
