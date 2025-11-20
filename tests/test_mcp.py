import json
import re
from unittest.mock import patch

import pytest
from fastmcp.client import Client
from fastmcp.client.transports import FastMCPTransport
from pydantic import ValidationError
from utils.logger import logger, _log_fields

from scout_report_agent.scout_report_schema import ScoutReport
from server import mcp

@pytest.fixture
async def main_mcp_client():
    async with Client(transport=mcp) as mcp_client:
        yield mcp_client

async def test_list_tools(main_mcp_client: Client[FastMCPTransport]):
    list_tools = await main_mcp_client.list_tools()

    assert len(list_tools) == 4
    
    expected_tools = [
      'curate_knowledge',
      'generate_scout_report',
      'fetch_scout_report_by_id',
      'search_knowledge_graph',
    ]
    
    for tool in list_tools:
        assert tool.name in expected_tools


async def test_generate_scout_report(main_mcp_client: Client[FastMCPTransport]):
    mock_headers = {'x-graph-id': 'cf460c59-6b2e-42d3-b08d-b20ff54deb57'}
    
    with patch('server.get_http_headers', return_value=mock_headers), \
         patch('utils.logs_with_request_context.get_http_headers', return_value=mock_headers):
        call_result = await main_mcp_client.call_tool(
            'generate_scout_report',
            arguments={'player_context': 'Ryder Lyons'}
        )
        
        assert call_result is not None
        
        result_text = call_result.content[0].text
        result = json.loads(result_text)

        
        try:
            scout_report = ScoutReport(**result)
            assert scout_report.player.name == 'George Ryder Lyons II'
            if scout_report.player.hudl_profile is not None:
                assert re.match(r'https://www\.hudl\.com/profile/\d+(?:/[\w-]+)?$', scout_report.player.hudl_profile)
                assert re.match(r'https://.*\.hudl\.com/.*', scout_report.player.highlighted_reel)
            assert len(scout_report.tags) > 0
            assert len(scout_report.analysis) > 0
            assert len(scout_report.stats) > 0
            assert len(scout_report.citations) > 0
        except ValidationError as e:
            pytest.fail(f"Scout report validation failed: {e}")
