import datetime as dt
import os
from dotenv import load_dotenv

from google.adk.runners import Runner
from google.adk.sessions import VertexAiSessionService
from google.genai import types

from .agent import agent
from .scout_report_service import store_scout_report

# Load environment variables from .env file in root directory
load_dotenv()

AGENT_ENGINE_ID = os.environ['SESSION_SERVICE_URI'].split('/')[-1]

session_service = VertexAiSessionService(
    agent_engine_id=AGENT_ENGINE_ID,
)

agent_runner = Runner(
    agent=agent,
    app_name=AGENT_ENGINE_ID,
    session_service=session_service
)

async def main(graph_id: str, user_id: str, query: str):
    session = await session_service.create_session(
            app_name=AGENT_ENGINE_ID,
            user_id=user_id,
            state={'graph_id': graph_id})

    user_content = types.Content(role='user', parts=[types.Part(text=query)])
    qwer = agent_runner.run_async(
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
