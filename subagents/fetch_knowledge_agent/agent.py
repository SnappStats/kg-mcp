from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from .tools import get_relevant_neighborhood

PROMPT = """
You are an agent with access to a knowledge graph. Your goal is to retrieve what is _currently_ stored in the knowledge graph, relevant to the user's input (e.g. conversation snippets, documents, etc.).

Examine the user input to identify all key topics and entities, then use the `get_relevant_neighborhood` tool to retrieve relevant portions of the knowledge graph.
"""

agent = Agent(
    name="fetch_knowledge_agent",
    model="gemini-2.5-flash",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=True,
            thinking_budget=512,
        )
    ),
    instruction=PROMPT,
    tools=[
        get_relevant_neighborhood
    ]
)
