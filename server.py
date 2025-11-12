import asyncio
import json
import logging
import os
import requests
from dotenv import load_dotenv
from typing import Annotated

from fastmcp import FastMCP
from fastmcp.server.dependencies import get_http_headers

from opentelemetry import trace
from opentelemetry.exporter.cloud_trace import CloudTraceSpanExporter
from opentelemetry.sdk.trace import export
from opentelemetry.sdk.trace import TracerProvider

from knowledge_curation_agent.main import main as _curate_knowledge
from scout_report_agent.main import main as _fetch_scout_report
from scout_report_agent.scout_report_service import fetch_scout_report
from logging_config import configure_logging, set_trace_id

# Load environment variables from .env file in root directory
load_dotenv()

# Configure logging with trace ID injection
configure_logging()
logger = logging.getLogger(__name__)

def _safe_serialize(obj):
    """Safely serialize any object for logging - handles non-JSON-serializable types"""
    if obj is None or isinstance(obj, (str, int, float, bool)):
        return obj

    try:
        # Try JSON serialization to validate it's safe (also checks for circular refs)
        json.dumps(obj)
        return obj
    except (TypeError, ValueError, OverflowError):
        # If not JSON-serializable (includes circular refs, custom objects), convert to string
        try:
            return str(obj)
        except Exception:
            # If even str() fails, return type info
            return f"<{type(obj).__name__} object (unserializable)>"

def _log_fields(**kwargs):
    """Helper to log fields dynamically - safely serializes all values"""
    return {k: _safe_serialize(v) for k, v in kwargs.items()}

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
async def curate_knowledge(
        query: Annotated[str, "A snippet of text or a document that contains potentially new or updated knowledge."],
) -> str:
    headers = get_http_headers()
    graph_id = headers['x-graph-id']
    user_id = headers.get('x-author-id', 'anonymous')
    trace_id = headers.get('x-trace-id')

    # Set trace ID for logging context
    set_trace_id(trace_id)

    # Log tool input (flexible - pass all fields dynamically)
    logger.info(
        "curate_knowledge called",
        extra={'json_fields': {'tool': 'curate_knowledge', **_log_fields(
            query=query, graph_id=graph_id, user_id=user_id
        )}}
    )

    # Create background task with trace ID propagation
    async def _run_with_trace():
        set_trace_id(trace_id)  # Propagate trace ID to task context
        await _curate_knowledge(graph_id=graph_id, user_id=user_id, query=query)

    asyncio.create_task(_run_with_trace())

    result = 'This is being taken care of.'

    # Log tool output (flexible - pass result directly)
    logger.info(
        "curate_knowledge completed",
        extra={'json_fields': {'tool': 'curate_knowledge', 'result': _safe_serialize(result)}}
    )
    return result


@mcp.tool(
        name='generate_scout_report',
        description=
        'This tool generates a Scout Report for a player from scratch. Provide the player name and sufficient disambiguating context for a sports athlete.' \
        'This creates a NEW report through analysis and should only be used when a stored scout report via other tools is NOT available. ' \
)
async def scout_report(
        player_context: Annotated[str, "Player name and disambiguating context."]
) -> str:
    headers = get_http_headers()
    graph_id = headers['x-graph-id']
    user_id = headers.get('x-author-id', 'anonymous')
    trace_id = headers.get('x-trace-id')

    # Set trace ID for logging context
    set_trace_id(trace_id)

    # Log tool input (flexible - pass all fields dynamically)
    logger.info(
        "generate_scout_report called",
        extra={'json_fields': {'tool': 'generate_scout_report', **_log_fields(
            player_context=player_context, graph_id=graph_id, user_id=user_id
        )}}
    )

    result = await _fetch_scout_report(
            graph_id=graph_id, user_id=user_id, query=player_context)

    # Log tool output (flexible - pass result directly)
    logger.info(
        "generate_scout_report completed",
        extra={'json_fields': {'tool': 'generate_scout_report', 'result': _safe_serialize(result)}}
    )

    if 'player' in result:
        message = f"""{result['player']} has property "Scout Report ID" with value "{result['id']}"."""
        # Propagate trace ID to background task
        async def _run_with_trace():
            set_trace_id(trace_id)
            await _curate_knowledge(graph_id=graph_id, user_id=user_id, query=message)
        asyncio.create_task(_run_with_trace())

    return json.dumps(result)


@mcp.tool(
        name='fetch_scout_report_by_id',
        description="This tool returns a player's Scout Report given its Scout Report ID.  Only use this if you have a Scout Report ID."
)
async def fetch_scout_report_by_id(
        scout_report_id: Annotated[str, "The ID of a Scout Report."]
) -> dict:
    headers = get_http_headers()
    graph_id = headers['x-graph-id']
    trace_id = headers.get('x-trace-id')

    # Set trace ID for logging context
    set_trace_id(trace_id)

    # Log tool input (flexible - pass all fields dynamically)
    logger.info(
        "fetch_scout_report_by_id called",
        extra={'json_fields': {'tool': 'fetch_scout_report_by_id', **_log_fields(
            scout_report_id=scout_report_id, graph_id=graph_id
        )}}
    )

    result = fetch_scout_report(scout_report_id)

    # Log tool output (flexible - pass result directly)
    logger.info(
        "fetch_scout_report_by_id completed",
        extra={'json_fields': {'tool': 'fetch_scout_report_by_id', 'result': _safe_serialize(result)}}
    )

    return result


@mcp.tool(
        name='search_knowledge_graph',
        description='This tool returns entities (e.g. players, teams, schools), their properties (e.g. Entity ID, Scout Report IDs, awards, personal info), and their inter-relationships, coming from the dynamic Knowledge Graph.'
)
async def search_knowledge_graph(
        query: Annotated[str, "A plain-text search query to find relevant knowledge in the knowledge graph."]
) -> dict:
    headers = get_http_headers()
    graph_id = headers['x-graph-id']
    trace_id = headers.get('x-trace-id')

    # Set trace ID for logging context
    set_trace_id(trace_id)

    # Log tool input (flexible - pass all fields dynamically)
    logger.info(
        "search_knowledge_graph called",
        extra={'json_fields': {'tool': 'search_knowledge_graph', **_log_fields(
            query=query, graph_id=graph_id
        )}}
    )

    url = os.environ['KG_URL'] + '/search'
    r = requests.get(url, params={'query': query, 'graph_id': graph_id})
    result = r.json()

    # Log tool output (flexible - pass result directly)
    logger.info(
        "search_knowledge_graph completed",
        extra={'json_fields': {'tool': 'search_knowledge_graph', 'status_code': r.status_code, 'result': _safe_serialize(result)}}
    )

    return result
