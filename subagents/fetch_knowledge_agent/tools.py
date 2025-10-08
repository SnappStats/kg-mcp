import json
import logging
import os
import networkx as nx
from dotenv import load_dotenv
from typing import Optional

from google.adk.tools import ToolContext
from google.cloud import storage
from thefuzz import fuzz
from floggit import flog

load_dotenv()

@flog
def get_relevant_neighborhood(entity_names: list[str], tool_context: ToolContext) -> dict:
    """
    Args:
        entity_names (list[str]): A list of entity names, and any synonyms, that might be found in the existing knowledge graph.

    Returns:
        dict: A relevant subgraph of the knowledge graph, including a surrounding neighborhood of the relevant entities (to help patching in a replacement subgraph).
    """
    graph_id = tool_context._invocation_context.user_id
    g = _fetch_knowledge_graph(graph_id=graph_id)

    relevant_entity_ids = _get_relevant_entities_for_phrases(
            phrases=entity_names, entities=g['entities'])
    neighborhood = _get_knowledge_subgraph(
            entity_ids=relevant_entity_ids, graph=g, num_hops=2)

    tool_context.state['existing_knowledge'] = neighborhood
    
    return neighborhood


@flog
def get_relevant_neighborhood_for_query(query: str, graph_id: str) -> dict:
    """
    Args:
        query (str): A user query that might be relevanet to some entities in the knowledge graph.
        graph_id (str): The ID of the knowledge graph to query.

    Returns:
        dict: A relevant subgraph of the knowledge graph, including a surrounding neighborhood of the relevant entities (to help patching in a replacement subgraph).
    """
    g = _fetch_knowledge_graph(graph_id=graph_id)

    relevant_entity_ids = _get_relevant_entities_in_query(
            query=query, entities=g['entities'])
    neighborhood = _get_knowledge_subgraph(
            entity_ids=relevant_entity_ids, graph=g, num_hops=1)

    return neighborhood


@flog
def _get_relevant_entities_for_phrases(phrases: list[str], entities: dict) -> set[str]:
    '''Returns a set of entity IDs from the knowledge graph that match the given phrases.'''

    relevant_entity_ids = set()

    for phrase in phrases:
        for entity_id, entity_data in entities.items():
            for entity_name in entity_data['entity_names']:
                if fuzz.ratio(phrase.lower(), entity_name.lower()) > 80:
                    relevant_entity_ids.add(entity_id)
                    break

    return relevant_entity_ids


@flog
def _get_relevant_entities_in_query(query: str, entities: dict) -> set[str]:
    '''Returns a set of entity IDs from the knowledge graph found in the given query.'''
    relevant_entity_ids = set()

    for entity_id, entity_data in entities.items():
        for entity_name in entity_data['entity_names']:
            if entity_name.lower() in query.lower():
                relevant_entity_ids.add(entity_id)
                break

    return relevant_entity_ids


def _get_bucket():
    storage_client = storage.Client()
    bucket_name = os.environ.get("KNOWLEDGE_GRAPH_BUCKET")
    if not bucket_name:
        raise ValueError("KNOWLEDGE_GRAPH_BUCKET environment variable not set.")
    return storage_client.get_bucket(bucket_name)


def _fetch_knowledge_graph(graph_id: str) -> dict:
    """Fetches the knowledge graph from the Google Cloud Storage bucket."""
    bucket = _get_bucket()
    blob = bucket.blob(f"{graph_id}.json")
    if not blob.exists():
        return {"entities": {}, "relationships": []}
    else:
        content = blob.download_as_text()
        return json.loads(content)


def _knowledge_graph_to_nx(g: dict) -> "nx.MultiDiGraph":
    """Converts the knowledge graph dictionary to a NetworkX MultiDiGraph."""
    mdg = nx.MultiDiGraph()
    mdg.add_nodes_from((k, v) for k, v in g["entities"].items())
    mdg.add_edges_from(
        (
            rel["source_entity_id"],
            rel["target_entity_id"],
            {"relationship": rel["relationship"]},
        )
        for rel in g.get("relationships", [])
    )
    return mdg


@flog
def _get_knowledge_subgraph(entity_ids: set[str], graph: dict, num_hops: Optional[int] = 2) -> dict:
    """Extracts a subgraph from the knowledge graph centered around the given entity IDs."""

    mdg = _knowledge_graph_to_nx(graph)

    # Relevant entities' 1-hop neighbors.
    nbrs1 = {
            nbr for entity_id in entity_ids
            for nbr in mdg.to_undirected().neighbors(entity_id)
            if nbr not in entity_ids
    }

    if num_hops > 1:
        # Relevant entities' 2-hop neighbors.
        nbrs2 = {
                nbr for entity_id in nbrs1
                for nbr in mdg.to_undirected().neighbors(entity_id)
                if nbr not in entity_ids and nbr not in nbrs1
        }

        outer_nbrs = nbrs2
    else:
        nbrs2 = set()
        outer_nbrs = nbrs1

    # outer neighbors connected to at least one external entity
    valence_entities = {
            entity_id for entity_id in outer_nbrs 
            if set(mdg.to_undirected().neighbors(entity_id)) - entity_ids - nbrs1 - nbrs2
    }

    subgraph = mdg.subgraph(entity_ids|nbrs1|nbrs2)
    subgraph_json = nx.node_link_data(subgraph, edges="links")

    # Reformat
    subgraph = {
        'entities': {
            node['entity_id']: dict(**node, has_external_neighbor=(node['entity_id'] in valence_entities))
            for node in subgraph_json['nodes']
        },
        'relationships': [
            {
                'source_entity_id': link['source'],
                'target_entity_id': link['target'],
                'relationship': link['relationship']
            } for link in subgraph_json['links']
        ]
    }

    return subgraph
