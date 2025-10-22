import asyncio
import threading
import os
from dotenv import load_dotenv

from fastmcp import FastMCP, Context
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from knowledge_curation_agent import agent as knowledge_curation_agent
from scout_report_agent import agent as scout_report_agent
from subagents.fetch_knowledge_agent.tools import (
        _get_relevant_entities_for_phrases,
        _get_knowledge_subgraph,
        _fetch_knowledge_graph)

APP_NAME = 'kg'

session_service = InMemorySessionService()

mcp = FastMCP("knowledge_graph")

# Load environment variables from .env file in root directory
load_dotenv()

async def _curate_knowledge(user_id: str, query: str):
    session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)

    runner = Runner(
        agent=knowledge_curation_agent,
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
async def curate_knowledge(user_id: str, query: str):
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

#@mcp.tool()
async def generate_scout_report(user_id: str, player_name: str):
    '''Generates a detailed scout report for a given player.

    user_id (str): The ID of the user making the request.
    player_name (str): The name of the player for whom the scout report is to be generated.
    '''
    g = _fetch_knowledge_graph(graph_id=user_id)
    relevant_entity_ids = _get_relevant_entities_for_phrases(
            phrases=[player_name], entities=g['entities'])
    relevant_knowledge = _get_knowledge_subgraph(
            entity_ids=relevant_entity_ids, graph=g, num_hops=2)

    session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
    runner = Runner(
        agent=scout_report_agent,
        app_name=APP_NAME,
        session_service=session_service
    )
    user_content = types.Content(
        role='user',
        parts=[types.Part(text=f'Generate a detailed scout report {player_name} using this data: {relevant_knowledge}.')]
    )
    qwer = runner.run_async(user_id=user_id, session_id=session.id, new_message=user_content)
    report = ""
    async for event in qwer:
        if event.content:
            report += event.content.parts[0].text
    return report
