from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class AnalysisItem(BaseModel):
    """
    Represents a single item of analysis (award, strength, weakness, quote).
    """
    title: str = Field(
        ...,
        description="The category or title of the analysis item (e.g., 'Awards', 'Strengths', 'Weaknesses', 'Coach Quotes')."
    )
    content: str = Field(
        ...,
        description="The detailed content of the item (e.g., specific weakness, the quotes itself), in markdown format."
    )


class Player(BaseModel):
    """
    Core demographic and identifying information for the player.
    """
    name: str = Field(
        ...,
        description="The full name of the player being scouted."
    )
    physicals: Dict[str, str] = Field(
        default_factory=dict,
        description="The player's key physical attributes (e.g., {'Height': '6ft 8in', 'Weight': '240lbs'})."
    )
    socials: Dict[str, str] = Field(
        default_factory=dict,
        description="A map of social media platform names to the player's handle/username."
    )
    hudl_profile: Optional[str] = Field(
        None,
        description="The player hudl.com profile url, e.g., https://www.hudl.com/profile/..."
    )
    highlighted_reel: Optional[str] = Field(
        None,
        description="The latest player highlight reel, IMPORTANT: ignore this field"
    )
    avatar_url: Optional[str] = Field(
        None,
        description="The player profile photo URL. Only include if a clear, valid facial photo of the player is available. Leave empty if no suitable photo exists or if the image quality is poor."
    )


class ScoutReport(BaseModel):
    """
    A comprehensive report detailing a player's profile, analysis, and statistics.
    """
    player: Player = Field(
        ...,
        description="The profile object containing the player's name and identifying details."
    )
    tags: List[str] = Field(
        default_factory=list,
        description="Smart, searchable tags that make sense for this player. Include what's relevant and important for filtering/searching. Examples of useful tags: sport, position, high school (with 'High School:' prefix), location (City, ST or City, Country), grad year, college status (with 'College:' prefix, add '(committed)' if not enrolled), star rating with source in parentheses, additional sports. Be smart and flexible."
    )
    analysis: List[AnalysisItem] = Field(
        default_factory=list,
        description="A list of analyses or opinions such as awards, rankings, strengths, and weaknesses."
    )
    stats: List[str] = Field(
        default_factory=list,
        description="A list of 3-6 key statistics - prioritize latest performance stats. Each stat should be a complete, self-explanatory statement with season/year. Format examples: '3,245 Passing Yards (2024/25)', '42 TD, 4 INT (2024/25)', '68.2% Completion (2024/25)'."
    )
    citations: List[str] = Field(
        default_factory=list,
        description="A list of urls from which this information was obtained."
    )
