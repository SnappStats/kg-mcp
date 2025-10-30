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
            base_message += f" Valence entity IDs: {self.valence_entity_ids}."
            base_message += f" Updated knowledge subgraph: {self.updated_knowledge_subgraph}."

            return base_message


def main(callback_context: CallbackContext, llm_response: LlmResponse) -> Optional[LlmResponse]:
    """
    Stores the provided graph in the knowledge graph store.
    This will overwrite the existing graph.
    """
    if llm_response.partial:
        return

    existing_subgraph = callback_context.state['existing_knowledge']
    if response_text := llm_response.content.parts[-1].text:
        replacement_subgraph = json.loads(response_text)

        # Reformat replacement_subgraph to have dict of entities
        replacement_subgraph = {
                'entities': {
                    entity['entity_id']: entity
                    for entity in replacement_subgraph['entities']
                },
                'relationships': replacement_subgraph['relationships']
        }

        _update_graph(
                old_subgraph=existing_subgraph,
                new_subgraph=replacement_subgraph,
                user_id=callback_context._invocation_context.user_id,
                graph_id=callback_context.state['graph_id'])
    else:
        logging.error("No response text found in LLM response.")
        return


@flog
def _update_graph(
        old_subgraph: dict, new_subgraph: dict, user_id: str, graph_id: str
) -> None:
    '''Updates the knowledge graph by replacing old_subgraph with new_subgraph.'''

    # Ensure valence entities are included in new_subgraph
    valence_entity_ids = {
            entity_id
            for entity_id, entity in old_subgraph['entities'].items()
            if entity['has_external_neighbor']
    }
    if not valence_entity_ids.issubset(new_subgraph['entities'].keys()):
        raise InvalidUpdatedKnowledgeSubgraphError(
                message="Updated subgraph missing valence entities.",
                valence_entity_ids=valence_entity_ids,
                updated_knowledge_subgraph=new_subgraph
        )

    # Restore original IDs for preserved entities
    new_subgraph = _restore_original_IDs(
            old_subgraph=old_subgraph,
            new_subgraph=new_subgraph)

    # Identify minimal subgraph delta
    remove_subgraph, add_subgraph = _identify_minimal_subgraph_delta(
            new_subgraph=new_subgraph,
            old_subgraph=old_subgraph)

    # Update metadata for new entities
    add_subgraph = _update_graph_metadata(
            graph=add_subgraph,
            user_id=user_id)

    # Splice updated subgraph into knowledge graph
    _splice_subgraph(
            graph_id=graph_id,
            remove_subgraph=remove_subgraph,
            add_subgraph=add_subgraph)


@flog
def _update_graph_metadata(graph: dict, user_id: str) -> dict:
    '''Updates the metadata of all entities in the graph.

    Args:
        graph (dict): A graph.
        user_id (str): The user ID of the person making the update.

    Returns:
        dict: The graph with updated metadata.
    '''
    id_mapping = {
            entity_id: _generate_entity_id(entity['entity_names'][0])
            for entity_id, entity in graph['entities'].items()
    }

    # Update entity IDs
    updated_entities = {}
    for old_entity_id, entity in graph['entities'].items():
        new_entity_id = id_mapping[old_entity_id]
        entity['entity_id'] = new_entity_id
        entity['updated_by'] = user_id
        entity['updated_at'] = dt.datetime.now(dt.UTC).isoformat(timespec='seconds')
        updated_entities[new_entity_id] = entity
    graph['entities'] = updated_entities

    # Update relationships
    for rel in graph['relationships']:
        rel['source_entity_id'] = id_mapping.get(
                rel['source_entity_id'], rel['source_entity_id'])
        rel['target_entity_id'] = id_mapping.get(
                rel['target_entity_id'], rel['target_entity_id'])

    return graph


@flog
def _restore_original_IDs(
        old_subgraph: dict, new_subgraph: dict) -> dict:
    '''Returns new_subgraph, but with "preserved" entities restored to their original IDs.

    Args:
        old_subgraph (dict): The old subgraph.
        new_subgraph (dict): The new subgraph.
    Returns:
        dict: The new subgraph with relabeled entities.
    '''

    ignore_keys = ['entity_id', 'updated_at', 'updated_by']
    old_subgraph_entity_signatures = {
        entity_id: {k: v for k, v in entity.items() if k not in ignore_keys}
        for entity_id, entity in old_subgraph['entities'].items()
    }
    id_mapping = {}

    # Identify "preserved" entities
    for new_entity_id, new_entity in new_subgraph['entities'].items():
        for old_entity_id, old_entity_signature in old_subgraph_entity_signatures.items():
            new_entity_signature = {
                    k: v for k, v in new_entity.items() if k not in ignore_keys}
            if new_entity_signature == old_entity_signature:
                id_mapping[new_entity_id] = old_entity_id
                break

    # Apply relabeling
    # Add preserved entities using old IDs
    for new_entity_id, new_entity in new_subgraph['entities'].items():
        if new_entity_id in id_mapping:
            old_entity_id = id_mapping[new_entity_id]
            new_subgraph['entities'][old_entity_id] = old_subgraph['entities'][old_entity_id]

    # Excise preserved entities with their new IDs
    new_subgraph['entities'] = {
            k: v for k, v in new_subgraph['entities'].items()
            if k not in id_mapping}

    # Update relationships to use old IDs
    for rel in new_subgraph['relationships']:
        if rel['source_entity_id'] in id_mapping:
            rel['source_entity_id'] = id_mapping[rel['source_entity_id']]
        if rel['target_entity_id'] in id_mapping:
            rel['target_entity_id'] = id_mapping[rel['target_entity_id']]

    # For good measure, ensure new_subgraph includes "valence" entities
    for entity_id, entity in old_subgraph['entities'].items():
        if entity['has_external_neighbor']:
            new_subgraph['entities'][entity_id] = entity

    return new_subgraph


@flog
def _identify_minimal_subgraph_delta(new_subgraph: dict, old_subgraph: dict) -> dict:
    '''Identifies the minimal subgraphs to delete and add.

    An entity/relationship should be removed if it exists in old_subgraph but not in new_subgraph.
    An entity/relationship should be added if it exists in new_subgraph but not in old_subgraph.

    Args:
        new_subgraph (dict): The new subgraph.
        old_subgraph (dict): The old subgraph.

    Returns:
        dict: The subgraphs to remove and add.
    '''

    add_subgraph = {'entities': {}, 'relationships': []}
    add_subgraph['entities'] = {
            k: v for k, v in new_subgraph['entities'].items()
            if k not in old_subgraph['entities']
    }
    add_subgraph['relationships'] = [
            rel for rel in new_subgraph['relationships']
            if rel not in old_subgraph['relationships']
    ]

    remove_subgraph = {'entities': {}, 'relationships': []}
    remove_subgraph['entities'] = {
            k: v for k, v in old_subgraph['entities'].items()
            if k not in new_subgraph['entities']
    }
    remove_subgraph['relationships'] = [
            rel for rel in old_subgraph['relationships']
            if rel not in new_subgraph['relationships']
    ]

    return remove_subgraph, add_subgraph


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
def _splice_subgraph(
        graph_id: str,
        remove_subgraph: dict,
        add_subgraph: dict):

    '''Splices new_subgraph into the knowledge graph identified by graph_id,
    excising old_subgraph first.'''

    graph = _fetch_knowledge_graph(graph_id)

    # Excise old subgraph
    graph['entities'] = {
            k: v
            for k, v in graph['entities'].items()
            if k not in remove_subgraph['entities']
    }
    remove_relationships = [
            (rel['source_entity_id'], rel['target_entity_id'])
            for rel in remove_subgraph['relationships']
    ]
    graph['relationships'] = [
            rel for rel in graph['relationships']
            if (rel['source_entity_id'], rel['target_entity_id'])
            not in remove_relationships
    ]

    # Insert new subgraph
    graph['entities'].update(
            add_subgraph['entities'])
    graph['relationships'].extend(
            add_subgraph['relationships'])

    _store_knowledge_graph(knowledge_graph=graph, graph_id=graph_id)
