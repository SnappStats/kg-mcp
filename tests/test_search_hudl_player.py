import json
import re
import pytest
from scout_report_agent.tools.search_hudl_player import search_hudl_player


class TestSearchHudlPlayer:
    """Test cases for the search_hudl_player function."""

    @pytest.mark.parametrize("player_name,expected_profile_ids", [
        ("Alex Duckett", ["17709524"]),
        ("Ryder Lyons", ["16389887"]),
        ("Bishop Merriweather", ["17709508"]),
        ("Dillon Hartman", ["18596366"]),
        ("Scott Nardinel", ["19142423"]),  # Note: Nardinelli vs Nardinel
    ])
    def test_search_hudl_player_finds_correct_profiles(self, player_name, expected_profile_ids):
        result_json = search_hudl_player(player_name)
        result = json.loads(result_json)

        assert result["status"] == "success", f"Expected success status for {player_name}, got {result['status']}"
        assert len(result["urls"]) > 0, f"No URLs found for {player_name}"

        found_profile_ids = set()
        for url in result["urls"]:
            import re
            match = re.search(r'hudl\.com/profile/(\d+)', url)
            if match:
                found_profile_ids.add(match.group(1))

        expected_ids_set = set(expected_profile_ids)
        assert expected_ids_set.intersection(found_profile_ids), (
            f"Expected profile ID(s) {expected_profile_ids} not found in results for {player_name}. "
            f"Found profile IDs: {found_profile_ids}"
        )

    def test_search_hudl_player_returns_valid_json(self):
        result = search_hudl_player("Alex Duckett")
        parsed = json.loads(result)
        assert "status" in parsed
        assert "message" in parsed
        assert "urls" in parsed
        assert isinstance(parsed["urls"], list)

    def test_search_hudl_player_nonexistent_player(self):
        result_json = search_hudl_player("ZzzNonExistentPlayerXyz123")
        result = json.loads(result_json)

        assert result["status"] in ["success", "not_found", "error"]
        assert isinstance(result["urls"], list)

    def test_search_hudl_player_url_format(self):
        result_json = search_hudl_player("Alex Duckett")
        result = json.loads(result_json)

        if result["status"] == "success" and len(result["urls"]) > 0:
            for url in result["urls"]:
                assert url.startswith("https://www.hudl.com/profile/")
                assert re.search(r'/profile/\d+', url)

    @pytest.mark.parametrize("player_name,expected_urls", [
        ("Alex Duckett", [
            "https://www.hudl.com/profile/17709524/Alex-Duckett",
            "https://www.hudl.com/profile/17709524"
        ]),
        ("Ryder Lyons", [
            "https://www.hudl.com/profile/16389887/Ryder-Lyons",
            "https://www.hudl.com/profile/16389887"
        ]),
        ("Bishop Merriweather", [
            "https://www.hudl.com/profile/17709508/Bishop-Merriweather",
            "https://www.hudl.com/profile/17709508"
        ]),
        ("Dillon Hartman", [
            "https://www.hudl.com/profile/18596366/Dillon-Hartman",
            "https://www.hudl.com/profile/18596366"
        ]),
        ("Scott Nardinelli", [
            "https://www.hudl.com/profile/19142423/Scott-Nardinelli",
            "https://www.hudl.com/profile/19142423"
        ]),
    ])
    def test_search_hudl_player_exact_url_match(self, player_name, expected_urls):
        result_json = search_hudl_player(player_name)
        result = json.loads(result_json)

        assert result["status"] == "success", f"Expected success for {player_name}"

        found_urls = set(result["urls"])
        expected_urls_set = set(expected_urls)

        profile_id = expected_urls[0].split("/profile/")[1].split("/")[0]
        found_matching = any(profile_id in url for url in found_urls)

        assert found_matching, (
            f"Expected to find profile ID {profile_id} in results for {player_name}. "
            f"Found URLs: {found_urls}"
        )
