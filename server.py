import asyncio
import threading
import os
from dotenv import load_dotenv

from fastmcp import FastMCP, Context
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

provider = TracerProvider()
processor = export.BatchSpanProcessor(
    CloudTraceSpanExporter(project_id=os.environ['GOOGLE_CLOUD_PROJECT'])
)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

APP_NAME = 'kg'

session_service = InMemorySessionService()

mcp = FastMCP("knowledge_graph")

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
async def curate_knowledge(user_id: str, query: str) -> str:
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

@mcp.tool()
async def generate_scout_report_mcp(user_id: str, player_name: str) -> str:
    '''Generates a detailed scout report for a given player.

    user_id (str): The ID of the user making the request.
    player_name (str): The name of the player for whom the scout report is to be generated.
    '''
    # Use fast direct API approach
    report = generate_scout_report(user_id, player_name)

    # Format as JSON string for MCP return
    return report.model_dump_json(indent=2)
