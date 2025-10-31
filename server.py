import asyncio
import threading
import os
import requests
from dotenv import load_dotenv
from typing import Annotated

from logger import logger

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_headers

from google.adk.runners import Runner
#from google.adk.sessions import InMemorySessionService
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

    #t = threading.Thread(
    #    target=_start_async_loop,
    #    name="BackgroundWorker",
    #    kwargs={'graph_id': graph_id, 'user_id': user_id, 'query': query},
    #    daemon=False
    #)

    asyncio.create_task(
            _curate_knowledge(
                graph_id=graph_id, user_id=user_id, query=query))
    t.start()

    return 'This is being taken care of.'

@mcp.tool(
        name='generate_scout_report',
        description='This tool returns a detailed Scout Report for a given player. It should be called whenever the user solicits a Scout Report, or solicits information likely to be found in a Scout Report.'
)
async def scout_report(
        player_name: Annotated[str, "The name of the player for whom a Scout Report is being requested."]
) -> str:
    graph_id = get_http_headers()['x-graph-id']
    user_id = get_http_headers().get('x-author-id','anonymous')
    
    logger.info(f'processing scout report request for {user_id} and graph {graph_id}')
    
    report = generate_scout_report(graph_id=graph_id, player_name=player_name)

    return report.model_dump_json(indent=2)


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
