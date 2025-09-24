# File server.py

import asyncio
import requests
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
from html2text import html2text

from fastmcp import FastMCP, Context

# Create an MCP server instance with an identifier ("webpage")
mcp = FastMCP("webpage")

@mcp.tool()
async def extract_webpage(url: str, ctx: Context) -> str:
    """
    Retrieves the contents of a given URL, extracting
    the main content and converting it to Markdown format.

    Usage:
        extract_webpage("https://en.wikipedia.org/wiki/Gemini_(chatbot)")
    """
    await ctx.info(f"Extracting content from URL: {url}")
    await ctx.report_progress(progress=10)
    try:
        if not url.startswith("http"):
            raise ValueError("URL must begin with http or https protocol.")

        response = requests.get(url, timeout=8)
        if response.status_code != 200:
            return f'Error: Unable to access the article. Server returned status: {str(response.status_code)}'

        soup = BeautifulSoup(response.text, "html.parser")
        content_div = soup.find("body")
        if not content_div:
            return 'Error: Unable to find the main content section in the webpage.'
        markdown_text = html2text(str(content_div))
        return markdown_text

    except Exception as e:
        return f"An unexpected error occurred: {str(e)}"
