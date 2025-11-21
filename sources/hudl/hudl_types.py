from typing import Optional, List
from pydantic import BaseModel

class AthleticismStats(BaseModel):
    forty_yard_dash: Optional[float] = None
    forty_verified: Optional[bool] = None
    vertical: Optional[int] = None
    vertical_verified: Optional[bool] = None
    bench: Optional[int] = None
    bench_verified: Optional[bool] = None
    bench_185_reps: Optional[int] = None
    bench_185_reps_verified: Optional[bool] = None
    squat: Optional[int] = None
    deadlift: Optional[int] = None
    clean: Optional[int] = None
    pro_agility: Optional[float] = None
    shuttle: Optional[float] = None
    shuttle_verified: Optional[bool] = None
    powerball: Optional[int] = None
    powerball_verified: Optional[bool] = None
    nike_football_rating: Optional[int] = None
    nike_football_rating_verified: Optional[bool] = None
    meter_100: Optional[float] = None
    meter_400: Optional[float] = None
    meter_1600: Optional[float] = None
    meter_3200: Optional[float] = None
    approach_jump_touch_one_arm: Optional[int] = None
    vertical_jump_one_arm: Optional[int] = None
    vertical_jumping_block_two_arms: Optional[int] = None
    six_touches_sideline_to_sideline: Optional[float] = None
    standing_reach: Optional[int] = None
    standing_blocking_reach: Optional[int] = None
    achievements: Optional[str] = None


class HudlVideoSource(BaseModel):
    url: str
    title: str
    date: int  # unix epoch timestamp
    season: int
    duration_ms: int


class HudlPlayerData(BaseModel):
    name: str
    positions: str
    school: str
    height: str
    weight: str
    location: str
    class_year: Optional[str] = None
    jersey_number: Optional[str] = None
    athleticism: Optional[AthleticismStats] = None
    hudl_video_sources: List[HudlVideoSource]
    source_identifier: str
    avatar_url: Optional[str] = None
