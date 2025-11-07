from pydantic import BaseModel, Field
from typing import Dict, List, Any, Optional


class AnalysisItem(BaseModel):
    """
    Represents a single item of analysis (award, strength, weakness, quote).
    """
    title: str = Field(
        ...,
        description="The category or title of the analysis item (e.g., 'Awards', 'Strengths', 'Weaknesses', 'Coach Quotes').",
        examples="2023 All-Conference First Team"
    )
    content: str = Field(
        ...,
        description="The detailed content of the item (e.g., specific weakness, the quotes itself), in markdown format.",
        examples="* Struggles with defensive close-outs.\n* Often gets beaten on the first step."
    )


class Player(BaseModel):
    """
    Core demographic and identifying information for the player.
    """
    name: str = Field(
        ...,
        description="The full name of the player being scouted.",
        examples="Jane E. Doe"
    )
    physicals: Dict[str, str] = Field(
        default_factory=dict,
        description="The player's key physical attributes (e.g., {'Height': '6ft 8in', 'Weight': '240lbs'}).",
        examples={"Height": "6ft 8in", "Weight": "240lbs"}
    )
    socials: Dict[str, str] = Field(
        default_factory=dict,
        description="A map of social media platform names to the player's handle/username.",
        examples={"Twitter": "@JaneDoeHoops", "Instagram": "janedoe_official"}
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
        description="Categorical tags for the report, including key identifying factors like **sport**, **school**, **team**, and **position**.",
        examples=["Football", "USC", "Trojans", "Wide Receiver"]
    )
    analysis: List[AnalysisItem] = Field(
        default_factory=list,
        description="A list of analyses or opinions such as awards, rankings, strengths, and weaknesses."
    )
    stats: List[str] = Field(
        default_factory=list,
        description="A list of relevant statistics, including game averages and **athletic measurables**.",
        examples=["Bench Press: 315 lbs", "40 Yard Dash: 4.41s", "PPG: 22.5"]
    )
    citations: List[str] = Field(
        default_factory=list,
        description="A list of urls from which this information was obtained."
    )
