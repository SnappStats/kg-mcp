import asyncio
import threading
import os
from dotenv import load_dotenv
from typing import Annotated

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

@mcp.tool(
        name='curate_knowledge',
        description='This tool records knowledge in the knowledge base. It should be called whenever potentially new, relevant knowledge is encountered.'
)
async def curate_knowledge(
        user_id: Annotated[str, "The ID of the user."],
        query: Annotated[str, "A snippet of text or a document that contains potentially new or updated knowledge."],
) -> str:
    headers = get_http_headers()
    print(f"Headers: {headers}")

    t = threading.Thread(
        target=_start_async_loop,
        name="BackgroundWorker",
        kwargs={'user_id': user_id, 'query': query},
        daemon=False
    )
    t.start()

    return 'This is being taken care of.'

@mcp.tool(
        name='generate_scout_report',
        description='This tool returns a detailed Scout Report for a given player. It should be called whenever the user solicits a Scout Report, or solicits information likely to be found in a Scout Report.'
)
async def scout_report(
        user_id: Annotated[str, "The ID of the user making the request."],
        player_name: Annotated[str, "The name of the player for whom the scout report is to be generated."]
) -> str:
    headers = get_http_headers()
    print(f"Headers: {headers}")
    # Use fast direct API approach
    report = generate_scout_report(user_id, player_name)

    # Format as JSON string for MCP return
    return report.model_dump_json(indent=2)
