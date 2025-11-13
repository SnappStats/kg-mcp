"""
Extract citations/URLs from Brightdata search results
"""

import re
from typing import List, Set


def extract_urls_from_markdown(markdown_text: str) -> List[str]:
    """
    Extract all URLs from markdown text returned by Brightdata.

    Brightdata returns markdown with URLs in formats like:
    - [link text](https://example.com)
    - https://example.com (plain URLs)

    Returns:
        List of unique URLs found in the markdown
    """
    urls = set()

    # Pattern 1: Markdown links [text](url)
    markdown_pattern = r'\[([^\]]+)\]\(([^)]+)\)'
    for match in re.finditer(markdown_pattern, markdown_text):
        url = match.group(2)
        if url.startswith('http'):
            urls.add(url)

    # Pattern 2: Plain URLs
    url_pattern = r'https?://[^\s<>"{}|\\^`\[\]()]+'
    for match in re.finditer(url_pattern, markdown_text):
        url = match.group(0)
        # Clean up common trailing punctuation
        url = re.sub(r'[.,;:!?]+$', '', url)
        urls.add(url)

    # Filter out search engine URLs and focus on actual content
    filtered_urls = []
    for url in urls:
        # Skip Google/Bing/Yandex search result pages
        if any(domain in url for domain in [
            'google.com/search',
            'bing.com/search',
            'yandex.com/search',
            'webcache.googleusercontent.com'
        ]):
            continue
        filtered_urls.append(url)

    return sorted(list(set(filtered_urls)))


def combine_citations(search_results: List[dict]) -> List[str]:
    """
    Combine citations from multiple search results.

    Args:
        search_results: List of search result dictionaries with 'result' field containing markdown

    Returns:
        List of unique URLs from all searches
    """
    all_urls = set()

    for result in search_results:
        if isinstance(result, dict) and 'result' in result:
            urls = extract_urls_from_markdown(result['result'])
            all_urls.update(urls)

    return sorted(list(all_urls))


# Test the extraction
if __name__ == "__main__":
    sample_markdown = """
## Search Results

### Bryce Underwood - Wikipedia
[https://en.wikipedia.org/wiki/Bryce_Underwood](https://en.wikipedia.org/wiki/Bryce_Underwood)
Bryce Underwood (born November 21, 2006) is an American football quarterback...

### MaxPreps Profile
View stats at https://www.maxpreps.com/athlete/bryce-underwood/

### 247Sports
[Top QB Recruit](https://247sports.com/player/bryce-underwood-46113169/)
The #1 overall recruit in the 2025 class...
"""

    urls = extract_urls_from_markdown(sample_markdown)
    print("Extracted URLs:")
    for url in urls:
        print(f"  - {url}")