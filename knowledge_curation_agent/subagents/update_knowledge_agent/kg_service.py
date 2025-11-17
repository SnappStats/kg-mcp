import datetime as dt
import json
import os
import logging
from dotenv import load_dotenv
from floggit import flog
from google.cloud import storage
from google.cloud import spanner

load_dotenv()

PROJECT_ID = os.environ['GOOGLE_CLOUD_PROJECT']
INSTANCE_ID = "knowledge-graph"
DATABASE_ID = "kg"

SPANNER_DATABASE = spanner.Client(
        project=PROJECT_ID).instance(INSTANCE_ID).database(DATABASE_ID)


def fetch_knowledge_graph(graph_id: str) -> dict:
    """Fetches the knowledge graph from the Google Cloud Storage bucket."""
    bucket = _get_bucket()
    blob = bucket.blob(f"{graph_id}.json")
    if not blob.exists():
        return {"entities": {}, "relationships": []}
    else:
        content = blob.download_as_text()
        return json.loads(content)


def store_knowledge_graph(knowledge_graph: dict, graph_id: str) -> None:
    """Stores the knowledge graph in the Google Cloud Storage bucket."""
    bucket = _get_bucket()
    blob = bucket.blob(f"{graph_id}.json")
    blob.upload_from_string(
        json.dumps(knowledge_graph), content_type="application/json"
    )

def _get_bucket():
    storage_client = storage.Client()
    bucket_name = os.environ.get("KNOWLEDGE_GRAPH_BUCKET")
    if not bucket_name:
        raise ValueError("KNOWLEDGE_GRAPH_BUCKET environment variable not set.")
    return storage_client.get_bucket(bucket_name)


def fetch_from_database():
    with SPANNER_DATABASE.snapshot() as snapshot:
        entities = snapshot.execute_sql("select * from entity")
    with SPANNER_DATABASE.snapshot() as snapshot:
        relationships = snapshot.execute_sql("select * from relationship")

    return entities, relationships


@flog
def store_graph_delta(remove_subgraph: dict, add_subgraph: dict):
    entities_to_upsert = [
        [
            e['entity_id'],
            e['entity_names'],
            dt.datetime.strptime(e['updated_at'], "%Y-%m-%dT%H:%M:%S%z"),
            e['updated_by'],
            json.dumps(e.get('properties', {}))
        ]
        for e in add_subgraph['entities'].values()
    ]

    relationships_to_upsert = [
        [
            r["source_entity_id"],
            r['target_entity_id'],
            r["relationship"]
        ]
        for r in add_subgraph['relationships']
    ]

    entities_to_delete = [
            [entity_id] for entity_id in remove_subgraph['entities']]

    relationships_to_delete = [
        (r['source_entity_id'], r['target_entity_id'], r['relationship'])
        for r in remove_subgraph['relationships']
    ]

    def execute(transaction):
        if relationships_to_delete:
            transaction.delete(
                    'relationship', keyset=spanner.KeySet(keys=relationships_to_delete))

        if entities_to_delete:
            transaction.delete(
                    'entity', keyset=spanner.KeySet(keys=entities_to_delete))

        if entities_to_upsert:
            transaction.insert_or_update(
                'entity',
                columns=['entity_id', 'entity_names', 'updated_at', 'updated_by', 'properties'],
                values=entities_to_upsert
            )

        if relationships_to_upsert:
            transaction.insert_or_update(
                'relationship',
                columns=['source_entity_id', 'target_entity_id', 'relationship'],
                values=relationships_to_upsert
            )

    if (
        entities_to_upsert
        or relationships_to_upsert
        or entities_to_delete
        or relationships_to_delete
    ):
        try:
            results = SPANNER_DATABASE.run_in_transaction(execute)
        except Exception as e:
            print('Transaction failed; rolled back.')
            logging.exception(e)
            return {
                'entities_inserted_or_updated': [],
                'entities_deleted': [],
                'relationships_inserted_or_updated': [],
                'relationships_deleted': []
            }

    return {
        'entities_inserted_or_updated': entities_to_upsert,
        'entities_deleted': entities_to_delete,
        'relationships_inserted_or_updated': relationships_to_upsert,
        'relationships_deleted': relationships_to_delete
    }
