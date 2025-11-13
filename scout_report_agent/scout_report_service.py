import json
import os
from floggit import flog
from dotenv import load_dotenv
from .utils import generate_random_string
from utils.logger import logger

load_dotenv()

from pymongo import MongoClient
mongo_client = MongoClient(os.environ['MONGO_URI'])
database = mongo_client.get_database('snappstats')
reports_collection = database.get_collection('reports')

@flog
@logger.catch(reraise=True)
def fetch_scout_report(scout_report_id: str) -> dict:
    '''
    Args:
        scout_report_id (str): The ID of a Scout Report.
    Returns:
        dict: A Scout Report
    '''
    report = reports_collection.find_one({'id': scout_report_id})

    if report:
        del report['_id']

    return report

@flog
@logger.catch(reraise=True)
def store_scout_report(scout_report: dict) -> str:
    """Stores the knowledge graph in the Google Cloud Storage bucket."""
    scout_report_id = generate_random_string()
    scout_report.update({'id': scout_report_id})

    reports_collection.replace_one(
            {'id': scout_report_id}, scout_report, upsert=True)

    return scout_report_id
