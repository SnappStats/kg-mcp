from google.adk.agents import SequentialAgent

from .subagents.fetch_knowledge_agent import agent as fetch_knowledge_agent
from .subagents.update_knowledge_agent import agent as update_knowledge_agent

agent = SequentialAgent(
    name="knowledge_graph_agent",
    description='Curates and stores all knowledge (entities and their relationships) detected in the user input.',
    sub_agents=[
        fetch_knowledge_agent,
        update_knowledge_agent
    ],
)
