import json
from floggit import flog
from .utils import generate_random_string

from google.cloud import storage

storage_client = storage.Client()
bucket = storage_client.get_bucket('snappstats-scout-reports')

@flog
def fetch_scout_report(scout_report_id: str) -> dict:
    '''
    Args:
        scout_report_id (str): The ID of a Scout Report.
    Returns:
        dict: A Scout Report
    '''
    blob = bucket.blob(scout_report_id)
    if not blob.exists():
        scout_report = {}
    else:
        scout_report = json.loads(blob.download_as_text())

    return scout_report


@flog
def store_scout_report(scout_report: dict) -> str:
    """Stores the knowledge graph in the Google Cloud Storage bucket."""
    scout_report_id = generate_random_string()
    scout_report.update({'id': scout_report_id})

    blob = bucket.blob(scout_report_id)
    blob.upload_from_string(
        json.dumps(scout_report), content_type="application/json"
    )

    return scout_report_id
