import asyncio
import threading
import os
import requests
from dotenv import load_dotenv
from typing import Annotated

from instrumentation import instrument_service, dd_tracer
from logger import logger

from fastmcp import FastMCP, Context
from fastmcp.server.dependencies import get_http_headers

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai import types

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import export
from opentelemetry.sdk.trace import TracerProvider

from knowledge_curation_agent import agent as knowledge_curation_agent
from scout_report_agent.agent import generate_scout_report

# Load environment variables from .env file in root directory
load_dotenv()

# DD Tracing
instrument_service()

provider = TracerProvider()
processor = export.BatchSpanProcessor(
    CloudTraceSpanExporter(project_id=os.environ['GOOGLE_CLOUD_PROJECT'])
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

APP_NAME = 'kg'
GRAPH_ID = 'cf460c59-6b2e-42d3-b08d-b20ff54deb57.json'

session_service = InMemorySessionService()

mcp = FastMCP("knowledge_graph")

async def _curate_knowledge(graph_id: str, user_id: str, query: str):
    with dd_tracer.trace("curate_knowledge_service") as span:
        span.set_attribute("graph_id", graph_id)
        span.set_attribute("user_id", user_id)
        span.set_attribute("query", len(query))
        
        session = await session_service.create_session(app_name=APP_NAME, user_id=user_id)
        span.set_attribute("session_id", session.id)

        runner = Runner(
            agent=knowledge_curation_agent,
            app_name=APP_NAME,
            session_service=session_service
        )

        session.state['graph_id'] = graph_id
        session.state['user_id'] = user_id

        user_content = types.Content(role='user', parts=[types.Part(text=query)])
        qwer = runner.run_async(user_id=user_id, session_id=session.id, new_message=user_content)

        # Need this line.... Is there a good replacement?
        event_count = 0
        async for event in qwer:
            event_count += 1
        
        span.set_attribute("events_processed", event_count)
        span.add_event("Knowledge curation completed")

def _start_async_loop(**kwargs):
    asyncio.run(_curate_knowledge(**kwargs))

@mcp.tool(
        name='curate_knowledge',
        description='This tool records knowledge in the knowledge base. It should be called whenever potentially new, relevant knowledge (e.g. entities, their properties, and their inter-relationships) is encountered.'
)
async def curate_knowledge(
        query: Annotated[str, "A snippet of text or a document that contains potentially new or updated knowledge."],
) -> str:
    with dd_tracer.trace("kg_curate_knowledge_tool") as span:
        graph_id = get_http_headers().get('x-graph-id', GRAPH_ID)
        user_id = get_http_headers().get('x-author-id','anonymous')
        
        span.set_attribute("graph_id", graph_id)
        span.set_attribute("user_id", user_id)
        span.set_attribute("query", query)
        span.set_attribute("operation", "curate_knowledge")

        t = threading.Thread(
            target=_start_async_loop,
            name="BackgroundWorker",
            kwargs={'graph_id': graph_id, 'user_id': user_id, 'query': query},
            daemon=False
        )
        t.start()
        
        span.set_attribute("thread_started", True)
        span.add_event("Background thread started for knowledge curation")

        return 'This is being taken care of.'

@mcp.tool(
        name='generate_scout_report',
        description='This tool returns a detailed Scout Report for a given player. It should be called whenever the user solicits a Scout Report, or solicits information likely to be found in a Scout Report.'
)
async def scout_report(
        player_name: Annotated[str, "The name of the player for whom a Scout Report is being requested."]
) -> str:
    with dd_tracer.trace("scout_report") as span:
        graph_id = get_http_headers()['x-graph-id']
        user_id = get_http_headers().get('x-author-id','anonymous')
        
        span.set_attribute("player_name", player_name)
        span.set_attribute("graph_id", graph_id)
        span.set_attribute("user_id", user_id)
        
        # Use fast direct API approach
        report = generate_scout_report(graph_id=graph_id, player_name=player_name)
        
        span.set_attribute("report_generated", True)
        span.add_event("Scout report generated successfully")

        # Format as JSON string for MCP return
        return report.model_dump_json(indent=2)


@mcp.tool(
        name='search_knowledge_graph',
        description='This tool returns knowledge from the knowledge graph of players, teams, schools, and so on.',
)
async def search_knowledge_graph(
        query: Annotated[str, "A search query to find relevant knowledge in the knowledge graph."]
) -> dict:
    with dd_tracer.trace("search_knowledge_graph") as span:
        graph_id = get_http_headers()['x-graph-id']

        span.set_attribute("query", query)
        span.set_attribute("graph_id", graph_id)
        span.set_attribute("kg_url", os.environ['KG_MCP_SERVER_URL'])

        url = os.environ['KG_MCP_SERVER_URL'] + '/search'
        r = requests.get(url, params={'query': query, 'graph_id': graph_id})

        span.set_attribute("http_status_code", r.status_code)
        span.set_attribute("response_size", len(r.content))

        if r.status_code == 200:
            span.add_event("Knowledge graph search successful")
        else:
            span.add_event("Knowledge graph search failed", {"status_code": r.status_code})

        return r.json()
