"""
Process inline citations to convert source names to numbered references
"""

import re
from typing import Dict, List, Any, Tuple


def process_inline_citations(scout_report: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert inline source citations to numbered references.

    Converts: "He is the #1 recruit [247Sports, On3]"
    To: "He is the #1 recruit [1,2]"

    And creates a numbered citations list at the end.
    """

    # Get the citations list (URLs)
    citations_urls = scout_report.get('citations', [])

    # Create a mapping from source names to citation numbers
    source_to_urls = {}
    source_to_number = {}

    # Common source name patterns to look for
    source_patterns = [
        r'247Sports', r'On3', r'ESPN', r'Rivals', r'MaxPreps',
        r'Gatorade(?:\.com)?', r'Wikipedia', r'Twitter', r'Instagram',
        r'YouTube', r'The Athletic', r'MLive', r'Yahoo(?:\sSports)?',
        r'SI(?:\.com)?', r'USA Today', r'Bleacher Report', r'CBS Sports',
        r'NBC Sports', r'Fox Sports', r'NFL\.com', r'NBA\.com'
    ]

    # Map URLs to source names
    for i, url in enumerate(citations_urls, 1):
        url_lower = url.lower()

        # Match URLs to source names
        if '247sports.com' in url_lower:
            source_to_urls.setdefault('247Sports', []).append(i)
        elif 'on3.com' in url_lower:
            source_to_urls.setdefault('On3', []).append(i)
        elif 'espn.com' in url_lower:
            source_to_urls.setdefault('ESPN', []).append(i)
        elif 'rivals.com' in url_lower:
            source_to_urls.setdefault('Rivals', []).append(i)
        elif 'maxpreps.com' in url_lower:
            source_to_urls.setdefault('MaxPreps', []).append(i)
        elif 'gatorade' in url_lower:
            source_to_urls.setdefault('Gatorade', []).append(i)
        elif 'wikipedia' in url_lower:
            source_to_urls.setdefault('Wikipedia', []).append(i)
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            source_to_urls.setdefault('Twitter', []).append(i)
        elif 'instagram.com' in url_lower:
            source_to_urls.setdefault('Instagram', []).append(i)
        elif 'youtube.com' in url_lower:
            source_to_urls.setdefault('YouTube', []).append(i)
        elif 'theathletic.com' in url_lower or 'nytimes.com/athletic' in url_lower:
            source_to_urls.setdefault('The Athletic', []).append(i)
        elif 'mlive.com' in url_lower:
            source_to_urls.setdefault('MLive', []).append(i)
        elif 'yahoo.com' in url_lower:
            source_to_urls.setdefault('Yahoo Sports', []).append(i)
        elif 'si.com' in url_lower:
            source_to_urls.setdefault('SI', []).append(i)
        elif 'usatoday.com' in url_lower:
            source_to_urls.setdefault('USA Today', []).append(i)

    # Assign first URL number for each source
    for source, url_numbers in source_to_urls.items():
        if url_numbers:
            source_to_number[source] = url_numbers[0]

    # Process sections - works for both 'analysis' array and 'sections' array
    if 'sections' in scout_report:
        processed_sections = []

        for item in scout_report['sections']:
            content = item.get('content', '')

            # Find all bracketed citations in the content
            citation_pattern = r'\[([^\]]+)\]'

            def replace_citation(match):
                citation_text = match.group(1)

                # Skip if it looks like it's already numbered
                if re.match(r'^[\d,\s-]+$', citation_text):
                    return match.group(0)

                # Split by comma and process each source
                sources = [s.strip() for s in citation_text.split(',')]
                numbers = []

                for source in sources:
                    # Try to match against known sources
                    matched = False
                    for pattern in source_patterns:
                        if re.search(pattern, source, re.IGNORECASE):
                            # Get the canonical source name
                            for canonical_name in source_to_number.keys():
                                if re.search(pattern, canonical_name, re.IGNORECASE):
                                    numbers.append(str(source_to_number[canonical_name]))
                                    matched = True
                                    break
                            if matched:
                                break

                    # If no match, try exact match
                    if not matched and source in source_to_number:
                        numbers.append(str(source_to_number[source]))

                # Return the numbered citation or original if no matches
                if numbers:
                    return f"[{','.join(numbers)}]"
                else:
                    return match.group(0)

            # Replace all citations in the content
            processed_content = re.sub(citation_pattern, replace_citation, content)

            processed_sections.append({
                'title': item.get('title', ''),
                'content': processed_content
            })

        scout_report['sections'] = processed_sections

    # Also handle 'analysis' for backward compatibility
    elif 'analysis' in scout_report:
        processed_analysis = []

        for item in scout_report['analysis']:
            content = item.get('content', '')

            # Find all bracketed citations in the content
            citation_pattern = r'\[([^\]]+)\]'

            def replace_citation(match):
                citation_text = match.group(1)

                # Skip if it looks like it's already numbered
                if re.match(r'^[\d,\s-]+$', citation_text):
                    return match.group(0)

                # Split by comma and process each source
                sources = [s.strip() for s in citation_text.split(',')]
                numbers = []

                for source in sources:
                    # Try to match against known sources
                    matched = False
                    for pattern in source_patterns:
                        if re.search(pattern, source, re.IGNORECASE):
                            # Get the canonical source name
                            for canonical_name in source_to_number.keys():
                                if re.search(pattern, canonical_name, re.IGNORECASE):
                                    numbers.append(str(source_to_number[canonical_name]))
                                    matched = True
                                    break
                            if matched:
                                break

                    # If no match, try exact match
                    if not matched and source in source_to_number:
                        numbers.append(str(source_to_number[source]))

                # Return the numbered citation or original if no matches
                if numbers:
                    return f"[{','.join(numbers)}]"
                else:
                    return match.group(0)

            # Replace all citations in the content
            processed_content = re.sub(citation_pattern, replace_citation, content)

            processed_analysis.append({
                'title': item.get('title', ''),
                'content': processed_content
            })

        scout_report['analysis'] = processed_analysis

    # Create numbered citations list with numbers
    numbered_citations = []
    for i, url in enumerate(citations_urls, 1):
        numbered_citations.append(f"[{i}] {url}")

    scout_report['citations'] = numbered_citations

    return scout_report


# Test the processor
if __name__ == "__main__":
    sample_report = {
        "analysis": [
            {
                "title": "Recruiting Rankings",
                "content": "Bryce is the #1 overall recruit [247Sports, On3] with a perfect 100 score [On3]."
            },
            {
                "title": "Stats",
                "content": "Posted 3,329 yards [MaxPreps] and won state championship [ESPN coverage]."
            }
        ],
        "citations": [
            "https://247sports.com/player/bryce",
            "https://on3.com/player/bryce",
            "https://maxpreps.com/athlete/bryce",
            "https://espn.com/bryce-championship"
        ]
    }

    processed = process_inline_citations(sample_report)

    print("Processed Analysis:")
    for item in processed['analysis']:
        print(f"\n{item['title']}:")
        print(item['content'])

    print("\nNumbered Citations:")
    for citation in processed['citations']:
        print(citation)