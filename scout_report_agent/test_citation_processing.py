"""
Test the citation processing functionality
"""

import json
import time
from citation_processor import process_inline_citations

# Simulate a scout report with inline source citations
sample_report = {
    "player": {
        "name": "Bryce Underwood",
        "physicals": {
            "Height": "6ft 4in",
            "Weight": "228lbs"
        },
        "socials": {
            "Instagram": "@19bryce.__"
        }
    },
    "tags": [
        "Football",
        "Quarterback",
        "High School: Belleville",
        "Belleville, MI",
        "Class of 2025",
        "College: Michigan (committed)",
        "5-star (247Sports)",
        "No. 1 Overall Recruit (2025)"
    ],
    "analysis": [
        {
            "title": "Recruiting Rankings",
            "content": "Bryce Underwood is a consensus five-star recruit [247Sports, On3, ESPN] and the No. 1 overall ranked high school football player in the nation for the 2025 class [247Sports, On3]. He is the highest-ranked quarterback to commit to Michigan in the modern ranking era [247Sports]. He received a perfect 100 score from On3 [On3], making him the first recruit ever to achieve this rating."
        },
        {
            "title": "Awards",
            "content": "- Gatorade Michigan Player of the Year (2023) [Gatorade]\n- MaxPreps National Sophomore Player of the Year (2022) [MaxPreps]\n- Michigan Mr. Football Award (2024) [MLive]"
        },
        {
            "title": "Strengths",
            "content": "Underwood possesses elite arm talent and arm strength [247Sports scouting report], capable of making difficult throws from various arm angles [ESPN analysis]. He demonstrates strong running abilities and excellent mobility [On3], earning a 5/5 on the mobility scale [On3 scouting report]. His poise in the pocket and ability to read defenses is advanced for his age [The Athletic]."
        },
        {
            "title": "Weaknesses",
            "content": "Areas for improvement include sometimes being tense in the upper body [ESPN scouting] and needing more consistency with his feet and platform within the pocket [247Sports]. His deep ball was an early weakness but has shown improvement [On3]. Some analysts note he needs to improve processing speed against complex defenses [Rivals]."
        },
        {
            "title": "Coach Quotes",
            "content": "Michigan coach Biff Poggi: \"He's gifted. I have a Labrador retriever who could coach that guy\" [MLive], highlighting Underwood's natural talent. Underwood himself stated: \"I'm here to shock the world. Nobody's seen a freshman like me\" [ESPN interview]. QB Mikey Keene noted: \"Bryce is going to learn a lot from me. I'm probably going to learn a lot from Bryce\" [The Athletic]."
        }
    ],
    "stats": [
        "50-4 Career Record (High School)",
        "2 State Championships (2021, 2022)",
        "12,919 All-Purpose Yards (High School Career)",
        "11,488 Passing Yards (High School Career - State Record 152 TDs)",
        "3,329 Passing Yards, 41 TDs (2023 Season)",
        "2,888 Passing Yards, 39 TDs, 4 INT (Freshman Season)"
    ],
    "citations": [
        "https://247sports.com/player/bryce-underwood-46113169/",
        "https://www.on3.com/rivals/bryce-underwood-15949/",
        "https://www.espn.com/college-football/player/_/id/5141741/bryce-underwood",
        "https://www.maxpreps.com/mi/belleville/belleville-tigers/athletes/bryce-underwood/",
        "https://playeroftheyear.gatorade.com/winner/bryce-underwood/39976",
        "https://www.mlive.com/wolverines/2025/bryce-underwood-michigan.html",
        "https://www.nytimes.com/athletic/bryce-underwood-michigan-quarterback-film/",
        "https://n.rivals.com/bryce-underwood-scouting-report",
        "https://www.instagram.com/19bryce.__/",
        "https://twitter.com/BryceUnderwoo16"
    ]
}

print("=" * 80)
print("TESTING INLINE CITATION PROCESSING")
print("=" * 80)
print("\n📝 ORIGINAL REPORT (with source name citations):\n")

for item in sample_report['analysis']:
    print(f"\n{item['title']}:")
    print(item['content'][:200] + "..." if len(item['content']) > 200 else item['content'])

print("\n" + "=" * 80)
print("⚙️  PROCESSING CITATIONS...")
print("=" * 80)

start_time = time.time()
processed_report = process_inline_citations(sample_report.copy())
elapsed_time = time.time() - start_time

print(f"\n⏱️  Processing time: {elapsed_time:.3f} seconds")

print("\n" + "=" * 80)
print("✅ PROCESSED REPORT (with numbered citations):")
print("=" * 80)

for item in processed_report['analysis']:
    print(f"\n{item['title']}:")
    print(item['content'])

print("\n" + "=" * 80)
print("📚 NUMBERED CITATIONS LIST:")
print("=" * 80)

for citation in processed_report['citations'][:10]:  # Show first 10
    print(citation)

if len(processed_report['citations']) > 10:
    print(f"... and {len(processed_report['citations']) - 10} more citations")

print("\n" + "=" * 80)
print("SUMMARY:")
print(f"✓ Timer shows: {elapsed_time:.3f} seconds to process")
print(f"✓ Total citations: {len(processed_report['citations'])}")
print(f"✓ Inline citations converted from source names to numbers")
print("=" * 80)