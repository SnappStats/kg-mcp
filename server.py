import asyncio
import json
import os
import requests
import atexit
from dotenv import load_dotenv
from typing import Annotated

# NOTE: this loads environment variables from .env file BEFORE any other imports
load_dotenv()

from utils.gcp_service_creds import load_service_credentials

# NOTE: do not change this, it is imperative to run this before any of the other imports that rely on the gcp credentials
load_service_credentials()

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import export
from opentelemetry.sdk.trace import TracerProvider

from knowledge_curation_agent.main import main as _curate_knowledge
from scout_report_agent.main import main as _fetch_scout_report
from scout_report_agent.scout_report_service import fetch_scout_report
from sources.hudl.scrape_hudl_profile_data import close_session
from utils.logger import logger, _log_fields, _safe_serialize
from utils.logs_with_request_context import log_with_request_context

provider = TracerProvider()
processor = export.BatchSpanProcessor(
    CloudTraceSpanExporter(project_id=os.environ['GOOGLE_CLOUD_PROJECT'])
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)


mcp = FastMCP("knowledge_graph")

@mcp.tool(
        name='curate_knowledge',
        description='This tool records knowledge in the knowledge base. It should be called whenever potentially new or updated relevant knowledge (e.g. entities, their properties, and their inter-relationships) is encountered. This can also include removing outdated or incorrect knowledge.'
)
@log_with_request_context
async def curate_knowledge(
        query: Annotated[str, "A snippet of text or a document that contains potentially new or updated knowledge."],
) -> str:
    headers = get_http_headers()
    graph_id = headers['x-graph-id']
    user_id = headers.get('x-author-id', 'anonymous')

    logger.info("curate_knowledge called", query=query)

    asyncio.create_task(_curate_knowledge(graph_id=graph_id, user_id=user_id, query=query))

    logger.info("curate_knowledge completed")
    
    return 'This is being taken care of.'


@mcp.tool(
        name='generate_scout_report',
        description=
        'This tool generates a Scout Report for a player from scratch. Provide the player name and sufficient disambiguating context for a sports athlete.' \
        'This creates a NEW report through analysis and should only be used when a stored scout report via other tools is NOT available. ' \
)
@log_with_request_context
async def generate_scout_report(
        athlete_context: Annotated[str, "Details for the athlete, disambiguating context."],
        athlete_name: Annotated[str, "The name of the athlete"]
) -> str:
    headers = get_http_headers()
    graph_id = headers['x-graph-id']
    user_id = headers.get('x-author-id', 'anonymous')

    logger.info("generate_scout_report called", **_log_fields(
        athlete_context=athlete_context,
        athlete_name=athlete_name
    ))

    result = await _fetch_scout_report(
            graph_id=graph_id, user_id=user_id, query=athlete_context, athlete_name=athlete_name)

    logger.info("generate_scout_report completed", **_log_fields(
        result=result
    ))
    
    if result and ('player' in result):
        message = f"""{result['player']} has property "Scout Report ID" with value "{result['id']}"."""
        logger.info('player found in generate scout report result, proceeding to curate knowledge')
        asyncio.create_task(_curate_knowledge(graph_id=graph_id, user_id=user_id, query=message))

    return json.dumps(result)


@mcp.tool(
        name='fetch_scout_report_by_id',
        description="This tool returns a player's Scout Report given its Scout Report ID.  Only use this if you have a Scout Report ID."
)
@log_with_request_context
async def fetch_scout_report_by_id(
        scout_report_id: Annotated[str, "The ID of a Scout Report."]
) -> dict:
    headers = get_http_headers()
    graph_id = headers['x-graph-id']

    logger.info("fetch_scout_report_by_id called", *_log_fields(
        scout_report_id=scout_report_id
    ))

    result = fetch_scout_report(scout_report_id)

    logger.info("fetch_scout_report_by_id completed", *_log_fields(
        result=result
    ))

    return result


@mcp.tool(
        name='search_knowledge_graph',
        description='This tool returns entities (e.g. players, teams, schools), their properties (e.g. Entity ID, Scout Report IDs, awards, personal info), and their inter-relationships, coming from the dynamic Knowledge Graph.'
)
@log_with_request_context
async def search_knowledge_graph(
        query: Annotated[str, "A plain-text search query to find relevant knowledge in the knowledge graph."]
) -> dict:
    headers = get_http_headers()
    graph_id = headers['x-graph-id']

    logger.info("search_knowledge_graph called", query=query)

    url = os.environ['KG_URL'] + '/search'
    r = requests.get(url, params={'query': query, 'graph_id': graph_id})
    result = r.json()

    logger.info("search_knowledge_graph completed", **_log_fields(
        status_code=r.status_code, result=result
    ))

    return result

def cleanup():
    try:
        asyncio.run(close_session())
    except Exception as e:
        logger.error(f"error raised during server cleanup: {e}")

atexit.register(cleanup)
