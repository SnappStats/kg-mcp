from google.adk.agents import Agent
from google.adk.planners import BuiltInPlanner
from google.genai import types

from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional, Dict, Union

# --- Nested Models for Structure ---

class TeamProfile(BaseModel):
    """Details about the player's high school team and recruiting environment."""
    high_school_team: str = Field(description="Name of the high school team.")
    coach: Optional[str] = Field(None, description="Name of the high school coach.")
    conference: Optional[str] = Field(None, description="Team conference or league name.")
    recruitment_breakdown: Optional[str] = Field(
        None,
        description="Complex string detailing the number of players recruited by division, star rating, and player names on his team."
    )

class Rankings(BaseModel):
    """Official rankings and accolades from major scouting sources."""
    accolades: List[str] = Field(description="General accolades and honors (e.g., All-State, Team MVP).")
    source_rankings: Dict[str, Optional[Union[str, int]]] = Field(
        description="Mapping of scouting sources to the player's rank/rating (e.g., {'247sports': '4-star, #5 QB', 'espn': '85 rating'})."
    )

class Statistics(BaseModel):
    """Detailed season statistics and game performance data."""
    season_stats: Dict[str, Union[str, float, int]] = Field(
        description="Key season statistics (e.g., {'Passing Yards': 3200, 'Touchdowns': 35})."
    )
    key_games_outcomes: List[str] = Field(
        description="Summary of key game performances and outcomes (e.g., 'Championship Game: 4 TDs, 300 yards, Win')."
    )

class PublicPerception(BaseModel):
    """Media and public view of the player."""
    articles_beat_writers: List[str] = Field(
        description="Links or summaries of articles and mentions by beat writers."
    )
    highlight_reels: Optional[str] = Field(
        None, description="Note on where highlight reels can be found (e.g., 'User to upload, see Hudl link')."
    )

class ExternalLinks(BaseModel):
    """Links to external profile platforms and social media."""
    hudl: Optional[HttpUrl] = Field(None, description="URL link to the player's Hudl profile.")
    social_media: Optional[str] = Field(
        None, description="Social media handle or URL (e.g., Twitter/X handle)."
    )
    red_flags: Optional[str] = Field(
        None, description="Any known behavioral, injury, or academic red flags."
    )

# --- Main Model ---

class ScoutReport(BaseModel):
    """
    Pydantic schema for a comprehensive college football scout report (player profile).
    """
    player_name: str
    school_name: str = Field(description="The formal name of the school attended.")

    # Summary
    executive_summary: str = Field(
        alias="TLDR",
        description="A concise summary of the player's profile and potential.",
    )

    # Physical Characteristics
    height: str = Field(description="Player height (e.g., 6'3\" or 1.91m).")
    weight: float = Field(description="Player weight in pounds or kilograms.")
    other_physical_characteristics: Optional[List[str]] = Field(
        None, description="Notable physical traits (e.g., 'wide shoulders', 'long arms')."
    )

    # Academics
    gpa: Optional[float] = Field(None, description="Player's current Grade Point Average.")

    # Team & Environment
    team_profile: TeamProfile

    # Athletic Profile
    athlete_characteristics: List[str] = Field(
        description="Key athletic attributes (e.g., 'elite speed', 'high football IQ', 'leader')."
    )

    # Awards and Recognition
    rankings_accolades: Rankings

    # Recruiting Status
    offers_commits: List[str] = Field(
        description="List of committed and offered colleges (e.g., ['Offer: USC', 'Commit: Ohio State']).",
    )
    conference_awards: List[str] = Field(
        description="Specific awards received at the conference level (e.g., 'First Team All-Conference')."
    )

    # Performance
    statistics: Statistics

    # External Data
    perception: PublicPerception
    external_links: ExternalLinks


PROMPT = """Generate a Scout Report based on the provided information."""

agent = Agent(
    name="scout_report_agent",
    model="gemini-2.5-flash",
    description="Generates a Scout Report for a given player.",
    planner=BuiltInPlanner(
        thinking_config=types.ThinkingConfig(
            include_thoughts=False,
            thinking_budget=512,
        )
    ),
    output_schema=ScoutReport,
    instruction=PROMPT,
)
