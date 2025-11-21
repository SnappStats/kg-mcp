import aiohttp
from bs4 import BeautifulSoup
import json
import re
from utils.logger import logger
from .hudl_types import HudlPlayerData, HudlVideoSource, AthleticismStats

# Module-level session for reuse across requests
_session: aiohttp.ClientSession | None = None


async def get_session() -> aiohttp.ClientSession:
    global _session
    if _session is None or _session.closed:
        _session = aiohttp.ClientSession()
    return _session


async def close_session():
    global _session
    if _session is not None and not _session.closed:
        await _session.close()
        _session = None


@logger.catch(reraise=True)
async def scrape_hudl_profile_data(url: str) -> HudlPlayerData:
    session = await get_session()
    async with session.get(url) as response:
        html_content = await response.text()

    soup = BeautifulSoup(html_content, "html.parser")

    script_tag = soup.find("script", string=re.compile(r"window\.__hudlEmbed"))
    if not script_tag:
        raise Exception("Could not find player data in page")

    script_content = script_tag.string

    json_match = re.search(
        r"window\.__hudlEmbed\s*=\s*({.*?});", script_content, re.DOTALL
    )
    if not json_match:
        json_match = re.search(
            r"window\.__hudlEmbed\s*=\s*({.*});</script>", script_content, re.DOTALL
        )

    if not json_match:
        raise Exception("Could not extract JSON data from script")

    data = json.loads(json_match.group(1))
    model_data = data.get("model", {})
    user_data = model_data.get("user", {})
    about_data = model_data.get("about", {})
    
    # NOTE: the following is to collect the player videos
    highlights_data = model_data.get("highlights", {})
    reels = highlights_data.get("reels", [])
    reels = sorted(reels, key=lambda x: (x.get("unixTime", 0), x.get("views", 0)), reverse=True)
    overview = about_data.get("overview", {})
    strength_speed = about_data.get("strengthAndSpeed", {})


    def safe_str(value, default=""):
        if value is None:
            return default
        return str(value).strip() if str(value).strip() else default

    name = safe_str(user_data.get("primaryName"))
    positions = safe_str(user_data.get("positions"))
    school = safe_str(overview.get("organization"))
    height = safe_str(overview.get("height"))
    weight = safe_str(overview.get("weight"))
    location = safe_str(overview.get("location"))
    avatar_url = user_data.get("profileLogoUri")
    
    if avatar_url is None:
        avatar_url = safe_str(user_data.get("mobileProfileLogoUri"))

    graduation_year = overview.get("graduationYear")
    class_year = str(graduation_year) if graduation_year is not None else None

    jersey = user_data.get("jersey")
    jersey_number = str(jersey) if jersey is not None else None

    athleticism_stats = None
    if strength_speed:
        athleticism_data = {}

        def safe_float(value):
            try:
                return float(value) if value is not None else None
            except (ValueError, TypeError):
                return None

        def safe_int(value):
            try:
                return int(value) if value is not None else None
            except (ValueError, TypeError):
                return None

        athleticism_data["forty_yard_dash"] = safe_float(
            strength_speed.get("forty")
        )
        athleticism_data["forty_verified"] = strength_speed.get("fortyVerified")
        athleticism_data["vertical"] = safe_int(strength_speed.get("vertical"))
        athleticism_data["vertical_verified"] = strength_speed.get(
            "verticalVerified"
        )
        athleticism_data["bench"] = safe_int(strength_speed.get("bench"))
        athleticism_data["bench_verified"] = strength_speed.get("benchVerified")
        athleticism_data["bench_185_reps"] = safe_int(
            strength_speed.get("benchPressReps")
        )
        athleticism_data["bench_185_reps_verified"] = strength_speed.get(
            "benchPressRepsVerified"
        )
        athleticism_data["squat"] = safe_int(strength_speed.get("squat"))
        athleticism_data["deadlift"] = safe_int(strength_speed.get("deadLift"))
        athleticism_data["clean"] = safe_int(strength_speed.get("clean"))
        athleticism_data["pro_agility"] = safe_float(
            strength_speed.get("proAgility")
        )
        athleticism_data["shuttle"] = safe_float(strength_speed.get("shuttle"))
        athleticism_data["shuttle_verified"] = strength_speed.get("shuttleVerified")
        athleticism_data["powerball"] = safe_int(strength_speed.get("powerball"))
        athleticism_data["powerball_verified"] = strength_speed.get(
            "powerballVerified"
        )
        athleticism_data["nike_football_rating"] = safe_int(
            strength_speed.get("nikeFootballRating")
        )
        athleticism_data["nike_football_rating_verified"] = strength_speed.get(
            "nikeFootballRatingVerified"
        )
        athleticism_data["meter_100"] = safe_float(strength_speed.get("meter100"))
        athleticism_data["meter_400"] = safe_float(strength_speed.get("meter400"))
        athleticism_data["meter_1600"] = safe_float(strength_speed.get("meter1600"))
        athleticism_data["meter_3200"] = safe_float(strength_speed.get("meter3200"))
        athleticism_data["approach_jump_touch_one_arm"] = safe_int(
            strength_speed.get("approachJumpTouchOneArm")
        )
        athleticism_data["vertical_jump_one_arm"] = safe_int(
            strength_speed.get("verticalJumpOneArm")
        )
        athleticism_data["vertical_jumping_block_two_arms"] = safe_int(
            strength_speed.get("verticalJumpingBlockTwoArms")
        )
        athleticism_data["six_touches_sideline_to_sideline"] = safe_float(
            strength_speed.get("sixTouchesSidelineToSideline")
        )
        athleticism_data["standing_reach"] = safe_int(
            strength_speed.get("standingReach")
        )
        athleticism_data["standing_blocking_reach"] = safe_int(
            strength_speed.get("standingBlockingReach")
        )

        achievements = strength_speed.get("achievements")
        if isinstance(achievements, list):
            athleticism_data["achievements"] = ", ".join(
                str(achievement).strip()
                for achievement in achievements
                if achievement
            )
        else:
            athleticism_data["achievements"] = achievements

        if any(value is not None for value in athleticism_data.values()):
            athleticism_stats = AthleticismStats(**athleticism_data)

    hudl_video_sources = []
    for video in reels:
        video_files = video.get("videoFiles", [])
        if not video_files:
            continue

        best_video = None
        for video_file in video_files:
            quality = video_file.get("quality", 0)
            if not best_video or quality > best_video.get("quality", 0):
                best_video = video_file

        if best_video and best_video.get("url"):
            hudl_video_sources.append(
                HudlVideoSource(
                    url=best_video.get("url"),
                    title=video.get("title", ""),
                    date=video.get("unixTime", 0),
                    season=video.get("season", 0),
                    duration_ms=video.get("durationMs", 0),
                )
            )

    return HudlPlayerData(
        name=name,
        positions=positions,
        school=school,
        height=height,
        weight=weight,
        location=location,
        class_year=class_year,
        jersey_number=jersey_number,
        athleticism=athleticism_stats,
        source_identifier=safe_str(user_data.get("userId")),
        hudl_video_sources=hudl_video_sources,
        avatar_url=avatar_url
    )

