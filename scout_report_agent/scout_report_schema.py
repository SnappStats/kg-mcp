from typing import Optional, List, Dict, Union, Any
from pydantic import BaseModel, Field, AliasPath # AliasPath needed for executive_summary alias

# --- Sub Models ---

class TeamProfile(BaseModel):
    """Details about the player's high school team and recruiting environment."""
    # All fields default to None or empty string
    high_school_team: Optional[str] = Field(
        None, description="Name of the high school team."
    )
    coach: Optional[str] = Field(None, description="Name of the high school coach.")
    conference: Optional[str] = Field(None, description="Team conference or league name.")
    recruitment_breakdown: Optional[str] = Field(
        None,
        description="Complex string detailing the number of players recruited by division, star rating, and player names on his team."
    )

class Rankings(BaseModel):
    """Official rankings and accolades from major scouting sources."""
    # Collections default to empty list/dict
    accolades: List[str] = Field(
        default_factory=list,
        description="General accolades and honors (e.g., All-State, Team MVP)."
    )
    source_rankings: Dict[str, Optional[Union[str, int]]] = Field(
        default_factory=dict,
        description="Mapping of scouting sources to the player's rank/rating (e.g., {'247sports': '4-star, #5 QB', 'espn': '85 rating'})."
    )

class Statistics(BaseModel):
    """Detailed season statistics and game performance data."""
    # Collections default to empty dict/list
    season_stats: Dict[str, Union[str, float, int]] = Field(
        default_factory=dict,
        description="Key season statistics (e.g., {'Passing Yards': 3200, 'Touchdowns': 35})."
    )
    key_games_outcomes: List[str] = Field(
        default_factory=list,
        description="Summary of key game performances and outcomes (e.g., 'Championship Game: 4 TDs, 300 yards, Win')."
    )

class PublicPerception(BaseModel):
    """Media and public view of the player."""
    # Collections default to empty list
    articles_beat_writers: List[str] = Field(
        default_factory=list,
        description="Links or summaries of articles and mentions by beat writers."
    )
    highlight_reels: Optional[str] = Field(
        None, description="Note on where highlight reels can be found (e.g., 'User to upload, see Hudl link')."
    )

class ExternalLinks(BaseModel):
    """Links to external profile platforms and social media."""
    # All fields default to None
    hudl: Optional[str] = Field(None, description="URL link to the player's Hudl profile.")
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
    All fields are given default values (None, empty string, 0, or empty sub-model) to ensure they are always present.
    """
    # Core identifiers can still default to empty string or None if not strictly required
    player_name: str = ""
    school_name: str = Field(
        "", description="The formal name of the school attended."
    )

    # Summary
    executive_summary: str = Field(
        "",
        alias="TLDR",
        validation_alias=AliasPath("TLDR", "executive_summary"),
        description="A concise summary of the player's profile and potential.",
    )

    # Physical Characteristics
    height: str = Field("", description="Player height (e.g., 6'3\" or 1.91m).")
    weight: float = Field(0.0, description="Player weight in pounds or kilograms.")
    other_physical_characteristics: List[str] = Field(
        default_factory=list, description="Notable physical traits (e.g., 'wide shoulders', 'long arms')."
    )

    # Academics
    gpa: Optional[float] = Field(
        None, description="Player's current Grade Point Average."
    ) # Keeping as None default as 0.0 might be misleading

    # Team & Environment
    # Defaulting to an instance of the sub-model, which itself has defaults
    team_profile: TeamProfile = Field(default_factory=TeamProfile)

    # Athletic Profile
    athlete_characteristics: List[str] = Field(
        default_factory=list,
        description="Key athletic attributes (e.g., 'elite speed', 'high football IQ', 'leader')."
    )

    # Awards and Recognition
    rankings_accolades: Rankings = Field(default_factory=Rankings)

    # Recruiting Status
    offers_commits: List[str] = Field(
        default_factory=list,
        description="List of committed and offered colleges (e.g., ['Offer: USC', 'Commit: Ohio State']).",
    )
    conference_awards: List[str] = Field(
        default_factory=list,
        description="Specific awards received at the conference level (e.g., 'First Team All-Conference')."
    )

    # Performance
    statistics: Statistics = Field(default_factory=Statistics)

    # External Data
    perception: PublicPerception = Field(default_factory=PublicPerception)
    external_links: ExternalLinks = Field(default_factory=ExternalLinks)
