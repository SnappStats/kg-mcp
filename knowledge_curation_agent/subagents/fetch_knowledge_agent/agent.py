from floggit import flog
import os
import requests
from dotenv import load_dotenv

from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.adk.tools import ToolContext
from google.genai import types

load_dotenv()

PROMPT = """
You are an agent with access to a knowledge graph. Your goal is to retrieve what is _currently_ stored in the knowledge graph, relevant to the user's input (e.g. conversation snippets, documents, etc.).

Examine the user input to identify all key topics and entities, then use the `get_relevant_neighborhood` tool to retrieve relevant portions of the knowledge graph.
"""

@flog
def get_relevant_neighborhood(query: str, tool_context: ToolContext) -> dict:
    '''
    Args:
        query (str): A query string representing relevant information (e.g. entities) to search for in the knowledge graph.
    Returns:
        dict: The relevant knowledge graph data.
    '''
    graph_id = tool_context.state['graph_id']
    url = os.environ['KG_URL'] + '/search'
    r = requests.get(url, params={'query': query, 'graph_id': graph_id})
    tool_context.state['existing_knowledge'] = r.json()
    return r.json()


agent = Agent(
    name="fetch_knowledge_agent",
    model="gemini-2.5-flash",
    #planner=BuiltInPlanner(
    #    thinking_config=types.ThinkingConfig(
    #        include_thoughts=True,
    #        thinking_budget=512,
    #    )
    #),
    instruction=PROMPT,
    tools=[
        get_relevant_neighborhood
    ]
)
