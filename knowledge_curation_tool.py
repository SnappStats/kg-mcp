import requests
from dotenv import load_dotenv
import os
from utils.logger import logger

load_dotenv()


def main(query: str, graph_id: str, user_id: str) -> dict:
    logger.info("curate_knowledge called", query=query)

    url = os.environ['KG_URL'] + '/curate_knowledge'

    r = requests.post(url, json={
        'query': query,
        'graph_id': graph_id,
        'user_id': user_id
    })
    if r.status_code == 200:
        logger.info("curate_knowledge completed")
        return r.json()
    else:
        logger.warning(f"Failed to call curate knowledge endpoint. {r.text}")
        return {'response': '(Move on....)'}
