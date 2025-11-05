import asyncio
import functools
import json
import logging
import os
import requests
from dotenv import load_dotenv
from typing import Annotated

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_headers

from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.genai import types

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import export
from opentelemetry.sdk.trace import TracerProvider

from knowledge_curation_agent import agent as knowledge_curation_agent
from scout_report_agent.agent import generate_scout_report

# Load environment variables from .env file in root directory
load_dotenv()

provider = TracerProvider()
processor = export.BatchSpanProcessor(
    CloudTraceSpanExporter(project_id=os.environ['GOOGLE_CLOUD_PROJECT'])
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

AGENT_ENGINE_ID = os.environ['SESSION_SERVICE_URI'].split('/')[-1]

session_service = VertexAiSessionService(
    agent_engine_id=AGENT_ENGINE_ID,
)

runner = Runner(
    agent=knowledge_curation_agent,
    app_name=AGENT_ENGINE_ID,
    session_service=session_service
)

mcp = FastMCP("knowledge_graph")

async def _curate_knowledge(graph_id: str, user_id: str, query: str):
    session = await session_service.create_session(
            app_name=AGENT_ENGINE_ID,
            user_id=user_id,
            state={'graph_id': graph_id})

    user_content = types.Content(role='user', parts=[types.Part(text=query)])
    qwer = runner.run_async(user_id=user_id, session_id=session.id, new_message=user_content)

    # Need this line.... Is there a good replacement?
    event_count = 0
    async for event in qwer:
        event_count += 1

def _start_async_loop(**kwargs):
    asyncio.run(_curate_knowledge(**kwargs))

@mcp.tool(
        name='curate_knowledge',
        description='This tool records knowledge in the knowledge base. It should be called whenever potentially new, relevant knowledge (e.g. entities, their properties, and their inter-relationships) is encountered.'
)
async def curate_knowledge(
        query: Annotated[str, "A snippet of text or a document that contains potentially new or updated knowledge."],
) -> str:
    graph_id = get_http_headers()['x-graph-id']
    user_id = get_http_headers().get('x-author-id','anonymous')

    asyncio.create_task(
            _curate_knowledge(
                graph_id=graph_id, user_id=user_id, query=query))

    return 'This is being taken care of.'


@mcp.tool(
        name='generate_scout_report',
        description='This tool returns a detailed Scout Report for a given player. CRITICAL: The player_name parameter MUST contain ALL identifying information you have gathered about the player. Pass comprehensive details including name, position, school, graduation class, rankings, stats, physical profile, commitment status - everything you know. This ensures the scout agent researches the exact right player.'
)
async def scout_report(
        ctx: Context,
        player_name: Annotated[str, "COMPREHENSIVE player identification with ALL details gathered. Include: Full name, position, school (city, state), graduation class, star rating, height/weight, key stats, commitment status, rankings, and any other identifying information. If multiple players with same name were found, include 'NOT:' section listing the other players to avoid confusion. Example single player: 'Justin Lewis - CB, Rancho Cucamonga High School (Rancho Cucamonga, CA), Class of 2026, 4-star (247Sports), 6'0\" 180 lbs, committed to UCLA, #15 CB nationally, 5 INTs senior year'. Example with disambiguation: 'Michael Smith - QB, DeSoto HS (TX), Class 2025, 5-star, 6'4\" 220 lbs, committed Texas, #1 QB. NOT: Michael Smith WR California Class 2026, Michael Smith RB Florida Class 2025'. DO NOT pass minimal information - the more details you provide, the more accurately the scout agent can identify and research the correct player."]
) -> str:
    graph_id = get_http_headers()['x-graph-id']
    user_id = get_http_headers().get('x-author-id','anonymous')

    logging.info(
        'Processing Scout Report request.',
        extra={'json_fields': {'user_id': user_id, 'graph_id': graph_id}})

    loop = asyncio.get_running_loop()
    result = await loop.run_in_executor(
            None, functools.partial(
                generate_scout_report,
                graph_id=graph_id,
                player_name=player_name,
            )
    )

    # Result is now a dict with 'notes' and 'sources'
    return json.dumps(result, indent=2)


@mcp.tool(
        name='search_knowledge_graph',
        description='This tool returns knowledge from the knowledge graph of players, teams, schools, and so on.',
)
async def search_knowledge_graph(
        query: Annotated[str, "A search query to find relevant knowledge in the knowledge graph."]
) -> dict:
    graph_id = get_http_headers()['x-graph-id']

    url = os.environ['KG_URL'] + '/search'
    r = requests.get(url, params={'query': query, 'graph_id': graph_id})

    return r.json()
