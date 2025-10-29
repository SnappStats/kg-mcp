import datetime as dt
import json
import logging
import os
from dotenv import load_dotenv
from typing import Optional
from floggit import flog

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse
from google.cloud import storage

from .utils import generate_random_string, remove_nonalphanumeric

load_dotenv()

GRAPH_ID = 'cf460c59-6b2e-42d3-b08d-b20ff54deb57'

def _get_bucket():
    storage_client = storage.Client()
    bucket_name = os.environ.get("KG_BUCKET")
    if not bucket_name:
        raise ValueError("KG_BUCKET environment variable not set.")
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


@flog
def _store_knowledge_graph(knowledge_graph: dict, graph_id: str) -> None:
    """Stores the knowledge graph in the Google Cloud Storage bucket."""
    entity_ids = set(knowledge_graph['entities'].keys())
    terminals = set(rel['source_entity_id'] for rel in knowledge_graph['relationships']).union(
        rel['target_entity_id'] for rel in knowledge_graph['relationships'])

    if terminals - entity_ids:
        logging.warning(f"Some relationships refer to non-existent entities: {terminals - entity_ids}")

    bucket = _get_bucket()
    blob = bucket.blob(f"{graph_id}.json")
    blob.upload_from_string(
        json.dumps(knowledge_graph, indent=2), content_type="application/json"
    )


def _generate_entity_id(name: str) -> str:
    return f"{remove_nonalphanumeric(name)[:4].lower()}.{generate_random_string(length=4)}"


@flog
def _reformat_graph(graph: dict, valence_entity_ids: set, user_id: str) -> dict:
    '''
    Args:
        graph (dict): A knowledge graph as a dict, with graph['entities'] as a list.

    Returns:
        dict: graph, but with new entity IDs, and with graph['entities'] now as a dict.'''

    utcnow = dt.datetime.now(dt.UTC).isoformat(timespec='seconds')

    id_mapping = {
            entity['entity_id']: (
                entity['entity_id']
                if entity['entity_id'] in valence_entity_ids
                else _generate_entity_id(entity['entity_names'][0])
            )
            for entity in graph['entities']
    }

    graph['entities'] = {
            id_mapping[entity['entity_id']]: (
                entity | {
                    'entity_id': id_mapping[entity['entity_id']],
                    'updated_at': entity.get('updated_at') if entity['entity_id'] in valence_entity_ids else utcnow,
                    'updated_by': entity.get('updated_by') if entity['entity_id'] in valence_entity_ids else user_id
                }
            )
            for entity in graph['entities']
    }

    graph['relationships'] = [
            rel | {
                'source_entity_id': id_mapping[rel['source_entity_id']],
                'target_entity_id': id_mapping[rel['target_entity_id']]
            }
            for rel in graph['relationships']
    ]

    return graph

class InvalidUpdatedKnowledgeSubgraphError(Exception):
        """Custom exception for invalid knowledge subgraph."""
        def __init__(
                self,
                message: str,
                valence_entity_ids: set = None,
                updated_knowledge_subgraph: dict = None):
            super().__init__(message)
            self.valence_entity_ids = valence_entity_ids
            self.updated_knowledge_subgraph = updated_knowledge_subgraph

        def __str__(self):
            base_message = super().__str__()
            base_message += f" Frozen entity IDs: {self.valence_entity_ids}."
            base_message += f" Updated knowledge subgraph: {self.updated_knowledge_subgraph}."

            return base_message


def update_graph(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """
    Stores the provided graph in the knowledge graph store.
    This will overwrite the existing graph.
    """
    if llm_response.partial:
        return

    existing_knowledge_subgraph = callback_context.state['existing_knowledge']
    valence_entity_ids = {
            k for k, v in existing_knowledge_subgraph['entities'].items()
            if v.get('has_external_neighbor')}
    if response_text := llm_response.content.parts[-1].text:
        updated_knowledge_subgraph = json.loads(response_text)

        # Ensure valence entities retain their IDs
        if not valence_entity_ids.issubset(
                {e['entity_id'] for e in updated_knowledge_subgraph['entities']}
        ):
            logging.error(
                    f"Updated subgraph missing valence entity IDs.",
                    extra={
                        'json_fields': {
                            'existing_knowledge_subgraph': existing_knowledge_subgraph,
                            'updated_knowledge_subgraph': updated_knowledge_subgraph,
                            'valence_entity_ids': list(valence_entity_ids)
                        }
                    }
            )
            raise InvalidUpdatedKnowledgeSubgraphError(
                    message="Updated subgraph missing valence entity IDs.",
                    valence_entity_ids=valence_entity_ids,
                    updated_knowledge_subgraph=updated_knowledge_subgraph
            )

        updated_knowledge_subgraph = _reformat_graph(
                graph=updated_knowledge_subgraph,
                valence_entity_ids=valence_entity_ids,
                user_id=callback_context._invocation_context.user_id)

        _update_knowledge_graph(
                #graph_id=callback_context._invocation_context.user_id,
                graph_id=GRAPH_ID,
                old_subgraph=existing_knowledge_subgraph,
                new_subgraph=updated_knowledge_subgraph)

@flog
def _update_knowledge_graph(
        graph_id: str,
        old_subgraph: dict,
        new_subgraph: dict):

    graph = _fetch_knowledge_graph(graph_id)

    # Excise existing_knowledge_graph
    graph['entities'] = {
            k: v
            for k, v in graph['entities'].items()
            if k not in old_subgraph['entities']
    }
    old_relationships = [
            (rel['source_entity_id'], rel['target_entity_id'])
            for rel in old_subgraph['relationships']
    ]
    graph['relationships'] = [
            rel for rel in graph['relationships']
            if (rel['source_entity_id'], rel['target_entity_id'])
            not in old_relationships
    ]

    # Insert updated_knowledge_graph
    graph['entities'].update(
            new_subgraph['entities'])
    graph['relationships'].extend(
            new_subgraph['relationships'])

    _store_knowledge_graph(knowledge_graph=graph, graph_id=graph_id)
