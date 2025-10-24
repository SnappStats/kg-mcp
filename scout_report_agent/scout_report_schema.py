from typing import Optional, List
from pydantic import BaseModel, Field, AliasPath

# --- Sub Models ---

class Source(BaseModel):
    """Citation source for grounding references."""
    number: Optional[int] = Field(None, description="Citation number (e.g., 1, 2, 3).")
    title: str = Field("", description="Title or name of the source.")
    url: str = Field("", description="URL to the source.")


class PhysicalProfile(BaseModel):
    """Detailed physical measurements and athletic testing data with historical tracking."""
    measurements: str = Field(
        "",
        description="ALL height/weight measurements from ALL sources with dates for historical tracking. "
        "Example: 'Height: 6'4\" (Texas Athletics, 2025), 6'3.5\" (On3, 2022), 6'3\" (HS, 2021). Weight: 219 lbs (Texas, 2025), 215 lbs (247Sports, 2022)'"
    )
    athletic_testing: str = Field(
        "",
        description="Weight room stats, track times, combine results, camp measurements with sources."
    )
    physical_development: str = Field(
        "",
        description="Physical growth and development notes year-to-year."
    )


class RecruitingProfile(BaseModel):
    """Comprehensive recruiting information with historical tracking."""
    star_ratings: str = Field(
        "",
        description="Star ratings from all services with rankings, formatted as single string. "
        "Example: '247Sports: 5-star, No. 1 QB | On3: 5-star | ESPN: 4-star, No. 2 QB'"
    )
    scholarship_offers: str = Field(
        "",
        description="All known college scholarship offers as comma-separated string. "
        "Example: 'Texas, Georgia, Alabama, LSU, Ohio State'"
    )
    latest_offer: str = Field(
        "",
        description="Most recent offer with school and date if available."
    )
    visits: str = Field(
        "",
        description="Official and unofficial visits with dates."
    )
    school_interest: str = Field(
        "",
        description="Schools/programs showing reported interest."
    )
    self_reported_offers: str = Field(
        "",
        description="Offers and commitments reported via player's social media."
    )


class TeamProfile(BaseModel):
    """Details about the player's high school team and recruiting environment."""
    high_school_team: Optional[str] = Field(
        None,
        description="Name of the high school team."
    )
    coach: Optional[str] = Field(
        None,
        description="Name of the high school coach."
    )
    conference: Optional[str] = Field(
        None,
        description="Team conference or league name."
    )
    recruitment_breakdown: Optional[str] = Field(
        None,
        description="Information about teammates recruited (division, star ratings, player names)."
    )


class Rankings(BaseModel):
    """Official rankings and accolades from major scouting sources."""
    accolades: str = Field(
        "",
        description="General accolades and honors formatted as string with separators and years. "
        "Example: 'All-State (2023) | All-American (2023) | MaxPreps National Freshman of Year (2020)'"
    )
    source_rankings: str = Field(
        "",
        description="Rankings from major scouting sources formatted as string. "
        "Example: '247Sports: 5-star, No. 1 QB | On3: 5-star | ESPN: 4-star, No. 2 nationally'"
    )


class Statistics(BaseModel):
    """Detailed season statistics and game performance data."""
    season_stats: str = Field(
        "",
        description="Year-by-year breakdown with stats as formatted string. "
        "Example: '2022 Junior: 2,500 yards, 25 TDs | 2023 Senior: 3,000 yards, 30 TDs'. "
        "If transferred, specify school for each year."
    )
    team_records: str = Field(
        "",
        description="Team W-L records by year as formatted string. "
        "Example: '2022: 10-2, State Semifinals | 2023: 12-1, State Champions'"
    )
    competition_level: str = Field(
        "",
        description="State classification, strength of region/schedule, notable opponents and teammates."
    )
    key_games_outcomes: Optional[str] = Field(
        None,
        description="Key game performances and outcomes formatted as string with years and citations. "
        "Example: 'Championship Game (2023): 4 TDs, 300 yards, Win [12] | vs #1 Ranked Team (2023): 2 TDs, Loss [15]'"
    )


class Intangibles(BaseModel):
    """Character, leadership, and off-field information."""
    character_leadership: Optional[str] = Field(
        "",
        description="Character traits, work ethic, leadership qualities from articles/interviews."
    )
    twitter_review: Optional[str] = Field(
        "",
        description="Analysis of X/Twitter activity - recruiting news, character indicators, engagement."
    )
    academic_profile: Optional[str] = Field(
        "",
        description="Full academic history: GPA over time, academic awards, AP/honors classes, school academic reputation. "
        "Example: 'GPA: 3.8 (Senior, 2023), 3.6 (Junior, 2022). Honors: AP Scholar, National Honor Society. School: Top-ranked prep school.'"
    )
    media_coverage: Optional[str] = Field(
        "",
        description="Key insights and narratives from local news, beat writers, media coverage."
    )


class PublicPerception(BaseModel):
    """Media and public view of the player."""
    articles_beat_writers: Optional[str] = Field(
        None,
        description="Links or summaries of articles and mentions by beat writers with dates. "
        "Example: 'ESPN article on recruitment (June 2023) [10] | Local Times feature on leadership (Sept 2023) [15]'"
    )
    highlight_reels: Optional[str] = Field(
        None,
        description="Note on where highlight reels can be found (e.g., Hudl link, YouTube channel)."
    )


class ExternalLinks(BaseModel):
    """Links to external profile platforms and social media."""
    hudl: Optional[str] = Field(
        None,
        description="URL link to the player's Hudl profile."
    )
    social_media: Optional[str] = Field(
        None,
        description="Social media handle or URL (e.g., Twitter/X handle, Instagram)."
    )
    red_flags: Optional[str] = Field(
        None,
        description="Any known behavioral, injury, or academic red flags or concerns."
    )


# --- Main Model ---

class ScoutReport(BaseModel):
    """
    Comprehensive college football scout report with quick-access fields and detailed historical tracking.

    Quick-access fields (top level) contain the most recent data from credible sources.
    Sub-models contain comprehensive historical data with all sources and dates.
    """

    # === QUICK ACCESS (Latest from Most Credible Sources) ===
    player_name: str = Field(
        "",
        description="Full name of the player."
    )
    position: str = Field(
        "",
        description="Football position(s) played (e.g., 'QB', 'WR', 'DB/WR')."
    )
    height: str = Field(
        "",
        description="Most recent height from credible source (major recruiting services, official athletics sites, verified measurements). "
        "Example: '6\\'4\"'"
    )
    weight: str = Field(
        "",
        description="Most recent weight from credible source. "
        "Example: '219 lbs'"
    )
    school_name: str = Field(
        "",
        description="Current or final high school name in 'School Name (City, State)' format."
    )
    location: str = Field(
        "",
        description="City, State location."
    )
    graduation_class: str = Field(
        "",
        description="High school graduation year (e.g., '2025')."
    )
    gpa: Optional[str] = Field(
        None,
        description="Most recent GPA from credible source if available. Format: just the number (e.g., '3.8') or null if unavailable."
    )
    twitter_handle: Optional[str] = Field(
        None,
        description="X/Twitter handle in '@username' format."
    )
    previous_schools: str = Field(
        "",
        description="Previous high schools attended while playing varsity with years. "
        "Example: 'St. John's HS (2020-2021) | Transfer to IMG Academy (2022)'. Empty string if no transfers."
    )

    # === SUMMARY ===
    executive_summary: str = Field(
        "",
        alias="TLDR",
        validation_alias=AliasPath("TLDR", "executive_summary"),
        description="Concise summary of the player's profile, strengths, and potential."
    )

    # === DETAILED TRACKING (Historical Data with Sources) ===
    physical_profile: PhysicalProfile = Field(
        default_factory=PhysicalProfile,
        description="Physical measurements and athletic testing with full historical tracking."
    )

    recruiting_profile: RecruitingProfile = Field(
        default_factory=RecruitingProfile,
        description="Comprehensive recruiting information and history."
    )

    team_profile: TeamProfile = Field(
        default_factory=TeamProfile,
        description="High school team environment and coaching."
    )

    statistics: Statistics = Field(
        default_factory=Statistics,
        description="Performance statistics and game outcomes."
    )

    intangibles: Intangibles = Field(
        default_factory=Intangibles,
        description="Character, leadership, academics, and off-field profile."
    )

    # === ACCOLADES & RECOGNITION ===
    rankings_accolades: Rankings = Field(
        default_factory=Rankings,
        description="Rankings and accolades from major scouting sources."
    )

    conference_awards: str = Field(
        "",
        description="Conference-level awards with years and citations. "
        "Example: 'First Team All-Conference (2023) [10] | Conference Defensive Player of Year (2023) [12]'"
    )

    offers_commits: str = Field(
        "",
        description="Scholarship offers and commitments with dates and citations. "
        "Example: 'Offer: USC (Jan 2023) [5] | Committed: Ohio State (June 2023) [8] | Offer: Alabama (March 2023) [6]'"
    )

    # === ATHLETICISM ===
    athlete_characteristics: str = Field(
        "",
        description="Key athletic attributes and traits with citations. "
        "Example: 'Elite speed [10] | Strong arm [12] | High football IQ [15] | Natural leader [20]'"
    )

    # === EXTERNAL DATA ===
    perception: PublicPerception = Field(
        default_factory=PublicPerception,
        description="Media coverage and public perception."
    )

    external_links: ExternalLinks = Field(
        default_factory=ExternalLinks,
        description="Links to external profiles and social media."
    )

    # === CITATIONS ===
    sources: List[Source] = Field(
        default_factory=list,
        description="Citation sources from grounding metadata with number, title, and URL."
    )
