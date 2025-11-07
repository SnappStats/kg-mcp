import asyncio
import datetime as dt
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
from scout_report_agent.agent import agent as scout_report_agent
from scout_report_agent.scout_report_service import fetch_scout_report, store_scout_report

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

knowledge_curation_agent_runner = Runner(
    agent=knowledge_curation_agent,
    app_name=AGENT_ENGINE_ID,
    session_service=session_service
)

scout_report_agent_runner = Runner(
    agent=scout_report_agent,
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
    qwer = knowledge_curation_agent_runner.run_async(
            user_id=user_id, session_id=session.id, new_message=user_content)

    # Need this line.... Is there a good replacement?
    async for event in qwer:
        pass


@mcp.tool(
        name='curate_knowledge',
        description='This tool records knowledge in the knowledge base. It should be called whenever potentially new or updated relevant knowledge (e.g. entities, their properties, and their inter-relationships) is encountered. This can also include removing outdated or incorrect knowledge.'
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


async def _fetch_scout_report(graph_id: str, user_id: str, query: str):
    session = await session_service.create_session(
            app_name=AGENT_ENGINE_ID,
            user_id=user_id,
            state={'graph_id': graph_id})

    user_content = types.Content(role='user', parts=[types.Part(text=query)])
    qwer = scout_report_agent_runner.run_async(
            user_id=user_id, session_id=session.id, new_message=user_content)

    async for event in qwer:
        if content := event.content:
            if parts := content.parts:
                if function_response := parts[0].function_response:
                    if function_response.name == 'set_model_response':
                        if 'player' in (scout_report := function_response.response):
                            utc_now = dt.datetime.now(dt.UTC)\
                                    .isoformat(timespec='seconds')
                            scout_report.update({'report_at': utc_now})
                            scout_report_id = store_scout_report(scout_report)

                            return scout_report
        if event.is_final_response():
            return {'text': event.content.parts[0].text}


@mcp.tool(
        name='get_scout_report',
        description='This tool fetches a Scout Report for a player, given their name and sufficient disambiguating context.'
)
async def scout_report(
        player_context: Annotated[str, "Player name and disambiguating context."]
) -> str:
    graph_id = get_http_headers()['x-graph-id']
    user_id = get_http_headers().get('x-author-id','anonymous')

    result = await _fetch_scout_report(
            graph_id=graph_id, user_id=user_id, query=player_context)

    if 'player' in result:
        message = f"""{result['player']} has property "Scout Report ID" with value "{result['id']}"."""
        asyncio.create_task(
                _curate_knowledge(
                    graph_id=graph_id, user_id=user_id, query=message))

    return json.dumps(result)


@mcp.tool(
        name='fetch_scout_report_by_id',
        description="This tool returns a player's Scout Report given its Scout Report ID."
)
async def fetch_scout_report_by_id(
        scout_report_id: Annotated[str, "The ID of a Scout Report."]
) -> dict:
    graph_id = get_http_headers()['x-graph-id']

    return fetch_scout_report(scout_report_id)


@mcp.tool(
        name='search_knowledge_graph',
        description='This tool returns entities (e.g. players, teams, schools), their properties (e.g. Entity ID, Scout Report IDs, awards, personal info), and their inter-relationships, coming from the dynamic Knowledge Graph.'
)
async def search_knowledge_graph(
        query: Annotated[str, "A plain-text search query to find relevant knowledge in the knowledge graph."]
) -> dict:
    graph_id = get_http_headers()['x-graph-id']

    url = os.environ['KG_URL'] + '/search'
    r = requests.get(url, params={'query': query, 'graph_id': graph_id})

    return r.json()
