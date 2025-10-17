import asyncio
from floggit import flog
import dotenv
import random
import os

from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.adk.tools import ToolContext
from google.adk.tools.mcp_tool.mcp_toolset import (
        McpToolset, StreamableHTTPConnectionParams)
from google.genai import types

from google.adk.tools import google_search
from google.adk.tools.agent_tool import AgentTool

from subagents.fetch_knowledge_agent.tools import _fetch_knowledge_graph, _get_knowledge_subgraph

dotenv.load_dotenv()
session_service = InMemorySessionService()
APP_NAME = 'kaybee_agent'


@flog
def get_random_entity(tool_context: ToolContext):
    user_id = tool_context._invocation_context.user_id
    g = _fetch_knowledge_graph(graph_id=user_id)
    entity_id = random.choice(list(g['entities'].keys()))
    entity = g['entities'][entity_id]
    nbhd = _get_knowledge_subgraph(
            entity_ids={entity_id}, graph=g, num_hops=1)

    entity_and_nbhd = {
        'entity': entity,
        'entity_neighborhood': nbhd
    }

    print(entity_and_nbhd)

    return entity_and_nbhd


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
            )
        ),
    ],
)

async def call_agent(user_id: str):
    session = await session_service.create_session(
            app_name=APP_NAME, user_id=user_id)

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    user_content = types.Content(role='user', parts=[types.Part(text=f'Expand the knowledge graph for user_id {user_id}.')])
    result = runner.run_async(
            user_id=user_id, session_id=session.id, new_message=user_content)

    # Need this line.... Is there a good replacement?
    async for event in result:
        pass


async def main(knowledge: str, tool_context: ToolContext):
    '''Curates/updates knowledge store with facts contained in the conversation.

    Args:
        knowledge (str): Any potentially new or updated knowledge encountered in the conversation.
    '''
    app_name = tool_context._invocation_context.app_name
    user_id = tool_context._invocation_context.user_id
    session_id = tool_context._invocation_context.session.id

    agent_call = call_agent(
            app_name=app_name, user_id=user_id, session_id=session_id, query=knowledge)
    #asyncio.create_task(agent_call)
    await agent_call

# If running this code as a standalone Python script, you'll need to use asyncio.run() or manage the event loop.
if __name__ == "__main__":
    #asyncio.run(main())
    import time
    while True:
        asyncio.run(call_agent(user_id='116034988107995783513'))
        time.sleep(600)
