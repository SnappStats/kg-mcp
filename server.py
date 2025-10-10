import asyncio
import threading
import os
from dotenv import load_dotenv

from fastmcp import FastMCP, Context
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from agent import agent

APP_NAME = 'kg'

session_service = InMemorySessionService()

mcp = FastMCP("knowledge_graph")

# Load environment variables from .env file in root directory
load_dotenv()

async def _curate_knowledge(user_id: str, query: str):
    session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)

    runner = Runner(
        agent=agent,
        app_name=APP_NAME,
        session_service=session_service
    )

    user_content = types.Content(role='user', parts=[types.Part(text=query)])
    qwer = runner.run_async(user_id=user_id, session_id=session.id, new_message=user_content)

    # Need this line.... Is there a good replacement?
    async for event in qwer:
        pass

def _start_async_loop(**kwargs):
    asyncio.run(_curate_knowledge(**kwargs))

@mcp.tool()
async def curate_knowledge(user_id: str, query: str, ctx: Context):
    '''Records any new or updated knowledge.

    user_id (str): The ID of the user.
    query (str): A snippet of text or a document that contains potentially new or updated knowledge.
    '''
    t = threading.Thread(
        target=_start_async_loop,
        name="BackgroundWorker",
        kwargs={'user_id': user_id, 'query': query},
        daemon=False
    )
    t.start()

    return 'This is being taken care of.'
