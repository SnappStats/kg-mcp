"""
Scout Report Function Schema Definition
Defines the structured output schema using Gemini function calling
"""

from google.genai import types

SCOUT_REPORT_FUNCTION = types.FunctionDeclaration(
    name="submit_scout_report",
    description="Submit the completed scout report with all researched information",
    parameters={
        "type": "object",
        "properties": {
            "status": {
                "type": "string",
                "enum": ["success", "ambiguous", "not_found"],
                "description": "Status of the research - success if player found, ambiguous if multiple matches, not_found if no matches"
            },
            "feedback_message": {
                "type": "string",
                "description": "If status is ambiguous or not_found, provide the feedback message for the user"
            },
            "player_identity": {
                "type": "object",
                "properties": {
                    "full_name": {"type": "string"},
                    "current_high_school": {"type": "string"},
                    "city": {"type": "string"},
                    "state": {"type": "string"},
                    "team_name": {"type": "string"},
                    "position": {"type": "array", "items": {"type": "string"}},
                    "graduation_class": {"type": "integer"},
                    "previous_high_schools": {"type": "array", "items": {"type": "string"}},
                    "twitter_handle": {"type": "string"},
                    "instagram_handle": {"type": "string"}
                },
                "description": "Basic player identity information"
            },
            "recruiting_profile": {
                "type": "object",
                "properties": {
                    "star_ratings": {
                        "type": "object",
                        "properties": {
                            "two47_sports": {"type": "number"},
                            "on3": {"type": "number"},
                            "espn": {"type": "number"},
                            "rivals": {"type": "number"},
                            "composite_score": {"type": "number"}
                        }
                    },
                    "rankings": {
                        "type": "object",
                        "properties": {
                            "national": {"type": "string"},
                            "position": {"type": "string"},
                            "state": {"type": "string"}
                        }
                    },
                    "scholarship_offers": {
                        "type": "object",
                        "properties": {
                            "elite_cfp": {"type": "array", "items": {"type": "string"}},
                            "power5": {"type": "array", "items": {"type": "string"}},
                            "group_of_5": {"type": "array", "items": {"type": "string"}},
                            "fcs": {"type": "array", "items": {"type": "string"}},
                            "total_count": {"type": "integer"}
                        }
                    },
                    "latest_offer": {
                        "type": "object",
                        "properties": {
                            "school": {"type": "string"},
                            "date": {"type": "string"}
                        }
                    },
                    "visits": {
                        "type": "object",
                        "properties": {
                            "official": {"type": "array", "items": {
                                "type": "object",
                                "properties": {
                                    "school": {"type": "string"},
                                    "date": {"type": "string"}
                                }
                            }},
                            "unofficial": {"type": "array", "items": {
                                "type": "object",
                                "properties": {
                                    "school": {"type": "string"},
                                    "date": {"type": "string"}
                                }
                            }}
                        }
                    },
                    "top_schools": {"type": "array", "items": {"type": "string"}},
                    "nil_valuation": {"type": "string"},
                    "enrollment_plan": {"type": "string"},
                    "family_connections": {"type": "array", "items": {"type": "string"}}
                },
                "description": "Recruiting profile and college interest"
            },
            "physical_athletic_profile": {
                "type": "object",
                "properties": {
                    "measurements": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "height": {"type": "string"},
                                "weight": {"type": "string"},
                                "wingspan": {"type": "string"},
                                "hand_size": {"type": "string"},
                                "source": {"type": "string"},
                                "date": {"type": "string"}
                            }
                        }
                    },
                    "athletic_testing": {
                        "type": "object",
                        "properties": {
                            "forty_yard_dash": {"type": "array", "items": {
                                "type": "object",
                                "properties": {
                                    "time": {"type": "string"},
                                    "source": {"type": "string"},
                                    "date": {"type": "string"}
                                }
                            }},
                            "vertical_jump": {"type": "string"},
                            "broad_jump": {"type": "string"},
                            "shuttle": {"type": "string"},
                            "bench_press": {"type": "string"},
                            "squat": {"type": "string"},
                            "power_clean": {"type": "string"}
                        }
                    },
                    "camp_performances": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "camp_name": {"type": "string"},
                            "date": {"type": "string"},
                            "performance": {"type": "string"},
                            "awards": {"type": "array", "items": {"type": "string"}}
                        }
                    }},
                    "other_sports": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "sport": {"type": "string"},
                            "level": {"type": "string"},
                            "years": {"type": "string"},
                            "achievements": {"type": "string"}
                        }
                    }}
                },
                "description": "Physical measurements and athletic testing results"
            },
            "performance_stats": {
                "type": "object",
                "properties": {
                    "yearly_stats": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "year": {"type": "string"},
                                "school": {"type": "string"},
                                "stats": {"type": "object"},
                                "games_played": {"type": "integer"}
                            }
                        }
                    },
                    "standout_performances": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "opponent": {"type": "string"},
                                "date": {"type": "string"},
                                "stats": {"type": "string"},
                                "game_result": {"type": "string"},
                                "context": {"type": "string"}
                            }
                        }
                    },
                    "awards": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "award": {"type": "string"},
                                "year": {"type": "string"}
                            }
                        }
                    },
                    "team_records": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "year": {"type": "string"},
                                "school": {"type": "string"},
                                "record": {"type": "string"},
                                "playoffs": {"type": "string"},
                                "championships": {"type": "string"}
                            }
                        }
                    },
                    "competition_level": {
                        "type": "object",
                        "properties": {
                            "classification": {"type": "string"},
                            "conference": {"type": "string"},
                            "conference_strength": {"type": "string"},
                            "notable_opponents": {"type": "array", "items": {"type": "string"}},
                            "d1_teammates": {"type": "array", "items": {"type": "string"}}
                        }
                    }
                },
                "description": "On-field performance statistics and team context"
            },
            "intangibles": {
                "type": "object",
                "properties": {
                    "character_notes": {"type": "array", "items": {"type": "string"}},
                    "leadership_examples": {"type": "array", "items": {"type": "string"}},
                    "academic_info": {
                        "type": "object",
                        "properties": {
                            "gpa": {"type": "string"},
                            "academic_awards": {"type": "array", "items": {"type": "string"}},
                            "school_reputation": {"type": "string"}
                        }
                    },
                    "scout_projection": {"type": "string"},
                    "player_comparisons": {"type": "array", "items": {
                        "type": "object",
                        "properties": {
                            "player": {"type": "string"},
                            "reason": {"type": "string"},
                            "source": {"type": "string"}
                        }
                    }},
                    "social_media_concerns": {"type": "array", "items": {"type": "string"}},
                    "social_media_positives": {"type": "array", "items": {"type": "string"}}
                },
                "description": "Character, leadership, academic profile, and projections"
            },
            "sources": {
                "type": "array",
                "items": {"type": "string"},
                "description": "All sources used in the research"
            }
        },
        "required": ["status"]
    }
)

RESEARCH_PROMPT = '''
You are a scout report researcher for coaching staff making recruiting decisions. Quality and credibility are CRITICAL.

**YOUR WORKFLOW:**
1. Use grounded search to research the player thoroughly
2. Determine if you found an exact match, multiple matches, or no matches
3. Call the submit_scout_report function with ALL the information you found

**CRITICAL INSTRUCTIONS:**
* Perform comprehensive online searches for current information
* If you find an EXACT MATCH → research thoroughly and call submit_scout_report with status="success"
* If you find MULTIPLE possible players → call submit_scout_report with status="ambiguous" and list all candidates in feedback_message
* If you CANNOT find the player → call submit_scout_report with status="not_found" and explain what you searched in feedback_message

**RESEARCH REQUIREMENTS:**
* Validate the player's current or final high school (some sources like Hudl may list training academies)
* Check for any high school transfers during their career
* Use sport-specific authoritative sources (247Sports, On3, ESPN, Rivals for recruiting; Athletic.net for track, etc.)
* NEVER use Wikipedia as a primary source - find the original sources instead
* For high school stats, prioritize: official school sites → state athletic associations → then MaxPreps/aggregators
* Check the player's social media (Twitter/X, Instagram) for self-reported offers and character insights

**WHEN CALLING submit_scout_report:**
* Fill in ALL fields that you have information for
* Leave fields as null if no information was found (don't make up data)
* For arrays, use empty arrays [] if nothing found
* Include specific dates, sources, and context wherever possible
* List all sources used at the end

The function will structure your research into a proper scout report format. Focus on gathering comprehensive, accurate, and well-sourced information.
'''
