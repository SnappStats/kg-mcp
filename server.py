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

from google.auth.transport.requests import Request as GoogleAuthRequest
import google.auth

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
                ctx=ctx
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


def _get_rag_credentials():
    """Get credentials for Vertex AI RAG."""
    try:
        from google.oauth2 import service_account

        key_json = os.getenv("API_GOOGLE_SERVICE_ACCOUNT_CREDENTIALS") or os.getenv("GOOGLE_APPLICATION_CREDENTIALS_JSON")
        if key_json:
            try:
                info = json.loads(key_json)
                return service_account.Credentials.from_service_account_info(info)
            except Exception:
                pass

        key_file = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
        if key_file and os.path.exists(key_file):
            try:
                return service_account.Credentials.from_service_account_file(key_file)
            except Exception:
                pass
    except ImportError:
        pass

    try:
        creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        return creds
    except Exception:
        return None


def _resolve_location_from_corpus(corpus_name: str) -> str:
    """Extract location from corpus name."""
    try:
        parts = (corpus_name or "").split("/")
        idx = parts.index("locations")
        return parts[idx + 1]
    except Exception:
        return os.getenv("VERTEX_LOCATION", "us-east4")


async def _retrieve_rag_contexts(query_text: str, top_k: int, corpus_name: str):
    """Retrieve contexts from Vertex AI RAG via REST API."""
    credentials = _get_rag_credentials()
    if credentials is None:
        raise RuntimeError("Missing Google credentials for RAG")

    scoped = credentials.with_scopes(["https://www.googleapis.com/auth/cloud-platform"])
    scoped.refresh(GoogleAuthRequest())
    token = scoped.token
    if not token:
        raise RuntimeError("Failed to obtain access token for Vertex AI")

    loc = _resolve_location_from_corpus(corpus_name)
    host = f"https://{loc}-aiplatform.googleapis.com"

    project_id = corpus_name.split('/')[1]
    parent = f"projects/{project_id}/locations/{loc}"

    url = f"{host}/v1/{parent}:retrieveContexts"

    payload = {
        "query": {
            "text": query_text,
            "ragRetrievalConfig": {
                "topK": int(top_k)
            }
        },
        "vertexRagStore": {
            "ragResources": [{
                "ragCorpus": corpus_name
            }]
        }
    }
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }

    loop = asyncio.get_running_loop()
    resp = await loop.run_in_executor(
        None,
        functools.partial(
            requests.post,
            url,
            headers=headers,
            data=json.dumps(payload),
            timeout=30
        )
    )

    if resp.status_code >= 300:
        raise RuntimeError(f"HTTP {resp.status_code}: {resp.text}")

    data = resp.json()
    contexts = []

    contexts_data = data.get("contexts", {})
    if isinstance(contexts_data, dict):
        context_list = contexts_data.get("contexts", [])
    else:
        context_list = contexts_data or []

    for ctx in context_list:
        if isinstance(ctx, dict):
            content = ctx.get("text") or ctx.get("content") or ""
            distance = ctx.get("distance")
            src = ctx.get("sourceUri") or ctx.get("source") or "unknown"
            contexts.append({
                "content": str(content),
                "distance": float(distance) if distance is not None else None,
                "source": str(src),
            })

    return contexts


@mcp.tool(
        name='search_football_knowledge',
        description='American Football Knowledge Base - Expert coaching knowledge from top football books and resources. Use this for answering questions about football concepts, strategy, technique, formations, schemes, coaching methodologies, etc. Returns top relevant knowledge snippets with sources.'
)
async def search_football_knowledge(
        query: Annotated[str, "Specific, focused query about football concepts. Examples: 'QB drop back mechanics', 'fire zone blitz coverage principles', 'zone blocking vs power scheme differences', 'what to look for when evaluating DE pass rush technique'"],
        top_k: Annotated[int, "Number of results to return (1-10)"] = 5
) -> str:
    """Search the American Football coaching knowledge base."""
    corpus_name = os.getenv(
        "RAG_AMERICAN_FB",
        os.getenv(
            "VERTEX_RAG_CORPUS",
            "projects/staging-470600/locations/us-east4/ragCorpora/4611686018427387904",
        ),
    )

    try:
        contexts = await _retrieve_rag_contexts(query, min(max(top_k, 1), 10), corpus_name)

        if not contexts:
            return json.dumps({"error": "No relevant information found in the knowledge base."})

        results = []
        for i, ctx in enumerate(contexts[:5], 1):
            content = (ctx.get("content") or "").strip()
            source = ctx.get("source") or "unknown"
            distance = ctx.get("distance")
            snippet = content[:800].replace("\n\n", "\n").strip()

            result = {
                "rank": i,
                "content": snippet,
                "source": source
            }
            if distance is not None:
                result["distance"] = round(distance, 4)

            results.append(result)

        return json.dumps({
            "query": query,
            "results": results,
            "total_found": len(contexts)
        }, indent=2)

    except Exception as e:
        logging.error(f"RAG search failed: {e}", exc_info=True)
        return json.dumps({"error": f"RAG search failed: {str(e)}"})
