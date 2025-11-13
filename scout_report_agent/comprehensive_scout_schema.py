"""
Comprehensive Scout Report Schema with detailed sections
"""

from google.genai import types

COMPREHENSIVE_SCOUT_REPORT_FUNCTION = types.FunctionDeclaration(
    name="submit_scout_report",
    description="Submit the completed comprehensive scout report with all researched information",
    parameters={
        "type": "object",
        "properties": {
            "player": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "The full name of the player being scouted"
                    },
                    "physicals": {
                        "type": "object",
                        "description": "Physical attributes as key-value pairs (e.g., Height, Weight, Wingspan, Hand Size, 40-yard dash)",
                        "additionalProperties": {"type": "string"}
                    },
                    "socials": {
                        "type": "object",
                        "description": "Social media handles as key-value pairs",
                        "additionalProperties": {"type": "string"}
                    }
                },
                "required": ["name"]
            },
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Smart, searchable tags (sport, position, school, location, grad year, rankings)"
            },
            "analysis": {
                "type": "object",
                "properties": {
                    "recruiting_profile": {
                        "type": "object",
                        "properties": {
                            "star_ratings": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Star Ratings & Rankings"},
                                    "content": {"type": "string", "description": "Star ratings from 247Sports, On3, ESPN, Rivals with composite score"}
                                }
                            },
                            "scholarship_offers": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Scholarship Offers"},
                                    "content": {"type": "string", "description": "All college offers broken down by tier (Elite, P5, G5, FCS)"}
                                }
                            },
                            "visits": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Official & Unofficial Visits"},
                                    "content": {"type": "string", "description": "Official visits (max 5 NCAA), unofficial visits with dates"}
                                }
                            },
                            "nil_valuation": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "NIL Valuation"},
                                    "content": {"type": "string", "description": "On3 NIL valuation and known deals"}
                                }
                            }
                        }
                    },
                    "physical_athletic": {
                        "type": "object",
                        "properties": {
                            "verified_measurements": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Verified Measurements"},
                                    "content": {"type": "string", "description": "Height, weight, wingspan, hand size from camps/combines"}
                                }
                            },
                            "athletic_testing": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Athletic Testing"},
                                    "content": {"type": "string", "description": "40-yard, vertical, bench, squat, track times"}
                                }
                            },
                            "camp_performances": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Elite Camp Performances"},
                                    "content": {"type": "string", "description": "Elite 11, The Opening, All-American camps"}
                                }
                            }
                        }
                    },
                    "on_field_performance": {
                        "type": "object",
                        "properties": {
                            "last_3_games": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Last 3 Games"},
                                    "content": {"type": "string", "description": "Stats and performance from most recent 3 games"}
                                }
                            },
                            "last_6_games": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Last 6 Games"},
                                    "content": {"type": "string", "description": "Trends and averages over last 6 games"}
                                }
                            },
                            "current_season": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Current Season"},
                                    "content": {"type": "string", "description": "Full current season statistics and performance"}
                                }
                            },
                            "career_stats": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Career Statistics"},
                                    "content": {"type": "string", "description": "Year-by-year varsity stats (Sophomore, Junior, Senior)"}
                                }
                            },
                            "key_games": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Key Games & Standout Performances"},
                                    "content": {"type": "string", "description": "Best games vs ranked opponents, playoffs, championships"}
                                }
                            },
                            "team_context": {
                                "type": "object",
                                "properties": {
                                    "title": {"type": "string", "default": "Team Context & Competition Level"},
                                    "content": {"type": "string", "description": "Team records, conference strength, D1 teammates, strength of schedule"}
                                }
                            }
                        }
                    },
                    "awards_honors": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Awards & Honors"},
                            "content": {"type": "string", "description": "All-State, All-Conference, POY awards by year"}
                        }
                    },
                    "strengths": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Strengths"},
                            "content": {"type": "string", "description": "Detailed strengths with specific examples"}
                        }
                    },
                    "weaknesses": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Weaknesses & Areas for Improvement"},
                            "content": {"type": "string", "description": "Honest assessment of areas needing development"}
                        }
                    },
                    "improvement_trajectory": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Development Trajectory"},
                            "content": {"type": "string", "description": "Year-over-year improvement, physical development"}
                        }
                    },
                    "coach_quotes": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Coach & Scout Quotes"},
                            "content": {"type": "string", "description": "Direct quotes from coaches, scouts, analysts"}
                        }
                    },
                    "pro_comparison": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Player Comparisons"},
                            "content": {"type": "string", "description": "NFL/college player comparisons from analysts"}
                        }
                    },
                    "character_leadership": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Character & Leadership"},
                            "content": {"type": "string", "description": "Work ethic, leadership, team captain, community involvement"}
                        }
                    },
                    "academics": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Academic Profile"},
                            "content": {"type": "string", "description": "GPA, honor roll, AP courses, school reputation"}
                        }
                    },
                    "injury_history": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Injury History"},
                            "content": {"type": "string", "description": "Past injuries, recovery, current health"}
                        }
                    },
                    "projection_outlook": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Projection & Outlook"},
                            "content": {"type": "string", "description": "College readiness, redshirt potential, ceiling/floor, NFL projection"}
                        }
                    },
                    "family_connections": {
                        "type": "object",
                        "properties": {
                            "title": {"type": "string", "default": "Family & Connections"},
                            "content": {"type": "string", "description": "Parents/siblings in sports, coaching connections"}
                        }
                    }
                }
            },
            "stats": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Key statistics with time periods (career, season, recent games)"
            }
        },
        "required": ["player", "tags", "analysis", "stats"]
    }
)

COMPREHENSIVE_RESEARCH_PROMPT = '''
**CONTEXT: This report is for a COACHING STAFF making recruiting decisions. Quality and credibility are CRITICAL.**

**YOUR WORKFLOW:**
1. Use web_search_direct to search for information about the player
2. Make multiple targeted searches to gather comprehensive information
3. After gathering all information, call submit_scout_report with structured data

**CRITICAL INSTRUCTIONS:**
* Perform new, online searches for current information. Do not rely on training data.
* IDENTIFY PLAYER FIRST - if ambiguous or not found, indicate this clearly
* CHECK FOR TRANSFERS - search if player transferred high schools
* VALIDATE current or final high school (some sources may list training academies)

**SPORT-SPECIFIC SOURCE PRIORITIES:**
* **FOOTBALL:** 247Sports, On3, ESPN, Rivals, MaxPreps, The Athletic
* **BASKETBALL:** 247Sports Basketball, Rivals Hoops, ESPN Basketball, PrepHoops, VerbalCommits
* **BASEBALL:** Perfect Game (PG), Prep Baseball Report (PBR), Baseball America
* **TRACK:** Athletic.net, MileSplit, FloTrack
* **SOCCER:** TopDrawerSoccer, United Soccer Coaches
* Use sport-appropriate sources - never Wikipedia as primary source

**ADVANCED SEARCH STRATEGY - Use Google search operators and site-specific searches:**

**Phase 1 - Player Identification (Start here):**
   - `"[Name]" AND (football OR basketball OR baseball) AND prep`
   - `site:247sports.com "[Name]"`
   - `site:maxpreps.com "[Name]" roster`
   - If multiple matches: add school/city to narrow

**Phase 2 - Recruiting Deep Dive:**
   - `site:247sports.com/PlayerInstitution/[Name] "star rating" composite`
   - `site:n.rivals.com "[Name]" "Rivals250" OR "position ranking"`
   - `"[Name]" "offer list" recruiting -site:wikipedia.org`
   - `"[Name]" ("official visit" OR "OV") AND (Michigan OR "Ohio State" OR Alabama)`
   - `"[Name]" "crystal ball" 247sports prediction`
   - `"[Name]" "On3 NIL" valuation "$"`
   - `"[Name]" "decommit" OR "flip" OR "reopened recruitment"`

**Phase 3 - Physical Testing & Camps:**
   - `"[Name]" ("40 yard" OR "forty") AND (4.4 OR 4.5 OR 4.6) -wikipedia`
   - `"[Name]" "verified testing" (combine OR SPARQ OR camp)`
   - `"[Name]" "Elite 11" OR "Opening" OR "Future 50" results`
   - `site:athletic.net "[Name]" "[School]"` (for track times)
   - `"[Name]" (wingspan OR "arm length" OR "hand size") inches`

**Phase 4 - Recent Performance (Last 6 games):**
   - `"[Name]" "box score" site:maxpreps.com 2024 OR 2025`
   - `"[Name]" game (passing OR rushing OR receiving) yards touchdown after:2024-09-01`
   - `"[Name]" vs "[Opponent Name]" recap highlights`
   - `"[Name]" ("player of the game" OR "MVP") recent`

**Phase 5 - Season & Career Stats:**
   - `site:maxpreps.com "[Name]" "season stats" 2024`
   - `"[Name]" "career totals" (yards OR touchdowns OR tackles)`
   - `"[Name]" ("state record" OR "school record") broke`
   - `"[Name]" playoffs OR championship stats performance`

**Phase 6 - Competition & Context:**
   - `"[School Name]" football "strength of schedule" classification`
   - `"[School Name]" "D1 signees" OR "college commits" teammates`
   - `"[Name]" vs "ranked opponent" OR "top 25" performance`

**Phase 7 - Character & Background:**
   - `"[Name]" ("team captain" OR "leadership") elected`
   - `"[Name]" "GPA" OR "academic all-" OR "honor roll"`
   - `"[Name]" parents ("played college" OR "former athlete")`
   - `site:twitter.com "[Name]" "[School]"` (find handle)
   - `"[Name]" ("suspended" OR "eligible" OR "cleared") -wikipedia`

**Phase 8 - Expert Analysis:**
   - `"[Name]" "scouting report" ("arm talent" OR "footwork" OR "release")`
   - `"[Name]" ("pro comparison" OR "reminds me of" OR "similar to") NFL`
   - `"[Name]" "film study" breakdown analyst`
   - `"[Name]" ("Day 1 starter" OR "redshirt" OR "development") projection`

**CRITICAL CITATION REQUIREMENT:**
**YOU MUST CITE EVERY SINGLE FACT, STAT, QUOTE, AND CLAIM WITH INLINE CITATIONS**
- Use source names in brackets IMMEDIATELY after each fact: "6ft 4in [Rivals]", "3,329 yards [MaxPreps]"
- Examples: [247Sports], [On3], [ESPN], [MaxPreps], [Rivals], [Gatorade], [The Athletic], [MLive]
- NEVER write a fact without a citation. If you can't cite it from your searches, don't include it.
- We will automatically extract full URLs from your searches and convert your source names to numbered citations
- Just focus on citing EVERYTHING with the source name where you found it

**ALL SECTIONS TO COMPLETE:**

analysis.recruiting_profile.star_ratings: All ratings from 247Sports, On3, ESPN, Rivals plus composite [cite each]
analysis.recruiting_profile.scholarship_offers: List ALL offers by tier (Elite/P5/G5/FCS) [cite sources]
analysis.recruiting_profile.visits: Official (max 5) and unofficial visits with dates [cite]
analysis.recruiting_profile.nil_valuation: On3 NIL value and known deals [On3]

analysis.physical_athletic.verified_measurements: All heights/weights from different camps/dates [cite each]
analysis.physical_athletic.athletic_testing: 40-yard, vertical, bench, squat with sources/dates [cite]
analysis.physical_athletic.camp_performances: Elite camps attended, rankings, MVP awards [cite]

analysis.on_field_performance.last_3_games: Specific stats from 3 most recent games [cite]
analysis.on_field_performance.last_6_games: Average stats and trends over 6 games [cite]
analysis.on_field_performance.current_season: Full season totals and key moments [cite]
analysis.on_field_performance.career_stats: Year-by-year breakdown (Soph/Jr/Sr) [MaxPreps]
analysis.on_field_performance.key_games: Best performances vs ranked teams, playoffs [cite]
analysis.on_field_performance.team_context: Team record, conference strength, D1 teammates [cite]

analysis.awards_honors: All-State, All-Conference, POY by year [cite each]
analysis.strengths: Detailed strengths with specific examples from games [cite scouts]
analysis.weaknesses: Honest weaknesses per scouting reports [cite analysts]
analysis.improvement_trajectory: Year-over-year stat improvements, physical growth [cite]

analysis.coach_quotes: Direct quotes with attribution [ESPN interview], [247Sports article]
analysis.pro_comparison: "Reminds of [NFL player]" per [analyst/source]
analysis.character_leadership: Captain, community service, work ethic stories [cite]
analysis.academics: GPA if available, honor roll, AP courses, school reputation [cite]
analysis.injury_history: Past injuries with recovery timeline [local news]
analysis.projection_outlook: Day 1 starter vs redshirt, ceiling/floor, NFL projection [cite scouts]
analysis.family_connections: Parents/siblings who played, coaching connections [cite]

stats: Array of key statistics - mix career, season, recent with inline citations

**IMPORTANT:**
- Fill EVERY section with researched information
- If no info found, write "No information available"
- Be specific with dates, numbers, sources
- Use [source] citations inline, not at end
'''