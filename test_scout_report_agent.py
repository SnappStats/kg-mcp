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

dotenv.load_dotenv()
session_service = InMemorySessionService()
APP_NAME = 'kaybee_agent'


PROMPT = '''Help the user build a scout report about a given player.'''

agent = Agent(
    name="knowledge_base_agent",
    model="gemini-2.5-flash",
    instruction=PROMPT,
    tools=[
        McpToolset(
            connection_params=StreamableHTTPConnectionParams(
                url=os.environ['KG_MCP_SERVER']
            ),
            tool_filter=['generate_scout_report']
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

    user_content = types.Content(role='user', parts=[types.Part(text=f'Joe Theismann. (I am user_id {user_id}).')])
    result = runner.run_async(
            user_id=user_id, session_id=session.id, new_message=user_content)

    # Need this line.... Is there a good replacement?
    async for event in result:
        print(event)
        #pass


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
    asyncio.run(call_agent(user_id='116034988107995783513'))
