import datetime as dt
import json
import logging
from typing import Optional
from floggit import flog

from google.adk.agents.callback_context import CallbackContext
from google.adk.models import LlmResponse

from .utils import generate_random_string, remove_nonalphanumeric
from .kg_service import fetch_knowledge_graph, store_knowledge_graph, store_graph_delta


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

    valence_entity_ids = _get_valence_entities(graph=old_subgraph)

    if missing_valence_entity_ids := _get_missing_entity_ids(
            graph=new_subgraph, required_entity_ids=valence_entity_ids):
        logging.error(
            'Updated subgraph missing valence entities.',
            extra={
                'json_fields': {
                    'missing_valence_entity_ids': missing_valence_entity_ids,
                    'old_subgraph': old_subgraph,
                    'new_subgraph': new_subgraph
                }
            }
        )
        return

    # Remove relationships pointing to nonexistent entities.
    new_subgraph = _trim_fuzzy_relationships(
            graph=new_subgraph, ignore=valence_entity_ids)

    # Give new IDs to new/modified entities
    new_subgraph = _relabel_inequivalent_entities(
            g1=old_subgraph, g2=new_subgraph)

    # Restore original IDs for preserved entities
    new_subgraph = _relabel_equivalent_entities(
            g1=old_subgraph, g2=new_subgraph)

    # Identify entities/relationships to remove.
    remove_subgraph = _calc_graph_difference(
            g1=old_subgraph, g2=new_subgraph)

    # Identify entities/relationships to add.
    add_subgraph = _calc_graph_difference(
            g1=new_subgraph, g2=old_subgraph)

    # Update metadata for new entities
    add_subgraph = _update_graph_metadata(g=add_subgraph, user_id=user_id)

    # Splice updated subgraph into knowledge graph
    _splice_subgraph(
            graph_id=graph_id,
            remove_subgraph=remove_subgraph,
            add_subgraph=add_subgraph)


@flog
def _trim_fuzzy_relationships(graph: dict, ignore: set) -> dict:
    '''Remove edges that refer to nonexistent entities.

    Such edges would arise due to imperfect AI.'''

    required_entity_ids = graph['entities'].keys() - ignore
    graph['relationships'] = [
            r for r in graph['relationships']
            if (
                r['source_entity_id'] in required_entity_ids
                and r['target_entity_id'] in required_entity_ids
            )
    ]

    return graph


@flog
def _get_valence_entities(graph: dict) -> dict:
    '''Returns a graph's valence entities.

    Args:
        graph (dict): A graph.

    Returns:
        set: A dict of valence entities.
    '''
    return {
            entity_id
            for entity_id, entity in graph['entities'].items()
            if entity['has_external_neighbor']
    }

@flog
def _get_missing_entity_ids(
        graph: dict, required_entity_ids: set) -> set:
    '''Returns the IDs of entities missing from the graph.'''
    existing_entity_ids = set(graph['entities'].keys()).union(
            rel['source_entity_id'] for rel in graph['relationships']).union(
            rel['target_entity_id'] for rel in graph['relationships'])

    return required_entity_ids - existing_entity_ids


@flog
def _update_graph_metadata(g: dict, user_id: str) -> dict:
    '''Updates the metadata of all entities in the graph.

    Args:
        graph (dict): A graph.
        user_id (str): The user ID of the person making the update.

    Returns:
        dict: The graph with updated metadata.
    '''

    for entity in g['entities'].values():
        entity['updated_by'] = user_id
        entity['updated_at'] = dt.datetime.now(dt.UTC).isoformat(timespec='seconds')

    return g


def _generate_entity_id(name: str) -> str:
    return f"{remove_nonalphanumeric(name)[:4].lower()}.{generate_random_string(length=4)}"


@flog
def _signature(entity):
    return {
            k: v for k, v in entity.items()
            if k in ['entity_names', 'properties']}


@flog
def _relabel_entities(g: dict, id_mapping: dict) -> dict:
    '''
    Args:
        g (dict): A graph
        entity_ids (list[str]): A list of entity IDs in g to be relabeled
    Returns:
        (dict): The graph g, but with the specified entity IDs changed
    '''

    # Add relabeled entities to g
    for old_id, new_id in id_mapping.items():
        g['entities'][new_id] = g['entities'][old_id] 
        g['entities'][new_id]['entity_id'] = new_id

    # Remove entities having old (and different!) IDs
    g['entities'] = {
            k: v for k, v in g['entities'].items()
            if (k not in id_mapping) or (id_mapping.get(k) == k)
    }

    # Update relationships to use new IDs
    for rel in g['relationships']:
        rel['source_entity_id'] = id_mapping.get(
                rel['source_entity_id'], rel['source_entity_id'])
        rel['target_entity_id'] = id_mapping.get(
                rel['target_entity_id'], rel['target_entity_id'])

    return g


@flog
def _relabel_inequivalent_entities(g1: dict, g2: dict) -> dict:
    '''
    Args:
        g1 (dict): A graph.
        g2 (dict): Another graph, possibly with entities different from g1's

    Returns:
        dict: g2, with a new ID for any entity labeled the same as, yet
        different from, an entity in g1
    '''

    entities_to_relabel = []

    colliding_entity_ids = set(g1['entities']).intersection(g2['entities'])
    entity_ids_to_relabel = [
            entity_id for entity_id in colliding_entity_ids
            if _signature(g1['entities'][entity_id]) != _signature(g2['entities'][entity_id])
    ]

    id_mapping = {
            entity_id: _generate_entity_id(
                g2['entities'][entity_id]['entity_names'][0])
            for entity_id in entity_ids_to_relabel
    }
    g2 = _relabel_entities(g2, id_mapping)

    return g2


@flog
def _relabel_equivalent_entities(g1: dict, g2: dict) -> dict:
    '''
    Args:
        g1 (dict): A graph.
        g2 (dict): Another graph, possibly with entities equivalent to g1's

    Returns:
        dict: g2, with entities equivalent to g1's now assigned with g1's labels 
    '''

    g1_entity_signatures = {
        entity_id: _signature(entity)
        for entity_id, entity in g1['entities'].items()
    }
    id_mapping = {}

    # Identify equivalent entities
    for g2_entity_id, g2_entity in g2['entities'].items():
        g2_entity_signature = _signature(g2_entity)
        for g1_entity_id, g1_entity_signature in g1_entity_signatures.items():
            if g2_entity_signature == g1_entity_signature:
                id_mapping[g2_entity_id] = g1_entity_id
                break

    g2 = _relabel_entities(g2, id_mapping)

    # For good measure, ensure g2 includes "valence" entities
    for entity_id, entity in g1['entities'].items():
        if entity['has_external_neighbor']:
            g2['entities'][entity_id] = entity

    return g2


@flog
def _calc_graph_difference(g1: dict, g2: dict) -> dict:
    '''
    Args:
        g1 (dict): A graph.
        g2 (dict): Another graph.

    Returns:
        dict: The entities/relationships in g1 - g2

    NB: Algo assumes A ~ B <=> A.id == B.id
    '''

    g1_minus_g2 = {'entities': {}, 'relationships': []}
    g1_minus_g2['entities'] = {
            k: v for k, v in g1['entities'].items()
            if k not in g2['entities']
    }
    g1_minus_g2['relationships'] = [
            rel for rel in g1['relationships']
            if rel not in g2['relationships']
    ]

    return g1_minus_g2


@flog
def _splice_subgraph(
        graph_id: str,
        remove_subgraph: dict,
        add_subgraph: dict):

    '''Splices new_subgraph into the knowledge graph identified by graph_id,
    excising old_subgraph first.'''

    # This is where to add a lock, to be removed either if graph is erroneous or stored.
    graph = fetch_knowledge_graph(graph_id)

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

    if invalid_entity_ids := _get_invalid_relationship_entity_ids(graph):
        logging.warning(
            'Graph delta not recorded due to invalid relationship entity IDs.',
            extra={
                'json_fields': {
                    'graph_id': graph_id,
                    'invalid_relationship_entity_ids': list(invalid_entity_ids)
                }
            }
        )
    else:
        store_graph_delta(
                remove_subgraph=remove_subgraph, add_subgraph=add_subgraph)
        store_knowledge_graph(knowledge_graph=graph, graph_id=graph_id)


@flog
def _get_invalid_relationship_entity_ids(graph: dict) -> set:
    '''Returns relationship between non-existent entities.'''

    entity_ids = set(graph['entities'].keys())
    terminals = set(rel['source_entity_id'] for rel in graph['relationships']).union(
        rel['target_entity_id'] for rel in graph['relationships'])

    return terminals - entity_ids
