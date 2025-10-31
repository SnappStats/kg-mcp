from typing import Optional, List
from pydantic import BaseModel, Field

# --- Sub Models ---

class Source(BaseModel):
    """Citation source for grounding references."""
    number: Optional[int] = None
    title: str = ""
    url: str = ""


class AthleteCharacteristics(BaseModel):
    """Scouting evaluation backed by measurable data and specific observations from film/stats."""

    playing_style: str = Field(
        "",
        description=(
            "Overall playing style backed by stats and measurables. Classification by position type (pass-first vs dual-threat QB, power vs finesse RB, possession vs deep threat WR). "
            "Include: completion %, TD:INT ratio, rush attempts/yards, YPC, target distribution, route tree. Scheme fit indicators (pro-style vs spread, RPO usage). "
            "Connect measurables (40-yard dash, height/weight) to playing style. "
            "Example: 'Pass-first pocket QB (68% completion, 42:4 TD:INT over 450 attempts) with limited designed runs (65 rush attempts).[1] 4.6 forty and 450 rush yards on RPOs.[2]'"
        )
    )

    strengths: str = Field(
        "",
        description=(
            "Key strengths with measurables and stats. Provide quantitative support for each claim: throw distance/velocity for arm strength, catch rate for hands, "
            "40-time/vertical for explosiveness. Extract specific language from scouting reports. Include both physical tools and technical skills. "
            "Example: 'Elite arm strength with 60+ yard range at Elite 11.[1] Ball velocity 58 mph at Under Armour combine.[2] Quick release sub-0.4 seconds.[3] "
            "Low INT rate (4 INTs in 450 attempts, 0.9%).[4] 78% completion on intermediate routes (15-25 yards).[5]'"
        )
    )

    weaknesses: str = Field(
        "",
        description=(
            "Areas for improvement with objective evidence from stats or scout observations. Provide statistical evidence: completion % on deep balls, sack rate under pressure, "
            "catch rate vs coverages, YPC against stacked boxes. Distinguish correctable technical issues vs physical limitations. Note if improving or persistent. "
            "Example: 'Deep ball accuracy needs work: 12 of 35 attempts (34%) on 20+ yard throws.[1] Struggles under pressure: 8 sacks when blitzed (12% sack rate vs 3% clean pocket).[2] "
            "Footwork inconsistent under pressure.[3]'"
        )
    )

    football_iq: str = Field(
        "",
        description=(
            "Processing speed and decision-making backed by stats and coach quotes. Evidence of pre-snap adjustments, check-downs, protection calls, audibles. "
            "Use TD:INT ratio for decision-making, sack rate for processing speed, completion rate on hot routes. Coach quotes about film study and leadership. "
            "Example: 'Advanced pre-snap recognition per coach: \"Calls protections like a college QB.\"[1] Elite 42:4 TD:INT ratio.[2] 68% completion on 3rd read progressions.[3] "
            "Low sack rate (1.2 per game, 3.4% sack rate).[4]'"
        )
    )

    multi_sport_athlete: str = Field(
        "",
        description=(
            "Other sports with achievements and timing. For each sport: level (varsity/JV), years played, stats/achievements, relevance to football athleticism. "
            "Note if focused on football junior/senior year or played multiple sports through graduation. "
            "Example: 'Basketball (varsity, 2 years): Averaged 12 PPG as starting PG, body control and change of direction.[1] Track (3 years): State Champion 100m (10.8s), elite straight-line speed.[2]' "
            "Empty string if single-sport."
        )
    )

    camp_circuit: str = Field(
        "",
        description=(
            "Elite camp performances. For each: camp name, date, performance highlights, rankings earned, awards won. "
            "Key camps: Elite 11 Finals, The Opening Finals, Under Armour All-American, Army All-American, Rivals Camp Series. "
            "Example: 'Elite 11 Finals (June 2024): Top QB performer, won accuracy challenge 18 of 20 targets.[1] The Opening Finals (July 2024): MVP award, 42 of 50 passes, 8 TDs.[2]' "
            "Empty string if no major camp participation."
        )
    )

    projection: str = Field(
        "",
        description=(
            "College/NFL projection and developmental outlook from scouts. Include: college readiness (Day 1 starter vs redshirt), development timeline, "
            "ceiling/floor analysis, NFL draft potential. Physical tools vs technical refinement needed. "
            "Example: 'Day 1 Power 5 starter potential per 247Sports.[1] Multi-year starter ceiling with All-American upside.[2] NFL draft prospect with 1st-3rd round potential.[3]'"
        )
    )

    player_comparisons: str = Field(
        "",
        description=(
            "Pro/college player comparisons from recruiting analysts. Look for 'reminds of', 'similar to', 'plays like' language. "
            "Include WHY the comparison fits (arm strength, playing style, body type, skillset). Only from scout reports. "
            "Example: '247Sports: \"Reminds me of Patrick Mahomes with similar arm talent and improvisational ability.\"[1] On3: \"Playing style similar to Joe Burrow with pocket presence and accuracy.\"[2]' "
            "Empty string if no comparisons found."
        )
    )


class RecruitingProfile(BaseModel):
    """Comprehensive recruiting information with historical tracking."""

    star_ratings: str = Field(
        "",
        description=(
            "Star ratings from all major services with specific rankings. Star count (1-5), composite score, overall national rank, position rank from each service. "
            "247Sports Composite (aggregates all services) is most important. Note discrepancies between services. "
            "Example: '247Sports: 5-star, No. 1 QB, composite 0.9998.[1] On3: 5-star, No. 2 QB, rating 98.50.[2] ESPN: 4-star, No. 2 QB in ESPN300, grade 92.[3] 247 Composite: 5-star, No. 1 overall.[4]'"
        )
    )

    scholarship_offers: str = Field(
        "",
        description=(
            "All known college scholarship offers as comma-separated list. Include Power 5, Group of 5, FCS offers. "
            "Example: 'Texas, Georgia, Alabama, LSU, Ohio State, Michigan, USC, Oregon, Florida, Notre Dame, total 20 offers.[1]'"
        )
    )

    latest_offer: str = Field(
        "",
        description=(
            "Most recent scholarship offer with school name and exact date. Shows current recruiting momentum. "
            "Example: 'USC (October 15, 2024).[1]'"
        )
    )

    visits: str = Field(
        "",
        description=(
            "Official and unofficial visits with dates. Official visits (NCAA-regulated, limited to 5, school-paid). Unofficial visits (player-funded, unlimited). "
            "For each: school name, dates, purpose. Include scheduled future visits. "
            "Example: 'Official: Texas (June 14-16, 2024).[1] Georgia (June 7-9).[2] Used 3 of 5. | Unofficial: Alabama spring practice (March 23).[3] LSU Spring Game (April 13).[4]'"
        )
    )

    school_interest: str = Field(
        "",
        description=(
            "Top contending schools and pursuit level. 247Sports Crystal Ball (expert picks with confidence %), On3 RPM (0-100% prediction score). "
            "Pursuit level indicators: leader, heavy pursuit, dark horse, long shot. "
            "Example: 'Texas leads with 85% Crystal Ball (12 picks Texas, 2 Alabama).[1] Georgia heavy pursuit.[2] On3 RPM: 95% Texas prediction.[3]'"
        )
    )

    self_reported_offers: str = Field(
        "",
        description=(
            "Offers and commitments player announced via social media. Commitment posts, offer graphics, visit announcements, top schools lists. "
            "Example: 'Committed to Texas via Twitter July 4, 2024.[1] Posted Georgia offer graphic May 15.[2] Top 10 schools list June 1.[3]'"
        )
    )

    offer_tier_analysis: str = Field(
        "",
        description=(
            "Breakdown of offers by competitive tier. Elite (CFP contenders), Power 5, Group of 5, FCS. Count offers in each tier. "
            "Example: 'Elite: Alabama, Georgia, Ohio State, Texas (4 offers).[1] Power 5: USC, Michigan, Penn State, LSU (8 more).[2] G5: SMU, Tulane (2).[3] Total 14 D1 offers.[1,2,3]'"
        )
    )

    nil_valuation: str = Field(
        "",
        description=(
            "NIL market valuation and known deals. On3 NIL Valuation, announced deals, brand partnerships. "
            "Example: 'On3 NIL: $2.1M value, No. 5 nationally.[1] Local dealership partnership (Aug 2024).[2] Regional restaurant chain deal (Sept 2024).[3]' "
            "Empty string if none found."
        )
    )

    enrollment_plans: str = Field(
        "",
        description=(
            "Enrollment timeline. Early (January = spring practice), Summer (workouts, no spring), Fall (August = standard). Mission service, grayshirt, special timing. "
            "Example: 'Early enroll January 2025, will participate in spring practice.[1]' "
            "Empty string if not specified."
        )
    )

    family_connections: str = Field(
        "",
        description=(
            "Family connections to college programs. Parents/siblings who played: sport, college, years, position, statistics. Coaches: relationship, role, school, years. "
            "Example: 'Father played QB at Texas (1995-1999), 3-year starter, 7,200 career passing yards.[1] Brother on Alabama roster as WR (RS Soph, 15 catches 2024).[2]' "
            "Empty string if none."
        )
    )


class TeamProfile(BaseModel):
    """High school team details and recruiting environment - all data-driven."""

    high_school_team: str = Field(
        "",
        description="Full official team name including mascot. Example: 'Lake Travis Cavaliers' or 'Mater Dei Monarchs'"
    )

    coach: str = Field(
        "",
        description=(
            "Head coach name with tenure stats. Full name, years at school, W-L record, championships, playoff appearances. "
            "Example: 'HC Mike Smith (10th year, 95-23 record, 2 state championships, 8 consecutive playoff appearances).[1]'"
        )
    )

    conference: str = Field(
        "",
        description="Official conference/district/league name. Example: 'District 25-6A' or 'Trinity League'"
    )

    team_records: str = Field(
        "",
        description=(
            "Team W-L records by year with playoff results. Include W-L, playoff round, championship results, PPG scored/allowed. List all years player on roster. "
            "Example: '2024: 13-1, State Champions (beat rival 45-42), 42 PPG.[1] 2023: 11-2, State Semifinals, 38 PPG, 21 PPG allowed.[2]'"
        )
    )

    competition_level: str = Field(
        "",
        description=(
            "State classification and regional competition strength. Classification level, number of teams, conference standings, ranked opponents faced. "
            "Example: 'Texas 6A Division I (200+ schools).[1] Faced 3 national top-25 opponents.[2] Finished 2nd in 8-team district (9-1 record).[3]'"
        )
    )

    conference_strength: str = Field(
        "",
        description=(
            "Conference talent concentration. Total teams, standings, combined D1 signees, nationally ranked teams, playoff success. "
            "Example: 'Trinity League: 6 teams, 47 D1 signees in 2024 class (7.8 per school).[1] 5 of 6 teams ranked national top 25.[2] 4 teams reached state semifinals.[3]'"
        )
    )

    school_recruiting_history: str = Field(
        "",
        description=(
            "Historical D1 pipeline. D1 signee counts by year (last 3-5 years), P5 vs G5 breakdown, notable alumni with college production, averages. "
            "Example: '2024: 8 D1 signees (5 P5, 3 G5).[1] 2023: 6 D1 (3 P5, 3 G5).[2] Notable: QB John Doe (Texas, 2,800 pass yds as true freshman).[3] 5-yr avg: 6.2 D1/year.[4]'"
        )
    )

    teammate_recruits: str = Field(
        "",
        description=(
            "Teammates with D1 offers. For each: name, position, star rating, composite, offer count, top offers, their stats, measurables. Total D1 prospect count. "
            "Example: 'OL James Johnson: 4-star (0.9234), 15 offers (Alabama/Georgia/Texas top 3), 6\\'5\" 310 lbs, First Team All-State.[1] Total: 5 teammates with D1 offers.[2]' "
            "Empty if none."
        )
    )

    opponent_quality: str = Field(
        "",
        description=(
            "Opponents with their stats and recruiting data. For top opponents: name, W-L, ranking, PPG, D1 recruit count, key players, head-to-head result. "
            "Example: 'vs Mater Dei (Won 28-24): 12-1, #1 nationally, 45 PPG/12 PPG allowed, 12 D1 recruits including 5-star DE (15 sacks).[1] Record vs teams with 5+ D1 recruits: 4-2.[2]'"
        )
    )

    strength_of_schedule: str = Field(
        "",
        description=(
            "Schedule difficulty quantified. Ranked opponents count, combined opponent win %, average ranking, playoff teams faced, state champions faced. "
            "Example: 'Faced 6 nationally ranked opponents (avg #18 ranking).[1] Combined opponent record: 95-35 (.731 win %).[2] 4 playoff teams, 2 state champions on schedule.[3]'"
        )
    )

    transfer_context: str = Field(
        "",
        description=(
            "Transfer details. Reason, timing, previous vs new school classification, stats before/after, previous school's record. "
            "Example: 'Transferred from St. John\\'s (5A, 6-5 in 2022) to IMG Academy (11-1 in 2023) for national exposure (summer 2023).[1] Stats improved: 2,100 pass yds to 3,200 yds.[2]' "
            "Empty if none."
        )
    )


class Rankings(BaseModel):
    """Official rankings and accolades from major scouting sources."""

    accolades: str = Field(
        "",
        description=(
            "All major honors and awards with years. Under Armour All-American, Army All-American, Gatorade POY, MaxPreps All-American, USA Today All-USA, "
            "State POY, All-State, Mr. Football, national/state/regional honors. "
            "Example: 'Under Armour All-American (2024).[1] Gatorade Texas POY (2024).[2] First Team All-State 6A (2024, 2023).[3] USA Today All-USA First Team (2024).[4]'"
        )
    )

    source_rankings: str = Field(
        "",
        description=(
            "All major recruiting service rankings. For each: star rating, composite score, overall national rank, position rank, class year. 247 Composite aggregates all. "
            "Example: '247Sports: 5-star, 0.9998 composite, No. 1 QB, No. 1 overall 2025.[1] On3: 5-star, 98.50 rating, No. 2 QB 2025.[2] ESPN: 4-star, grade 92, No. 2 QB ESPN300.[3]'"
        )
    )

    conference_awards: str = Field(
        "",
        description=(
            "Conference/district awards with years. All-conference/district teams, POY, Offensive/Defensive POY, Newcomer of Year. "
            "Example: 'District 25-6A Offensive MVP (2024, 2023).[1] First Team All-District (2024, 2023, 2022).[2] Trinity League Offensive POY (2024).[3]'"
        )
    )


class Statistics(BaseModel):
    """Player performance statistics - individual production data only."""

    season_stats: str = Field(
        "",
        description=(
            "Year-by-year player stats with grade level. Complete stats by year, all position-relevant stats, per-game averages, efficiency metrics. Note backup/limited time context. "
            "Example QB: '2024 Senior (12 games): 3,845 pass yds (320 YPG), 42 TDs, 4 INTs, 68% comp (305/450), 158.2 rating, 450 rush yds (6.9 YPC), 8 rush TDs.[1] "
            "2023 Junior: 2,912 pass yds (243 YPG), 28 TDs, 6 INTs, 64% comp (268/420), 380 rush yds.[2]' "
            "Example WR: '2024 Senior (12 games): 1,245 rec yds (104 YPG), 18 TDs, 72 rec, 17.3 YPC, 55% catch rate (130 targets), 8 catches 40+ yds.[1]'"
        )
    )

    key_games_outcomes: str = Field(
        "",
        description=(
            "Standout performances in key games. Championship games, vs ranked opponents, career-highs, clutch performances. Include: opponent (with ranking), complete stat line, result/score, context. "
            "Example: 'State Championship vs #3 Allen (Won 45-42): 425 pass yds (28/35, 80%), 5 TDs, 0 INTs, 45 rush yds, game-winning drive final 2 min.[1] "
            "vs #1 Mater Dei (Lost 31-28): 380 pass yds (32/42, 76%), 3 pass TDs, 2 rush TDs, 120 rush yds.[2]'"
        )
    )


# --- Main Scout Report Model ---

class ScoutReport(BaseModel):
    """Complete scouting report for a high school football recruit."""

    # Basic info
    player_name: str = ""
    position: str = ""
    height: str = ""
    weight: str = ""
    school_name: str = ""
    location: str = ""
    graduation_class: str = ""
    gpa: str = ""
    twitter_handle: str = ""
    previous_schools: str = ""

    # Main sections
    athlete_characteristics: AthleteCharacteristics = Field(default_factory=AthleteCharacteristics)
    recruiting_profile: RecruitingProfile = Field(default_factory=RecruitingProfile)
    team_profile: TeamProfile = Field(default_factory=TeamProfile)
    rankings: Rankings = Field(default_factory=Rankings)
    statistics: Statistics = Field(default_factory=Statistics)

    # Sources
    sources: List[Source] = Field(default_factory=list)
