import datetime as dt
from dotenv import load_dotenv

from .agent import generate_scout_report
from .scout_report_service import store_scout_report

# Load environment variables from .env file in root directory
load_dotenv()


async def main(graph_id: str, user_id: str, query: str):
    """
    Main entry point for scout report generation via MCP.

    Args:
        graph_id: Knowledge graph ID
        user_id: User ID for attribution
        query: Player query string

    Returns:
        Scout report dict or feedback dict
    """
    # Generate the scout report
    scout_report = generate_scout_report(query)

    # If successful, add timestamp and store
    if 'player' in scout_report:
        utc_now = dt.datetime.now(dt.UTC).isoformat(timespec='seconds')
        scout_report.update({'report_at': utc_now})
        scout_report_id = store_scout_report(scout_report)
        scout_report.update({'id': scout_report_id})
        return scout_report

    # Otherwise return feedback
    return scout_report
