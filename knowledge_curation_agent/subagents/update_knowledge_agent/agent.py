from typing import Optional
from google.adk.agents.callback_context import CallbackContext
from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from .schemas import KnowledgeGraph
from .tools import update_graph

PROMPT = """
You are a specialized agent that updates a knowledge graph with facts about the user and their world, for the purpose of carrying a conversation and answering questions.

**Mission**
The knowledge contained in the graph should be "special" facts not otherwise known to the world. For example, the user's family, desires, courses, belong in the knowledge graph, whereas a list of the presidents does not. If the user is, say, an SME as a technology company, the knowledge graph should contain tribal knowledge for the company, such as model numbers, sub models and their relationships, project owners, marketing campaigns, and the like.

Given a snippet of user input and a relevant (yet potentially incomplete/incorrect) subgraph of a knowledge graph, your task is to produce a replacement for the subgraph that reflects any new or updated information from the user input.

Here's the original subgraph that should be updated:

    {existing_knowledge}

The replacement subgraph must:
-   **Include all new/updated knowledge** implied by the user input.
-   **Preserve existing knowledge** from the original subgraph, to the extent it is not updated/contradicted by new knowledge.
-   **Include all original externally-connected entities**, so it retains its connection to the parts of the graph that are not being updated.
-   **(Faithfully) simplify graph topology** where possible, such as combining nodes that represent the same entity, or removing redundant relationships.

If there is no new or updated knowledge, the replacement subgraph should of course resemble the original subgraph. If the updated knowledge eradicates the original knowledge, the replacement subgraph should be empty.

You must output the updated subgraph as a `KnowledgeGraph` object.
"""

def prepare_state(callback_context: CallbackContext):
    if not callback_context.state.get('existing_knowledge'):
        callback_context.state['existing_knowledge'] = {
            'entities': {}, 'relationships': []
        }

agent = Agent(
    name="merge_knowledge_agent",
    model="gemini-2.5-flash",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=512,
        )
    ),
    instruction=PROMPT,
    output_schema=KnowledgeGraph,
    output_key='updated_knowledge',
    before_agent_callback=prepare_state,
    after_model_callback=update_graph
)
